from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.api.tags.tag_model import Tag

class TagDTO(BaseModel):
    id: int
    name: Optional[str]  
    last_push: datetime
    last_pushed_by_username : str

    @staticmethod
    def from_tag(tag: Tag) -> "TagDTO":
        return TagDTO(
            id=tag.id,
            name=tag.name,
            last_push=tag.last_push,
            last_pushed_by_username=tag.last_pushed_by.username
        )