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
from app.api.config.exception_handler import AccessDeniedException, NotFoundException, UserException
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

    def create_team(self, dto: TeamCreateDTO, user_id: int) -> Team:
        self._validate_organization_and_creator(dto.organization_id, user_id)

        new_team = Team.model_validate(dto)
        new_team = self.team_repo.add(new_team)
        return new_team
    
    def get_team(self, team_id: int) -> Team | None:
        team = self.team_repo.get(team_id)
        if team is None:
            raise NotFoundException(Team, team_id)
        return team
    
    def add_member(self, dto: TeamAddMemberDTO, user_id: int) -> TeamMember:
        # User is already member of team.

        existing_membership = self.team_repo.find_member(dto.team_id, dto.user_id)
        if existing_membership is not None:
            return existing_membership
        
        # User doesn't exist.

        if self.user_repo.find_by_id(dto.user_id) is None:
            raise NotFoundException(User, dto.user_id)
        
        # Team doesn't exist.

        team = self.get_team(dto.team_id)
        if team is None:
            raise NotFoundException(Team, dto.team_id)
        
        # User is not member of organization.

        if not self.org_repo.user_is_in_org(dto.user_id, team.organization_id):
            raise NotFoundException(User, dto.user_id)
        
        # Only the organization owner can do this.

        self._validate_organization_and_creator(team.organization_id, user_id)

        # Ok.

        return self.team_repo.add_member(dto.team_id, dto.user_id)

    def add_permission(self, dto: TeamAddPermissionDTO, user_id: int) -> TeamPermission:
        # Permission is already defined for this repo for this team.

        existing_permission = self.team_repo.find_permission(dto.team_id, dto.repo_id)
        if existing_permission is not None:
            return existing_permission

        # Repo doesn't exist.

        repo = self.repo_repo.find_by_id(dto.repo_id)
        if repo is None:
            raise NotFoundException(Repository, dto.user_id)
        
        # Team doesn't exist.

        team = self.get_team(dto.team_id)
        if team is None:
            raise NotFoundException(Team, dto.team_id)

        # Repo isn't part of organization.

        if repo.organization_id != team.organization_id:
            raise NotFoundException(Repository, dto.repo_id)
        
        # Only the organization owner can do this.

        self._validate_organization_and_creator(team.organization_id, user_id)

        # Ok.

        return self.team_repo.add_permission(dto.team_id, dto.repo_id, dto.kind)
    
    def _validate_organization_and_creator(self, org_id: int, user_id: int) -> Organization:
        """
        Check if organization exists and the specified user is the owner of the
        organization. Most operations on a `Team` require the user to be the owner
        of the organization

        Returns the `Organization` on success, else it throws an exception.
        """

        # Find organization by ID.

        org = self.org_repo.find_by_id(org_id)
        if org is None:
            raise NotFoundException(Organization, org_id)
        
        # Check if creator of team is the owner of the organization.

        if org.owner_id != user_id:
            raise AccessDeniedException("You are not the owner of this organization.")
        
        return org
    

def get_team_service(session: Session = Depends(get_database)) -> TeamService:
    return TeamService(session)