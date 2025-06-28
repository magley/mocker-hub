from typing import List, Tuple
from fastapi import Depends
from app.api.config.exception_handler import AccessDeniedException, ConflictException, FieldTakenException, NotFoundException, InvalidInputException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.repo.repo_model import Repository, RepositoryBadge, RepositoryStar
from app.api.repo.repo_dto import RepositoryCreateDTO, RepositoryDescUpdateDTO, RepositoryVisibilityUpdateDTO
from app.api.org.org_repo import OrganizationRepo
from app.api.team.team_repo import TeamRepo
from app.api.access_control.access_control_service import AccessControlService
 
class RepositoryService:
    def __init__(self, session: Session):
        self.session = session
        self.repo_repo = RepositoryRepo(session)
        self.user_repo = UserRepo(session)
        self.org_repo = OrganizationRepo(session)
        self.access_control_service = AccessControlService(session)
        self.team_repo = TeamRepo(session)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
    # Utility methods. Many of these already exist as methods of other services, but we can't
    # use them because of circular dependencies (FastAPI does not support it).
    
    def _update_repo_attribute(self, repo: Repository, dto: RepositoryDescUpdateDTO | RepositoryVisibilityUpdateDTO) -> Repository:
        if dto is None:
            raise InvalidInputException(f"Repository {repo.id} cannot be updated with a None value")
        elif isinstance(dto, RepositoryDescUpdateDTO):
            repo = self.repo_repo.set_desc(repo, dto.desc)
        elif isinstance(dto, RepositoryVisibilityUpdateDTO):
            repo = self.repo_repo.set_visibility(repo, dto.public)
        return repo

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #

    def find_by_canonical_name(self, canonical_name: str) -> Repository:
        repo = self.repo_repo.find_by_canonical_name(canonical_name)
        if repo is None:
            raise NotFoundException(Repository, canonical_name)
        return repo 

    def add(self, user_id: int, dto: RepositoryCreateDTO) -> Repository:
        # Find the User who's creating the repository.

        owner = self.user_repo.find_by_id(user_id)
        if owner is None:
            raise NotFoundException(User, user_id)
        repo_is_official = owner.role == UserRole.admin 

        # Find the organization this repository is created for (if any).

        org_name = None
        if dto.organization_id is not None:
            organization = self.org_repo.find_by_id(dto.organization_id)
            if organization is not None:
                org_name = organization.name

        # Check if user can add repo to this org (if any).

        if org_name is not None:
            if not self.org_repo.user_is_in_org(user_id, dto.organization_id):
                raise AccessDeniedException(f"User {user_id} cannot create repositories in organization {dto.organization_id}")
        
        # Compute the canonical name of the repository.

        canonical_name = Repository.compute_canonical_name(dto.name, owner.username, repo_is_official, org_name)
        if self.repo_repo.find_by_canonical_name(canonical_name):
            raise FieldTakenException("Repository name")
        
        # Determine the badge for this repository.

        badge = RepositoryBadge.none
        if owner.role == UserRole.admin:
            badge = RepositoryBadge.official 

        # Create the new repository.

        new_repo = Repository.model_validate(dto, update={
            "canonical_name": canonical_name,
            "owner_id": owner.id,
            "badge": badge,
        })

        return self.repo_repo.add(new_repo)
    
    def get_repositories_of_user(self, user_id: int, whos_asking_user_id: int | None) -> List[Repository]:
        user_repos = self.repo_repo.get_repositories_for_user(user_id)

        # Filter out repositories which `whos_asking_user_id` cannot see.
        result = []
        for repo in user_repos:
            if self.access_control_service.has_read_access(whos_asking_user_id, repo.id):
                result.append(repo)

        return result
    
    def find_by_id(self, repo_id: int) -> Repository:
        repo = self.repo_repo.find_by_id(repo_id)
        if repo is None:
            raise NotFoundException(Repository, repo_id)
        return repo
    
    def update_repo_by_id(self, repo_id: int, dto: RepositoryDescUpdateDTO | RepositoryVisibilityUpdateDTO | None) -> Repository:
        repo = self.find_by_id(repo_id)
        repo = self._update_repo_attribute(repo, dto)
        return repo
    
    def update_repo_attrs(self, repo_id: int, **kwargs) -> Repository:
        repo = self.find_by_id(repo_id)
        for attr, value in kwargs.items():
            repo = self.repo_repo.set_attribute(repo, attr, value)
        return repo

    def is_repo_starred_by(self, repo: Repository, user: User) -> bool:
        return any(star.repository.id == repo.id for star in user.stars)
    
    def toggle_repo_star(self, user_id: int, repo_id: int) -> Tuple[Repository, bool]:
        repo = self.repo_repo.find_by_id(repo_id)
        if repo is None:
            raise NotFoundException(Repository, repo_id)
        
        user = self.user_repo.find_by_id(user_id)
        if user is None:
            raise NotFoundException(User, user_id)
        
        repo_is_starred = self.is_repo_starred_by(repo, user)

        if repo_is_starred == False:
            new_star = RepositoryStar(starrer_id=user_id, repository_id=repo_id)
            # `True` indicates the repo is now starred
            return self.repo_repo.star_repo(new_star, repo), True

        repo = self.repo_repo.unstar_repo(repo, user)
        
        if repo is None:
            raise ConflictException("The repository star was removed (unstarred) by a different operation")

        # `False` indicates the repo is no longer starred
        return repo, False

    def get_starred_repositories_of_user(self, user_id: int) -> List[Repository]:
        user_repos = self.repo_repo.find_user_starred_repos(user_id)
        return user_repos
    
    def remove_repo(self, repo: Repository) -> None:
        self.repo_repo.remove(repo)
    
def get_repo_service(session: Session = Depends(get_database)) -> RepositoryService:
    return RepositoryService(session)