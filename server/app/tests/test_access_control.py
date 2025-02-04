import pytest
from unittest.mock import MagicMock

from app.api.access_control.access_control_service import AccessControlService
from app.api.org.org_repo import OrganizationRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.team.team_repo import TeamRepo
from app.api.user.user_repo import UserRepo
from app.api.team.team_model import TeamPermission, TeamPermissionKind
from app.api.repo.repo_model import Repository
from app.api.org.org_model import Organization
from app.api.user.user_model import User, UserRole

@pytest.fixture
def service() -> AccessControlService:
    session = MagicMock()
    repo_repo = MagicMock(RepositoryRepo)
    user_repo = MagicMock(UserRepo)
    org_repo = MagicMock(OrganizationRepo)
    team_repo = MagicMock(TeamRepo)

    ac_service = AccessControlService(session)
    ac_service.repo_repo = repo_repo
    ac_service.user_repo = user_repo
    ac_service.org_repo = org_repo
    ac_service.team_repo = team_repo

    return ac_service

class TestHasReadAccess:
    '''
    TestHasReadAccess tests for has_read_access
    It's split into two groups:
     - when the repo is public
     - when the repo is private

    These are the test cases:
    ```[
        public repo, no org, user is owner
        public repo, no org, user isn't owner
        public repo, no org, user is guest

        public repo, org, no team permission, user is owner,
        public repo, org, no team permission, user is member of org,
        public repo, org, no team permission, user is outsider of org,
        public repo, org, no team permission, user is guest,

        public repo, org, team permission, user is owner,
        public repo, org, team permission, user is in that team
        public repo, org, team permission, user is not in that team
        public repo, org, team permission, user is outsider of org
        public repo, org, team permission, user is guest
    ]```
    
    And then the same with private repo.
    '''

    class TestPublicRepo:
        class TestNoOrg:
            def test_public_repo_no_org_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_no_org_user_is_not_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_public_repo_no_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is True

        class TestOrgNoTeamPermission:
            def test_public_repo_org_no_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_no_team_permission_user_is_member_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = True
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_no_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_no_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is True

        class TestOrgWithTeamPermission:
            def test_public_repo_org_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_not_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=3, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is True

    class TestPrivateRepo:
        class TestNoOrg:
            def test_private_repo_no_org_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_no_org_user_is_not_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is False

            def test_private_repo_no_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgNoTeamPermission:
            def test_private_repo_org_no_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_org_no_team_permission_user_is_member_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = True
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_org_no_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is False

            def test_private_repo_org_no_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgWithTeamPermission:
            def test_private_repo_org_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_org_team_permission_user_is_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_private_repo_org_team_permission_user_is_not_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is False

            def test_private_repo_org_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=3, repo_id=123)
                assert result is False

            def test_private_repo_org_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is False


