from app.api.events.event_model import Event, EventLevel
from elasticsearch_dsl import Search
from datetime import datetime


class EventService:
    def __init__(self):
        ...

    def save(self, date_time: datetime, log_level: EventLevel, text_content: str) -> Event:
        event = Event(date_time=date_time, log_level=str(log_level), text_content=text_content)
        event.save()
        return event

def get_event_service() -> EventService:
    return EventService()