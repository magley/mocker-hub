import asyncio
import os
import time
from elasticsearch_dsl import connections
import requests
from app.api.config.logutil import LOGGER

def get_elasticsearch_address():
    hostname = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
    port = os.getenv("ELASTICSEARCH_PORT", "9200")
    return f"http://{hostname}:{port}"


async def try_to_init_elasticsearch():
    LOGGER.info("Establishing ElasticSearch connection...")
    while True:
        try:
            from app.api.events.event_model import Event
            hostname = os.getenv("ELASTICSEARCH_HOST", "elasticsearch")
            port = os.getenv("ELASTICSEARCH_PORT", "9200")
            es = connections.create_connection(hosts=[get_elasticsearch_address()])

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

    
def wait_for_elasticsearch(max_retries=30, delay=2):
    url = get_elasticsearch_address()
    for i in range(max_retries):
        try:
            print(f"Connecting to ElasticSearch ({i+1}/{max_retries})...")
            response = requests.get(f"{url}/_cluster/health")
            if response.status_code == 200:
                print("Connected to ElasticSearch")
                return True
        except requests.ConnectionError as e:
            print(f"Failed {str(e)}")
            pass
        time.sleep(delay)
    print(f"Failed to wait for ElasticSearch ({max_retries} retries, {delay} delay) :/")
    return False