from typing import List
from fastapi import APIRouter, Depends

from app.api.config.pagination import PaginatedResultDTO
from app.api.events.event_service import EventService, get_event_service
from app.api.events.event_model import EventLevel
from app.api.config.exception_handler import InvalidInputException
from app.api.user.user_model import UserRole
from app.api.config.cache import cache
from app.api.config.auth import JWTDep, pre_authorize

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=PaginatedResultDTO, status_code=200, summary="Query for analytics")
@cache(expire=10)
@pre_authorize([UserRole.admin, UserRole.superadmin])
async def query_analytics(jwt: JWTDep, query: str, page_number: int, page_size: int, sort_by: str, sort_ascending: bool, event_service: EventService = Depends(get_event_service)):
    result = event_service.query(query, page_number, page_size, sort_by, sort_ascending)
    return result