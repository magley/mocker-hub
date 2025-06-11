from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.registry.registry_utils import decode_auth_header
from app.api.registry.registry_service import RegistryService, get_registry_service
from app.api.config.logutil import LOGGER
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTDep, get_id_from_jwt, get_username_from_jwt, pre_authorize
from app.api.tags.tag_service import TagService, get_tag_service
from app.api.registry.registry_dto import DeleteTagDTO, DeleteTagResponseDTO
from app.api.repo.repo_service import RepositoryService, get_repo_service
from app.api.access_control.access_control_service import AccessControlService, get_access_control_service
from app.api.config.exception_handler import AccessDeniedException
from app.api.registry.registry_client import RegistryClient, get_registry_client

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

@router.delete("/tag", status_code=200, summary="Delete a tag by its name", response_model=DeleteTagResponseDTO)
@pre_authorize([UserRole.user, UserRole.admin])                             
async def delete_tag_endpoint(
    jwt: JWTDep,
    dto: DeleteTagDTO,
    repo_service: RepositoryService = Depends(get_repo_service), 
    registry_service: RegistryService = Depends(get_registry_service), 
    tag_service: TagService = Depends(get_tag_service),
    registry_client: RegistryClient = Depends(get_registry_client),
    access_control_service: AccessControlService = Depends(get_access_control_service)
):
    user_id = get_id_from_jwt(jwt)
    username = get_username_from_jwt(jwt)
    repo = repo_service.find_by_id(dto.repo_id)
    tag = tag_service.find_by_name_and_repo_id(dto.tag_name, dto.repo_id)

    if not access_control_service.has_delete_tag_access(user_id, repo.id):
        raise AccessDeniedException(f"User {user_id} cannot delete a tag {tag.name} of repository with identifier {repo.id}")

    response = await registry_service.delete_tag(registry_client, username, repo, tag)   

    return response
