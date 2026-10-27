"""Zahlen der README (Befunde): jede dort genannte Zahl steht hier als Behauptung, gerechnet mit den festen Zufalls-Seeds der Reihen."""

import pytest

import kom_constants as C
import kom_evaluation as ev


@pytest.fixture(scope="module")
def violations():
    return ev.series_violations()


@pytest.fixture(scope="module")
def greedy():
    return ev.series_greedy()


@pytest.fixture(scope="module")
def examples():
    return ev.series_examples()


def row(rows, **kw):
    return next(r for r in rows if all(r[k] == v for k, v in kw.items()))


# --- Reihe 1: Verletzungen und Abdeckung --------------------------------------------------------------------------------------------------------

def test_jr_and_ejr_violation_counts(violations):
    expected = {("zwei", "av"): 56, ("drei", "av"): 6}
    for r in violations:
        want = expected.get((r["model"], r["rule"]), 0)
        assert r["jr"] == want and r["ejr"] == want, (r["model"], r["rule"])                  # JR und EJR fallen hier zusammen: es verletzt nur die Zustimmungswahl


def test_coverage_and_pav_share_per_rule_in_the_two_camp_model(violations):
    expected = {  # Regel: (vertretene Wähler, PAV-Summe im Verhältnis zur besten, besetzte Sitze)
        "av": (0.84646, 0.93952, 5.0), "seqpav": (0.98729, 0.99969, 5.0), "pav": (0.98896, 1.0, 5.0), "seqcc": (1.0, 0.97091, 5.0), "cc": (1.0, 0.96561, 5.0),
        "es": (0.96313, 0.87867, 3.83), "esfill": (0.97188, 0.99336, 5.0)}
    for rule, (cov, pav, size) in expected.items():
        r = row(violations, model="zwei", rule=rule)
        assert r["cov_mean"] == pytest.approx(cov, abs=6e-6) and r["pav_mean"] == pytest.approx(pav, abs=6e-6) and r["size_mean"] == pytest.approx(size, abs=6e-3), rule


def test_equal_shares_fills_only_part_of_the_seats(violations):
    sizes = {m: row(violations, model=m, rule="es")["size_mean"] for m in C.MODELS}
    assert sizes == pytest.approx({"zwei": 3.83, "drei": 3.145, "keine": 4.0}) and all(row(violations, model=m, rule="esfill")["size_mean"] == 5.0 for m in C.MODELS)


def test_series_one_verdict_and_table(violations):
    kind, text = ev.verdict_violations(violations)
    assert text == ("Über 600 Instanzen (24 Wähler, 10 Kandidaten, 5 Sitze): EJR verletzt Zustimmungswahl in 10,3 %, Chamberlin–Courant in 0,0 %, Seq. CC in 0,0 %; "
                    "JR verletzt nur die Zustimmungswahl (10,3 %). Ohne EJR-Verletzung blieben in diesen Instanzen: Seq. PAV, PAV, Seq. CC, Chamberlin–Courant, Equal Shares und Equal Shares + Auffüllen.")
    t = ev.violation_table(violations)
    assert t[0] == {"Lager": "Zwei Lager", "Regel": "Zustimmungswahl", "JR verletzt": "56 von 200", "EJR verletzt": "56 von 200", "vertretene Wähler": "84,6 %", "PAV-Summe (Anteil am besten)": "93,95 %", "besetzte Sitze": "5,00"}
    assert t[5]["besetzte Sitze"] == "3,83" and t[12]["besetzte Sitze"] == "3,15" and t[7]["JR verletzt"] == "6 von 200"


# --- Reihe 2: gierig gegen exakt ----------------------------------------------------------------------------------------------------------------

def test_greedy_against_exact(greedy):
    expected = {  # Sitze: (PAV Mittel, PAV schlechtester, PAV gleich, CC Mittel, CC schlechtester, CC gleich)
        3: (0.998855, 0.97175, 180, 0.989881, 0.91667, 155), 4: (0.999282, 0.9697, 180, 0.996667, 0.95833, 184),
        5: (0.999664, 0.98847, 186, 0.999792, 0.95833, 199), 6: (0.999872, 0.99553, 188, 1.0, 1.0, 200)}
    for k, (pm, pn, pe, cm, cn, ce) in expected.items():
        r = row(greedy, k=k)
        assert r["pav_mean"] == pytest.approx(pm, abs=2e-6) and r["pav_min"] == pytest.approx(pn, abs=2e-5) and r["pav_equal"] == pe
        assert r["cc_mean"] == pytest.approx(cm, abs=2e-6) and r["cc_min"] == pytest.approx(cn, abs=2e-5) and r["cc_equal"] == ce


