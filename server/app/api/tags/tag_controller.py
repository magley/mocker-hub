from typing import List
from fastapi import APIRouter, Depends

from app.api.tags.tag_dto import TagDTO
from app.api.tags.tag_service import TagService, get_tag_service

router = APIRouter(prefix="/tags", tags=["tags"])

@router.post("/", response_model=List[TagDTO], status_code=200, summary="Get all tags of a repository")
def get_tags_of_repo(repo_name: str, tag_service: TagService = Depends(get_tag_service)):
    tags = tag_service.get_tags_by_repository_name(repo_name)
    return tags

# TODO:  add method for filtering and sorting