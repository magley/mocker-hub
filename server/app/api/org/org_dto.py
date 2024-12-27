from typing import List
from pydantic import BaseModel

class OrganizationCreateDTO(BaseModel):
    name: str
    desc: str
    image: str | None = None

class OrganizationDTOBasic(BaseModel):
    id: int
    name: str
    desc: str
    image: str
    owner_id: int

class OrganizationRepoDTO(BaseModel):
    id: int
    name: str
    canonical_name: str
    desc: str

class OrganizationDTO(BaseModel):
    id: int
    name: str
    desc: str
    image: str
    owner_id: int 
    repositories: List[OrganizationRepoDTO]

class OrganizationHasMemberDTO(BaseModel):
    org_id: int
    user_id: int | None
    is_member: bool