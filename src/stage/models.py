import logging

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Asset(BaseModel):
    """The identifying attributes for an Asset."""

    kind: str
    name: str
