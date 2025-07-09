import asyncio

from dotenv import load_dotenv

from lagransala.applications import today_events_message

load_dotenv()


def main():
    asyncio.run(today_events_message())


if __name__ == "__main__":
    main()
