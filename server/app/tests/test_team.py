import pytest
from unittest.mock import MagicMock, patch

from app.api.config.exception_handler import AccessDeniedException, NotFoundException
from app.api.org.org_model import Organization
from app.api.repo.repo_model import Repository
from app.api.team.team_dto import TeamAddMemberDTO, TeamAddPermissionDTO, TeamCreateDTO
from app.api.team.team_model import Team, TeamMember, TeamPermission
from app.api.team.team_service import TeamService
from app.api.user.user_model import User

@pytest.fixture
def team_service():
    service = TeamService(MagicMock())
    
    service.repo_repo = MagicMock()
    service.user_repo = MagicMock()
    service.org_repo = MagicMock()
    service.team_repo = MagicMock()

    return service


class TestCreateTeam:
    def test_create_team_organization_not_found(self, team_service: "TeamService"):
        dto = TeamCreateDTO(organization_id=1, name="New Team", desc="")
        user_id = 1
        
        team_service.org_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            team_service.create_team(dto, user_id)

    def test_create_team_user_is_not_owner(self, team_service: "TeamService"):
        dto = TeamCreateDTO(organization_id=1, name="New Team", desc="")
        user_id = 2
        
        org = Organization(id=1, owner_id=1)
        team_service.org_repo.find_by_id.return_value = org

        with pytest.raises(AccessDeniedException):
            team_service.create_team(dto, user_id)

    def test_create_team_success(self, team_service: "TeamService"):
        dto = TeamCreateDTO(organization_id=1, name="New Team", desc="")
        user_id = 1
        
        org = Organization(id=1, owner_id=1)
        team_service.org_repo.find_by_id.return_value = org
        new_team = Team(id=None, name="New Team", desc="", organization_id=1)
        new_team_with_id = Team(id=1, name="New Team", desc="", organization_id=1)
        team_service.team_repo.add.return_value = new_team_with_id

        result = team_service.create_team(dto, user_id)
        
        assert result == new_team_with_id
        team_service.org_repo.find_by_id.assert_called_once_with(1)
        team_service.team_repo.add.assert_called_once_with(new_team)

class TestGetTeam:
    def test_get_team_not_found(self, team_service: "TeamService"):
        team_id = 1
        team_service.team_repo.get.return_value = None

        with pytest.raises(NotFoundException):
            team_service.get_team(team_id)

    def test_get_team_success(self, team_service: "TeamService"):
        team_id = 1
        expected_team = Team(id=team_id, name="Team A", desc="", organization_id=1)
        team_service.team_repo.get.return_value = expected_team

        result = team_service.get_team(team_id)

        assert result == expected_team
        team_service.team_repo.get.assert_called_once_with(team_id)

class TestFindByOrg:
    def test_find_by_org_org_not_found(self, team_service: "TeamService"):
        org_id = 1
        user_id = 1
        
        team_service.org_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            team_service.find_by_org(org_id, user_id)

    def test_find_by_org_user_not_member(self, team_service: "TeamService"):
        org_id = 1
        user_id = 999  # Invalid user ID
        
        org = Organization(id=org_id, owner_id=1)
        team_service.org_repo.find_by_id.return_value = org
        team_service.org_repo.user_is_in_org.return_value = False
        
        with pytest.raises(NotFoundException):
            team_service.find_by_org(org_id, user_id)

    def test_find_by_org_success(self, team_service: "TeamService"):
        org_id = 1
        user_id = 1
        
        org = Organization(id=org_id, owner_id=1)
        team_service.org_repo.find_by_id.return_value = org
        team_service.org_repo.user_is_in_org.return_value = True

        teams = [
            Team(id=1, name="Team A", desc="", organization_id=org_id),
            Team(id=2, name="Team B", desc="", organization_id=org_id),
        ]
        team_service.team_repo.find_all_by_organization.return_value = teams
        
        result = team_service.find_by_org(org_id, user_id)
        
        assert result == teams
        team_service.org_repo.find_by_id.assert_called_once_with(org_id)
        team_service.org_repo.user_is_in_org.assert_called_once_with(user_id, org_id)
        team_service.team_repo.find_all_by_organization.assert_called_once_with(org_id)

#