import pytest
from generaltranslation.translate._batch import create_batches, process_batches

def test_create_batches_basic():
    items = list(range(5))
    result = create_batches(items, 2)
    assert result == [[0, 1], [2, 3], [4]]

def test_create_batches_empty():
    assert create_batches([], 10) == []

def test_create_batches_exact():
    items = list(range(4))
    result = create_batches(items, 2)
    assert result == [[0, 1], [2, 3]]

def test_create_batches_single():
    items = [1, 2, 3]
    result = create_batches(items, 100)
    assert result == [[1, 2, 3]]

@pytest.mark.asyncio
async def test_process_batches_empty():
    async def processor(batch):
        return batch
    result = await process_batches([], processor)
    assert result == {"data": [], "count": 0, "batch_count": 0}

@pytest.mark.asyncio
async def test_process_batches_basic():
    async def processor(batch):
        return [x * 2 for x in batch]
    result = await process_batches([1, 2, 3, 4, 5], processor, batch_size=2)
    assert sorted(result["data"]) == [2, 4, 6, 8, 10]
    assert result["count"] == 5
    assert result["batch_count"] == 3

@pytest.mark.asyncio
async def test_process_batches_sequential():
    order = []
    async def processor(batch):
        order.extend(batch)
        return batch
    result = await process_batches([1, 2, 3, 4], processor, batch_size=2, parallel=False)
    assert order == [1, 2, 3, 4]
    assert result["count"] == 4
