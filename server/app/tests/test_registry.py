import jwt
import pytest
from unittest.mock import MagicMock, call, patch
from fastapi import HTTPException
from app.api.registry.registry_service import RegistryService
from app.api.registry.registry_dto import RegistryActionOperation
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.access_control.access_control_service import AccessControlService
from app.api.registry.registry_utils import build_jwt_for_docker_registry, parse_scopes

@pytest.fixture
def registry_service() -> RegistryService:
    mock_session = MagicMock()
    service = RegistryService(mock_session)
    
    service.user_service = MagicMock(UserService)
    service.repo_service = MagicMock(RepositoryService)
    service.access_control_service = MagicMock(AccessControlService)
    
    return service

@pytest.fixture
def mock_jwt_encode():
    original_jwt_encode = jwt.encode
    mock_jwt_encode = MagicMock(return_value="mocked.jwt.token")

    jwt.encode = mock_jwt_encode
    yield mock_jwt_encode

    jwt.encode = original_jwt_encode

def test_handle_registry_request_push(registry_service: RegistryService, mock_jwt_encode):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")
    registry_service.access_control_service.has_write_access.return_value = True

    scopes = ["repository:test/repo:push,pull"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    response = registry_service.handle_registry_request(username, password, scopes, service)
    
    assert response["token"] == "mocked.jwt.token"
    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)
    registry_service.repo_service.find_by_canonical_name.assert_called_once_with("test/repo")
    registry_service.access_control_service.has_write_access.assert_called_once_with(1, 1)
    registry_service.access_control_service.has_read_access.assert_called_once_with(1, 1)

def test_handle_registry_request_push_with_mount(registry_service: RegistryService, mock_jwt_encode):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.access_control_service.has_write_access.return_value = True
    registry_service.access_control_service.has_read_access.return_value = True

    def find_repo_by_name(name):
        if name == "test/repo1":
            return MagicMock(id=1, canonical_name="test/repo1")
        elif name == "test/repo2":
            return MagicMock(id=2, canonical_name="test/repo2")
        return None

    registry_service.repo_service.find_by_canonical_name.side_effect = find_repo_by_name

    scopes = ["repository:test/repo1:pull", "repository:test/repo2:pull", "repository:test/repo2:pull,push"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    response = registry_service.handle_registry_request(username, password, scopes, service)
    
    assert response["token"] == "mocked.jwt.token"
    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)
    expected_calls = [call(1, 1), call(1, 2), call(1, 2)]
    assert registry_service.access_control_service.has_read_access.call_args_list == expected_calls
    registry_service.access_control_service.has_write_access.assert_called_once_with(1, 2)
    expected_calls = [call("test/repo1"), call("test/repo2"), call("test/repo2")]
    assert registry_service.repo_service.find_by_canonical_name.call_args_list == expected_calls

def test_handle_registry_request_invalid_credentials(registry_service: RegistryService):
    registry_service.user_service.exists_with_credentials.return_value = False

    scopes = ["repository:test/repo:push,pull"]
    username = "invaliduser"
    password = "wrongpassword"
    service = "docker-registry"

    with pytest.raises(HTTPException) as excinfo:
        registry_service.handle_registry_request(username, password, scopes, service)
    
    assert excinfo.value.status_code == 401
    assert "Invalid username or password" in str(excinfo.value.detail)

def test_handle_registry_request_pull(registry_service: RegistryService, mock_jwt_encode):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")
    registry_service.access_control_service.has_read_access.return_value = True

    scopes = ["repository:test/repo:pull"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    response = registry_service.handle_registry_request(username, password, scopes, service)
    
    assert response["token"] == "mocked.jwt.token"
    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)
    registry_service.repo_service.find_by_canonical_name.assert_called_once_with("test/repo")
    registry_service.access_control_service.has_read_access.assert_called_once_with(1, 1)

