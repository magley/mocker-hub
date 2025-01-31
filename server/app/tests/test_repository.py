from fastapi import Response
from fastapi.testclient import TestClient
import pytest
import unittest.mock as mock
from typing import Callable

from sqlmodel import SQLModel, Session

from app.api.config.security import hash_password
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.user.user_service import UserService
from app.api.config.exception_handler import InvalidInputException, FieldTakenException, NotFoundException
from app.api.repo.repo_repo import RepositoryRepo
from app.api.repo.repo_service import RepositoryService
from app.api.repo.repo_dto import RepositoryCreateDTO, RepositoryDescUpdateDTO, RepositoryVisibilityUpdateDTO
from app.api.repo.repo_model import Repository, RepositoryBadge, RepositoryStar
from app.api.main import app
from app.api.org.org_repo import OrganizationRepo
from app.api.org.org_model import OrganizationMembers
from app.api.team.team_model import TeamMember, TeamPermission, TeamPermissionKind
from app.api.team.team_repo import TeamRepo
from app.api.access_control.access_control_service import AccessControlService

@pytest.fixture
def mock_session():
    return mock.MagicMock(spec=Session)

@pytest.fixture
def mock_user_repo():
    return mock.MagicMock(spec=UserRepo)

@pytest.fixture
def mock_repo_repo():
    return mock.MagicMock(spec=RepositoryRepo)

@pytest.fixture
def mock_org_repo():
    return mock.MagicMock(spec=OrganizationRepo)

@pytest.fixture
def mock_team_repo():
    return mock.MagicMock(spec=TeamRepo)

@pytest.fixture
def user_service(mock_session, mock_user_repo):
    service = UserService(mock_session)
    service.user_repo = mock_user_repo
    return service

@pytest.fixture
def repo_service(mock_session):
    service = RepositoryService(mock_session)
    service.repo_repo = mock.MagicMock(spec=RepositoryRepo)
    service.user_repo = mock.MagicMock(spec=UserRepo)
    service.org_repo = mock.MagicMock(spec=OrganizationRepo)
    service.team_repo = mock.MagicMock(spec=TeamRepo)
    service.access_control_service = mock.MagicMock(spec=AccessControlService)
    return service

@pytest.fixture
def mock_repo():
    return mock.MagicMock(Repository)


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    from app.api.config.database import engine
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
    

def create_mock_user(id: int, username: str, role: UserRole):
    return User(id=id, email=f"username@email.com", username=username, role=role, hashed_password=hash_password("1234"))


def test_add_repo(repo_service):
    user1 = create_mock_user(1, "user1", UserRole.user)

    repo_service.user_repo.find_by_id.return_value = user1
    repo_service.repo_repo.find_by_canonical_name.return_value = None

    dto = RepositoryCreateDTO(
        name="Some repo",
        desc="",
        public=True,
        organization_id=None
    )

    repo_result = repo_service.add(user1.id, dto)

    assert repo_result.id is not None


def test_add_repo__no_user(repo_service):
    repo_service.user_repo.find_by_id.return_value = None
    dto = RepositoryCreateDTO(
        name="Some repo",
        desc="",
        public=True,
        organization_id=None
    )

    with pytest.raises(NotFoundException) as e:
        repo_service.add(1, dto)
    
    assert e.value.entity_type == User
    assert e.value.identifier == 1


def test_add_repo__repo_name(repo_service):
    user1 = create_mock_user(1, "user1", UserRole.user)
    user2 = create_mock_user(2, "user2", UserRole.user)
    user3 = create_mock_user(2, "user3", UserRole.admin)

    def get_user_mocked(id: int):
        return [ user1, user2, user3][id - 1]
    repo_service.user_repo.find_by_id.side_effect = get_user_mocked
    
    def get_repo_mocked(canonical_name: str):
        repos = {
            "user1/python": Repository(),
            "user2/node": Repository(),
            "python": Repository(),
        }
        return repos.get(canonical_name, None)
    repo_service.repo_repo.find_by_canonical_name.side_effect = get_repo_mocked

    # [1] Trying to create "user1/python".

    dto = RepositoryCreateDTO(
        name="python",
        desc="",
        public=True,
        organization_id=None
    )

    with pytest.raises(FieldTakenException) as e:
        repo_service.add(1, dto)

    # [2] Trying to create "user2/python".

    dto = RepositoryCreateDTO(
        name="python",
        desc="",
        public=True,
        organization_id=None
    )

    repo_res = repo_service.add(2, dto)

    assert repo_res is not None

    # [3] Trying to create "python"
    # user is admin, so repo is official.

    dto = RepositoryCreateDTO(
        name="python",
        desc="",
        public=True,
        organization_id=None
    )

    with pytest.raises(FieldTakenException) as e:
        repo_service.add(3, dto)


