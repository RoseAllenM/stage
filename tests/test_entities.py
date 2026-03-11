from pathlib import Path

import pytest

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
