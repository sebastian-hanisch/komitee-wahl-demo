"""Auswertung: Einstellungen, Ausschüsse je Regel, Kennzahlen, Tabellen, Verdikte als reine Funktionen (ohne Streamlit) und die festen Reihen."""

import math
import random
from dataclasses import dataclass
from fractions import Fraction

import kom_algorithm as A
import kom_constants as C
import kom_scenario as S

RULES = tuple(C.RULES)


def num(x: float, digits: int = 1) -> str:
    return f"{x:.{digits}f}".replace(".", ",").replace("-", "−")


def pct(x, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.{digits}f} %".replace(".", ",").replace("-", "−")


def cand(c: int) -> str:
    return C.LETTERS[c]


def committee_text(w) -> str:
    return ", ".join(cand(c) for c in sorted(w)) or "(leer)"


def voters_text(voters) -> str:
    return ", ".join(f"Wähler {i + 1}" for i in voters)


def names(rules) -> str:
    short = [C.RULE_SHORT[r] for r in rules]
    if len(short) <= 1:
        return "".join(short)
    return ", ".join(short[:-1]) + " und " + short[-1]


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    k: int = C.DEFAULT_K
    model: str = C.DEFAULT_MODEL
    cohesion: int = C.DEFAULT_COHESION
    cross: int = C.DEFAULT_CROSS
    seed: int = C.DEFAULT_SEED
    rule: str = C.DEFAULT_RULE
    ballots: str = ""


@dataclass
class RuleResult:
    rule: str
    committee: frozenset
    covered: int           # Wähler mit mindestens einem Gewählten
    satisfaction: float    # mittlere Zahl zugestimmter Gewählter je Wähler
    pav: Fraction          # PAV-Summe
    pav_ratio: float       # PAV-Summe / beste PAV-Summe
    jr: object             # None oder (ℓ, T, S)
    ejr: object            # None oder (ℓ, T, S)
    trace: list            # Schritte von Equal Shares: (Kandidat, ρ oder None)
    seats_by_camp: object  # Sitze je Lager (Liste) oder None


@dataclass
class Analysis:
    settings: Settings
    ballots: list
    source: str            # "eingegeben" oder "erzeugt"
    voter_camp: object     # Lager je Wähler oder None (eingegebene Stimmzettel)
    cand_camp: object
    errors: list
    note: str
    n: int
    m: int
    k: int
    results: dict          # Regel -> RuleResult
    best_pav: Fraction
    best_cc: int
    counts: list          # Zustimmungen je Kandidat


def analyse(settings: Settings) -> Analysis:
    errors, note = [], ""
    m, k = settings.m, settings.k
    rows, err = S.parse_ballots(settings.ballots, m)
    if err:
        errors.append("Eigene Stimmzettel: " + err + " Die Eingabe wird ignoriert.")
    if rows is not None:
        ballots, source, vcamp, ccamp = rows, "eingegeben", None, None
    else:
        ballots, vcamp, ccamp = S.make_ballots(settings.model, settings.n, m, settings.cohesion, settings.cross, settings.seed)
        source = "erzeugt"
    if k > m:
        note = f"Es gibt nur {m} Kandidaten, gerechnet wird mit {m} Sitzen statt {k}."
        k = m
    n = len(ballots)
    committees, traces = {}, {}
    for rule in RULES:
        trace = []
        if rule == "es":
            committees[rule] = A.equal_shares(ballots, m, k, trace=trace)
        elif rule == "esfill":
            committees[rule] = A.equal_shares(ballots, m, k, fill=True, trace=trace)
        else:
            committees[rule] = A.committee(rule, ballots, m, k)
        traces[rule] = trace
    best_pav = A.pav_score(ballots, committees["pav"])
    best_cc = A.cc_score(ballots, committees["cc"])
    results = {}
    for rule in RULES:
        w = committees[rule]
        pav = A.pav_score(ballots, w)
        by_camp = None
        if vcamp is not None:
            groups = len(C.MODEL_SHARES[settings.model])
            by_camp = [sum(1 for c in w if ccamp[c] == g) for g in range(groups)]
        results[rule] = RuleResult(
            rule=rule, committee=w, covered=A.coverage(ballots, w), satisfaction=float(A.satisfaction(ballots, w)), pav=pav, pav_ratio=float(pav / best_pav),
            jr=A.group_violation(ballots, m, k, w, level=1), ejr=A.group_violation(ballots, m, k, w), trace=traces[rule], seats_by_camp=by_camp)
    return Analysis(settings=settings, ballots=ballots, source=source, voter_camp=vcamp, cand_camp=ccamp, errors=errors, note=note, n=n, m=m, k=k, results=results,
                    best_pav=best_pav, best_cc=best_cc, counts=A.approval_counts(ballots, m))


