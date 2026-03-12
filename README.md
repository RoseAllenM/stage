# Stage

**Manage assets and their versions.**

`stage` is a lightweight asset validation and registration service built around a small Python API and a CLI. 
- validates asset identifiers and version metadata
- stores records on disk
- supports loading assets from JSON while skipping invalid entries without halting the entire run

## What it does

Stage models two core concepts:

- **Asset**: identified by `kind` and `name`
- **Version**: identified by `asset`, `department`, and `number`

The service validates values using token rules and path templates defined in YAML configuration, then stores assets and versions in a filesystem-backed hierarchy.

Default examples:

- Asset path: `character/hero_01`
- Version path: `character/hero_01/animation/1.json`

## Installation

### Runtime install

```shell
uv pip install .
```

### Development install

```shell
uv pip install --editable ".[dev]"
```

## Configuration

Stage uses two optional environment variables:

- `STAGE_STORE`: root directory where assets and versions are stored
- `STAGE_CONFIG`: directory containing custom `templates.yaml` and `tokens.yaml`

If `STAGE_STORE` is not set, Stage defaults to a temporary directory under your system temp path.

### Example

```shell
export STAGE_STORE=/path/to/stage-store
```

## User Guide

### CLI overview

After installation, the package exposes the `stage` command.

```shell
stage --help
```

You can increase logging verbosity with:

```shell
stage --info ...
stage --debug ...
```

> `--info` and `--debug` are mutually exclusive.

### Asset commands

#### Add an asset

```shell
stage add hero_01 character
```

Example output:

```text
Created Asset character/hero_01
```

#### Get an asset

```shell
stage get hero_01 character
```

Example output:

```text
Asset character/hero_01 found
```

If the asset does not exist:

```text
Asset character/hero_01 missing
```

#### List assets

```shell
stage list
stage list --asset-type character
stage list --asset-name hero_01
```

If matches are found, Stage prints each asset id. Otherwise:

```text
No Assets found
```

### Version commands

#### Add a version

```shell
stage versions add hero_01 character animation 1 active
```

Example output:

```text
Created Version character/hero_01/animation/1.json
```

Valid status values are:

- `active`
- `inactive`

#### Get a version

```shell
stage versions get hero_01 character animation 1
```

Example output:

```text
Version character/hero_01/animation/1.json found
```

If the version does not exist:

```text
No Version found
```

#### List versions

```shell
stage versions list hero_01 character
stage versions list hero_01 character --department animation
stage versions list hero_01 character --status active
stage versions list hero_01 character --version 2
```

If no versions match:

```text
No Versions found
```

### Bulk load from JSON

```shell
stage load /path/to/assets.json
```

The loader:

- parses a list of asset/version entries from JSON
- skips invalid entries while continuing the run
- stores contiguous version sequences
- warns when entries are malformed or versions are missing/skipped

If nothing valid is loaded:

```text
No Assets loaded
```

### Sample JSON shape

```json
[
  {
    "asset": {
      "type": "character",
      "name": "hero_01"
    },
    "department": "animation",
    "version": 1,
    "status": "active"
  }
]
```

## Developer Technical Overview

### Architecture

The codebase is intentionally small and split into focused modules:

- `src/stage/resolver.py`
  - loads YAML configuration
  - validates token values
  - resolves ids into filesystem paths
  - iterates existing assets/versions from disk using template matching
- `src/stage/entities.py`
  - base entity abstraction
  - shared id/path/existence behavior
  - generic discovery via `find(...)`
- `src/stage/assets.py`
  - asset domain object
  - asset creation and version spawning
- `src/stage/versions.py`
  - version domain object
  - payload loading, active-state inspection, and filtered lookup
- `src/stage/_cli.py`
  - Click-based user interface
  - command orchestration and user-facing messaging

### Storage model

Stage currently uses a **filesystem-backed persistence model**:

- assets are directories
- versions are JSON files below their asset directory

This keeps the implementation lightweight while preserving a clean abstraction around ids, discovery, and validation.

### Validation model

Validation is driven by two config files in `src/stage/_config/`:

- `templates.yaml`: maps logical object types to tokenized path templates
- `tokens.yaml`: defines accepted token values as lists or regex patterns

This makes the system easy to extend without rewriting path logic everywhere.

### Error handling approach

The service is designed to fail gracefully where appropriate:

- CLI commands surface user-facing failures via `click.ClickException`
- JSON bulk load skips malformed entries instead of aborting the entire import
- missing or invalid filter/status values produce explicit messages

### Testing

The test suite covers:

- resolver config loading, token validation, and path iteration
- entity discovery and filesystem existence checks
- asset and version creation rules
- CLI success, empty-result, and error-message behavior

Run the tests with:

```shell
pytest -q
```

## Development

This package uses the following tooling:

- [MyPy](https://www.mypy-lang.org/) - static type checking
- [PyTest](https://docs.pytest.org/en/stable/) - testing framework
- [pytest-cov](https://pytest-cov.readthedocs.io/) - coverage reporting
- [Ruff](https://docs.astral.sh/ruff/) - linting and formatting
- [Semantic Versioning](https://semver.org/) - `Major.Minor.Patch`
- [UV](https://docs.astral.sh/uv/) - environment management

### Setting up a development environment

1. Clone this repo and `cd` into it.
2. Create a virtual environment.
   ```shell
   uv venv
   ```
3. Activate the virtual environment.
   ```shell
   # Windows
   .venv\Scripts\Activate.ps1

   # Linux
   source .venv/bin/activate
   ```
4. Install the package in editable mode with development dependencies.
   ```shell
   uv pip install --editable ".[dev]"
   ```
5. Install [pre-commit](https://pre-commit.com/) hooks.
   ```shell
   pre-commit install
   ```

### Useful developer commands

```shell
pytest -q
ruff check .
ruff format .
mypy src
```

## Future improvements

Potential next steps include:

- a higher-level public Python API module for application consumers
- storage backend abstraction beyond filesystem persistence
- richer structured logging for load/validation events
- REST API support
- CI automation for linting, typing, and tests
