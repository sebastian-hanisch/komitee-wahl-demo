"""Verdikte, Tabellen, Texte und Formatierung als reine Funktionen: jeder Zweig mit Beispielen, deren Text von Hand erwartet wird."""

import kom_constants as C
import kom_evaluation as ev


def analyse(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


# --- Formatierung -----------------------------------------------------------------------------------------------------------------------------

def test_formatting():
    assert ev.num(1.5, 2) == "1,50" and ev.num(-0.5) == "−0,5" and ev.pct(0.5) == "50,0 %" and ev.pct(-0.012) == "−1,2 %" and ev.pct(None) == "–" and ev.pct(float("nan")) == "–"
    assert ev.cand(0) == "A" and ev.cand(11) == "L"
    assert ev.committee_text({3, 0, 1}) == "A, B, D" and ev.committee_text(set()) == "(leer)"
    assert ev.voters_text((0, 2)) == "Wähler 1, Wähler 3"


def test_names_lists_in_german():
    assert ev.names([]) == "" and ev.names(["av"]) == "Zustimmungswahl" and ev.names(["av", "cc"]) == "Zustimmungswahl und Chamberlin–Courant"
    assert ev.names(["av", "seqpav", "cc"]) == "Zustimmungswahl, Seq. PAV und Chamberlin–Courant"


# --- Gegenbeispiele und Ablauf -----------------------------------------------------------------------------------------------------------------

def test_witness_texts():
    a = analyse("Zustimmungswahl übergeht eine Minderheit")
    assert ev.witness_text(a, None) == "keines"
    assert ev.witness_text(a, a.results["av"].jr) == "3 von 9 Wählern (Wähler 7, Wähler 8, Wähler 9) stimmen D zu, aber jeder von ihnen hat keinen Gewählten"
    b = analyse("Chamberlin–Courant lässt einen Sitz verfallen")
    assert ev.witness_text(b, b.results["cc"].ejr) == "3 von 3 Wählern (Wähler 1, Wähler 2, Wähler 3) stimmen B, C zu, aber jeder von ihnen hat weniger als 2 Gewählte"


def test_equal_shares_trace_lines():
    assert ev.trace_lines(analyse("Zustimmungswahl übergeht eine Minderheit")) == [
        "Jeder der 9 Wähler hat das Budget 3/9; ein Sitz kostet 1.",
        "Kandidat A wird gewählt: seine 6 Unterstützer zahlen höchstens 0,167 je Kopf (der kleinste Preis aller Kandidaten in dieser Runde).",
        "Kandidat B wird gewählt: seine 6 Unterstützer zahlen höchstens 0,167 je Kopf (der kleinste Preis aller Kandidaten in dieser Runde).",
        "Kandidat D wird gewählt: seine 3 Unterstützer zahlen höchstens 0,333 je Kopf (der kleinste Preis aller Kandidaten in dieser Runde).",
    ]
    assert ev.trace_lines(analyse("Equal Shares bleibt leer")) == [
        "Jeder der 4 Wähler hat das Budget 2/4; ein Sitz kostet 1.",
        "Danach kann kein weiterer Kandidat bezahlt werden. Frei bleiben 2 von 2 Sitzen; Equal Shares mit Auffüllen vergibt sie nach Zustimmungszahl.",
    ]


# --- Tabellen ---------------------------------------------------------------------------------------------------------------------------------

def test_committee_rows_by_hand():
    rows = ev.committee_rows(analyse("Zustimmungswahl übergeht eine Minderheit"))
    assert [r["Regel"] for r in rows] == ["Zustimmungswahl", "Seq. PAV", "PAV", "Seq. CC", "Chamberlin–Courant", "Equal Shares", "Equal Shares + Auffüllen"]
    assert rows[0] == {"Regel": "Zustimmungswahl", "Ausschuss": "A, B, C", "Sitze": "3 von 3", "Vertretene Wähler": "6 von 9 (66,7 %)", "PAV-Summe": "11,00 (91,7 % des besten)",
                       "gerechtfertigt (JR)": "nein", "erweitert gerechtfertigt (EJR)": "nein"}
    assert rows[2]["Ausschuss"] == "A, B, D" and rows[2]["PAV-Summe"] == "12,00 (100,0 % des besten)" and rows[2]["gerechtfertigt (JR)"] == "ja"


def test_committee_rows_show_incomplete_equal_shares():
    rows = ev.committee_rows(analyse("Equal Shares bleibt leer"))
    assert rows[5]["Ausschuss"] == "(leer)" and rows[5]["Sitze"] == "0 von 2" and rows[5]["Vertretene Wähler"] == "0 von 4 (0,0 %)" and rows[6]["Ausschuss"] == "A, B"


def test_camp_rows():
    rows = ev.camp_rows(analyse("Zwei Lager, fünf Sitze"))
    assert rows[0] == {"Regel": "Anteil der Wähler × Sitze", "Lager 1": "3,5", "Lager 2": "1,5"}
    assert rows[1] == {"Regel": "Zustimmungswahl", "Lager 1": "5", "Lager 2": "0"} and rows[3] == {"Regel": "PAV", "Lager 1": "4", "Lager 2": "1"}
    assert ev.camp_rows(analyse("Equal Shares bleibt leer")) is None                                # eingegebene Stimmzettel haben keine Lager


# --- Verdikte -------------------------------------------------------------------------------------------------------------------------------------

def test_verdict_for_the_approval_preset():
    kind, text = ev.verdict_state(analyse("Zustimmungswahl übergeht eine Minderheit"))
    assert kind == "warning" and text == (
        "Gerechtfertigte Repräsentation (JR) verletzen: Zustimmungswahl. Erweiterte (EJR) verletzen: Zustimmungswahl. Vertretene Wähler: Zustimmungswahl 66,7 %, PAV 100,0 %, Chamberlin–Courant 100,0 %. "
        "Beispiel (Zustimmungswahl): 3 von 9 Wählern (Wähler 7, Wähler 8, Wähler 9) stimmen D zu, aber jeder von ihnen hat keinen Gewählten.")


def test_verdict_for_the_chamberlin_courant_preset():
    kind, text = ev.verdict_state(analyse("Chamberlin–Courant lässt einen Sitz verfallen"))
    assert kind == "warning" and "Gerechtfertigte Repräsentation (JR) verletzen: keine Regel. Erweiterte (EJR) verletzen: Seq. CC und Chamberlin–Courant." in text
    assert text.endswith("Beispiel (Chamberlin–Courant): 3 von 3 Wählern (Wähler 1, Wähler 2, Wähler 3) stimmen B, C zu, aber jeder von ihnen hat weniger als 2 Gewählte.")


def test_verdict_success_and_incomplete_equal_shares():
    kind, text = ev.verdict_state(analyse("Equal Shares bleibt leer"))
    assert kind == "success" and text == ("Gerechtfertigte Repräsentation (JR) verletzen: keine Regel. Erweiterte (EJR) verletzen: keine Regel. "
                                          "Vertretene Wähler: Zustimmungswahl 50,0 %, PAV 50,0 %, Chamberlin–Courant 50,0 %. Equal Shares besetzt nur 0 von 2 Sitzen.")


def test_verdict_rule_line():
    a = analyse("Gierig verpasst den besten Ausschuss")
    assert ev.verdict_rule(a, "seqcc") == "Sequentielles Chamberlin–Courant (gierig): Ausschuss A, B; 7 von 8 Wählern vertreten, PAV-Summe 8,00 (100,0 % des besten); JR erfüllt, EJR erfüllt."


def test_k_larger_than_m_is_reduced_with_a_note():
    a = ev.analyse(ev.Settings(m=3, k=5, n=10))
    assert a.k == 3 and a.note == "Es gibt nur 3 Kandidaten, gerechnet wird mit 3 Sitzen statt 5." and all(len(a.results[r].committee) <= 3 for r in ev.RULES)


def test_invalid_ballots_fall_back_to_generated_ones_with_a_message():
    a = ev.analyse(ev.Settings(ballots="A\nZ"))
    assert a.source == "erzeugt" and a.n == C.DEFAULT_N
    assert a.errors == ["Eigene Stimmzettel: Zeile 2: „Z“ ist kein Kandidat (erlaubt: die Buchstaben A bis J, getrennt durch Komma, Semikolon oder Leerzeichen; „-“ für keine Zustimmung). Die Eingabe wird ignoriert."]


def test_ballots_override_the_number_of_voters():
    a = ev.analyse(ev.Settings(n=30, ballots="A\nB\nC"))
    assert a.source == "eingegeben" and a.n == 3 and a.voter_camp is None and a.errors == []


# --- Reihen-Verdikte mit künstlichen Zeilen ---------------------------------------------------------------------------------------------------

def _violation_rows(av=5, cc=1):
    rows = []
    for model in C.MODELS:
        for rule in ev.RULES:
            rows.append({"model": model, "rule": rule, "runs": 100, "jr": av if rule == "av" else 0, "ejr": av if rule == "av" else (cc if rule == "cc" else 0),
                         "cov_mean": 0.9, "pav_mean": 0.95, "size_mean": 3.5 if rule == "es" else 5.0})
    return rows


def test_verdict_violations():
    kind, text = ev.verdict_violations(_violation_rows())
    assert kind == "warning" and text == ("Über 300 Instanzen (24 Wähler, 10 Kandidaten, 5 Sitze): EJR verletzt Zustimmungswahl in 5,0 %, Chamberlin–Courant in 1,0 %, Seq. CC in 0,0 %; "
                                          "JR verletzt nur die Zustimmungswahl (5,0 %). Ohne EJR-Verletzung blieben in diesen Instanzen: Seq. PAV, PAV, Seq. CC, Equal Shares und Equal Shares + Auffüllen.")


def test_verdict_greedy():
    rows = [{"k": k, "runs": 100, "pav_mean": 0.999, "pav_min": 0.97, "pav_equal": 90, "cc_mean": 0.99, "cc_min": 0.9, "cc_equal": 80} for k in (3, 4)]
    kind, text = ev.verdict_greedy(rows)
    assert kind == "info" and text == ("Über 200 Instanzen erreicht das gierige PAV im Mittel 99,90 % der exakten PAV-Summe (schlechtester Fall 97,0 %, gleich in 180 Instanzen), "
                                       "das gierige Chamberlin–Courant 99,00 % der exakten Abdeckung (schlechtester Fall 90,0 %, gleich in 160). Schlechter als die exakte Regel ist die gierige in 20 (PAV) bzw. 40 (Chamberlin–Courant) Instanzen; ob sich die Aufzählung lohnt, hängt vom Rechenaufwand ab.")


def test_verdict_examples():
    rows = [{"rule": r, "runs": 4000, "jr": 0, "ejr": 10 if r in ("av", "cc") else 0, "example": None, "size": None} for r in ev.RULES]
    kind, text = ev.verdict_examples(rows)
    assert text == ("In 4.000 kleinen Zufallsinstanzen verletzen EJR: Zustimmungswahl und Chamberlin–Courant; nie verletzt wurde es von Seq. PAV, PAV, Seq. CC, Equal Shares und Equal Shares + Auffüllen. "
                    "Die kleinsten gefundenen Gegenbeispiele stehen in der Tabelle.")
    none = [{**r, "ejr": 0} for r in rows]
    assert "verletzen EJR: keine Regel" in ev.verdict_examples(none)[1]


def test_series_tables_format_the_rows():
    row = ev.violation_table(_violation_rows())[0]
    assert row == {"Lager": "Zwei Lager", "Regel": "Zustimmungswahl", "JR verletzt": "5 von 100", "EJR verletzt": "5 von 100", "vertretene Wähler": "90,0 %", "PAV-Summe (Anteil am besten)": "95,00 %", "besetzte Sitze": "5,00"}
    assert ev.violation_table(_violation_rows())[5]["besetzte Sitze"] == "3,50"
    g = ev.greedy_table([{"k": 5, "runs": 200, "pav_mean": 0.999664, "pav_min": 0.98847, "pav_equal": 186, "cc_mean": 0.999792, "cc_min": 0.95833, "cc_equal": 199}])[0]
    assert g == {"Sitze": 5, "Instanzen": 200, "Seq. PAV: Mittel": "99,97 %", "schlechtester Fall": "98,8 %", "gleich": "186 von 200", "Seq. CC: Mittel": "99,98 %", "schlechtester Fall ": "95,8 %", "gleich ": "199 von 200"}
    e = ev.example_table([{"rule": "cc", "runs": 4000, "jr": 0, "ejr": 27, "example": "AC | AC | AC (k = 2); gewählt: A, B", "size": (9, 3, 3, 2)}, {"rule": "pav", "runs": 4000, "jr": 0, "ejr": 0, "example": None, "size": None}])
    assert e[0]["kleinste gefundene Instanz (Wähler | …)"] == "AC | AC | AC (k = 2); gewählt: A, B" and e[1]["kleinste gefundene Instanz (Wähler | …)"] == "–"
