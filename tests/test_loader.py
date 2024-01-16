import pytest

from facilitate.loader import _join_sequences


def test_join_sequences() -> None:
    sx = ["io9Jcf3?[Z3`[$L)5Zbd", "Y!JRDur.[+fZ7g7{L@!}", "E/817{xDdN,ihs?r1r}k", "%N@J{jHTQ!),(@%CkG^L"]
    sy = ["%N@J{jHTQ!),(@%CkG^L", "p1E##?Z;nx;a55uC.XP9"]
    sequences = [sx, sy]

    sz = [
        "io9Jcf3?[Z3`[$L)5Zbd", "Y!JRDur.[+fZ7g7{L@!}", "E/817{xDdN,ihs?r1r}k", "%N@J{jHTQ!),(@%CkG^L", "p1E##?Z;nx;a55uC.XP9"
    ]
    expected = [sz]
    actual = _join_sequences(sequences)

    assert actual == expected
