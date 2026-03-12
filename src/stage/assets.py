import logging
from typing import TYPE_CHECKING

import stage.entities
from stage.versions import Version

if TYPE_CHECKING:
    from stage.resolver import Resolver


logger = logging.getLogger(__name__)


class Asset(stage.entities.Entity):
    """A high-level production tracking element, a container for versioned work."""

    _template = "asset"

    def __init__(self, kind: str, name: str, resolver: Resolver | None = None):
        self._tokens = {"kind": kind, "name": name}

        super().__init__(resolver=resolver)

    def create(self, exist_ok: bool = False):
        """Create the Asset on disk."""
        if not exist_ok and self.exists:
            raise FileExistsError(f"Asset {self._path} already exists")

        self._path.mkdir(parents=True, exist_ok=exist_ok)

    def new_version(self, department: str, number: int, active: bool) -> Version:
        """Create a new Version of this Asset."""
        version = Version(
            asset=self,
            department=department,
            number=number,
            resolver=self._resolver,
        )

        version.create(active=active)

        return version
