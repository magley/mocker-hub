from typing import List
from fastapi import Depends, HTTPException
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.access_control.access_control_service import AccessControlService
from app.api.registry.registry_utils import build_manifest_jwt, parse_scopes, build_jwt_for_docker_registry
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.registry.registry_dto import DeleteTagResponseDTO, RegistryActionOperation
from app.api.tags.tag_service import TagService
from app.api.repo.repo_model import Repository
from app.api.tags.tag_model import Tag
from app.api.registry.registry_client import RegistryClient

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

    def _format_registry_event(self, username: str, action: str, repo_name: str, tag_name: str | None, digest: str, method: str, url: str | None):

        is_layer_action = url is not None and "blobs" in url
        is_tag_action = tag_name is not None 
        is_referrers_action = url is not None and "referrers" in url

        # The condition `(url is None)` is a bit hardcoded — it represents
        # a special case when an image manifest link is being deleted.
        # This operation always follows the deletion of tag links.
        # TODO: Consider revising this logic in the future when implementing repository deletion
        is_manifest_action = (url is not None and "manifests" in url) or (url is None)

        if is_layer_action:
            target = "layer"
            desc = digest
                
        elif is_tag_action:
            target = "tag"
            desc = tag_name

        elif is_manifest_action: 
            target = "manifest"
            desc = digest

        elif is_referrers_action: 
            target = "referrers"
            desc = digest

        else: 
            raise ValueError(f"Unsupported event: action='{action}', repo='{repo_name}', tag='{tag_name}', method='{method}', url='{url}'")
    
        return f"User '{username}' completed a {action} using method {method} on repo '{repo_name}' ({target}) [{desc}]"

    def on_notification(self, username: str, action: str, repo_name: str, tag_name: str | None, digest: str, method: str, url: str | None):

        if action == 'push' and tag_name is not None:
            user = self.user_service.find_by_username(username)
            repo = self.repo_service.find_by_canonical_name(repo_name)
            tag = self.tag_service.on_push(user.id, repo.id, tag_name)
            print(f"Pushed tag {tag}")

        elif action == 'delete' and tag_name is not None:
            repo = self.repo_service.find_by_canonical_name(repo_name)
            tag = self.tag_service.find_by_name_and_repo_id(tag_name, repo.id)
            self.tag_service.remove_tag(tag.id)
            print(f"Deleted tag {tag_name}")

        message = self._format_registry_event(username, action, repo_name, tag_name, digest, method, url)
        print(message)

    def handle_registry_request(self, username: str, password: str, scopes: List[str] | None, service: str | None):
        # User with the provided credentials must exist.

        if not self.user_service.exists_with_credentials(username, password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Scopes are defined, therefore these are push/pull requests. If scopes
        # aren't defined, this is a login request, so we can skip to creating the
        # JWT.

        if scopes is not None:
            actions = parse_scopes(username, scopes)
            user = self.user_service.find_by_username(username)

            for action in actions:
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
                        raise HTTPException(status_code=400, detail=f"Unknown operation {operation}")
                
        # Create the JWT.
        jwt = build_jwt_for_docker_registry(username, service, scopes)
        return {"token": jwt}
    
   
    async def _fetch_manifest_digest(self, client: RegistryClient, repo_name: str, tag_name: str, username: str) -> str | None:

        jwt = build_manifest_jwt(username, repo_name, "GET")
        response = await client.get_manifest(repo_name, tag_name, jwt)

        if response.status_code == 404:
            return None
        
        assert response.status_code == 200
        return response.headers["Docker-Content-Digest"]
        
    async def _delete_manifest_by_digest(self, client: RegistryClient, repo_name: str, digest: str, username: str) -> None:
        jwt = build_manifest_jwt(username, repo_name, "DELETE")
        response = await client.delete_manifest(repo_name, digest, jwt)
        assert response.status_code == 202

    async def delete_tag(self, client: RegistryClient, username: str, repo: Repository, tag: Tag) -> DeleteTagResponseDTO:
        # If the manifest for a certain tag can't be found,
        # it means the manifest has already been deleted.
        # Two tags can point to the same manifest.
        # If a manifest pointed to by two tags is deleted,
        # both tags are also removed from the Distribution.
        digest = await self._fetch_manifest_digest(client, repo.canonical_name, tag.name, username)   
        if digest is None:
            self.tag_service.remove_tag(tag.id)
            return DeleteTagResponseDTO(message=f"Tag '{tag.name}' successfully deleted from repository '{repo.name}'.")

        # Since deletion of the manifest is accepted (202) 
        # by Distribution, it is a slightly better approach 
        # to delete it from the backend database afterward.
        await self._delete_manifest_by_digest(client, repo.canonical_name, digest, username)
        return DeleteTagResponseDTO(message=f"Tag '{tag.name}' successfully deleted from repository '{repo.name}'.")
   
def get_registry_service(session: Session = Depends(get_database)) -> RegistryService:
    return RegistryService(session)