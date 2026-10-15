# AGENTS.md

This file provides guidance to AI coding agents when working with code in this repository.

## Project Overview

La Gran Sala discovers and catalogs cultural events (cinema, talks, live music) from venues in Madrid. It scrapes each venue's programme, extracts structured events with an LLM, stores them in SQLite and serves them in a small FastAPI app. The project follows clean architecture principles with bounded contexts and layered architecture.

**Tech Stack:** Python 3.13, FastAPI, SQLModel/SQLite, Pydantic, aiohttp, BeautifulSoup4, Typer, Groq (default LLM provider), Langfuse, uv, ruff, ty, ProperDocs (documentation).

Full documentation lives in `docs/` (published with GitHub Pages). Keep it in sync when behavior changes.

## Environment

- Nix flake dev shell (`nix develop`, or direnv with `use flake` in `.envrc`) provides Python 3.13, `uv` and the shared libraries some wheels need (for example `libstdc++` for `litellm`). Python packages are managed only by `uv`.
- Copy `.env.template` to `.env`. It needs `GROQ_API_KEY` for the default extractor, plus `GEMINI_API_KEY` and `LANGFUSE_*` for the other integrations (`GROQ_API_KEY` is not in the template yet).

## Development Commands

```bash
# Setup
uv sync --dev
cp .env.template .env  # Edit .env with API keys

# Run applications
uv run lagransala --help                    # CLI help
uv run lagransala event-discovery           # Event discovery pipeline
uv run lagransala web --watch               # FastAPI server with hot-reload

# Testing
uv run pytest                               # Run tests with coverage
uv run pytest tests/schedule/domain/        # Run specific test file
uv run pytest -k "test_venue"               # Run tests matching pattern

# Code quality
uv run ruff format                          # Format code
uv run ruff check --fix                     # Lint (includes import sorting)
uv run ty check                             # Type check (warnings fail)
uv run lint-imports                         # Architecture validation
uv run pre-commit run --all-files           # Run all pre-commit hooks

# Documentation
uv sync --group docs
uv run properdocs serve                     # Live preview
uv run properdocs build --strict            # Build into site/, fail on warnings

# Maintenance
uv run python scripts/clear_cache.py        # Show and clear the .cache/ file caches

# Docker workflow
./run build                                 # Build Docker image
./run                                       # Enter container
./run uv run pytest                         # Run tests in container
```

## Architecture

### Bounded Contexts

Four main bounded contexts organized under `src/lagransala/`:

1. **`schedule/`** - Venues and events (domain models, venue seeding)
2. **`scraper/`** - Reading venue pages (pagination strategies, content scrapers, a generic same-host crawler)
3. **`extractor/`** - LLM-based event extraction from page content
4. **`shared/`** - Cross-cutting utilities (fetcher, caching, URL handling, markdown)

Entry points:
- **`__main__.py`** - CLI entry point (Typer-based)
- **`applications/event_discovery/`** - Event discovery pipeline
- **`applications/web/`** - FastAPI web application

### Layered Architecture

Each bounded context follows clean architecture with three layers:

```
context/
├── domain/          # Entities, value objects, Protocol interfaces
├── application/     # Use cases, application services (depends on domain)
└── infrastructure/  # Technical implementations (depends on domain + application)
```

**Dependencies flow:** infrastructure → application → domain → shared

### Import Rules

- Use **relative imports** within a bounded context
- Use **absolute imports** for cross-context dependencies
- Import at the **layer package level** via `__init__.py` (which defines `__all__`)
- Bounded contexts are independent except through `shared`
- Applications/entrypoints can depend on any context

Enforced by four Import Linter contracts in `pyproject.toml` (layers for `schedule`, `scraper` and `extractor`, and independence between the three). Run `uv run lint-imports`; it is not part of the pytest suite.

## Domain Models

Persisted (`schedule/domain`), as SQLModel tables with `UUID` primary keys:

- **`Venue`**: `name`, unique `slug`, `description`, `address`, `location_latitude`, `location_longitude`, `website`, `schedule_url`, `events`.
- **`Event`**: `venue_id`, `url` (source page), `title`, `author`, `description`, `duration`, `schedule`.
- **`EventDateTime`**: `event_id` and a naive `datetime` (venue-local wall-clock time, annotated `NaiveDatetime`).

