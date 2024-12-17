from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest
from app.api.org.org_service import OrganizationService
from app.api.org.org_dto import OrganizationCreateDTO
from app.api.config.exception_handler import FieldTakenException
from app.api.config.exception_handler import FieldTakenException
from app.api.main import app


@pytest.fixture
def org_service():
    session = MagicMock()
    service = OrganizationService(session)
    
    service.org_repo = MagicMock()
    service.add_user_to_org = MagicMock()
    return service


def test_add_org(org_service):
    user_id = 1
    dto = OrganizationCreateDTO(name="some org", desc="", image=None)
    org_service.org_repo.find_by_name.return_value = None

    org_service.add(user_id, dto)

    org_service.org_repo.find_by_name.assert_called_once_with("some org")
    org_service.org_repo.add.assert_called_once()
    org_service.add_user_to_org.assert_called_once()


def test_add_org_name_taken(org_service):
    user_id = 1
    dto = OrganizationCreateDTO(name="some org", desc="", image=None)
    org_service.org_repo.find_by_name.return_value = MagicMock()

    with pytest.raises(FieldTakenException):
        org_service.add(user_id, dto)


def test_add_org_integration():
    with TestClient(app) as client:
        # Create test user
        dto_register = {
            "username": "u1",
            "email": "u1@gmail.com",
            "password": "1234"
        }
        response = client.post("/api/v1/users/", json=dto_register)
        created_user = response.json()

        # Sign in with the test user
        dto_login = {
            "username": "u1",
            "password": "1234"
        }
        response = client.post("/api/v1/users/login", json=dto_login)
        jwt = response.json()["token"]
        header = {
            "Authorization": f"Bearer {jwt}"
        }

        # Create first organization

        dto1 = {
            "name": "my-org",
            "desc": "",
            "image": None
        }
        response = client.post("/api/v1/organizations", json=dto1, headers=header)

        org1 = response.json()
        assert response.is_success
        assert org1["name"] == dto1["name"]
        assert org1["desc"] == dto1["desc"]
        assert org1["owner_id"] == created_user["id"]

        # Try to create org with same name

        dto2 = {
            "name": "my-org",
            "desc": "",
            "image": None
        }
        response = client.post("/api/v1/organizations", json=dto2, headers=header)

        org1 = response.json()
        assert response.is_error