def test_add___integration():
    with TestClient(app) as client:
        data = {
            "username": "u1",
            "email": "u1@gmail.com",
            "password": "1234"
        }
        response = client.post("/api/v1/users/", json=data)
        created_user = response.json()

        data = {
            "username": "u1",
            "password": "1234"
        }
        response = client.post("/api/v1/users/login", json=data)
        jwt = response.json()["token"]

        header = {
            "Authorization": f"Bearer {jwt}"
        }

        data = {
            "name": "python",
            "desc": "",
            "public": True,
            "organization_id": None,
        }

        response = client.post("/api/v1/repositories/", json=data, headers=header)
        created_repo = response.json()

        assert created_repo['canonical_name'] == f'u1/python'
        assert created_repo['badge'] == RepositoryBadge.none

        response = client.post("/api/v1/repositories/", json=data)
        assert response.is_client_error

        
def test_find_by_canonical_name_success(repo_service):
    """Test case for when the repository is found."""
    canonical_name = "user1/python"
    expected_repo = mock.MagicMock(Repository)
    
    repo_service.repo_repo.find_by_canonical_name.return_value = expected_repo
    
    result = repo_service.find_by_canonical_name(canonical_name)
    
    assert result == expected_repo
    repo_service.repo_repo.find_by_canonical_name.assert_called_once_with(canonical_name)


def test_find_by_canonical_name_not_found(repo_service):
    """Test case for when the repository is not found."""
    canonical_name = "user7438437/python"
    
    repo_service.repo_repo.find_by_canonical_name.return_value = None
    
    with pytest.raises(NotFoundException):
        repo_service.find_by_canonical_name(canonical_name)
    
    repo_service.repo_repo.find_by_canonical_name.assert_called_once_with(canonical_name)


def test_get_repositories_of_user_all_accessible(repo_service):
    """Test case for when all repositories are accessible by whos_asking_user_id."""
    user_id = 1
    whos_asking_user_id = 2

    mock_repo = mock.MagicMock(Repository)
    mock_repo.id = 1

    repo_service.repo_repo.get_repositories_for_user.return_value = [mock_repo, mock_repo]
    repo_service.access_control_service.has_read_access.return_value = True

    result = repo_service.get_repositories_of_user(user_id, whos_asking_user_id)

    assert len(result) == 2
    assert result == [mock_repo, mock_repo]
    repo_service.repo_repo.get_repositories_for_user.assert_called_once_with(user_id)
    repo_service.access_control_service.has_read_access.assert_any_call(whos_asking_user_id, mock_repo.id)


def test_get_repositories_of_user_some_accessible(repo_service):
    """Test case for when some repositories are not accessible by whos_asking_user_id."""
    user_id = 1
    whos_asking_user_id = 2

    repo1 = mock.MagicMock(Repository)
    repo1.id = 1
    
    repo2 = mock.MagicMock(Repository)
    repo2.id = 2

    repo_service.repo_repo.get_repositories_for_user.return_value = [repo1, repo2]
    repo_service.access_control_service.has_read_access = mock.MagicMock(side_effect=[True, False])

    result = repo_service.get_repositories_of_user(user_id, whos_asking_user_id)

    assert len(result) == 1
    assert result == [repo1]
    repo_service.repo_repo.get_repositories_for_user.assert_called_once_with(user_id)
    repo_service.access_control_service.has_read_access.assert_any_call(whos_asking_user_id, repo1.id)
    repo_service.access_control_service.has_read_access.assert_any_call(whos_asking_user_id, repo2.id)


def test_get_repositories_of_user_no_repositories(repo_service):
    """Test case for when there are no repositories returned for the user."""
    user_id = 1
    whos_asking_user_id = 2

    repo_service.repo_repo.get_repositories_for_user.return_value = []

    result = repo_service.get_repositories_of_user(user_id, whos_asking_user_id)

    assert result == []
    repo_service.repo_repo.get_repositories_for_user.assert_called_once_with(user_id)


