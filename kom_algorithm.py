"""Kern: Komitee-Wahl mit Zustimmungsstimmen. Es gibt n Wähler, m Kandidaten (0 bis m − 1) und k Sitze; jeder Wähler stimmt einer Menge von Kandidaten zu (`ballots[i]`, eine frozenset).

Alle Rechnungen sind EXAKT (ganze Zahlen und `fractions.Fraction`). Gleichstände entscheidet der kleinere Kandidat: die gierigen Regeln nehmen den kleinsten Kandidaten unter den besten,
die exakten Regeln (alle C(m, k) Ausschüsse werden aufgezählt) den lexikografisch kleinsten unter den besten, Equal Shares den kleinsten Kandidaten unter den günstigsten."""

import itertools
from fractions import Fraction

RULE_NAMES = ("av", "seqpav", "pav", "seqcc", "cc", "es", "esfill")


def check_input(ballots, m: int, k: int) -> None:
    if not ballots:
        raise ValueError("Es braucht mindestens einen Wähler")
    if not 1 <= k <= m:
        raise ValueError("Es muss 1 ≤ k ≤ m gelten")
    if any(c < 0 or c >= m for b in ballots for c in b):
        raise ValueError("Kandidaten müssen zwischen 0 und m − 1 liegen")


def harmonic(c: int) -> Fraction:
    return sum((Fraction(1, j) for j in range(1, c + 1)), Fraction(0))


def approval_counts(ballots, m: int) -> list:
    return [sum(1 for b in ballots if c in b) for c in range(m)]


def pav_score(ballots, committee) -> Fraction:
    """Summe über alle Wähler von 1 + 1/2 + … + 1/(Zahl der zugestimmten Gewählten)."""
    w = frozenset(committee)
    return sum((harmonic(len(b & w)) for b in ballots), Fraction(0))


def cc_score(ballots, committee) -> int:
    """Zahl der Wähler mit mindestens einem zugestimmten Gewählten."""
    w = frozenset(committee)
    return sum(1 for b in ballots if b & w)


def av_committee(ballots, m: int, k: int) -> frozenset:
    """Zustimmungswahl: die k am häufigsten genannten Kandidaten."""
    check_input(ballots, m, k)
    counts = approval_counts(ballots, m)
    return frozenset(sorted(range(m), key=lambda c: (-counts[c], c))[:k])


def greedy_committee(ballots, m: int, k: int, kind: str) -> frozenset:
    """Gierig Sitz für Sitz: der Kandidat mit dem größten Zuwachs. kind „pav“: Zuwachs = Summe von 1/(bisherige Treffer + 1) über seine Unterstützer; kind „cc“: Zahl seiner noch nicht vertretenen Unterstützer."""
    check_input(ballots, m, k)
    if kind not in ("pav", "cc"):
        raise ValueError(kind)
    chosen = set()
    for _ in range(k):
        best = None
        for c in range(m):
            if c in chosen:
                continue
            if kind == "pav":
                gain = sum((Fraction(1, len(b & chosen) + 1) for b in ballots if c in b), Fraction(0))
            else:
                gain = sum(1 for b in ballots if c in b and not b & chosen)
            if best is None or gain > best[0]:
                best = (gain, c)
        chosen.add(best[1])
    return frozenset(chosen)


def exact_committee(ballots, m: int, k: int, kind: str) -> frozenset:
    """Der beste Ausschuss nach PAV-Summe (kind „pav“) oder Abdeckung (kind „cc“), durch Aufzählung aller C(m, k) Ausschüsse; Gleichstand: lexikografisch kleinster."""
    check_input(ballots, m, k)
    if kind not in ("pav", "cc"):
        raise ValueError(kind)
    score = pav_score if kind == "pav" else cc_score
    best, arg = None, None
    for w in itertools.combinations(range(m), k):
        s = score(ballots, w)
        if best is None or s > best:
            best, arg = s, w
    return frozenset(arg)


def min_price(budgets) -> Fraction:
    """Der kleinste Preis ρ, bei dem die Unterstützer mit den Budgets `budgets` zusammen genau 1 aufbringen (jeder zahlt min(ρ, sein Budget)); None, wenn ihre Budgets zusammen unter 1 liegen."""
    if sum(budgets, Fraction(0)) < 1:
        return None
    paid = Fraction(0)
    ordered = sorted(budgets)
    for idx, b in enumerate(ordered):
        rho = (1 - paid) / (len(ordered) - idx)
        if rho <= b:
            return rho
        paid += b
    raise AssertionError("unerreichbar: die Summe der Budgets ist mindestens 1")


