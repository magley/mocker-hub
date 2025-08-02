from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends
from app.api.repo.repo_dto import ReposOfUserDTO, RepositoryCreateDTO, RepositoryDTO, RepositoryExtDTO, \
    RepositoryDescUpdateDTO, RepositoryVisibilityUpdateDTO, ToggleStarRepoDTO, RepositoriesResultDTO
from app.api.repo.repo_service import RepositoryService, get_repo_service
from app.api.config.auth import get_id_from_jwt, get_id_from_jwt_optional, pre_authorize
from app.api.user.user_model import User, UserRole
from app.api.config.auth import JWTBearer, JWTDep, JWTDepOptional
from app.api.user.user_service import UserService, get_user_service
from app.api.org.org_service import OrganizationService, get_org_service
from app.api.config.exception_handler import NotFoundException, AccessDeniedException
from app.api.repo.repo_model import Repository
from app.api.access_control.access_control_service import AccessControlService, get_access_control_service
from app.api.events.event_service import EventService, get_event_service
from app.api.events.event_model import EventLevel

router = APIRouter(prefix="/repositories", tags=["repositories"])

def _repo_model_to_dto(r: Repository) -> RepositoryDTO:
    return RepositoryDTO.model_validate(r.model_dump())

@router.post("/", response_model=RepositoryDTO, status_code=200, summary="Create a new repository")
@pre_authorize([UserRole.user, UserRole.admin])
def register_repo(jwt: JWTDep, dto: RepositoryCreateDTO, repo_service: RepositoryService = Depends(get_repo_service)):
    user_id = get_id_from_jwt(jwt)
    repo = repo_service.add(user_id, dto)
    return repo

@router.get("/u/{username}", response_model=ReposOfUserDTO, status_code=200, summary="Get repositories of user")
def get_repositories_of_user(
    jwt: JWTDepOptional, 
    username: str, 
    repo_service: RepositoryService = Depends(get_repo_service), 
    user_service: UserService = Depends(get_user_service),
    org_service: OrganizationService = Depends(get_org_service)
):
    me_id = get_id_from_jwt_optional(jwt)

    user = user_service.find_by_username(username)
    user_id = user.id

    # NOTE: I had to convert Repository -> RepositoryDTO manually here,
    # because FastAPI does automatic conversion ONLY if the DTO is the
    # response_model (@router.get(..., response_model=...)). If the DTO
    # is nested, it won't work.
    repos = repo_service.get_repositories_of_user(user_id, me_id)
    repos = [_repo_model_to_dto(repo) for repo in repos]

    org_names = org_service.get_org_names_from_repos(repos)

    return ReposOfUserDTO(user_id=user_id, user_name=user.username, repos=repos, organization_names=org_names)

@router.get("/name/{repo_canonical_name:path}", response_model=RepositoryExtDTO, status_code=200, summary="Find repository by its full name")
def get_repo_by_canonical_name(
    jwt: JWTDepOptional, 
    repo_canonical_name: str, 
    repo_service: RepositoryService = Depends(get_repo_service),
    user_service: UserService = Depends(get_user_service),
    access_control_service: AccessControlService = Depends(get_access_control_service),
    event_service: EventService = Depends(get_event_service)
    ):

    user_id = get_id_from_jwt_optional(jwt)
    user = None if (user_id is None) else user_service.find_by_id(user_id) 
    repo = repo_service.find_by_canonical_name(repo_canonical_name)

    event_service.log_read(user_id, User, user_id)
    event_service.log_read(user_id, Repository, repo_canonical_name)

    if not access_control_service.has_read_access(user_id, repo.id):
        raise NotFoundException(Repository, repo_canonical_name)
    
    result = repo.model_dump()
    result["owner_name"] = repo.owner.username
    result["org_name"] = None if (repo.organization is None) else repo.organization.name
    result["can_update"] = access_control_service.has_admin_access(user_id, repo.id)
    result["can_star"] = access_control_service.has_star_access(user_id, repo.id)
    result["starred"] = repo_service.is_repo_starred_by(repo, user) if (result["can_star"]) else False
    result = RepositoryExtDTO.model_validate(result)
    
    return result

