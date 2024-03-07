import pytest

from pathlib import Path

from facilitate.loader import (
    _join_sequences,
    load_from_file,
)

_PATH_TESTS = Path(__file__).parent
_PATH_PROGRAMS = _PATH_TESTS / "resources" / "programs"


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

    # failure case from: spike_curric_cleaning_the_home_challenge_v2/2605231/1.json
    sequences = [
        ["a[c6l;66=_(l1 {xk6s.", "xLLqnXK]7Pt#zxJ!182q", "$nGp17SOH7{tXvKb}./t", "1$JaAZ?e6S 6kE]G~-q", "s3p,yCs{~fbr1]0Hzz8u", "v^[hulR6e_MJ#9=Ba_If", "FL)oNEd9ne^qrUMR,KCB", "5_EAD@/3W6lkUyi=Gjo1", "iLbNDuR*J$Pl|[W 4tnH", "I9M_D}G).bEhRR3_5S/-", "%726Fayu%F2$7;8IZsyc"],
        ["/Xwe50{tuguvnU0jv/jF", "%{VW6};]WTMr9e=aqq3]", "(DwG814k[ORK7.L(KEwf"],
        ["VK{|Wti|pPw6BK5c1Bb!", "X;ZfhjNw)xyG^KI(SFq6", "__3lOpGm^-#4oG%In#Kn", "5lw`F~rH(,7Ww;R@-rf#"],
        ["(DwG814k[ORK7.L(KEwf", "OYt.fwD^t8bqw}P*kht%", "VK{|Wti|pPw6BK5c1Bb!"],
        ["m@1_OoMdu5JSGzIwPF-3", "Z[3FE.1kfDA?^|4qBdnS"],
        ["dDJZOT^r,BCbfDSqHg*o", "m@1_OoMdu5JSGzIwPF-3"],
        ["r]3J 3v~6-Viflfmd2fa", "!#S(jjhsc)AI5:CGFaPw", "cD1^%tqX$UIaD`RTy*`i", "uGiRJkzmt}kz4oHdfe9n"],
        ["uGiRJkzmt}kz4oHdfe9n", "WM:$](e$:ZWtMe]G:Cd8", "`G`c# SLDotAMAhW~(M{"],
    ]

    expected = [
        ["a[c6l;66=_(l1 {xk6s.", "xLLqnXK]7Pt#zxJ!182q", "$nGp17SOH7{tXvKb}./t", "1$JaAZ?e6S 6kE]G~-q", "s3p,yCs{~fbr1]0Hzz8u", "v^[hulR6e_MJ#9=Ba_If", "FL)oNEd9ne^qrUMR,KCB", "5_EAD@/3W6lkUyi=Gjo1", "iLbNDuR*J$Pl|[W 4tnH", "I9M_D}G).bEhRR3_5S/-", "%726Fayu%F2$7;8IZsyc"],
        ["/Xwe50{tuguvnU0jv/jF", "%{VW6};]WTMr9e=aqq3]", "(DwG814k[ORK7.L(KEwf", "OYt.fwD^t8bqw}P*kht%", "VK{|Wti|pPw6BK5c1Bb!", "X;ZfhjNw)xyG^KI(SFq6", "__3lOpGm^-#4oG%In#Kn", "5lw`F~rH(,7Ww;R@-rf#"],
        ["dDJZOT^r,BCbfDSqHg*o", "m@1_OoMdu5JSGzIwPF-3", "Z[3FE.1kfDA?^|4qBdnS"],
        ["r]3J 3v~6-Viflfmd2fa", "!#S(jjhsc)AI5:CGFaPw", "cD1^%tqX$UIaD`RTy*`i", "uGiRJkzmt}kz4oHdfe9n", "WM:$](e$:ZWtMe]G:Cd8", "`G`c# SLDotAMAhW~(M{"],
    ]
    actual = _join_sequences(sequences)

    assert actual == expected


def test_load_from_file() -> None:
    def load(filename: str) -> None:
        load_from_file(_PATH_PROGRAMS / filename)

    load("spike_curric_cleaning_the_home_challenge_v2/2605231/1.json")
