import os
from redis import Redis
from rq import Worker, Queue

scheme = os.environ["REDIS_SCHEME"]
host = os.environ["REDIS_HOST"]
port = os.environ["REDIS_PORT"]
connection = Redis.from_url(f"{scheme}://{host}:{port}")

if __name__ == '__main__':
    default_queue = [Queue(name, connection=connection) for name in ['delete_tag']]
    worker = Worker(queues=default_queue, connection=connection)
    worker.work()