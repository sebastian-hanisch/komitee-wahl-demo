"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, keines auf einem Rand der Regler, keines durch eine einzelne Regleränderung vom Standard;
die Aussagen der Hilfetexte stimmen mit der Rechnung überein."""

import pytest
from conftest import letters

import kom_constants as C
import kom_evaluation as ev
import kom_presets as P
import kom_scenario as S

FIRST = "Zwei Lager, fünf Sitze"
BOUNDS = {"n": (C.N_MIN, C.N_MAX), "m": (C.M_MIN, C.M_MAX), "k": (C.K_MIN, C.K_MAX), "cohesion": (C.COHESION_MIN, C.COHESION_MAX), "cross": (C.CROSS_MIN, C.CROSS_MAX), "seed": (0, C.SEED_MAX)}


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_regler_bounds_and_options_exist():
    for name, p in C.PRESETS.items():
        for key, (lo, hi) in BOUNDS.items():
            assert lo <= p[key] <= hi, (name, key)
        assert p["model"] in C.MODELS and p["rule"] in C.RULES and p["k"] <= p["m"], name


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[FIRST]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_preset_sits_on_a_bound_of_n_m_or_k():
    for name, preset in C.PRESETS.items():
        for key in ("n", "m", "k"):
            lo, hi = BOUNDS[key]
            assert preset[key] not in (lo, hi), (name, key)


def test_no_single_change_of_the_default_produces_another_preset():
    default = C.PRESETS[FIRST]
    for name, p in C.PRESETS.items():
        if name != FIRST:
            assert sum(1 for k in p if p[k] != default[k]) >= 2, name


def test_presets_are_pairwise_different():
    values = [tuple(sorted(p.items())) for p in C.PRESETS.values()]
    assert len(set(values)) == len(values)


def test_presets_with_ballots_have_matching_n_and_letters_inside_the_slate():
    for name, p in C.PRESETS.items():
        rows, err = S.parse_ballots(p["ballots"], p["m"])
        assert err is None, name
        if rows is not None:
            assert p["n"] == len(rows), name


def test_presets_have_no_input_errors_and_no_note():
    for name in C.PRESETS:
        a = analyse(name)
        assert a.errors == [] and a.note == "", name


# --- Aussagen der Hilfetexte ---------------------------------------------------------------------------------------------------------------

def test_default_preset_help():
    a = analyse(FIRST)
    assert a.results["av"].seats_by_camp == [5, 0] and a.results["pav"].seats_by_camp == [4, 1]       # alle fünf Sitze an das größere Lager gegen 4 : 1
    assert a.results["av"].jr is not None and a.results["pav"].jr is None and [a.results[r].jr for r in ("seqpav", "seqcc", "cc", "es", "esfill")] == [None] * 5


def test_approval_preset_help():
    a = analyse("Zustimmungswahl übergeht eine Minderheit")
    assert letters(a.results["av"].committee) == "ABC" and a.results["av"].covered == 6
    assert all(letters(a.results[r].committee) == "ABD" for r in ev.RULES if r != "av")             # alle anderen Regeln wählen A, B und D
    assert a.results["av"].jr == (1, (3,), (6, 7, 8))                                              # ein Drittel der Wähler: 3 ≥ 9/3


def test_chamberlin_courant_preset_help():
    a = analyse("Chamberlin–Courant lässt einen Sitz verfallen")
    assert letters(a.results["cc"].committee) == "AB" and a.counts[0] == 0                          # A, dem niemand zustimmt
    assert a.results["cc"].jr is None and a.results["cc"].ejr == (2, (1, 2), (0, 1, 2))
    assert [r for r in ev.RULES if a.results[r].ejr is not None] == ["seqcc", "cc"]


def test_greedy_preset_help():
    a = analyse("Gierig verpasst den besten Ausschuss")
    assert letters(a.results["seqcc"].committee) == "AB" and a.results["seqcc"].covered == 7        # 7 von 8
    assert letters(a.results["cc"].committee) == "BC" and a.results["cc"].covered == 8              # alle 8


def test_equal_shares_preset_help():
    a = analyse("Equal Shares bleibt leer")
    assert a.results["es"].committee == frozenset() and a.results["es"].trace == []
    assert letters(a.results["esfill"].committee) == "AB"


def test_three_camps_preset_help():
    a = analyse("Drei Lager, vier Sitze")
    assert a.results["av"].seats_by_camp == [3, 0, 1] and a.results["pav"].seats_by_camp == [2, 1, 1]
    assert sum(1 for v in a.voter_camp if v == 1) == 9 and 9 / 30 == pytest.approx(0.3)
