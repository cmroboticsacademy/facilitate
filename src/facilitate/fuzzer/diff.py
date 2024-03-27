from __future__ import annotations

import abc
import random
import typing as t
from dataclasses import dataclass
from pathlib import Path

from overrides import overrides

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

    @abc.abstractmethod
    def generate_pairs(self) -> t.Iterator[tuple[Path, Path]]:
        ...

    def run(self) -> t.Iterator[DiffCrash]:
        """Runs fuzzer and yields pairs of program paths that failed to diff."""
        pairs: list[tuple[Path, Path]] = list(self.generate_pairs())
        if self.number:
            pairs = pairs[:self.number]
        print(f"testing {len(pairs)} pairs")
        for from_program_file, to_program_file in pairs:
            if crash := self._run_one(from_program_file, to_program_file):
                yield crash

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

    @overrides
    def generate_pairs(self) -> t.Iterator[tuple[Path, Path]]:
        """Generates pairs of programs to diff."""
        level_dirs = [
            child for child in self.program_directory.iterdir() if child.is_dir()
        ]
        level_dir_to_student_dirs: dict[Path, list[Path]] = {
            level_dir: [child for child in level_dir.iterdir() if child.is_dir()]
            for level_dir in level_dirs
        }

        # ignore any student directory that doesn't have at least two programs
        level_dir_to_student_dirs = {
            level_dir: student_dirs
            for level_dir, student_dirs in level_dir_to_student_dirs.items()
            if len(student_dirs) >= 2  # noqa: PLR2004
        }

        for level_dir in level_dir_to_student_dirs:
            student_dirs = level_dir_to_student_dirs[level_dir]
            for student_dir in student_dirs:
                program_files = list(student_dir.glob("*.json"))
                for i in range(1, len(program_files)):
                    from_program_file = program_files[i - 1]
                    to_program_file = program_files[i]
                    yield from_program_file, to_program_file

