from pydantic import BaseModel
from datetime import datetime
from typing import List

from app.api.config.pagination import PaginatedResultInfoDTO


class EventDTO(BaseModel):
    date_time: datetime
    log_level: str
    text_content: str


class LogDTO(BaseModel):
    date_time: datetime
    level: str
    text: str
