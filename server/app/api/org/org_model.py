from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.api.repo.repo_model import Repository
    from app.api.user.user_model import User


class Organization(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    name: str = Field()
    desc: str = Field(default="")
    image: str = Field(default="")

    owner_id: int = Field(default=None, foreign_key="user.id")
    owner: "User" = Relationship()

    repositories: list["Repository"] = Relationship(back_populates="organization", cascade_delete=True)