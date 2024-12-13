from typing import List
from pydantic import BaseModel

class OrganizationCreateDTO(BaseModel):
    name: str
    desc: str
    image: str

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