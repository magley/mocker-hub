from unittest import mock

from fastapi import Response
from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, patch

from sqlmodel import SQLModel

from app.api.config.exception_handler import AccessDeniedException, FieldTakenException, NotFoundException, NotInRelationshipException, UserException
from app.api.org.org_model import Organization
from app.api.repo.repo_model import Repository
from app.api.team.team_dto import TeamAddMemberDTO, TeamAddPermissionDTO, TeamCreateDTO, TeamDTOBasic, \
    TeamPermissionsDTO
from app.api.team.team_model import Team, TeamMember, TeamPermission
from app.api.team.team_service import TeamService
from app.api.user.user_model import User
from app.api.main import app


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    from app.api.config.database import engine
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)


@pytest.fixture
def team_service():
    service = TeamService(MagicMock())
    
    service.repo_repo = MagicMock()
    service.user_repo = MagicMock()
    service.org_repo = MagicMock()
    service.team_repo = MagicMock()

    return service


class TestCreateTeam:
    def test_create_team_bad_name(self, team_service: "TeamService"):
        user_id = 1
        dto = TeamCreateDTO(organization_id=1, name=" Starts with whitespace", desc="")
        with pytest.raises(UserException):
            team_service.create_team(dto, user_id)

        dto = TeamCreateDTO(organization_id=1, name="", desc="")
        with pytest.raises(UserException):
            team_service.create_team(dto, user_id)

    def test_create_team_name_already_taken_in_same_org(self, team_service: "TeamService"):
        user_id = 1
        dto1 = TeamCreateDTO(organization_id=1, name="Team01", desc="")  # This team already exists

        team_service.team_repo.find_by_name_in_org.return_value = MagicMock()
        with pytest.raises(FieldTakenException):
            team_service.create_team(dto1, user_id)

    def test_create_team_organization_not_found(self, team_service: "TeamService"):
        dto = TeamCreateDTO(organization_id=1, name="New Team", desc="")
        user_id = 1
        
        team_service.team_repo.find_by_name_in_org.return_value = None
        team_service.org_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            team_service.create_team(dto, user_id)

    def test_create_team_user_is_not_owner(self, team_service: "TeamService"):
        dto = TeamCreateDTO(organization_id=1, name="New Team", desc="")
        user_id = 2
        
        org = Organization(id=1, owner_id=1)
        team_service.team_repo.find_by_name_in_org.return_value = None
        team_service.org_repo.find_by_id.return_value = org

        with pytest.raises(AccessDeniedException):
            team_service.create_team(dto, user_id)

    def test_create_team_success(self, team_service: "TeamService"):
        dto = TeamCreateDTO(organization_id=1, name="New Team", desc="")
        user_id = 1
        
        org = Organization(id=1, owner_id=1)
        team_service.team_repo.find_by_name_in_org.return_value = None
        team_service.org_repo.find_by_id.return_value = org
        new_team = Team(id=None, name="New Team", desc="", organization_id=1)
        new_team_with_id = Team(id=1, name="New Team", desc="", organization_id=1)
        team_service.team_repo.add.return_value = new_team_with_id

        result = team_service.create_team(dto, user_id)
        
        assert result == new_team_with_id
        team_service.org_repo.find_by_id.assert_called_once_with(1)
        team_service.team_repo.add.assert_called_once_with(new_team)

    def test_add_team_integration(self):
        with TestClient(app) as client:
            def add_user(username):
                data = {
                    "username": username,
                    "email": f"{username}@gmail.com",
                    "password": "1234"
                }
                response = client.post("/api/v1/users/", json=data)
                response.json()
            
            def log_in(username):
                data = {
                    "username": username,
                    "password": "1234"
                }
                response = client.post("/api/v1/users/login", json=data)
                jwt = response.json()["token"]
                return jwt
            
            def add_org(username, name: str) -> dict:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                dto1 = {
                    "name": name,
                    "desc": "",
                    "image": None
                }
                return client.post("/api/v1/organizations", json=dto1, headers=header).json()

            def add_team(username: str, org_id: int, name: str, desc: str = "") -> Response:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                dto1 = {
                    "organization_id": org_id,
                    "name": name,
                    "desc": desc,
                }
                return client.post("/api/v1/teams", json=dto1, headers=header)
            
            add_user("u1")
            add_user("u2")

            org1 = add_org("u1", "o1")

            team1 = add_team("u1", org1['id'], 't1')
            team2 = add_team("u1", org1['id'], 't2')
            team3 = add_team("u2", org1['id'], 'will fail because u2 isnt owner of org1')

            assert team1.is_success
            assert team2.json()['name'] == 't2'
            assert not team3.is_success

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

    def test_find_by_org_integration(self):
        with TestClient(app) as client:
            def add_user(username):
                data = {
                    "username": username,
                    "email": f"{username}@gmail.com",
                    "password": "1234"
                }
                response = client.post("/api/v1/users/", json=data)
                return response.json()
            
            def log_in(username):
                data = {
                    "username": username,
                    "password": "1234"
                }
                response = client.post("/api/v1/users/login", json=data)
                jwt = response.json()["token"]
                return jwt
            
            def add_org(username, name: str) -> dict:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                dto1 = {
                    "name": name,
                    "desc": "",
                    "image": None
                }
                return client.post("/api/v1/organizations", json=dto1, headers=header).json()

            def add_user_to_org(username, user_id: int, org_id: int):
                # TODO: Once we implement "add user to org" in the controller, use the proper endpoint for that here.
                from app.api.config.database import engine
                from app.api.org.org_repo import OrganizationRepo
                from app.api.config.database import get_database

                session = next(get_database())
                org_repo = OrganizationRepo(session)
                org_repo.add_user_to_org(org_id, user_id)
                
            def add_team(username: str, org_id: int, name: str, desc: str = "") -> dict:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                dto1 = {
                    "organization_id": org_id,
                    "name": name,
                    "desc": desc,
                }
                return client.post("/api/v1/teams", json=dto1, headers=header).json()
            
            def find_by_org_id(username: str, org_id: int):
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}
                return client.get(f"/api/v1/teams/o/{org_id}", headers=header)

            u1 = add_user("u1") # Org owner
            u2 = add_user("u2") # Org member
            u3 = add_user("u3") # Outsider

            org1 = add_org("u1", "o1")
            add_user_to_org("u1", u2['id'], org1['id'])

            team1 = add_team("u1", org1['id'], 't1')
            team2 = add_team("u1", org1['id'], 't2')

            res1 = find_by_org_id("u1", org1['id'])
            res2 = find_by_org_id("u2", org1['id'])
            res3 = find_by_org_id("u3", org1['id'])

            assert res1.is_success
            assert res1.json() == [team1, team2]
            assert res2.is_success
            assert res2.json() == [team1, team2]
            assert res3.is_error


