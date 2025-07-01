import asyncio
from app.api.events.event_model import EventLevel
import pytest
from app.api.events.event_service import EventService
from app.api.jobs.jobs_service import JobsService
from sqlmodel import SQLModel
from unittest.mock import MagicMock
from app.api.registry.registry_service import RegistryService
from app.api.registry.registry_dto import DeleteResponseDTO
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.access_control.access_control_service import AccessControlService
from app.api.registry.registry_client import RegistryClient
from app.api.config.exception_handler import NotFoundException, NotInRelationshipException, RegistryException
from app.api.repo.repo_model import Repository
from app.api.tags.tag_model import Tag
from app.api.tags.tag_service import TagService

@pytest.fixture
def jobs_service() -> JobsService:
    service = JobsService()
    return service

@pytest.fixture
def registry_service() -> RegistryService:
    mock_session = MagicMock()
    service = RegistryService(mock_session)
    
    service.user_service = MagicMock(UserService)
    service.repo_service = MagicMock(RepositoryService)
    service.access_control_service = MagicMock(AccessControlService)
    service.tag_service = MagicMock(TagService)
    service.event_service = MagicMock(EventService)

    return service

@pytest.fixture(scope="function", autouse=True)
def reset_db():
    from app.api.config.database import engine
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

class TestGetCurrentJobMetadata:

    def test_job_is_known(self, monkeypatch, jobs_service):
        """ Test case for when the job is known. """
        class JobMock:
            def __init__(self, id, origin, retries_left):
                self.id = id
                self.origin = origin
                self.retries_left = retries_left

        job = JobMock(id="123", origin="delete_tag", retries_left=5)
        monkeypatch.setattr("app.api.jobs.jobs_service.get_current_job", lambda: job)
        result = jobs_service._get_current_job_metadata()
        assert result == {
            "id": "123",
            "origin": "delete_tag",
            "retries_left": 5
        }

    def test_job_is_unknown(self, monkeypatch, jobs_service):
        """ Test case for when the job is unknown. """
        monkeypatch.setattr("app.api.jobs.jobs_service.get_current_job", lambda: None)
        result = jobs_service._get_current_job_metadata()
        assert result == {
            "id": "unknown",
            "origin": "unknown",
            "retries_left": "unknown"
        }

