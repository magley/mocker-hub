import os
from fastapi.testclient import TestClient
import jwt
from app.api.events.event_model import EventLevel
import pytest
from app.api.jobs.jobs_client import JobsClient
from app.api.user.user_model import User
from app.api.events.event_service import EventService
from sqlmodel import SQLModel
from app.api.main import app
from unittest.mock import MagicMock, AsyncMock, call, patch
from fastapi import HTTPException
from app.api.registry.registry_service import RegistryService
from app.api.registry.registry_dto import DeleteResponseDTO, RegistryActionOperation
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.access_control.access_control_service import AccessControlService
from app.api.registry.registry_utils import build_jwt_for_docker_registry, parse_scopes, build_manifest_jwt
from app.api.registry.registry_client import RegistryClient
from app.api.config.exception_handler import AccessDeniedException, NotFoundException, RegistryException
from app.api.repo.repo_model import Repository
from app.api.tags.tag_model import Tag
from httpx import AsyncClient, Response, Request

from app.api.config.database import get_database
from app.api.tags.tag_service import TagService
from app.api.team.team_model import TeamMember, TeamPermissionKind, TeamPermission
from app.api.org.org_model import Organization, OrganizationMembers
from app.api.org.org_service import OrganizationService

BUILD_MANIFEST_JWT_PATH = "app.api.registry.registry_service.build_manifest_jwt"

@pytest.fixture
def registry_service() -> RegistryService:
    mock_session = MagicMock()
    service = RegistryService(mock_session)
    
    service.user_service = MagicMock(UserService)
    service.repo_service = MagicMock(RepositoryService)
    service.access_control_service = MagicMock(AccessControlService)
    service.tag_service = MagicMock(TagService)
    service.event_service = MagicMock(EventService)
    service.org_service = MagicMock(OrganizationService)

    return service

@pytest.fixture
def mock_jwt_encode():
    original_jwt_encode = jwt.encode
    mock_jwt_encode = MagicMock(return_value="mocked.jwt.token")

    jwt.encode = mock_jwt_encode
    yield mock_jwt_encode

    jwt.encode = original_jwt_encode

