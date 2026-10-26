"""Szenario: Stimmzettel (erzeugt oder eingegeben). Deterministisch aus (Modell, Wähler, Kandidaten, Zustimmungswahrscheinlichkeiten, Zufalls-Seed)."""

import re

import numpy as np

import kom_constants as C


def camps_of(model: str, n: int, m: int) -> tuple:
    """(Lager je Wähler, Lager je Kandidat): die Wähler werden nach den Anteilen des Modells in Blöcke geteilt, die Kandidaten gleichmäßig auf die Lager."""
    shares = C.MODEL_SHARES[model]
    g = len(shares)
    bounds = [round(sum(shares[: i + 1]) * n) for i in range(g)]
    voter_camp = [next(i for i, b in enumerate(bounds) if v < b) if v < bounds[-1] else g - 1 for v in range(n)]
    cand_camp = [min(g - 1, c * g // m) for c in range(m)]
    return voter_camp, cand_camp


def make_ballots(model: str, n: int, m: int, cohesion: int, cross: int, seed: int):
    """Stimmzettel als Liste von frozensets. Ein Wähler stimmt einem Kandidaten seines Lagers mit der Wahrscheinlichkeit `cohesion` %, einem fremden mit `cross` % zu (ohne Lager: überall `cohesion` %).
    Hat ein Wähler nichts angekreuzt, bekommt er einen zufälligen Kandidaten seines Lagers. Rückgabe (Stimmzettel, Lager je Wähler, Lager je Kandidat)."""
    if model not in C.MODELS:
        raise ValueError(model)
    rng = np.random.default_rng(seed)
    voter_camp, cand_camp = camps_of(model, n, m)
    single = len(C.MODEL_SHARES[model]) == 1
    ballots = []
    for v in range(n):
        p = [cohesion / 100 if single or cand_camp[c] == voter_camp[v] else cross / 100 for c in range(m)]
        picked = {c for c in range(m) if rng.random() < p[c]}
        if not picked:
            own = [c for c in range(m) if single or cand_camp[c] == voter_camp[v]]
            picked = {own[int(rng.integers(0, len(own)))]}
        ballots.append(frozenset(picked))
    return ballots, voter_camp, cand_camp


def _expand(token: str) -> list:
    """Ein Wort aus mehreren Buchstaben („ABC“) steht für die einzelnen Kandidaten; alles andere bleibt ein Wort."""
    return list(token) if len(token) > 1 and token.isalpha() else [token]


def parse_ballots(text: str, m: int):
    """Eingabe: eine Zeile je Wähler, darin die zugestimmten Kandidaten als Buchstaben A bis L (getrennt durch Komma, Semikolon oder Leerzeichen, auch ohne Trennzeichen). Eine Zeile mit „-“ ist ein Wähler ohne Zustimmung.
    Rückgabe (Liste von frozensets oder None, Fehlermeldung oder None); leerer Text: (None, None)."""
    text = (text or "").strip()
    if not text:
        return None, None
    lines = [ln.strip() for ln in re.split(r"[\r\n]+", text) if ln.strip()]
    if not C.BALLOTS_MIN <= len(lines) <= C.N_MAX:
        return None, f"Es müssen {C.BALLOTS_MIN} bis {C.N_MAX} Zeilen sein, eine je Wähler (eingegeben: {len(lines)})."
    ballots = []
    for k, line in enumerate(lines, start=1):
        if line == "-":
            ballots.append(frozenset())
            continue
        letters = [x for token in re.split(r"[,;\s]+", line) if token for x in _expand(token)]
        chosen = set()
        for t in letters:
            t = t.upper()
            if len(t) != 1 or t not in C.LETTERS:
                return None, f"Zeile {k}: „{t}“ ist kein Kandidat (erlaubt: die Buchstaben A bis {C.LETTERS[m - 1]}, getrennt durch Komma, Semikolon oder Leerzeichen; „-“ für keine Zustimmung)."
            if C.LETTERS.index(t) >= m:
                return None, f"Zeile {k}: Kandidat „{t}“ gibt es nicht, es gibt nur die Buchstaben A bis {C.LETTERS[m - 1]}."
            chosen.add(C.LETTERS.index(t))
        ballots.append(frozenset(chosen))
    return ballots, None
