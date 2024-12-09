import datetime
from pydantic import BaseModel, EmailStr, Field
from app.api.user.user_model import UserRole

class UserDTO(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    join_date: datetime.datetime

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