@pytest.fixture(scope="function", autouse=True)
def reset_db():
    from app.api.config.database import engine
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

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

    scopes = ["repository:test/repo:update"]
    username = "testuser"
    password = "password"
    service = "docker-registry"

    with pytest.raises(ValueError) as ex:
        registry_service.handle_registry_request(username, password, scopes, service)
    assert "update" in str(ex)

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
    
    @patch("app.api.registry.registry_service.build_manifest_jwt", return_value="fake-jwt")
    def test_delete_tag__integration(self, mock_build_jwt):

        # NOTE: We can’t add tags through the API, so we need
        # to insert them directly into the backend database
        # and use the distribution API to preserve the image
        # there. This process is very complex. Therefore, this
        # test will mock communication with the distribution API.
        # An end-to-end test would be the ideal choice to fully
        # cover this functionality.

        with TestClient(app) as client:
            def add_user(username):
                data = {
                    "username": username,
                    "email": f"{username}@email.com",
                    "password": "1234"
                }
                response = client.post("/api/v1/users/", json=data)
                return response.json()

            def log_in(username):
                data = {"username": username, "password": "1234"}
                response = client.post("/api/v1/users/login", json=data)
                return response.json()["token"]

            def add_repo(username, repo_name, org_id = None):
                data = {
                    "name": repo_name,
                    "desc": "",
                    "public": True,
                    "organization_id": org_id,
                }
                header = {"Authorization": f"Bearer {log_in(username)}"}

                return client.post("/api/v1/repositories/", json=data, headers=header).json()
            
            def add_org(username, name: str) -> dict:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                dto = {
                    "name": name,
                    "desc": "",
                    "image": None
                }
                return client.post("/api/v1/organizations", json=dto, headers=header).json()

            def add_user_to_org(user_id: int, org_id: int) -> OrganizationMembers:
                # TODO: Once we implement "add user to org" in the controller, use the proper endpoint for that here.
                from app.api.config.database import engine
                from app.api.org.org_repo import OrganizationRepo
                from app.api.config.database import get_database

                session = next(get_database())
                org_repo = OrganizationRepo(session)
                return org_repo.add_user_to_org(org_id, user_id)

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
                return team_repo.add_permission(team_id, repo_id, kind).model_dump()

            def add_tag(user_id, repo_id, tag_name):
                session = next(get_database())
                tag_service = TagService(session)
                return tag_service.on_push(user_id, repo_id, tag_name).model_dump()

            def search_tags(repo_canonical_name):
                return client.get(f"/api/v1/tags/?repo_name={repo_canonical_name}").json()
        
            def delete_tag(repo_id, tag_name, username):
                data = {
                    "repo_id": repo_id, 
                    "tag_name": tag_name
                }
                header = {"Authorization": f"Bearer {log_in(username)}"}
                return client.request("DELETE", "/api/v1/registry/tag", json=data, headers=header)

            class MockResponse:
                def __init__(self, status_code, headers = {}):
                    self.status_code = status_code
                    self.headers = headers

            async def mock_get_manifest(self, repo_name, tag_name, token):
                return MockResponse(200, {"Docker-Content-Digest": "sha256:abc"})
            
            async def mock_get_manifest_502(self, repo_name, tag_name, token):
                raise RegistryException(502, "Error when calling Distribution")

            async def mock_get_missing_manifest(self, repo_name, tag_name, token):
                return MockResponse(404)

            async def mock_delete_manifest(self, repo_name, digest, token):
                return MockResponse(202)
            
            def patch_object(type):
                if type == "get_manifest":
                    return patch.object(RegistryClient, "get_manifest", new=mock_get_manifest)
                elif type == "delete_manifest":
                    return patch.object(RegistryClient, "delete_manifest", new=mock_delete_manifest)
                elif type == "get_manifest_unresponsive":
                    return patch.object(RegistryClient, "get_manifest", new=mock_get_manifest_502)
                elif type == "get_missing_manifest":
                    return patch.object(RegistryClient, "get_manifest", new=mock_get_missing_manifest)

            u1 = add_user("u1")
            u2 = add_user("u2")
            o1 = add_org("u1", "o1")
            r1 = add_repo("u1", "r1")
            r2 = add_repo("u1", "r2", o1["id"])
            r3 = add_repo("u1", "r3", o1["id"])
            t1 = add_tag(u1["id"], r1["id"], "t1")
            t2 = add_tag(u1["id"], r1["id"], "t2")
            t3 = add_tag(u1["id"], r2["id"], "t3")
            t4 = add_tag(u1["id"], r3["id"], "t4")

            add_user_to_org(u2["id"], o1["id"])
            tm1 = add_team("u1", o1["id"], "tm1")
            add_team_member(u2["id"], tm1["id"])
            add_team_permission(tm1["id"], r2["id"], TeamPermissionKind.admin)
            add_team_permission(tm1["id"], r3["id"], TeamPermissionKind.read_write)

            # 1) Repo doesn't exist.
            with patch_object("get_manifest"), patch_object("delete_manifest"):
                response = delete_tag(99, t1["name"], u1["username"])
                assert response.status_code == 404

            # 2) User is not authorized to delete tag.
            with patch_object("get_manifest"), patch_object("delete_manifest"):
                response = delete_tag(r1["id"], t2["name"], u2["username"])
                assert response.status_code == 400

            # 3) Tag and manifest exist, but the tag is not deleted from the backend DB  
            #    because deletion is postponed until a notification is received Distribution.
            def standard_deleting_test(repo, tag, user):
                with patch_object("get_manifest"), patch_object("delete_manifest"):
                    response = delete_tag(repo["id"], tag["name"], user["username"])
                    assert response.status_code == 200
            standard_deleting_test(r1, t1, u1)

            # 4) Tag exists, but the manifest doesn't; two tags were pointing to the same image.
            with patch_object("get_missing_manifest"):
                response = delete_tag(r1["id"], t2["name"], u1["username"])
                assert response.status_code == 200
                tags = search_tags(r1['canonical_name'])
                assert len(tags) == 1

            # 5) Tag doesn't exist.
            with patch_object("get_manifest"), patch_object("delete_manifest"):
                response = delete_tag(r1["id"], t2["name"], u1["username"])
                assert response.status_code == 400

            # 6) Distribution is unresponsive.
            with patch_object("get_manifest_unresponsive"):
                response = delete_tag(r1["id"], t1["name"], u1["username"])
                assert response.status_code == 502
                payload = response.json()
                assert "Error when calling Distribution" in payload["detail"]["message"]
            
            # 7) Delete tag as an organization member with `admin` permissions.
            standard_deleting_test(r2, t3, u2)
            
            # 8) Delete tag as an organization member with `read_write` permissions.
            standard_deleting_test(r3, t4, u2)

