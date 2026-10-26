"""Kern von Hand gerechnet: Summen, die sieben Regeln, Preise von Equal Shares, JR und EJR, Eingabeprüfung."""

from fractions import Fraction as F

import pytest
from conftest import fs, letters

import kom_algorithm as A

# --- Summen -----------------------------------------------------------------------------------------------------------------------------------

def test_harmonic_numbers():
    assert [A.harmonic(c) for c in range(5)] == [0, 1, F(3, 2), F(11, 6), F(25, 12)]


def test_pav_and_cc_scores_by_hand(mini):
    assert A.pav_score(mini, {0, 1, 2}) == 11 and A.pav_score(mini, {0, 1, 3}) == 12 and A.pav_score(mini, set()) == 0
    assert A.cc_score(mini, {0, 1, 2}) == 6 and A.cc_score(mini, {0, 1, 3}) == 9 and A.cc_score(mini, {3}) == 3
    assert A.coverage(mini, [0]) == 6 and A.satisfaction(mini, {0, 1, 3}) == F(6 * 2 + 3, 9)


def test_approval_counts(mini):
    assert A.approval_counts(mini, 4) == [6, 6, 6, 3] and A.approval_counts(fs("A", "AB"), 3) == [2, 1, 0]


# --- Die Regeln ---------------------------------------------------------------------------------------------------------------------------------

def test_approval_voting_takes_the_three_most_named(mini):
    assert letters(A.av_committee(mini, 4, 3)) == "ABC"
    assert letters(A.av_committee(fs("B", "B", "A", "C"), 3, 1)) == "B"
    assert letters(A.av_committee(fs("A", "B", "C"), 3, 2)) == "AB"                         # Gleichstand: kleinere Buchstaben


def test_pav_rules_find_the_minority_seat(mini):
    assert letters(A.exact_committee(mini, 4, 3, "pav")) == "ABD"                           # 12 gegen 11; unter den gleich guten ABD, ACD, BCD der lexikografisch kleinste
    assert letters(A.greedy_committee(mini, 4, 3, "pav")) == "ABD"                          # A (6), dann B (3, Gleichstand mit C und D: B), dann D (3 gegen C: 6/3 = 2)


def test_cc_rules_cover_everyone(mini):
    assert letters(A.exact_committee(mini, 4, 3, "cc")) == "ABD" and A.cc_score(mini, A.exact_committee(mini, 4, 3, "cc")) == 9
    assert letters(A.greedy_committee(mini, 4, 3, "cc")) == "ABD"


def test_greedy_chamberlin_courant_misses_the_best_committee():
    """Acht Wähler, zwei Sitze. A hat 5 Unterstützer (Wähler 1, 3, 6, 7, 8), B 4, C 4, D 1: gierig A; dann haben die Wähler 2, 4 (B) und 5 (C) keinen Vertreter, B gewinnt 2, C nur 1: {A, B} vertritt 7.
    {B, C} vertritt alle 8 (Wähler 1: B, 3: C, 5: C, 8: C)."""
    b = fs("AB", "B", "AC", "B", "C", "AB", "AC", "ACD")
    assert letters(A.greedy_committee(b, 4, 2, "cc")) == "AB" and A.cc_score(b, A.greedy_committee(b, 4, 2, "cc")) == 7
    assert letters(A.exact_committee(b, 4, 2, "cc")) == "BC" and A.cc_score(b, A.exact_committee(b, 4, 2, "cc")) == 8


def test_chamberlin_courant_gives_the_spare_seat_to_the_smallest_candidate():
    b = fs("BC", "BC", "BC")
    assert letters(A.exact_committee(b, 3, 2, "cc")) == "AB"                                # A, die niemand will, aber der kleinere Buchstabe bei gleicher Abdeckung
    assert letters(A.exact_committee(b, 3, 2, "pav")) == "BC"                               # PAV: 3 · 3/2 = 4,5 gegen 3


def test_greedy_picks_the_smallest_candidate_among_equal_gains():
    assert letters(A.greedy_committee(fs("B", "AB", "AC", "C"), 3, 2, "pav")) == "AB"        # alle drei Kandidaten haben zwei Zustimmungen: A zuerst (PAV 3,5), {B, C} wäre 4
    assert A.pav_score(fs("B", "AB", "AC", "C"), {1, 2}) == 4 and A.pav_score(fs("B", "AB", "AC", "C"), {0, 1}) == F(7, 2)


