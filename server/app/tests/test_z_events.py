from fastapi.testclient import TestClient


from app.api.main import app
from app.api.config.elasticsearch import wait_for_elasticsearch

def test_temp___integration():
    with TestClient(app) as client:
        assert wait_for_elasticsearch()

        def search_for_something(level: str):
            response = client.get(f"/api/v1/events/?log_level={level}")
            return response
        
        res = search_for_something("info")
        assert res.is_success
        assert len(res.json()) > 0