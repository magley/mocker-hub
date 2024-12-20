from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from app.api.repo.repo_model import Repository
    from app.api.user.user_model import User


class OrganizationMembers(SQLModel, table=True):
    __tablename__ = "organization_members"

    user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    organization_id: int | None = Field(default=None, foreign_key="organization.id", primary_key=True)

    organization: "Organization" = Relationship(back_populates="members")
    user: "User" = Relationship()


class Organization(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    name: str = Field()
    desc: str = Field(default="")
    image: str = Field(default="")
    """
    Path to the image, relative to the internal `/images/` folder.
    """

    owner_id: int = Field(default=None, foreign_key="user.id")
    owner: "User" = Relationship()

    repositories: list["Repository"] = Relationship(back_populates="organization", cascade_delete=True)
    members: List["OrganizationMembers"] = Relationship(back_populates="organization")