def equal_shares(ballots, m: int, k: int, fill: bool = False, trace=None) -> frozenset:
    """Methode gleicher Anteile (Rule X) für Ausschüsse: jeder Wähler hat das Budget k/n, ein Kandidat kostet 1. In jeder Runde wird der Kandidat gewählt, dessen Unterstützer den kleinsten gleichen Preis ρ je Kopf
    (höchstens ihr Rest) aufbringen; es endet, wenn kein Kandidat mehr bezahlbar ist. Dann kann der Ausschuss kleiner als k bleiben; mit `fill` werden die freien Sitze nach Zustimmungszahl aufgefüllt.
    `trace` bekommt je gewähltem Kandidaten (Kandidat, ρ) und beim Auffüllen (Kandidat, None)."""
    check_input(ballots, m, k)
    n = len(ballots)
    budget = [Fraction(k, n)] * n
    chosen = set()
    while len(chosen) < k:
        best = None
        for c in range(m):
            if c in chosen:
                continue
            supporters = [i for i in range(n) if c in ballots[i]]
            rho = min_price([budget[i] for i in supporters])
            if rho is not None and (best is None or rho < best[0]):
                best = (rho, c, supporters)
        if best is None:
            break
        rho, c, supporters = best
        for i in supporters:
            budget[i] -= min(rho, budget[i])
        chosen.add(c)
        if trace is not None:
            trace.append((c, rho))
    if fill:
        counts = approval_counts(ballots, m)
        for c in sorted(range(m), key=lambda c: (-counts[c], c)):
            if len(chosen) >= k:
                break
            if c not in chosen:
                chosen.add(c)
                if trace is not None:
                    trace.append((c, None))
    return frozenset(chosen)


def committee(rule: str, ballots, m: int, k: int) -> frozenset:
    if rule == "av":
        return av_committee(ballots, m, k)
    if rule == "seqpav":
        return greedy_committee(ballots, m, k, "pav")
    if rule == "pav":
        return exact_committee(ballots, m, k, "pav")
    if rule == "seqcc":
        return greedy_committee(ballots, m, k, "cc")
    if rule == "cc":
        return exact_committee(ballots, m, k, "cc")
    if rule == "es":
        return equal_shares(ballots, m, k)
    if rule == "esfill":
        return equal_shares(ballots, m, k, fill=True)
    raise ValueError(rule)


def group_violation(ballots, m: int, k: int, committee_, level=None):
    """Erweiterte gerechtfertigte Repräsentation (EJR): für jede Stufe ℓ (1 bis k) darf es keine Gruppe von mindestens ℓ·n/k Wählern geben, die ℓ Kandidaten gemeinsam zustimmen und von denen jeder weniger als ℓ
    Gewählte gutheißt (die Gruppe darf also nur aus Unterstützern von T bestehen, die zu kurz kommen). Mit `level` wird nur diese Stufe geprüft (ℓ = 1 ist die gerechtfertigte Repräsentation JR). Rückgabe: None oder das erste Gegenbeispiel (ℓ, Kandidaten T, Wähler S),
    geordnet nach ℓ und dann lexikografisch nach T; S sind alle Unterstützer von T mit weniger als ℓ Gewählten. Die Unterstützer von T sind der Durchschnitt der Unterstützermengen (als Bitmasken);
    Mengen mit zu wenig Unterstützern werden samt Erweiterungen übersprungen (die Unterstützer werden nur weniger)."""
    check_input(ballots, m, k)
    n = len(ballots)
    w = frozenset(committee_)
    hits = [len(b & w) for b in ballots]
    support = [sum(1 << i for i, b in enumerate(ballots) if c in b) for c in range(m)]

    def search(start, chosen, mask, lv):
        if len(chosen) == lv:
            short = [i for i in range(n) if mask >> i & 1 and hits[i] < lv]               # Unterstützer von T mit weniger als ℓ Gewählten: die größte Gruppe, die zu kurz kommt
            return (lv, tuple(chosen), tuple(short)) if len(short) * k >= lv * n else None
        for c in range(start, m):
            sub = mask & support[c]
            if bin(sub).count("1") * k >= lv * n:
                found = search(c + 1, chosen + [c], sub, lv)
                if found:
                    return found
        return None

    full = (1 << n) - 1
    for lv in ([level] if level else range(1, k + 1)):
        found = search(0, [], full, lv)
        if found:
            return found
    return None


def coverage(ballots, committee_) -> int:
    return cc_score(ballots, committee_)


def satisfaction(ballots, committee_) -> Fraction:
    """Mittlere Zahl der zugestimmten Gewählten je Wähler."""
    w = frozenset(committee_)
    return Fraction(sum(len(b & w) for b in ballots), len(ballots))
