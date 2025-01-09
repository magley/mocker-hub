import os
from app.api.events.event_model import Event, EventLevel
from elasticsearch_dsl import Search
from datetime import datetime


class EventService:
    def __init__(self):
        ...

    def save(self, date_time: datetime, log_level: EventLevel, text_content: str) -> Event:
        event = Event(date_time=date_time, log_level=log_level.value, text_content=text_content)
        if os.getenv('mocker_hub_TEST_ENV') is None:
            event.save()
        return event

    def search(self, log_level: EventLevel, start_date: str = None, end_date: str = None):
        s = Search(index=Event.Index.name).filter("term", log_level=log_level.value)
        
        if start_date and end_date:
            s = s.filter("range", date_time={"gte": start_date, "lte": end_date})
        
        response = s.execute()
        return [{
            "date_time": hit.date_time, 
            "log_level": hit.log_level, 
            "text_content": hit.text_content
        } for hit in response]
  

def get_event_service() -> EventService:
    return EventService()