class TestAddMember:
    def test_add_member_user_already_member(self, team_service: "TeamService"):
        dto = TeamAddMemberDTO(team_id=1, user_id=1)
        user_id = 1
        existing_membership = TeamMember(user_id=1, team_id=1)
        team_service.team_repo.find_member.return_value = existing_membership

        result = team_service.add_member(dto, user_id)

        assert result == existing_membership
        team_service.team_repo.find_member.assert_called_once_with(dto.team_id, dto.user_id)
        team_service.team_repo.add_member.assert_not_called()

    def test_add_member_user_not_found(self, team_service: "TeamService"):
        dto = TeamAddMemberDTO(team_id=1, user_id=999)
        user_id = 1
        team_service.team_repo.find_member.return_value = None
        team_service.user_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            team_service.add_member(dto, user_id)

        team_service.user_repo.find_by_id.assert_called_once_with(dto.user_id)
        team_service.team_repo.find_member.assert_called_once_with(dto.team_id, dto.user_id)
        team_service.team_repo.add_member.assert_not_called()

    def test_add_member_team_not_found(self, team_service: "TeamService"):
        dto = TeamAddMemberDTO(team_id=999, user_id=1)
        user_id = 1
        team_service.team_repo.find_member.return_value = None
        team_service.user_repo.find_by_id.return_value = User(id=1, name="John Doe")
        team_service.team_repo.get.return_value = None

        with pytest.raises(NotFoundException):
            team_service.add_member(dto, user_id)

        team_service.team_repo.find_member.assert_called_once_with(dto.team_id, dto.user_id)
        team_service.team_repo.get.assert_called_once_with(dto.team_id)
        team_service.team_repo.add_member.assert_not_called()

    def test_add_member_user_not_in_org(self, team_service: "TeamService"):
        dto = TeamAddMemberDTO(team_id=1, user_id=2)
        user_id = 1
        org = Organization(id=1, owner_id=1)
        team = Team(id=1, name="Team A", desc="", organization_id=org.id)
        
        team_service.team_repo.find_member.return_value = None
        team_service.user_repo.find_by_id.return_value = User(id=2, name="Jane Doe")
        team_service.org_repo.find_by_id.return_value = org
        team_service.org_repo.user_is_in_org.return_value = False
        team_service.get_team = MagicMock(return_value=team)

        with pytest.raises(NotFoundException):
            team_service.add_member(dto, user_id)

        team_service.org_repo.user_is_in_org.assert_called_once_with(dto.user_id, org.id)
        team_service.team_repo.find_member.assert_called_once_with(dto.team_id, dto.user_id)
        team_service.team_repo.add_member.assert_not_called()

    def test_add_member_org_not_found(self, team_service: "TeamService"):
        dto = TeamAddMemberDTO(team_id=1, user_id=2)
        user_id = 1
        org = Organization(id=1, owner_id=1)
        team = Team(id=1, name="Team A", desc="", organization_id=org.id)
        
        team_service.team_repo.find_member.return_value = None
        team_service.user_repo.find_by_id.return_value = User(id=2, name="Jane Doe")
        team_service.org_repo.find_by_id.return_value = None
        team_service.get_team = MagicMock(return_value=team)

        with pytest.raises(NotFoundException):
            team_service.add_member(dto, user_id)

        team_service.org_repo.find_by_id.assert_called_once_with(dto.team_id)
        team_service.team_repo.find_member.assert_called_once_with(dto.team_id, dto.user_id)
        team_service.team_repo.add_member.assert_not_called()

    def test_add_member_user_not_owner(self, team_service: "TeamService"):
        dto = TeamAddMemberDTO(team_id=1, user_id=2)
        user_id = 3
        org = Organization(id=1, owner_id=1)
        team = Team(id=1, name="Team A", desc="", organization_id=org.id)
        team_service.team_repo.find_member.return_value = None
        team_service.user_repo.find_by_id.return_value = User(id=2, name="Jane Doe")
        team_service.org_repo.find_by_id = MagicMock(return_value=org)
        team_service.org_repo.user_is_in_org.return_value = True
        team_service.get_team = MagicMock(return_value=team)

        with pytest.raises(AccessDeniedException):
            team_service.add_member(dto, user_id)

        team_service.org_repo.user_is_in_org.assert_called_once_with(dto.user_id, org.id)
        team_service.team_repo.find_member.assert_called_once_with(dto.team_id, dto.user_id)
        team_service.team_repo.add_member.assert_not_called()

    def test_add_member_success(self, team_service: "TeamService"):
        dto = TeamAddMemberDTO(team_id=1, user_id=2)
        user_id = 1
        org = Organization(id=1, owner_id=1)
        team = Team(id=1, name="Team A", desc="", organization_id=1)
        team_service.team_repo.find_member.return_value = None
        team_service.user_repo.find_by_id.return_value = User(id=2, name="Jane Doe")
        team_service.org_repo.find_by_id.return_value = org
        team_service.org_repo.user_is_in_org.return_value = True
        new_member = TeamMember(user_id=2, team_id=1)
        team_service.team_repo.add_member = MagicMock(return_value=new_member)
        team_service.get_team = MagicMock(return_value=team)

        result = team_service.add_member(dto, user_id)

        assert result == new_member
        team_service.team_repo.find_member.assert_called_once_with(dto.team_id, dto.user_id)
        team_service.user_repo.find_by_id.assert_called_once_with(dto.user_id)
        team_service.org_repo.user_is_in_org.assert_called_once_with(dto.user_id, team.organization_id)
        team_service.team_repo.add_member.assert_called_once_with(dto.team_id, dto.user_id)