# --- Tabellen und Texte ---------------------------------------------------------------------------------------------------------------------

def witness_text(a: Analysis, witness) -> str:
    if witness is None:
        return "keines"
    lv, t, s = witness
    short = "keinen Gewählten" if lv == 1 else f"weniger als {lv} Gewählte"
    return f"{len(s)} von {a.n} Wählern ({voters_text(s)}) stimmen {', '.join(cand(c) for c in t)} zu, aber jeder von ihnen hat {short}"


def committee_rows(a: Analysis) -> list:
    rows = []
    for rule in RULES:
        r = a.results[rule]
        rows.append({
            "Regel": C.RULE_SHORT[rule], "Ausschuss": committee_text(r.committee), "Sitze": f"{len(r.committee)} von {a.k}",
            "Vertretene Wähler": f"{r.covered} von {a.n} ({pct(r.covered / a.n)})", "PAV-Summe": f"{num(float(r.pav), 2)} ({pct(r.pav_ratio)} des besten)",
            "gerechtfertigt (JR)": "ja" if r.jr is None else "nein", "erweitert gerechtfertigt (EJR)": "ja" if r.ejr is None else "nein",
        })
    return rows


def camp_rows(a: Analysis):
    """Sitze je Lager und Regel neben dem Verhältnis der Wähler; None bei eingegebenen Stimmzetteln."""
    if a.voter_camp is None:
        return None
    groups = len(C.MODEL_SHARES[a.settings.model])
    voters = [sum(1 for v in a.voter_camp if v == g) for g in range(groups)]
    rows = [{"Regel": "Anteil der Wähler × Sitze", **{f"Lager {g + 1}": num(voters[g] / a.n * a.k, 1) for g in range(groups)}}]
    for rule in RULES:
        rows.append({"Regel": C.RULE_SHORT[rule], **{f"Lager {g + 1}": str(a.results[rule].seats_by_camp[g]) for g in range(groups)}})
    return rows


def trace_lines(a: Analysis) -> list:
    """Der Ablauf von Equal Shares in Worten."""
    r = a.results["es"]
    lines = [f"Jeder der {a.n} Wähler hat das Budget {a.k}/{a.n}; ein Sitz kostet 1."]
    for c, rho in r.trace:
        lines.append(f"Kandidat {cand(c)} wird gewählt: seine {a.counts[c]} Unterstützer zahlen höchstens {num(float(rho), 3)} je Kopf (der kleinste Preis aller Kandidaten in dieser Runde).")
    if len(r.committee) < a.k:
        lines.append(f"Danach kann kein weiterer Kandidat bezahlt werden. Frei bleiben {a.k - len(r.committee)} von {a.k} Sitzen; Equal Shares mit Auffüllen vergibt sie nach Zustimmungszahl.")
    return lines


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------

def verdict_state(a: Analysis):
    """Kernfrage: wer wird vertreten, und welche Regel verletzt welche Gerechtigkeit? Rückgabe (st-Methode, Text)."""
    jr_bad = [r for r in RULES if a.results[r].jr is not None]
    ejr_bad = [r for r in RULES if a.results[r].ejr is not None]
    parts = []
    parts.append(f"Gerechtfertigte Repräsentation (JR) verletzen: {names(jr_bad) if jr_bad else 'keine Regel'}. Erweiterte (EJR) verletzen: {names(ejr_bad) if ejr_bad else 'keine Regel'}.")
    cov = {r: a.results[r].covered / a.n for r in RULES}
    parts.append(f"Vertretene Wähler: {C.RULE_SHORT['av']} {pct(cov['av'])}, PAV {pct(cov['pav'])}, Chamberlin–Courant {pct(cov['cc'])}.")
    short = a.k - len(a.results["es"].committee)
    if short:
        parts.append(f"Equal Shares besetzt nur {len(a.results['es'].committee)} von {a.k} Sitzen.")
    first = next((r for r in ("av", "cc", "seqcc", "seqpav", "pav", "es", "esfill") if a.results[r].ejr is not None), None)
    if first is not None:
        parts.append(f"Beispiel ({C.RULE_SHORT[first]}): {witness_text(a, a.results[first].ejr)}.")
    return ("warning" if ejr_bad else "success"), " ".join(parts)


def verdict_rule(a: Analysis, rule: str) -> str:
    r = a.results[rule]
    return (f"{C.RULES[rule]}: Ausschuss {committee_text(r.committee)}; {r.covered} von {a.n} Wählern vertreten, PAV-Summe {num(float(r.pav), 2)} ({pct(r.pav_ratio)} des besten); "
            f"JR {'erfüllt' if r.jr is None else 'verletzt'}, EJR {'erfüllt' if r.ejr is None else 'verletzt'}.")


