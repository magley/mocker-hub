import datetime
import enum
from sqlmodel import Field, Relationship, SQLModel
from pydantic import EmailStr

from app.api.repo.repo_model import Repository

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True)
    role: UserRole = Field(default=UserRole.user)
    join_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    hashed_password: str
    must_change_password: bool = Field(default=False)

    repositories: list["Repository"] = Relationship(back_populates="owner")