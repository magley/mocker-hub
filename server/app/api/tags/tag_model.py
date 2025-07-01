from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from app.api.repo.repo_model import Repository
    from app.api.user.user_model import User

class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: Optional[str] = Field(default=None)
    last_push: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    repository_id: int = Field(foreign_key="repository.id", ondelete="CASCADE")
    repository: "Repository" = Relationship(back_populates="tags")

    last_pushed_by_id: int = Field(default=None, foreign_key="user.id")
    last_pushed_by: "User" = Relationship()