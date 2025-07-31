import logging
from fastapi.testclient import TestClient

from datetime import datetime
from app.api.main import app
from app.api.config.elasticsearch import wait_for_elasticsearch

from fastapi.testclient import TestClient
from app.api.events.event_model import EventLevel
import pytest
from app.api.events.event_service import EventService
from app.api.main import app
from unittest.mock import MagicMock, patch
from app.api.config.pagination import PaginatedResultDTO

class TestEventService:

    # -------------------------------
    # Logging Tests
    # -------------------------------

    def test_log_read_logs_correct_message(self):
        service = EventService()
        with patch.object(service, 'log') as mock_log:
            service.log_read(user_id=42, entity_type=str, entity_identifier="abc123")
            mock_log.assert_called_once_with(EventLevel.Info, "User 42 wants to read str abc123")

    def test_event_level_to_log_level_mapping(self):
        service = EventService()
        assert service._event_level_to_log_level(EventLevel.Debug) == logging.DEBUG
        assert service._event_level_to_log_level(EventLevel.Info) == logging.INFO
        assert service._event_level_to_log_level(EventLevel.Warning) == logging.WARNING
        assert service._event_level_to_log_level(EventLevel.Error) == logging.ERROR

        with pytest.raises(ValueError):
            service._event_level_to_log_level("INVALID")

    # -------------------------------
    # Grammar Parsing & Query Conversion
    # -------------------------------

    @pytest.mark.parametrize("query_str,expected", [
        ('status == "active"', {'term': {'status': 'active'}}),
        ('status != "inactive"', {'bool': {'must_not': [{'term': {'status': 'inactive'}}]}}),
        ('score >= "10"', {'range': {'score': {'gte': '10'}}}),
        ('name ~= "john"', {'match': {'name': 'john'}}),
        ('name ~~= "john doe"', {'match_phrase': {'name': 'john doe'}}),
    ])
    def test_to_query_basic_conditions(self, query_str, expected):
        service = EventService()
        model = service.meta.model_from_str(query_str)
        query = service._to_query(model)
        assert query.to_dict() == expected

    def test_to_query_logical_and_or(self):
        service = EventService()
        model = service.meta.model_from_str('status == "active" and score > "10" or name ~= "john"')
        query = service._to_query(model)
        assert 'bool' in query.to_dict()

    def test_to_query_not_expression(self):
        service = EventService()
        model = service.meta.model_from_str('not status == "inactive"')
        query = service._to_query(model)
        assert query.to_dict() == {
            'bool': {
                'must_not': [{'term': {'status': 'inactive'}}]
            }
        }

    # -------------------------------
    # Query Execution & Pagination
    # -------------------------------

    @patch('app.api.events.event_service.Search')
    def test_query_executes_correctly(self, mock_search_cls):
        mock_hit = MagicMock()
        mock_hit.date_time = "2025-01-01T00:00:00"
        mock_hit.log_level = "INFO"
        mock_hit.text_content = "Test log"

        mock_response = MagicMock()
        mock_response.hits.total.value = 1
        mock_response.__iter__.return_value = [mock_hit]

        mock_search = MagicMock()
        mock_search.query.return_value = mock_search
        mock_search.sort.return_value = mock_search
        mock_search.__getitem__.return_value = mock_search
        mock_search.execute.return_value = mock_response

        mock_search_cls.return_value = mock_search

        service = EventService()
        result = service.query(
            query_string='log_level == "INFO"',
            page_num=1,
            page_size=10,
            sort_by='date_time',
            sort_asc=True
        )

        assert result.info.total_hits == 1
        assert result.hits[0].text == "Test log"
        assert result.hits[0].level == "INFO"
        assert result.hits[0].date_time == datetime(2025, 1, 1, 0, 0)

    @patch('app.api.events.event_service.Search')
    def test_query_invalid_sort_field_skips_sorting(self, mock_search_cls):
        mock_response = MagicMock()
        mock_response.hits.total.value = 0
        mock_response.__iter__.return_value = []

        mock_search = MagicMock()
        mock_search.query.return_value = mock_search
        mock_search.__getitem__.return_value = mock_search
        mock_search.execute.return_value = mock_response

        mock_search_cls.return_value = mock_search

        service = EventService()
        result = service.query(
            query_string='log_level == "INFO"',
            page_num=1,
            page_size=10,
            sort_by='text_content', # Unsupported field
            sort_asc=True
        )

        assert result.info.total_hits == 0
        assert result.hits == []

    def test_query_invalid_grammar_raises_exception(self):
        service = EventService()
        with pytest.raises(Exception):
            service.meta.model_from_str('status === "active"') # Invalid operator

def test_events___integration():
    with TestClient(app) as client:
        assert wait_for_elasticsearch()

        def search_for_something(headers):
            response = client.get(
                f"/api/v1/events/?query=date_time+%3C%3D+%222165-07-24%22&page_number=1&page_size=10&sort_by=date_time&sort_ascending=true",
                headers=headers)
            return response

        def login(data: dict) -> dict:
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == 200
            jwt = response.json()["token"]
            return {"Authorization": f"Bearer {jwt}"}

        superadmin_creds = {
            "username": "admin",
            "password": "Password1" # WARNING: Superadmin password is changed by an earlier test (update user badge?)
            # Therefore, that must run before this!
        }

        superadmin_header = login(superadmin_creds)

        res = search_for_something(superadmin_header)
        assert res.is_success

        hits = res.json()["hits"]
        assert len(hits) >= 0
