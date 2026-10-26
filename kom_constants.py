"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 2, 40, 24             # Wähler
M_MIN, M_MAX, DEFAULT_M = 3, 12, 10             # Kandidaten (Buchstaben A bis L)
K_MIN, K_MAX, DEFAULT_K = 1, 6, 5               # Sitze
COHESION_MIN, COHESION_MAX, DEFAULT_COHESION = 30, 90, 70   # Zustimmung zu den Kandidaten des eigenen Lagers in %
CROSS_MIN, CROSS_MAX, DEFAULT_CROSS = 0, 30, 10             # Zustimmung zu Kandidaten fremder Lager in %
SEED_MAX, DEFAULT_SEED = 9999, 6
BALLOTS_MIN = 2                                  # eigene Stimmzettel: mindestens zwei Wähler (höchstens N_MAX)

LETTERS = "ABCDEFGHIJKL"

MODELS = {
    "zwei": "Zwei Lager (70 : 30)",
    "drei": "Drei Lager (50 : 30 : 20)",
    "keine": "Keine Lager (jeder stimmt zufällig zu)",
}
MODEL_SHORT = {"zwei": "Zwei Lager", "drei": "Drei Lager", "keine": "Keine Lager"}
MODEL_SHARES = {"zwei": (0.7, 0.3), "drei": (0.5, 0.3, 0.2), "keine": (1.0,)}
DEFAULT_MODEL = "zwei"

RULES = {
    "av": "Zustimmungswahl (die k Meistgenannten)",
    "seqpav": "Sequentielles PAV (gierig)",
    "pav": "PAV (exakt)",
    "seqcc": "Sequentielles Chamberlin–Courant (gierig)",
    "cc": "Chamberlin–Courant (exakt)",
    "es": "Equal Shares (Methode gleicher Anteile)",
    "esfill": "Equal Shares mit Auffüllen",
}
RULE_SHORT = {"av": "Zustimmungswahl", "seqpav": "Seq. PAV", "pav": "PAV", "seqcc": "Seq. CC", "cc": "Chamberlin–Courant", "es": "Equal Shares", "esfill": "Equal Shares + Auffüllen"}
RULE_COLORS = {"av": "#b04a3a", "seqpav": "#8fb4d8", "pav": "#4c78a8", "seqcc": "#f2cf85", "cc": "#e8a838", "es": "#7fb3ad", "esfill": "#2F6B65"}
RULE_TEXT = {
    "av": "Jeder Wähler nennt seine Kandidaten; gewählt sind die k mit den meisten Nennungen. Einfach, aber eine Mehrheit kann alle Sitze holen.",
    "seqpav": "Sitz für Sitz der Kandidat, der die Summe 1 + 1/2 + 1/3 … der Wähler am meisten steigert (jede weitere Zustimmung zählt weniger).",
    "pav": "Der Ausschuss mit der größten PAV-Summe (Proportional Approval Voting), durch Aufzählung aller Ausschüsse; NP-schwer im Allgemeinen.",
    "seqcc": "Sitz für Sitz der Kandidat, der die meisten noch nicht vertretenen Wähler gewinnt.",
    "cc": "Der Ausschuss, in dem die meisten Wähler mindestens einen Gewählten haben (Chamberlin–Courant), durch Aufzählung; NP-schwer im Allgemeinen.",
    "es": "Jeder Wähler hat das Budget k/n, ein Sitz kostet 1; der Kandidat mit dem kleinsten gleichen Preis je Unterstützer wird gewählt. Der Ausschuss kann kleiner als k bleiben.",
    "esfill": "Wie Equal Shares; übrig gebliebene Sitze gehen an die meistgenannten Kandidaten.",
}
DEFAULT_RULE = "pav"
HIGHLIGHT_COLORS = {"voter": "#2F6B65", "winner": "#e8a838"}
CAMP_COLORS = ["#4c78a8", "#e8a838", "#2F6B65", "#b04a3a"]
COLOR_ALERT = "#c0392b"

