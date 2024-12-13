import os
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

# When you want to use cache, you just import the decorator:
#
# from fastapi_cache.decorator import cache
#
# @cache
# def f(...)
#
# But when calling `f`, an exception will be raised in case Redis
# isn't set up. When we're doing e.g. integration tests, we don't
# have Redis set up, so we have to mock `cache` into a no-op.
#
# This means that you have to import `cache` from _here_, and not
# from `fastapi_cache.decorator`.
if os.getenv('mocker_hub_TEST_ENV') is not None:
    print("[!] Detected environment variable mocker_hub_TEST_ENV -> not using cache")

    def no_op(expire=None):
        def decorator(func):
            return func
        return decorator

    def cache(expire=None):
        return no_op(expire)
    
    def init_cache():
        ...
else:
    from fastapi_cache.decorator import cache as _cache
    cache = _cache

    def init_cache():
        hostname = os.environ['REDIS_HOST']
        port = os.environ['REDIS_PORT']
        redis = aioredis.from_url(f"redis://{hostname}:{port}")
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")