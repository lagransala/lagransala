from typing import Generator, Iterable, TypeVar

T = TypeVar("T")


def flatten(l: Iterable[Iterable[T]]) -> Generator[T]:
    return (item for sublist in l for item in sublist)
