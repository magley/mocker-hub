import math
from typing import List

from fastapi import Depends

from app.api.config.pagination import PaginatedResultInfoDTO, PaginatedResultDTO
from app.api.config.security import hash_password, verify_password
from app.api.config.exception_handler import FieldTakenException, NotFoundException, UserException, \
    AccessDeniedException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.org.org_repo import OrganizationRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.user.user_dto import UserPasswordChangeDTO, UserRegisterDTO, UserLoginDTO, UserTokenDTO, UserDTO
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.config.auth import sign_jwt

class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepo(session)
        self.org_repo = OrganizationRepo(session)
        self.repo_repo = RepositoryRepo(session)

    def add(self, dto: UserRegisterDTO) -> User:
        if self.user_repo.find_by_email(dto.email) is not None:
            raise FieldTakenException("Email")
        if self.user_repo.find_by_username(dto.username) is not None:
            raise FieldTakenException("Username")

        hashed_password = hash_password(dto.password)
        new_user = User.model_validate(dto, update={
            "hashed_password":hashed_password
        })

        return self.user_repo.add(new_user)
    
    def add_superadmin(self, dto: UserRegisterDTO) -> User:
        user = self.add(dto)
        user = self.user_repo.set_role(user, UserRole.superadmin)
        user = self.user_repo.flag_password_needs_change(user)
        return user
    
    def change_password(self, id: int, dto: UserPasswordChangeDTO):
        user = self.user_repo.find_by_id(id)

        if user is None:
            raise NotFoundException(User, id)
        if not verify_password(dto.old_password, user.hashed_password):
            raise UserException("Current password is incorrect")
        if dto.old_password == dto.new_password:
            raise UserException("New password must be different from the current password")
        
        hashed_password = hash_password(dto.new_password)
        user = self.user_repo.change_password(user, hashed_password)

        return

    def login(self, dto: UserLoginDTO) -> UserTokenDTO:
        user = self.user_repo.find_by_username(dto.username)
        
        if user is None:
            raise NotFoundException(User, dto.username)
        if not verify_password(dto.password, user.hashed_password):
            raise UserException("Username or password incorrect")

        return sign_jwt(user)
    
    def find_by_id(self, id: int) -> User:
        user = self.user_repo.find_by_id(id)
        if user is None:
            raise NotFoundException(User, id)
        return user
    
    def find_by_username(self, username: str) -> User:
        user = self.user_repo.find_by_username(username)
        if user is None:
            raise NotFoundException(User, username)
        return user      
      
    def add_admin(self, dto: UserRegisterDTO) -> User:
        user = self.add(dto)
        user = self.user_repo.set_role(user, UserRole.admin)
        return user
    
    def exists_with_credentials(self, username: str, password: str) -> bool:
        user = self.user_repo.find_by_username(username)
        
        if user is None:
            return False
        if not verify_password(password, user.hashed_password):
            raise False

        return True

    def search_by_username_prefix(self, query: str, org_id_to_exclude_members: int = 0) -> List[User]:
        all_users = self.user_repo.search_by_username_prefix(query)
        users_to_exclude = self.org_repo.find_members_of_org(org_id_to_exclude_members)
        users = [u for u in all_users if u not in users_to_exclude]
        return users

    def update_profile(self, user_id: int, dto: UserDTO) -> User:
        user = self.user_repo.find_by_id(dto.id)
        if not user:
            raise NotFoundException(user, dto.id)
        if user_id != dto.id:
            raise AccessDeniedException(f"User {user_id} cannot update another user with id {dto.id}")
        if user.email != dto.email:
            if self.user_repo.find_by_email(dto.email) is not None:
                raise FieldTakenException("Email")
            user.email = dto.email
        if dto.first_name is not None:
            user.first_name = dto.first_name
        if dto.last_name is not None:
            user.last_name = dto.last_name
        if dto.bio is not None:
            user.bio = dto.bio

        self.user_repo.add(user)
        return user

    def search_paginated(self, query, page_number, page_size, sort_by, sort_ascending) -> PaginatedResultDTO:
        if page_number < 1:
            page_number = 1
        if page_size < 1:
            page_size = 1

        users, total_hits = self.user_repo.search_users_paginated(query, page_number, page_size, sort_by, sort_ascending)
        total_pages = math.ceil(total_hits / page_size)
        users_dto = []
        for user in users:
            u = UserDTO(id=user.id, username=user.username, first_name=user.first_name, bio=user.bio, role=user.role, join_date=user.join_date,
                        last_name=user.last_name, email=user.email, badge=user.badge)
            users_dto.append(u)
        result_info = PaginatedResultInfoDTO(
            page=page_number,
            page_size=page_size,
            total_pages=total_pages,
            total_hits=total_hits
        )
        result = PaginatedResultDTO(hits=users_dto, info=result_info)
        return result

    def update_badge(self, user_id, badge) -> User:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundException(user, user_id)
        user = self.user_repo.update_badge(user, badge)
        repositories = self.repo_repo.get_repositories_for_user(user_id)
        for repo in repositories:
            self.repo_repo.set_attribute(repo, "badge", badge)
        return user


def get_user_service(session: Session = Depends(get_database)) -> UserService:
    return UserService(session)