def verdict_violations(rows):
    """Reihe 1: wie oft verletzt eine Regel JR und EJR? Rückgabe (st-Methode, Text)."""
    tot = sum(r["runs"] for r in rows if r["rule"] == "av")
    share = {rule: sum(r["ejr"] for r in rows if r["rule"] == rule) / tot for rule in RULES}
    jr = {rule: sum(r["jr"] for r in rows if r["rule"] == rule) / tot for rule in RULES}
    clean = [rule for rule in RULES if share[rule] == 0]
    text = (f"Über {tot:,} Instanzen".replace(",", ".") + f" (24 Wähler, 10 Kandidaten, 5 Sitze): EJR verletzt {C.RULE_SHORT['av']} in {pct(share['av'])}, Chamberlin–Courant in {pct(share['cc'])}, "
            f"Seq. CC in {pct(share['seqcc'])}; JR verletzt nur die Zustimmungswahl ({pct(jr['av'])}). Nie verletzen EJR: {names(clean)}.")
    return "warning", text


def verdict_greedy(rows):
    """Reihe 2: wie nah kommt die gierige Regel an die exakte? Rückgabe (st-Methode, Text)."""
    runs = sum(r["runs"] for r in rows)
    pav_mean = sum(r["pav_mean"] * r["runs"] for r in rows) / runs
    cc_mean = sum(r["cc_mean"] * r["runs"] for r in rows) / runs
    worst_pav = min(r["pav_min"] for r in rows)
    worst_cc = min(r["cc_min"] for r in rows)
    equal_pav = sum(r["pav_equal"] for r in rows)
    equal_cc = sum(r["cc_equal"] for r in rows)
    text = (f"Über {runs:,} Instanzen".replace(",", ".") + f" erreicht das gierige PAV im Mittel {pct(pav_mean, 2)} der exakten PAV-Summe (schlechtester Fall {pct(worst_pav, 1)}, gleich in {equal_pav} Instanzen), "
            f"das gierige Chamberlin–Courant {pct(cc_mean, 2)} der exakten Abdeckung (schlechtester Fall {pct(worst_cc, 1)}, gleich in {equal_cc}). Die Aufzählung lohnt sich selten.")
    return "info", text


def verdict_examples(rows):
    """Reihe 3: kleinste Gegenbeispiele. Rückgabe (st-Methode, Text)."""
    bad = [r for r in rows if r["ejr"] > 0]
    ok = [r["rule"] for r in rows if r["ejr"] == 0]
    text = (f"In {rows[0]['runs']:,} kleinen Zufallsinstanzen".replace(",", ".") + f" verletzen EJR: {names([r['rule'] for r in bad]) if bad else 'keine Regel'}; nie verletzt wurde es von {names(ok) if ok else 'keiner Regel'}. "
            "Die kleinsten gefundenen Gegenbeispiele stehen in der Tabelle.")
    return "info", text


# --- Feste Reihen ---------------------------------------------------------------------------------------------------------------------------

def _instance(model, n, m, seed):
    return S.make_ballots(model, n, m, C.DEFAULT_COHESION, C.DEFAULT_CROSS, seed)[0]


def _committees(ballots, m, k):
    return {rule: A.committee(rule, ballots, m, k) for rule in RULES}


def series_violations() -> list:
    """Je Lagermodell und Regel: Zahl der Instanzen mit JR- und EJR-Verletzung, mittlere Abdeckung, mittleres Verhältnis zur besten PAV-Summe, mittlere Ausschussgröße."""
    rows = []
    n, m, k = C.SERIES_N, C.SERIES_M, C.SERIES_K
    for mi, model in enumerate(C.MODELS):
        acc = {rule: {"jr": 0, "ejr": 0, "cov": 0.0, "pav": 0.0, "size": 0} for rule in RULES}
        for run in range(C.SERIES_RUNS):
            ballots = _instance(model, n, m, C.SERIES_SEED + 10000 * mi + run)
            comm = _committees(ballots, m, k)
            best = A.pav_score(ballots, comm["pav"])
            for rule, w in comm.items():
                a = acc[rule]
                a["jr"] += A.group_violation(ballots, m, k, w, level=1) is not None
                a["ejr"] += A.group_violation(ballots, m, k, w) is not None
                a["cov"] += A.coverage(ballots, w) / n
                a["pav"] += float(A.pav_score(ballots, w) / best)
                a["size"] += len(w)
        for rule in RULES:
            a = acc[rule]
            rows.append({"model": model, "rule": rule, "runs": C.SERIES_RUNS, "jr": a["jr"], "ejr": a["ejr"], "cov_mean": a["cov"] / C.SERIES_RUNS, "pav_mean": a["pav"] / C.SERIES_RUNS,
                         "size_mean": a["size"] / C.SERIES_RUNS})
    return rows


