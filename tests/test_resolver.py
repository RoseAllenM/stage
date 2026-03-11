import logging

import pytest
from upath import UPath

from stage.resolver import Resolver


@pytest.fixture
def resolver() -> Resolver:
    return Resolver()


def test_templates_load_from_packaged_config(resolver: Resolver) -> None:
    assert resolver.templates == {
        "asset": "{kind}/{name}",
        "version": "{kind}/{name}/{department}/{version}.json",
    }


def test_tokens_load_from_packaged_config(resolver: Resolver) -> None:
    assert resolver.tokens == {
        "department": [
            "animation",
            "cfx",
            "fx",
            "modeling",
            "rigging",
            "texturing",
        ],
        "kind": [
            "character",
            "dressing",
            "environment",
            "fx",
            "prop",
            "set",
            "vehicle",
        ],
        "name": "[0-9A-z_]+",
        "version": r"\d+",
    }


def test_resolve_returns_upath_for_asset_template(resolver: Resolver) -> None:
    path = resolver.resolve("asset", kind="character", name="hero_01")

    assert path == UPath("character/hero_01")


def test_resolve_returns_upath_for_version_template(resolver: Resolver) -> None:
    path = resolver.resolve(
        "version",
        kind="character",
        name="hero_01",
        department="animation",
        version="001",
    )

    assert path == UPath("character/hero_01/animation/001.json")


def test_resolve_raises_for_unknown_template(resolver: Resolver) -> None:
    with pytest.raises(ValueError):
        resolver.resolve("missing")


def test_resolve_raises_for_invalid_list_token_value(resolver: Resolver) -> None:
    with pytest.raises(ValueError):
        resolver.resolve(
            "version",
            kind="character",
            name="hero_01",
            department="lighting",
            version="001",
        )


def test_resolve_raises_for_invalid_regex_token_value(resolver: Resolver) -> None:
    with pytest.raises(ValueError):
        resolver.resolve(
            "version",
            kind="character",
            name="hero_01",
            department="animation",
            version="v001",
        )


def test_resolve_raises_when_required_tokens_are_missing(
    resolver: Resolver,
) -> None:
    with pytest.raises(KeyError):
        resolver.resolve("version", kind="character", name="hero_01")


def test_resolve_allows_extra_tokens_without_validation_rules(
    resolver: Resolver,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        path = resolver.resolve(
            "asset",
            kind="character",
            name="hero_01",
            episode="101",
        )

    assert path == UPath("character/hero_01")
    assert "'episode' token has no validation requirements" in caplog.text
