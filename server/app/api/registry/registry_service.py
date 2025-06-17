from fastapi import Depends, HTTPException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.access_control.access_control_service import AccessControlService
from app.api.registry.registry_utils import parse_scope, build_jwt_for_docker_registry
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.registry.registry_dto import RegistryActionOperation
from app.api.tags.tag_service import TagService

class RegistryService:
    def __init__(self, session: Session):
        self.session = session

        #  / \   / \                 / \   / \
        # / ! \ / ! \    N O T E    / ! \ / ! \
        # -------------------------------------
        #
        # Since we _KNOW_ that Registry service
        # only talks to distribution and SHOULD
        # NEVER be used by any other service, I
        # can safely inject UserService in here
        # and not worry about circular imports.
        #
        # --------------------------------------

        self.user_service = UserService(session)
        self.repo_service = RepositoryService(session)
        self.tag_service = TagService(session)
        self.access_control_service = AccessControlService(session)

    def on_notification(self, username: str, action: str, repo_name: str, tag: str | None):
        if action == 'push':
            user = self.user_service.find_by_username(username)
            repo = self.repo_service.find_by_canonical_name(repo_name)

            tag = self.tag_service.on_push(user.id, repo.id, tag)
            print(f"Pushed tag {tag}")

        print(f"User '{username}' completed '{action}' of repository '{repo_name}' with tag '{tag}'")


    def handle_registry_request(self, username: str, password: str, scope: str | None, service: str | None):
        # User with the provided credentials must exist.

        if not self.user_service.exists_with_credentials(username, password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Scope is defined, therefore this is a push/pull request. If the scope
        # isn't defined, this is a login request, so we can skip to creating the
        # JWT.

        if scope is not None:
            action = parse_scope(username, scope)
            user = self.user_service.find_by_username(username)
            repo = self.repo_service.find_by_canonical_name(action.repo_canonical_name)

            for operation in action.operations:

                # Case 1 - User requested push operation on the repo.

                if operation == RegistryActionOperation.push:
                    # This will cover all the neccessary cases:
                    #  - repo doesn't exist
                    #  - user doesn't exist
                    #  - user doesn't have access
                    #  - etc.

                    can_write = self.access_control_service.has_write_access(user.id, repo.id)
                    if not can_write:
                        raise HTTPException(status_code=401, detail=f"User {user.username} cannot push to repo {repo.canonical_name}")      
                    
                # Case 2 - User requested pull operation on the repo.

                elif operation == RegistryActionOperation.pull:
                    can_read = self.access_control_service.has_read_access(user.id, repo.id)
                    if not can_read:
                        raise HTTPException(status_code=401, detail=f"User {user.username} cannot pull from repo {repo.canonical_name}")
                    
                # Case 3 - Unknown operation.

                else:
                    raise HTTPException(status_code=400, detail=f"Unknown operations {action.operations}")
            
        # Create the JWT.
            
        jwt = build_jwt_for_docker_registry(username, service, scope)
        return {"token": jwt}
    
def get_registry_service(session: Session = Depends(get_database)) -> RegistryService:
    return RegistryService(session)