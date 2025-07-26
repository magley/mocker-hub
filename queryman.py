import os
from typing import List
from enum import Enum
from elasticsearch_dsl import Document, Text, Date, Keyword, Search, Q, connections
import math

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

def search(page_number: int, page_size: int, sort_by: str, sort_ascending: bool) -> List:
    hostname = os.getenv("ES_HOST", "localhost:9200")
    connections.create_connection(hosts=[f"http://{hostname}"])

    if page_number < 1:
        page_number = 1
    if page_size < 1:
        page_size = 1

    sort_str = f"{'' if sort_ascending else '-'}{sort_by}"
    if sort_by not in ['date_time', 'log_level', 'text_content']:
        sort_str = None

    pag_start = (page_number - 1) * page_size
    pag_end = pag_start + page_size

    s = Search(index=Event.Index.name)
    if sort_str is not None:
        s = s.sort(sort_str)
    s = s[pag_start:pag_end]


    q = Q('bool',
        must = [
            Q("match", text_content="wants"),
            #Q('term', log_level=EventLevel.Error.value),
            Q('range', date_time={"gte": "2025-06-10"}),
        ]
    )
    
    s = s.query(q)
    response = s.execute()

    return response

PAGE_NUM = 1
PAGE_SIZE = 40

res = search(PAGE_NUM, PAGE_SIZE, 'date_time', True)
total_hits = res.hits.total.value
total_pages = math.ceil(total_hits / PAGE_SIZE)

for hit in res:
    print(f"[{hit.date_time}] [{hit.log_level}] {hit.text_content}")

print()
print(f"Page ({PAGE_NUM} / {total_pages}) [{PAGE_SIZE} items of {total_hits}]")