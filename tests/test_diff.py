from pathlib import Path

import pytest

from facilitate.diff import compute_edit_script
from facilitate.loader import load_from_file
from facilitate.model.node import Node

_PATH_TESTS = Path(__file__).parent
_PATH_PROGRAMS = _PATH_TESTS / "resources" / "programs"


@pytest.mark.xfail()
def test_diff_literal_already_has_expression() -> None:
    level_dir = _PATH_PROGRAMS / "spike_curric_moving_forward_50cm_try_it"
    student_dir = level_dir / "2762924"
    before_file = student_dir / "11.json"
    after_file = student_dir / "12.json"
    tree_from = load_from_file(before_file)
    tree_to = load_from_file(after_file)
    script = compute_edit_script(tree_from, tree_to)


def test_diff_minimal_trees(minimal_tree: Node, minimal_with_extra_tree: Node) -> None:
    tree_from = minimal_tree
    tree_to = minimal_with_extra_tree
    script = compute_edit_script(tree_from, tree_to)
