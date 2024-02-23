from facilitate.diff import compute_edit_script
from facilitate.model.node import Node


def test_diff_minimal_trees(minimal_tree: Node, minimal_with_extra_tree: Node) -> None:
    tree_from = minimal_tree
    tree_to = minimal_with_extra_tree
    script = compute_edit_script(tree_from, tree_to)