class TestDeleteRepo:
    
    def test_repo_not_exist(self, registry_service: RegistryService):
        """ Test case for when the repository does not exist. """
        client = MagicMock(spec=JobsClient)
        user_id = 1
        repo_id = 99999
        registry_service.repo_service.find_by_id.side_effect = NotFoundException(Repository, repo_id)

        with pytest.raises(NotFoundException): 
            registry_service.delete_repo(client, "user", user_id, repo_id)
    
        registry_service.repo_service.find_by_id.assert_called_once_with(repo_id)

    def test_user_not_permitted(self, registry_service: RegistryService):
        """ Test case for when the user is not permitted to delete the repository. """
        repo = MagicMock(spec=Repository)
        client = MagicMock(spec=JobsClient)
        registry_service.repo_service.find_by_id.return_value = repo
        user_id = 1
        repo.id = 1
        registry_service.access_control_service.has_delete_access.return_value = False

        with pytest.raises(AccessDeniedException): 
            registry_service.delete_repo(client, "user", user_id, repo.id)
    
        registry_service.repo_service.find_by_id.assert_called_once_with(repo.id)
        registry_service.access_control_service.has_delete_access.assert_called_once_with(user_id, repo.id)
        
    def test_repo_not_have_tags(self, registry_service: RegistryService):
        """ Test case for when the repository does not have any tags. """
        user_id = 1
        client = MagicMock(spec=JobsClient)
        repo = MagicMock(spec=Repository)
        repo.id =1
        repo.name = "repo"
        repo.owner = MagicMock(spec=User)
        repo.owner.username = "user"
        repo.tags = []
        repo.organization = MagicMock(spec=Organization)
        repo.organization.deleting = False
        registry_service.repo_service.find_by_id.return_value = repo
        registry_service.repo_service.remove_repo.return_value = None

        result = registry_service.delete_repo(client, "user", user_id, repo.id)

        assert isinstance(result, DeleteResponseDTO)
        registry_service.repo_service.find_by_id.assert_called_once_with(repo.id)
        registry_service.access_control_service.has_delete_access.assert_called_once_with(user_id, repo.id)
        registry_service.repo_service.remove_repo.assert_called_once_with(repo)
        registry_service.event_service.log.assert_called_once_with(EventLevel.Info, f"Repository '{repo.canonical_name}' is deleted.")

    def test_repo_has_tags(self, registry_service: RegistryService):
        """ Test case for when the repository has tags. """
        user_id = 1
        tag_1 = MagicMock(spec=Tag(name="tag_1"))
        tag_2 = MagicMock(spec=Tag(name="tag_2"))
        
        repo = MagicMock(spec=Repository)
        repo.id = 1
        repo.name = "repo"
        repo.owner = MagicMock(spec=User)
        repo.owner.username = "user"
        repo.tags = [tag_1, tag_2]

        queue = MagicMock()
        client = MagicMock(spec=JobsClient)
        client.get.return_value = queue

        registry_service.repo_service.find_by_id.return_value = repo
        registry_service.repo_service.remove_repo.return_value = None

        result = registry_service.delete_repo(client, "user", user_id, repo.id)

        assert isinstance(result, DeleteResponseDTO)
        assert queue.enqueue.call_count == 2
        client.get.assert_called_with("delete_tag")
        registry_service.repo_service.find_by_id.assert_called_once_with(repo.id)
        registry_service.access_control_service.has_delete_access.assert_called_once_with(user_id, repo.id)
        registry_service.repo_service.update_repo_attrs.assert_called_once_with(repo.id, deleting=True)

    @patch("app.api.jobs.jobs_client.JobsClient.get", return_value=MagicMock())
    def test_delete_repo__integration(self, mock_get_queue):

        # NOTE: Queues are mocked in these tests, as  
        # spinning up Redis and workers is very complex.

        with TestClient(app) as client:
            def add_user(username):
                data = {
                    "username": username,
                    "email": f"{username}@email.com",
                    "password": "1234"
                }
                response = client.post("/api/v1/users/", json=data)
                return response.json()

            def log_in(username):
                data = {"username": username, "password": "1234"}
                response = client.post("/api/v1/users/login", json=data)
                return response.json()["token"]

            def add_repo(username, repo_name, org_id = None):
                data = {
                    "name": repo_name,
                    "desc": "",
                    "public": True,
                    "organization_id": org_id,
                }
                header = {"Authorization": f"Bearer {log_in(username)}"}

                return client.post("/api/v1/repositories/", json=data, headers=header).json()
            
            def add_org(username, name: str) -> dict:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                dto = {
                    "name": name,
                    "desc": "",
                    "image": None
                }
                return client.post("/api/v1/organizations", json=dto, headers=header).json()

            def add_user_to_org(user_id: int, org_id: int) -> OrganizationMembers:
                # TODO: Once we implement "add user to org" in the controller, use the proper endpoint for that here.
                from app.api.config.database import engine
                from app.api.org.org_repo import OrganizationRepo
                from app.api.config.database import get_database

                session = next(get_database())
                org_repo = OrganizationRepo(session)
                return org_repo.add_user_to_org(org_id, user_id)

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
                return team_repo.add_permission(team_id, repo_id, kind).model_dump()

            def add_tag(user_id, repo_id, tag_name):
                session = next(get_database())
                tag_service = TagService(session)
                return tag_service.on_push(user_id, repo_id, tag_name).model_dump()
            
            

            def delete_repo(repo_id, username):
                header = {"Authorization": f"Bearer {log_in(username)}"}
                return client.request("DELETE", f"/api/v1/registry/repository/{repo_id}", headers=header)

            u1 = add_user("u1")
            u2 = add_user("u2")
            u3 = add_user("u3")
            o1 = add_org("u1", "o1")
            r1 = add_repo("u1", "r1")
            r2 = add_repo("u1", "r2", o1["id"])
            r3 = add_repo("u1", "r3", o1["id"])
            r4 = add_repo("u1", "r4", o1["id"])
            add_tag(u1["id"], r2["id"], "t1")
            add_tag(u1["id"], r2["id"], "t2")
            add_tag(u1["id"], r4["id"], "t3")
            add_tag(u1["id"], r4["id"], "t4")

            add_user_to_org(u3["id"], o1["id"])
            t1 = add_team("u1", o1["id"], "t1")
            add_team_member(u3["id"], t1["id"])
            add_team_permission(t1["id"], r3["id"], TeamPermissionKind.admin)
            add_team_permission(t1["id"], r4["id"], TeamPermissionKind.read_write)

            # 1) Repository does not exist.
            response = delete_repo(99999, u1["username"])
            assert response.status_code == 404
            assert mock_get_queue.call_count == 0

            # 2) User is not authorized to delete the repository.
            response = delete_repo(r1["id"], u2["username"])
            assert response.status_code == 400
            assert mock_get_queue.call_count == 0

            # 3) User removes a repository without tags successfully.
            with patch("app.api.events.event_service.EventService.log"):
                response = delete_repo(r1["id"], u1["username"])
                assert response.status_code == 202
                assert mock_get_queue.call_count == 0

            with patch("app.api.events.event_service.EventService.log"):
                response = delete_repo(r3["id"], u3["username"])
                assert response.status_code == 202
                assert mock_get_queue.call_count == 0

            # 4) User removes a repository with tags successfully.
            response = delete_repo(r2["id"], u1["username"])
            assert response.status_code == 202
            assert mock_get_queue.call_count == 2   

            response = delete_repo(r4["id"], u3["username"])
            assert response.status_code == 202
            assert mock_get_queue.call_count == 4   

