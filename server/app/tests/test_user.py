import pytest
import unittest.mock as mock

from sqlmodel import Session

from app.api.config.security import hash_password
from app.api.user.user_dto import UserPasswordChangeDTO
from app.api.user.user_model import User, UserRole
from app.api.user.user_repo import UserRepo
from app.api.user.user_service import UserService
from app.api.config.exception_handler import NotFoundException, UserException

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
