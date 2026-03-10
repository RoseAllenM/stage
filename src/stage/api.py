import logging

from fastapi import FastAPI

logger = logging.getLogger(__name__)


app = FastAPI(title="Stage")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
