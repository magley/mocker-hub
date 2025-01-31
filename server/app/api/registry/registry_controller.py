from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.registry.registry_utils import decode_auth_header
from app.api.registry.registry_service import RegistryService, get_registry_service
from app.api.config.logutil import LOGGER

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