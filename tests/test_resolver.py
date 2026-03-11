import logging
import tempfile

import pytest

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

    assert path == "character/hero_01"


def test_resolve_returns_upath_for_version_template(resolver: Resolver) -> None:
    path = resolver.resolve(
        "version",
        kind="character",
        name="hero_01",
        department="animation",
        version="001",
    )

    assert path == "character/hero_01/animation/001.json"


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

    assert path == "character/hero_01"


def test_store_uses_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("STAGE_STORE", str(tmp_path / "store"))

    resolver = Resolver()

    assert resolver.store == tmp_path / "store"


def test_store_defaults_to_temp_directory_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.delenv("STAGE_STORE", raising=False)

    resolver = Resolver()

    with caplog.at_level(logging.WARNING):
        store = resolver.store

    assert store == Resolver().store.__class__(tempfile.gettempdir()) / "stage"
    assert "STAGE_STORE" in caplog.text


def test_templates_and_tokens_can_load_from_stage_config_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "templates.yaml").write_text(
        'asset: "custom/{kind}/{name}"\n',
        encoding="utf-8",
    )
    (config_dir / "tokens.yaml").write_text(
        "kind:\n  - prop\nname: '[a-z]+'\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("STAGE_CONFIG", str(config_dir))

    resolver = Resolver()

    assert resolver.templates == {"asset": "custom/{kind}/{name}"}
    assert resolver.tokens == {"kind": ["prop"], "name": "[a-z]+"}
