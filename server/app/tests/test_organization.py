from unittest.mock import MagicMock
import pytest
from app.api.org.org_service import OrganizationService
from app.api.org.org_dto import OrganizationCreateDTO
from app.api.org.org_model import Organization
from app.api.config.exception_handler import FieldTakenException

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
    new_org = MagicMock()
    Organization.model_validate = MagicMock(return_value=new_org)
    org_service.org_repo.add.return_value = new_org

    result = org_service.add(user_id, dto)

    org_service.org_repo.find_by_name.assert_called_once_with("some org")
    org_service.org_repo.add.assert_called_once_with(new_org)
    org_service.add_user_to_org.assert_called_once_with(new_org.id, user_id)
    assert result == new_org


def test_add_org_name_taken(org_service):
    user_id = 1
    dto = OrganizationCreateDTO(name="some org", desc="", image=None)
    org_service.org_repo.find_by_name.return_value = MagicMock()

    with pytest.raises(FieldTakenException):
        org_service.add(user_id, dto)