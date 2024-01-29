import pytest

import functools

from facilitate.model.block import Block
from facilitate.model.sequence import Sequence


def test_insert_block() -> None:
    def blocks_to_ids(blocks: list[Block]) -> list[str]:
        return [block.id_ for block in blocks]

    sequence = Sequence(id_="seq")
    assert sequence.blocks == []

    opcode = "PLACEHOLDER"

    insert_block = functools.partial(
        sequence.insert_block,
        opcode=opcode,
        is_shadow=False,
    )

    insert_block(id_="1", position=0)
    assert blocks_to_ids(sequence.blocks) == [
        "ADDED:1",
    ]

    insert_block(id_="2", position=0)
    assert blocks_to_ids(sequence.blocks) == [
        "ADDED:2",
        "ADDED:1",
    ]

    insert_block(id_="3", position=1)
    assert blocks_to_ids(sequence.blocks) == [
        "ADDED:2",
        "ADDED:3",
        "ADDED:1",
    ]

    insert_block(id_="4", position=2)
    assert blocks_to_ids(sequence.blocks) == [
        "ADDED:2",
        "ADDED:3",
        "ADDED:4",
        "ADDED:1",
    ]

    insert_block(id_="5", position=5)
    assert blocks_to_ids(sequence.blocks) == [
        "ADDED:2",
        "ADDED:3",
        "ADDED:4",
        "ADDED:1",
        "ADDED:5",
    ]
