"""Orakel (DEMO-PLAYBOOK §12): unabhängige Gegenrechnungen.

- PAV und Chamberlin–Courant: **ganzzahlige lineare Programme** (scipy.optimize.milp) gegen die Aufzählung aller Ausschüsse.
- JR und EJR: Aufzählung ALLER Wählergruppen (Teilmengen der Wähler) gegen die Suche über Kandidatenmengen, geprüft an jedem möglichen Ausschuss kleiner Instanzen.
- Equal Shares: Preis nach der Definition (Halbierung), Zahlungen summieren sich je Sitz auf genau 1, kein negatives Budget.
- Sätze der Literatur als Eigenschaften über Zufallsinstanzen: PAV und Equal Shares erfüllen EJR, Chamberlin–Courant erfüllt JR, die gierige Abdeckung erreicht mindestens 1 − 1/e."""

import itertools
import math
import random
from fractions import Fraction as F

import numpy as np
import pytest
from scipy.optimize import LinearConstraint, milp

import kom_algorithm as A


def random_ballots(rng, n, m, p=0.45):
    return [frozenset(c for c in range(m) if rng.random() < p) for _ in range(n)]


# --- ILP-Orakel -------------------------------------------------------------------------------------------------------------------------------

def ilp_pav(ballots, m, k):
    """Variablen: x_c (Kandidat gewählt) und y_ij (Wähler i hat mindestens j Gewählte, j = 1 bis m); y_ij ≤ y_i,j−1; Σ_j y_ij = Σ_{c ∈ A_i} x_c. Zielwert Σ_i Σ_j y_ij / j."""
    n = len(ballots)
    nv = m + n * m
    cost = np.zeros(nv)
    for i in range(n):
        for j in range(m):
            cost[m + i * m + j] = -1.0 / (j + 1)
    rows, lo, hi = [], [], []

    def add(row, low, high):
        rows.append(row)
        lo.append(low)
        hi.append(high)

    row = np.zeros(nv)
    row[:m] = 1
    add(row, k, k)
    for i in range(n):
        row = np.zeros(nv)
        for j in range(m):
            row[m + i * m + j] = 1
        for c in ballots[i]:
            row[c] -= 1
        add(row, 0, 0)
        for j in range(1, m):
            row = np.zeros(nv)
            row[m + i * m + j] = 1
            row[m + i * m + j - 1] = -1
            add(row, -np.inf, 0)
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=np.ones(nv), bounds=(0, 1))
    assert res.status == 0
    return -res.fun


def ilp_cc(ballots, m, k):
    n = len(ballots)
    nv = m + n
    cost = np.zeros(nv)
    cost[m:] = -1
    rows, lo, hi = [], [], []

    def add(row, low, high):
        rows.append(row)
        lo.append(low)
        hi.append(high)

    row = np.zeros(nv)
    row[:m] = 1
    add(row, k, k)
    for i in range(n):
        row = np.zeros(nv)
        row[m + i] = 1
        for c in ballots[i]:
            row[c] -= 1
        add(row, -np.inf, 0)
    res = milp(cost, constraints=LinearConstraint(np.array(rows), lo, hi), integrality=np.ones(nv), bounds=(0, 1))
    assert res.status == 0
    return -res.fun


@pytest.mark.parametrize("small", [False, True])
def test_exact_pav_and_cc_match_the_integer_programs(small):
    rng = random.Random(1)
    for _ in range(60):
        n, m = rng.randint(3, 9), rng.randint(3, 7)
        k = rng.randint(1, m)
        ballots = random_ballots(rng, n, m, p=0.25 if small else 0.5)
        assert float(A.pav_score(ballots, A.exact_committee(ballots, m, k, "pav"))) == pytest.approx(ilp_pav(ballots, m, k), abs=1e-7)
        assert A.cc_score(ballots, A.exact_committee(ballots, m, k, "cc")) == pytest.approx(ilp_cc(ballots, m, k), abs=1e-7)


def test_exact_committees_are_lexicographically_first_among_the_optima():
    rng = random.Random(2)
    for _ in range(80):
        n, m, k = rng.randint(3, 8), rng.randint(3, 6), 2
        ballots = random_ballots(rng, n, m)
        for kind, score in (("pav", A.pav_score), ("cc", A.cc_score)):
            chosen = tuple(sorted(A.exact_committee(ballots, m, k, kind)))
            best = max(score(ballots, w) for w in itertools.combinations(range(m), k))
            first = next(w for w in itertools.combinations(range(m), k) if score(ballots, w) == best)
            assert chosen == first


