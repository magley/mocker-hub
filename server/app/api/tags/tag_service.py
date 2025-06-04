from typing import List
from fastapi import Depends
from app.api.config.exception_handler import AccessDeniedException, NotFoundException, NotInRelationshipException, UserException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.repo.repo_model import Repository
from app.api.access_control.access_control_service import AccessControlService
from app.api.repo.repo_repo import RepositoryRepo
from app.api.tags.tag_repo import TagRepo
from app.api.tags.tag_model import Tag
from app.api.config.pagination import PaginationParams

class TagService:
    def __init__(self, session: Session):

        self.session = session
        self.access_control_service = AccessControlService(session)
        self.repo_repo = RepositoryRepo(session)
        self.tag_repo = TagRepo(session)  

    def on_push(self, user_id: int | None, repo_id: int, tag_name: str | None) -> Tag:
        """
        #### PRE-CONDITION:
        Tag was pushed onto Distribution.
        This implies that user and repo exist, and 
        the user has been granted access to push tags.

        In other words, this method should never fail
        unless there are issues with the database.
        """
 
        repo = self.repo_repo.find_by_id(repo_id)
        assert repo is not None

        existing_tag = self.tag_repo.find_by_name_and_repo_id(tag_name, repo_id)
        if existing_tag is None:
            new_tag = Tag(name=tag_name, repository_id=repo.id, last_pushed_by_id=user_id)
            return self.tag_repo.add(new_tag)
        else:
            return self.tag_repo.update_last_push(existing_tag, user_id)

    def remove_tag(self, user_id: int | None, tag_id: int) -> None:
        # Fetch the tag.

        tag = self.tag_repo.find_by_id(tag_id)
        if tag is None:
            raise NotFoundException(Tag, tag_id)
        
        # Access control.
        
        if not self.access_control_service.has_write_access(user_id, tag.repository_id):
            raise AccessDeniedException(f"User {user_id} cannot remove tag {tag.name} to repo {tag.repository.canonical_name}")
          
        # Delete the tag.

        self.tag_repo.remove(tag)

    def get_tags_for_repository(self, repo_id: int) -> List[Tag]:
        return self.tag_repo.get_all_by_repo_id(repo_id)

    def get_tags_by_repository_name(self, repo_name: str) -> List[Tag]:
        return self.tag_repo.get_all_by_repo_name(repo_name)
    
    def search_tags(self, repo_id: int, text: str) -> List[Tag]:
        text = text.strip()
        return self.tag_repo.find_by_text(repo_id, text)
    
    def filter(self, repo_name: str, search_query: str, params: PaginationParams) -> tuple[List[Tag], int]:
        """
        Returns list of tags after filtering and total number of tags for pagination.
        """
        search_query = search_query.strip()
        return self.tag_repo.filter(repo_name, search_query, params)
    
    def find_by_name_and_repo_id(self, name: str, repo_id: int) -> Tag:
        tag = self.tag_repo.find_by_name_and_repo_id(name, repo_id)
        if tag is None:
            raise NotInRelationshipException(Repository, repo_id, Tag, name)
        return tag

def get_tag_service(session: Session = Depends(get_database)) -> TagService:
    return TagService(session)