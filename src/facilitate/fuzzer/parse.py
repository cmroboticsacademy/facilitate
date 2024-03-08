from __future__ import annotations

import random
import typing as t
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from facilitate.loader import load_from_file
from facilitate.util import exception_to_crash_description


@dataclass(frozen=True)
class ParserCrash:
    program: Path
    exception: Exception

    @classmethod
    def build(cls, program: Path, exception: Exception) -> ParserCrash:
        program = program.absolute()
        return ParserCrash(
            program=program,
            exception=exception,
        )

    def to_csv_row(self) -> list[str]:
        return [
            str(self.program),
            exception_to_crash_description(self.exception),
        ]


@dataclass
class ParserFuzzer:
    number: int | None
    program_directory: Path
    _rng: random.Random

    @classmethod
    def build(
        cls,
        number: int,
        program_directory: Path,
        *,
        seed: int | None = None,
    ) -> ParserFuzzer:
        rng = random.Random(seed)
        return ParserFuzzer(
            number=number,
            program_directory=Path(program_directory),
            _rng=rng,
        )

    def run(self) -> t.Iterator[ParserCrash]:
        """Runs fuzzer and yields paths to programs that failed to parse."""
        program_files = list(self.program_directory.glob("**/*.json"))
        logger.debug(f"found {len(program_files)} programs to parse")
        self._rng.shuffle(program_files)
        if self.number:
            program_files = program_files[:self.number]
        logger.debug(f"fuzzing {len(program_files)} programs")

        for program_file in program_files:
            maybe_crash = self._run_one(program_file)
            if maybe_crash:
                yield maybe_crash

    def _run_one(self, program_file: Path) -> ParserCrash | None:
        """Fuzzes a single program.

        Returns a description of the crash, if one occurred.
        """
        try:
            load_from_file(program_file)
        except Exception as err:  # noqa: BLE001
            return ParserCrash.build(
                program=program_file,
                exception=err,
            )
        return None
