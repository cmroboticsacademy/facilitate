"""Provides a simple command-line interface for Facilitate."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import click
from loguru import logger

from facilitate.diff import compute_edit_script
from facilitate.edit import EditScript
from facilitate.fuzzer.diff import (
    BaseDiffFuzzer,
    SuccessiveVersionDiffFuzzer,
)
from facilitate.fuzzer.parse import (
    ParserCrash,
    ParserFuzzer,
)
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


@cli.group()
def fuzz() -> None:
    pass


@fuzz.command("parse")
@click.option(
    "-n", "--number",
    type=int,
    default=None,
    help="maximum number of programs to parse.",
)
@click.option(
    "-i", "--input", "input_",
    default="./programs",
    type=click.Path(exists=True),
    help="directory containing programs to parse.",
)
@click.option(
    "-s", "--seed",
    type=int,
    default=None,
    help="seed for random number generator.",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="parsing_failures.csv",
    help="file to which list of failed programs will be written.",
)
def fuzz_parse(
    number: int,
    input_: Path | str,
    seed: int,
    output: Path | str,
) -> None:
    """Fuzzes the parsing of Scratch programs."""
    input_ = Path(input_)
    output = Path(output)

    crashes: list[ParserCrash] = []
    for crash in ParserFuzzer.build(
        number=number,
        program_directory=input_,
        seed=seed,
    ).run():
        crashes.append(crash)  # noqa: PERF402

    with output.open("w") as file:
        writer = csv.writer(file)
        for crash in crashes:
            writer.writerow(crash.to_csv_row())


@fuzz.command("diff")
@click.option(
    "-m", "--method",
    type=click.Choice(["successive"]),
    default="successive",
    help="method that should be used to select program pairs.",
)
@click.option(
    "-n", "--number",
    type=int,
    default=None,
    help="maximum number of program pairs to diff.",
)
@click.option(
    "-i", "--input", "input_",
    default="./programs",
    type=click.Path(exists=True),
    help="directory containing programs to diff.",
)
@click.option(
    "-s", "--seed",
    type=int,
    default=None,
    help="seed for random number generator.",
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="diff_failures.csv",
    help="file to which list of failed program pairs will be written.",
)
def fuzz_diff(
    method: str,
    number: int,
    input_: Path | str,
    seed: int,
    output: Path | str,
) -> None:
    """Fuzzes the diffing of Scratch programs."""
    input_ = Path(input_)
    output = Path(output)

    fuzzer: BaseDiffFuzzer
    if method == "successive":
        fuzzer = SuccessiveVersionDiffFuzzer.build(
            number=number,
            program_directory=input_,
            seed=seed,
        )
    else:
        error = f"unknown method for picking pairs: {method}"
        raise ValueError(error)

    crashes = list(fuzzer.run())
    with output.open("w") as file:
        writer = csv.writer(file)
        for crash in crashes:
            writer.writerow(crash.to_csv_row())


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
