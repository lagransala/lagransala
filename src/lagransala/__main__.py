import asyncio
import logging

import typer
from dotenv import load_dotenv

from lagransala.applications import event_discovery as event_discovery_app

load_dotenv()

app = typer.Typer()


@app.callback()
def callback(debug: bool = typer.Option(False, "--debug")):
    """lagransala CLI"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("lagransala").setLevel(log_level)


@app.command("event-discovery")
def event_discovery():
    """Run the event discovery application."""
    asyncio.run(event_discovery_app())


if __name__ == "__main__":
    app()
