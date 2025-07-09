import json
from typing import cast

import pytest
from pydantic import HttpUrl
from sqlalchemy import Dialect

from lagransala.shared.application import build_sqlmodel_list_type, build_sqlmodel_type


@pytest.fixture(scope="module")
def dummy_dialect() -> Dialect:
    return cast(Dialect, None)


def test_build_sqlmodel_type_roundtrip_valid_str(dummy_dialect):
    UrlType = build_sqlmodel_type(HttpUrl)
    # bind param
    url_str = "http://example.com/path"
    bound = UrlType().process_bind_param(url_str, dialect=dummy_dialect)
    assert bound == url_str
    # result value parsing
    parsed = UrlType().process_result_value(url_str, dialect=dummy_dialect)
    assert isinstance(parsed, HttpUrl)
    assert str(parsed) == url_str


def test_build_sqlmodel_type_none(dummy_dialect):
    UrlType = build_sqlmodel_type(HttpUrl)
    assert UrlType().process_bind_param(None, dialect=dummy_dialect) is None
    assert UrlType().process_result_value(None, dialect=dummy_dialect) is None


def test_build_sqlmodel_type_invalid_str_raises(dummy_dialect):
    UrlType = build_sqlmodel_type(HttpUrl)
    with pytest.raises(ValueError):
        UrlType().process_bind_param("not-a-url", dialect=dummy_dialect)


def test_build_sqlmodel_type_non_str_casts(dummy_dialect):
    UrlType = build_sqlmodel_type(str)
    bound = UrlType().process_bind_param(123, dialect=dummy_dialect)
    assert bound == "123"
    assert UrlType().process_result_value("456", dialect=dummy_dialect) == "456"


def test_build_sqlmodel_list_type_roundtrip(dummy_dialect):
    IntListType = build_sqlmodel_list_type(int)
    data = [1, 2, 3]
    bound = IntListType().process_bind_param(data, dialect=dummy_dialect)
    assert json.loads(bound) == data
    result = IntListType().process_result_value(bound, dialect=dummy_dialect)
    assert result == data
    assert result and all(isinstance(x, int) for x in result)


def test_build_sqlmodel_list_type_invalid_json_raises(dummy_dialect):
    IntListType = build_sqlmodel_list_type(int)
    with pytest.raises(ValueError):
        IntListType().process_bind_param("[1, ", dialect=dummy_dialect)


def test_build_sqlmodel_list_type_none(dummy_dialect):
    IntListType = build_sqlmodel_list_type(int)
    assert IntListType().process_bind_param(None, dialect=dummy_dialect) is None
    assert IntListType().process_result_value(None, dialect=dummy_dialect) is None
