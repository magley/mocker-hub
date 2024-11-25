from sqlmodel import Session, select
from app.api.user.user_model import User, UserRole

class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def find_by_email(self, email: str) -> User | None:
        return self.session.exec(select(User).where(User.email == email)).first()
    
    def find_by_username(self, username: str) -> User | None:
        return self.session.exec(select(User).where(User.username == username)).first()
    
    def set_role(self, user: User, role: UserRole) -> User:
        user.sqlmodel_update({"role": role})
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user