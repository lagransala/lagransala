from typing import Iterable
from uuid import uuid4

import pytest
from pydantic import ValidationError

from lagransala.scraper.domain import Pagination


@pytest.fixture()
def valid_pagination_constructor_params() -> list[dict]:
    return [
        {
            "venue_slug": "cinema",
            "type": None,
            "url": "https://cinema.com/films",
            "base_url": "https://cinema.com",
            "element_url_pattern": "/films/\\d+",
        },
        {
            "venue_slug": "cinema2",
            "type": "simple",
            "url": "https://cinema.com/films?page={n}",
            "simple_start_from": 0,
            "limit": 10,
            "base_url": "https://cinema.com",
            "element_url_pattern": "/films/\\d+",
        },
        {
            "venue_slug": "cinema3",
            "type": "day",
            "url": "https://cinema.com/films?date={date}",
            "date_format": "%Y-%m-%d",
            "limit": 31,
            "base_url": "https://cinema.com",
            "element_url_pattern": "/films/\\d+",
        },
        {
            "venue_slug": "cinema4",
            "type": "month",
            "url": "https://cinema.com/films?month={month}",
            "date_format": "%Y-%m",
            "limit": 2,
            "base_url": "https://cinema.com",
            "element_url_pattern": "/films/\\d+",
        },
    ]


@pytest.fixture()
def paginations(valid_pagination_constructor_params: list[dict]) -> list[Pagination]:
    return [Pagination(**params) for params in valid_pagination_constructor_params]


@pytest.fixture()
def invalid_pagination_constructor_params() -> list[dict]:
    return [
        {
            "id": uuid4(),
            "type": None,
        },
        {
            "id": uuid4(),
            "type": "simple",
            "url": "https://cinema.com/films?page={n}",
            "simple_start_from": 0,
        },
        {
            "id": uuid4(),
            "type": "simple",
            "url": "https://cinema.com/films",
            "simple_start_from": 0,
            "limit": 10,
        },
        {
            "id": uuid4(),
            "type": "day",
            "url": "https://cinema.com/films?date={day}",
            "date_format": "asdasda",
            "limit": -10,
        },
    ]


def test_valid_paginations(valid_pagination_constructor_params: list[dict]):
    for params in valid_pagination_constructor_params:
        Pagination(**params)


def test_invalid_paginations(invalid_pagination_constructor_params: list[dict]):
    for params in invalid_pagination_constructor_params:
        with pytest.raises(ValidationError):
            Pagination(**params)


def test_pagination_urls(paginations: list[Pagination]):
    for pagination in paginations:
        urls = pagination.urls()
        assert isinstance(urls, Iterable), "URLs should be iterable"
        assert (
            not pagination.limit or len(urls) == pagination.limit
        ), "Number of URLs should match the limit"
