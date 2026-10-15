# La Gran Sala

[![Actions Status](https://github.com/lagransala/lagransala/workflows/test/badge.svg)](https://github.com/lagransala/lagransala/actions)
[![Docs](https://github.com/lagransala/lagransala/workflows/docs/badge.svg)](https://lagransala.github.io/lagransala/)

La Gran Sala discovers and catalogs cultural events (cinema, talks, live music) from
venues in Madrid. It scrapes each venue's programme, extracts structured events with
an LLM, stores them in SQLite and serves them in a small web application.

## Quick start

```bash
uv sync --dev
cp .env.template .env             # add your API keys
uv run lagransala event-discovery # scrape venues and fill lagransala.db
uv run lagransala web             # serve http://localhost:8000
```

## Documentation

Architecture, domain models, the event discovery pipeline and the development guide
are in the [documentation](https://lagransala.github.io/lagransala/). To read it
locally:

```bash
uv sync --group docs
uv run properdocs serve
```
