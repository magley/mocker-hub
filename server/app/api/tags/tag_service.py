from typing import List
from fastapi import Depends
from app.api.config.exception_handler import AccessDeniedException, NotFoundException, UserException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.repo.repo_model import Repository
from app.api.access_control.access_control_service import AccessControlService
from app.api.repo.repo_repo import RepositoryRepo
from app.api.tags.tag_repo import TagRepo
from app.api.tags.tag_model import Tag

class TagService:
    def __init__(self, session: Session):

        self.session = session
        self.access_control_service = AccessControlService(session)
        self.repo_repo = RepositoryRepo(session)
        self.tag_repo = TagRepo(session)  

    def create_tag(self, user_id: int | None, repo_id: int, tag_name: str) -> Tag:
        # Fetch the repository.

        repo = self.repo_repo.find_by_id(repo_id)
        if not repo:
            raise NotFoundException(Repository, repo_id)
        
        # Access control.
        
        if not self.access_control_service.has_write_access(user_id, repo_id):
            raise AccessDeniedException(f"User {user_id} cannot push tag {tag_name} to repo {repo.canonical_name}")
        
        # Check if tag already exists for the repo.

        existing_tag = self.tag_repo.find_by_name_and_repo_id(tag_name, repo_id)
        if existing_tag:
            raise UserException(f"Tag '{tag_name}' already exists for repository {repo.name}.")

        # Create and add the new tag
        new_tag = Tag(name=tag_name, repository_id=repo.id)
        return self.tag_repo.add(new_tag)

    def remove_tag(self, user_id: int | None, tag_id: int) -> None:
        # Fetch the tag.

        tag = self.tag_repo.find_by_id(tag_id)
        if not tag:
            raise NotFoundException(Tag, tag_id)
        
        # Access control.
        
        if not self.access_control_service.has_write_access(user_id, tag.repository_id):
            raise AccessDeniedException(f"User {user_id} cannot remove tag {tag.name} to repo {tag.repository.canonical_name}")
          
        # Delete the tag.

        self.tag_repo.remove(tag)

    def touch_tag(self, user_id: int | None, tag_id: int) -> None:
        # Fetch the tag.

        tag = self.tag_repo.find_by_id(tag_id)
        if not tag:
            raise NotFoundException(Tag, tag_id)
        
        # Access control.
        
        if not self.access_control_service.has_write_access(user_id, tag.repository_id):
            raise AccessDeniedException(f"User {user_id} cannot remove tag {tag.name} to repo {tag.repository.canonical_name}")
          
        # Touch the tag.

        self.tag_repo.update_last_push(tag)        

    def get_tags_for_repository(self, repo_id: int) -> List[Tag]:
        return self.tag_repo.get_all_by_repo_id(repo_id)

    def get_tags_by_repository_name(self, repo_name: str) -> List[Tag]:
        return self.tag_repo.get_all_by_repo_name(repo_name)
    
    def search_tags(self, repo_id: int, text: str) -> List[Tag]:
        return self.tag_repo.find_by_text(repo_id, text)


def get_tag_service(session: Session = Depends(get_database)) -> TagService:
    return TagService(session)