# Feste Reihen (Zufallsinstanzen mit festen Zufalls-Seeds; Anteile exakt gezählt)
SERIES_SEED = 300000
SERIES_RUNS = 200
SERIES_N, SERIES_M, SERIES_K = 24, 10, 5
SERIES_KS = (3, 4, 5, 6)                         # Reihe 2: Sitze
SERIES_EXAMPLE_RUNS = 4000                       # Reihe 3: kleine Zufallsinstanzen
EXAMPLE_N = (3, 8)
EXAMPLE_M = (3, 6)
EXAMPLE_K_MAX = 4
EXAMPLE_P = 0.45

NL = chr(10)


def lines(*rows):
    return NL.join(rows)


PRESETS = {
    "Zwei Lager, fünf Sitze": {"n": 24, "m": 10, "k": 5, "model": "zwei", "cohesion": 70, "cross": 10, "seed": 6, "rule": "pav", "ballots": ""},
    "Zustimmungswahl übergeht eine Minderheit": {
        "n": 9, "m": 4, "k": 3, "model": "zwei", "cohesion": 70, "cross": 10, "seed": 4, "rule": "av",
        "ballots": lines(*(["A B C"] * 6 + ["D"] * 3)),
    },
    "Chamberlin–Courant lässt einen Sitz verfallen": {
        "n": 3, "m": 4, "k": 2, "model": "zwei", "cohesion": 70, "cross": 10, "seed": 4, "rule": "cc",
        "ballots": lines("B C", "B C", "B C"),
    },
    "Gierig verpasst den besten Ausschuss": {
        "n": 8, "m": 4, "k": 2, "model": "zwei", "cohesion": 70, "cross": 10, "seed": 4, "rule": "seqcc",
        "ballots": lines("A B", "B", "A C", "B", "C", "A B", "A C", "A C D"),
    },
    "Equal Shares bleibt leer": {
        "n": 4, "m": 4, "k": 2, "model": "zwei", "cohesion": 70, "cross": 10, "seed": 4, "rule": "es",
        "ballots": lines("A", "B", "C", "D"),
    },
    "Drei Lager, vier Sitze": {"n": 30, "m": 9, "k": 4, "model": "drei", "cohesion": 80, "cross": 5, "seed": 7, "rule": "av", "ballots": ""},
}
PRESET_HELP = {
    "Zwei Lager, fünf Sitze": "Voreinstellung: 24 Wähler in zwei Lagern (70 : 30), zehn Kandidaten, fünf Sitze, PAV. Die Zustimmungswahl gibt alle fünf Sitze dem größeren Lager und verletzt die gerechtfertigte Repräsentation; PAV gibt dem kleineren Lager einen Sitz.",
    "Zustimmungswahl übergeht eine Minderheit": "Sechs Wähler stimmen A, B und C zu, drei nur D: die Zustimmungswahl wählt A, B, C, und die drei bleiben unvertreten, obwohl sie ein Drittel der Wähler sind (und damit einen von drei Sitzen verdienen). Alle anderen Regeln wählen A, B und D.",
    "Chamberlin–Courant lässt einen Sitz verfallen": "Drei Wähler stimmen alle B und C zu. Chamberlin–Courant braucht nur einen von beiden, um alle zu vertreten, und gibt den zweiten Sitz an A, dem niemand zustimmt (Gleichstand: kleinster Kandidat); die erweiterte gerechtfertigte Repräsentation ist verletzt.",
    "Gierig verpasst den besten Ausschuss": "Acht Wähler, zwei Sitze: die gierige Regel nimmt zuerst A (5 Wähler) und dann B und vertritt 7 von 8; der beste Ausschuss B und C vertritt alle 8.",
    "Equal Shares bleibt leer": "Vier Wähler, jeder stimmt nur seinem eigenen Kandidaten zu, zwei Sitze: jeder hat das Budget 1/2, ein Sitz kostet 1, keine Gruppe kann einen Sitz bezahlen; Equal Shares wählt niemanden, mit Auffüllen gehen die Sitze an A und B.",
    "Drei Lager, vier Sitze": "Drei Lager (50 : 30 : 20), 30 Wähler, neun Kandidaten, vier Sitze: die Zustimmungswahl gibt dem mittleren Lager (30 % der Wähler) keinen Sitz (3 : 0 : 1), PAV gibt jedem Lager mindestens einen (2 : 1 : 1).",
}
