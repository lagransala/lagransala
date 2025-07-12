from pydantic import BaseModel


class ContentScraper(BaseModel):
    venue_slug: str
    main_selector: str | None