class TestDeleteOrg:
    
    def test_org_not_exist(self, registry_service: RegistryService):
        """ Test case for when the organization does not exist. """
        client = MagicMock(spec=JobsClient)
        user_id = 1
        org_name = "o1"
        registry_service.org_service.find_by_name.side_effect = NotFoundException(Organization, org_name)

        with pytest.raises(NotFoundException): 
            registry_service.delete_org(client, "user", user_id, org_name)
    
        registry_service.org_service.find_by_name.assert_called_once_with(org_name)
        registry_service.org_service.update_org_attrs.assert_not_called()

    def test_user_not_have_permission(self, registry_service: RegistryService):
        """ Test case for when the user does not have permission. """
        client = MagicMock(spec=JobsClient)
        user_id = 9999
        org = MagicMock(spec=Organization)
        org.name = "o1"
        org.owner_id = 1
        registry_service.org_service.find_by_name.return_value = org

        with pytest.raises(AccessDeniedException): 
            registry_service.delete_org(client, "user", user_id, org.name)
    
        registry_service.org_service.find_by_name.assert_called_once_with(org.name)
        registry_service.org_service.update_org_attrs.assert_not_called()

    def test_org_not_have_repos(self, registry_service: RegistryService):
        """ Test case for when the org does not have any repo. """
        client = MagicMock(spec=JobsClient)
        user_id = 1
        org = MagicMock(spec=Organization)
        org.name = "o1"
        org.owner_id = 1
        org.repositories = []
        registry_service.org_service.find_by_name.return_value = org

        result = registry_service.delete_org(client, "user", user_id, org.name)
    
        registry_service.org_service.find_by_name.assert_called_once_with(org.name)
        registry_service.org_service.update_org_attrs.assert_called_once_with(org.name, deleting=True)
        registry_service.org_service.remove_org.assert_called_once_with(org)
        registry_service.event_service.log.assert_called_once()
        assert result.message == f"Request to delete organization '{org.name}' has been accepted and will be processed shortly."

    def test_org_have_repos(self, registry_service: RegistryService):
        """ Test case for when the org has repos. """
        
        # I won't test the deeper logic behind `self.delete_repo`, 
        # as we have unit tests specifically designed for it.

        client = MagicMock(spec=JobsClient)
        user_id = 1
        tag = MagicMock(speci=Tag)
        repo = MagicMock(spec=Repository)
        repo.id = 1
        repo.deleting = False
        repo.tags = [tag]
        org = MagicMock(spec=Organization)
        org.name = "o1"
        org.owner_id = 1
        org.repositories = [repo]
        org.deleting = False
        repo.organization = org
        registry_service.org_service.find_by_name.return_value = org
        registry_service.repo_service.find_by_id.return_value = repo

        result = registry_service.delete_org(client, "user", user_id, org.name)
    
        registry_service.org_service.find_by_name.assert_called_once_with(org.name)
        registry_service.org_service.update_org_attrs.assert_called_once_with(org.name, deleting=True)
        registry_service.org_service.remove_org.assert_not_called()
        registry_service.event_service.log.assert_not_called()
        registry_service.repo_service.find_by_id.assert_called_once_with(repo.id)
        registry_service.access_control_service.has_delete_access.assert_called_once_with(user_id, repo.id)
        client.get.assert_called_once_with("delete_tag")
        assert result.message == f"Request to delete organization '{org.name}' has been accepted and will be processed shortly."

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
    scopes = ["repository:test/repo:push,update"]
    username = "testuser"

    with pytest.raises(ValueError) as ex:
        parse_scopes(username, scopes)
    assert "update" in str(ex)

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
    mock_build_jwt.assert_called_once_with(username, service, [expected_scope])

