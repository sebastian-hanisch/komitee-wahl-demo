"""Randfälle: Extremwerte der Regler, Invarianten jeder Analyse, Gleichstände, leere Stimmzettel, Adresszeile und eigene Eingaben."""

import itertools
import os

import pytest
from streamlit.testing.v1 import AppTest

import kom_algorithm as A
import kom_constants as C
import kom_evaluation as ev

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
GRID = list(itertools.product((C.N_MIN, 12, C.N_MAX), (C.M_MIN, 8, C.M_MAX), (C.K_MIN, 3, C.K_MAX), tuple(C.MODELS)))


@pytest.mark.parametrize("n,m,k,model", GRID)
def test_invariants_at_the_extremes(n, m, k, model):
    a = ev.analyse(ev.Settings(n=n, m=m, k=k, model=model, seed=1))
    kk = min(k, m)
    assert a.n == n and a.m == m and a.k == kk and bool(a.note) == (k > m) and a.errors == []
    assert len(a.counts) == m and sum(a.counts) == sum(len(b) for b in a.ballots) and all(b for b in a.ballots)
    for rule in ev.RULES:
        r = a.results[rule]
        assert r.committee <= frozenset(range(m)) and len(r.committee) <= kk and (len(r.committee) == kk or rule == "es"), (rule, n, m, k)
        assert 0 <= r.covered <= n and 0 <= r.pav_ratio <= 1 + 1e-12
    assert a.results["pav"].pav_ratio == 1.0 and a.results["cc"].covered == a.best_cc == max(r.covered for r in a.results.values())
    assert a.results["pav"].ejr is None and a.results["es"].ejr is None and a.results["esfill"].ejr is None and a.results["cc"].jr is None
    assert len(ev.committee_rows(a)) == 7 and ev.verdict_state(a)[1] and ev.trace_lines(a)
    camp = ev.camp_rows(a)
    groups = len(C.MODEL_SHARES[model])
    assert len(camp) == 8
    for row, rule in zip(camp[1:], ev.RULES):
        assert sum(int(row[f"Lager {g + 1}"]) for g in range(groups)) == len(a.results[rule].committee)                  # jeder gewählte Kandidat gehört zu genau einem Lager


def test_k_equals_m_and_k_equals_one():
    a = ev.analyse(ev.Settings(n=10, m=4, k=4, seed=2))
    assert all(a.results[r].committee == frozenset(range(4)) for r in ev.RULES if r != "es")
    one = ev.analyse(ev.Settings(n=10, m=5, k=1, seed=2))
    assert len(one.results["av"].committee) == 1 and one.results["av"].committee == one.results["pav"].committee == one.results["seqpav"].committee


def test_voters_without_any_approval_are_never_covered():
    a = ev.analyse(ev.Settings(ballots="A\n-\n-\nB"))
    assert a.n == 4 and a.results["cc"].covered == 2 and all(a.results[r].covered <= 2 for r in ev.RULES)
    assert A.group_violation(a.ballots, a.m, a.k, a.results["av"].committee) is None                  # leere Stimmzettel stützen keine Gruppe


def test_identical_voters_have_one_slate():
    a = ev.analyse(ev.Settings(m=5, k=2, ballots="\n".join(["B C"] * 6)))
    assert all(set(a.results[r].committee) <= {1, 2} or r in ("cc", "seqcc") for r in ev.RULES)
    assert a.results["pav"].committee == frozenset({1, 2}) and a.results["es"].committee == frozenset({1, 2})


def test_ties_everywhere_choose_the_smallest_candidates():
    a = ev.analyse(ev.Settings(m=4, k=2, ballots="\n".join(["A B C D"] * 4)))
    assert all(a.results[r].committee == frozenset({0, 1}) for r in ev.RULES)


# --- App: Adresszeile und eigene Eingaben ------------------------------------------------------------------------------------------------------

def _run(**params):
    at = AppTest.from_file(APP, default_timeout=180)
    for key, value in params.items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_permalink_with_ballots_fills_the_text_area_and_disables_the_generator():
    at = _run(ballots="A B C\nD\nA D", k="2", m="4", rule="av")
    assert at.sidebar.text_area(key="ballots_text").value.count("\n") == 2
    assert at.sidebar.slider(key="n_slider").proto.disabled and at.sidebar.selectbox(key="model_select").disabled and at.sidebar.slider(key="cohesion_slider").proto.disabled
    assert at.metric[0].label == "Ausschuss (Zustimmungswahl)" and at.metric[0].value == "A, D"


def test_permalink_values_are_clamped_and_bad_values_ignored():
    at = _run(n="999", m="1", k="x", model="nichts", rule="kuchen", seed="-3")
    assert at.sidebar.slider(key="n_slider").value == C.N_MAX and at.sidebar.slider(key="m_slider").value == C.M_MIN
    assert at.sidebar.slider(key="k_slider").value == C.DEFAULT_K and at.sidebar.selectbox(key="model_select").value == C.DEFAULT_MODEL
    assert at.sidebar.selectbox(key="rule_select").value == C.DEFAULT_RULE and at.sidebar.number_input(key="seed_input").value == 0


def test_bad_ballots_show_a_warning_and_the_app_still_runs():
    at = _run(ballots="A\nQ")
    assert any("Eigene Stimmzettel" in w.value for w in at.warning) and not at.sidebar.slider(key="n_slider").proto.disabled


def test_k_larger_than_m_shows_a_note_and_runs():
    at = _run(m="3", k="6")
    assert any("Es gibt nur 3 Kandidaten" in i.value for i in at.info)


def test_counterexample_is_shown_for_the_selected_rule():
    at = _run(ballots="\n".join(["A B C"] * 6 + ["D"] * 3), m="4", k="3", rule="av")
    assert any("Gegenbeispiel zur erweiterten gerechtfertigten Repräsentation bei Zustimmungswahl" in e.value for e in at.error)
    ok = _run(ballots="\n".join(["A B C"] * 6 + ["D"] * 3), m="4", k="3", rule="pav")
    assert not ok.error


def test_changing_the_sliders_keeps_the_app_running():
    at = _run()
    for key, value in (("k_slider", 1), ("m_slider", 12), ("n_slider", 2), ("n_slider", 40), ("cohesion_slider", 30)):
        at.sidebar.slider(key=key).set_value(value).run()
        assert not at.exception
