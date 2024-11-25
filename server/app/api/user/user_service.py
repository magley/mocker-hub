from fastapi import Depends
from app.api.config.security import hash_password
from app.api.config.exception_handler import FieldTakenException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.user.user_dto import UserDTO, UserRegisterDTO
from app.api.user.user_model import User
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
        

def get_user_service(session: Session = Depends(get_database)) -> UserService:
    return UserService(session)