def test_handle_registry_request_no_push_access(registry_service: RegistryService):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")
    registry_service.access_control_service.has_write_access.return_value = False

    scopes = ["repository:test/repo:push"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    with pytest.raises(HTTPException) as excinfo:
        registry_service.handle_registry_request(username, password, scopes, service)

    assert excinfo.value.status_code == 401
    assert "User testuser cannot push to repo test/repo" in str(excinfo.value.detail)

def test_handle_registry_request_push_with_mount_no_pull_access(registry_service: RegistryService, mock_jwt_encode):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.access_control_service.has_write_access.return_value = True

    def check_read_access(user_id, repo_id):
        if (user_id, repo_id) == (1, 1):
            return False
        elif (user_id, repo_id) == (1, 2):
            return True
        return None

    registry_service.access_control_service.has_read_access.side_effect = check_read_access

    def find_repo_by_name(name):
        if name == "test/repo1":
            return MagicMock(id=1, canonical_name="test/repo1")
        elif name == "test/repo2":
            return MagicMock(id=2, canonical_name="test/repo2")
        return None

    registry_service.repo_service.find_by_canonical_name.side_effect = find_repo_by_name

    scopes = ["repository:test/repo2:pull", "repository:test/repo2:pull,push", "repository:test/repo1:pull"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    with pytest.raises(HTTPException) as excinfo:
        registry_service.handle_registry_request(username, password, scopes, service)
    
    assert excinfo.value.status_code == 401
    assert "User testuser cannot pull from repo test/repo1" in str(excinfo.value.detail)

    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)
    expected_calls = [call(1, 2), call(1, 2), call(1, 1)]
    assert registry_service.access_control_service.has_read_access.call_args_list == expected_calls
    registry_service.access_control_service.has_write_access.assert_called_once_with(1, 2)
    expected_calls = [call("test/repo2"), call("test/repo2"), call("test/repo1")]
    assert registry_service.repo_service.find_by_canonical_name.call_args_list == expected_calls

def test_handle_registry_request_unknown_operation(registry_service: RegistryService):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")

    scopes = ["repository:test/repo:delete"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    with pytest.raises(ValueError) as ex:
        registry_service.handle_registry_request(username, password, scopes, service)
    assert "delete" in str(ex)

def test_handle_registry_request_jwt_generation(registry_service: RegistryService, mock_jwt_encode):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")


    scopes = ["repository:test/repo:push,pull"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    response = registry_service.handle_registry_request(username, password, scopes, service)
    
    assert response["token"] == "mocked.jwt.token"
    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)
    registry_service.access_control_service.has_write_access.assert_called_once_with(1, 1)
    registry_service.access_control_service.has_read_access.assert_called_once_with(1, 1)
    
# -----------------------------------
# Util functions
# -----------------------------------

def test_parse_scopes_valid_input():
    scopes = ["repository:test/repo1:push,pull", "repository:test/repo2:pull"]
    username = "testuser"

    actions = parse_scopes(username, scopes)

    action = actions[0]
    assert action.username == "testuser"
    assert action.repo_canonical_name == "test/repo1"
    assert action.operations == [RegistryActionOperation.push, RegistryActionOperation.pull]

    action = actions[1]
    assert action.username == "testuser"
    assert action.repo_canonical_name == "test/repo2"
    assert action.operations == [RegistryActionOperation.pull]

def test_parse_scopes_invalid_scope():
    scopes = ["repository:test/repo:push,delete"]
    username = "testuser"

    with pytest.raises(ValueError) as ex:
        parse_scopes(username, scopes)
    assert "delete" in str(ex)

def test_build_jwt_for_docker_registry_with_scope(mock_jwt_encode):
    username = "testuser"
    service = "docker-registry"
    scopes = ["repository:test/repo:push,pull", "repository:test/repo:pull"]

    jwt_token = build_jwt_for_docker_registry(username, service, scopes)

    assert isinstance(jwt_token, str)
    assert len(jwt_token) > 0

def test_build_jwt_for_docker_registry_without_scope(mock_jwt_encode):
    username = "testuser"
    service = "docker-registry"
    scope = None

    jwt_token = build_jwt_for_docker_registry(username, service, scope)

    assert isinstance(jwt_token, str)
    assert len(jwt_token) > 0
