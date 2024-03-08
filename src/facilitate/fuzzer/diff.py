from __future__ import annotations

import abc
import random
import typing as t
from dataclasses import dataclass
from pathlib import Path

from facilitate.diff import compute_edit_script
from facilitate.loader import load_from_file
from facilitate.util import exception_to_crash_description


@dataclass(frozen=True)
class DiffCrash:
    from_program: Path
    to_program: Path
    exception: Exception

    @classmethod
    def build(
        cls,
        from_program: Path,
        to_program: Path,
        exception: Exception,
    ) -> DiffCrash:
        from_program = from_program.absolute()
        to_program = to_program.absolute()
        return DiffCrash(
            from_program=from_program,
            to_program=to_program,
            exception=exception,
        )

    def to_csv_row(self) -> list[str]:
        return [
            str(self.from_program),
            str(self.to_program),
            exception_to_crash_description(self.exception),
        ]


@dataclass
class BaseDiffFuzzer(abc.ABC):
    number: int | None
    program_directory: Path
    _rng: random.Random



@dataclass
class SuccessiveVersionDiffFuzzer(BaseDiffFuzzer):
    @classmethod
    def build(
        cls,
        number: int,
        program_directory: Path,
        *,
        seed: int | None = None,
    ) -> SuccessiveVersionDiffFuzzer:
        rng = random.Random(seed)
        return SuccessiveVersionDiffFuzzer(
            number=number,
            program_directory=Path(program_directory),
            _rng=rng,
        )

    def run(self) -> t.Iterator[DiffCrash]:
        """Runs fuzzer and yields pairs of program paths that failed to diff."""
        raise NotImplementedError

    def _run_one(
        self,
        from_program_file: Path,
        to_program_file: Path,
    ) -> DiffCrash | None:
        """Fuzzes a pair of programs.

        Returns a description of the crash, if one occurred.
        """
        try:
            from_program = load_from_file(from_program_file)
            to_program = load_from_file(to_program_file)
            compute_edit_script(from_program, to_program)
        except Exception as err:  # noqa: BLE001
            return DiffCrash.build(
                from_program=from_program_file,
                to_program=to_program_file,
                exception=err,
            )
        return None
