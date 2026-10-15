import json
from collections.abc import Callable
from typing import Any

from sqlmodel import AutoString


def _type_name(internal_type: Callable[..., Any]) -> str:
    return getattr(internal_type, "__name__", repr(internal_type))


def build_sqlmodel_type[T](internal_type: Callable[[Any], T]) -> type[AutoString]:
    class CustomType(AutoString):
        def process_bind_param(self, value, dialect) -> str | None:
            if value is None:
                return None

            if isinstance(value, str):
                # Test if value is valid to avoid `process_result_value` failling
                try:
                    internal_type(value)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid value for {_type_name(internal_type)}: {e}"
                    ) from e

            return str(value)

        def process_result_value(self, value, dialect) -> T | None:
            if value is None:
                return None

            return internal_type(value)

    return CustomType


def build_sqlmodel_list_type[T](internal_type: Callable[[Any], T]) -> type[AutoString]:
    class CustomType(AutoString):
        def process_bind_param(self, value, dialect) -> str | None:
            if value is None:
                return None

            if isinstance(value, str):
                # Test if value is valid to avoid `process_result_value` failling
                try:
                    values = json.loads(value)
                    if not isinstance(values, list):
                        raise ValueError("Value must be a list")
                    for v in values:
                        internal_type(v)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid value for {_type_name(internal_type)}: {e}"
                    ) from e

            return json.dumps(value)

        def process_result_value(self, value, dialect) -> list[T] | None:
            if value is None:
                return None
            return [internal_type(v) for v in json.loads(value)]

    return CustomType