def series_greedy() -> list:
    """Je Zahl der Sitze: das gierige PAV gegen das exakte PAV (Verhältnis der PAV-Summen), das gierige gegen das exakte CC (Verhältnis der Abdeckung); Zahl der Instanzen mit gleichem Wert."""
    rows = []
    n, m = C.SERIES_N, C.SERIES_M
    for ki, k in enumerate(C.SERIES_KS):
        pav, cc = [], []
        for run in range(C.SERIES_RUNS):
            ballots = _instance(C.DEFAULT_MODEL, n, m, C.SERIES_SEED + 100000 + 10000 * ki + run)
            pav.append(float(A.pav_score(ballots, A.committee("seqpav", ballots, m, k)) / A.pav_score(ballots, A.committee("pav", ballots, m, k))))
            cc.append(A.coverage(ballots, A.committee("seqcc", ballots, m, k)) / A.coverage(ballots, A.committee("cc", ballots, m, k)))
        rows.append({"k": k, "runs": C.SERIES_RUNS, "pav_mean": sum(pav) / len(pav), "pav_min": min(pav), "pav_equal": sum(x == 1.0 for x in pav),
                     "cc_mean": sum(cc) / len(cc), "cc_min": min(cc), "cc_equal": sum(x == 1.0 for x in cc)})
    return rows


def _ballot_text(ballots) -> str:
    return " | ".join("".join(cand(c) for c in sorted(b)) or "-" for b in ballots)


def series_examples() -> list:
    """Je Regel: in wie vielen kleinen Zufallsinstanzen (3 bis 8 Wähler, 3 bis 6 Kandidaten, 2 bis 4 Sitze) JR bzw. EJR verletzt ist, und die kleinste gefundene Instanz (kleinstes Produkt aus Wählern und Kandidaten, bei Gleichstand die erste)."""
    rng = random.Random(C.SERIES_SEED + 200000)
    rows = {rule: {"rule": rule, "runs": C.SERIES_EXAMPLE_RUNS, "jr": 0, "ejr": 0, "example": None, "size": None} for rule in RULES}
    for _ in range(C.SERIES_EXAMPLE_RUNS):
        n = rng.randint(*C.EXAMPLE_N)
        m = rng.randint(*C.EXAMPLE_M)
        k = rng.randint(2, min(C.EXAMPLE_K_MAX, m - 1))
        ballots = [frozenset(c for c in range(m) if rng.random() < C.EXAMPLE_P) for _ in range(n)]
        for rule, w in _committees(ballots, m, k).items():
            row = rows[rule]
            row["jr"] += A.group_violation(ballots, m, k, w, level=1) is not None
            if A.group_violation(ballots, m, k, w) is not None:
                row["ejr"] += 1
                size = (n * m, n, m, k)
                if row["size"] is None or size < row["size"]:
                    row["size"] = size
                    row["example"] = f"{_ballot_text(ballots)} (k = {k}); gewählt: {committee_text(w)}"
    return list(rows.values())


def violation_table(rows) -> list:
    out = []
    for r in rows:
        out.append({"Lager": C.MODEL_SHORT[r["model"]], "Regel": C.RULE_SHORT[r["rule"]], "JR verletzt": f"{r['jr']} von {r['runs']}", "EJR verletzt": f"{r['ejr']} von {r['runs']}",
                    "vertretene Wähler": pct(r["cov_mean"]), "PAV-Summe (Anteil am besten)": pct(r["pav_mean"], 2), "besetzte Sitze": num(r["size_mean"], 2)})
    return out


def greedy_table(rows) -> list:
    return [{"Sitze": r["k"], "Instanzen": r["runs"], "Seq. PAV: Mittel": pct(r["pav_mean"], 2), "schlechtester Fall": pct(r["pav_min"], 1), "gleich": f"{r['pav_equal']} von {r['runs']}",
             "Seq. CC: Mittel": pct(r["cc_mean"], 2), "schlechtester Fall ": pct(r["cc_min"], 1), "gleich ": f"{r['cc_equal']} von {r['runs']}"} for r in rows]


def example_table(rows) -> list:
    return [{"Regel": C.RULE_SHORT[r["rule"]], "JR verletzt": f"{r['jr']} von {r['runs']}", "EJR verletzt": f"{r['ejr']} von {r['runs']}", "kleinste gefundene Instanz (Wähler | …)": r["example"] or "–"} for r in rows]
