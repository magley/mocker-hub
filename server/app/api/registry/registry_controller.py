from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.user.user_service import UserService, get_user_service
from app.api.registry.registry_utils import decode_auth_header, parse_scope, build_jwt_for_docker_registry

router = APIRouter(prefix="/registry", tags=["dockerhub-registry"])

# In case you still have issues, create a file `/etc/docker/daemon.json`
# and write the following:
# 
# {
#  "insecure-registries": ["localhost:5000"]
# }

@router.get("", summary="???")
def registry_endpoint(request: Request, user_service: UserService = Depends(get_user_service), service: str | None = None, scope: str | None = None):
    authorization_header = request.headers.get("Authorization")
    print(authorization_header)

    if not authorization_header:
        # TODO:  Most `pull` operations _should_ work (unless the repo is private etc.)
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme (must be Basic)")

    auth_token = authorization_header.split(" ")[1]
    username, password = decode_auth_header(auth_token)

    if not user_service.exists_with_credentials(username, password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if scope is not None:
        action = parse_scope(username, scope)
        print(action)

        raise HTTPException(status_code=401)

    jwt = build_jwt_for_docker_registry(username, service, scope)

    return {"token": jwt}


@router.api_route("/notifications", methods=["POST", "PUT"], summary="Webhook for Docker Registry")
def registry_notification_endpoint(data: dict):
    for event in data["events"]:
        action = event.get("action", None)
        username = event.get("actor", {}).get("name", None)
        repository = event.get("target", {}).get("repository", None)
        tag = event.get("target", {}).get("tag", None)
        
        print(f"User '{username}' completed '{action}' of repository '{repository}' with tag '{tag}'")

    return {}