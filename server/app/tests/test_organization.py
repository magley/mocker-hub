from unittest.mock import MagicMock, call
from fastapi.testclient import TestClient
import pytest
from app.api.org.org_service import OrganizationService
from app.api.org.org_dto import OrganizationCreateDTO, OrganizationDescUpdateDTO
from app.api.config.exception_handler import AccessDeniedException, FieldTakenException, NotFoundException
from app.api.config.exception_handler import FieldTakenException
from app.api.main import app
from app.api.repo.repo_model import Repository
from app.api.org.org_model import Organization
from app.api.user.user_model import User


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


def test_find_org_names_by_ids_valid(org_service):
    """Test case for when valid org ids are passed."""
    ids = [1, 2]
    expected_output = {1: "abc", 2: "def"}
    org_service.org_repo.find_orgs_by_ids.return_value = expected_output

    result = org_service.find_org_names_by_ids(ids)

    assert result == expected_output
    org_service.org_repo.find_orgs_by_ids.assert_called_once_with(ids)


def test_find_org_names_by_ids_empty_list(org_service):
    """Test case for when an empty list is passed."""
    ids = []
    org_service.org_repo.find_orgs_by_ids.return_value = {}

    result = org_service.find_org_names_by_ids(ids)
    assert result == {}
    org_service.org_repo.find_orgs_by_ids.assert_called_once_with(ids)


def test_find_org_names_by_ids_partial_match(org_service):
    """Test case for when some org ids are valid and others are not."""
    ids = [1, 2, 999999]
    expected_output = {1: "abc", 2: "def"}
    org_service.org_repo.find_orgs_by_ids.return_value = expected_output

    result = org_service.find_org_names_by_ids(ids)

    assert result == expected_output
    org_service.org_repo.find_orgs_by_ids.assert_called_once_with(ids)


def test_find_org_names_by_ids_no_matches(org_service):
    """Test case for when no org ids match."""
    ids = [999998, 999999]
    expected_output = {}
    org_service.org_repo.find_orgs_by_ids.return_value = expected_output

    result = org_service.find_org_names_by_ids(ids)

    assert result == expected_output
    org_service.org_repo.find_orgs_by_ids.assert_called_once_with(ids)

class TestGetOrgNamesFromRepos:
    ''' 
    The following tests for `get_org_names_from_repos` are trivial,
    since the observed method is mostly dependent on `find_org_names_by_ids`
    which is already tested in various cases. 
    '''

    def test_repos_is_empty(self, org_service):
        """Test case for when repos is emtpy."""
        expected_output = {}
        org_service.org_repo.find_orgs_by_ids.return_value = expected_output
        repos = []
        result = org_service.get_org_names_from_repos(repos)
        assert result == expected_output
        org_service.org_repo.find_orgs_by_ids.assert_called_once_with([])

    def test_repos_is_not_empty(self, org_service):
        """Test case for when repos is not emtpy."""
        o1 = MagicMock(spec=Organization)
        o2 = MagicMock(spec=Organization)
        o1.name = "org1"
        o2.name = "org2"
        o1.id = 1
        o2.id = 2
        r1 = MagicMock(spec=Repository)
        r2 = MagicMock(spec=Repository)
        r1.organization_id = o1.id
        r2.organization_id = o2.id

        ids = [o1.id, o2.id]
        expected_output = {o1.id: o1.name, o2.id: o2.name}
        org_service.org_repo.find_orgs_by_ids.return_value = expected_output

        repos = [r1, r2]

        result = org_service.get_org_names_from_repos(repos)
        assert result[o1.id] == o1.name
        assert result[o2.id] == o2.name
        org_service.org_repo.find_orgs_by_ids.assert_called_once_with(ids)

