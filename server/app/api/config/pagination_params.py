from typing import Optional
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