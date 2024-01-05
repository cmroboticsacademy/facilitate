"""Provides a simple command-line interface for Facilitate."""
from __future__ import annotations

import sys

import click
from loguru import logger

from facilitate.diff import compute_edit_script
from facilitate.loader import load_from_file


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        format="<level>{level}:</level> {message}",
        level="TRACE",
        colorize=True,
    )


@click.group()
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="enables verbose logging.",
)
def cli(verbose: bool) -> None:
    if verbose:
        setup_logging()


@cli.command()
@click.argument("program", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    default="output.png",
    help="Output file name.",
    type=click.Path(),
)
def draw(program: str, output: str) -> None:
    """Draws a given Scratch program as a PNG image."""
    ast = load_from_file(program)
    ast.to_dot_png(output)


@cli.command()
@click.argument("before", type=click.Path(exists=True))
@click.argument("after", type=click.Path(exists=True))
def diff(before: str, after: str) -> None:
    """Computes an edit script between two version of a Scratch program."""
    ast_before = load_from_file(before)
    ast_after = load_from_file(after)

    compute_edit_script(ast_before, ast_after)
