from typing import List, Tuple

from sqlmodel import Session, select
from app.api.user.user_model import User, UserRole
from sqlalchemy import func

class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    def find_by_id(self, id: int) -> User | None:
        return self.session.get(User, id)
        
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
    
    def flag_password_needs_change(self, user: User) -> User:
        user.sqlmodel_update({"must_change_password": True})
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)  
        return user   
    
    def change_password(self, user: User, new_password_hashed: str) -> User | None:
        user.sqlmodel_update({
            "hashed_password": new_password_hashed, 
            "must_change_password": False
        })
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def search_by_username_prefix(self, query: str, limit: int = 7) -> List[User]:
        return self.session.exec(
            select(User)
            .where(User.username.ilike(f"{query}%"), User.role != UserRole.superadmin)
            .limit(limit)
        ).all()

    def search_users_paginated(self, query: str, page_number: int, page_size: int, sort_by: str, sort_ascending: bool) -> Tuple[List[User], int]:
        filter_condition = User.username.ilike(f"{query}%"), User.role != UserRole.superadmin, User.role != UserRole.admin

        count_query = select(func.count()).where(*filter_condition)
        total_hits = self.session.exec(count_query).one()

        sort_column = getattr(User, sort_by, User.username)
        if not sort_ascending:
            sort_column = sort_column.desc()

        base_query = (
            select(User)
            .where(*filter_condition)
            .order_by(sort_column)
            .offset((page_number - 1) * page_size)
            .limit(page_size)
        )
        users = self.session.exec(base_query).all()
        return users, total_hits
