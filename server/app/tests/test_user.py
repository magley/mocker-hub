import pytest
import unittest.mock as mock

from sqlmodel import Session

from app.api.config.security import hash_password
from app.api.user.user_dto import UserPasswordChangeDTO, UserRegisterDTO
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.user.user_service import UserService
from app.api.config.exception_handler import NotFoundException, UserException, FieldTakenException

@pytest.fixture
def mock_session():
    return mock.MagicMock(spec=Session)

@pytest.fixture
def mock_user_repo():
    return mock.MagicMock(spec=UserRepo)

@pytest.fixture
def user_service(mock_session, mock_user_repo):
    service = UserService(mock_session)
    service.user_repo = mock_user_repo
    return service

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
    user_start = User(id=1, username="Username1", email="a@email.com", role=UserRole.user, hashed_password=hash_password("Password1"))
    user_end = User(id=1, username="Username1", email="a@email.com", role=UserRole.admin, hashed_password=hash_password("Password1"))

    with mock.patch.object(user_service, "add", return_value=user_start) as _:
        mock_user_repo.set_role.return_value = user_end

        def set_role(user: User, role: UserRole):
            user.sqlmodel_update({"role": role})
            return user
        mock_user_repo.set_role.side_effect = set_role

        result = user_service.add_admin(dto)
        
        assert result.role == UserRole.admin