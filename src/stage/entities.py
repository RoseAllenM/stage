import logging
from typing import Any, Generator

from upath import UPath

from stage.resolver import Resolver

logger = logging.getLogger(__name__)


class Entity:
    """Base class for Database entries."""

    _template = None

    def __init__(self, resolver: Resolver | None = None):
        self._resolver = resolver or Resolver()

        if self._template is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} doesn't have an associated Template",
            )

        self._id = self._resolver.resolve(self._template, **self.tokens)

    def __repr__(self):
        package = ".".join(self.__module__.split(".")[:2])
        return f"<{package}.{self.__class__.__name__}: {self.id} at {hex(id(self))}>"

    @property
    def _path(self) -> UPath:
        """The location on disk that defines this Entity."""
        return self._resolver.store / self.id

    @property
    def exists(self) -> bool:
        """Whether the Entity exists in the service."""
        return self._path.exists()

    @property
    def id(self) -> str:
        """The unique identier for this Entity."""
        return self._id

    @property
    def tokens(self) -> dict[str, int | str]:
        """The identifying key/values for this Entity."""
        try:
            return getattr(self, "_tokens")
        except AttributeError:
            return {}

    @staticmethod
    def _tokens_to_kwargs(resolver: Resolver | None = None, **tokens) -> dict[str, Any]:
        """Convert raw token key/values to instantiation kwargs"""
        return {"resolver": resolver, **tokens}

    @classmethod
    def find(cls, resolver: Resolver | None = None, **tokens) -> Generator[Entity]:
        """Yield any existing instance that match the given tokens."""
        if not cls._template:
            raise NotImplementedError(
                f"Class {cls.__name__} doesn't specify a template"
            )

        resolver = resolver or Resolver()

        tokens = {key: value for key, value in tokens.items() if value is not None}
        for _, values in resolver.iterate(cls._template, **tokens):
            yield cls(**cls._tokens_to_kwargs(resolver=resolver, **values))