def test_get_repositories_of_user___integration():
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

        def add_repo(username, name: str, public: bool, org_id: int | None) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            data = {
                "name": name,
                "desc": "",
                "public": public,
                "organization_id": org_id,
            }

            response = client.post("/api/v1/repositories/", json=data, headers=header)
            return response.json()
        
        def get_repos(username: str | None, of_user: str) -> dict:
            if username is not None:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                response = client.get(f"/api/v1/repositories/u/{of_user}", headers=header)
                return response.json()
            else:
                response = client.get(f"/api/v1/repositories/u/{of_user}")
                return response.json()

        
        add_user("u1")
        add_user("u2")
        add_user("u3")
        add_user("u4")

        org1 = add_org("u1", "o1")
        org2 = add_org("u2", "o2")

        add_repo("u1", "u1_public", True, None)
        add_repo("u1", "u1_private", False, None)
        add_repo("u1", "o1_public", True, org1["id"])
        add_repo("u1", "o1_private", False, org1["id"])

        add_repo("u2", "u2_private", False, None)

        assert len(get_repos("u1", "u1")["repos"]) == 4
        assert len(get_repos("u2", "u1")["repos"]) == 2
        assert len(get_repos(None, "u1")["repos"]) == 2
        assert len(get_repos("u1", "u2")["repos"]) == 0
        assert len(get_repos("u2", "u2")["repos"]) == 1


def test_get_repo_by_canonical_name___integration():
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

        def add_repo(username, name: str, public: bool, org_id: int | None) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            data = {
                "name": name,
                "desc": "",
                "public": public,
                "organization_id": org_id,
            }

            response = client.post("/api/v1/repositories/", json=data, headers=header)
            return response.json()
        
        def get_repo_by_canonical_name(username: str | None, repo_canonical_name: str):
            if username is not None:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                response = client.get(f"/api/v1/repositories/name/{repo_canonical_name}", headers=header)
                return response
            else:
                response = client.get(f"/api/v1/repositories/name/{repo_canonical_name}")
                return response

        
        add_user("u1")
        add_user("u2")
        add_user("u3")
        add_user("u4")

        org1 = add_org("u1", "o1")
        org2 = add_org("u2", "o2")

        add_repo("u1", "u1_public", True, None)
        add_repo("u1", "u1_private", False, None)
        add_repo("u1", "o1_public", True, org1["id"])
        add_repo("u1", "o1_private", False, org1["id"])

        add_repo("u2", "u2_private", False, None)

        assert get_repo_by_canonical_name("u1", "u1/u1_public").is_success
        assert get_repo_by_canonical_name("u1", "u1/u1_private").is_success
        assert get_repo_by_canonical_name("u1", "o1/o1_public").is_success
        assert get_repo_by_canonical_name("u1", "o1/o1_private").is_success
        assert get_repo_by_canonical_name("u1", "u1/o1_public").status_code == 404
        assert get_repo_by_canonical_name("u1", "u1/o1_private").status_code == 404
        assert get_repo_by_canonical_name("u1", "u2/u2_private").status_code == 404

        assert get_repo_by_canonical_name("u2", "u1/u1_public").is_success
        assert get_repo_by_canonical_name("u2", "u1/u1_private").status_code == 404
        assert get_repo_by_canonical_name("u2", "o1/o1_public").is_success
        assert get_repo_by_canonical_name("u2", "o1/o1_private").status_code == 404
        assert get_repo_by_canonical_name("u2", "u1/o1_public").status_code == 404
        assert get_repo_by_canonical_name("u2", "u1/o1_private").status_code == 404
        assert get_repo_by_canonical_name("u2", "u2/u2_private").is_success