@router.put("/{repo_id}/desc", response_model=RepositoryDTO, status_code=200, summary="Update repository description by its id")
@pre_authorize([UserRole.user, UserRole.admin])
def update_repo_desc_by_id(
    jwt: JWTDep, repo_id: int, 
    dto: RepositoryDescUpdateDTO, 
    repo_service:RepositoryService = Depends(get_repo_service),
    access_control_service: AccessControlService = Depends(get_access_control_service)):
    
    user_id = get_id_from_jwt(jwt)

    if not access_control_service.has_admin_access(user_id, repo_id):
        raise AccessDeniedException(f"User {user_id} cannot update repository description with identifier {repo_id}")
    
    repo = repo_service.update_repo_by_id(repo_id, dto)
    return repo

@router.put("/{repo_id}/visibility", response_model=RepositoryDTO, status_code=200, summary="Update repository visibility by its id")
@pre_authorize([UserRole.user, UserRole.admin])
def update_repo_visibility_by_id(
    jwt: JWTDep, 
    repo_id: int, 
    dto: RepositoryVisibilityUpdateDTO, 
    repo_service:RepositoryService = Depends(get_repo_service),
    access_control_service: AccessControlService = Depends(get_access_control_service)):

    user_id = get_id_from_jwt(jwt)
    
    if not access_control_service.has_admin_access(user_id, repo_id):
        raise AccessDeniedException(f"User {user_id} cannot update repository visibiliy with identifier {repo_id}")
    
    repo = repo_service.update_repo_by_id(repo_id, dto)
    return repo

@router.put("/star/{repo_id}", response_model=ToggleStarRepoDTO, status_code=200, summary="Star or unstar a repository by its ID")
@pre_authorize([UserRole.user])
def toggle_repo_star(
    jwt: JWTDep, 
    repo_id: int, 
    repo_service:RepositoryService = Depends(get_repo_service),
    access_control_service: AccessControlService = Depends(get_access_control_service)):

    user_id = get_id_from_jwt(jwt)
    
    can_star = access_control_service.has_star_access(user_id, repo_id)
    if can_star == False:
        raise AccessDeniedException(f"User {user_id} cannot star or unstar repository with identifier {repo_id}")
    
    repo, starred = repo_service.toggle_repo_star(user_id, repo_id)
    
    return ToggleStarRepoDTO(**repo.model_dump(), starred=starred)

@router.get("/starred/u/{username}", response_model=ReposOfUserDTO, status_code=200, summary="Get starred repositories of user")
def get_starred_repositories_of_user(
    username: str, 
    user_service: UserService = Depends(get_user_service),
    repo_service: RepositoryService = Depends(get_repo_service), 
    org_service: OrganizationService = Depends(get_org_service)):
    
    user = user_service.find_by_username(username)

    if (user.role != UserRole.user):
        raise AccessDeniedException(f"User {username} cannot star or unstar repositories")

    repos = repo_service.get_starred_repositories_of_user(user.id)
    repos = [_repo_model_to_dto(repo) for repo in repos]

    org_names = org_service.get_org_names_from_repos(repos)

    return ReposOfUserDTO(user_id=user.id, user_name=user.username, repos=repos, organization_names=org_names)

@router.get("/public/", response_model=RepositoriesResultDTO, status_code=200, summary="Search all public repositories with paginated results")
async def search_public_repositories(page_number: int, page_size: int, show_badge_official: bool, show_badge_sponsored: bool,
                                     show_badge_verified: bool, query: str = "", repo_service: RepositoryService = Depends(get_repo_service),
                                     org_service: OrganizationService = Depends(get_org_service)):
    repos, result_info = repo_service.search_public_repositories(query, page_number, page_size, show_badge_official, show_badge_sponsored, show_badge_verified)
    org_names = org_service.get_org_names_from_repos(repos)
    repos = [_repo_model_to_dto(repo) for repo in repos]
    return RepositoriesResultDTO(hits=repos, info=result_info, organization_names=org_names)


@router.get("/org/{org_id}", response_model=List[RepositoryDTO], status_code=200, summary="Get repositories of user")
@pre_authorize([UserRole.user, UserRole.admin])
def get_repositories_by_org(jwt: JWTDep, org_id: int, repo_service: RepositoryService = Depends(get_repo_service)):
    user_id = get_id_from_jwt(jwt)
    repos = repo_service.get_repositories_by_org(org_id, user_id)
    return repos

