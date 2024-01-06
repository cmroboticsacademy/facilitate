from __future__ import annotations

from pathlib import Path
import typing as t

import pytest

from facilitate.loader import load_from_file

if t.TYPE_CHECKING:
    from facilitate.model.node import Node

_TEST_DIR = Path(__file__).parent
_PROJECT_DIR = _TEST_DIR.parent
_EXAMPLES_DIR = _PROJECT_DIR / "examples"
_GOOD_EXAMPLE_PATH = _EXAMPLES_DIR / "good.json"
_BAD_EXAMPLE_PATH = _EXAMPLES_DIR / "bad.json"
_UGLY_EXAMPLE_PATH = _EXAMPLES_DIR / "ugly.json"


@pytest.fixture
def good_tree() -> Node:
    return load_from_file(_GOOD_EXAMPLE_PATH)

@pytest.fixture
def bad_tree() -> Node:
    return load_from_file(_BAD_EXAMPLE_PATH)

@pytest.fixture
def ugly_tree() -> Node:
    return load_from_file(_UGLY_EXAMPLE_PATH)