# --- Equal Shares -------------------------------------------------------------------------------------------------------------------------------

def test_min_price_by_hand():
    assert A.min_price([F(1, 2), F(1, 2)]) == F(1, 2)                                       # genau 1 zusammen: jeder zahlt die Hälfte
    assert A.min_price([F(1, 10), F(1)]) == F(9, 10)                                        # der Arme zahlt alles (1/10), der Reiche den Rest
    assert A.min_price([F(1, 3)] * 3) == F(1, 3) and A.min_price([F(1, 4)] * 3) is None
    assert A.min_price([F(2)]) == 1 and A.min_price([]) is None
    assert A.min_price([F(1, 5), F(2, 5), F(2, 5)]) == F(2, 5)                              # der Ärmste zahlt 1/5, die beiden anderen teilen den Rest je 2/5


def test_min_price_sums_to_exactly_one():
    for budgets in ([F(1, 10), F(1)], [F(1, 7), F(2, 7), F(5, 7)], [F(3, 8)] * 4):
        rho = A.min_price(budgets)
        assert sum(min(rho, b) for b in budgets) == 1


def test_equal_shares_nobody_can_pay_alone():
    b = fs("A", "B", "C", "D")
    trace = []
    assert A.equal_shares(b, 4, 2, trace=trace) == frozenset() and trace == []                # jeder hat 1/2, ein Sitz kostet 1
    trace = []
    assert letters(A.equal_shares(b, 4, 2, fill=True, trace=trace)) == "AB" and trace == [(0, None), (1, None)]


def test_equal_shares_pairs_pay_together():
    trace = []
    w = A.equal_shares(fs("A", "A", "B", "B"), 2, 2, trace=trace)
    assert letters(w) == "AB" and trace == [(0, F(1, 2)), (1, F(1, 2))]                       # je zwei Wähler mit 1/2 zahlen zusammen 1


def test_equal_shares_leaves_a_seat_free_after_a_shared_voter_paid():
    """Fünf Wähler, zwei Sitze, Budget 2/5. A: Wähler 1, 2, 3 (Preis 1/3 je Kopf); B: Wähler 3, 4, 5. Nach A hat Wähler 3 nur noch 2/5 − 1/3 = 1/15; B-Unterstützer haben 1/15 + 2/5 + 2/5 = 13/15 < 1."""
    b = fs("A", "A", "AB", "B", "B")
    trace = []
    w = A.equal_shares(b, 2, 2, trace=trace)
    assert letters(w) == "A" and trace == [(0, F(1, 3))]
    assert letters(A.equal_shares(b, 2, 2, fill=True)) == "AB"


def test_equal_shares_picks_the_cheapest_candidate_first():
    """Vier Wähler, zwei Sitze, Budget 1/2. A: Wähler 1, 2 (zusammen 1, Preis 1/2 je Kopf); B: Wähler 2, 3, 4 (zusammen 3/2, Preis 1/3). B ist billiger und kommt zuerst, obwohl A der kleinere Buchstabe ist.
    Danach hat Wähler 2 nur noch 1/6, A hat 1/2 + 1/6 = 2/3 < 1: der zweite Sitz bleibt frei."""
    trace = []
    w = A.equal_shares(fs("A", "AB", "B", "B"), 2, 2, trace=trace)
    assert letters(w) == "B" and trace == [(1, F(1, 3))]


# --- JR und EJR -------------------------------------------------------------------------------------------------------------------------------

def test_jr_and_ejr_violation_by_hand(mini):
    assert A.group_violation(mini, 4, 3, {0, 1, 2}, level=1) == (1, (3,), (6, 7, 8))            # 3 Wähler ≥ 9/3, alle stimmen D zu, keiner hat einen Gewählten
    assert A.group_violation(mini, 4, 3, {0, 1, 2}) == (1, (3,), (6, 7, 8))
    assert A.group_violation(mini, 4, 3, {0, 1, 3}) is None


