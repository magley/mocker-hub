from elasticsearch_dsl import connections

def init_elasticsearch_connection():
    """
    NOTE: For each `Document` you want to be indexed in ElasticSearch,
    you must call its `init()` function _AFTER_ this function.
    """
    connections.create_connection(hosts=["http://elasticsearch:9200"])