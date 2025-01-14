from pydantic import BaseModel
from datetime import datetime

class EventDTO(BaseModel):
    date_time: datetime
    log_level: str
    text_content: str