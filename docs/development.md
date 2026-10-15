# Development

## Environment

The project uses [uv](https://docs.astral.sh/uv/) for Python packages and Python
3.13. The Nix flake provides the interpreter, `uv` and the shared libraries that
some prebuilt wheels need (for example `libstdc++` for `litellm`).

```bash
nix develop        # or let direnv load it: add `use flake` to .envrc
uv sync --dev
cp .env.template .env
```

`.env` is loaded at startup. It needs the keys of the services in use:
`GEMINI_API_KEY`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and `LANGFUSE_HOST`,
plus `GROQ_API_KEY` for the default Groq extractor.

## Commands

```bash
uv run lagransala --help          # CLI
uv run lagransala event-discovery # event discovery pipeline
uv run lagransala web --watch     # web application with reload

uv run pytest                     # tests with coverage
uv run ruff format                # format
uv run ruff check --fix           # lint (includes import sorting)
uv run ty check                   # type check
uv run lint-imports               # architecture contracts
uv run pre-commit run --all-files # everything the hooks run
```

## Code quality

- **[Ruff](https://docs.astral.sh/ruff/)** formats and lints. Besides the default
  rules it enables isort, pyupgrade, bugbear, simplify, comprehensions, pie,
  ruff-specific, async, pytest-style, pathlib and type-checking rules. The line
  length is 88 characters.
- **[ty](https://docs.astral.sh/ty/)** type checks the project. Warnings fail the
  check.
- **[Import Linter](https://import-linter.readthedocs.io/)** enforces the
  [architecture](architecture.md).
- Async callables end in `_async` when applicable, repositories end in `Repo` and
  services in `Service` or `Extractor`.

## Git workflow

Commits follow [Conventional Commits](https://www.conventionalcommits.org/), checked
by [Commitizen](https://commitizen-tools.github.io/commitizen/), for example
`feat(scraper): add pagination crawler`. Install the hooks once:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

The pre-commit hooks run ruff (check and format) and ty, and the commit-msg hook
validates the message.

Releases are cut with Commitizen, which bumps the version from the commit history
and updates `CHANGELOG.md`. `feat` bumps the minor version and `fix`, `refactor` and
`perf` the patch version. The changelog also lists `build`, `ci` and `docs` commits,
which do not change the version.

```bash
uv run cz bump
```

## Tests

Tests mirror the package structure under `tests/`. Async tests use `pytest-asyncio`
with a session-scoped event loop. HTTP code is tested against a local server started
with `aiohttp.test_utils.TestServer`, so no network access is needed.

## Documentation

The documentation is built with [ProperDocs](https://properdocs.org/), a maintained
continuation of MkDocs 1.x, and the Material theme. Its dependencies are in a
separate `docs` group and the configuration is in `properdocs.yml`.

```bash
uv sync --group docs
uv run properdocs serve           # live preview at http://localhost:8000
uv run properdocs build --strict  # build into site/, failing on warnings
```

The API reference is generated from the docstrings by `mkdocstrings`. Design notes
under `docs/superpowers/` are not part of the site.

## Continuous integration

Two GitHub Actions workflows live in `.github/workflows/`:

- `test.yml` runs the tests on pushes and pull requests to `main`.
- `docs.yml` builds the documentation and publishes it to GitHub Pages when `main`
  changes.

## Docker

A `Dockerfile` and a `./run` wrapper are available to work inside a container:

```bash
./run build                # build the image
./run uv run pytest        # run a command in the container
```
