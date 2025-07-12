from lagransala.schedule.domain import Venue
from lagransala.scraper.domain import Pagination, PaginationRepo


def get_venue_pagination(repo: PaginationRepo, venue: Venue) -> Pagination:
    pagination = repo.get(venue.slug)
    if pagination is None:
        raise ValueError(f"Pagination with venue_slug {venue.slug} not found")
    return pagination
