from typing import List
from fastapi import APIRouter, Depends

from app.api.tags.tag_dto import TagDTO
from app.api.tags.tag_service import TagService, get_tag_service
from app.api.config.pagination import PaginatedDTO, PaginationParams
from app.api.config.cache import cache

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/", response_model=List[TagDTO], status_code=200, summary="Get all tags of a repository")
@cache(expire=10)
def get_tags_of_repo(repo_name: str, tag_service: TagService = Depends(get_tag_service)):
    tags = tag_service.get_tags_by_repository_name(repo_name)
    tags = [TagDTO.from_tag(tag) for tag in tags]
    return tags

@router.get("/filter", response_model=PaginatedDTO[TagDTO], status_code=200, summary="Filters tags of a repository")
@cache(expire=10)
def filter(
        repo_name: str,
        search_query: str = "",
        params: PaginationParams = Depends(), 
        tag_service: TagService = Depends(get_tag_service)):
    tags, total_tags = tag_service.filter(repo_name, search_query, params)
    tags = [TagDTO.from_tag(tag) for tag in tags]
    return PaginatedDTO(items=tags, total_count=total_tags)