from sqlmodel import Session
from app.api.user.user_repo import UserRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.org.org_repo import OrganizationRepo
from app.api.team.team_repo import TeamRepo
from typing import List

from app.api.team.team_model import Team, TeamMember, TeamPermission
from app.api.team.team_dto import TeamAddMemberDTO, TeamAddPermissionDTO, TeamCreateDTO
from app.api.user.user_model import User
from app.api.config.exception_handler import AccessDeniedException, NotFoundException
from app.api.org.org_model import Organization

class TeamService:
    def __init__(self, session: Session):
        self.session = session
        self.repo_repo = RepositoryRepo(session)
        self.user_repo = UserRepo(session)
        self.org_repo = OrganizationRepo(session)
        self.team_repo = TeamRepo(session)

    def create_team(self, dto: TeamCreateDTO, user: User) -> Team:
        self._validate_organization_and_user(dto.organization_id, user)

        new_team = Team.model_validate(dto)
        new_team = self.team_repo.add(new_team)
        return new_team
    
    def get_team(self, team_id: int) -> Team | None:
        team = self.team_repo.get(team_id)
        if team is None:
            raise NotFoundException(Team, team_id)
        return team
    
    def add_member(self, dto: TeamAddMemberDTO, user: User) -> TeamMember:
        team = self.get_team(dto.team_id)
        self._validate_organization_and_user(team.organization_id, user)

        return self.team_repo.add_member(dto.team_id, dto.user_id)

    def add_permission(self, dto: TeamAddPermissionDTO, user: User) -> TeamPermission:
        team = self.get_team(dto.team_id)
        self._validate_organization_and_user(team.organization_id, user)
        
        return self.team_repo.add_permission(dto.team_id, dto.repo_id, dto.kind)
    
    def _validate_organization_and_user(self, org_id: int, user: User) -> Organization:
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

        if org.owner_id != user.id:
            raise AccessDeniedException("You are not the owner of this organization.")
        
        return user