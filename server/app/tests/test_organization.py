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
    service.user_repo = MagicMock()
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
        """ Test case for when the user is eligible and organization does exist. """
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

    @pytest.mark.parametrize("user_type", [("user"), ("admin")])
    def integration_test(self, user_type):
        with TestClient(app) as client:
            def add_user(username):
                data = {
                    "username": username,
                    "email": f"{username}@gmail.com",
                    "password": "12345678"
                }
                response = client.post("/api/v1/users/", json=data)
                return response.json()

            def log_in(username: str, password: str = "12345678"):
                data = {
                    "username": username,
                    "password": password
                }
                response = client.post("/api/v1/users/login", json=data)
                if response.status_code == 400:
                    assert response.json() == False
                jwt = response.json()["token"]
                return jwt

            def change_superadmin_password():
                # [1] Loading the super admin credentials
                config_file = "./volume-server-cfg/superadmin_password.txt"

                with open(config_file, "r") as f:
                    old_password = f.readline()

                jwt = log_in("admin", old_password)
                header = {"Authorization": f"Bearer {jwt}"}

                # [2] Changing the super admin password
                data = {
                    "old_password": old_password,
                    "new_password": "12345678"
                }
                response = client.post("/api/v1/users/password", json=data, headers=header)
                assert response.is_success

            def add_admin(admin_username: str) -> dict:
                jwt = log_in("admin", "12345678")
                header = {"Authorization": f"Bearer {jwt}"}
                data = {
                    "username": admin_username,
                    "email": f"{admin_username}@gmail.com",
                    "password": "12345678"
                }
                response = client.post("/api/v1/users/register-admin", json=data, headers=header)
                created_admin = response.json()

                return created_admin

            def add_org(username, name: str) -> dict:
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                dto1 = {
                    "name": name,
                    "desc": "",
                    "owner"
                    "image": None
                }
                return client.post("/api/v1/organizations", json=dto1, headers=header).json()

            def update_desc(username: str, org_name: str, desc: str):
                jwt = log_in(username)
                header = {"Authorization": f"Bearer {jwt}"}

                data = {
                    "desc": desc
                }

                response = client.put(f"/api/v1/organizations/{org_name}/desc", json=data, headers=header)
                return response

            if (user_type == "user"):
                add_user("u1")
                add_user("u2")
            else:
                change_superadmin_password()
                add_admin("u1")
                add_admin("u2")

            o1 = add_org("u1", "o1")

            # User who is the organization owner
            assert update_desc("u1", o1["name"], "new desc").is_success
            # User who is trying to update a non existing organization
            assert update_desc("u1", "unknown org", "new desc").status_code == 400
            # User who is not an organization owner
            assert update_desc("u2", o1["id"], "new desc").status_code == 400


class TestFindMembersOfOrg:
    def test_non_eligible_user(self, org_service):
        """ Test case for when user is not in organization """
        org_id = 1
        user_id = 5

        org_service.org_repo.user_is_in_org.return_value = False

        with pytest.raises(AccessDeniedException):
            org_service.find_members_of_org(org_id, user_id)

        org_service.org_repo.user_is_in_org.assert_called_once_with(user_id, org_id)
        org_service.org_repo.find_members_of_org.assert_not_called()

    def test_successfully_find_members(self, org_service):
        """ Test case for when user is in organization and therefore the organization has at least one member"""
        org_id = 1
        user_id = 5

        member1 = MagicMock(spec=User)
        expected_members = [member1]

        org_service.org_repo.user_is_in_org.return_value = True
        org_service.org_repo.find_members_of_org.return_value = expected_members

        result = org_service.find_members_of_org(org_id, user_id)

        org_service.org_repo.user_is_in_org.assert_called_once_with(user_id, org_id)
        org_service.org_repo.find_members_of_org.assert_called_once_with(org_id)
        assert result == expected_members