class TestAddPermission:
    def test_add_permission_existing_permission(self, team_service: "TeamService"):
        dto = TeamAddPermissionDTO(team_id=1, repo_id=1, kind="read_write")
        user_id = 1
        
        existing_permission = TeamPermission(team_id=1, repo_id=1, kind="read_write")
        team_service.team_repo.find_permission.return_value = existing_permission

        result = team_service.add_permission(dto, user_id)

        assert result == existing_permission
        team_service.team_repo.find_permission.assert_called_once_with(dto.team_id, dto.repo_id)
        team_service.team_repo.add_permission.assert_not_called()

    def test_add_permission_repo_not_found(self, team_service: "TeamService"):
        dto = TeamAddPermissionDTO(team_id=1, repo_id=999, kind="read_write")
        user_id = 1
        
        team_service.team_repo.find_permission.return_value = None
        team_service.repo_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            team_service.add_permission(dto, user_id)

        team_service.repo_repo.find_by_id.assert_called_once_with(dto.repo_id)
        team_service.team_repo.find_permission.assert_called_once_with(dto.team_id, dto.repo_id)
        team_service.team_repo.add_permission.assert_not_called()

    def test_add_permission_team_not_found(self, team_service: "TeamService"):
        dto = TeamAddPermissionDTO(team_id=999, repo_id=1, kind="read_write")
        user_id = 1
        
        team_service.team_repo.find_permission.return_value = None
        team_service.repo_repo.find_by_id.return_value = Repository(id=1, name="repo1")
        team_service.team_repo.get.return_value = None

        with pytest.raises(NotFoundException):
            team_service.add_permission(dto, user_id)

        team_service.team_repo.find_permission.assert_called_once_with(dto.team_id, dto.repo_id)
        team_service.team_repo.get.assert_called_once_with(dto.team_id)
        team_service.team_repo.add_permission.assert_not_called()

    def test_add_permission_repo_not_part_of_org(self, team_service: "TeamService"):
        dto = TeamAddPermissionDTO(team_id=1, repo_id=1, kind="read_write")
        user_id = 1
        org = Organization(id=1, owner_id=1)
        team = Team(id=1, name="Team A", desc="", organization_id=1)
        repo = Repository(id=1, name="repo1", organization_id=2)
        
        team_service.team_repo.find_permission.return_value = None
        team_service.repo_repo.find_by_id.return_value = repo
        team_service.team_repo.get.return_value = team
        team_service.org_repo.find_by_id.return_value = org

        with pytest.raises(NotInRelationshipException):
            team_service.add_permission(dto, user_id)

        team_service.team_repo.find_permission.assert_called_once_with(dto.team_id, dto.repo_id)
        team_service.repo_repo.find_by_id.assert_called_once_with(dto.repo_id)
        team_service.team_repo.get.assert_called_once_with(dto.team_id)
        team_service.team_repo.add_permission.assert_not_called()

    def test_add_permission_user_not_owner(self, team_service: "TeamService"):
        dto = TeamAddPermissionDTO(team_id=1, repo_id=1, kind="read_write")
        user_id = 2
        org = Organization(id=1, owner_id=1)
        team = Team(id=1, name="Team A", desc="", organization_id=1)
        repo = Repository(id=1, name="repo1", organization_id=1)
        
        team_service.team_repo.find_permission.return_value = None
        team_service.repo_repo.find_by_id.return_value = repo
        team_service.team_repo.get.return_value = team
        team_service.org_repo.find_by_id.return_value = org

        with pytest.raises(AccessDeniedException):
            team_service.add_permission(dto, user_id)

        team_service.team_repo.find_permission.assert_called_once_with(dto.team_id, dto.repo_id)
        team_service.repo_repo.find_by_id.assert_called_once_with(dto.repo_id)
        team_service.team_repo.get.assert_called_once_with(dto.team_id)
        team_service.team_repo.add_permission.assert_not_called()

    def test_add_permission_success(self, team_service: "TeamService"):
        dto = TeamAddPermissionDTO(team_id=1, repo_id=1, kind="read_write")
        user_id = 1
        org = Organization(id=1, owner_id=1)
        team = Team(id=1, name="Team A", desc="", organization_id=1)
        repo = Repository(id=1, name="repo1", organization_id=1)
        
        team_service.team_repo.find_permission.return_value = None
        team_service.repo_repo.find_by_id.return_value = repo
        team_service.team_repo.get.return_value = team
        team_service.org_repo.find_by_id.return_value = org
        team_service.org_repo.user_is_in_org.return_value = True
        new_permission = TeamPermission(team_id=1, repo_id=1, kind="read_write")
        team_service.team_repo.add_permission = MagicMock(return_value=new_permission)

        result = team_service.add_permission(dto, user_id)

        assert result == new_permission
        team_service.team_repo.find_permission.assert_called_once_with(dto.team_id, dto.repo_id)
        team_service.repo_repo.find_by_id.assert_called_once_with(dto.repo_id)
        team_service.team_repo.get.assert_called_once_with(dto.team_id)
        team_service.team_repo.add_permission.assert_called_once_with(dto.team_id, dto.repo_id, dto.kind)


