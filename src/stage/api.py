import logging

from fastapi import FastAPI, HTTPException, status

from stage.models import Asset
from stage.resolver import Resolver

logger = logging.getLogger(__name__)

_status_codes = {
    FileExistsError: status.HTTP_409_CONFLICT,
    KeyError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    ValueError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}

app = FastAPI(title="Stage")


def _resolver_http_exception(exc: Exception) -> HTTPException:
    """Translate resolver failures into HTTP responses."""
    detail = exc.args[0] if isinstance(exc, KeyError) and exc.args else str(exc)

    for cls, status_code in _status_codes.items():
        if isinstance(exc, cls):
            return HTTPException(status_code=status_code, detail=detail)

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    )


@app.post("/assets")
def create_asset(asset: Asset, exist_ok: bool = False) -> dict[str, str]:
    """Create an Asset"""
    try:
        path = Resolver().create("asset", exist_ok=exist_ok, **asset.model_dump())
    except Exception as e:
        raise _resolver_http_exception(e) from e

    return {"path": path.as_posix(), **asset.model_dump()}


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
