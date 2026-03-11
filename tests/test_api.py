import pytest
from fastapi.testclient import TestClient

from stage.api import app


def test_create_app_returns_fastapi_instance() -> None:
    assert app.title == "Stage"


def test_healthcheck_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("resolver_error", "expected_status", "expected_detail"),
    [
        (ValueError("bad token"), 422, "bad token"),
        (KeyError("missing token"), 422, "missing token"),
        (FileExistsError("already exists"), 409, "already exists"),
        (OSError("disk failure"), 500, "disk failure"),
    ],
)
def test_create_asset_endpoint_returns_resolver_errors(
    monkeypatch: pytest.MonkeyPatch,
    resolver_error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    client = TestClient(app)

    def mock_create(*args, **kwargs):
        raise resolver_error

    monkeypatch.setattr("stage.api.Resolver.create", mock_create)

    response = client.post(
        "/assets",
        json={"kind": "character", "name": "hero_01"},
    )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
