from redis import Redis
from fastapi import Request
from rq import Queue

class JobsClient:
    
    def __init__(self, host, port):
        self.connection: Redis = Redis(host=host, port=port)

    def create(self, name: str) -> Queue:
        return Queue(name, connection=self.connection)

    def get(self, name: str) -> Queue:
        return self.create(name)
    
def get_jobs_client(request: Request = Request) -> JobsClient:
    return request.app.jobs_client