class TestAddMembersToOrg:
    def test_org_not_exists(self, org_service):
        """ Test case for when organization does not exist"""
        org_id = 1
        owner_id = 10
        new_members_ids = [2, 3]

        org_service.org_repo.find_by_id.return_value = None

        with pytest.raises(NotFoundException):
            org_service.add_members_to_org(org_id, new_members_ids, owner_id)

        org_service.org_repo.find_by_id.assert_called_once_with(org_id)
        org_service.org_repo.add_user_to_org.assert_not_called()

    def test_user_is_not_owner_of_org(self, org_service):
        """ Test case for when user is not the owner of the organization"""
        owner_id = 10
        new_members_ids = [2, 3]
        org = MagicMock(spec=Organization)
        org.id = 1
        org.owner_id = 11
        org_service.org_repo.find_by_id.return_value = org

        with pytest.raises(AccessDeniedException):
            org_service.add_members_to_org(org.id, new_members_ids, owner_id)

        org_service.org_repo.find_by_id.assert_called_once_with(org.id)
        org_service.org_repo.add_user_to_org.assert_not_called()

    def test_skip_nonexistent_users(self, org_service):
        """ Test case for when nonexistent users are skipped """
        non_existent_users = [15, 16]
        org = MagicMock(spec=Organization)
        org.id = 1
        org.owner_id = 10
        org_service.org_repo.find_by_id.return_value = org
        org_service.user_repo.find_by_id.side_effect = [None, None]

        result = org_service.add_members_to_org(org.id, non_existent_users, org.owner_id)

        assert result == []
        assert org_service.user_repo.find_by_id.call_count == 2
        org_service.org_repo.add_user_to_org.assert_not_called()

    def test_skip_existing_members(self, org_service):
        """ Test case to skip users that already are members of organization """
        org = MagicMock(spec=Organization)
        org.id = 1
        org.owner_id = 10
        org_service.org_repo.find_by_id.return_value = org

        user = MagicMock(spec=User)
        user.id = 1
        org_service.user_repo.find_by_id.return_value = user
        org_service.org_repo.user_is_in_org.return_value = True

        result = org_service.add_members_to_org(org.id, [user.id], org.owner_id)

        assert result == []
        org_service.org_repo.add_user_to_org.assert_not_called()

    def test_partial_skip(self, org_service):
        """ Test case for when some users are added and some skipped"""
        org = MagicMock(spec=Organization)
        org.id = 1
        org.owner_id = 10
        org_service.org_repo.find_by_id.return_value = org

        valid_user = MagicMock(spec=User)
        valid_user.id = 2

        superadmin = MagicMock(spec=User)
        superadmin.id = 1
        superadmin.role = "superadmin"

        org_service.user_repo.find_by_id.side_effect = [
            valid_user,
            superadmin,
            None
        ]
        # False for valid_user, False for superadmin, not called for non-existant user
        org_service.org_repo.user_is_in_org.side_effect = [False, False]

        result = org_service.add_members_to_org(org.id, [2, 1, 66], org.owner_id)
        assert result == [valid_user]
        assert org_service.org_repo.add_user_to_org.call_count == 1
        org_service.org_repo.add_user_to_org.assert_called_once_with(org.id, 2)

    def test_successfully_add_members(self, org_service):
        """ Test case to add valid members to organization """
        org = MagicMock(spec=Organization)
        org.id = 1
        org.owner_id = 10
        org_service.org_repo.find_by_id.return_value = org

        user1 = MagicMock(spec=User)
        user1.id = 1
        user2 = MagicMock(spec=User)
        user2.id = 2

        org_service.user_repo.find_by_id.side_effect = [user1, user2]
        org_service.org_repo.user_is_in_org.return_value = False

        result = org_service.add_members_to_org(org.id, [user1.id, user2.id], org.owner_id)

        assert result == [user1, user2]
        assert org_service.org_repo.add_user_to_org.call_count == 2

    def test_search_users_and_add_them_to_org_integration(self):
        with TestClient(app) as client:
            def create_user(username: str, email: str, password: str = "Password123") -> dict:
                data = {"username": username, "email": email, "password": password}
                response = client.post("/api/v1/users", json=data)
                assert response.status_code == 200
                return response.json()

            create_user("john", "john@mail.com")
            create_user("josh", "josh@mail.com")
            create_user("jane", "jane@mail.com")

            def login(username: str, password: str = "Password123") -> dict:
                data = {"username": username, "password": password}
                response = client.post("/api/v1/users/login", json=data)
                assert response.status_code == 200
                token = response.json()["token"]
                return {"Authorization": f"Bearer {token}"}

            create_user("user00", "user00@mail.com")
            user_header = login("user00")

            org_data = {"name": "TestOrg", "desc": "Integration test org", "image": None}
            org_response = client.post("/api/v1/organizations", json=org_data, headers=user_header)
            assert org_response.status_code == 200
            org_id = org_response.json()["id"]

            def search_users_by_username_prefix(query: str) -> dict:
                search_response = client.get(f"/api/v1/users/search/{query}?organization_id={org_id}",
                                             headers=user_header)
                assert search_response.status_code == 200
                return search_response.json()

            found_users = search_users_by_username_prefix("jo")
            assert len(found_users) == 2  # john + josh

            def add_members_to_org(user_ids: list) -> dict:
                add_members_response = client.post( f"/api/v1/organizations/{org_id}/addMember",
                    json=user_ids,
                    headers=user_header
                )
                assert add_members_response.status_code == 200
                return add_members_response.json()

            user_ids_to_add = [user["id"] for user in found_users]
            add_members_to_org(user_ids_to_add)

            # Verify they are indeed in the org
            members_response = client.get(f"/api/v1/organizations/{org_id}/members", headers=user_header)
            assert members_response.status_code == 200
            members = members_response.json()
            member_usernames = [m["username"] for m in members]

            assert "john" in member_usernames
            assert "josh" in member_usernames
            assert "jane" not in member_usernames



