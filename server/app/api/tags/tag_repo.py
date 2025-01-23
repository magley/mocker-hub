from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func
from sqlmodel import Session, select
from app.api.repo.repo_model import Repository
from app.api.tags.tag_model import Tag
from app.api.config.pagination import PaginationParams

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
    
    def filter(self, repo_canonical_name: str, search_query: str, params: PaginationParams) -> Tuple[List[Tag], int]:
        """
        Returns a list of tags after filtering and the total number of elements (for pagination).
        """

        # Filter
        query = select(Tag).where(Repository.canonical_name == repo_canonical_name)
        if search_query:
            query = query.where(Tag.name.ilike(f"%{search_query}%"))

        # Count. This must go before order.
        total_count_query = query.with_only_columns(func.count(Tag.id))
        total_count = self.session.exec(total_count_query).all()[0]
 
        # Order
        if params.sort_by:
            if params.sort_by == "name":
                query = query.order_by(Tag.name.asc() if params.sort_order == "asc" else Tag.name.desc())
            elif params.sort_by == "last_push":
                query = query.order_by(Tag.last_push.asc() if params.sort_order == "asc" else Tag.id.desc())

        # Limit
        query = query.offset(params.skip).limit(params.limit)
        tags = self.session.exec(query).all()

        return tags, total_count