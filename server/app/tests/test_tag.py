from fastapi import Response
from fastapi.testclient import TestClient
import pytest
from unittest.mock import MagicMock, patch

from sqlmodel import SQLModel

from app.api.config.exception_handler import AccessDeniedException, NotFoundException, UserException
from app.api.repo.repo_model import Repository
from app.api.tags.tag_model import Tag
from app.api.tags.tag_service import TagService
from app.api.user.user_model import User
from app.api.main import app
from app.api.config.pagination import PaginationParams
from app.api.config.database import get_database


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    from app.api.config.database import engine
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)


@pytest.fixture
def tag_service():
    service = TagService(MagicMock())
    
    service.repo_repo = MagicMock()
    service.tag_repo = MagicMock()
    service.access_control_service = MagicMock()

    return service

class TestCreateOrTouch:
    def test_create_tag_success(self, tag_service: "TagService"):
        user_id = 1
        repo_id = 1
        tag_name = "v1.0"
        
        repo = Repository(id=1, canonical_name="repo1")
        tag_service.repo_repo.find_by_id.return_value = repo
        tag_service.access_control_service.has_write_access.return_value = True
        tag_service.tag_repo.find_by_name_and_repo_id.return_value = None
        new_tag = Tag(name=tag_name, repository_id=repo_id)
        tag_service.tag_repo.add = MagicMock(return_value=new_tag)

        result = tag_service.create_or_touch(user_id, repo_id, tag_name)

        assert result == new_tag
        tag_service.tag_repo.find_by_name_and_repo_id.assert_called_with(tag_name, repo_id)

    def test_create_tag_access_denied(self, tag_service: "TagService"):
        user_id = 2
        repo_id = 1
        tag_name = "v1.0"
        
        repo = Repository(id=1, canonical_name="repo1")
        tag_service.repo_repo.find_by_id.return_value = repo
        tag_service.access_control_service.has_write_access.return_value = False

        with pytest.raises(AccessDeniedException):
            tag_service.create_or_touch(user_id, repo_id, tag_name)

    def test_create_tag_repo_not_found(self, tag_service: "TagService"):
        user_id = 1
        repo_id = 1
        tag_name = "v1.0"
        
        tag_service.repo_repo.find_by_id.return_value = None
        tag_service.tag_repo.find_by_name_and_repo_id.return_value = None

        with pytest.raises(NotFoundException):
            tag_service.create_or_touch(user_id, repo_id, tag_name)

class TestRemoveTag:
    def test_remove_tag_success(self, tag_service: "TagService"):
        user_id = 1
        tag_id = 1
        
        tag = Tag(id=tag_id, name="v1.0", repository_id=1)
        repo = Repository(id=1, canonical_name="repo1")
        
        tag_service.tag_repo.find_by_id.return_value = tag
        tag_service.repo_repo.find_by_id.return_value = repo
        tag_service.access_control_service.has_write_access.return_value = True
        tag_service.tag_repo.remove = MagicMock()

        tag_service.remove_tag(user_id, tag_id)

        tag_service.tag_repo.remove.assert_called_once_with(tag)

    def test_remove_tag_access_denied(self, tag_service: "TagService"):
        user_id = 2
        tag_id = 1
        
        repo = Repository(id=1, canonical_name="repo1")
        tag = Tag(id=tag_id, name="v1.0", repository_id=1, repository=repo)
        
        tag_service.tag_repo.find_by_id.return_value = tag
        tag_service.repo_repo.find_by_id.return_value = repo
        tag_service.access_control_service.has_write_access.return_value = False

        with pytest.raises(AccessDeniedException):
            tag_service.remove_tag(user_id, tag_id)

    def test_remove_tag_not_found(self, tag_service: "TagService"):
        user_id = 1
        tag_id = 999
        
        tag_service.tag_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            tag_service.remove_tag(user_id, tag_id)

class TestTouchTag:
    def test_touch_tag_success(self, tag_service: "TagService"):
        user_id = 1
        tag_id = 1
        
        tag = Tag(id=tag_id, name="v1.0", repository_id=1)
        repo = Repository(id=1, canonical_name="repo1")
        
        tag_service.tag_repo.find_by_id.return_value = tag
        tag_service.repo_repo.find_by_id.return_value = repo
        tag_service.access_control_service.has_write_access.return_value = True
        tag_service.tag_repo.update_last_push = MagicMock(return_value=tag)

        result = tag_service._touch_tag(user_id, tag_id)

        assert result == tag
        tag_service.tag_repo.update_last_push.assert_called_once_with(tag)

    def test_touch_tag_access_denied(self, tag_service: "TagService"):
        user_id = 2
        tag_id = 1
        
        repo = Repository(id=1, canonical_name="repo1")
        tag = Tag(id=tag_id, name="v1.0", repository_id=1, repository=repo)
        
        tag_service.tag_repo.find_by_id.return_value = tag
        tag_service.repo_repo.find_by_id.return_value = repo
        tag_service.access_control_service.has_write_access.return_value = False

        with pytest.raises(AccessDeniedException):
            tag_service._touch_tag(user_id, tag_id)

    def test_touch_tag_not_found(self, tag_service: "TagService"):
        user_id = 1
        tag_id = 999
        
        tag_service.tag_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            tag_service._touch_tag(user_id, tag_id)

