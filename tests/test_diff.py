import typing as t
from pathlib import Path

from facilitate.diff import compute_edit_script
from facilitate.edit import EditScript
from facilitate.loader import load_from_file
from facilitate.model.node import Node


_PATH_TESTS = Path(__file__).parent
_PATH_PROGRAMS = _PATH_TESTS / "resources" / "programs"


def diff_student_program_versions(
    level_name: str,
    student_id: str,
    before_version: int,
    after_version: int,
) -> EditScript:
    level_dir = _PATH_PROGRAMS / level_name
    student_dir = level_dir / student_id
    before_file = student_dir / f"{before_version}.json"
    after_file = student_dir / f"{after_version}.json"
    tree_from = load_from_file(before_file)
    tree_to = load_from_file(after_file)
    return compute_edit_script(tree_from, tree_to)


def test_diff_literal_already_has_expression() -> None:
    diff_student_program_versions(
        "spike_curric_moving_forward_50cm_try_it",
        "2762924",
        11,
        12,
    )


def test_diff_merge_top_level_sequences() -> None:
    diff_student_program_versions(
        "spike_curric_arm_movement_getting_stuck_try_it",
        "2605221",
        3,
        8
    )


def test_diff_programs_with_field_value_change() -> None:
    level_dir = _PATH_PROGRAMS / "spike_curric_turning_in_place_left_turn_try_it"
    student_dir = level_dir / "4847845"
    before_file = student_dir / "4.json"
    after_file = student_dir / "5.json"
    tree_from = load_from_file(before_file)
    tree_to = load_from_file(after_file)
    compute_edit_script(tree_from, tree_to)


def test_diff_update_is_not_none() -> None:
    level_dir = _PATH_PROGRAMS / "spike_curric_sequential_movements_mini_challenge_curriculum"
    student_dir = level_dir / "2952515"
    before_file = student_dir / "12.json"
    after_file = student_dir / "45.json"
    tree_from = load_from_file(before_file)
    tree_to = load_from_file(after_file)
    compute_edit_script(tree_from, tree_to)


def test_diff_leads_to_find_insertion_point_failure() -> None:
    level_dir = _PATH_PROGRAMS / "spike_curric_vacuum_mini_challenge"
    student_dir = level_dir / "2515268"
    before_file = student_dir / "20.json"
    after_file = student_dir / "36.json"
    tree_from = load_from_file(before_file)
    tree_to = load_from_file(after_file)
    compute_edit_script(tree_from, tree_to)


def test_diff_minimal_trees(minimal_tree: Node, minimal_with_extra_tree: Node) -> None:
    tree_from = minimal_tree
    tree_to = minimal_with_extra_tree
    compute_edit_script(tree_from, tree_to)
