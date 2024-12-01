from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.api.user.user_model import User

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
    """
    desc: str = Field(default="")
    public: bool = Field(default=True)
    official: bool = Field(default=False)
    """
    Official repositories are created and maintained by administrators.
    """

    owner_id: int = Field(default=None, foreign_key="user.id")
    owner: "User" = Relationship(back_populates="repositories")


    def compute_canonical_name(this) -> str:
        if this.official:
            return f'{this.name}'
        else:
            return f'{this.owner.username}/{this.name}'