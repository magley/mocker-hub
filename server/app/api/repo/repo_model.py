from datetime import datetime, timezone
import enum
from sqlmodel import Field, Relationship, SQLModel

from app.api.org.org_model import Organization
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from app.api.user.user_model import User

class RepositoryBadge(str, enum.Enum):
    none = "none"
    official = "official"
    verified = "verified"
    sponsored_oss = "sponsored_oss"


class Repository(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field()
    """
    Name of the repository.
    """
    canonical_name: str = Field(index=True)
    """
    The canonical name of a repository. Must be unique.
    It is set once during repository creation and **should not change**.

    For official repositories, it is equal to `{name}`.

    For user repositories, it is equal to `{owner.username}/{name}`.

    For organization repositories, it is equal to `{organization.name}/{name}`.
    """
    desc: str = Field(default="")
    public: bool = Field(default=True)

    @property
    def official(self) -> bool:
        return self.badge == RepositoryBadge.official
    """
    Official repositories are created and maintained by administrators.
    """

    owner_id: int = Field(default=None, foreign_key="user.id")
    owner: "User" = Relationship(back_populates="repositories")

    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id")
    organization: Organization = Relationship(back_populates="repositories")

    badge: RepositoryBadge = Field(default=RepositoryBadge.none)

    @staticmethod
    def compute_canonical_name(name: str, user: str, official: bool, org: str | None) -> str:
        if official:
            return f'{name}'
        else:
            if org is not None:
                return f'{org}/{name}'
            else:
                return f'{user}/{name}'
    
    def compute_canonical_name_of(self) -> str:
        org_name = None if self.organization is None else self.organization.name
        return Repository.compute_canonical_name(self.name, self.owner.username, self.official, org_name)