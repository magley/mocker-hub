import datetime
import enum
from sqlmodel import Field, Relationship, SQLModel
from pydantic import EmailStr

from app.api.repo.repo_model import Repository, RepositoryStar

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    superadmin = "superadmin"


class UserBadge(str, enum.Enum):
    none = "none"
    verified = "verified"
    sponsored_oss = "sponsored_oss"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True)
    role: UserRole = Field(default=UserRole.user)
    join_date: datetime.datetime = Field(default_factory=datetime.datetime.now)
    
    hashed_password: str
    must_change_password: bool = Field(default=False)

    first_name: str | None = Field(default="")
    last_name: str | None = Field(default="")
    bio: str | None = Field(default="")
    badge: UserBadge | None = Field(default=UserBadge.none)

    repositories: list["Repository"] = Relationship(back_populates="owner")
    stars: list["RepositoryStar"] = Relationship(back_populates="starrer")