import json
import logging
from typing import TYPE_CHECKING, Any, Generator, cast

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

        self._payload = None

    @property
    def asset(self) -> Asset:
        """The parent Asset of this Version."""
        return self._asset

    @property
    def is_active(self) -> bool:
        """Whether the Version is active or not."""
        return self.payload.get("active") or False

    @property
    def number(self) -> int:
        """The iteration number of this Version."""
        return int(self.tokens["version"])

    @property
    def payload(self) -> dict[str, Any]:
        """The stored key/values for the Version"""
        if self._payload is None:
            with self._path.open() as f:
                self._payload = json.load(f)
        return self._payload

    def _next_version_number(self) -> int:
        """Get the next available version number for the department."""
        tokens = self.tokens
        tokens.pop("version", None)

        try:
            highest = max(
                [
                    version.number
                    for version in self.find(resolver=self._resolver, **tokens)
                ]
            )
        except ValueError:
            highest = 0

        return highest + 1

    @staticmethod
    def _tokens_to_kwargs(resolver: Resolver | None = None, **tokens) -> dict[str, Any]:
        """Convert raw token key/values to instantiation kwargs"""
        from stage.assets import Asset

        return {
            "asset": Asset(kind=tokens["kind"], name=tokens["name"], resolver=resolver),
            "department": tokens["department"],
            "number": int(tokens["version"]),
            "resolver": resolver,
        }

    def create(self, active: bool, exist_ok: bool = False):
        """Write the given json data to the resolved template."""
        if not exist_ok and self.exists:
            raise FileExistsError(f"Version {self._path} already exists")

        next_number = self._next_version_number()
        if self.number != next_number:
            raise ValueError(
                f"{self.number} isn't the next available version number {next_number}",
            )

        self._path.parent.mkdir(parents=True, exist_ok=True)

        with self._path.open("w") as f:
            json.dump({"active": active}, f, indent=4, sort_keys=True)

    @classmethod
    def find(
        cls,
        resolver: Resolver | None = None,
        **tokens,
    ) -> Generator[Version]:
        """Yield any existing instance that match the given tokens."""
        tokens.pop("version", None)
        if "number" in tokens:
            tokens["version"] = tokens.pop("number")

        for entity in super().find(resolver=resolver, **tokens):
            yield cast(Version, entity)
