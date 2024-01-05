"""Provides a simple command-line interface for Facilitate."""
from __future__ import annotations

import click

from facilitate.loader import load_from_file


@click.group()
def cli() -> None:
    pass


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