@pytest.mark.parametrize(
    "dto_class, a_name, a_value", [
    (None, None, None), 
    (RepositoryDescUpdateDTO, "desc", "Some repo desc"), 
    (RepositoryVisibilityUpdateDTO, "public", True)
])
class TestUpdateRepoById:

    def test_update_when_missing_repo(self, repo_service, dto_class, a_name, a_value):
        """
            Test case for when the user is requesting an update for a missing repository.
        """   
        repo_id = 1
        repo_service.repo_repo.find_by_id.return_value = None
        dto = dto_class(**{a_name: a_value}) if dto_class is not None else None

        with pytest.raises(NotFoundException):
            repo_service.update_repo_by_id(repo_id, dto)
        
        repo_service.repo_repo.find_by_id.assert_called_once_with(repo_id)

        if a_name == "desc":
            repo_service.repo_repo.set_desc.assert_not_called()
        elif a_name == "public": 
            repo_service.repo_repo.set_visibility.assert_not_called()
        else:
            repo_service.repo_repo.set_desc.assert_not_called()
            repo_service.repo_repo.set_visibility.assert_not_called()

    def test_update_by_eligible_user(self, mock_repo, repo_service, dto_class, a_name, a_value):
        """
            Test case for when the user is eligible to make an update.        
        """   
        repo_id = 1
        dto = dto_class(**{a_name: a_value}) if dto_class is not None else None

        repo_service.repo_repo.find_by_id.return_value = mock_repo
        if a_name == "desc":
            repo_service.repo_repo.set_desc.return_value = mock_repo
        elif a_name == "public": 
            repo_service.repo_repo.set_visibility.return_value = mock_repo

        if a_name == None:
            with pytest.raises(InvalidInputException):
                repo_service.update_repo_by_id(repo_id, dto)
        else:
            result = repo_service.update_repo_by_id(repo_id, dto)
            assert result == mock_repo

        repo_service.repo_repo.find_by_id.assert_called_once_with(repo_id)

        if a_name == "desc":
            repo_service.repo_repo.set_desc.assert_called_once_with(mock_repo, dto.desc)
        elif a_name == "public": 
            repo_service.repo_repo.set_visibility.assert_called_once_with(mock_repo, dto.public)
        else:
            repo_service.repo_repo.set_desc.assert_not_called()
            repo_service.repo_repo.set_visibility.assert_not_called()

