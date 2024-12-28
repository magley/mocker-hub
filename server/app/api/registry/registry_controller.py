from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.user.user_service import UserService, get_user_service
from app.api.registry.registry_utils import decode_auth_header, parse_scope, build_jwt_for_docker_registry
from app.api.access_control.access_control_service import AccessControlService, get_access_control_service
from app.api.repo.repo_service import RepositoryService, get_repo_service
from app.api.registry.registry_dto import RegistryActionOperation

router = APIRouter(prefix="/registry", tags=["dockerhub-registry"])

@router.get("", summary="???")
def registry_endpoint(
    request: Request, 
    user_service: UserService = Depends(get_user_service), 
    repo_service: RepositoryService = Depends(get_repo_service),
    access_control_service: AccessControlService = Depends(get_access_control_service),
    service: str | None = None, scope: str | None = None
    ):
    authorization_header = request.headers.get("Authorization")
    print(authorization_header)

    if not authorization_header:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not authorization_header.startswith("Basic "):
        raise HTTPException(status_code=401, detail="Invalid authorization scheme (must be Basic)")

    auth_token = authorization_header.split(" ")[1]
    username, password = decode_auth_header(auth_token)

    if not user_service.exists_with_credentials(username, password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if scope is not None:  # Push/pull to repo. If it's None, then this is a login.
        action = parse_scope(username, scope)
        user = user_service.find_by_username(username)
        repo = repo_service.find_by_canonical_name(action.repo_canonical_name)

        if RegistryActionOperation.push in action.operations:
            can_write = access_control_service.has_write_access(user.id, repo.id)
            if not can_write:
                raise HTTPException(status_code=401, detail=f"User {user.username} cannot push to repo {repo.canonical_name}")
        elif RegistryActionOperation.pull in action.operations:
            can_read = access_control_service.has_read_access(user.id, repo.id)
            if not can_read:
                raise HTTPException(status_code=401, detail=f"User {user.username} cannot pull from repo {repo.canonical_name}")
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operations {action.operations}")

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