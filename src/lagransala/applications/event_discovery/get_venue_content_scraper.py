from lagransala.schedule.domain import Venue
from lagransala.scraper.domain import ContentScraper, ContentScraperRepo


def get_venue_content_scraper(repo: ContentScraperRepo, venue: Venue) -> ContentScraper:
    content_scraper = repo.get(venue.slug)
    if content_scraper is None:
        raise ValueError(f"Pagination with venue_slug {venue.slug} not found")
    return content_scraper
