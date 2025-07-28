from pydantic import BaseModel
from datetime import datetime
from typing import List

class EventDTO(BaseModel):
    date_time: datetime
    log_level: str
    text_content: str


class LogDTO(BaseModel):
    date_time: datetime
    level: str
    text: str

class LogsResultInfoDTO(BaseModel):
    page: int
    page_size: int
    total_pages: int
    total_hits: int

class LogsResultDTO(BaseModel):
    hits: List[LogDTO]
    info: LogsResultInfoDTO