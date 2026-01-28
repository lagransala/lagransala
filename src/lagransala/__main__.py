import asyncio
import sys

import typer
import uvicorn
from dotenv import load_dotenv
from loguru import logger

from lagransala.applications import event_discovery as event_discovery_app

load_dotenv()

app = typer.Typer()


@app.callback()
def callback(
    debug: bool = typer.Option(False, "--debug", "-d"),
    doubledebug: bool = typer.Option(False, "--ddebug", "-D"),
):
    """lagransala CLI"""
    logger.remove()
    logger.add(
        sys.stderr, level="TRACE" if doubledebug else ("DEBUG" if debug else "INFO")
    )


@app.command("event-discovery")
def event_discovery():
    """Run the event discovery application."""
    asyncio.run(event_discovery_app())


@app.command("web")
def web(watch: bool = typer.Option(False, "--watch")):
    """Run the web application server."""

    reload_dirs = []
    if watch:
        reload_dirs.append("src/lagransala/applications/web/")

    uvicorn.run(
        "lagransala.applications.web.__main__:app",
        host="0.0.0.0",
        port=8000,
        reload=watch,
        reload_dirs=reload_dirs,
    )


if __name__ == "__main__":
    app()
