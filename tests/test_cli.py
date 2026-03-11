import json
import logging
from pathlib import Path

from click.testing import CliRunner

from stage._cli import _parse_asset_json, cli


def test_parse_asset_json_groups_valid_entries_and_skips_invalid_ones(
    tmp_path: Path,
    caplog,
) -> None:
    payload = [
        {
            "asset": {"type": "character", "name": "hero_01"},
            "department": "animation",
            "version": 1,
            "status": "active",
        },
        {
            "asset": {"type": "character", "name": "hero_01"},
            "department": "animation",
            "version": 2,
            "status": "inactive",
        },
        {
            "asset": {"name": "hero_01"},
            "department": "animation",
            "version": 3,
            "status": "active",
        },
        {
            "asset": {"type": "character", "name": "hero_01"},
            "department": "animation",
            "version": 2,
            "status": "active",
        },
        {
            "asset": {"type": "character", "name": "hero_01"},
            "department": "animation",
            "version": 0,
            "status": "active",
        },
        {
            "asset": {"type": "character", "name": "hero_01"},
            "department": "animation",
            "version": 4,
            "status": "pending",
        },
    ]
    file_path = tmp_path / "assets.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        result = _parse_asset_json(file_path)

    assert result == {
        "character": {"hero_01": {"animation": {1: True, 2: False}}},
    }
    assert "doesn't specify an asset type" in caplog.text
    assert "duplicates a previous entry" in caplog.text
    assert "version isn't a positive integer" in caplog.text
    assert "doesn't specify a valid status" in caplog.text


def test_load_command_creates_only_contiguous_versions(
    monkeypatch,
    tmp_path: Path,
) -> None:
    store = tmp_path / "store"
    monkeypatch.setenv("STAGE_STORE", str(store))

    payload = [
        {
            "asset": {"type": "character", "name": "hero_01"},
            "department": "animation",
            "version": 1,
            "status": "active",
        },
        {
            "asset": {"type": "character", "name": "hero_01"},
            "department": "animation",
            "version": 3,
            "status": "inactive",
        },
    ]
    file_path = tmp_path / "assets.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["load", str(file_path)])

    assert result.exit_code == 0, result.output
    assert "Loaded Asset character/hero_01" in result.output
    assert (store / "character" / "hero_01" / "animation" / "1.json").exists()
    assert not (store / "character" / "hero_01" / "animation" / "3.json").exists()


def test_cli_rejects_info_and_debug_flags_together(tmp_path: Path) -> None:
    file_path = tmp_path / "assets.json"
    file_path.write_text("[]", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(cli, ["--info", "--debug", "load", str(file_path)])

    assert result.exit_code != 0
    assert "mutually exclusive" in result.output
