import os
import jwt
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException
from app.api.registry.registry_service import RegistryService
from app.api.registry.registry_dto import RegistryActionOperation
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.access_control.access_control_service import AccessControlService
from app.api.registry.registry_utils import build_jwt_for_docker_registry, parse_scope, build_manifest_jwt
from app.api.registry.registry_client import RegistryClient
from app.api.config.exception_handler import RegistryException
from app.api.repo.repo_model import Repository
from app.api.tags.tag_model import Tag
from httpx import AsyncClient, Response, Request

BUILD_MANIFEST_JWT_PATH = "app.api.registry.registry_service.build_manifest_jwt"

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

    scope = "repository:test/repo:push,pull"
    username = "testuser"
    password = "password"
    service = "docker-registry"

    response = registry_service.handle_registry_request(username, password, scope, service)
    
    assert response["token"] == "mocked.jwt.token"
    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)
    registry_service.repo_service.find_by_canonical_name.assert_called_once_with("test/repo")
    registry_service.access_control_service.has_write_access.assert_called_once_with(1, 1)

def test_handle_registry_request_invalid_credentials(registry_service: RegistryService):
    registry_service.user_service.exists_with_credentials.return_value = False

    scope = "repository:test/repo:push,pull"
    username = "invaliduser"
    password = "wrongpassword"
    service = "docker-registry"

    with pytest.raises(HTTPException) as excinfo:
        registry_service.handle_registry_request(username, password, scope, service)
    
    assert excinfo.value.status_code == 401
    assert "Invalid username or password" in str(excinfo.value.detail)

def test_handle_registry_request_pull(registry_service: RegistryService, mock_jwt_encode):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")
    registry_service.access_control_service.has_read_access.return_value = True

    scope = "repository:test/repo:pull"
    username = "testuser"
    password = "password"
    service = "docker-registry"

    response = registry_service.handle_registry_request(username, password, scope, service)
    
    assert response["token"] == "mocked.jwt.token"
    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)
    registry_service.repo_service.find_by_canonical_name.assert_called_once_with("test/repo")
    registry_service.access_control_service.has_read_access.assert_called_once_with(1, 1)

def test_handle_registry_request_no_push_access(registry_service: RegistryService):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")
    registry_service.access_control_service.has_write_access.return_value = False

    scope = "repository:test/repo:push"
    username = "testuser"
    password = "password"
    service = "docker-registry"

    with pytest.raises(HTTPException) as excinfo:
        registry_service.handle_registry_request(username, password, scope, service)

    assert excinfo.value.status_code == 401
    assert "User testuser cannot push to repo test/repo" in str(excinfo.value.detail)

def test_handle_registry_request_unknown_operation(registry_service: RegistryService):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")
    registry_service.repo_service.find_by_canonical_name.return_value = MagicMock(id=1, canonical_name="test/repo")

    scope = "repository:test/repo:update"
    username = "testuser"
    password = "password"
    service = "docker-registry"

    with pytest.raises(ValueError) as ex:
        registry_service.handle_registry_request(username, password, scope, service)
    assert "update" in str(ex)

def test_handle_registry_request_jwt_generation(registry_service: RegistryService, mock_jwt_encode):
    registry_service.user_service.exists_with_credentials.return_value = True
    registry_service.user_service.find_by_username.return_value = MagicMock(id=1, username="testuser")

    scope = "repository:test/repo:push,pull"
    username = "testuser"
    password = "password"
    service = "docker-registry"

    response = registry_service.handle_registry_request(username, password, scope, service)
    
    assert response["token"] == "mocked.jwt.token"
    registry_service.user_service.exists_with_credentials.assert_called_once_with(username, password)

