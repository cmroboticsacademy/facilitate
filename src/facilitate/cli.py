"""Provides a simple command-line interface for Facilitate."""
from __future__ import annotations

import sys

import click
from loguru import logger

from facilitate.diff import compute_edit_script
from facilitate.edit import EditScript
from facilitate.loader import load_from_file
from facilitate.scraper import scrape as _scrape


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
@click.option(
    "-f", "--format", "format_",
    default="png",
    help="Output file format.",
    type=click.Choice(["png", "pdf"]),
)
def draw(program: str, output: str, format_: str) -> None:
    """Draws a given Scratch program as a PNG image."""
    ast = load_from_file(program)
    if format_ == "pdf":
        ast.to_dot_pdf(output)
    elif format_ == "png":
        ast.to_dot_png(output)
    else:
        error = f"unknown format: {format}"
        raise ValueError(error)


@cli.command()
@click.argument("before", type=click.Path(exists=True))
@click.argument("after", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    default="edit_script.json",
    help="Output file name.",
    type=click.Path(),
)
def diff(before: str, after: str, output: str) -> None:
    """Computes an edit script between two version of a Scratch program."""
    ast_before = load_from_file(before)
    ast_after = load_from_file(after)

    edits = compute_edit_script(ast_before, ast_after)
    edits.save_to_json(output)


@cli.command()
@click.argument("script", type=click.Path(exists=True))
@click.argument("before", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    default="animation.gif",
    help="Output file name.",
    type=click.Path(),
)
def animate(
    script: str,
    before: str,
    output: str,
) -> None:
    """Animates the effects of applying an edit script to a Scratch program."""
    edit_script = EditScript.load(script)
    ast_before = load_from_file(before)

    edit_script.save_to_dot_gif(
        output,
        ast_before,
    )


@cli.command()
@click.argument("dump", type=click.Path(exists=True))
@click.option(
    "-o", "--output",
    default="programs",
    help="Output directory.",
    type=click.Path(),
)
def scrape(dump: str, output: str) -> None:
    _scrape(
        dump_filename=dump,
        output_to=output,
    )
