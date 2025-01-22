from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from app.api.repo.repo_model import Repository

class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field()
    last_push: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    repository_id: int = Field(foreign_key="repository.id")
    repository: "Repository" = Relationship(back_populates="tags")