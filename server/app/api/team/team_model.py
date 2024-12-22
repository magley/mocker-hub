import enum
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.api.org.org_model import Organization
    from app.api.repo.repo_model import Repository
    from app.api.user.user_model import User

class TeamPermissionKind(str, enum.Enum):
    read = "read"
    read_write = "read_write"
    admin = "admin"

class TeamMember(SQLModel, table=True):
    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    team_id: int | None = Field(default=None, foreign_key="team.id", primary_key=True)

    team: "Team" = Relationship(back_populates="members")
    user: "User" = Relationship()

class TeamPermission(SQLModel, table=True):
    team_id: int | None = Field(default=None, foreign_key="team.id", primary_key=True)
    repo_id: int | None = Field(default=None, foreign_key="repository.id", primary_key=True)

    kind: TeamPermissionKind = Field(default=TeamPermissionKind.read)

    team: "Team" = Relationship(back_populates="permissions")
    repo: "Repository" = Relationship()

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    organization: "Organization" = Relationship()

    members: List["TeamMember"] = Relationship(back_populates="team")
    permissions : List["TeamPermission"] = Relationship(back_populates="team")