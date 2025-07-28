import datetime
from typing import List

from pydantic import BaseModel, EmailStr, Field
from app.api.user.user_model import UserRole, UserBadge


class UserDTO(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    join_date: datetime.datetime
    first_name: str | None
    last_name: str | None
    bio: str | None
    badge: UserBadge | None

class UserTokenDTO(BaseModel):
    token: str

class UserRegisterDTO(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserPasswordChangeDTO(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)

class UserLoginDTO(BaseModel):
    username: str
    password: str

class UserBadgeDTO(BaseModel):
    user_id: int
    badge: UserBadge

class UsersResultInfoDTO(BaseModel):
    page: int
    page_size: int
    total_pages: int
    total_hits: int

class UsersResultDTO(BaseModel):
    hits: List[UserDTO]
    info: UsersResultInfoDTO