Extraction (`extractor/domain`, plain Pydantic):

- **`EventData`**: one extracted event, including `tags`, `category` and `price`. These three are **not persisted** because `Event` has no columns for them.
- **`EventExtraction`** / **`SourcedEventExtraction`**: events found in one page, with `EmptyReason`, model, source URL and datetime.
- **`SourcedContent`** / **`ContentFormat`**: fetched page content (`markdown`, `html` or `empty`).

Scraping (`scraper/domain`): **`Pagination`** (`none`, `simple`, `day`, `month`) and **`ContentScraper`** (`venue_slug`, optional CSS `main_selector`). More detail in `docs/domain-models.md`.

## Configuration Files

- **`.env.template`** - Environment variables (GEMINI_API_KEY, LANGFUSE_*_KEY, LANGFUSE_HOST)
- **`seeds/venues.json`** - Venue definitions (seeded only when the venue table is empty)
- **`seeds/content_scrapers.json`** - Scraping configuration per venue
- **`seeds/paginations.json`** - Pagination strategy per venue
- **`pyproject.toml`** - Dependencies, ruff, ty, pytest, Import Linter and Commitizen configuration
- **`properdocs.yml`** - Documentation site configuration

## Event Discovery Pipeline

`applications/event_discovery/`:

1. **Seed venues** from `seeds/venues.json` if the table is empty
2. **For each venue**, load its `Pagination` and `ContentScraper` (a missing entry raises `ValueError` and stops the run)
3. **Fetch the listing pages** from `pagination.urls()` and collect the links matching `element_url_pattern`
4. **Fetch every event page** and convert the HTML to markdown
5. **Extract events** with `GroqEventExtractor` (`openai/gpt-oss-120b`). The Gemini, Instructor and LiteLLM extractors exist but are not wired in
6. **Store events**. Every run first **deletes all existing events**, so the database only holds the last run

## Coding Conventions

- **4-space indentation** with type annotations on public APIs
- **88-character line length** (ruff formatter)
- Ruff rule families: E, W, F, I, UP, B, SIM, C4, PIE, RUF, ASYNC, PT, PTH, TC
- Generics use PEP 695 type parameters (`class Foo[T]:`, `def f[T](...)`)
- **Protocol classes** use `Protocol` base class for dependency injection
- **Repository classes** follow `*Repo` naming pattern
- **Extractor classes** follow `*Extractor` naming
- **Descriptive module names** aligned with domain layers

## Testing

- Tests mirror package structure in `tests/`
- Use `pytest-asyncio` for async tests (fixture loop scope: session)
- Use `aiohttp.test_utils.TestServer` (local server) for HTTP tests
- Coverage reports under `htmlcov/`

## Git Workflow

- Work happens on `develop`. To release: `uv run cz bump` on `develop`, then fast-forward `main` to it and push both branches and the tag (`vX.Y.Z`). Do not squash: the changelog is generated from the commits
- **Conventional Commits** enforced by Commitizen (e.g., `feat(scraper): add pagination crawler`). Types that appear in `CHANGELOG.md`: feat, fix, refactor, perf, build, ci, docs. `feat` bumps the minor version, `fix`/`refactor`/`perf` the patch version
- **Pre-commit hooks**: ruff (check + format), ty, commitizen. Install with `uv run pre-commit install --hook-type pre-commit --hook-type commit-msg`
- Pushing to `main` runs the tests and publishes the docs (GitHub Pages)

## Skills

Project skills live in `.claude/skills/` (currently `web-style-changes`, for the Tailwind/Jinja2 web templates).

## Important Notes

- **Database:** SQLite with SQLModel ORM (`lagransala.db` in project root)
- **Caching:** on disk under `.cache/`: HTTP responses (10 min TTL for listing pages, 23 h for event pages), extractions and Groq completions (no TTL)
- **Rate Limiting:** `AsyncLimiter` for AI API calls (30 requests per minute for Groq)
- **Observability:** Langfuse tracing; without keys the client disables itself and logs a warning at startup
- **Async-First:** Entire application uses async/await
- **Design notes:** `docs/superpowers/specs/` holds internal design specs (in Spanish), excluded from the published site
