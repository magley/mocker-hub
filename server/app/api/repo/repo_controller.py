from fastapi import APIRouter, Depends

from app.api.repo.repo_dto import RepositoryCreateDTO, RepositoryDTO
from app.api.repo.repo_service import RepositoryService, get_repo_service

router = APIRouter(prefix="/repositories", tags=["repositories"])

@router.post("/", response_model=RepositoryDTO, status_code=200, summary="Create a new repository")
def register_user(dto: RepositoryCreateDTO, repo_service: RepositoryService = Depends(get_repo_service)):
    repo = repo_service.add(dto)
    return repo