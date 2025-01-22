from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Session, select
from app.api.repo.repo_model import Repository
from app.api.tags.tag_model import Tag

class TagRepo:
    def __init__(self, session: Session):
        self.session = session

    def add(self, tag: Tag) -> Tag:
        self.session.add(tag)
        self.session.commit()
        self.session.refresh(tag)
        return tag
    
    def remove(self, tag: Tag) -> None:
        self.session.delete(tag)
        self.session.commit()

    def find_by_id(self, id: int) -> Optional[Tag]:
        return self.session.get(Tag, id)
    
    def get_all_by_repo_id(self, repo_id: int) -> List[Tag]:
        query = select(Tag).where(Tag.repository_id == repo_id)
        return self.session.exec(query).all()
    
    def get_all_by_repo_name(self, repo_canonical_name: str) -> List[Tag]:
        query = (
            select(Tag)
            .join(Repository, Repository.id == Tag.repository_id)
            .where(Repository.canonical_name == repo_canonical_name)
        )
        return self.session.exec(query).all()

    def find_by_name_and_repo_id(self, name: str, repo_id: int) -> Optional[Tag]:
        return (
            self.session.exec(
                select(Tag).where(Tag.name == name, Tag.repository_id == repo_id)
            ).first()
        )
    
    def update_last_push(self, tag: Tag) -> Tag:
        tag.last_push = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(tag)
        return tag
    
    def find_by_text(self, repo_id: int, text: str) -> List[Tag]:
        query = select(Tag).where(Tag.repository_id == repo_id, Tag.name.ilike(f"%{text}%"))
        return self.session.exec(query).all()