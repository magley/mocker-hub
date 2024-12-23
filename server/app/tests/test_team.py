from fastapi import Response
from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, patch

from sqlmodel import SQLModel

from app.api.config.exception_handler import AccessDeniedException, NotFoundException, NotInRelationshipException
from app.api.org.org_model import Organization
from app.api.repo.repo_model import Repository
from app.api.team.team_dto import TeamAddMemberDTO, TeamAddPermissionDTO, TeamCreateDTO
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