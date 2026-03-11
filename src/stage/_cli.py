import json
import logging

import click

from stage.assets import Asset
from stage.resolver import Resolver
from stage.versions import Version

logger = logging.getLogger(__name__)


def _parse_asset_json(
    file_path: click.Path,
) -> dict[str, dict[str, dict[str, dict[int, bool]]]]:
    """Organize the contents of the .json file."""
    with open(str(file_path)) as f:
        entries = json.load(f)

    asset_types = {}
    for i, entry in enumerate(entries):
        try:
            assets = asset_types.setdefault(entry["asset"]["type"], {})
        except KeyError:
            logger.warning("Entry %d doesn't specify an asset type %s", i, entry)
            continue

        try:
            departments = assets.setdefault(entry["asset"]["name"], {})
        except KeyError:
            logger.warning("Entry %d doesn't specify an asset name %s", i, entry)
            continue

        try:
            versions = departments.setdefault(entry["department"], {})
        except KeyError:
            logger.warning("Entry %d doesn't specify a department %s", i, entry)
            continue

        try:
            version = entry["version"]
        except KeyError:
            logger.warning("Entry %d doesn't specify a version number %s", i, entry)
            continue

        if not isinstance(version, int) or version < 1:
            logger.warning("Entry %d version isn't a positive integer %s", i, entry)
            continue

        if version in versions:
            logger.warning("Entry %d duplicates a previous entry")
            continue

        try:
            if entry["status"].lower() == "active":
                active = True
            elif entry["status"].lower() == "inactive":
                active = False
            else:
                raise KeyError()
        except KeyError:
            logger.warning("Entry %d doesn't specify a valid status %s", i, entry)
            continue

        versions[version] = active

    return asset_types


@click.group()
@click.option("--info", "info", is_flag=True, help="Set logging level to INFO")
@click.option("--debug", "debug", is_flag=True, help="Set logging level to DEBUG")
@click.pass_context
def cli(ctx, info: bool, debug: bool):
    """Stage: Asset Validation & Registration Service CLI"""
    if info and debug:
        raise click.UsageError("--info and --debug are mutually exclusive.")

    ctx.ensure_object(dict)

    logging_level = logging.WARNING
    if info:
        logging_level = logging.INFO
    elif debug:
        logging_level = logging.DEBUG

    logging.basicConfig(level=logging_level)

    ctx.obj["logging_level"] = logging_level

    ctx.obj["resolver"] = Resolver()


@cli.command()
@click.argument("asset_name")
@click.argument("asset_type")
@click.pass_context
def add(ctx, asset_name, asset_type):
    """Add an asset from a JSON file."""
    asset = Asset(kind=asset_type, name=asset_name, resolver=ctx.obj["resolver"])
    try:
        asset.create()
    except Exception as e:
        logger.warning(e)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def load(ctx, file_path):
    """Load assets from a JSON file."""
    _resolver = ctx.obj["resolver"]

    for kind, assets in sorted(_parse_asset_json(file_path).items()):
        for name, departments in sorted(assets.items()):
            asset = None

            loaded = [""]
            for department, versions in sorted(departments.items()):
                _next = 1
                skipped = []
                for number, active in sorted(versions.items()):
                    if number != _next:
                        skipped.append(number)
                        continue

                    _next += 1
                    if asset is None:
                        asset = Asset(kind=kind, name=name, resolver=_resolver)

                    version = Version(
                        asset=asset,
                        department=department,
                        number=number,
                        resolver=_resolver,
                    )
                    version.create(active=active, exist_ok=True)
                    loaded.append(version.id)

                if skipped:
                    logger.warning(
                        "Missing version %d of %s %s for %s, skipping version(s) %s",
                        _next,
                        kind,
                        name,
                        department,
                        skipped,
                    )

            if asset and loaded:
                print(f"\nLoaded Asset {asset.id} Versions{'\n\t'.join(loaded)}")


def main():
    """Entry point for the CLI."""
    cli(obj={})
