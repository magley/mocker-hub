import logging
import os
from typing import Type
from app.api.events.event_model import Event, EventLevel
from elasticsearch_dsl import Search
from datetime import datetime
from app.api.config.logutil import LOGGER


class EventService:
    def __init__(self):
        ...

    def log_read(self, user_id: int | None, entity_type: Type, entity_identifier: int | str):
        """
        Log case when user tries to access an entity.
        Example: `log_read(1, Repository, 'user1/reponame')`
        """
        self.log(EventLevel.Info, f"User {user_id} wants to read {entity_type.__name__} {entity_identifier}")

    def log(self, log_level: EventLevel, text_content: str):
        """Generic log function."""
        LOGGER.log(self._event_level_to_log_level(log_level), text_content)

    def search(self, log_level: EventLevel, start_date: str = None, end_date: str = None):
        s = Search(index=Event.Index.name).filter("term", log_level=log_level.value)
        
        if start_date and end_date:
            s = s.filter("range", date_time={"gte": start_date, "lte": end_date})
        elif start_date:
            s = s.filter("range", date_time={"gte": start_date})
        elif end_date:
            s = s.filter("range", date_time={"lte": end_date})
        
        response = s.execute()
        return [{
            "date_time": hit.date_time, 
            "log_level": hit.log_level, 
            "text_content": hit.text_content
        } for hit in response]
    
    def _event_level_to_log_level(self, event_level: EventLevel):
        if event_level == EventLevel.Debug:
            return logging.DEBUG
        elif event_level == EventLevel.Info:
            return logging.INFO
        elif event_level == EventLevel.Warning:
            return logging.WARNING
        elif event_level == EventLevel.Error:
            return logging.ERROR
        else:
            raise ValueError(f"Unknown event level: {event_level}")


def get_event_service() -> EventService:
    return EventService()