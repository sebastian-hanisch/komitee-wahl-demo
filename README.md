# Komitee-Wahl: wer vertritt wen? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-komitee-wahl-demo.streamlit.app/)** -->

Gelber Kandidat 6b der Linie **Abstimmen und Fair Teilen** (Konzepte-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“). Verwandt: [gemeinsames-budget-demo](https://github.com/sebastian-hanisch/gemeinsames-budget-demo) (dieselben Gruppenansprüche bei Projekten mit Kosten), [wahlregeln-demo](https://github.com/sebastian-hanisch/wahlregeln-demo) (ein einzelner Sieger), [wahlaxiome-demo](https://github.com/sebastian-hanisch/wahlaxiome-demo) (welche Eigenschaften sich ausschließen) und [sitzverteilung-demo](https://github.com/sebastian-hanisch/sitzverteilung-demo) (Sitze auf Verbände).
Die Demo fragt: **Ein Verein wählt einen Ausschuss mit k Sitzen, jeder Wähler stimmt beliebig vielen Kandidaten zu. Welche Regel vertritt die Wähler verhältnismäßig, wer bleibt unvertreten, und lohnt sich die exakte (NP-schwere) Optimierung gegenüber der gierigen?** Sieben Regeln im Vergleich: **Zustimmungswahl** (die k meistgenannten), **PAV** und **Chamberlin–Courant**, je **gierig und exakt**, und die **Methode gleicher Anteile** (Equal Shares) ohne und mit Auffüllen. Geprüft wird die **gerechtfertigte Repräsentation (JR)** und ihre **erweiterte Form (EJR)**: eine genügend große Gruppe, die sich auf Kandidaten einig ist, darf nicht ganz oder zu weit ohne Vertreter bleiben.

Der Kern ist eigener Code (`fractions`): alle Rechnungen sind **exakt** (ganze Zahlen und Brüche), die exakten Regeln zählen **alle C(m, k) Ausschüsse** auf. Unabhängige Orakel in den Tests: **ganzzahlige lineare Programme** (PAV und Chamberlin–Courant, `scipy.optimize.milp`), die **Aufzählung aller Wählergruppen** für JR und EJR (an jedem möglichen Ausschuss kleiner Instanzen), der Preis von Equal Shares **nach der Definition** (Halbierung) mit Nachrechnung jeder Zahlung.

## Warum dieses Problem

Die Zustimmungswahl ist einfach und lässt **eine Mehrheit alle Sitze holen**: bei zwei Lagern (70 : 30) verletzt sie die gerechtfertigte Repräsentation in **56 von 200** Instanzen (28 %), PAV, Equal Shares und die gierigen Regeln in **keiner**. Chamberlin–Courant vertritt am meisten Wähler (100 %), ignoriert aber, **wie viele** Kandidaten jemand gutheißt, und kann die erweiterte Form brechen (bei Gleichstand zugunsten des kleinsten Kandidaten in 27 von 4.000 kleinen Instanzen; mit anderer Gleichstandsregel wären es weniger). PAV erfüllt EJR und vertritt dabei 98,9 % der Wähler (zwei Lager).
Der Plan fragte, ob die **Aufzählung gegen die gierige Regel** lohnt. Gemessen im Zwei-Lager-Modell (24 Wähler, 10 Kandidaten, 3 bis 6 Sitze): das gierige PAV erreicht im Mittel **99,94 %** der exakten PAV-Summe, das gierige Chamberlin–Courant **99,66 %** der exakten Abdeckung; in 66 bzw. 62 von 800 Instanzen (etwa 8 %) ist die gierige Regel schlechter. Ob sich die Aufzählung lohnt, hängt vom Rechenaufwand ab (hier höchstens 924 Ausschüsse). Der große Befund liegt woanders: **Equal Shares lässt Sitze frei** (im Mittel nur 3,83 von 5 bei zwei Lagern, 3,15 bei drei Lagern) und erfüllt dabei EJR; „mit Auffüllen“ besetzt alle Sitze, behält EJR und erreicht bei zwei Lagern 99,3 % der besten PAV-Summe.

## Modell

**Wahl.** n Wähler, m Kandidaten (A bis L), k Sitze. Wähler i stimmt der Menge A<sub>i</sub> zu. Gleichstand: der kleinere Buchstabe (bei den exakten Regeln der lexikografisch kleinste unter den besten Ausschüssen).
**Regeln.** *Zustimmungswahl:* die k meistgenannten. *PAV:* größte Summe über alle Wähler von 1 + 1/2 + … + 1/c (c = Zahl der Gewählten, denen der Wähler zustimmt); *Chamberlin–Courant:* die meisten Wähler mit mindestens einem Gewählten; beide **gierig** (Sitz für Sitz der größte Zuwachs) und **exakt** (Aufzählung). *Equal Shares:* Budget k/n je Wähler, Preis 1 je Sitz; gewählt wird der Kandidat, dessen Unterstützer den kleinsten gleichen Preis ρ je Kopf aufbringen (jeder zahlt höchstens sein Restbudget); es endet, wenn kein Kandidat mehr bezahlbar ist, der Ausschuss kann also kleiner als k bleiben; *mit Auffüllen* gehen die freien Sitze an die meistgenannten Kandidaten.
**JR und EJR.** Für jede Stufe ℓ von 1 bis k darf es keine Gruppe von mindestens ℓ·n/k Wählern geben, die ℓ Kandidaten gemeinsam zustimmen und von denen jeder weniger als ℓ Gewählte gutheißt. ℓ = 1 ist JR, alle Stufen zusammen sind EJR.
**Erzeugte Stimmzettel.** Wähler und Kandidaten in Lagern (70 : 30, 50 : 30 : 20 oder keine); ein Wähler stimmt einem Kandidaten des eigenen Lagers mit der eingestellten Wahrscheinlichkeit zu (Standard 70 %), einem fremden mit 10 %; wer sonst niemanden ankreuzt, bekommt einen zufälligen Kandidaten des eigenen Lagers. Formeln im 📐-Expander der App.

## Methodik

- **Kern** (`kom_algorithm.py`): Summen, Zustimmungswahl, gierige und exakte Regeln, `min_price` und `equal_shares` (mit Ablaufprotokoll), `group_violation` (JR und EJR mit Gegenbeispiel, Bitmasken mit Abbruch bei zu kleinen Gruppen).
- **Szenario und Auswertung** (`kom_scenario.py`, `kom_evaluation.py`): Lager und Stimmzettel, Texteingabe mit Prüfung, sieben Ausschüsse mit allen Kennzahlen, Sitze je Lager, drei feste Reihen, alle Verdikte als reine Funktionen.
- **Oberfläche** (`app.py`): sechs Schnellstart-Szenarien (fünf von Hand nachgerechnet), Regler für Sitze, Kandidaten, Wähler, Lager und Zustimmung, Regel für die Anzeige, Textfeld für eigene Stimmzettel, Raster der Stimmzettel mit Ausschuss, Tabelle aller Regeln, Abdeckung, Sitze je Lager, Ablauf von Equal Shares, Gegenbeispiel, drei Reiter mit festen Reihen, Annahmen und Formeln.

## Befunde (gemessen, keine Behauptungen)

Alle Ausschüsse sind **exakt gerechnet**; die Reihen zählen Anteile in Zufallsinstanzen mit **festen Zufalls-Seeds** (Reihe 1 und 2: 200 Instanzen je Zeile, 24 Wähler, 10 Kandidaten; Reihe 3: 4.000 kleine Instanzen).

| Frage | Befund | Test |
|---|---|---|
| Stimmt der Kern? | PAV und Chamberlin–Courant (exakt) gleich den **ganzzahligen linearen Programmen**; die exakten Ausschüsse sind unter allen besten die lexikografisch kleinsten; JR und EJR gleich der **Aufzählung aller Wählergruppen** an jedem Ausschuss (Fälle mit und ohne Verletzung); jedes gemeldete Gegenbeispiel ist echt; Equal Shares: Preis nach der Definition, jede Zahlung summiert sich je Sitz auf genau 1, kein Budget wird negativ; die Sätze der Literatur gelten in Hunderten Zufallsinstanzen (PAV und Equal Shares erfüllen EJR, Chamberlin–Courant erfüllt JR, die gierige Abdeckung erreicht mindestens 1 − 1/e). | `test_oracle_komitee_wahl.py`, `test_algorithm.py` |
| Wer verletzt die gerechtfertigte Repräsentation? | Bei zwei Lagern (70 : 30) **nur die Zustimmungswahl: 56 von 200** Instanzen (JR und EJR fallen zusammen); bei drei Lagern 6 von 200; ohne Lager 0. Seq. PAV, PAV, Seq. CC, Chamberlin–Courant, Equal Shares und Equal Shares + Auffüllen: **0**. Über die 600 Instanzen verletzt die Zustimmungswahl in 10,3 %. | `test_claims.py::test_jr_and_ejr_violation_counts` |
| Wie viele Wähler werden vertreten? | Zwei Lager: Zustimmungswahl **84,6 %**, Seq. PAV 98,7 %, PAV 98,9 %, Seq. CC und Chamberlin–Courant **100,0 %**, Equal Shares 96,3 %, mit Auffüllen 97,2 %. PAV-Summe im Verhältnis zur besten: Zustimmungswahl 94,0 %, Chamberlin–Courant 96,6 %, Equal Shares 87,9 %, mit Auffüllen **99,3 %**. | `test_claims.py::test_coverage_and_pav_share_per_rule_in_the_two_camp_model` |
| Lässt Equal Shares Sitze frei? | **Ja:** im Mittel besetzt es von 5 Sitzen **3,83** (zwei Lager), **3,15** (drei Lager), 4,00 (keine Lager); mit Auffüllen immer 5. | `test_claims.py::test_equal_shares_fills_only_part_of_the_seats` |
| Lohnt sich die Aufzählung? | Gierig gegen exakt (3 bis 6 Sitze, 800 Instanzen): gierige PAV-Summe im Mittel **99,94 %** der exakten (schlechtester Fall 97,0 %, gleich in 734 Instanzen), gierige Abdeckung **99,66 %** (schlechtester Fall 91,7 %, gleich in 738). Im Mittel wird der Abstand mit mehr Sitzen kleiner (6 Sitze: 99,99 % und 100,00 %), zum Teil, weil beide Regeln dann fast alle Wähler abdecken. | `test_claims.py::test_greedy_against_exact` |
| Kleinste Gegenbeispiele | In 4.000 kleinen Instanzen (3 bis 8 Wähler, 3 bis 6 Kandidaten): EJR verletzt **Zustimmungswahl 16**, **Seq. CC 20**, **Chamberlin–Courant 27**, PAV, Seq. PAV und beide Equal-Shares-Regeln **0**; JR verletzt nur die Zustimmungswahl. Kleinste gefundene Beispiele (ab drei Wählern), Zustimmungswahl: drei Wähler `ABD | C | D`, drei Sitze; Chamberlin–Courant: drei Wähler `AC | AC | AC`, zwei Sitze, gewählt A und B. | `test_claims.py::test_small_instances`, `…::test_the_examples_really_violate` |
| Schnellstart-Szenarien | Von Hand nachgerechnet: **Zustimmungswahl übergeht eine Minderheit** (6 × ABC, 3 × D: A, B, C gegen A, B, D; PAV-Summe 11 gegen 12), **Chamberlin–Courant lässt einen Sitz verfallen** (3 × BC, zwei Sitze: A und B), **Gierig verpasst den besten Ausschuss** (acht Wähler, gierig 7 von 8, exakt 8 von 8), **Equal Shares bleibt leer** (vier Wähler mit je einem Kandidaten), dazu zwei erzeugte Szenarien (zwei Lager: Zustimmungswahl 5 : 0, PAV 4 : 1; drei Lager: 3 : 0 : 1 gegen 2 : 1 : 1). | `test_presets.py`, `test_algorithm.py` |

## Ehrliche Grenzen

- **Zustimmungsstimmen mit gleichem Gewicht.** Wer Kandidaten ordnen will, braucht Rangfolgen (übertragbare Einzelstimme, `wahlregeln-demo`); Zustimmung sagt nichts über die Stärke der Präferenz.
- **Ein Kandidat kostet einen Sitz.** Mit verschiedenen Kosten wird es ein gemeinsames Budget (`gemeinsames-budget-demo`); dort stehen dieselben Gruppenansprüche für Projekte.
- **Ehrliche Stimmzettel.** Taktisches Zustimmen ist ein eigenes Thema (`taktisch-waehlen-demo`).
- **Exakt durch Aufzählung.** Alle C(m, k) Ausschüsse werden durchprobiert (höchstens 924); das ist für große Wahlen nicht der richtige Weg (ganzzahlige Programme, Näherungen).
- **Gleichstände.** Bei Chamberlin–Courant entscheidet der Gleichstand mit, wer den „überflüssigen“ Sitz bekommt (A in den Beispielen, ein Kandidat, dem niemand zustimmt); echte Wahlen losen.
- **Erzeugte Lager.** Die Reihen gelten für diese Zufallsmodelle (Standard: 70 % Zustimmung zum eigenen, 10 % zu fremden Lagern); in zufälligen Instanzen sind Verletzungen selten bis auf die Zustimmungswahl bei einer deutlichen Mehrheit.
- **Equal Shares** ist hier für Ausschüsse mit Einheitskosten gerechnet (die Methode für Projekte mit Kosten steht in `gemeinsames-budget-demo`).
- **Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Chamberlin und Courant (1983); Thiele (1895) zu PAV; Aziz, Brill, Conitzer, Elkind, Freeman, Walsh (2017) zu JR und EJR; Peters und Skowron (2020) zu Equal Shares für Ausschüsse.

## Befunde und Korrekturen gegenüber dem Plan

- **Port:** 9198.
- **Plan:** „mehrere Sieger statt eines; Proportionalität durch Summe der Zufriedenheit; NP-schwer, exakt per ILP gegen Greedy“, „Überlappung mit Stück 6 prüfen, evtl. Tab“. Umgesetzt als **eigene kompakte Demo** (nach der Register- und README-Prüfung: `gemeinsames-budget-demo` führt die Komitee-Wahl ausdrücklich als nicht umgesetzt), mit dem, was dort fehlt: Abdeckung gegen Intensität, Equal Shares mit freien Sitzen, gierig gegen exakt, kleinste Gegenbeispiele.
- **Exakt per Aufzählung statt ILP im Kern:** `scipy.optimize.milp` dient als **unabhängiges Orakel** in den Tests, der Kern bleibt ohne Optimierer (kein `scipy` in `requirements.txt`).
- **Fehler der Vormessung (vom Orakel gefunden):** die erste Fassung der Gruppenprüfung betrachtete nur die Gruppe **aller** Unterstützer einer Kandidatenmenge und übersah Untergruppen, die allein zu kurz kommen. Die Aufzählung aller Wählergruppen deckte das auf; nach der Korrektur verletzt die Zustimmungswahl bei zwei Lagern in **56 von 200** Instanzen. Die Zahlen der Vormessung stehen deshalb nirgends in dieser README.
- **Reglerspanne:** Wähler 2 bis 40 (eigene Stimmzettel: 2 bis 40 Zeilen), Kandidaten 3 bis 12, Sitze 1 bis 6, Zustimmung zum eigenen Lager 30 bis 90 %, zu fremden 0 bis 30 %.

## Verifikation

- **Kern:** jede Einheit an Mini-Fällen von Hand (Summen, die sieben Regeln an `6 × ABC, 3 × D`, den Preis von Equal Shares mit Fraktionen, Gleichstände, Gegenbeispiele nach Stufe und Reihenfolge, Eingabeprüfung).
- **Orakel:** ganzzahlige lineare Programme, Aufzählung aller Gruppen, Preis nach der Definition, Zahlungen, Sätze der Literatur über Zufallsinstanzen (siehe Befunde).
- **Reihen und Texte:** jede Zahl dieser README in `tests/test_claims.py`; Verdikte, Tabellen, Ablauftexte, Gegenbeispiele und Eingabefehler als reine Funktionen (`tests/test_verdicts.py`), Randfälle und Adresszeile (`tests/test_edge_cases.py`).
- **Presets, Layout, Oberfläche:** wie in allen Demos (Presets vollständig und im Regelbereich, keines auf einem Rand von Wählern, Kandidaten und Sitzen, kein Preset entsteht durch Änderung eines einzigen Reglers, Schnellstart oben, aktives Preset hervorgehoben, AppTest jeder Button und jeder Regler an den Rändern, Footer, Laufzeit-Importe).
- **Mutationsprüfung** (`tools/mutate_demo.py`): 83 Stellen im Kern `kom_algorithm.py`, **79 gefangen**, **4 als äquivalent festgehalten** (`while len(chosen) < k` gegen `<=` in `equal_shares`: nach k bezahlten Sitzen ist das Budget aufgebraucht; die Stufe k + 1 in `group_violation`: sie verlangt mehr Wähler, als es gibt; zwei Mutanten der Maske `(1 << n) − 1`: das zusätzliche Bit gehört keinem Wähler und fällt beim Schnitt mit den Unterstützern weg). Der erste Lauf ließ 6 überleben: **eine echte Lücke** (ein Kandidat mit der Nummer m wurde nicht abgewiesen; neuer Randfalltest), **eine überflüssige Absicherung** (`m < 1` neben `1 ≤ k ≤ m`; entfernt, 3 Mutanten) und zwei Äquivalente; der zweite Lauf zwei weitere Äquivalente.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `kom_algorithm.py` | Kern: sieben Regeln, Preis von Equal Shares, JR und EJR |
| `kom_constants.py` | Regler-Grenzen, feste Reihen, Farben, Presets |
| `kom_evaluation.py` | Analyse, Tabellen, Ablauf, Verdikte, drei feste Reihen |
| `kom_layout.py` | Fester Kopf (Stylesheet) |
| `kom_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `kom_scenario.py` | Lager, Stimmzettel, Texteingabe |
| `kom_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `messen.py` | Einmalige Messung der Zahlen in dieser README (nicht Teil der App) |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (für die Orakel) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Kern, Orakel, Reihen und Claims, Verdikte, Randfälle, Szenario, Presets, Abbildungen, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Rangfolgen und übertragbare Einzelstimme:** ein anderes Wahlsystem mit eigenen Eigenschaften.
- **Ganzzahlige Programme im Kern** für große Wahlen (`scipy` nur als Test-Orakel): die Aufzählung genügt für höchstens 924 Ausschüsse.
- **Weitere Regeln** (Phragmén, Monroe, Rule X mit Kosten, STV): sie ändern die Aussage nicht; Equal Shares steht stellvertretend für die budgetbasierten Regeln.
- **Taktisches Zustimmen und Zufallsgremien:** eigene Themen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