@pytest.mark.parametrize(
    "user_type, update_type", [
    ("user", "desc"), 
    ("user", "visibility"), 
    ("admin", "desc"), 
    ("admin", "visibility")
])
def test_update_repo_by_id___integration(user_type, update_type):
    with TestClient(app) as client:
        def add_user(username):
            data = {
                "username": username,
                "email": f"{username}@gmail.com",
                "password": "12345678"
            }
            response = client.post("/api/v1/users/", json=data)
            return response.json()
        
        def log_in(username: str, password: str = "12345678"):
            data = {
                "username": username,
                "password": password
            }
            response = client.post("/api/v1/users/login", json=data)
            if response.status_code == 400:
                assert response.json() == False
            jwt = response.json()["token"]
            return jwt
        
        def change_superadmin_password():
            # [1] Loading the super admin credentials
            config_file = "./volume-server-cfg/superadmin_password.txt"

            with open(config_file, "r") as f:
                old_password = f.readline()

            jwt = log_in("admin", old_password)
            header = {"Authorization": f"Bearer {jwt}"}

            # [2] Changing the super admin password
            data = {
                "old_password": old_password,
                "new_password": "12345678"
            }
            response = client.post("/api/v1/users/password", json=data, headers=header)
            assert response.is_success
        
        def add_admin(admin_username: str) -> dict:
            jwt = log_in("admin", "12345678")
            header = {"Authorization": f"Bearer {jwt}"}
            data = {
                "username": admin_username,
                "email": f"{admin_username}@gmail.com",
                "password": "12345678"
            }
            response = client.post("/api/v1/users/register-admin", json=data, headers=header)
            created_admin = response.json()

            return created_admin

        def add_org(username, name: str) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            dto1 = {
                "name": name,
                "desc": "",
                "image": None
            }
            return client.post("/api/v1/organizations", json=dto1, headers=header).json()

        def add_user_to_org(user_id: int, org_id: int) -> OrganizationMembers:
            # TODO: Once we implement "add user to org" in the controller, use the proper endpoint for that here.
            from app.api.config.database import engine
            from app.api.org.org_repo import OrganizationRepo
            from app.api.config.database import get_database

            session = next(get_database())
            org_repo = OrganizationRepo(session)
            return org_repo.add_user_to_org(org_id, user_id)

        def add_repo(username, name: str, public: bool, org_id: int | None) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            data = {
                "name": name,
                "desc": "",
                "public": public,
                "organization_id": org_id,
            }

            response = client.post("/api/v1/repositories/", json=data, headers=header)
            return response.json()
        
        def add_team(username: str, org_id: int, name: str, desc: str = "") -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            dto1 = {
                "organization_id": org_id,
                "name": name,
                "desc": desc,
            }
            return client.post("/api/v1/teams", json=dto1, headers=header).json()

        def add_team_member(user_id: int, team_id: int) -> TeamMember:
            # TODO: Once we implement "add team_member" in the controller, use the proper endpoint for that here.
            from app.api.team.team_repo import TeamRepo
            from app.api.config.database import get_database

            session = next(get_database())
            team_repo = TeamRepo(session)
            return team_repo.add_member(team_id, user_id)
        
        def add_team_permission(team_id: int, repo_id: int, kind: TeamPermissionKind) -> TeamPermission:
            # TODO: Once we implement "add_team_permission" in the controller, use the proper endpoint for that here.
            from app.api.team.team_repo import TeamRepo
            from app.api.config.database import get_database

            session = next(get_database())
            team_repo = TeamRepo(session)
            return team_repo.add_permission(team_id, repo_id, kind)

        def update_repo_desc_by_id(username: str, repo_id: int, desc: str):
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}
            
            data = {
                "desc": desc
            }

            response = client.put(f"/api/v1/repositories/{repo_id}/desc", json=data, headers=header)
            return response

        def update_repo_visibility_by_id(username: str, repo_id: int, public: bool):
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}
            
            data = {
                "public": public
            }

            response = client.put(f"/api/v1/repositories/{repo_id}/visibility", json=data, headers=header)
            return response

        def get_fun(update_type: str) -> Callable[[str, int, str | bool], Response]:
            if update_type == "desc":
                return update_repo_desc_by_id
            else:
                return update_repo_visibility_by_id

        if (user_type == "user"):
            add_user("user_1")
            user_2 = add_user("user_2")
        else:
            change_superadmin_password()
            add_admin("user_1")
            user_2 = add_admin("user_2")

        organization_1 = add_org("user_1", "organization_1")
        organization_2 = add_org("user_2", "organization_2")
        repo_1 = add_repo("user_1", "repo_1", True, organization_1["id"])
        repo_2 = add_repo("user_1", "repo_2", True, organization_1["id"])
        repo_3 = add_repo("user_1", "repo_3", True, organization_1["id"])
        repo_4 = add_repo("user_2", "repo_4", True, organization_2["id"])

        # Add a member to a team with admin permissions to the specific repo
        add_user_to_org(user_2["id"], organization_1["id"])
        team_1 = add_team("user_1", organization_1["id"], "team_1")
        add_team_member(user_2["id"], team_1["id"])
        add_team_permission(team_1["id"], repo_1["id"], TeamPermissionKind.admin)
        add_team_permission(team_1["id"], repo_2["id"], TeamPermissionKind.read)
        add_team_permission(team_1["id"], repo_3["id"], TeamPermissionKind.read_write)

        update = get_fun(update_type)
        attribute = "some desc" if update_type == "desc" else True

        """ NOTE: 'User' is a regular user or an admin. """
        # User who is the owner of the repo
        assert update("user_1", repo_1["id"], attribute).is_success
        # User who is trying to update a non existing repo
        assert update("user_1", -1, attribute).status_code == 400
        # User without any special relations to the repo
        assert update("user_1", repo_4["id"], attribute).status_code == 400
        # User who is a team member with admin permissions against repo
        assert update("user_2", repo_1["id"], attribute).is_success
        # User who is a team member with read permissions against repo
        assert update("user_2", repo_2["id"], attribute).status_code == 400
        # User who is a team member with read write permissions against repo
        assert update("user_2", repo_3["id"], attribute).status_code == 200

