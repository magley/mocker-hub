from typing import Generic, List, Optional, TypeVar
from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int = Query(1, ge=1)
    limit: int = Query(10, le=100)
    sort_by: Optional[str] = Query("")
    sort_order: Optional[str] = Query("asc", regex="^(asc|desc)$")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.limit


T = TypeVar('T')
class PaginatedDTO(BaseModel, Generic[T]):
    items: List[T]
    total_count: int

class PaginatedResultInfoDTO(BaseModel):
    page: int
    page_size: int
    total_pages: int
    total_hits: int

class PaginatedResultDTO(BaseModel, Generic[T]):
    hits: List[T]
    info: PaginatedResultInfoDTO