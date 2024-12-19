from fastapi.testclient import TestClient
import pytest
import unittest.mock as mock

from sqlmodel import SQLModel, Session

from app.api.config.security import hash_password
from app.api.user.user_dto import UserPasswordChangeDTO, UserRegisterDTO
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.user.user_service import UserService
from app.api.config.exception_handler import NotFoundException, UserException, FieldTakenException
from app.api.main import app

@pytest.fixture
def mock_session():
    return mock.MagicMock(spec=Session)

@pytest.fixture
def mock_user_repo():
    return mock.MagicMock(spec=UserRepo)

@pytest.fixture
def mock_user():
    return mock.MagicMock(User)

@pytest.fixture
def user_service(mock_session, mock_user_repo):
    service = UserService(mock_session)
    service.user_repo = mock_user_repo
    return service

@pytest.fixture(scope="function", autouse=True)
def reset_db():
    from app.api.config.database import engine
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

def test_change_password(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password1234", new_password="NewPassword1234")
    user_start = User(id=1, email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password(dto.old_password))
    user_end = User(id=1, email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password(dto.new_password))

    mock_user_repo.find_by_id.return_value = user_start
    mock_user_repo.change_password.return_value = user_end

    user_service.change_password(1, dto) # Should not raise exception.

def test_change_password_no_user(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password1234", new_password="NewPassword1234")
    mock_user_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundException) as e:
        user_service.change_password(1, dto)
    
    assert e.value.entity_type == User
    assert e.value.identifier == 1

def test_change_password_wrong_current_password(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password12345", new_password="NewPassword1234")
    user_start = User(id=1, email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password("Password1234"))
    mock_user_repo.find_by_id.return_value = user_start

    with pytest.raises(UserException) as e:
        user_service.change_password(1, dto)

def test_change_password_new_password_is_same_as_current_password(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password1234", new_password="Password1234")
    user_start = User(email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password(dto.old_password))
    mock_user_repo.find_by_id.return_value = user_start

    with pytest.raises(UserException) as e:
        user_service.change_password(1, dto)

def test_find_by_id_user_found(user_service, mock_user):
    """Test case for when a user is found by ID."""
    user_id = 1
    user_service.user_repo.find_by_id.return_value = mock_user

    result = user_service.find_by_id(user_id)

    assert result == mock_user
    user_service.user_repo.find_by_id.assert_called_once_with(user_id)

def test_find_by_id_user_not_found(user_service):
    """Test case for when a user is not found by ID."""
    user_id = 1
    user_service.user_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        user_service.find_by_id(user_id)

    user_service.user_repo.find_by_id.assert_called_once_with(user_id)

def test_find_by_username_user_found(user_service, mock_user):
    """Test case for when a user is found by username."""
    username = "bob"
    user_service.user_repo.find_by_username.return_value = mock_user

    result = user_service.find_by_username(username)

    assert result == mock_user
    user_service.user_repo.find_by_username.assert_called_once_with(username)

def test_find_by_username_user_not_found(user_service):
    """Test case for when a user is not found by username."""
    username = "bob"
    user_service.user_repo.find_by_username.return_value = None

    with pytest.raises(NotFoundException):
        user_service.find_by_username(username)

    user_service.user_repo.find_by_username.assert_called_once_with(username)

def test_add(user_service, mock_user_repo):
    dto = UserRegisterDTO(username="Username1", email="email1@email.com", password="Password1")
    mock_user_repo.find_by_email.return_value = None
    mock_user_repo.find_by_username.return_value = None

    test_result = user_service.add(dto)

    assert test_result.id is not None

def test_add_existing_user(user_service, mock_user_repo):
    dto = UserRegisterDTO(username="Username1", email="email1@email.com", password="Password1")
    user = User(username="Username1", email="email1@email.com", role=UserRole.user, hashed_password=hash_password(dto.password))
    
    def get_user_by_email_mocked(email: str):
        return user if user.email == email else None
    mock_user_repo.find_by_email.side_effect = get_user_by_email_mocked

    def get_user_by_username_mocked(username: str):
        return user if user.username == username else None
    mock_user_repo.find_by_username.side_effect = get_user_by_username_mocked

    # [1] Creating a user with a non-unique email
    with pytest.raises(FieldTakenException) as e:
        user_service.add(dto)
    assert e.value.message == "Email already taken"

    # [2] Creating a user with a non-unique username
    dto.email = "email2@email.com"
    with pytest.raises(FieldTakenException) as e:
        user_service.add(dto)
    assert e.value.message == "Username already taken"

def test_add_admin(user_service, mock_user_repo):
    dto = UserRegisterDTO(username="Username1", email="a@email.com", password="Password1")

    mock_user_repo.find_by_email.return_value = None
    mock_user_repo.find_by_username.return_value = None

    def mock_add(user: User):
        return user
    mock_user_repo.add.side_effect = mock_add

    def set_role(user: User, role: UserRole):
        user.sqlmodel_update({"role": role})
        return user
    mock_user_repo.set_role.side_effect = set_role

    result = user_service.add_admin(dto)
    
    assert result.role == UserRole.admin

def test_add_admin___integration():

    with TestClient(app) as client:
    
        def get_auth_header(data: dict | None) -> dict:
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == 200
            
            ok_request = response.json()
            jwt = ok_request["token"]
            header = {
                "Authorization": f"Bearer {jwt}"
            }

            return header
    
        config_file = "./volume-server-cfg/superadmin_password.txt"
        data = {
            "username" : "admin",
            "password" : ""
        }

        with open(config_file, "r") as f:
            data["password"] = old_password = f.readline()

        # [1] Adding an admin before changing the super admin password
        header = get_auth_header(data)

        data = {
            "username": "Username1",
            "email": "email1@email.com",
            "password": "Password1"
        }
        
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        bad_request = response.json()
        
        assert response.status_code == 403
        assert bad_request["detail"] == "Password change required"
        
        # [2] Changing the super admin password
        data = {
            "old_password": old_password,
            "new_password": "Password1" 
        }
        response = client.post("/api/v1/users/password", json=data, headers=header)
        assert response.status_code == 204

        data = {
            "username" : "admin",
            "password" : data["new_password"]
        }
        header = get_auth_header(data)

        # [3] Adding an admin
        data = {
            "username": "Username1",
            "email": "email1@email.com",
            "password": "Password1"
        }
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        assert response.status_code == 200

        created_admin = response.json()
        assert created_admin["username"] == data["username"]
        assert created_admin["role"] == "admin"

        # [4] Adding an admin with a non-unique username
        data["email"] = "email2@email.com"
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        assert response.status_code == 400

        # [5] Adding an admin with a non-unique email
        data["username"] = "Username2"
        data["email"] = "email1@email.com"
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        assert response.status_code == 400
        
def test_add___integration():

    with TestClient(app) as client:

        def add_user(username: str | None, status_code: int | None) -> dict:
            data = {
                "username": username,
                "email": f"{username}@gmail.com",
                "password": "1234"
            }
            response = client.post("/api/v1/users/", json=data)
            assert response.status_code == status_code
            return response.json()

        def log_in(username: str | None, status_code: int | None) -> str:
            data = {
                "username": username,
                "password": "1234"
            }
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == status_code

        username = "Username1"
        
        user = add_user(username, 200)
        assert user["username"] == username

        log_in(username, 200)
        
        add_user(username, 400)