def test_ejr_level_two_violation_without_a_jr_violation():
    b = fs("BC", "BC", "BC")
    w = frozenset({0, 1})                                                                      # A und B: jeder hat einen Gewählten (JR), aber die Gruppe will zwei von B, C
    assert A.group_violation(b, 3, 2, w, level=1) is None
    assert A.group_violation(b, 3, 2, w) == (2, (1, 2), (0, 1, 2))
    assert A.group_violation(b, 3, 2, w, level=2) == (2, (1, 2), (0, 1, 2))
    assert A.group_violation(b, 3, 2, {1, 2}) is None


def test_group_needs_enough_voters():
    b = fs("D", "ABC", "ABC", "ABC", "ABC")                                                   # eine Einzelne unter fünf, k = 3: 1 < 5/3, keine Berechtigung
    assert A.group_violation(b, 4, 3, {0, 1, 2}, level=1) is None
    assert A.group_violation(fs("D", "D", "ABC", "ABC", "ABC"), 4, 3, {0, 1, 2}, level=1) == (1, (3,), (0, 1))     # zwei von fünf ≥ 5/3


def test_witness_is_ordered_by_level_then_lexicographically():
    b = fs("AB", "AB", "CD", "CD")
    w = frozenset()                                                                            # leerer Ausschuss: jede berechtigte Gruppe ist ein Gegenbeispiel
    assert A.group_violation(b, 4, 2, w) == (1, (0,), (0, 1))


# --- Eingabeprüfung ---------------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("rule", A.RULE_NAMES)
def test_invalid_input_raises(rule):
    for ballots, m, k in (([], 3, 1), (fs("A"), 3, 0), (fs("A"), 3, 4), (fs("A"), 0, 1), ([frozenset({5})], 3, 1), ([frozenset({3})], 3, 1), ([frozenset({-1})], 3, 1)):
        with pytest.raises(ValueError):
            A.committee(rule, ballots, m, k)


def test_unknown_rule_and_kind_raise():
    with pytest.raises(ValueError):
        A.committee("dhondt", fs("A", "B"), 2, 1)
    with pytest.raises(ValueError):
        A.greedy_committee(fs("A", "B"), 2, 1, "xyz")
    with pytest.raises(ValueError):
        A.exact_committee(fs("A", "B"), 2, 1, "xyz")


def test_dispatch_matches_the_direct_functions(mini):
    assert A.committee("av", mini, 4, 3) == A.av_committee(mini, 4, 3) and A.committee("pav", mini, 4, 3) == A.exact_committee(mini, 4, 3, "pav")
    assert A.committee("seqcc", mini, 4, 3) == A.greedy_committee(mini, 4, 3, "cc") and A.committee("es", mini, 4, 3) == A.equal_shares(mini, 4, 3)
    assert A.committee("esfill", mini, 4, 3) == A.equal_shares(mini, 4, 3, fill=True)


def test_all_rules_pick_the_whole_slate_when_k_equals_m():
    for rule in A.RULE_NAMES:
        if rule != "es":
            assert letters(A.committee(rule, fs("AB", "C", "A"), 3, 3)) == "ABC", rule
    # Equal Shares: Budget 1 je Wähler. A (Wähler 1, 3) kostet je 1/2 und kommt zuerst; dann hat Wähler 1 nur noch 1/2, B (nur Wähler 1) ist nicht bezahlbar; C (Wähler 2) kostet 1: gewählt A und C
    assert letters(A.committee("es", fs("AB", "C", "A"), 3, 3)) == "AC"


@pytest.mark.parametrize("rule", A.RULE_NAMES)
def test_one_candidate_and_one_seat(rule):
    # Equal Shares: bei drei Wählern hat jeder 1/3, zwei Unterstützer bringen nur 2/3 auf; der Sitz bleibt frei
    assert letters(A.committee(rule, fs("A", "A", "-"), 1, 1)) == ("" if rule == "es" else "A") and A.committee(rule, fs("A", "A"), 1, 1) == frozenset({0})
    assert A.committee(rule, fs("A", "A"), 3, 1) == frozenset({0})                              # ein Kandidat von drei, ein Sitz


def test_voters_without_approvals_are_allowed():
    b = fs("A", "-", "A")
    assert letters(A.committee("pav", b, 2, 1)) == "A" and A.coverage(b, {0}) == 2