class TestDeleteTagJob:

    def test_repo_not_exist(self, monkeypatch, jobs_service, registry_service):
        """ Test case for when the repository does not exist. """
        repo_id = 99999
        tag_name = "tag"
        username = "user"
        mock_client = MagicMock(spec=RegistryClient)
        mock_session = MagicMock()
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        monkeypatch.setattr(
            "app.api.jobs.jobs_service.init_registry_client", 
            lambda: mock_client
        )
        monkeypatch.setattr(
            "app.api.registry.registry_service.RegistryService",
            lambda session: registry_service
        )
        monkeypatch.setattr(
            jobs_service, 
            "_get_session", 
            lambda: mock_session
        )
        monkeypatch.setattr(
            jobs_service,
            "_get_event_loop",
            lambda: mock_loop
        )
        registry_service.repo_service.find_by_id.side_effect = NotFoundException(Repository, repo_id)

        jobs_service.delete_tag_job(username, repo_id, tag_name)

        mock_loop.run_until_complete.assert_not_called()
        registry_service.repo_service.find_by_id.assert_called_once_with(repo_id)
        registry_service.event_service.log.assert_called_once_with(EventLevel.Info, f"Repository with identifier '{repo_id}' has already been deleted by another job.")

    def test_tag_not_exist(self, monkeypatch, jobs_service, registry_service):
        """ Test case for when the tag does not exist. """
        repo_id = 99999
        username = "user"
        tag_name = "tag"
        mock_client = MagicMock(spec=RegistryClient)
        mock_session = MagicMock()
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        monkeypatch.setattr(
            "app.api.jobs.jobs_service.init_registry_client", 
            lambda: mock_client
        )
        monkeypatch.setattr(
            "app.api.registry.registry_service.RegistryService",
            lambda session: registry_service
        )
        monkeypatch.setattr(
            jobs_service, 
            "_get_session", 
            lambda: mock_session
        )
        monkeypatch.setattr(
            jobs_service,
            "_get_event_loop",
            lambda: mock_loop
        )
        registry_service.tag_service.find_by_name_and_repo_id.side_effect = NotInRelationshipException(Repository, repo_id, Tag, tag_name)

        jobs_service.delete_tag_job(username, repo_id, tag_name)
    
        mock_loop.run_until_complete.assert_not_called()
        registry_service.repo_service.find_by_id.assert_called_once_with(repo_id)
        registry_service.tag_service.find_by_name_and_repo_id.assert_called_once_with(tag_name, repo_id)
        registry_service.event_service.log.assert_called_once_with(EventLevel.Info, f"Tag '{tag_name}' has already been deleted by another job.")

    def test_tag_is_deleted(self, monkeypatch, jobs_service, registry_service):
        """ Test case for when the tag is deleted. """

        mock_client = MagicMock(spec=RegistryClient)
        mock_session = MagicMock()
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        monkeypatch.setattr(
            "app.api.jobs.jobs_service.init_registry_client", 
            lambda: mock_client
        )
        monkeypatch.setattr(
            "app.api.registry.registry_service.RegistryService",
            lambda session: registry_service
        )
        monkeypatch.setattr(
            jobs_service, 
            "_get_session", 
            lambda: mock_session
        )
        monkeypatch.setattr(
            jobs_service,
            "_get_event_loop",
            lambda: mock_loop
        )

        username = "user"
        repo = MagicMock(spec=Repository(id=1, name="repo"))
        tag = MagicMock(spec=Tag(id=1, name="tag"))
        registry_service.repo_service.find_by_id.return_value = repo
        registry_service.tag_service.find_by_name_and_repo_id.return_value = tag
        response_dto = DeleteResponseDTO(message=f"Tag '{tag.name}' successfully deleted from repository '{repo.canonical_name}'.")
        mock_loop.run_until_complete.return_value = response_dto

        jobs_service.delete_tag_job(username, repo.id, tag.name)
    
        registry_service.repo_service.find_by_id.assert_called_once_with(repo.id)
        registry_service.tag_service.find_by_name_and_repo_id.assert_called_once_with(tag.name, repo.id)
        mock_loop.run_until_complete.assert_called_once()
        registry_service.event_service.log.assert_called_once_with(EventLevel.Info, response_dto.message)

    def test_deleting_tag_raises_unexpected_exception(self, monkeypatch, jobs_service, registry_service):
        """ Test case for when the tag is being deleted and an unexpected exception occurred. """

        mock_client = MagicMock(spec=RegistryClient)
        mock_session = MagicMock()
        mock_loop = MagicMock(spec=asyncio.AbstractEventLoop)
        monkeypatch.setattr(
            "app.api.jobs.jobs_service.init_registry_client", 
            lambda: mock_client
        )
        monkeypatch.setattr(
            "app.api.registry.registry_service.RegistryService",
            lambda session: registry_service
        )
        monkeypatch.setattr(
            jobs_service, 
            "_get_session", 
            lambda: mock_session
        )
        monkeypatch.setattr(
            jobs_service,
            "_get_event_loop",
            lambda: mock_loop
        )

        class JobMock:
            def __init__(self, id, origin, retries_left):
                self.id = id
                self.origin = origin
                self.retries_left = retries_left
        job = JobMock(id="123", origin="delete_tag", retries_left=5)
        monkeypatch.setattr("app.api.jobs.jobs_service.get_current_job", lambda: job)

        username = "user"
        repo = MagicMock(spec=Repository(id=1, name="repo"))
        tag = MagicMock(spec=Tag(id=1, name="tag"))
        registry_service.repo_service.find_by_id.return_value = repo
        registry_service.tag_service.find_by_name_and_repo_id.return_value = tag
        mock_loop.run_until_complete.side_effect = RegistryException(502, "distribution is not available")

        with pytest.raises(RegistryException): 
            jobs_service.delete_tag_job(username, repo.id, tag.name)
    
        registry_service.repo_service.find_by_id.assert_called_once_with(repo.id)
        registry_service.tag_service.find_by_name_and_repo_id.assert_called_once_with(tag.name, repo.id)
        mock_loop.run_until_complete.assert_called_once()
        registry_service.event_service.log.assert_called_once_with(
            EventLevel.Error, 
            (
                f"Tag '{tag.name}' is not deleted (job_id={job.id}, retries_left={job.retries_left}, queue={job.origin}). " 
                f"ADMIN: For an immediate response, check both the queue dashboard and the log trace."
            )
        )

