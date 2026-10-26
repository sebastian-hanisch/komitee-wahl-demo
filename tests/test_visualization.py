"""Abbildungen: Aufbau, gesperrte Achsen, Werte an der Hand-Analyse."""

import pytest

import kom_constants as C
import kom_evaluation as ev
import kom_visualization as V


def locked(fig):
    return all(ax.fixedrange for ax in fig.select_xaxes()) and all(ax.fixedrange for ax in fig.select_yaxes())


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_ballot_grid_marks_approvals_and_the_committee():
    a = analyse("Zustimmungswahl übergeht eine Minderheit")
    fig = V.build_ballots(a, "av")
    z = fig.data[0].z
    assert len(z) == 10 and list(z[0]) == [1, 1, 1, 0] and list(z[6]) == [0, 0, 0, 1] and list(z[9]) == [2, 2, 2, 0]         # sechs Wähler ABC, drei D, der Ausschuss A, B, C
    assert list(fig.data[0].x) == ["A", "B", "C", "D"] and fig.data[0].y[-1] == "Ausschuss (Zustimmungswahl)" and fig.layout.yaxis.autorange == "reversed" and locked(fig)
    assert list(V.build_ballots(a, "pav").data[0].z[9]) == [2, 2, 0, 2]


def test_coverage_figure_has_one_bar_and_one_diamond_per_rule():
    a = analyse("Zustimmungswahl übergeht eine Minderheit")
    fig = V.build_coverage(a)
    assert list(fig.data[0].x) == [C.RULE_SHORT[r] for r in ev.RULES]
    assert list(fig.data[0].y) == pytest.approx([6 / 9] + [1.0] * 6)
    assert fig.data[1].y[0] == pytest.approx(11 / 12) and fig.data[1].y[2] == pytest.approx(1.0) and locked(fig)


def test_camp_figure_stacks_the_seats_next_to_the_proportional_column():
    a = analyse("Zwei Lager, fünf Sitze")
    fig = V.build_camps(a)
    assert [t.name for t in fig.data] == ["Lager 1 (17 Wähler)", "Lager 2 (7 Wähler)"] and fig.layout.barmode == "stack"
    assert list(fig.data[0].x)[0] == "Anteil der Wähler × Sitze" and fig.data[0].y[0] == pytest.approx(17 / 24 * 5) and fig.data[1].y[0] == pytest.approx(7 / 24 * 5)
    assert list(fig.data[0].y)[1:] == [5, 4, 4, 4, 4, 2, 4] and list(fig.data[1].y)[1:] == [0, 1, 1, 1, 1, 1, 1] and locked(fig)


def _violation_rows():
    return [{"model": m, "rule": r, "runs": 100, "jr": 0, "ejr": 3 if r == "av" else 0, "cov_mean": 0.9, "pav_mean": 0.95, "size_mean": 3.5 if r == "es" else 5.0} for m in C.MODELS for r in ev.RULES]


def test_violation_series_figure():
    fig = V.build_violation_series(_violation_rows())
    assert [t.name for t in fig.data] == ["Zwei Lager", "Drei Lager", "Keine Lager"] and list(fig.data[0].x) == [C.RULE_SHORT[r] for r in ev.RULES]
    assert list(fig.data[0].y) == pytest.approx([0.03] + [0.0] * 6) and fig.layout.yaxis.tickformat == ".0%" and locked(fig)


def test_size_series_figure():
    fig = V.build_size_series(_violation_rows())
    assert [t.name for t in fig.data] == ["Equal Shares", "Equal Shares + Auffüllen"] and list(fig.data[0].y) == [3.5] * 3 and list(fig.data[1].y) == [5.0] * 3
    assert list(fig.data[0].x) == ["Zwei Lager", "Drei Lager", "Keine Lager"] and tuple(fig.layout.yaxis.range)[0] == 0 and locked(fig)


def test_greedy_series_figure():
    rows = [{"k": k, "runs": 10, "pav_mean": 0.999, "pav_min": 0.97, "pav_equal": 9, "cc_mean": 0.99, "cc_min": 0.9, "cc_equal": 8} for k in C.SERIES_KS]
    fig = V.build_greedy_series(rows)
    assert [t.name for t in fig.data] == ["Seq. PAV gegen PAV: Mittel", "Seq. PAV gegen PAV: schlechtester Fall", "Seq. CC gegen CC: Mittel", "Seq. CC gegen CC: schlechtester Fall"]
    assert list(fig.data[0].x) == ["3 Sitze", "4 Sitze", "5 Sitze", "6 Sitze"] and list(fig.data[3].y) == [0.9] * 4 and locked(fig)
