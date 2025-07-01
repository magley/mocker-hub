from typing import List

from rq import Retry
from fastapi import Depends, HTTPException
from app.api.config.exception_handler import AccessDeniedException
from app.api.jobs.jobs_client import JobsClient
from app.api.events.event_service import EventService
from app.api.jobs.jobs_service import JobsService
from app.api.events.event_model import EventLevel
from sqlmodel import Session
from app.api.config.database import get_database
from app.api.access_control.access_control_service import AccessControlService
from app.api.registry.registry_utils import build_manifest_jwt, parse_scopes, build_jwt_for_docker_registry
from app.api.user.user_service import UserService
from app.api.repo.repo_service import RepositoryService
from app.api.registry.registry_dto import DeleteResponseDTO, RegistryActionOperation
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
        self.event_service = EventService()
        self.jobs_service = JobsService()

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
            self.tag_service.on_push(user.id, repo.id, tag_name)
            self.event_service.log(EventLevel.Info, f"Tag '{tag_name}' of repository '{repo.canonical_name}' is pushed.")

        elif action == 'delete' and tag_name is not None:
            repo = self.repo_service.find_by_canonical_name(repo_name)
            tag = self.tag_service.find_by_name_and_repo_id(tag_name, repo.id)
            self.tag_service.remove_tag(tag.id)
            self.event_service.log(EventLevel.Info, f"Tag '{tag_name}' of repository '{repo.canonical_name}' is deleted.")

            if repo.deleting and len(repo.tags) == 0:
                name = repo.canonical_name
                self.repo_service.remove_repo(repo)
                self.event_service.log(EventLevel.Info, f"Repository '{name}' is deleted.")

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

    async def delete_tag(self, client: RegistryClient, username: str, repo: Repository, tag: Tag) -> DeleteResponseDTO:
        # If the manifest for a certain tag can't be found,
        # it means the manifest has already been deleted.
        # Two tags can point to the same manifest.
        # If a manifest pointed to by two tags is deleted,
        # both tags are also removed from the Distribution.
        digest = await self._fetch_manifest_digest(client, repo.canonical_name, tag.name, username)   
        if digest is None:
            self.tag_service.remove_tag(tag.id)
            return DeleteResponseDTO(message=f"Tag '{tag.name}' successfully deleted from repository '{repo.canonical_name}'.")

        # Since deletion of the manifest is accepted (202) 
        # by Distribution, it is a slightly better approach 
        # to delete it from the backend database afterward.
        await self._delete_manifest_by_digest(client, repo.canonical_name, digest, username)
        return DeleteResponseDTO(message=f"Tag '{tag.name}' successfully deleted from repository '{repo.canonical_name}'.")
   
    def delete_repo(self, client: JobsClient, username: str, user_id: int, repo_id: int) -> DeleteResponseDTO:
        repo = self.repo_service.find_by_id(repo_id)

        if not self.access_control_service.has_delete_access(user_id, repo_id):
            raise AccessDeniedException(f"User {username} cannot delete a repository with identifier {repo_id}.")

        if len(repo.tags) == 0:
            name = repo.canonical_name
            self.repo_service.remove_repo(repo)
            self.event_service.log(EventLevel.Info, f"Repository '{name}' is deleted.")
        else:
            self.repo_service.update_repo_attrs(repo.id, deleting=True)
            for tag in repo.tags:
                queue = client.get("delete_tag")
                queue.enqueue(
                    self.jobs_service.delete_tag_job, 
                    args=(username, repo.id, tag.name),
                    retry=Retry(max=6, interval=[60, 60, 60, 120, 4*3600])
                )

        return DeleteResponseDTO(message=f"Request to delete repository '{repo.canonical_name}' has been accepted and will be processed shortly.")

def get_registry_service(session: Session = Depends(get_database)) -> RegistryService:
    return RegistryService(session)