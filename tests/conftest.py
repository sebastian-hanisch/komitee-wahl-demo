"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

LETTERS = "ABCDEFGHIJKL"


def fs(*rows):
    """Stimmzettel aus Zeichenketten: fs("AB", "C") sind zwei Wähler mit den Zustimmungen {A, B} und {C}."""
    return [frozenset(LETTERS.index(c) for c in row if c != "-") for row in rows]


def letters(committee):
    return "".join(LETTERS[c] for c in sorted(committee))


@pytest.fixture
def mini():
    """Neun Wähler, vier Kandidaten, drei Sitze. Sechs Wähler stimmen A, B und C zu, drei nur D.
    Handrechnung: Zustimmungen A, B, C je 6, D 3, also gewählt A, B, C und die drei D-Wähler bleiben ohne Vertreter (Gruppe von 3 ≥ 9/3: JR verletzt).
    PAV-Summe von {A, B, C}: 6 · (1 + 1/2 + 1/3) = 11; von {A, B, D}: 6 · (1 + 1/2) + 3 · 1 = 12."""
    return fs(*(["ABC"] * 6 + ["D"] * 3))
