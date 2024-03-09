import functools
from pathlib import Path
from pprint import pprint

import pytest

from facilitate.model.block import Block
from facilitate.model.sequence import Sequence
from facilitate.loader import load_from_file

_PATH_TESTS = Path(__file__).parent
_PATH_PROGRAMS = _PATH_TESTS / "resources" / "programs"


def test_position_of_block() -> None:
    filename = _PATH_PROGRAMS / "spike_curric_vacuum_mini_challenge"  / "2515268" / "36.json"
    tree = load_from_file(filename)
    sequence = tree.find("io9Jcf3?[Z3`[$L)5Zbd").parent
    pprint(sequence)
    assert isinstance(sequence, Sequence)
    assert len(sequence.blocks) == 9

    block = tree.find("j]U#7^CHJOqlaahe)(2n")
    assert block is not None

    expected = 8
    actual = sequence.position_of_block(block)
    assert actual == expected


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
        "1",
    ]

    insert_block(id_="2", position=0)
    assert blocks_to_ids(sequence.blocks) == [
        "2",
        "1",
    ]

    insert_block(id_="3", position=1)
    assert blocks_to_ids(sequence.blocks) == [
        "2",
        "3",
        "1",
    ]

    insert_block(id_="4", position=2)
    assert blocks_to_ids(sequence.blocks) == [
        "2",
        "3",
        "4",
        "1",
    ]

    insert_block(id_="5", position=5)
    assert blocks_to_ids(sequence.blocks) == [
        "2",
        "3",
        "4",
        "1",
        "5",
    ]
