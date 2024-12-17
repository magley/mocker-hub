from typing import List
from fastapi import APIRouter, Depends

from app.api.repo.repo_dto import ReposOfUserDTO, RepositoryCreateDTO, RepositoryDTO, RepositoryExtDTO
from app.api.repo.repo_service import RepositoryService, get_repo_service
from app.api.config.auth import get_id_from_jwt, get_id_from_jwt_optional, pre_authorize
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTBearer, JWTDep, JWTDepOptional
from app.api.user.user_service import UserService, get_user_service
from app.api.org.org_service import OrganizationService, get_org_service
from app.api.config.exception_handler import NotFoundException
from app.api.repo.repo_model import Repository

router = APIRouter(prefix="/repositories", tags=["repositories"])

@router.post("/", response_model=RepositoryDTO, status_code=200, summary="Create a new repository")
@pre_authorize([UserRole.user, UserRole.admin])
def register_repo(jwt: JWTDep, dto: RepositoryCreateDTO, repo_service: RepositoryService = Depends(get_repo_service)):
    user_id = get_id_from_jwt(jwt)
    repo = repo_service.add(user_id, dto)
    return repo

@router.get("/u/{user_id}", response_model=ReposOfUserDTO, status_code=200, summary="Get repositories of suer")
def get_repositories_of_user(
    jwt: JWTDepOptional, 
    user_id: int, 
    repo_service: RepositoryService = Depends(get_repo_service), 
    user_service: UserService = Depends(get_user_service),
    org_service: OrganizationService = Depends(get_org_service)
):
    me_id = get_id_from_jwt_optional(jwt)

    # NOTE: I had to convert Repository -> RepositoryDTO manually here,
    # because FastAPI does automatic conversion ONLY if the DTO is the
    # response_model (@router.get(..., response_model=...)). If the DTO
    # is nested, it won't work.
    repos = repo_service.get_repositories_of_user(user_id, me_id)
    repos = [RepositoryDTO.model_validate(repo.model_dump()) for repo in repos]

    user = user_service.find_by_id(user_id)
    org_names = org_service.find_org_names_by_ids([r.organization_id for r in repos if r.organization_id is not None])

    return ReposOfUserDTO(user_id=user_id, user_name=user.username, repos=repos, organization_names=org_names)


@router.get("/{repo_canonical_name:path}", response_model=RepositoryExtDTO, status_code=200, summary="Find repository by its full name")
def get_repo_by_canonical_name(jwt: JWTDepOptional, repo_canonical_name: str, repo_service: RepositoryService = Depends(get_repo_service)):
    user_id = get_id_from_jwt_optional(jwt)
    repo = repo_service.find_by_canonical_name(repo_canonical_name)

    if not repo_service.user_has_read_access_to_repo(repo, user_id):
        raise NotFoundException(Repository, repo_canonical_name)
    
    result = repo.model_dump()
    result["owner_name"] = repo.owner.username
    result["org_name"] = None if (repo.organization is None) else repo.organization.name
    result = RepositoryExtDTO.model_validate(result)

    return result