# --- JR und EJR durch Aufzählung aller Gruppen ----------------------------------------------------------------------------------------------

def violation_by_groups(ballots, k, w, level=None):
    """Definition: eine Gruppe S mit |S| ≥ ℓ n / k und mindestens ℓ gemeinsamen Zustimmungen, in der jeder weniger als ℓ Gewählte hat. Alle 2^n Gruppen werden geprüft; Stufen von 1 bis k (oder nur `level`)."""
    n = len(ballots)
    for size in range(1, n + 1):
        for s in itertools.combinations(range(n), size):
            common = frozenset.intersection(*(ballots[i] for i in s))
            for lv in ([level] if level else range(1, k + 1)):
                if size * k >= lv * n and len(common) >= lv and all(len(ballots[i] & w) < lv for i in s):
                    return True
    return False


def test_group_violation_matches_the_enumeration_of_all_groups_for_every_committee():
    rng = random.Random(3)
    checked = flagged = 0
    for _ in range(120):
        n, m, k = rng.randint(2, 7), rng.randint(3, 5), rng.randint(1, 3)
        k = min(k, m)
        ballots = random_ballots(rng, n, m, p=rng.choice([0.3, 0.5, 0.7]))
        for w in itertools.combinations(range(m), k):
            wset = frozenset(w)
            for level in (None, 1):
                found = A.group_violation(ballots, m, k, wset, level=level) is not None
                assert found == violation_by_groups(ballots, k, wset, level), (ballots, k, w, level)
                checked += 1
                flagged += found
    assert flagged > 50 and checked - flagged > 100             # Prüfung nicht leer: sowohl Verletzungen als auch Erfüllungen kommen vor


def test_every_reported_witness_is_a_real_counterexample():
    rng = random.Random(4)
    seen = 0
    for _ in range(1000):
        n, m, k = rng.randint(3, 9), rng.randint(3, 6), rng.randint(2, 3)
        ballots = random_ballots(rng, n, m)
        for rule in ("av", "cc", "seqcc", "zufall"):
            w = frozenset(rng.sample(range(m), k)) if rule == "zufall" else A.committee(rule, ballots, m, k)
            found = A.group_violation(ballots, m, k, w)
            if found:
                lv, t, s = found
                seen += 1
                assert len(t) == lv and len(s) * k >= lv * n
                assert all(set(t) <= ballots[i] and len(ballots[i] & w) < lv for i in s)
                assert set(s) == {i for i in range(n) if set(t) <= ballots[i] and len(ballots[i] & w) < lv}          # alle Unterstützer von T, die zu kurz kommen
    assert seen > 50


# --- Equal Shares nach der Definition -------------------------------------------------------------------------------------------------------

def rho_by_bisection(budgets):
    if sum(budgets) < 1:
        return None
    lo, hi = F(0), max(budgets) if max(budgets) > 0 else F(1)
    hi = max(hi, F(1))
    for _ in range(200):
        mid = (lo + hi) / 2
        if sum(min(mid, b) for b in budgets) >= 1:
            hi = mid
        else:
            lo = mid
    return hi


def test_min_price_matches_the_bisection_and_is_minimal():
    rng = random.Random(5)
    for _ in range(200):
        budgets = [F(rng.randint(0, 20), rng.choice([7, 12, 30])) for _ in range(rng.randint(1, 7))]
        rho = A.min_price(budgets)
        if rho is None:
            assert sum(budgets) < 1
            continue
        assert sum(min(rho, b) for b in budgets) == 1
        assert sum(min(rho - F(1, 10 ** 9), b) for b in budgets) < 1
        assert abs(float(rho) - float(rho_by_bisection(budgets))) < 1e-12


def simulate_payments(ballots, m, k, trace):
    """Wiederholt die Zahlungen eines Ablaufs und prüft: jeder gewählte Kandidat wird zu genau 1 bezahlt, kein Budget wird negativ."""
    n = len(ballots)
    budget = [F(k, n)] * n
    for c, rho in trace:
        if rho is None:
            continue
        paid = F(0)
        for i in range(n):
            if c in ballots[i]:
                pay = min(rho, budget[i])
                budget[i] -= pay
                paid += pay
        assert paid == 1 and min(budget) >= 0
    return budget