class TestToggleRepoStar:

    def test_missing_repo(self, repo_service):
        """ Test case for when the user requests an update for a missing repository. """   
        user_id = 1
        repo_id = 1

        repo_service.repo_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            repo_service.toggle_repo_star(user_id, repo_id)

    def test_missing_user(self, repo_service):
        """ Test case for when the request is made by a guest or a missing user. """   
        user_id = None
        repo_id = 1
        repo = mock.MagicMock(spec=Repository)

        repo_service.repo_repo.find_by_id.return_value = repo
        repo_service.user_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            repo_service.toggle_repo_star(user_id, repo_id)

        user_id = 1
        with pytest.raises(NotFoundException):
            repo_service.toggle_repo_star(user_id, repo_id)

    def test_when_repo_becomes_starred(self, repo_service):
        """ Test case for when the repo is unstarred and then becomes starred. """   
        user_id = 1
        repo_id = 1

        start_repo = mock.MagicMock(spec=Repository)
        start_repo.stars = 0
        start_repo.id = repo_id

        end_repo = mock.MagicMock(spec=Repository)
        end_repo.stars = 1
        end_repo.id = repo_id

        user = mock.MagicMock(spec=User)
        user.stars = []

        repo_service.user_repo.find_by_id.return_value = user 
        repo_service.repo_repo.find_by_id.return_value = start_repo
        repo_service.repo_repo.star_repo.return_value = end_repo

        res_repo, starred = repo_service.toggle_repo_star(user_id, repo_id)

        assert res_repo.id == repo_id
        assert res_repo.stars == end_repo.stars
        assert starred is True

    def test_when_repo_becomes_unstarred(self, repo_service):
        """ Test case for when the repo is starred and then becomes unstarred. """   
        user_id = 1
        repo_id = 1

        start_repo = mock.MagicMock(spec=Repository)
        start_repo.stars = 1
        start_repo.id = repo_id

        end_repo = mock.MagicMock(spec=Repository)
        end_repo.stars = 0
        end_repo.id = repo_id

        repo_star = mock.MagicMock(spec=RepositoryStar)
        repo_star.repository = start_repo

        user = mock.MagicMock(spec=User)
        user.stars = [repo_star]

        repo_service.user_repo.find_by_id.return_value = user 
        repo_service.repo_repo.find_by_id.return_value = start_repo
        repo_service.repo_repo.unstar_repo.return_value = end_repo

        res_repo, starred = repo_service.toggle_repo_star(user_id, repo_id)

        assert res_repo.id == repo_id
        assert res_repo.stars == end_repo.stars
        assert starred is False

    def test_when_repo_star_suddenly_missing(self, repo_service):
        """ Test case for when the repo star becomes missing during runtime. """   
        user_id = 1
        repo_id = 1

        start_repo = mock.MagicMock(spec=Repository)
        start_repo.stars = 1
        start_repo.id = repo_id

        repo_star = mock.MagicMock(spec=RepositoryStar)
        repo_star.repository = start_repo

        user = mock.MagicMock(spec=User)
        user.stars = [repo_star]

        repo_service.user_repo.find_by_id.return_value = user 
        repo_service.repo_repo.find_by_id.return_value = start_repo
        repo_service.repo_repo.unstar_repo.return_value = None

        with pytest.raises(NotFoundException):
            repo_service.toggle_repo_star(user_id, repo_id)

