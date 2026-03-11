import json
import logging
from typing import TYPE_CHECKING

import stage.entities

if TYPE_CHECKING:
    from stage.assets import Asset
    from stage.resolver import Resolver

logger = logging.getLogger(__name__)


class Version(stage.entities.Entity):
    """An iteration of a specific Asset by a specific department."""

    _template = "version"

    def __init__(
        self,
        asset: Asset,
        department: str,
        number: int,
        resolver: Resolver | None = None,
    ):
        self._asset = asset
        self._tokens = {"department": department, "version": number, **asset.tokens}

        super().__init__(resolver=resolver)

    @property
    def asset(self) -> Asset:
        """The parent Asset of this Version."""
        return self._asset

    def create(self, active: bool, exist_ok: bool = False):
        """Write the given json data to the resolved template."""
        if not exist_ok and self._path.exists():
            raise FileExistsError(f"Version {self._path} already exists")

        self._path.parent.mkdir(parents=True, exist_ok=True)

        with self._path.open("w") as f:
            json.dump({"active": active}, f, indent=4, sort_keys=True)
