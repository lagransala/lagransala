from datetime import datetime, timedelta
from pydantic import HttpUrl

from lagransala.scraper.domain.pagination import Pagination, PaginationType


def pagination_urls(pagination: Pagination) -> list[HttpUrl]:
    match pagination.type:
        case PaginationType.NONE | None:
            return [HttpUrl(pagination.url)]
        case PaginationType.SIMPLE:
            assert pagination.simple_start_from is not None
            assert pagination.limit is not None
            return [
                HttpUrl(pagination.url.format(n=i))
                for i in range(
                    pagination.simple_start_from,
                    pagination.limit + pagination.simple_start_from,
                )
            ]
        case PaginationType.DAY:
            assert pagination.date_format is not None
            assert pagination.limit is not None
            today = datetime.now().replace(minute=0, hour=0, second=0)
            result: list[HttpUrl] = []
            for i in range(0, pagination.limit):
                date = today + timedelta(days=i)
                url = HttpUrl(
                    pagination.url.format(date=date.strftime(pagination.date_format))
                )
                result.append(url)
            return result
        case PaginationType.MONTH:
            assert pagination.date_format is not None
            assert pagination.limit is not None
            month_start = datetime.now().replace(day=1, minute=0, hour=0, second=0)
            current_month = month_start.month
            result: list[HttpUrl] = []
            for i in range(0, pagination.limit):
                month = month_start.replace(month=current_month + i)
                url = HttpUrl(
                    pagination.url.format(date=month.strftime(pagination.date_format))
                )
                result.append(url)
            return result
