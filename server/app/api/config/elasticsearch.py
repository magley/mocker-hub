import os
from elasticsearch_dsl import connections


def init_elasticsearch_connection():
    if os.getenv('mocker_hub_TEST_ENV') is not None:
        print("[!] Detected mocker_hub_TEST_ENV -> Disabling Elasticsearch for testing")
        # connections._co.clear()   # Obviously this is bad if we wanna do integration tests...
    else:
        """
        NOTE: For each `Document` you want to be indexed in ElasticSearch,
        you must call its `init()` function _AFTER_ this function.
        """
        connections.create_connection(hosts=["http://elasticsearch:9200"])