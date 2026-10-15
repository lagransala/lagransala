# Web application

A small read-only FastAPI application that renders the events stored in
`lagransala.db`.

```bash
uv run lagransala web            # http://localhost:8000
uv run lagransala web --watch    # reload when files in applications/web/ change
```

The server listens on `0.0.0.0:8000`.

## Routes

| Route | Shows |
|-------|-------|
| `GET /` | Events of the current month. |
| `GET /{date}` | Events of a month (`YYYY-MM`) or a single day (`YYYY-MM-DD`). Any other format returns `400`. |

Both routes render the same template, `templates/index.html`.

## How it works

- The database is `lagransala.db` in the working directory. If that file does not
  exist, the application falls back to `../../../lagransala.db`, which is relative
  to `applications/web/`.
- A query joins `Event` with its `EventDateTime` rows, keeps those between the start
  and the end of the requested range and loads the venue of each event.
- Events are grouped by day and time for display. Dates are shown in Spanish, for
  example `Lunes 4 de mayo`, through the `format_date_spanish` template function.
  The `url_domain` filter shows the domain of an event's source URL.
- The session is created per request with a FastAPI dependency.

!!! note
    The application only reads data. Events are written by the
    [event discovery](pipeline.md) pipeline.
