import os
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

def init_cache():
    hostname = os.environ['REDIS_HOST']
    port = os.environ['REDIS_PORT']
    redis = aioredis.from_url(f"redis://{hostname}:{port}")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")