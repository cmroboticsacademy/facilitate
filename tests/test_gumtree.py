import pytest

from pathlib import Path

from facilitate.gumtree import (
    compute_gumtree_mappings,
    compute_topdown_mappings,
    dice,
)
from facilitate.loader import load_from_file
from facilitate.mappings import NodeMappings
from facilitate.model.node import Node

_PATH_TESTS = Path(__file__).parent
_PATH_PROGRAMS = _PATH_TESTS / "resources" / "programs"


def test_diff_programs_with_field_value_change() -> None:
    level_dir = _PATH_PROGRAMS / "spike_curric_turning_in_place_left_turn_try_it"
    student_dir = level_dir / "4847845"
    before_file = student_dir / "4.json"
    after_file = student_dir / "5.json"
    tree_from = load_from_file(before_file)
    tree_to = load_from_file(after_file)
    mappings = compute_gumtree_mappings(
        tree_from,
        tree_to,
    )

    x = tree_from.find
    y = tree_to.find

    assert (x("PROGRAM"), y("PROGRAM")) in mappings
    assert (x("9QjVuYDhN]nxRQi1KR9+"), y("9QjVuYDhN]nxRQi1KR9+")) in mappings
    assert (x("#FZ(.H$KR:RYV8|n1ZwG"), y("#FZ(.H$KR:RYV8|n1ZwG")) in mappings
    assert (
        x("#FZ(.H$KR:RYV8|n1ZwG").find_field("UNITS"),
        y("#FZ(.H$KR:RYV8|n1ZwG").find_field("UNITS"),
    ) in mappings
    assert (
        x("#FZ(.H$KR:RYV8|n1ZwG").find_input("RATE"),
        y("#FZ(.H$KR:RYV8|n1ZwG").find_input("RATE"),
    ) in mappings
    assert (
        x("#FZ(.H$KR:RYV8|n1ZwG").find_input("RATE").expression,
        y("#FZ(.H$KR:RYV8|n1ZwG").find_input("RATE").expression,
    ) in mappings


def test_dice(good_tree: Node, bad_tree: Node) -> None:
    mappings = NodeMappings()

    input_to = good_tree.find("0z(.tYRa{!SepmI$)#U,").find_input("DIRECTION")
    assert input_to is not None
    input_from = bad_tree.find("tJ6ev+AvtHAf*PZbI}7i").find_input("DIRECTION")
    assert input_from is not None

    mappings.add_with_descendants(input_from, input_to)

    assert dice(input_from, input_to, mappings) == 1.0


# FIXME fails non-deterministically!
@pytest.mark.xfail(reason="non-deterministic behavior")
def test_topdown_mappings(good_tree: Node, bad_tree: Node) -> None:
    tree_from = bad_tree
    tree_to = good_tree

    nx = tree_from.find
    ny = tree_to.find

    mappings = compute_topdown_mappings(tree_from, tree_to)

    x = nx("ON]Ie`,s9aYllf=Ko6pI")
    y = ny("jR#!l0]kqB%K}fB9a_{O")

    assert x.equivalent_to(y)
    assert dice(x, y, mappings) == 1.0
    assert (x, y) in mappings
