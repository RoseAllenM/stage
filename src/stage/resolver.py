import logging
import os
import re
import tempfile
from importlib.resources import files

from omegaconf import OmegaConf
from upath import UPath

logger = logging.getLogger(__name__)

_CONFIG = "stage._config"
_STAGE_ROOT = "STAGE_ROOT"


class Resolver:
    """Asset version validator and resolver."""

    def __init__(self) -> None:
        self._root = None
        self._templates = None
        self._tokens = None

    @property
    def root(self) -> UPath:
        """The root directory of all other template paths."""
        if self._root is None:
            root = os.getenv(_STAGE_ROOT)
            if root:
                self._root = UPath(root)
            else:
                self._root = UPath(tempfile.gettempdir()) / "stage"
                logger.warning(
                    "'%s' environment variable is NOT defined, using %s",
                    _STAGE_ROOT,
                    self._root.as_posix(),
                )

        return self._root

    @property
    def templates(self) -> dict[str, str]:
        """All named tokenized locations."""
        if self._templates is None:
            self._templates = OmegaConf.to_container(
                OmegaConf.load(str(files(_CONFIG).joinpath("templates.yaml"))),
                resolve=True,
            )
        return self._templates  # pyright: ignore[reportReturnType]

    @property
    def tokens(self) -> dict[str, list[str] | str]:
        """The validation patterns for tokens in templates."""
        if self._tokens is None:
            self._tokens = OmegaConf.to_container(
                OmegaConf.load(str(files(_CONFIG).joinpath("tokens.yaml"))),
                resolve=True,
            )
        return self._tokens  # pyright: ignore[reportReturnType]

    def _validate_token(self, key: str, value: str):
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

        match = re.fullmatch(pattern=pattern, string=value)
        if not match:
            raise ValueError(
                f"'{key}' token value '{value}' doesn't match regex pattern {pattern}",
            )

    def create(self, template: str, /, exist_ok: bool = False, **tokens) -> UPath:
        """Validate and create the template using the given tokens"""
        path = self.resolve(template, **tokens)

        (path.parent if path.suffix else path).mkdir(parents=True, exist_ok=exist_ok)

        return path

    def resolve(self, template: str, /, **tokens) -> UPath:
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
            return self.root / path.format(**tokens)
        except KeyError as e:
            msg = f"Template {template} missing required tokens {path}"
            logger.warning(msg)
            raise KeyError(msg) from e
