from datetime import datetime

from fastapi.testclient import TestClient
import pytest
import unittest.mock as mock

from sqlmodel import SQLModel, Session

from app.api.config.pagination import PaginatedResultDTO
from app.api.config.security import hash_password
from app.api.repo.repo_model import Repository
from app.api.repo.repo_repo import RepositoryRepo
from app.api.user.user_dto import UserPasswordChangeDTO, UserRegisterDTO, UserDTO
from app.api.user.user_model import User, UserRole, UserBadge
from app.api.user.user_repo import UserRepo
from app.api.user.user_service import UserService
from app.api.org.org_repo import OrganizationRepo
from app.api.config.exception_handler import NotFoundException, UserException, FieldTakenException, \
    AccessDeniedException
from app.api.main import app


@pytest.fixture
def mock_session():
    return mock.MagicMock(spec=Session)

@pytest.fixture
def mock_user_repo():
    return mock.MagicMock(spec=UserRepo)

@pytest.fixture
def mock_org_repo():
    return mock.MagicMock(spec=OrganizationRepo)

@pytest.fixture
def mock_repo_repo():
    return mock.MagicMock(spec=RepositoryRepo)

@pytest.fixture
def mock_user():
    return mock.MagicMock(User)

@pytest.fixture
def user_service(mock_session, mock_user_repo, mock_org_repo, mock_repo_repo):
    service = UserService(mock_session)
    service.user_repo = mock_user_repo
    service.org_repo = mock_org_repo
    service.repo_repo = mock_repo_repo
    return service

@pytest.fixture(scope="function", autouse=True)
def reset_db():
    from app.api.config.database import engine
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)

