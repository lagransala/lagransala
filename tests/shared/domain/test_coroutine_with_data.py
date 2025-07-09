import pytest

from lagransala.shared.domain.coroutine_with_data import coroutine_with_data


@pytest.mark.asyncio
async def test_coroutine_with_data() -> None:
    async def sample_coroutine() -> str:
        return "hello"

    def combiner(result: str, data: str) -> str:
        return f"{result} {data}"

    result = await coroutine_with_data(
        coroutine=sample_coroutine(),
        data="world",
        combiner=combiner,
    )
    assert result == "hello world"
