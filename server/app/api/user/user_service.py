from fastapi import Depends
from app.api.config.security import hash_password, verify_password
from app.api.config.exception_handler import FieldTakenException, NotFoundException, UserException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.user.user_dto import UserDTO, UserPasswordChangeDTO, UserRegisterDTO
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
 
class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepo(session)

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
    
    def change_password(self, dto: UserPasswordChangeDTO) -> User:
        user = self.user_repo.find_by_id(dto.id)

        if user is None:
            raise NotFoundException(User, dto.id)
        if not verify_password(dto.old_password, user.hashed_password):
            raise UserException("Current password is incorrect")
        if dto.old_password == dto.new_password:
            raise UserException("New password must be different from the current password")
        
        hashed_password = hash_password(dto.new_password)
        return self.user_repo.change_password(user, hashed_password)

        

def get_user_service(session: Session = Depends(get_database)) -> UserService:
    return UserService(session)