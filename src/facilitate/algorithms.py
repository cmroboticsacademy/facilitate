from __future__ import annotations

import typing as t
from collections import deque

if t.TYPE_CHECKING:
    from facilitate.model.node import Node


def breadth_first_search(root: Node) -> t.Iterator[Node]:
    """Performs a breadth-first search of the tree rooted at the given node."""
    queue = deque([root])
    while queue:
        node = queue.popleft()
        yield node
        queue.extend(node.children())
