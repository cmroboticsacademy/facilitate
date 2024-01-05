import json
import os
import sys

from loguru import logger
from pprint import pprint
import networkx as nx

from facilitate.gumtree import compute_gumtree_mappings
from facilitate.loader import load_from_file
from facilitate.model import Program

EXAMPLE_DIR = os.path.dirname(__file__)
REPO_DIR = os.path.dirname(EXAMPLE_DIR)
DATA_DIR = os.path.join(REPO_DIR, "Vacuum348")


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{level}:</level> {message}",
        level="TRACE",
        colorize=True,
    )


def load_good() -> Program:
    filename = f"{EXAMPLE_DIR}/good.json"
    with open(filename) as f:
        description = json.load(f)
    return load_program_from_block_descriptions(description)


def load_bad() -> Program:
    filename = f"{EXAMPLE_DIR}/bad.json"
    with open(filename) as f:
        description = json.load(f)
    return load_program_from_block_descriptions(description)


def load_ugly() -> Program:
    filename = f"{EXAMPLE_DIR}/ugly.json"
    with open(filename) as f:
        description = json.load(f)
    return load_program_from_block_descriptions(description)


def main() -> None:
    setup_logging()

    program_ugly = load_from_file(f"{EXAMPLE_DIR}/ugly.json")
    program_ugly.to_dot_png("visualizations/ugly.dot.png")

    program_bad = load_from_file(f"{EXAMPLE_DIR}/bad.json")
    program_bad.to_dot_png("visualizations/bad.dot.png")

    program_good = load_from_file(f"{EXAMPLE_DIR}/good.json")
    program_good.to_dot_png("visualizations/good.dot.png")

    # edit distance: bad -> good



if __name__ == "__main__":
    main()
