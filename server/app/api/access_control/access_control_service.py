from fastapi import Depends
from sqlmodel import Session
from app.api.user.user_repo import UserRepo
from app.api.repo.repo_repo import RepositoryRepo
from app.api.org.org_repo import OrganizationRepo
from app.api.team.team_repo import TeamRepo
from typing import List

from app.api.team.team_model import Team, TeamMember, TeamPermission, TeamPermissionKind
from app.api.team.team_dto import TeamAddMemberDTO, TeamAddPermissionDTO, TeamCreateDTO
from app.api.user.user_model import User
from app.api.config.exception_handler import AccessDeniedException, FieldTakenException, NotFoundException, NotInRelationshipException, UserException
from app.api.org.org_model import Organization
from app.api.config.database import get_database
from app.api.repo.repo_model import Repository


# NOTE: This is the only service that other services _should_ inject directly.
# Be careful with circular imports though!
class AccessControlService:
    def __init__(self, session: Session):
        self.session = session
        self.repo_repo = RepositoryRepo(session)
        self.user_repo = UserRepo(session)
        self.org_repo = OrganizationRepo(session)
        self.team_repo = TeamRepo(session)

    def has_read_access(self, user_id: int | None, repo_id: int) -> bool:    
        # Case 1: Repo doesn't exist.

        repo = self.repo_repo.find_by_id(repo_id)
        if repo is None:
            return False
        
        # Case 2: Public repository is readable by everyone.

        if repo.public:
            return True
        
        # Case 3: Guests can only view public repositories.

        if user_id is None:
            return False
        
        # Case 4: User isn't a guest but the user doesn't exist.

        if self.user_repo.find_by_id(user_id) is None:
            return False
 
        # Case 5: Creator of the repository can always read it.
        
        if user_id == repo.owner_id:
            return True
        
        # Case 6: The repository is private, not in an org, and user isn't the owner.

        org = repo.organization
        if org is None:
            return False

        # Case 7: Repo is in org and org has no team permissions for that repo.

        team_permissions = self.team_repo.find_permissions_by_repo_and_org(repo.id, org.id)
        if not team_permissions:
            return self.org_repo.user_is_in_org(user_id, org.id)

        # Case 8: Repo is in org and org has team permissions for that repo.

        for team_permission in team_permissions:
            if self.team_repo.find_member(team_permission.team_id, user_id) is not None:
                return True

        return False
    
    def has_write_access(self, user_id: int | None, repo_id: int) -> bool:
        # Case 1: Repo doesn't exist.

        repo = self.repo_repo.find_by_id(repo_id)
        if repo is None:
            return False

        # Case 2: User is not provided.
        # user_id MUST NOT be None, but we'll leave `int | None` for consistency.

        if user_id is None:
            return False

        # Case 3: User doesn't exist.
        
        if self.user_repo.find_by_id(user_id) is None:
            return False

        # Case 4: Owner of the repo always has write access.

        if user_id == repo.owner_id:
            return True

        # Case 5: Repo is not in an org, fallback to 'denied access'.

        org = repo.organization
        if org is None:
            return False
        
        # Case 6: Repo is in org but has no teams, fallback again.

        team_permissions = self.team_repo.find_permissions_by_repo_and_org(repo.id, org.id)
        if not team_permissions:
            return False

        # Case 7: Repo is in org and org has team permissions for that repo.

        for team_permission in team_permissions:
            if team_permission.kind in [TeamPermissionKind.read_write, TeamPermissionKind.admin]:
                if self.team_repo.find_member(team_permission.team_id, user_id) is not None:
                    return True

        return False
    

def get_access_control_service(session: Session = Depends(get_database)) -> AccessControlService:
    return AccessControlService(session)