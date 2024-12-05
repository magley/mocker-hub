from fastapi.testclient import TestClient
import pytest
import unittest.mock as mock

from sqlmodel import Session

from app.api.config.security import hash_password
from app.api.user.user_dto import UserPasswordChangeDTO, UserRegisterDTO
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.user.user_service import UserService
from app.api.config.exception_handler import FieldTakenException, NotFoundException, UserException
from app.api.repo.repo_repo import RepositoryRepo
from app.api.repo.repo_service import RepositoryService
from app.api.repo.repo_dto import RepositoryCreateDTO
from app.api.repo.repo_model import Repository
from app.api.main import app

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
def user_service(mock_session, mock_user_repo):
    service = UserService(mock_session)
    service.user_repo = mock_user_repo
    return service

@pytest.fixture
def repo_service(mock_session):
    service = RepositoryService(mock_session)
    service.repo_repo = mock.MagicMock(spec=RepositoryRepo)
    service.user_repo = mock.MagicMock(spec=UserRepo)
    return service

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
        organization_id=None,
        owner_id=user1.id
    )

    repo_result = repo_service.add(dto)

    assert repo_result.id is not None

def test_add_repo__no_user(repo_service):
    repo_service.user_repo.find_by_id.return_value = None
    dto = RepositoryCreateDTO(
        name="Some repo",
        desc="",
        public=True,
        organization_id=None,
        owner_id=1
    )

    with pytest.raises(NotFoundException) as e:
        repo_service.add(dto)
    
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
        organization_id=None,
        owner_id=1
    )

    with pytest.raises(FieldTakenException) as e:
        repo_service.add(dto)

    # [2] Trying to create "user2/python".

    dto = RepositoryCreateDTO(
        name="python",
        desc="",
        public=True,
        organization_id=None,
        owner_id=2
    )

    repo_res = repo_service.add(dto)

    assert repo_res is not None

    # [3] Trying to create "python"
    # user is admin, so repo is official.

    dto = RepositoryCreateDTO(
        name="python",
        desc="",
        public=True,
        organization_id=None,
        owner_id=3
    )

    with pytest.raises(FieldTakenException) as e:
        repo_service.add(dto)

def test_add___integration():
    with TestClient(app) as client:
        data = {
            "username": "u1",
            "email": "u1@gmail.com",
            "password": "1234"
        }

        response = client.post("/api/v1/users/", json=data)
        print(response.json())

        response = client.post("/api/v1/users/", json=data)
        print(response.json())