class TestUpdateOrgAttrs():
        
    def test_org_not_exist(self, org_service):
        """ Test case for when the org does not exist. """
        org_name = "o1"
        org_service.org_repo.find_by_name.return_value = None

        with pytest.raises(NotFoundException):
            org_service.update_org_attrs(org_name, desc="desc123")
        
        org_service.org_repo.find_by_name.assert_called_once_with(org_name)

    def test_attributes_not_passed(self, org_service):
        """ Test case for when no attributes are passed. """ 
        org = MagicMock(spec=Organization)
        org.id = 1
        org.name = "o1"
        org.desc = "desc"
        org_service.org_repo.find_by_name.return_value = org

        result = org_service.update_org_attrs(org.name)

        assert result == org 
        assert result.id == org.id
        assert result.name == org.name
        assert result.desc == org.desc
        org_service.org_repo.find_by_name.assert_called_once_with(org.name)

    def test_attribute_not_exist(self, org_service):
        """ Test case for when a specified attribute does not exist. """  
        org = MagicMock(spec=Organization)
        org.id = 1
        org.name = "o1"
        org.desc = "desc"
        org_service.org_repo.find_by_name.return_value = org
        org_service.org_repo.set_attribute.side_effect = ValueError("unknown attribute")

        with pytest.raises(ValueError) as e: 
            org_service.update_org_attrs(org.name, unknown_attr="fail")
        
        assert "unknown attribute" in str(e.value)
        org_service.org_repo.find_by_name.assert_called_once_with(org.name)
        org_service.org_repo.set_attribute.assert_called_once_with(org, "unknown_attr", "fail")
    
    def test_successfully_update_attributes(self, org_service):
        """ Test case for when the attributes exist. """
        org = MagicMock(spec=Organization)
        org.id = 1
        org.desc = "desc"
        org.deleting = False
        org_service.org_repo.find_by_name.return_value = org

        def mock_set_attribute(org, attr, value):
            setattr(org, attr, value)
            return org
        org_service.org_repo.set_attribute.side_effect = mock_set_attribute

        result = org_service.update_org_attrs(name=org.name, deleting=True, desc="new_desc")

        assert result.id == 1
        assert result.deleting == True
        assert result.desc == "new_desc"
        org_service.org_repo.find_by_name.assert_called_once_with(org.name)
        expected_calls = [
            call(org, "deleting", True), 
            call(org, "desc", "new_desc"), 
        ]
        assert org_service.org_repo.set_attribute.call_args_list == expected_calls

class TestFindByName:

    def test_org_not_exist(self, org_service):
        """ Test case for when the org does not exist. """
        org_name = "o999"
        org_service.org_repo.find_by_name.return_value = None

        with pytest.raises(NotFoundException): 
            org_service.find_by_name(org_name)

        org_service.org_repo.find_by_name.assert_called_once_with(org_name)

    def test_org_exist(self, org_service):
        """ Test case for when the org exists. """
        org = MagicMock(spec=Organization)
        org.name = "o1"
        org_service.org_repo.find_by_name.return_value = org

        result = org_service.find_by_name(org.name)

        org_service.org_repo.find_by_name.assert_called_once_with(org.name)
        assert result == org

class TestUpdateOrgDescByName:

    def test_org_not_exist(self, org_service):
        """ Test case for when organization does not exist. """   
        user_id = 1
        dto = OrganizationDescUpdateDTO(desc="new desc")
        org_name = "o1"
        org_service.org_repo.find_by_name.return_value = None

        with pytest.raises(NotFoundException):
            org_service.update_desc_by_name(org_name, dto, user_id)

        org_service.org_repo.set_attribute.assert_not_called()
        org_service.org_repo.find_by_name.assert_called_once_with(org_name)

    def test_non_eligible_user(self, org_service):
        """ Test case for when the user is not eligible to make an update. """   
        user_id = 1
        dto = OrganizationDescUpdateDTO(desc="new desc")

        owner = MagicMock(spec=User)
        owner.id = 999999
        org = MagicMock(spec=Organization)
        org.name = "o1"
        org.owner = owner        

        org_service.org_repo.find_by_name.return_value = org

        with pytest.raises(AccessDeniedException):
            org_service.update_desc_by_name(org.name, dto, user_id)

        org_service.org_repo.set_attribute.assert_not_called()
        org_service.org_repo.find_by_name.assert_called_once_with(org.name)

    def test_successful_update(self, org_service):
        """ Test case for when the user is eligble and org does exist. """   
        dto = OrganizationDescUpdateDTO(desc="new desc")
        user = MagicMock(spec=User)
        user.id = 1
        org = MagicMock(spec=Organization)
        org.name = "o1"
        org.owner = user
        org.desc = "old desc"

        org_service.org_repo.find_by_name.return_value = org

        org.desc = "new desc"
        org_service.org_repo.set_attribute.return_value = org

        result = org_service.update_desc_by_name(org.name, dto, user.id)

        assert result.desc == "new desc"

        org_service.org_repo.set_attribute.assert_called_once_with(org, "desc", "new desc")
        expected_calls = [call(org.name), call(org.name)]
        assert org_service.org_repo.find_by_name.call_args_list == expected_calls

