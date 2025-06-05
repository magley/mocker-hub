from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.registry.registry_utils import build_get_manifest_jwt, decode_auth_header, build_delete_manifest_jwt
from app.api.registry.registry_service import RegistryService, get_registry_service
from app.api.config.logutil import LOGGER
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTDep, get_id_from_jwt, get_username_from_jwt, pre_authorize
from app.api.tags.tag_service import TagService, get_tag_service
from app.api.registry.registry_dto import DeleteRepoTagDTO
from app.api.repo.repo_service import RepositoryService, get_repo_service
from app.api.access_control.access_control_service import AccessControlService, get_access_control_service
from app.api.config.exception_handler import AccessDeniedException

router = APIRouter(prefix="/registry", tags=["dockerhub-registry"])

@router.get("", summary="???")
def registry_endpoint(
    request: Request, 
    registry_service: RegistryService = Depends(get_registry_service),
    scope: str | None = None,
    service: str | None = None):

    authorization_header = request.headers.get("Authorization")
    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    if not authorization_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme (must be Basic)")
    
    auth_token = authorization_header.split(" ")[1]
    username, password = decode_auth_header(auth_token)

    return registry_service.handle_registry_request(username, password, scope, service)

@router.api_route("/notifications", methods=["POST", "PUT"], summary="Webhook for Docker Registry")
def registry_notification_endpoint(data: dict, registry_service: RegistryService = Depends(get_registry_service)):
    for event in data["events"]:
        action = event.get("action", None)
        username = event.get("actor", {}).get("name", None)
        repository = event.get("target", {}).get("repository", None)
        tag = event.get("target", {}).get("tag", None)
        
        try:
            registry_service.on_notification(username, action, repository, tag)
        except Exception as e:
            LOGGER.error(f"Couldn't handle Distribution webhook: {e}")

    return {}

def _create_manifest_path(repo_name: str, digest: str | None = None, tag_name: str | None = None) -> str:
    ref = tag_name if digest is None else digest
    return f"https://distribution:5000/v2/{repo_name}/manifests/{ref}"

async def get_manifest(request: Request, repo_name: str, tag_name: str, token: str):
    url = _create_manifest_path(repo_name, tag_name)
    headers = {
        "Authorization": f"Bearer {token}", 
        "Accept": "application/vnd.docker.distribution.manifest.v2+json, "
                  "application/vnd.oci.image.index.v1+json, "
                  "application/vnd.oci.image.manifest.v1+json"
    }
    client = request.app.client
    return await client.get(url, headers=headers)

async def delete_manifest(request: Request, repo_name: str, digest: str, token: str):
    url = _create_manifest_path(repo_name, digest)
    headers = { "Authorization": f"Bearer {token}" }
    client = request.app.client
    return await client.delete(url, headers=headers)

@router.delete("/tag", status_code=200, summary="Delete a tag by its name")
@pre_authorize([UserRole.user, UserRole.admin])                             
async def delete_tag_endpoint(
    jwt: JWTDep,
    dto: DeleteRepoTagDTO,
    request: Request,
    repo_service: RepositoryService = Depends(get_repo_service), 
    tag_service: TagService = Depends(get_tag_service),
    access_control_service: AccessControlService = Depends(get_access_control_service)
):
    repo = repo_service.find_by_id(dto.repo_id)
    tag = tag_service.find_by_name_and_repo_id(dto.tag_name, dto.repo_id)
    username = get_username_from_jwt(jwt)
    user_id = get_id_from_jwt(jwt)

    if not access_control_service.has_delete_tag_access(user_id, repo.id):
        raise AccessDeniedException(f"User {user_id} cannot delete a tag {tag.name} of repository with identifier {repo.id}")

    token = build_get_manifest_jwt(username, repo.name)

    response = await get_manifest(request, repo.name, tag.name, token)
    if response.status_code == 404: 
        # If the manifest for a certain tag can't be found,
        # it means the manifest has already been deleted.
        # Two tags can point to the same manifest.
        # If a manifest pointed to by two tags is deleted,
        # both tags are also removed from the distribution.
        tag_service.remove_tag(tag.id)
        return {"message": f"Tag '{tag.name}' successfully deleted from repository '{repo.name}'."}
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json()) 

    token = build_delete_manifest_jwt(username, repo.name)
    manifest_digest = response.headers['Docker-Content-Digest']
    response = await delete_manifest(request, repo.name, manifest_digest, token)
    if response.status_code != 202:
        raise HTTPException(status_code=response.status_code, detail=response.json())   

    tag_service.remove_tag(tag.id) 
    return {"message": f"Tag '{tag.name}' successfully deleted from repository '{repo.name}'."}