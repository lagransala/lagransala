from collections.abc import Generator, Iterable


def flatten[T](nested: Iterable[Iterable[T]]) -> Generator[T]:
    return (item for sublist in nested for item in sublist)
