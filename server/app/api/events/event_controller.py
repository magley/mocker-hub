from typing import List
from fastapi import APIRouter, Depends

from app.api.events.event_dto import EventDTO, LogsResultDTO
from app.api.events.event_service import EventService, get_event_service
from app.api.events.event_model import EventLevel
from app.api.config.exception_handler import InvalidInputException

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=LogsResultDTO, status_code=200, summary="Query for analytics")
async def query_analytics(query: str, page_number: int, page_size: int, sort_by: str, sort_ascending: bool, event_service: EventService = Depends(get_event_service)):
    result = event_service.query(query, page_number, page_size, sort_by, sort_ascending)
    return result