class TestFindMembersOfTeam:
    def test_team_not_found(self, team_service: TeamService):
        team_service.team_repo.get.return_value = None
        with pytest.raises(NotFoundException):
            team_service.find_members_of_team(team_id=1, user_id=2)
        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.find_members_of_team.assert_not_called()

    def test_team_access_denied(self, team_service: TeamService):
        user_id = 1
        team = mock.Mock(spec=Team)
        team_service.team_repo.get.return_value = team
        team_service.team_repo.find_member.return_value = None
        org = mock.Mock(spec=Organization)
        org.owner_id = 99
        team.organization = org

        with pytest.raises(AccessDeniedException):
            team_service.find_members_of_team(team_id=team.id, user_id=user_id)
        team_service.team_repo.get.assert_called_once_with(team.id)
        team_service.team_repo.find_member.assert_called_once()
        team_service.team_repo.find_members_of_team.assert_not_called()

    def test_success_when_user_is_member(self, team_service: TeamService):
        user1 = mock.Mock(spec=User)
        user2 = mock.Mock(spec=User)
        expected_result = [user1, user2]
        team = mock.Mock(spec=Team)
        team_service.team_repo.get.return_value = team
        team_service.team_repo.find_member.return_value = MagicMock()
        team_service.team_repo.find_members_of_team.return_value = [user1, user2]

        result = team_service.find_members_of_team(team_id=1, user_id=2)
        assert result == expected_result
        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.find_member.assert_called_once()
        team_service.team_repo.find_members_of_team.assert_called_once()

    def test_success_when_user_is_org_owner(self, team_service: TeamService):
        user_id = 1
        team = Team(id=1, organization_id=10)
        org = mock.Mock(spec=Organization)
        org.id = 10
        org.owner_id = user_id
        team.organization = org
        expected_user = User(id=2, name="Member")
        team_service.team_repo.get.return_value = team
        team_service.team_repo.find_member.return_value = None
        team_service.team_repo.find_members_of_team.return_value = [expected_user]

        result = team_service.find_members_of_team(team_id=team.id, user_id=user_id)
        assert result == [expected_user]
        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.find_member.assert_called_once()
        team_service.team_repo.find_members_of_team.assert_called_once()

    def test_search_org_members_and_add_them_to_teams_integration(self):
        with TestClient(app) as client:
            # --- Step 1: Create users ---
            def create_user(username: str, email: str) -> dict:
                data = {"username": username, "email": email, "password": "Password123"}
                res = client.post("/api/v1/users", json=data)
                assert res.status_code == 200
                return res.json()

            def add_members_to_org(user_ids: list) -> dict:
                add_members_response = client.post(
                    f"/api/v1/organizations/{org_id}/addMember",
                    json=user_ids,
                    headers=headers
                )
                assert add_members_response.status_code == 200
                return add_members_response.json()

            user1 = create_user("john", "john@mail.com")
            user2 = create_user("josh", "josh@mail.com")
            user3 = create_user("jane", "jane@mail.com")

            create_user("owner", "owner@mail.com")
            owner_auth = client.post("/api/v1/users/login", json={"username": "owner", "password": "Password123"})
            assert owner_auth.status_code == 200
            headers = {"Authorization": f"Bearer {owner_auth.json()['token']}"}

            # --- Step 2: Create organization ---
            org_data = {"name": "OrgWithTeam", "desc": "Testing team integration", "image": None}
            org_res = client.post("/api/v1/organizations", json=org_data, headers=headers)
            assert org_res.status_code == 200
            org_id = org_res.json()["id"]

            # --- Step 3: Create team ---
            team_data = {"name": "DevTeam", "desc": "Core Dev Team", "organization_id": org_id}
            team_res = client.post("/api/v1/teams", json=team_data, headers=headers)
            assert team_res.status_code == 200
            team_id = team_res.json()["id"]

            # --- Step 4: Add users to the organization ---
            user_ids_to_add = [user1["id"], user2["id"], user3["id"]]
            added_members = add_members_to_org(user_ids_to_add)

            # --- Step 4: Search for members to add to the team (excluding current members) ---
            search_res = client.get(f"/api/v1/organizations/search/jo?team_id_to_exclude_members={team_id}", headers=headers)
            assert search_res.status_code == 200
            users_to_add = search_res.json()
            assert len(users_to_add) == 2  # john + josh

            user_ids = [u["id"] for u in users_to_add]

            # --- Step 5: Add them to the team ---
            add_members_res = client.post(f"/api/v1/teams/{team_id}/addMember", json=user_ids, headers=headers)
            assert add_members_res.status_code == 200
            added_members = add_members_res.json()
            assert len(added_members) == 2

            # --- Step 6: Verify team members ---
            get_members_res = client.get(f"/api/v1/teams/{team_id}/members", headers=headers)
            assert get_members_res.status_code == 200
            members = get_members_res.json()
            usernames = [m["username"] for m in members]

            assert "john" in usernames
            assert "josh" in usernames
            assert "jane" not in usernames