def test_greedy_is_never_better_than_exact_and_improves_with_more_seats(greedy):
    assert all(r["pav_mean"] <= 1 and r["cc_mean"] <= 1 and r["pav_min"] <= 1 and r["cc_min"] <= 1 for r in greedy)
    assert [r["pav_mean"] for r in greedy] == sorted(r["pav_mean"] for r in greedy) and [r["cc_mean"] for r in greedy] == sorted(r["cc_mean"] for r in greedy)


def test_greedy_verdict_and_table(greedy):
    kind, text = ev.verdict_greedy(greedy)
    assert text == ("Über 800 Instanzen erreicht das gierige PAV im Mittel 99,94 % der exakten PAV-Summe (schlechtester Fall 97,0 %, gleich in 734 Instanzen), "
                    "das gierige Chamberlin–Courant 99,66 % der exakten Abdeckung (schlechtester Fall 91,7 %, gleich in 738). Schlechter als die exakte Regel ist die gierige in 66 (PAV) bzw. 62 (Chamberlin–Courant) Instanzen; ob sich die Aufzählung lohnt, hängt vom Rechenaufwand ab.")
    assert ev.greedy_table(greedy)[0] == {"Sitze": 3, "Instanzen": 200, "Seq. PAV: Mittel": "99,89 %", "schlechtester Fall": "97,2 %", "gleich": "180 von 200",
                                          "Seq. CC: Mittel": "98,99 %", "schlechtester Fall ": "91,7 %", "gleich ": "155 von 200"}


# --- Reihe 3: kleinste Gegenbeispiele -------------------------------------------------------------------------------------------------------------

def test_small_instances(examples):
    got = {r["rule"]: (r["jr"], r["ejr"]) for r in examples}
    assert got == {"av": (16, 16), "seqpav": (0, 0), "pav": (0, 0), "seqcc": (0, 20), "cc": (0, 27), "es": (0, 0), "esfill": (0, 0)}
    assert all(r["runs"] == 4000 for r in examples)


def test_smallest_examples(examples):
    assert row(examples, rule="av")["size"] == (12, 3, 4, 3) and row(examples, rule="av")["example"] == "ABD | C | D (k = 3); gewählt: A, B, D"
    assert row(examples, rule="cc")["size"] == (9, 3, 3, 2) and row(examples, rule="cc")["example"] == "AC | AC | AC (k = 2); gewählt: A, B"
    assert row(examples, rule="seqcc")["example"] == row(examples, rule="cc")["example"] and row(examples, rule="pav")["example"] is None


def test_small_instance_verdict(examples):
    kind, text = ev.verdict_examples(examples)
    assert text == ("In 4.000 kleinen Zufallsinstanzen verletzen EJR: Zustimmungswahl, Seq. CC und Chamberlin–Courant; nie verletzt wurde es von Seq. PAV, PAV, Equal Shares und Equal Shares + Auffüllen. "
                    "Die kleinsten gefundenen Gegenbeispiele stehen in der Tabelle.")


def test_the_examples_really_violate(examples):
    """Jedes in der Tabelle genannte Gegenbeispiel wird aus dem Text neu gelesen (Stimmzettel, Sitze, gewählter Ausschuss) und mit der Gruppenprüfung geprüft."""
    import kom_algorithm as A
    import kom_scenario as S

    checked = 0
    for r in examples:
        if r["example"] is None:
            continue
        ballot_part, rest = r["example"].split(" (k = ")
        k = int(rest.split(")")[0])
        chosen = [C.LETTERS.index(t.strip()) for t in rest.split("gewählt:")[1].split(",")]
        ballots, err = S.parse_ballots(C.NL.join(ballot_part.split(" | ")), 12)
        assert err is None and len(chosen) == k
        m = max(c for b in ballots for c in b | frozenset(chosen)) + 1
        assert A.group_violation(ballots, m, k, frozenset(chosen)) is not None
        assert A.committee(r["rule"], ballots, m, k) == frozenset(chosen)                  # und die Regel wählt tatsächlich diesen Ausschuss
        checked += 1
    assert checked == 3


def test_series_are_deterministic(violations, greedy, examples):
    assert ev.series_examples() == examples
