"""Einmalige Messung der README-Zahlen (nicht Teil der App): feste Pläne, Ausgabe auf stdout. Alle Ausschüsse sind exakt gerechnet; die Reihen zählen Anteile in Zufallsinstanzen mit festen Zufalls-Seeds."""

import sys
import time

sys.path.insert(0, ".")
import kom_constants as C
import kom_evaluation as ev

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

t0 = time.time()
print("PRESETS")
for name, p in C.PRESETS.items():
    a = ev.analyse(ev.Settings(**p))
    print(name, p["rule"], a.n, a.m, a.k)
    for r in ev.committee_rows(a):
        print("   ", r)
    print("   ", ev.verdict_state(a))

rows = ev.series_violations()
print("REIHE 1 (Verletzungen und Abdeckung)")
for r in ev.violation_table(rows):
    print("   ", r)
print("   ", ev.verdict_violations(rows))
rows = ev.series_greedy()
print("REIHE 2 (gierig gegen exakt)")
for r in ev.greedy_table(rows):
    print("   ", r)
print("   ", ev.verdict_greedy(rows))
rows = ev.series_examples()
print("REIHE 3 (kleinste Gegenbeispiele)")
for r in ev.example_table(rows):
    print("   ", r)
print("   ", ev.verdict_examples(rows))
print("sec", round(time.time() - t0, 1))
