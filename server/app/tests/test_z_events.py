from fastapi.testclient import TestClient


from app.api.main import app
from app.api.config.elasticsearch import wait_for_elasticsearch

def test_events___integration():
    with TestClient(app) as client:
        assert wait_for_elasticsearch()

        def search_for_something():
            response = client.get(f"/api/v1/events/?query=date_time+%3C%3D+%222165-07-24%22&page_number=1&page_size=10&sort_by=date_time&sort_ascending=true")
            return response
        
        res = search_for_something()
        assert res.is_success

        hits = res.json()["hits"]
        assert len(hits) >= 0