class TestGetPermissionsByTeam:
    def test_get_permissions_team_not_found(self, team_service: TeamService):
        team_service.team_repo.get.return_value = None
        with pytest.raises(NotFoundException):
            team_service.get_permissions_by_team(team_id=1, user_id=2)
        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.get_permissions_by_team.assert_not_called()

    def test_get_permissions_team_access_denied(self, team_service: TeamService):
        user_id = 1
        team = mock.Mock(spec=Team)
        team_service.team_repo.get.return_value = team
        team_service.team_repo.find_member.return_value = None
        org = mock.Mock(spec=Organization)
        org.owner_id = 99
        team.organization = org

        with pytest.raises(AccessDeniedException):
            team_service.get_permissions_by_team(team_id=team.id, user_id=user_id)
        team_service.team_repo.get.assert_called_once_with(team.id)
        team_service.team_repo.find_member.assert_called_once()
        team_service.team_repo.get_permissions_by_team.assert_not_called()

    def test_get_permissions_success_when_user_is_member(self, team_service: TeamService):
        user1 = mock.Mock(spec=User)
        user2 = mock.Mock(spec=User)
        expected_result = [user1, user2]
        team = mock.Mock(spec=Team)
        team_service.team_repo.get.return_value = team
        team_service.team_repo.find_member.return_value = MagicMock()
        team_service.team_repo.get_permissions_by_team.return_value = [user1, user2]

        result = team_service.get_permissions_by_team(team_id=1, user_id=2)
        assert result == expected_result
        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.find_member.assert_called_once()
        team_service.team_repo.get_permissions_by_team.assert_called_once()

    def test_get_permissions_success_when_user_is_org_owner(self, team_service: TeamService):
        user_id = 1
        team = Team(id=1, organization_id=10)
        org = mock.Mock(spec=Organization)
        org.id = 10
        org.owner_id = user_id
        team.organization = org
        expected_user = User(id=2, name="Member")
        team_service.team_repo.get.return_value = team
        team_service.team_repo.find_member.return_value = None
        team_service.team_repo.get_permissions_by_team.return_value = [expected_user]

        result = team_service.get_permissions_by_team(team_id=team.id, user_id=user_id)
        assert result == [expected_user]
        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.find_member.assert_called_once()
        team_service.team_repo.get_permissions_by_team.assert_called_once()

    def test_add_get_delete_permission_integration(self):
        with TestClient(app) as client:
            # Step 1: Create user and login
            def create_user(username: str, email: str, password: str = "Password123"):
                response = client.post("/api/v1/users",
                                       json={"username": username, "email": email, "password": password})
                assert response.status_code == 200
                return response.json()

            def login(username: str, password: str = "Password123") -> dict:
                response = client.post("/api/v1/users/login", json={"username": username, "password": password})
                assert response.status_code == 200
                return {"Authorization": f"Bearer {response.json()['token']}"}

            create_user("teamadmin", "teamadmin@mail.com")
            headers = login("teamadmin")

            # Step 2: Create org
            org_data = {"name": "PermOrg", "desc": "Test org for perms", "image": None}
            org_resp = client.post("/api/v1/organizations", json=org_data, headers=headers)
            assert org_resp.status_code == 200
            org_id = org_resp.json()["id"]

            # Step 3: Create repo in org
            repo_data = {
                "name": "Repo1",
                "desc": "Team permission test repo",
                "public": True,
                "organization_id": org_id,
            }
            repo_resp = client.post(f"/api/v1/repositories/", json=repo_data, headers=headers)
            assert repo_resp.status_code == 200
            repo_id = repo_resp.json()["id"]

            # Step 4: Create team
            team_data = {"name": "DevTeam", "desc": "Core Dev Team", "organization_id": org_id}
            team_resp = client.post("/api/v1/teams", json=team_data, headers=headers)
            assert team_resp.status_code == 200
            team_id = team_resp.json()["id"]

            # Step 5: Add permission
            perm_dto = {
                "team_id": team_id,
                "repo_id": repo_id,
                "kind": "read_write"
            }
            perm_add_resp = client.post("/api/v1/teams/permission", json=perm_dto, headers=headers)
            assert perm_add_resp.status_code == 200

            # Step 6: Get permissions and verify
            perm_list_resp = client.get(f"/api/v1/teams/{team_id}/permissions", headers=headers)
            assert perm_list_resp.status_code == 200
            permissions = perm_list_resp.json()
            assert any(p["repo_id"] == repo_id and p["kind"] == "read_write" for p in permissions)

            # Step 7: Delete permission
            perm_del_resp = client.request("DELETE", "/api/v1/teams/permission", json=perm_dto, headers=headers)
            assert perm_del_resp.status_code == 202

            # Step 8: Get permissions again to verify deletion
            perm_list_resp_2 = client.get(f"/api/v1/teams/{team_id}/permissions", headers=headers)
            assert perm_list_resp_2.status_code == 200
            permissions_after = perm_list_resp_2.json()
            assert not any(p["repo_id"] == repo_id for p in permissions_after)


