from fastapi import Depends
from sqlmodel import Session
from app.api.user.user_repo import UserRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.org.org_repo import OrganizationRepo
from app.api.team.team_repo import TeamRepo
from typing import List

from app.api.team.team_model import Team, TeamMember, TeamPermission
from app.api.team.team_dto import TeamAddMemberDTO, TeamAddPermissionDTO, TeamCreateDTO
from app.api.user.user_model import User
from app.api.config.exception_handler import AccessDeniedException, NotFoundException, NotInRelationshipException, UserException
from app.api.org.org_model import Organization
from app.api.config.database import get_database
from app.api.repo.repo_model import Repository

class TeamService:
    def __init__(self, session: Session):
        self.session = session
        self.repo_repo = RepositoryRepo(session)
        self.user_repo = UserRepo(session)
        self.org_repo = OrganizationRepo(session)
        self.team_repo = TeamRepo(session)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #
    # Utility methods. Many of these already exist as methods of other services, but we can't
    # use them because of circular dependencies (FastAPI does not support it).

    def _get_org_by_id(self, org_id: int) -> Organization:
        org = self.org_repo.find_by_id(org_id)
        if org is None:
            raise NotFoundException(Organization, org_id)
        return org
    
    def _ensure_user_is_owner_of_org(self, org: Organization, user_id: int):
        if org.owner_id != user_id:
            raise AccessDeniedException(f"You are not the owner of organization {org.name}")
       
    def _ensure_user_is_member_of_org(self, org_id: int, user_id: int):
        if not self.org_repo.user_is_in_org(user_id, org_id):
            raise NotFoundException(User, user_id)
        
    def _ensure_user_exists(self, user_id: int):
        if self.user_repo.find_by_id(user_id) is None:
            raise NotFoundException(User, user_id)
        
    def _get_repo_by_id(self, repo_id: int):
        repo = self.repo_repo.find_by_id(repo_id)
        if repo is None:
            raise NotFoundException(Repository, repo_id)
        return repo
    
    def _ensure_repo_is_part_of_org(self, repo: Repository, org_id: int):
        if repo.organization_id != org_id:
            raise NotInRelationshipException(Organization, org_id, Repository, repo.id)

    # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=- #

    def create_team(self, dto: TeamCreateDTO, user_id: int) -> Team:
        org = self._get_org_by_id(dto.organization_id)
        self._ensure_user_is_owner_of_org(org, user_id)

        new_team = Team.model_validate(dto)
        new_team = self.team_repo.add(new_team)
        return new_team
    
    def get_team(self, team_id: int) -> Team:
        team = self.team_repo.get(team_id)
        if team is None:
            raise NotFoundException(Team, team_id)
        return team
    
    def add_member(self, dto: TeamAddMemberDTO, user_id: int) -> TeamMember:
        existing_membership = self.team_repo.find_member(dto.team_id, dto.user_id)
        if existing_membership is not None:
            return existing_membership
        
        self._ensure_user_exists(dto.user_id)
        team = self.get_team(dto.team_id) 
        self._ensure_user_is_member_of_org(team.organization_id, dto.user_id)
        org = self._get_org_by_id(team.organization_id)
        self._ensure_user_is_owner_of_org(org, user_id)

        return self.team_repo.add_member(dto.team_id, dto.user_id)

    def add_permission(self, dto: TeamAddPermissionDTO, user_id: int) -> TeamPermission:
        existing_permission = self.team_repo.find_permission(dto.team_id, dto.repo_id)
        if existing_permission is not None:
            return existing_permission

        repo = self._get_repo_by_id(dto.repo_id)
        team = self.get_team(dto.team_id)
        self._ensure_repo_is_part_of_org(repo, team.organization_id)
        org = self._get_org_by_id(team.organization_id)
        self._ensure_user_is_owner_of_org(org, user_id)

        return self.team_repo.add_permission(dto.team_id, dto.repo_id, dto.kind)
    
    def find_by_org(self, org_id: int, user_id: int) -> List[Team]:
        """
        Find all teams of the given organization. 
        The user making this request MUST be a member of the organization.
        """

        org = self._get_org_by_id(org_id)
        self._ensure_user_is_member_of_org(org.id, user_id)

        return self.team_repo.find_all_by_organization(org_id)
    

def get_team_service(session: Session = Depends(get_database)) -> TeamService:
    return TeamService(session)