def test_equal_shares_payments_add_up_to_exactly_one_per_seat():
    rng = random.Random(6)
    incomplete = 0
    for _ in range(150):
        n, m = rng.randint(3, 12), rng.randint(3, 8)
        k = rng.randint(1, min(5, m))
        ballots = random_ballots(rng, n, m, p=rng.choice([0.2, 0.4]))
        trace = []
        w = A.equal_shares(ballots, m, k, trace=trace)
        assert [c for c, _ in trace] == sorted(w, key=[c for c, _ in trace].index) and len(w) <= k
        left = simulate_payments(ballots, m, k, trace)
        assert sum(left) == F(k) - len(w)                                                    # das Budget k ist um genau einen Sitzpreis je Gewähltem gesunken
        incomplete += len(w) < k
    assert incomplete > 10


def test_equal_shares_with_fill_extends_the_plain_committee_by_approval_counts():
    rng = random.Random(7)
    for _ in range(100):
        n, m = rng.randint(3, 10), rng.randint(3, 7)
        k = rng.randint(1, m)
        ballots = random_ballots(rng, n, m, p=0.3)
        plain = A.equal_shares(ballots, m, k)
        filled = A.equal_shares(ballots, m, k, fill=True)
        assert plain <= filled and len(filled) == k
        counts = A.approval_counts(ballots, m)
        extra = sorted(filled - plain)
        rest = sorted((c for c in range(m) if c not in plain), key=lambda c: (-counts[c], c))[: k - len(plain)]
        assert extra == sorted(rest)


# --- Sätze über Zufallsinstanzen ----------------------------------------------------------------------------------------------------------------

def test_pav_and_equal_shares_satisfy_ejr_and_chamberlin_courant_satisfies_jr():
    rng = random.Random(8)
    for _ in range(250):
        n, m = rng.randint(3, 10), rng.randint(3, 6)
        k = rng.randint(1, min(4, m))
        ballots = random_ballots(rng, n, m, p=rng.choice([0.25, 0.45]))
        assert A.group_violation(ballots, m, k, A.committee("pav", ballots, m, k)) is None
        assert A.group_violation(ballots, m, k, A.committee("es", ballots, m, k)) is None
        assert A.group_violation(ballots, m, k, A.committee("esfill", ballots, m, k)) is None
        assert A.group_violation(ballots, m, k, A.committee("cc", ballots, m, k), level=1) is None


def test_approval_voting_and_chamberlin_courant_do_fail_somewhere():
    rng = random.Random(9)
    av_jr = cc_ejr = 0
    for _ in range(1500):
        n, m = rng.randint(3, 8), rng.randint(3, 6)
        k = rng.randint(2, min(4, m - 1))
        ballots = random_ballots(rng, n, m)
        av_jr += A.group_violation(ballots, m, k, A.committee("av", ballots, m, k), level=1) is not None
        cc_ejr += A.group_violation(ballots, m, k, A.committee("cc", ballots, m, k)) is not None
    assert av_jr > 0 and cc_ejr > 0


def test_exact_rules_dominate_every_other_committee_on_their_own_score():
    rng = random.Random(10)
    for _ in range(60):
        n, m, k = rng.randint(3, 9), rng.randint(3, 6), 2
        ballots = random_ballots(rng, n, m)
        comm = {rule: A.committee(rule, ballots, m, k) for rule in A.RULE_NAMES}
        best_pav, best_cc = A.pav_score(ballots, comm["pav"]), A.cc_score(ballots, comm["cc"])
        assert all(A.pav_score(ballots, w) <= best_pav and A.cc_score(ballots, w) <= best_cc for w in comm.values())


def test_greedy_coverage_reaches_one_minus_one_over_e_of_the_optimum():
    rng = random.Random(11)
    worst = 1.0
    for _ in range(150):
        n, m = rng.randint(5, 14), rng.randint(4, 8)
        k = rng.randint(2, min(5, m))
        ballots = random_ballots(rng, n, m, p=0.3)
        opt = A.cc_score(ballots, A.exact_committee(ballots, m, k, "cc"))
        got = A.cc_score(ballots, A.greedy_committee(ballots, m, k, "cc"))
        if opt:
            worst = min(worst, got / opt)
    assert worst >= 1 - 1 / math.e
