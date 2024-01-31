from __future__ import annotations

import typing as t

T = t.TypeVar("T")


def quote(s: str) -> str:
    return f'"{s}"'


def longest_common_subsequence(
    lx: list[T],
    ly: list[T],
    criteria: t.Callable[[T, T], bool],
) -> list[tuple[T, T]]:
    """Finds the longest common subsequence within X and Y that satisfies a given criteria."""
    m = len(lx)
    n = len(ly)

    if m == 0 or n == 0:
        return []

    table: list[list[list[tuple[T, T]] | None]] = [
        [None] * (n + 1) for i in range(m + 1)
    ]

    for i in range(m + 1):
        for j in range(n + 1):
            x = lx[i - 1]
            y = ly[j - 1]
            if i == 0 or j == 0:
                table[i][j] = []
            elif criteria(x, y):
                prev = table[i - 1][j - 1]
                assert prev is not None
                table[i][j] = [*prev, (x, y)]
            else:
                a = table[i - 1][j]
                b = table[i][j - 1]
                assert a is not None
                assert b is not None
                table[i][j] = a if len(a) > len(b) else b

    result = table[m][n]
    assert result is not None
    return result