class TestFetchManifestDigest:
    
    @pytest.mark.asyncio
    @patch(BUILD_MANIFEST_JWT_PATH, return_value="fake-jwt")
    async def test_fetch_manifest_digest_404(self, mock_build_jwt, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        response = Response(404)
        client.get_manifest = AsyncMock(return_value=response)

        digest = await registry_service._fetch_manifest_digest(client, "repo", "tag", "user")
        
        assert digest is None
        mock_build_jwt.assert_called_once_with("user", "repo", "GET")
        client.get_manifest.assert_awaited_once_with("repo", "tag", "fake-jwt")

    @pytest.mark.asyncio
    @patch(BUILD_MANIFEST_JWT_PATH, return_value="fake-jwt")
    async def test_fetch_manifest_digest_200(self, mock_build_jwt, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        response = Response(200)
        client.get_manifest = AsyncMock(return_value=response)
        client.get_manifest.return_value.headers = {
            "Docker-Content-Digest": "sha256:abc"
        }

        digest = await registry_service._fetch_manifest_digest(client, "repo", "tag", "user")
        assert digest == "sha256:abc"
        client.get_manifest.assert_awaited_once_with("repo", "tag", "fake-jwt")
        mock_build_jwt.assert_called_once_with("user", "repo", "GET")


    @pytest.mark.asyncio
    @patch(BUILD_MANIFEST_JWT_PATH, return_value="fake-jwt")
    async def test_fetch_manifest_digest_unexpected_status(self, mock_build_jwt, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        err = RegistryException(500, "Server is damaged")
        client.get_manifest.side_effect = err

        with pytest.raises(RegistryException) as e:
            await registry_service._fetch_manifest_digest(client, "repo", "tag", "user")

        assert e.value.status_code == 500
        assert "Server is damaged" in e.value.message
        client.get_manifest.assert_awaited_once_with("repo", "tag", "fake-jwt")
        mock_build_jwt.assert_called_once_with("user", "repo", "GET")

class TestDeleteManifestByDigest:  

    @pytest.mark.asyncio
    @patch(BUILD_MANIFEST_JWT_PATH, return_value="fake-jwt")
    async def test_delete_manifest_by_digest_202(self, mock_build_jwt, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        response = Response(202)
        client.delete_manifest = AsyncMock(return_value=response)

        result = await registry_service._delete_manifest_by_digest(client, "repo", "sha256:abc", "user")

        assert result is None
        client.delete_manifest.assert_awaited_once_with("repo", "sha256:abc", "fake-jwt")
        mock_build_jwt.assert_called_once_with("user", "repo", "DELETE")

    @pytest.mark.asyncio
    @patch(BUILD_MANIFEST_JWT_PATH, return_value="fake-jwt")
    async def test_delete_manifest_by_digest_assertion_error_on_404(self, mock_build_jwt, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        request = Request("DELETE", "https://registry/v2/my-repo/manifests/sha256:abc")
        response = Response(404, request=request)
        client.delete_manifest = AsyncMock(return_value=response)

        with pytest.raises(AssertionError):
            await registry_service._delete_manifest_by_digest(client, "repo", "sha256:abc", "user")

        client.delete_manifest.assert_awaited_once_with("repo", "sha256:abc", "fake-jwt")
        mock_build_jwt.assert_called_once_with("user", "repo", "DELETE")

    @pytest.mark.asyncio
    @patch(BUILD_MANIFEST_JWT_PATH, return_value="fake-jwt")
    async def test_delete_manifest_by_digest_throws_on_500(self, mock_build_jwt, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        err = RegistryException(500, "Server is damaged")
        client.delete_manifest.side_effect = err

        with pytest.raises(RegistryException) as e:
            await registry_service._delete_manifest_by_digest(client, "repo", "sha256:abc", "user")

        client.delete_manifest.assert_awaited_once_with("repo", "sha256:abc", "fake-jwt")
        assert "Server is damaged" in e.value.message
        assert e.value.status_code == 500
        mock_build_jwt.assert_called_once_with("user", "repo", "DELETE")

class TestDeleteTag:

    @pytest.mark.asyncio
    async def test_delete_tag_manifest_not_found(self, registry_service: RegistryService):
        repo = Repository(id=1, name="repo", canonical_name="repo")
        tag = Tag(id=2, name="latest", repository_id=1)
        client = AsyncMock(spec=RegistryClient)

        registry_service._fetch_manifest_digest = AsyncMock(return_value=None)
        registry_service.tag_service.remove_tag = MagicMock(return_value=None)

        response = await registry_service.delete_tag(client, "user", repo, tag)

        assert response.message == "Tag 'latest' successfully deleted from repository 'repo'."
        registry_service._fetch_manifest_digest.assert_awaited_once_with(client, "repo", "latest", "user")
        registry_service.tag_service.remove_tag.assert_called_once_with(2)

    @pytest.mark.asyncio
    async def test_delete_tag_manifest_found(self, registry_service: RegistryService):
        repo = Repository(id=1, name="repo", canonical_name="repo")
        tag = Tag(id=2, name="latest", repository_id=1)
        client = AsyncMock(spec=RegistryClient)

        registry_service._fetch_manifest_digest = AsyncMock(return_value="sha256:abc")
        registry_service._delete_manifest_by_digest = AsyncMock(return_value=None)

        response = await registry_service.delete_tag(client, "user", repo, tag)

        assert response.message == "Tag 'latest' successfully deleted from repository 'repo'."
        registry_service._fetch_manifest_digest.assert_awaited_once_with(client, "repo", "latest", "user")
        registry_service._delete_manifest_by_digest.assert_awaited_once_with(client, "repo", "sha256:abc", "user")

    @pytest.mark.asyncio
    async def test_delete_tag_throws_on_digest_fetch(self, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        tag = Tag(id=2, name="tag", repository_id=1)
        repo = Repository(id=1, name="repo", canonical_name="repo")

        err = RegistryException(500, "Server is damaged")
        registry_service._fetch_manifest_digest = AsyncMock(side_effect = err)

        with pytest.raises(RegistryException) as e:
            await registry_service.delete_tag(client, "user", repo, tag)

        assert e.value.status_code == 500
        assert "Server is damaged" in e.value.message
        registry_service._fetch_manifest_digest.assert_awaited_once_with(client, "repo", "tag", "user")

    @pytest.mark.asyncio
    async def test_delete_tag_throws_on_manifest_delete(self, registry_service: RegistryService):
        client = AsyncMock(spec=RegistryClient)
        tag = Tag(id=2, name="tag", repository_id=1)
        repo = Repository(id=1, name="repo", canonical_name="repo")

        err = RegistryException(500, "Server is damaged")
        registry_service._delete_manifest_by_digest = AsyncMock(side_effect = err)
        registry_service._fetch_manifest_digest = AsyncMock(return_value="sha256:abc")

        with pytest.raises(RegistryException) as e:
            await registry_service.delete_tag(client, "user", repo, tag)

        assert e.value.status_code == 500
        assert "Server is damaged" in e.value.message
        registry_service._fetch_manifest_digest.assert_awaited_once_with(client, "repo", "tag", "user")
        registry_service._delete_manifest_by_digest.assert_awaited_once_with(client, "repo", "sha256:abc", "user")
# -----------------------------------
# Util functions
# -----------------------------------

def test_parse_scope_valid_input():
    scope = "repository:test/repo:push,pull"
    username = "testuser"

    result = parse_scope(username, scope)

    assert result.username == "testuser"
    assert result.repo_canonical_name == "test/repo"
    assert result.operations == [RegistryActionOperation.push, RegistryActionOperation.pull]

def test_parse_scope_invalid_scope():
    scope = "repository:test/repo:push,update"
    username = "testuser"

    with pytest.raises(ValueError) as ex:
        parse_scope(username, scope)
    assert "update" in str(ex)

def test_build_jwt_for_docker_registry_with_scope(mock_jwt_encode):
    username = "testuser"
    service = "docker-registry"
    scope = "repository:test/repo:push,pull"

    jwt_token = build_jwt_for_docker_registry(username, service, scope)

    assert isinstance(jwt_token, str)
    assert len(jwt_token) > 0

def test_build_jwt_for_docker_registry_without_scope(mock_jwt_encode):
    username = "testuser"
    service = "docker-registry"
    scope = None

    jwt_token = build_jwt_for_docker_registry(username, service, scope)

    assert isinstance(jwt_token, str)
    assert len(jwt_token) > 0

@pytest.mark.parametrize("method, expected_scope", [
    ("GET", "repository:repo:pull"),
    ("DELETE", "repository:repo:delete"),
])
@patch("app.api.registry.registry_utils.build_jwt_for_docker_registry", return_value="fake-jwt-token")
def test_build_manifest_jwt_calls_build_jwt_correctly(mock_build_jwt, method, expected_scope):
    
    os.environ["DISTRIBUTION_HOST"] = "host"
    os.environ["DISTRIBUTION_PORT"] = "port"
    
    service = f"{os.environ['DISTRIBUTION_HOST']}:{os.environ['DISTRIBUTION_PORT']}"
    username = "user"
        
    token = build_manifest_jwt(username, "repo", method)

    assert token == "fake-jwt-token"
    mock_build_jwt.assert_called_once_with(username, service, expected_scope)

# -----------------------------------
# Client functions
# -----------------------------------

class TestRegistryClient:

    @pytest.mark.parametrize("method", ["GET", "DELETE"])
    class TestRequest():

        @pytest.mark.asyncio
        async def test_request_returns_valid_response(monkeypatch, method):
            
            token = "fake-token"
            url = "http://host:9999/..."
            response = Response(200, request=Request(method, url))
            async_client = AsyncMock(spec=AsyncClient)
            async_client.request.return_value = response

            client = RegistryClient(async_client, "host", "9999")

            result = await client._request(method, url, token)
            
            assert result.status_code == 200
            async_client.request.assert_awaited_once_with(method, url, headers={"Authorization": f"Bearer {token}"})

        @pytest.mark.asyncio
        async def test_request_raises_on_http_error(monkeypatch, method):

            token = "fake-token"
            url = "http://host:9999/..."
            async_client = AsyncMock(spec=AsyncClient)
            async_client.request.side_effect = Exception("HTTP calling error")

            client = RegistryClient(async_client, "host", "9999")

            with pytest.raises(RegistryException) as e:
                await client._request(method, url, token)
            
            assert e.value.status_code == 502
            async_client.request.assert_awaited_once_with(method, url, headers={"Authorization": f"Bearer {token}"})

        @pytest.mark.asyncio
        async def test_request_raises_on_unexpected_status(monkeypatch, method):
            
            token = "fake-token"
            url = "http://host:9999/..."
            request = Request(method, url)
            response = Response(500, request=request, content="Server is damaged")
            async_client = AsyncMock(spec=AsyncClient)
            async_client.request.return_value = response

            client = RegistryClient(async_client, "host", "port")

            with pytest.raises(RegistryException) as e:
                await client._request(method, url, token)

            assert e.value.status_code == 500
            assert "Server is damaged" in e.value.message
            async_client.request.assert_awaited_once_with(method, url, headers={"Authorization": f"Bearer {token}"})

    # Note: `TestGetManifest` and `TestDeleteManifest` implicitly provide
    # sufficient coverage for `_create_manifest_path` and `_get_scheme`.

    class TestGetManiest:
        
        @pytest.mark.asyncio
        async def test_get_manifest_calls_request_with_correct_args(self):

            token = "fake-token"
            expected_url = "https://host:9999/v2/my_repo/manifests/my_tag"
            expected_headers = {
                "Accept": "application/vnd.docker.distribution.manifest.v2+json, "
                        "application/vnd.oci.image.index.v1+json, "
                        "application/vnd.oci.image.manifest.v1+json"
            }

            response = Response(200, request=Request("GET", expected_url))
            async_client = AsyncMock(spec=AsyncClient)
            client = RegistryClient(client=async_client, host="host", port="9999", secured=True)

            client._request = AsyncMock(return_value=response)

            response = await client.get_manifest("my_repo", "my_tag", token)

            client._request.assert_awaited_once_with("GET", expected_url, token, headers=expected_headers)
            assert response.status_code == 200                                                              

    class TestDeleteManifest:

        @pytest.mark.asyncio
        async def test_delete_manifest_calls_request_with_correct_args(self):
            token = "fake-token"
            expected_url = "https://host:9999/v2/my_repo/manifests/sha256:abc"

            response = Response(202, request=Request("DELETE", expected_url))
            async_client = AsyncMock(spec=AsyncClient)
            client = RegistryClient(client=async_client, host="host", port="9999", secured=True)

            client._request = AsyncMock(return_value=response)

            response = await client.delete_manifest("my_repo", "sha256:abc", token)

            client._request.assert_awaited_once_with("DELETE", expected_url, token)
            assert response.status_code == 202
    