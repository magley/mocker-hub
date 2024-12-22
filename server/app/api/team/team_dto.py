from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, EmailStr, Field
from app.api.user.user_model import UserRole
from app.api.repo.repo_model import RepositoryBadge
from app.api.team.team_model import TeamPermissionKind

class TeamDTOMember(BaseModel):
    id: int
    username: str

class TeamPermissionsDTO(BaseModel):
    team_id: int
    repo_id: int
    kind: TeamPermissionKind

class TeamDTOBasic(BaseModel):
    id: int
    name: str
    desc: str
    organization_id: int | None = None

class TeamDTOFull(TeamDTOBasic):
    members: List[TeamDTOMember]
    permissions: List[TeamPermissionsDTO]

class TeamCreateDTO(BaseModel):
    name: str
    desc: str
    organization_id: int

class TeamAddMemberDTO(BaseModel):
    team_id: int
    user_id: int

class TeamAddPermissionDTO(TeamPermissionsDTO):
    ...