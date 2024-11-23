from sqlmodel import Session
from app.api.user.user_model import User

class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user