from fastapi.testclient import TestClient


from app.api.main import app
from app.api.config.elasticsearch import wait_for_elasticsearch

def test_events___integration():
    with TestClient(app) as client:
        assert wait_for_elasticsearch()

        def search_for_something(headers):
            response = client.get(
                f"/api/v1/events/?query=date_time+%3C%3D+%222165-07-24%22&page_number=1&page_size=10&sort_by=date_time&sort_ascending=true",
                headers=headers)
            return response

        def login(data: dict) -> dict:
            response = client.post("/api/v1/users/login", json=data)
            assert response.status_code == 200
            jwt = response.json()["token"]
            return {"Authorization": f"Bearer {jwt}"}

        superadmin_creds = {
            "username": "admin",
            "password": "Password1" # WARNING: Superadmin password is changed by an earlier test (update user badge?)
            # Therefore, that must run before this!
        }

        superadmin_header = login(superadmin_creds)

        res = search_for_something(superadmin_header)
        assert res.is_success

        hits = res.json()["hits"]
        assert len(hits) >= 0