class TestSearchTags:
    def test_search_tags_success(self, tag_service: "TagService"):
        repo_id = 1
        text = "v1.0"
        
        tags = [Tag(id=1, name="v1.0", repository_id=repo_id)]
        tag_service.tag_repo.find_by_text.return_value = tags

        result = tag_service.search_tags(repo_id, text)

        assert result == tags
        tag_service.tag_repo.find_by_text.assert_called_once_with(repo_id, text)

    def test_search_tags_no_results(self, tag_service: "TagService"):
        repo_id = 1
        text = "v2.0"
        
        tag_service.tag_repo.find_by_text.return_value = []

        result = tag_service.search_tags(repo_id, text)

        assert result == []
        tag_service.tag_repo.find_by_text.assert_called_once_with(repo_id, text)

    def test_search_tags__integration(self):
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
            
            def add_repo(username, repo_name):
                data = {
                    "name": repo_name,
                    "desc": "",
                    "public": True,
                    "organization_id": None,
                }
                header = {"Authorization": f"Bearer {log_in(username)}"}

                return client.post("/api/v1/repositories/", json=data, headers=header).json()
            
            def add_tag(user_id, repo_id, tag_name):
                # You can't add tags through the API, so we either insert into
                # the DB _or_ we somehow user the docker api.

                from app.api.tags.tag_service import TagService
                session = next(get_database())
                tag_service = TagService(session)

                return tag_service.create_or_touch(user_id, repo_id, tag_name)
            
            def search_tags(repo_canonical_name):
                return client.get(f"/api/v1/tags/?repo_name={repo_canonical_name}").json()

            u1 = add_user("u1")
            r1 = add_repo("u1", "r1")
            add_tag(u1['id'], r1['id'], 't1')
            add_tag(u1['id'], r1['id'], 't2')
            add_tag(u1['id'], r1['id'], 't3')
            add_tag(u1['id'], r1['id'], 't4')

            tags = search_tags(r1['canonical_name'])
            assert len(tags) == 4

class TestFilterTags:
    def test_filter_tags_success(self, tag_service: "TagService"):
        repo_name = "repo1"
        search_query = "v1.0"
        params = PaginationParams(page=1, size=10)
        
        tags = [Tag(id=1, name="v1.0", repository_id=1)]
        tag_service.tag_repo.filter.return_value = (tags, 1)

        result_tags, total_count = tag_service.filter(repo_name, search_query, params)

        assert result_tags == tags
        assert total_count == 1
        tag_service.tag_repo.filter.assert_called_once_with(repo_name, search_query, params)

    def test_filter_tags_no_results(self, tag_service: "TagService"):
        repo_name = "repo1"
        search_query = "v2.0"
        params = PaginationParams(page=1, size=10)
        
        tag_service.tag_repo.filter.return_value = ([], 0)

        result_tags, total_count = tag_service.filter(repo_name, search_query, params)

        assert result_tags == []
        assert total_count == 0
        tag_service.tag_repo.filter.assert_called_once_with(repo_name, search_query, params)

    def test_filter_tags__integration(self):
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
            
            def add_repo(username, repo_name):
                data = {
                    "name": repo_name,
                    "desc": "",
                    "public": True,
                    "organization_id": None,
                }
                header = {"Authorization": f"Bearer {log_in(username)}"}

                return client.post("/api/v1/repositories/", json=data, headers=header).json()
            
            def add_tag(user_id, repo_id, tag_name):
                # You can't add tags through the API, so we either insert into
                # the DB _or_ we somehow user the docker api.

                from app.api.tags.tag_service import TagService
                session = next(get_database())
                tag_service = TagService(session)

                return tag_service.create_or_touch(user_id, repo_id, tag_name)
            
            def filter_tags(repo_canonical_name, search_query):
                query_params = {
                    "repo_name": repo_canonical_name,
                    "search_query": search_query,
                    "sort_by": "",
                    "sort_order": "asc",
                    "page": 1,
                    "limit": 10,
                }
                query_params_str = ','.join(f"{k}={v}" for k, v in query_params.items())
                return client.get(f"/api/v1/tags/filter", params=query_params).json()['items']

            u1 = add_user("u1")
            r1 = add_repo("u1", "r1")
            add_tag(u1['id'], r1['id'], 'aaabbb')
            add_tag(u1['id'], r1['id'], 'aaa')
            add_tag(u1['id'], r1['id'], 'bbb')
            add_tag(u1['id'], r1['id'], 'ccc')

            assert len(filter_tags(r1['canonical_name'], '')) == 4
            assert len(filter_tags(r1['canonical_name'], 'a')) == 2
            assert len(filter_tags(r1['canonical_name'], 'b')) == 2
            assert len(filter_tags(r1['canonical_name'], 'ab')) == 1
            assert len(filter_tags(r1['canonical_name'], 'd')) == 0