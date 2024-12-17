from typing import List
from fastapi import APIRouter, Depends

from app.api.repo.repo_dto import RepositoryCreateDTO, RepositoryDTO
from app.api.repo.repo_service import RepositoryService, get_repo_service
from app.api.config.auth import get_id_from_jwt, pre_authorize
from app.api.user.user_model import UserRole
from app.api.config.auth import JWTBearer, JWTDep, JWTDepOptional

router = APIRouter(prefix="/repositories", tags=["repositories"])

@router.post("/", response_model=RepositoryDTO, status_code=200, summary="Create a new repository")
@pre_authorize([UserRole.user, UserRole.admin])
def register_repo(jwt: JWTDep, dto: RepositoryCreateDTO, repo_service: RepositoryService = Depends(get_repo_service)):
    user_id = get_id_from_jwt(jwt)
    repo = repo_service.add(user_id, dto)
    return repo

@router.get("/u/{user_id}", response_model=List[RepositoryDTO], status_code=200, summary="Get repositories of suer")
def get_repositories_of_user(jwt: JWTDepOptional, user_id: int, repo_service: RepositoryService = Depends(get_repo_service)):
    me_id = None
    try: 
        me_id = get_id_from_jwt(jwt)
    except: ...

    return repo_service.get_repositories_of_user(user_id, me_id)