import datetime
from pydantic import BaseModel, EmailStr, Field
from app.api.user.user_model import UserRole

class RepositoryDTO(BaseModel):
    id: int
    name: str
    canonical_name: str
    desc: str
    public: bool
    official: bool
    owner_id: int
    organization_id: int | None = None


class RepositoryCreateDTO(BaseModel):
    name: str
    desc: str
    public: bool
    organization_id: int | None = None