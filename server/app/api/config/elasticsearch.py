import asyncio
import os
from elasticsearch_dsl import connections
from app.api.config.logutil import LOGGER

async def try_to_init_elasticsearch():
    if os.getenv('mocker_hub_TEST_ENV') is not None:
        print("[!] Detected mocker_hub_TEST_ENV -> Disabling Elasticsearch for testing")
        return

    LOGGER.info("Establishing ElasticSearch connection...")
    while True:
        try:
            from app.api.events.event_model import Event
            es = connections.create_connection(hosts=["http://elasticsearch:9200"])

            if es.ping():
                LOGGER.info(f"Elasticsearch connected successfully")
                Event.init()
                return
            else:
                raise ConnectionError("Elasticsearch connected but is not reachable")
        except Exception as e:
            seconds = 5
            LOGGER.error(f"Could not load ElasticSearch: {e}. Retrying in {seconds} seconds...", exc_info=False)
            await asyncio.sleep(seconds)