def test_toggle_repo_star___integration():
    with TestClient(app) as client:
        def add_user(username):
            data = {
                "username": username,
                "email": f"{username}@gmail.com",
                "password": "12345678"
            }
            response = client.post("/api/v1/users/", json=data)
            return response.json()
        
        def log_in(username: str, password: str = "12345678"):
            data = {
                "username": username,
                "password": password
            }
            response = client.post("/api/v1/users/login", json=data)
            if response.status_code == 400:
                assert response.json() == False
            jwt = response.json()["token"]
            return jwt
        
        def change_superadmin_password():
            # [1] Loading the super admin credentials
            config_file = "./volume-server-cfg/superadmin_password.txt"

            with open(config_file, "r") as f:
                old_password = f.readline()

            jwt = log_in("admin", old_password)
            header = {"Authorization": f"Bearer {jwt}"}

            # [2] Changing the super admin password
            data = {
                "old_password": old_password,
                "new_password": "12345678"
            }
            response = client.post("/api/v1/users/password", json=data, headers=header)
            assert response.is_success

        def toggle_repo_star(username: str, repo_id: int) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            response = client.put(f"/api/v1/repositories/star/{repo_id}", headers=header)

            return response

        def add_admin(admin_username: str) -> dict:
            jwt = log_in("admin", "12345678")
            header = {"Authorization": f"Bearer {jwt}"}
            data = {
                "username": admin_username,
                "email": f"{admin_username}@gmail.com",
                "password": "12345678"
            }
            response = client.post("/api/v1/users/register-admin", json=data, headers=header)
            created_admin = response.json()

            return created_admin

        def add_org(username, name: str) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            dto1 = {
                "name": name,
                "desc": "",
                "image": None
            }
            return client.post("/api/v1/organizations", json=dto1, headers=header).json()

        def add_user_to_org(user_id: int, org_id: int) -> OrganizationMembers:
            # TODO: Once we implement "add user to org" in the controller, use the proper endpoint for that here.
            from app.api.config.database import engine
            from app.api.org.org_repo import OrganizationRepo
            from app.api.config.database import get_database

            session = next(get_database())
            org_repo = OrganizationRepo(session)
            return org_repo.add_user_to_org(org_id, user_id)

        def add_repo(username, name: str, public: bool, org_id: int | None) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            data = {
                "name": name,
                "desc": "",
                "public": public,
                "organization_id": org_id,
            }

            response = client.post("/api/v1/repositories/", json=data, headers=header)
            return response.json()
        
        def add_team(username: str, org_id: int, name: str, desc: str = "") -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            dto1 = {
                "organization_id": org_id,
                "name": name,
                "desc": desc,
            }
            return client.post("/api/v1/teams", json=dto1, headers=header).json()

        def add_team_member(user_id: int, team_id: int) -> TeamMember:
            # TODO: Once we implement "add team_member" in the controller, use the proper endpoint for that here.
            from app.api.team.team_repo import TeamRepo
            from app.api.config.database import get_database

            session = next(get_database())
            team_repo = TeamRepo(session)
            return team_repo.add_member(team_id, user_id)
        
        def add_team_permission(team_id: int, repo_id: int, kind: TeamPermissionKind) -> TeamPermission:
            # TODO: Once we implement "add_team_permission" in the controller, use the proper endpoint for that here.
            from app.api.team.team_repo import TeamRepo
            from app.api.config.database import get_database

            session = next(get_database())
            team_repo = TeamRepo(session)
            return team_repo.add_permission(team_id, repo_id, kind)

        change_superadmin_password()

        user_1 = add_user("user_1")
        user_2 = add_user("user_2")
        user_3 = add_user("user_3")
        user_4 = add_admin("user_4")
        
        org_1 = add_org("user_2", "org_1")

        repo_1 = add_repo("user_1", "repo_1", True, None)
        repo_2 = add_repo("user_1", "repo_2", False, None)
        repo_3 = add_repo("user_2", "repo_3", True, org_1["id"])
        repo_4 = add_repo("user_2", "repo_4", True, org_1["id"])
        repo_5 = add_repo("user_2", "repo_5", True, org_1["id"])

        add_user_to_org(user_3["id"], org_1["id"])
        
        team_1 = add_team("user_2", org_1["id"], "team_1")
        add_team_member(user_3["id"], team_1["id"])
        
        add_team_permission(team_1["id"], repo_3["id"], TeamPermissionKind.admin)
        add_team_permission(team_1["id"], repo_4["id"], TeamPermissionKind.read)
        add_team_permission(team_1["id"], repo_5["id"], TeamPermissionKind.read_write)

        # A regular user who is the owner of the repo
        assert toggle_repo_star("user_1", repo_1["id"]).status_code == 400
        # A regular user who is attempting to update a non-existent repo
        assert toggle_repo_star("user_1", -1).status_code == 400
        # A regular user without any special relations to the repo
        assert toggle_repo_star("user_2", repo_1["id"]).is_success
        # A regular user who is attempting to star a private repo
        assert toggle_repo_star("user_2", repo_2["id"]).status_code == 400
        # A regular user who is a member of the repo's organization
        assert toggle_repo_star("user_2", repo_3["id"]).status_code == 400
        # A regular user who is a team member with admin permissions on the repo
        assert toggle_repo_star("user_3", repo_3["id"]).status_code == 400
        # A regular user who is a team member with read permissions on the repo
        assert toggle_repo_star("user_3", repo_4["id"]).status_code == 400
        # A regular user who is a team member with read write permissions on the repo
        assert toggle_repo_star("user_3", repo_5["id"]).status_code == 400
        # An admin who is attempting to star a repo
        assert toggle_repo_star("user_4", repo_1["id"]).status_code == 403
        # A super admin who is attempting to star a repo
        assert toggle_repo_star("admin", repo_1["id"]).status_code == 403

