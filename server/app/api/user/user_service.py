from fastapi import Depends
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.user.user_dto import UserDTO
from app.api.user.user_model import User
from app.api.user.user_repo import UserRepo

 
class UserService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepo(session)

    def add(self, dto: UserDTO) -> User:
        user = User.model_validate(dto)
        return self.user_repo.add(user)
        

def get_user_service(session: Session = Depends(get_database)) -> UserService:
    return UserService(session)