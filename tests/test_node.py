import pytest

from loguru import logger

from facilitate.model.node import Node


def test_height(good_tree: Node) -> None:
    node = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    assert node.height == 3

    node = good_tree.find("0z(.tYRa{!SepmI$)#U,")
    assert node.height == 4


def test_has_children(good_tree: Node) -> None:
    node = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    assert node.has_children()

    node = good_tree.find("x:e}MT(JcdrCU9-b]!D?")
    assert node.has_children()

    node = good_tree.find(":field[SPIN_DIRECTIONS]@x:e}MT(JcdrCU9-b]!D?")
    assert not node.has_children()


def test_parent(good_tree: Node) -> None:
    assert good_tree.parent is None
    for node in good_tree.nodes():
        for child in node.children():
            assert child.parent == node


def test_size(good_tree: Node) -> None:
    node = good_tree.find("0z(.tYRa{!SepmI$)#U,")
    assert node.size() == 4

    node = good_tree.find(":input[DIRECTION]@0z(.tYRa{!SepmI$)#U,")
    assert node.size() == 3


def test_postorder(good_tree: Node) -> None:
    actual_postordered_ids = [node.id_ for node in good_tree.postorder()]
    expected_postordered_ids = [
        'io9Jcf3?[Z3`[$L)5Zbd',
        ':field[SPIN_DIRECTIONS]@x:e}MT(JcdrCU9-b]!D?',
        'x:e}MT(JcdrCU9-b]!D?',
        ':input[DIRECTION]@0z(.tYRa{!SepmI$)#U,',
        '0z(.tYRa{!SepmI$)#U,',
        ':field[STATE]@?kegHpYMl}a-h4_m8Ve4',
        ':field[PORT]@6D.mq-}FNkcpkuTweX|b',
        '6D.mq-}FNkcpkuTweX|b',
        ':input[PORT]@?kegHpYMl}a-h4_m8Ve4',
        '?kegHpYMl}a-h4_m8Ve4',
        ':input[CONDITION]@8JDo}mJ%HU*F^eT)9li:',
        '8JDo}mJ%HU*F^eT)9li:',
        ':field[UNITS]@iGEvR$b[2QHK#2K`bkrB',
        ':field[SPIN_DIRECTIONS]@T$b^Tq0.mV9wdws.DA@[',
        'T$b^Tq0.mV9wdws.DA@[',
        ':input[DIRECTION]@iGEvR$b[2QHK#2K`bkrB',
        ':literal@:input[RATE]@iGEvR$b[2QHK#2K`bkrB',
        ':input[RATE]@iGEvR$b[2QHK#2K`bkrB',
        'iGEvR$b[2QHK#2K`bkrB',
        ':field[SPIN_DIRECTIONS]@;UXN^kcB}()L,w3LFgoL',
        ';UXN^kcB}()L,w3LFgoL',
        ':input[DIRECTION]@Bs]SL)6S`k(hLjl*Cz,$',
        'Bs]SL)6S`k(hLjl*Cz,$',
        ':field[STATE]@nidJdKyZHARft!JOYU[}',
        ':field[PORT]@Zdo!7Kx)+^*N?qk?x(0P',
        'Zdo!7Kx)+^*N?qk?x(0P',
        ':input[PORT]@nidJdKyZHARft!JOYU[}',
        'nidJdKyZHARft!JOYU[}',
        ':input[CONDITION]@}Are5C@zU$,k#,A80|ww',
        '}Are5C@zU$,k#,A80|ww',
        ':field[UNITS]@:O(/=jeye9E{vE|o@0qe',
        ':field[SPIN_DIRECTIONS]@d5--.+c(ir]=#q`#x+tX',
        'd5--.+c(ir]=#q`#x+tX',
        ':input[DIRECTION]@:O(/=jeye9E{vE|o@0qe',
        ':literal@:input[RATE]@:O(/=jeye9E{vE|o@0qe',
        ':input[RATE]@:O(/=jeye9E{vE|o@0qe',
        ':O(/=jeye9E{vE|o@0qe',
        ':field[SPIN_DIRECTIONS]@WcFLv%YwG},{pS[|H%,s',
        'WcFLv%YwG},{pS[|H%,s',
        ':input[DIRECTION]@U$G9M~S)yP?MMH=Y)z1:',
        'U$G9M~S)yP?MMH=Y)z1:',
        ':field[STATE]@|2BJ{b~692qUEcqDPeVu',
        ':field[PORT]@C,?2y;lhr:1kj.^xG1vX',
        'C,?2y;lhr:1kj.^xG1vX',
        ':input[PORT]@|2BJ{b~692qUEcqDPeVu',
        '|2BJ{b~692qUEcqDPeVu',
        ':input[CONDITION]@j]U#7^CHJOqlaahe)(2n',
        'j]U#7^CHJOqlaahe)(2n',
        ':field[UNITS]@~!j{FGa?zF-y|vZ^4GD4',
        ':field[SPIN_DIRECTIONS]@Y)H|V?W:]b;ovMea7h55',
        'Y)H|V?W:]b;ovMea7h55',
        ':input[DIRECTION]@~!j{FGa?zF-y|vZ^4GD4',
        ':literal@:input[RATE]@~!j{FGa?zF-y|vZ^4GD4',
        ':input[RATE]@~!j{FGa?zF-y|vZ^4GD4',
        '~!j{FGa?zF-y|vZ^4GD4',
        ':field[SPIN_DIRECTIONS]@g^S4/M.eGOY5*O*-;?iR',
        'g^S4/M.eGOY5*O*-;?iR',
        ':input[DIRECTION]@@.isSP-6jVKHiY.#*TM6',
        '@.isSP-6jVKHiY.#*TM6',
        ':field[STATE]@+9cn]gk)O3l,q*iT,loz',
        ':field[PORT]@^p+Od{v##FGmPi33Bb8f',
        '^p+Od{v##FGmPi33Bb8f',
        ':input[PORT]@+9cn]gk)O3l,q*iT,loz',
        '+9cn]gk)O3l,q*iT,loz',
        ':input[CONDITION]@jR#!l0]kqB%K}fB9a_{O',
        'jR#!l0]kqB%K}fB9a_{O',
        ':field[UNITS]@Y?t;5vXlQ]dvL,LPjHBG',
        ':field[SPIN_DIRECTIONS]@$uB%+:F}W6r7bim--nK@',
        '$uB%+:F}W6r7bim--nK@',
        ':input[DIRECTION]@Y?t;5vXlQ]dvL,LPjHBG',
        ':literal@:input[RATE]@Y?t;5vXlQ]dvL,LPjHBG',
        ':input[RATE]@Y?t;5vXlQ]dvL,LPjHBG',
        'Y?t;5vXlQ]dvL,LPjHBG',
        ':seq@io9Jcf3?[Z3`[$L)5Zbd',
        'PROGRAM',
    ]
    assert actual_postordered_ids == expected_postordered_ids