def test_get_starred_repositories_of_user___integration():
    with TestClient(app) as client:
        def add_user(username):
            data = {
                "username": username,
                "email": f"{username}@gmail.com",
                "password": "12345678"
            }
            response = client.post("/api/v1/users/", json=data)
            return response.json()
        
        def log_in(username: str, password: str = "12345678"):
            data = {
                "username": username,
                "password": password
            }
            response = client.post("/api/v1/users/login", json=data)
            if response.status_code == 400:
                assert response.json() == False
            jwt = response.json()["token"]
            return jwt
        
        def change_superadmin_password():
            # [1] Loading the super admin credentials
            config_file = "./volume-server-cfg/superadmin_password.txt"

            with open(config_file, "r") as f:
                old_password = f.readline()

            jwt = log_in("admin", old_password)
            header = {"Authorization": f"Bearer {jwt}"}

            # [2] Changing the super admin password
            data = {
                "old_password": old_password,
                "new_password": "12345678"
            }
            response = client.post("/api/v1/users/password", json=data, headers=header)
            assert response.is_success

        def add_admin(admin_username: str) -> dict:
            jwt = log_in("admin", "12345678")
            header = {"Authorization": f"Bearer {jwt}"}
            data = {
                "username": admin_username,
                "email": f"{admin_username}@gmail.com",
                "password": "12345678"
            }
            response = client.post("/api/v1/users/register-admin", json=data, headers=header)
            created_admin = response.json()

            return created_admin

        def add_org(username, name: str) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            dto1 = {
                "name": name,
                "desc": "",
                "image": None
            }
            return client.post("/api/v1/organizations", json=dto1, headers=header).json()

        def toggle_repo_star(username: str, repo_id: int) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            response = client.put(f"/api/v1/repositories/star/{repo_id}", headers=header)

            return response

        def add_repo(username, name: str, org_id: int | None) -> dict:
            jwt = log_in(username)
            header = {"Authorization": f"Bearer {jwt}"}

            data = {
                "name": name,
                "desc": "",
                "public": True,
                "organization_id": org_id,
            }

            response = client.post("/api/v1/repositories/", json=data, headers=header)
            return response.json()
        
        def get_starred_repos(requester: str | None, target_user: str) -> dict:
            if requester is not None:
                jwt = log_in(requester)
                header = {"Authorization": f"Bearer {jwt}"}
                response = client.get(f"/api/v1/repositories/starred/u/{target_user}", headers=header)
            else:
                response = client.get(f"/api/v1/repositories/starred/u/{target_user}")

            return response

        change_superadmin_password()

        add_user("u1")
        add_user("u2")
        add_user("u3")
        add_admin("a1")

        org1 = add_org("u1", "o1")

        r1 = add_repo("u1", "r1", org1["id"])
        r2 = add_repo("u1", "r2", None)
        r3 = add_repo("u1", "r3", None)

        toggle_repo_star("u2", r2["id"])
        toggle_repo_star("u2", r3["id"])
        toggle_repo_star("u3", r1["id"])
        toggle_repo_star("u3", r2["id"])

        # Target user is missing
        assert get_starred_repos(None, "invalid").status_code == 404
        # Target user has zero starred repos
        assert len(get_starred_repos(None, "u1").json()["repos"]) == 0
        # Target user has some starred repos while none belongs to org
        assert len(get_starred_repos(None, "u2").json()["repos"]) == 2
        assert len(get_starred_repos(None, "u2").json()["organization_names"]) == 0
        # Target user has some starred repos while some belongs to org
        assert len(get_starred_repos(None, "u3").json()["repos"]) == 2
        assert len(get_starred_repos(None, "u3").json()["organization_names"]) == 1
        # Requester doesn't need to be logged in
        assert len(get_starred_repos(None, "u2").json()["repos"]) == 2
        assert len(get_starred_repos("u1", "u2").json()["repos"]) == 2
        assert len(get_starred_repos("a1", "u2").json()["repos"]) == 2
        assert len(get_starred_repos("admin", "u2").json()["repos"]) == 2
        # Admin doesn't have starred repos        
        assert get_starred_repos(None, "a1").status_code == 400
        # Super admin doesn't have starred repos        
        assert get_starred_repos(None, "admin").status_code == 400

