"""Szenario: Erzeuger der Stimmzettel, Lager und Texteingabe."""

import pytest
from conftest import letters

import kom_constants as C
import kom_scenario as S


@pytest.mark.parametrize("model", list(C.MODELS))
def test_ballots_are_deterministic_nonempty_and_inside_the_slate(model):
    a, vc, cc = S.make_ballots(model, 20, 8, 60, 10, 3)
    assert a == S.make_ballots(model, 20, 8, 60, 10, 3)[0] and a != S.make_ballots(model, 20, 8, 60, 10, 4)[0]
    assert len(a) == 20 and len(vc) == 20 and len(cc) == 8
    assert all(b and max(b) < 8 and min(b) >= 0 for b in a)


def test_default_instance_by_hand():
    ballots, vc, cc = S.make_ballots("zwei", 24, 10, 70, 10, 6)
    assert [letters(b) for b in ballots][:5] == [letters(b) for b in S.make_ballots("zwei", 24, 10, 70, 10, 6)[0]][:5]
    assert vc == [0] * 17 + [1] * 7 and cc == [0] * 5 + [1] * 5


@pytest.mark.parametrize("model,n,m,voters,cands", [
    ("zwei", 10, 6, [7, 3], [3, 3]),
    ("drei", 10, 6, [5, 3, 2], [2, 2, 2]),
    ("keine", 10, 6, [10], [6]),
    ("zwei", 24, 10, [17, 7], [5, 5]),
    ("drei", 30, 9, [15, 9, 6], [3, 3, 3]),
])
def test_camps_follow_the_shares(model, n, m, voters, cands):
    vc, cc = S.camps_of(model, n, m)
    assert [vc.count(g) for g in range(len(voters))] == voters and [cc.count(g) for g in range(len(cands))] == cands
    assert vc == sorted(vc) and cc == sorted(cc)


def test_camps_for_a_slate_that_does_not_divide_evenly():
    vc, cc = S.camps_of("drei", 7, 8)
    assert len(vc) == 7 and len(cc) == 8 and set(cc) == {0, 1, 2} and cc == sorted(cc)


def test_cohesion_and_cross_approval_change_the_ballots():
    own, _, cc = S.make_ballots("zwei", 40, 10, 90, 0, 1)
    vc = S.camps_of("zwei", 40, 10)[0]
    assert all(c < 5 for b, v in zip(own, vc) for c in b if v == 0) and all(c >= 5 for b, v in zip(own, vc) for c in b if v == 1)      # ohne Zustimmung zu fremden Lagern bleibt jeder im eigenen
    mixed, _, _ = S.make_ballots("zwei", 40, 10, 90, 30, 1)
    assert any(c >= 5 for b, v in zip(mixed, vc) for c in b if v == 0)


def test_unknown_model_raises():
    with pytest.raises(ValueError):
        S.make_ballots("nichts", 10, 5, 70, 10, 1)


def test_parse_ballots_accepts_letters_in_every_notation():
    rows, err = S.parse_ballots("A B C\nd\nabc\n-\nA,B;C", 4)
    assert err is None and [letters(b) for b in rows] == ["ABC", "D", "ABC", "", "ABC"]


def test_parse_ballots_empty_is_no_input_and_no_error():
    assert S.parse_ballots("", 4) == (None, None) and S.parse_ballots("  \n ", 4) == (None, None) and S.parse_ballots(None, 4) == (None, None)


@pytest.mark.parametrize("text,fragment", [
    ("A", "2 bis 40 Zeilen"),
    ("\n".join(["A"] * 41), "2 bis 40 Zeilen"),
    ("A\nA 1", "Zeile 2: „1“ ist kein Kandidat"),
    ("A\nA %", "Zeile 2: „%“ ist kein Kandidat"),
    ("A\nE", "Zeile 2: Kandidat „E“ gibt es nicht, es gibt nur die Buchstaben A bis D"),
    ("A\nM", "Zeile 2: „M“ ist kein Kandidat"),
])
def test_parse_ballots_rejects_bad_input_with_a_message(text, fragment):
    rows, err = S.parse_ballots(text, 4)
    assert rows is None and fragment in err


def test_parse_ballots_respects_the_number_of_candidates():
    assert S.parse_ballots("A\nL", 12)[1] is None and S.parse_ballots("A\nL", 11)[1] is not None


def test_parse_ballots_accepts_the_bounds():
    assert S.parse_ballots("\n".join(["A"] * 2), 3)[1] is None and S.parse_ballots("\n".join(["A"] * 40), 3)[1] is None
