from __future__ import annotations

import pytest


def test_track():
    from heapq import heappush

    h = []
    for value in range(1):
        heappush(h, value)
    assert [1] * 5_000


@pytest.mark.limit_memory("100 KB")
def test_memory_exceed():
    found = [[i] * 1_000 for i in range(15)]
    assert found