class TestFormatRegistryEvent:

    def test_layer_action(self, registry_service: RegistryService):
        msg = registry_service._format_registry_event(
            username="user",
            action="push",
            repo_name="repo",
            tag_name=None,
            digest="sha:123",
            method="PUT",
            url="/v2/repo/blobs/sha:123"
        )
        assert "user" in msg
        assert "push" in msg
        assert "repo" in msg
        assert "PUT" in msg

        assert "sha:123" in msg
        assert "layer" in msg

    def test_tag_action(self, registry_service: RegistryService):
        msg = registry_service._format_registry_event(
            username="user",
            action="delete",
            repo_name="repo",
            tag_name="v1",
            digest="sha:123",
            method="DELETE",
            url="/v2/repo/manifests/sha:123"
        )
        assert "user" in msg
        assert "delete" in msg
        assert "DELETE" in msg
        assert "repo" in msg

        assert "v1" in msg
        assert "tag" in msg

    def test_manifest_action(self, registry_service: RegistryService):
        msg = registry_service._format_registry_event(
            username="user",
            action="pull",
            repo_name="repo",
            tag_name=None,
            digest="sha:123",
            method="GET",
            url="/v2/repo/manifests/sha:123"
        )
        assert "user" in msg
        assert "pull" in msg
        assert "repo" in msg
        assert "GET" in msg

        assert "manifest" in msg
        assert "sha:123" in msg

    def test_referrers_action(self, registry_service: RegistryService):
        msg = registry_service._format_registry_event(
            username="user",
            action="pull",
            repo_name="repo",
            tag_name=None,
            digest="sha:123",
            method="GET",
            url="/v2/repo/referrers/sha:123"
        )
        assert "user" in msg
        assert "pull" in msg
        assert "repo" in msg
        assert "GET" in msg

        assert "referrers" in msg
        assert "sha:123" in msg

    def test_unsupported_event_raises(self, registry_service: RegistryService):
        with pytest.raises(ValueError):
            registry_service._format_registry_event(
                username="user",
                action="unknown",
                repo_name="repo",
                tag_name=None,
                digest="sha:123",
                method="POST",
                url="/v2/repo/..."
            )

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
    