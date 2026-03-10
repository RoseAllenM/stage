# Stage

**Manage assets and their version.**

[Stage-Py](https://github.com/RoseAllenM/stage-py) is the python API for integrating with this service.

## Development

This package using the following
- [MyPy](https://www.mypy-lang.org/) - static type checking
- [Pydantic](https://docs.pydantic.dev/latest/) - runtime type validation
- [PyTest](https://docs.pytest.org/en/stable/) - testing framework
- [Ruff](https://docs.astral.sh/ruff/) - linter and code formating
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
4. Build and install the package in editable mode, and install the extra dev dependencies.
   ```shell
   uv pip install --editable ".[dev]"
   ```
5. Install [pre-commit](https://pre-commit.com/) hooks.
   ```shell
   pre-commit install
   ```
