import importlib.resources
import logging
import os
import re
import string
import tempfile
from copy import deepcopy
from typing import Generator, Tuple

from omegaconf import OmegaConf
from upath import UPath

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG = "stage._config"
_STAGE_CONFIG = "STAGE_CONFIG"
_STAGE_STORE = "STAGE_STORE"


class Resolver:
    """Asset version validator and resolver."""

    def __init__(self) -> None:
        self._store = None

        self._templates = None
        self._tokens = None

    @property
    def store(self) -> UPath:
        """The root storage directory of all other template paths."""
        if self._store is None:
            store = os.getenv(_STAGE_STORE)
            if store:
                self._store = UPath(store)
            else:
                self._store = UPath(tempfile.gettempdir()) / "stage"
                logger.warning(
                    "'%s' environment variable is NOT defined, using %s",
                    _STAGE_STORE,
                    self._store.as_posix(),
                )

        return self._store

    @property
    def templates(self) -> dict[str, str]:
        """All named tokenized locations."""
        if self._templates is None:
            self._templates = _load_config_file("templates.yaml")
        return deepcopy(self._templates)

    @property
    def tokens(self) -> dict[str, list[str] | str]:
        """The validation patterns for tokens in templates."""
        if self._tokens is None:
            self._tokens = _load_config_file("tokens.yaml")
        return deepcopy(self._tokens)

    def _validate_token(self, key: str, value: int | str):
        """Ensure the given value match the requirements for the token."""
        try:
            pattern = self.tokens[key]
        except KeyError:
            logger.info("'%s' token has no validation requirements", key)
            return

        if isinstance(pattern, list):
            if value in pattern:
                return
            raise ValueError(
                f"'{key}' token value '{value}' isn't a valid value {pattern}",
            )

        match = re.fullmatch(pattern=pattern, string=str(value))
        if not match:
            raise ValueError(
                f"'{key}' token value '{value}' doesn't match regex pattern {pattern}",
            )

    def iterate(
        self,
        template: str,
        /,
        **tokens,
    ) -> Generator[Tuple[UPath, dict[str, str]]]:
        """Find and yield existing instances of the given template."""
        try:
            path = self.templates[template]
        except KeyError as e:
            msg = f"No template named '{template}'"
            logger.warning(msg)
            raise ValueError(msg) from e

        tokens = deepcopy(tokens)
        for key in _get_tokens(path):
            pattern = self.tokens.get(key, "\\.+")
            if isinstance(pattern, list):
                pattern = "|".join(pattern)

            tokens.setdefault(key, f"(?P<{key}>{pattern})")

        yield from _recursive_match(root=self.store, parts=path.split("/"), **tokens)

    def resolve(self, template: str, /, **tokens) -> str:
        """Validate and resolve template using the given tokens."""
        try:
            path = self.templates[template]
        except KeyError as e:
            msg = f"No template named '{template}'"
            logger.warning(msg)
            raise ValueError(msg) from e

        for key, value in tokens.items():
            self._validate_token(key, value)

        try:
            return path.format(**tokens)
        except KeyError as e:
            msg = f"Template {template} missing required tokens {path}"
            logger.warning(msg)
            raise KeyError(msg) from e


def _get_tokens(value: str) -> set[str]:
    """Get the required token keys for the given template."""
    return {key for _, key, _, _ in string.Formatter().parse(value) if key is not None}


def _load_config_file(name: str) -> dict:
    """The named file from the configuration directory."""
    path = os.getenv(_STAGE_CONFIG)
    if path:
        config = str(UPath(path) / name)
    else:
        config = str(importlib.resources.files(_DEFAULT_CONFIG).joinpath(name))

    return OmegaConf.to_container(OmegaConf.load(config), resolve=True)  # pyright: ignore[reportReturnType]


def _recursive_match(
    root: UPath,
    parts: list[str],
    **tokens,
) -> Generator[Tuple[UPath, dict[str, str]]]:
    """Recursively iterate through directories to find existing matches."""
    if not root.is_dir():
        return

    pattern, *parts = parts
    pattern = pattern.format(**tokens)
    for child in sorted(root.iterdir()):
        match = re.fullmatch(pattern=pattern, string=child.name)

        if not match:
            continue

        combined = {**tokens, **match.groupdict()}

        if not parts:
            yield child, combined
            continue

        yield from _recursive_match(root=child, parts=parts, **combined)
