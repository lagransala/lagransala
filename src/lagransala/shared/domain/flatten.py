from typing import Generator, Iterable, TypeVar

T = TypeVar("T")


def flatten(nested: Iterable[Iterable[T]]) -> Generator[T]:
    return (item for sublist in nested for item in sublist)
