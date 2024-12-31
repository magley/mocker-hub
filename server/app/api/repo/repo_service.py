from typing import List, Optional
from fastapi import Depends
from app.api.config.exception_handler import AccessDeniedException, FieldTakenException, NotFoundException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.repo.repo_model import Repository, RepositoryBadge
from app.api.repo.repo_dto import RepositoryCreateDTO, RepositoryDescUpdateDTO, RepositoryVisibilityUpdateDTO
from app.api.org.org_repo import OrganizationRepo
from app.api.team.team_repo import TeamRepo
from app.api.org.org_model import Organization
from app.api.team.team_model import Team, TeamPermissionKind


class RepositoryService:
    def __init__(self, session: Session):
        self.session = session
        self.repo_repo = RepositoryRepo(session)
        self.user_repo = UserRepo(session)
        self.org_repo = OrganizationRepo(session)
        self.team_repo = TeamRepo(session)


    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
    # Utility methods. Many of these already exist as methods of other services, but we can't
    # use them because of circular dependencies (FastAPI does not support it).

    def _get_all_teams_by_org(self, org_id: int) -> List[Team]:
        teams = self.team_repo.find_all_by_organization(org_id)
        if teams is None:
            raise NotFoundException(List[Team], org_id)
        return teams
    
    def _update_repo_attribute(self, repo: Repository, dto: RepositoryDescUpdateDTO | RepositoryVisibilityUpdateDTO) -> Repository:
        if isinstance(dto, RepositoryDescUpdateDTO):
            repo = self.repo_repo.set_desc(repo, dto.desc)
        elif isinstance(dto, RepositoryVisibilityUpdateDTO):
            repo = self.repo_repo.set_visibility(repo, dto.public)
        return repo

    def _is_user_org_member_with_admin_permissions(self, user_id: int, repo: Repository):
        user_is_organization_member = user_id in [member.user_id for member in repo.organization.members]
        
        if not user_is_organization_member:
            return False

        ''' Find all teams belonging to the organization '''
        teams = self._get_all_teams_by_org(repo.organization_id)

        for team in teams:
            ''' Check if the team has admin permissions for the observed repository '''
            for permission in team.permissions:
                if permission.repo_id == repo.id and permission.kind == TeamPermissionKind.admin:
                    ''' Check if the member belongs to the team '''
                    if user_id in [member.user_id for member in team.members]:
                        return True

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
            if self.user_has_read_access_to_repo(repo, whos_asking_user_id):
                result.append(repo)

        return result
    
    def user_has_read_access_to_repo(self, repo: Repository, user_id: int | None):
        if repo.public:
            return True
        
        # Private repo - signed out users certainly cannot see them.
        if user_id is None:
            return False
        
        repo_is_personal = repo.organization_id is None
        if repo_is_personal:
            # For personal repositories, you must be the owner of the repo.

            if not repo.owner_id == user_id:
                return False
        else:
            # For organization repositories, you must be a member of the same org.

            user_is_in_org = self.org_repo.user_is_in_org(user_id, repo.organization_id)
            if not user_is_in_org:
                return False
            
            # TODO: Teams...

        return True # Just in case :)
    
    def find_by_id(self, repo_id: int) -> Repository:
        repo = self.repo_repo.find_by_id(repo_id)
        if repo is None:
            raise NotFoundException(Repository, repo_id)
        return repo
    
    def update_repo_by_id(self, user_id: int, repo_id: int, dto: RepositoryDescUpdateDTO | RepositoryVisibilityUpdateDTO) -> Repository:
        user_can_make_update = self.user_has_update_permission(user_id, repo_id)
        if not user_can_make_update:
            raise AccessDeniedException(f"User {user_id} cannot update repository with identifier {repo_id}")

        repo = self.find_by_id(repo_id)
        repo = self._update_repo_attribute(repo, dto)
        return repo

    def user_has_update_permission(self, user_id: int | None, repo_id: int) -> bool:
        # Check whether the guest is making request
        if user_id is None:
            return False
        
        repo = self.find_by_id(repo_id)

        # Check whether the owner (admin or user) is making request
        if user_id == repo.owner_id:
            return True
                
        # Check whether the repository belongs to an organization
        if repo.organization is not None:
            # Check whether the repository owner or a team member with admin permissions is making request
            user_is_owner = user_id == repo.organization.owner_id
            if user_is_owner:
                return True
            
            team_privileged_user = self._is_user_org_member_with_admin_permissions(user_id, repo)  
            if user_is_owner or team_privileged_user:
                return True
        
        return False

def get_repo_service(session: Session = Depends(get_database)) -> RepositoryService:
    return RepositoryService(session)