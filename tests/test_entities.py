from pathlib import Path

import pytest

from stage.assets import Asset
from stage.entities import Entity
from stage.resolver import Resolver


class DummyEntity(Entity):
    _template = "asset"

    def __init__(self, resolver: Resolver | None = None):
        self._tokens = {"kind": "character", "name": "hero_01"}
        super().__init__(resolver=resolver)


class MissingTemplateEntity(Entity):
    pass


@pytest.fixture
def resolver(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Resolver:
    monkeypatch.setenv("STAGE_STORE", str(tmp_path / "store"))
    return Resolver()


def test_entity_requires_associated_template() -> None:
    with pytest.raises(NotImplementedError):
        MissingTemplateEntity()


def test_entity_resolves_id_path_and_repr(resolver: Resolver, tmp_path: Path) -> None:
    entity = DummyEntity(resolver=resolver)

    assert entity.id == "character/hero_01"
    assert entity.tokens == {"kind": "character", "name": "hero_01"}
    assert entity._path == tmp_path / "store" / "character" / "hero_01"
    assert "DummyEntity" in repr(entity)
    assert entity.id in repr(entity)


def test_entity_exists_reflects_filesystem_state(resolver: Resolver) -> None:
    entity = DummyEntity(resolver=resolver)

    assert entity.exists is False

    entity._path.mkdir(parents=True)

    assert entity.exists is True


def test_entity_find_returns_matching_assets(resolver: Resolver) -> None:
    Asset(kind="character", name="hero_01", resolver=resolver).create()
    Asset(kind="character", name="hero_02", resolver=resolver).create()
    Asset(kind="prop", name="chair", resolver=resolver).create()

    found = list(Asset.find(resolver=resolver, kind="character"))

    assert [asset.id for asset in found] == [
        "character/hero_01",
        "character/hero_02",
    ]
