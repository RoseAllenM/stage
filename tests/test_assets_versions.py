import json
from pathlib import Path

import pytest

from stage.assets import Asset
from stage.resolver import Resolver
from stage.versions import Version


@pytest.fixture
def resolver(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Resolver:
    monkeypatch.setenv("STAGE_STORE", str(tmp_path / "store"))
    return Resolver()


@pytest.fixture
def asset(resolver: Resolver) -> Asset:
    return Asset(kind="character", name="hero_01", resolver=resolver)


def test_asset_create_makes_directory(asset: Asset) -> None:
    asset.create()

    assert asset._path.is_dir()


def test_asset_new_version_creates_version_file(asset: Asset) -> None:
    version = asset.new_version(department="animation", number=1, active=True)

    assert isinstance(version, Version)
    assert version.asset is asset
    assert version.id == "character/hero_01/animation/1.json"
    assert version.exists
    assert json.loads(version._path.read_text()) == {"active": True}


def test_version_create_raises_when_file_exists(asset: Asset) -> None:
    version = Version(asset=asset, department="animation", number=1)
    version.create(active=False)

    with pytest.raises(FileExistsError):
        version.create(active=True)