class TestUpdateTeam:
    def test_update_team_not_found(self, team_service: "TeamService"):
        team_service.team_repo.get.return_value = None
        dto = mock.Mock(spec=TeamDTOBasic)
        dto.id = 1
        with pytest.raises(NotFoundException):
            team_service.update_team(dto, user_id=2)
        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.add.assert_not_called()

    def test_update_team_success(self, team_service: "TeamService"):
        dto = TeamDTOBasic(id=1, organization_id=1, name="New Team", desc="")
        old_team = Team(id=1, name="Old Team", desc="", organization_id=1)
        excpected_team = Team(id=1, name="New Team", desc="", organization_id=1)
        user_id = 1

        org = Organization(id=1, owner_id=1)
        team_service.team_repo.get.return_value = old_team
        team_service.team_repo.find_by_name_in_org.return_value = None
        team_service.org_repo.find_by_id.return_value = org
        team_service.team_repo.add.return_value = excpected_team

        result = team_service.update_team(dto, user_id)

        assert result == excpected_team
        team_service.org_repo.find_by_id.assert_called_once_with(1)
        team_service.team_repo.add.assert_called_once_with(excpected_team)

        # All other cases have been covered with the create_team tests, so we don't need to repeat them here.

    def test_update_team_integration(self):
        client = TestClient(app)

        # Step 1: Create user and login
        def create_user(username, email, password="Password123"):
            res = client.post("/api/v1/users", json={"username": username, "email": email, "password": password})
            assert res.status_code == 200
            return res.json()

        def login(username, password="Password123"):
            res = client.post("/api/v1/users/login", json={"username": username, "password": password})
            assert res.status_code == 200
            token = res.json()["token"]
            return {"Authorization": f"Bearer {token}"}

        create_user("teamuser", "teamuser@example.com")
        headers = login("teamuser")

        # Step 2: Create organization
        org_data = {"name": "TestOrg", "desc": "Org for testing", "image": None}
        org_res = client.post("/api/v1/organizations", json=org_data, headers=headers)
        assert org_res.status_code == 200
        org_id = org_res.json()["id"]

        # Step 3: Create team
        team_data = {"name": "Initial Team", "desc": "Initial description", "organization_id": org_id}
        team_res = client.post("/api/v1/teams", json=team_data, headers=headers)
        assert team_res.status_code == 200
        team = team_res.json()
        team_id = team["id"]

        # Step 4: Update team
        updated_team_data = {"id": team_id, "name": "Updated Team", "desc": "Updated description"}
        update_res = client.put("/api/v1/teams", json=updated_team_data, headers=headers)
        assert update_res.status_code == 200

        # Step 5: Confirm update
        get_res = client.get(f"/api/v1/teams/o/{org_id}", headers=headers)
        assert get_res.status_code == 200
        team_after_update = get_res.json()[0]
        assert team_after_update["name"] == "Updated Team"
        assert team_after_update["desc"] == "Updated description"