def test_change_password(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password1234", new_password="NewPassword1234")
    user_start = User(id=1, email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password(dto.old_password))
    user_end = User(id=1, email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password(dto.new_password))

    mock_user_repo.find_by_id.return_value = user_start
    mock_user_repo.change_password.return_value = user_end

    user_service.change_password(1, dto) # Should not raise exception.

def test_change_password_no_user(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password1234", new_password="NewPassword1234")
    mock_user_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundException) as e:
        user_service.change_password(1, dto)
    
    assert e.value.entity_type == User
    assert e.value.identifier == 1

def test_change_password_wrong_current_password(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password12345", new_password="NewPassword1234")
    user_start = User(id=1, email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password("Password1234"))
    mock_user_repo.find_by_id.return_value = user_start

    with pytest.raises(UserException) as e:
        user_service.change_password(1, dto)

def test_change_password_new_password_is_same_as_current_password(user_service, mock_user_repo):
    dto = UserPasswordChangeDTO(old_password="Password1234", new_password="Password1234")
    user_start = User(email="a@email.com", username="a", role=UserRole.user, hashed_password=hash_password(dto.old_password))
    mock_user_repo.find_by_id.return_value = user_start

    with pytest.raises(UserException) as e:
        user_service.change_password(1, dto)

def test_find_by_id_user_found(user_service, mock_user):
    """Test case for when a user is found by ID."""
    user_id = 1
    user_service.user_repo.find_by_id.return_value = mock_user

    result = user_service.find_by_id(user_id)

    assert result == mock_user
    user_service.user_repo.find_by_id.assert_called_once_with(user_id)

def test_find_by_id_user_not_found(user_service):
    """Test case for when a user is not found by ID."""
    user_id = 1
    user_service.user_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        user_service.find_by_id(user_id)

    user_service.user_repo.find_by_id.assert_called_once_with(user_id)

def test_find_by_username_user_found(user_service, mock_user):
    """Test case for when a user is found by username."""
    username = "bob"
    user_service.user_repo.find_by_username.return_value = mock_user

    result = user_service.find_by_username(username)

    assert result == mock_user
    user_service.user_repo.find_by_username.assert_called_once_with(username)

def test_find_by_username_user_not_found(user_service):
    """Test case for when a user is not found by username."""
    username = "bob"
    user_service.user_repo.find_by_username.return_value = None

    with pytest.raises(NotFoundException):
        user_service.find_by_username(username)

    user_service.user_repo.find_by_username.assert_called_once_with(username)

def test_add(user_service, mock_user_repo):
    dto = UserRegisterDTO(username="Username1", email="email1@email.com", password="Password1")
    mock_user_repo.find_by_email.return_value = None
    mock_user_repo.find_by_username.return_value = None

    test_result = user_service.add(dto)

    assert test_result.id is not None

def test_add_existing_user(user_service, mock_user_repo):
    dto = UserRegisterDTO(username="Username1", email="email1@email.com", password="Password1")
    user = User(username="Username1", email="email1@email.com", role=UserRole.user, hashed_password=hash_password(dto.password))
    
    def get_user_by_email_mocked(email: str):
        return user if user.email == email else None
    mock_user_repo.find_by_email.side_effect = get_user_by_email_mocked

    def get_user_by_username_mocked(username: str):
        return user if user.username == username else None
    mock_user_repo.find_by_username.side_effect = get_user_by_username_mocked

    # [1] Creating a user with a non-unique email
    with pytest.raises(FieldTakenException) as e:
        user_service.add(dto)
    assert e.value.message == "Email already taken"

    # [2] Creating a user with a non-unique username
    dto.email = "email2@email.com"
    with pytest.raises(FieldTakenException) as e:
        user_service.add(dto)
    assert e.value.message == "Username already taken"

def test_add_admin(user_service, mock_user_repo):
    dto = UserRegisterDTO(username="Username1", email="a@email.com", password="Password1")

    mock_user_repo.find_by_email.return_value = None
    mock_user_repo.find_by_username.return_value = None

    def mock_add(user: User):
        return user
    mock_user_repo.add.side_effect = mock_add

    def set_role(user: User, role: UserRole):
        user.sqlmodel_update({"role": role})
        return user
    mock_user_repo.set_role.side_effect = set_role

    result = user_service.add_admin(dto)
    
    assert result.role == UserRole.admin

def test_add_admin___integration():

    with TestClient(app) as client:
    
        def get_auth_header(data: dict | None) -> dict:
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == 200
            
            ok_request = response.json()
            jwt = ok_request["token"]
            header = {
                "Authorization": f"Bearer {jwt}"
            }

            return header
    
        config_file = "./volume-server-cfg/superadmin_password.txt"
        data = {
            "username" : "admin",
            "password" : ""
        }

        with open(config_file, "r") as f:
            data["password"] = old_password = f.readline()

        # [1] Adding an admin before changing the super admin password
        header = get_auth_header(data)

        data = {
            "username": "Username1",
            "email": "email1@email.com",
            "password": "Password1"
        }
        
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        bad_request = response.json()
        
        assert response.status_code == 403
        assert bad_request["detail"] == "Password change required"
        
        # [2] Changing the super admin password
        data = {
            "old_password": old_password,
            "new_password": "Password1" 
        }
        response = client.post("/api/v1/users/password", json=data, headers=header)
        assert response.status_code == 204

        data = {
            "username" : "admin",
            "password" : data["new_password"]
        }
        header = get_auth_header(data)

        # [3] Adding an admin
        data = {
            "username": "Username1",
            "email": "email1@email.com",
            "password": "Password1"
        }
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        assert response.status_code == 200

        created_admin = response.json()
        assert created_admin["username"] == data["username"]
        assert created_admin["role"] == "admin"

        # [4] Adding an admin with a non-unique username
        data["email"] = "email2@email.com"
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        assert response.status_code == 400

        # [5] Adding an admin with a non-unique email
        data["username"] = "Username2"
        data["email"] = "email1@email.com"
        response = client.post("/api/v1/users/register-admin", json=data, headers=header)
        assert response.status_code == 400
        
def test_add___integration():
    with TestClient(app) as client:
        def add_user(username: str | None, status_code: int | None) -> dict:
            data = {
                "username": username,
                "email": f"{username}@gmail.com",
                "password": "1234"
            }
            response = client.post("/api/v1/users/", json=data)
            assert response.status_code == status_code
            return response.json()

        def log_in(username: str | None, status_code: int | None) -> str:
            data = {
                "username": username,
                "password": "1234"
            }
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == status_code

        username = "Username1"
        
        user = add_user(username, 200)
        assert user["username"] == username

        log_in(username, 200)
        
        add_user(username, 400)

def make_user(user_id: int, username: str) -> User:
    return User(
        id=user_id,
        username=username,
        email=f"{username}@mail.com",
        role=UserRole.user,
        hashed_password="hash"
    )

def make_user_dto(id: int, username: str, email: str, first_name=None, last_name=None, bio=None) -> UserDTO:
    return UserDTO(
        id=id,
        username=username,
        email=email,
        role=UserRole.user,
        join_date=datetime.utcnow(),
        first_name=first_name,
        last_name=last_name,
        bio=bio,
        badge=None
    )

def test_search_by_username_prefix(user_service):
    """ Searching for users by username prefix and filtering those that are already members of specific organization. """
    org_id = 1
    query = "jo"
    user1 = make_user(1, "john")
    user2 = make_user(2, "josh")
    user3 = make_user(3, "jane")
    user_service.user_repo.search_by_username_prefix.return_value = [user1, user2]
    user_service.org_repo.find_members_of_org.return_value = [user2, user3]

    result = user_service.search_by_username_prefix(query, org_id)
    assert result == [user1]
    user_service.user_repo.search_by_username_prefix.assert_called_once_with(query)
    user_service.org_repo.find_members_of_org.assert_called_once_with(org_id)

def test_update_profile_user_not_found(user_service):
    """ Test case for when the user to update is not found. """
    dto = make_user_dto(id=99, username="john", email="john@mail.com")
    user_service.user_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        user_service.update_profile(user_id=1, dto=dto)

    user_service.user_repo.find_by_id.assert_called_once_with(dto.id)
    user_service.user_repo.add.assert_not_called()

def test_update_profile_access_denied(user_service):
    """ Test case for when a user tries to update another user's profile. """
    user = make_user(2, "josh")
    dto = make_user_dto(id=2, username="josh", email="josh@mail.com")
    user_service.user_repo.find_by_id.return_value = user

    with pytest.raises(AccessDeniedException):
        user_service.update_profile(user_id=1, dto=dto)

    user_service.user_repo.find_by_id.assert_called_once_with(dto.id)
    user_service.user_repo.add.assert_not_called()

def test_update_profile_email_taken(user_service):
    """ Test case for when a user tries to update data with an email that is already taken. """
    user = make_user(1, "john")
    dto = make_user_dto(id=1, username="john", email="taken@mail.com")

    user_service.user_repo.find_by_id.return_value = user
    user_service.user_repo.find_by_email.return_value = make_user(2, "josh")

    with pytest.raises(FieldTakenException):
        user_service.update_profile(user_id=1, dto=dto)

    user_service.user_repo.find_by_id.assert_called_once_with(dto.id)
    user_service.user_repo.find_by_email.assert_called_once_with(dto.email)
    user_service.user_repo.add.assert_not_called()

def test_update_profile_partial_update(user_service):
    """ Test case for updating only some fields of the user (the email is staying the same). """
    user = make_user(1, "john")
    dto = make_user_dto(id=1, username="john", email=user.email, bio="New bio")

    user_service.user_repo.find_by_id.return_value = user
    updated_user = user_service.update_profile(user_id=1, dto=dto)

    assert updated_user.bio == "New bio"
    assert updated_user.email == user.email
    user_service.user_repo.find_by_email.assert_not_called()
    user_service.user_repo.add.assert_called_once_with(updated_user)

def test_update_profile_all_attributes(user_service):
    """ Test case for updating all attributes of the user successfully. """
    user = make_user(1, "john")
    dto = make_user_dto(
        id=1,
        username="john",
        email="newEmail@mail.com",
        first_name="John",
        last_name="Doe",
        bio="New bio"
    )
    user_service.user_repo.find_by_id.return_value = user
    user_service.user_repo.find_by_email.return_value = None
    updated_user = user_service.update_profile(user_id=1, dto=dto)

    assert updated_user.email == "newEmail@mail.com"
    assert updated_user.first_name == "John"
    assert updated_user.last_name == "Doe"
    assert updated_user.bio == "New bio"
    user_service.user_repo.add.assert_called_once_with(updated_user)


def test_update_profile_integration():
    with TestClient(app) as client:
        def create_user(username: str, email: str, password: str = "Password123") -> dict:
            data = {"username": username, "email": email, "password": password}
            response = client.post("/api/v1/users", json=data)
            assert response.status_code == 200
            return response.json()

        def login(username: str, password: str = "Password123") -> dict:
            data = {"username": username, "password": password}
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == 200
            token = response.json()["token"]
            return {"Authorization": f"Bearer {token}"}

        username = "John"
        user = create_user(username, "john@mail.com")
        auth_header = login(username)

        user_dto = {
            "id": user["id"],
            "username": username,
            "first_name": "John",
            "last_name": "Doe",
            "bio": "bio bio",
            "role": "user",
            "join_date": datetime.now().isoformat(),
            "email": "newprofile@mail.com",
            "badge": user["badge"]
        }

        response = client.put("/api/v1/users", json=user_dto, headers=auth_header)
        assert response.status_code == 200
        assert response.json()["username"] == user_dto["username"]

        get_response = client.get(f"/api/v1/users/{username}", headers=auth_header)
        assert get_response.status_code == 200
        updated_user = get_response.json()
        assert updated_user["first_name"] == user_dto["first_name"]
        assert updated_user["last_name"] == user_dto["last_name"]
        assert updated_user["bio"] == user_dto["bio"]
        assert updated_user["email"] == user_dto["email"]

def test_update_badge_user_not_found(user_service):
    """ Test case for when the user's badge to update is not found. """
    user_id = 99
    user_service.user_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        user_service.update_badge(user_id, UserBadge.verified)

    user_service.user_repo.find_by_id.assert_called_once_with(user_id)
    user_service.user_repo.update_badge.assert_not_called()

def test_update_badge_no_repositories_success(user_service):
    user = make_user(1, "john")
    user.badge = UserBadge.none
    expected_user = make_user(1, "john")
    new_badge = UserBadge.verified
    expected_user.badge = new_badge

    user_service.user_repo.find_by_id.return_value = user
    user_service.repo_repo.get_repositories_for_user.return_value = []
    user_service.user_repo.update_badge.return_value = expected_user

    updated_user = user_service.update_badge(user.id, new_badge)
    assert updated_user.badge == expected_user.badge
    user_service.user_repo.find_by_id.assert_called_once_with(expected_user.id)
    user_service.repo_repo.get_repositories_for_user.assert_called_once()
    user_service.repo_repo.set_attribute.assert_not_called()
    user_service.user_repo.update_badge.assert_called_once()

def test_update_badge_and_repositories_success(user_service):
    user = make_user(1, "john")
    user.badge = UserBadge.none
    expected_user = make_user(1, "john")
    new_badge = UserBadge.verified
    expected_user.badge = new_badge
    repository1 = mock.MagicMock(Repository)
    repository2 = mock.MagicMock(Repository)

    user_service.user_repo.find_by_id.return_value = user
    user_service.repo_repo.get_repositories_for_user.return_value = [repository1, repository2]
    user_service.user_repo.update_badge.return_value = expected_user

    updated_user = user_service.update_badge(user.id, new_badge)
    assert updated_user.badge == expected_user.badge
    user_service.user_repo.find_by_id.assert_called_once_with(expected_user.id)
    user_service.repo_repo.get_repositories_for_user.assert_called_once()
    user_service.repo_repo.set_attribute.assert_has_calls([
        mock.call(repository1, "badge", new_badge),
        mock.call(repository2, "badge", new_badge)
    ])
    assert user_service.repo_repo.set_attribute.call_count == 2

    user_service.user_repo.update_badge.assert_called_once()

def test_search_paginated_success(user_service):
    query = "john"
    page_number = 1
    page_size = 2
    sort_by = "username"
    sort_ascending = True

    user1 = make_user(1, "john")
    user2 = make_user(2, "johnny")
    user_list = [user1, user2]
    total_hits = 5

    user_service.user_repo.search_users_paginated.return_value = (user_list, total_hits)
    result = user_service.search_paginated(query, page_number, page_size, sort_by, sort_ascending)

    assert isinstance(result, PaginatedResultDTO)
    assert result.info.page == page_number
    assert result.info.page_size == page_size
    assert result.info.total_hits == total_hits
    assert result.info.total_pages == 3  # ceil(5 / 2)
    assert len(result.hits) == 2
    assert all(isinstance(u, UserDTO) for u in result.hits)
    user_service.user_repo.search_users_paginated.assert_called_once_with(
        query, page_number, page_size, sort_by, sort_ascending)

def test_search_paginated_min_page_and_size(user_service):
    user = make_user(1, "john")
    user_service.user_repo.search_users_paginated.return_value = ([user], 1)

    result = user_service.search_paginated("j", 0, 0, "email", False)

    assert result.info.page == 1
    assert result.info.page_size == 1
    assert result.info.total_pages == 1
    assert result.info.total_hits == 1
    assert len(result.hits) == 1
    user_service.user_repo.search_users_paginated.assert_called_once_with(
        "j", 1, 1, "email", False)

def test_update_user_badge_and_search_paginated_integration():
    with TestClient(app) as client:
        def login(data: dict) -> dict:
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == 200
            jwt = response.json()["token"]
            return {"Authorization": f"Bearer {jwt}"}

        # Login as superadmin using password from file
        superadmin_creds = {
            "username": "admin",
            "password": ""
        }
        with open("./volume-server-cfg/superadmin_password.txt", "r") as f:
            superadmin_creds["password"] = old_password = f.readline()

        superadmin_header = login(superadmin_creds)

        # Change superadmin password
        change_pw_payload = {
            "old_password": old_password,
            "new_password": "Password1"
        }
        response = client.post("/api/v1/users/password", json=change_pw_payload, headers=superadmin_header)
        assert response.status_code == 204

        superadmin_creds["password"] = "Password1"
        superadmin_header = login(superadmin_creds)

        # Register an admin
        new_admin_data = {
            "username": "TestAdmin",
            "email": "admin@example.com",
            "password": "AdminPass123"
        }
        response = client.post("/api/v1/users/register-admin", json=new_admin_data, headers=superadmin_header)
        assert response.status_code == 200
        admin = response.json()
        admin_auth = login({"username": new_admin_data["username"], "password": new_admin_data["password"]})

        # Register a regular user (to later update badge)
        user_data = {
            "username": "TestUser",
            "email": "testuser@example.com",
            "password": "UserPass123"
        }
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 200
        user = response.json()
        user_id = user["id"]

        # Update badge
        badge_update_dto = {
            "user_id": user_id,
            "badge": "verified"
        }
        response = client.put("/api/v1/users/badge", json=badge_update_dto, headers=admin_auth)
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["badge"] == "verified"

        # Search paginated and verify badge is included
        params = {
            "query": "Test",
            "page_number": 1,
            "page_size": 10,
            "sort_by": "username",
            "sort_ascending": True
        }
        response = client.get("/api/v1/users/paginated/", headers=admin_auth, params=params)
        assert response.status_code == 200
        paginated = response.json()
        assert any(u["id"] == user_id and u["badge"] == "verified" for u in paginated["hits"])

