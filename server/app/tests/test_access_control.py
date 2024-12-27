import pytest
from unittest.mock import MagicMock

from app.api.access_control.access_control_service import AccessControlService
from app.api.org.org_repo import OrganizationRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.team.team_repo import TeamRepo
from app.api.user.user_repo import UserRepo

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
                repo = MagicMock()
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_no_org_user_is_not_owner(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_public_repo_no_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is True

        class TestOrgNoTeamPermission:
            def test_public_repo_org_no_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_no_team_permission_user_is_member_of_org(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = True
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_no_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_no_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is True

        class TestOrgWithTeamPermission:
            def test_public_repo_org_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_in_team(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_not_in_team(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=3, repo_id=123)
                assert result is True

            def test_public_repo_org_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = True
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is True

    class TestPrivateRepo:
        class TestNoOrg:
            def test_private_repo_no_org_user_is_owner(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_no_org_user_is_not_owner(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is False

            def test_private_repo_no_org_user_is_guest(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                repo.owner_id = 1
                repo.organization = None
                service.repo_repo.find_by_id.return_value = repo
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgNoTeamPermission:
            def test_private_repo_org_no_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_org_no_team_permission_user_is_member_of_org(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = True
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_org_no_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is False

            def test_private_repo_org_no_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = []
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is False

        class TestOrgWithTeamPermission:
            def test_private_repo_org_team_permission_user_is_owner(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                repo.owner_id = 1
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=1, repo_id=123)
                assert result is True

            def test_private_repo_org_team_permission_user_is_in_team(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = MagicMock()
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is True

            def test_private_repo_org_team_permission_user_is_not_in_team(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=2, repo_id=123)
                assert result is False

            def test_private_repo_org_team_permission_user_is_outsider_of_org(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                service.org_repo.user_is_in_org.return_value = False
                result = service.has_read_access(user_id=3, repo_id=123)
                assert result is False

            def test_private_repo_org_team_permission_user_is_guest(self, service: AccessControlService):
                repo = MagicMock()
                repo.public = False
                org = MagicMock()
                org.id = 1
                repo.organization = org
                team_permission = MagicMock()
                team_permission.team_id = 1
                service.repo_repo.find_by_id.return_value = repo
                service.team_repo.find_permissions_by_repo_and_org.return_value = [team_permission]
                service.team_repo.find_member.return_value = None
                result = service.has_read_access(user_id=None, repo_id=123)
                assert result is False