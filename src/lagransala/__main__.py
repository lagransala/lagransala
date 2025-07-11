import asyncio
import logging

from dotenv import load_dotenv

from lagransala.applications import today_events_message

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.getLogger("lagransala").setLevel(logging.INFO)


def main():
    asyncio.run(today_events_message())


if __name__ == "__main__":
    main()
