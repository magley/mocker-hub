from enum import Enum
from elasticsearch_dsl import Document, Text, Date, Keyword

class EventLevel(Enum):
    Debug = "debug"
    Info = "info"
    Warning = "warning"
    Error = "error"

class Event(Document):
    date_time = Date()
    log_level = Keyword()
    text_content = Text()

    class Index:
        name = 'events'