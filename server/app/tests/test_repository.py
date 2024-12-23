from fastapi.testclient import TestClient
import pytest
import unittest.mock as mock

from sqlmodel import SQLModel, Session

from app.api.config.security import hash_password
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.user.user_service import UserService
from app.api.config.exception_handler import FieldTakenException, NotFoundException, UserException
from app.api.repo.repo_repo import RepositoryRepo
from app.api.repo.repo_service import RepositoryService
from app.api.repo.repo_dto import RepositoryCreateDTO
from app.api.repo.repo_model import Repository, RepositoryBadge
from app.api.main import app
from app.api.org.org_repo import OrganizationRepo

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


def test_user_has_read_access_to_repo_public(repo_service, mock_repo):
    """Test case for when the repository is public."""
    mock_repo.public = True
    
    assert repo_service.user_has_read_access_to_repo(mock_repo, None) == True
    assert repo_service.user_has_read_access_to_repo(mock_repo, 1) == True


def test_user_has_read_access_to_repo_private_signed_out(repo_service, mock_repo):
    mock_repo.public = False
    mock_repo.owner_id = 1
    mock_repo.organization_id = None
    
    assert repo_service.user_has_read_access_to_repo(mock_repo, None) == False


def test_user_has_read_access_to_repo_private_personal_owner(repo_service, mock_repo):
    """Test case for when the repository is personal, and the user is the owner."""
    mock_repo.public = False
    mock_repo.owner_id = 1
    mock_repo.organization_id = None
    
    # I am the owner of this private repo.
    assert repo_service.user_has_read_access_to_repo(mock_repo, 1) == True
    # Someone else is the owner of this private personal repo.
    assert repo_service.user_has_read_access_to_repo(mock_repo, 2) == False


def test_user_has_read_access_to_repo_private_org_member(repo_service, mock_repo):
    """Test case for when the repository is an organization repository and the user is a member."""
    mock_repo.public = False
    mock_repo.owner_id = 1
    mock_repo.organization_id = 1
    
    # Member of the org.
    repo_service.org_repo.user_is_in_org.return_value = True
    assert repo_service.user_has_read_access_to_repo(mock_repo, 1) == True
    
    # Outsider relative to the org.
    repo_service.org_repo.user_is_in_org.return_value = False
    assert repo_service.user_has_read_access_to_repo(mock_repo, 1) == False


def test_user_has_read_access_to_repo_private_org_not_member(repo_service, mock_repo):
    """Test case for when the repository is an organization repository and the user is not a member."""
    mock_repo.public = False
    mock_repo.owner_id = 1
    mock_repo.organization_id = 1
    
    # Outsider relative to org.
    repo_service.org_repo.user_is_in_org.return_value = False
    assert repo_service.user_has_read_access_to_repo(mock_repo, 1) == False

"""
NOTE: `user_had_red_access` has way too many possible cases to test them all because
of the number of variables:

- am i logged in
    - am i the owner of this repo
- is the repo public
- is the repo in an organization
    - am i a member of this repo

So instead, `user_had_red_access` is done with whitebox testing.
The integration tests should cover some interesting cases (if any).
"""

def test_get_repositories_of_user_all_accessible(repo_service, mock_repo):
    """Test case for when all repositories are accessible by whos_asking_user_id."""
    user_id = 1
    whos_asking_user_id = 2

    repo_service.repo_repo.get_repositories_for_user.return_value = [mock_repo, mock_repo]
    repo_service.user_has_read_access_to_repo = mock.MagicMock(return_value=True)

    result = repo_service.get_repositories_of_user(user_id, whos_asking_user_id)

    assert len(result) == 2
    assert result == [mock_repo, mock_repo]
    repo_service.repo_repo.get_repositories_for_user.assert_called_once_with(user_id)
    repo_service.user_has_read_access_to_repo.assert_any_call(mock_repo, whos_asking_user_id)


def test_get_repositories_of_user_some_accessible(repo_service):
    """Test case for when some repositories are not accessible by whos_asking_user_id."""
    user_id = 1
    whos_asking_user_id = 2

    repo1 = mock.MagicMock(Repository)
    repo1.id = 1
    
    repo2 = mock.MagicMock(Repository)
    repo2.id = 2

    repo_service.repo_repo.get_repositories_for_user.return_value = [repo1, repo2]
    repo_service.user_has_read_access_to_repo = mock.MagicMock(side_effect=[True, False])

    result = repo_service.get_repositories_of_user(user_id, whos_asking_user_id)

    assert len(result) == 1
    assert result == [repo1]
    repo_service.repo_repo.get_repositories_for_user.assert_called_once_with(user_id)
    repo_service.user_has_read_access_to_repo.assert_any_call(repo1, whos_asking_user_id)


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