from typing import List
from fastapi import APIRouter, Depends

from app.api.events.event_dto import EventDTO
from app.api.events.event_service import EventService, get_event_service
from app.api.events.event_model import EventLevel
from app.api.config.exception_handler import InvalidInputException

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[EventDTO], status_code=200, summary="Something...")
async def search_events_route(log_level: str, start_date: str = None, end_date: str = None, event_service: EventService = Depends(get_event_service)):
    try:
        log_level = EventLevel(log_level)
    except ValueError:
        possible_values = [lvl.value for lvl in EventLevel]
        raise InvalidInputException(f"Unknown log level '{log_level}', supported values are {possible_values}")

    events = event_service.search(log_level, start_date, end_date)
    return events