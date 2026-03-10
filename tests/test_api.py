from fastapi.testclient import TestClient

from stage.api import app, create_app


def test_create_app_returns_fastapi_instance() -> None:
    created_app = create_app()

    assert created_app.title == "stage"


def test_healthcheck_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