class TestDeletePermission:
    def test_delete_permission_not_found(self, team_service: "TeamService"):
        team_service.team_repo.find_permission.return_value = None
        dto = TeamPermissionsDTO(team_id=1, repo_id=1, kind="read_write")
        with pytest.raises(NotFoundException):
            team_service.delete_team_permission(dto, user_id=2)
        team_service.team_repo.find_permission.assert_called_once()
        team_service.team_repo.add.assert_not_called()

    def test_delete_permission_access_denied(self, team_service: TeamService):
        dto = TeamPermissionsDTO(team_id=1, repo_id=1, kind="read_write")
        team = mock.Mock(spec=Team)
        team.id = dto.team_id
        permission = TeamPermission(team_id=dto.team_id, repo_id=dto.repo_id, kind=dto.kind)
        org = mock.Mock(spec=Organization)

        org.owner_id = 99
        team.organization = org
        team_service.team_repo.find_permission.return_value = permission
        team_service.team_repo.get.return_value = team

        with pytest.raises(AccessDeniedException):
            team_service.delete_team_permission(dto, user_id=1)
        team_service.team_repo.get.assert_called_once()
        team_service.team_repo.delete_team_permission.assert_not_called()

    def test_delete_permission_success(self, team_service: "TeamService"):
        dto = TeamPermissionsDTO(team_id=1, repo_id=1, kind="read_write")
        team = mock.Mock(spec=Team)
        team.id = dto.team_id
        permission = TeamPermission(team_id=dto.team_id, repo_id=dto.repo_id, kind=dto.kind)
        org = mock.Mock(spec=Organization)

        org.owner_id = 1
        team.organization = org
        team_service.team_repo.find_permission.return_value = permission
        team_service.team_repo.get.return_value = team

        team_service.delete_team_permission(dto, 1)

        team_service.team_repo.get.assert_called_once()
        team_service.team_repo.delete_permission.assert_called_once()

