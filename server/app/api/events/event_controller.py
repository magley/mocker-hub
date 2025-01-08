from typing import List
from fastapi import APIRouter

from app.api.events.event_dto import EventDTO
from app.api.events.event_service import EventService
from app.api.events.event_model import EventLevel

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[EventDTO], status_code=200, summary="Something...")
async def search_events_route(log_level: str, start_date: str = None, end_date: str = None):
    event_service = EventService()

    log_level = EventLevel(log_level)
    events = event_service.search(log_level, start_date, end_date)
    return events