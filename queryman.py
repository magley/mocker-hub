import os
from enum import Enum
from elasticsearch_dsl import Document, Text, Date, Keyword, Search, Q, connections


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

def search():
    hostname = os.getenv("ES_HOST", "localhost:9200")
    connections.create_connection(hosts=[f"http://{hostname}"])

    s = Search(index=Event.Index.name)

    q = Q('term', log_level=EventLevel.Error.value)

    q = Q('range', date_time={
              "gte": "2025-07-10",
              "lt": "2025-07-31"
    })

    q = Q('bool',
        must = [
            #Q("match", text_content="wants"),
            Q('term', log_level=EventLevel.Error.value),
            Q('range', date_time={"gte": "2025-06-10"}),
        ]
    )
    
    s = s.query(q)
    response = s.execute()

    for hit in response:
        print(f"[{hit.date_time}] [{hit.log_level}] {hit.text_content}")

search()