class TestHasWriteAccess:
    '''
    TestHasWriteAccess tests for has_write_access
    It's split into two groups:
     - when the repo is public
     - when the repo is private

    Additionally, write access implies read access, so whenever write access is true,
    we also assert that read access is true. 

    These are the test cases:
    ```[ 
        public repo, no org, user is owner
        public repo, no org, user isn't owner
        public repo, no org, user is guest

        public repo, org, no team permission, user is owner,
        public repo, org, no team permission, user is member of org,
        public repo, org, no team permission, user is outsider of org,
        public repo, org, no team permission, user is guest,

        public repo, org, team permission (read_write/admin), user is owner,
        public repo, org, team permission (read_write/admin), user is in that team
        public repo, org, team permission (read_write/admin), user is not in that team
        public repo, org, team permission (read_write/admin), user is outsider of org
        public repo, org, team permission (read_write/admin), user is guest
    ]```
    
    And then the same with private repo.
    '''
    
    class TestPublicRepo:
        class TestNoOrg:
            def test_public_repo_no_org_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_public_repo_no_org_user_is_not_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_write_access(user_id=2, repo_id=123)
                assert result is False

            def test_public_repo_no_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_write_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgNoTeamPermission:
            def test_public_repo_org_no_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_public_repo_org_no_team_permission_user_is_member_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = True
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is False

            def test_public_repo_org_no_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is False

            def test_public_repo_org_no_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_write_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgWithTeamPermission:
            def test_public_repo_org_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_public_repo_org_team_permission_user_is_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.kind = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_write_access(user_id=2, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=2, repo_id=123)


            def test_public_repo_org_team_permission_user_is_not_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_write_access(user_id=2, repo_id=123)
                assert result is False

            def test_public_repo_org_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_write_access(user_id=3, repo_id=123)
                assert result is False

            def test_public_repo_org_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_write_access(user_id=None, repo_id=123)
                assert result is False

    class TestPrivateRepo:
        class TestNoOrg:
            def test_private_repo_no_org_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_private_repo_no_org_user_is_not_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_write_access(user_id=2, repo_id=123)
                assert result is False

            def test_private_repo_no_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_write_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgNoTeamPermission:
            def test_private_repo_org_no_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_private_repo_org_no_team_permission_user_is_member_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = True
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is False

            def test_private_repo_org_no_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is False

            def test_private_repo_org_no_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_write_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgWithTeamPermission:
            def test_private_repo_org_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_write_access(user_id=1, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_private_repo_org_team_permission_user_is_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.kind = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_write_access(user_id=2, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=2, repo_id=123)

            def test_private_repo_org_team_permission_user_is_not_in_team(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_write_access(user_id=2, repo_id=123)
                assert result is False

            def test_private_repo_org_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_write_access(user_id=3, repo_id=123)
                assert result is False

            def test_private_repo_org_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = False
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                team_permission = MagicMock(spec=TeamPermission)
                team_permission.team_id = 1
                team_permission.permission = TeamPermissionKind.read_write
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_write_access(user_id=None, repo_id=123)
                assert result is False


class TestHasStarAccess:
    '''
    TestHasStarAccess tests for has_star_access
    It's split into three groups:
     - basic tests
     - when the repo is public tests
     - when the repo is private tests

    Additionally, star access implies read access, so whenever star access is true,
    we also assert that read access is true. 

    NOTE: The user is a regular user unless otherwise noted.

    These are the test cases:
    ```[ 

        Basic tests

        Since each test when the repo is invalid or the user doesn't 
        exist will fail, there's no point in testing all of them. 
        Therefore, we selected the tests with the highest likelihood of success.

        repo is invalid, user is valid
        public repo, no org, user doesn't exist
        

        Public repo tests

        public repo, no org, user is guest
        public repo, no org, user is owner
        public repo, no org, user isn't owner  
        public repo, no org, user isn't owner & is admin 
        public repo, no org, user isn't owner & is super admin 

        public repo, org, user is guest
        public repo, org, user is owner
        public repo, org, user is member of org
        public repo, org, user isn't member of org
        public repo, org, user isn't member of org & is admin
        public repo, org, user isn't member of org & is super admin

        
        Private repo tests

        Since each test for the private repository will fail, there's no point 
        in testing all of them. Therefore, we selected the tests with the highest
        likelihood of success.

        private repo, no org, user isn't owner
        private repo, org, user isn't member of org
        
    ]```
    
    '''
    
    class TestBasicFuns:
        def test_repo_is_invalid_user_is_valid(self, service: AccessControlService):
            user = MagicMock(spec=User)
            user.id = 1
            user.role = UserRole.user
            service.repo_repo.find_by_id.return_value = None
            service.user_repo.find_by_id.return_value = user
            result = service.has_star_access(user_id=1, repo_id=99999999)
            assert result is False
            assert service.has_read_access(user_id=1, repo_id=99999999) is False

        def test_public_repo_no_org_user_doesnt_exist(self, service: AccessControlService):
            repo = MagicMock(spec=Repository)
            repo.public = True
            repo.owner_id = 1
            repo.organization = None
            service.repo_repo.find_by_id.return_value = repo
            service.user_repo.find_by_id.return_value = None
            result = service.has_star_access(user_id=99999999, repo_id=1)
            assert result is False
            assert service.has_read_access(user_id=1, repo_id=99999999)

    class TestPublicRepo:
        class TestNoOrg:
            def test_public_repo_no_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_star_access(user_id=None, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=None, repo_id=123)

            def test_public_repo_no_org_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                user = MagicMock(spec=User)
                user.id = 1
                user.role = UserRole.user
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_star_access(user_id=1, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=1, repo_id=123)
        
            def test_public_repo_no_org_user_is_not_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                user = MagicMock(spec=User)
                user.id = 2
                user.role = UserRole.user
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_star_access(user_id=2, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=2, repo_id=123)

            def test_public_repo_no_org_user_is_not_owner_and_is_admin(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                user = MagicMock(spec=User)
                user.id = 2
                user.role = UserRole.admin
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_star_access(user_id=2, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=2, repo_id=123)

            def test_public_repo_no_org_user_is_not_owner_and_is_super_admin(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                user = MagicMock(spec=User)
                user.id = 2
                user.role = UserRole.superadmin
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_star_access(user_id=2, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=2, repo_id=123)

        class TestOrg:
            def test_public_repo_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_star_access(user_id=None, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=None, repo_id=123)

            def test_public_repo_org_user_is_owner(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                user = MagicMock(spec=User)
                user.id = 1
                user.role = UserRole.user
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_star_access(user_id=1, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=1, repo_id=123)
        
            def test_public_repo_org_user_is_member_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo                
                user = MagicMock(spec=User)
                user.id = 1
                user.role = UserRole.user
                service.user_repo.find_by_id.return_value = user
                service.org_repo.user_is_in_org.return_value = True
                result = service.has_star_access(user_id=1, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=1, repo_id=123)
        
            def test_public_repo_org_user_is_not_member_of_org(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                user = MagicMock(spec=User)
                user.id = 1
                user.role = UserRole.user
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_star_access(user_id=1, repo_id=123)
                assert result is True
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_public_repo_org_user_is_not_member_of_org_and_is_admin(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                user = MagicMock(spec=User)
                user.id = 1
                user.role = UserRole.admin
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_star_access(user_id=1, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=1, repo_id=123)

            def test_public_repo_org_user_is_not_member_of_org_and_is_super_admin(self, service: AccessControlService):
                repo = MagicMock(spec=Repository)
                repo.public = True
                org = MagicMock(spec=Organization)
                org.id = 1
                repo.organization = org
                user = MagicMock(spec=User)
                user.id = 1
                user.role = UserRole.superadmin
                service.user_repo.find_by_id.return_value = user
                service.repo_repo.find_by_id.return_value = repo
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_star_access(user_id=1, repo_id=123)
                assert result is False
                assert service.has_read_access(user_id=1, repo_id=123)

    class TestPrivateRepo:
        def test_private_repo_no_org_user_is_not_owner(self, service: AccessControlService):
            repo = MagicMock(spec=Repository)
            repo.public = False
            repo.owner_id = 1
            repo.organization = None
            user = MagicMock(spec=User)
            user.id = 2
            user.role = UserRole.user
            service.user_repo.find_by_id.return_value = user
            service.repo_repo.find_by_id.return_value = repo
            result = service.has_star_access(user_id=2, repo_id=123)
            assert result is False
            assert service.has_read_access(user_id=2, repo_id=123) is False
        
        def test_private_repo_org_user_is_not_member_of_org(self, service: AccessControlService):
            repo = MagicMock(spec=Repository)
            repo.public = False
            org = MagicMock(spec=Organization)
            org.id = 1
            repo.organization = org
            user = MagicMock(spec=User)
            user.id = 1
            user.role = UserRole.user
            service.user_repo.find_by_id.return_value = user
            service.repo_repo.find_by_id.return_value = repo
            service.org_repo.user_is_in_org.return_value = False
            result = service.has_star_access(user_id=1, repo_id=123)
            assert result is False
            assert service.has_read_access(user_id=1, repo_id=123) is False

# ...
#
#