class TestRemoveTeamMember:
    def test_remove_team_member_not_found(self, team_service: "TeamService"):
        team_service.team_repo.find_member.return_value = None

        with pytest.raises(NotFoundException):
            team_service.remove_team_member(member_id=42, team_id=1, user_id=10)

        team_service.team_repo.find_member.assert_called_once_with(1, 42)
        team_service.team_repo.get.assert_not_called()
        team_service.team_repo.delete_team_member.assert_not_called()

    def test_remove_team_member_access_denied(self, team_service: "TeamService"):
        tm = mock.Mock()
        team = mock.Mock(spec=Team)
        org = mock.Mock(spec=Organization)
        org.owner_id = 999
        team.organization = org

        team_service.team_repo.find_member.return_value = tm
        team_service.team_repo.get.return_value = team

        with pytest.raises(AccessDeniedException):
            team_service.remove_team_member(member_id=42, team_id=1, user_id=123)

        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.delete_team_member.assert_not_called()

    def test_remove_team_member_success(self, team_service: "TeamService"):
        tm = mock.Mock()
        team = mock.Mock(spec=Team)
        org = mock.Mock(spec=Organization)
        org.owner_id = 123
        team.organization = org

        team_service.team_repo.find_member.return_value = tm
        team_service.team_repo.get.return_value = team

        team_service.remove_team_member(member_id=42, team_id=1, user_id=123)

        team_service.team_repo.get.assert_called_once_with(1)
        team_service.team_repo.delete_team_member.assert_called_once_with(tm)
