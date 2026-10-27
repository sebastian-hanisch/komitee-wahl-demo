"""Komitee-Wahl: wer vertritt wen? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück der Linie „Abstimmen und Fair Teilen“ (gelber Kandidat 6b): ein Ausschuss mit k Sitzen wird aus Zustimmungsstimmen gewählt. Sieben Regeln werden EXAKT gerechnet (Zustimmungswahl, gierig und exakt für PAV und für
Chamberlin–Courant, Equal Shares ohne und mit Auffüllen); gezeigt werden die gerechtfertigte Repräsentation (JR), ihre erweiterte Form (EJR), vertretene Wähler und die PAV-Summe. Der Kern liegt in kom_algorithm.py.

Lauffähig mit: streamlit run app.py
"""

import time

import streamlit as st

import kom_constants as C
import kom_evaluation as ev
from kom_evaluation import Settings, analyse, num
from kom_layout import dunkles_design, kopf_css
from kom_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kom_scenario import parse_ballots
from kom_visualization import build_ballots, build_camps, build_coverage, build_greedy_series, build_size_series, build_violation_series

st.set_page_config(page_title="Komitee-Wahl – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _series_violations():
    return ev.series_violations()


@st.cache_data(show_spinner=False)
def _series_greedy():
    return ev.series_greedy()


@st.cache_data(show_spinner=False)
def _series_examples():
    return ev.series_examples()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kom_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🗳️ Komitee-Wahl: wer vertritt wen?")
st.markdown(
    """
Ein Verein wählt einen **Ausschuss mit k Sitzen**. Jeder Wähler **stimmt Kandidaten zu** (beliebig vielen), und gesucht ist ein Ausschuss, der die Wähler **verhältnismäßig vertritt**. Die einfachste Regel, die **Zustimmungswahl** (die k meistgenannten Kandidaten), lässt eine Mehrheit alle Sitze holen.
Die Demo vergleicht sieben Regeln **exakt**: **PAV** (jede weitere Zustimmung eines Wählers zählt weniger) und **Chamberlin–Courant** (möglichst viele Wähler haben mindestens einen Vertreter), jeweils **gierig und exakt** (Aufzählung aller Ausschüsse; im Allgemeinen NP-schwer), und die **Methode gleicher Anteile** (Equal Shares). Geprüft werden die **gerechtfertigte Repräsentation (JR)** und ihre **erweiterte Form (EJR)**: eine Gruppe, die groß genug ist und sich auf Kandidaten einig ist, darf nicht ohne Vertreter bleiben.
Verwandt: `gemeinsames-budget-demo` (dieselben Gruppenansprüche bei Projekten mit Kosten), `wahlregeln-demo` (ein einzelner Sieger) und `sitzverteilung-demo` (Sitze auf Verbände).

Weiter unten: die **Kernfrage**, der Abschnitt **🔬 Feste Reihen** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So wird gerechnet", expanded=True):
    st.markdown(
        """
Jeder Wähler hat eine **Zustimmungsmenge** (die Kandidaten A, B, C, …, die er gutheißt). Gleichstand: der kleinere Buchstabe.
1. **Zustimmungswahl:** die k Kandidaten mit den meisten Zustimmungen.
2. **PAV:** der Ausschuss mit der größten Summe über alle Wähler von 1 + 1/2 + … + 1/c, wobei c die Zahl der Gewählten ist, denen der Wähler zustimmt. **Sequentiell:** Sitz für Sitz der Kandidat mit dem größten Zuwachs.
3. **Chamberlin–Courant:** der Ausschuss, in dem die meisten Wähler mindestens einen Gewählten gutheißen; **sequentiell:** Sitz für Sitz der Kandidat, der die meisten noch nicht vertretenen Wähler gewinnt.
4. **Equal Shares:** jeder Wähler hat das Budget k/n, ein Sitz kostet 1. Der Kandidat, dessen Unterstützer den kleinsten gleichen Preis je Kopf aufbringen, wird gewählt; jeder zahlt höchstens sein Restbudget. Wenn kein Kandidat mehr bezahlbar ist, **bleiben Sitze frei**; „mit Auffüllen“ vergibt sie nach Zustimmungszahl.
5. **JR / EJR:** gibt es eine Gruppe von mindestens ℓ·n/k Wählern, die ℓ Kandidaten gemeinsam zustimmen und von denen jeder weniger als ℓ Gewählte gutheißt? ℓ = 1 ist JR, jedes ℓ bis k zusammen ist EJR.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

_ballots_valid, _ = parse_ballots(st.session_state["ballots_text"], st.session_state["m_slider"])
custom = _ballots_valid is not None
with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Wahl**")
    k = st.slider("Sitze im Ausschuss", *bounds("k_slider"), key="k_slider", help="Wie viele Kandidaten gewählt werden (höchstens so viele, wie es Kandidaten gibt).")
    m = st.slider("Kandidaten", *bounds("m_slider"), key="m_slider", help="Wie viele Kandidaten zur Wahl stehen (Buchstaben A bis L).")
    rule = st.selectbox("Regel für die Anzeige", list(C.RULES), format_func=C.RULES.get, key="rule_select", help="Welcher Ausschuss im Raster der Stimmzettel markiert wird. Die Tabelle zeigt immer alle sieben Regeln.")
    st.markdown("**Wähler**")
    n = st.slider("Zahl der Wähler", *bounds("n_slider"), key="n_slider", disabled=custom, help="Wie viele Wähler abstimmen. Bei eigenen Stimmzetteln bestimmt die Zahl der Zeilen den Wert.")
    model = st.selectbox("Lager", list(C.MODELS), format_func=C.MODELS.get, key="model_select", disabled=custom, help="Wie die Wähler und Kandidaten in Lager aufgeteilt sind. Ein Wähler stimmt eher Kandidaten seines Lagers zu.")
    cohesion = st.slider("Zustimmung zum eigenen Lager (%)", *bounds("cohesion_slider"), key="cohesion_slider", disabled=custom, help="Mit dieser Wahrscheinlichkeit stimmt ein Wähler einem Kandidaten seines Lagers zu (ohne Lager: jedem).")
    cross = st.slider("Zustimmung zu fremden Lagern (%)", *bounds("cross_slider"), key="cross_slider", disabled=custom, help="Mit dieser Wahrscheinlichkeit stimmt ein Wähler einem Kandidaten eines anderen Lagers zu.")
    seed = st.number_input("Zufalls-Seed der Stimmzettel", *bounds("seed_input"), key="seed_input", step=1, disabled=custom)
    st.button("🎲 Neue Stimmzettel erzeugen", width="stretch", on_click=randomize_seed, disabled=custom)
    st.markdown("**Eigene Stimmzettel (optional)**")
    ballots_text = st.text_area("Zustimmungen je Wähler", key="ballots_text", height=120, placeholder="eine Zeile je Wähler, z. B.\nA B C\nD\n- (keine Zustimmung)",
                                help=f"{C.BALLOTS_MIN} bis {C.N_MAX} Zeilen, je Zeile die zugestimmten Kandidaten als Buchstaben A bis L (getrennt durch Leerzeichen oder Komma, auch „ABC“). Eine Zeile mit „-“ ist ein Wähler ohne Zustimmung. Leer lassen, um sie erzeugen zu lassen.")

sync_query_params({"n_slider": int(n), "m_slider": int(m), "k_slider": int(k), "model_select": model, "cohesion_slider": int(cohesion), "cross_slider": int(cross), "seed_input": int(seed),
                   "rule_select": rule, "ballots_text": ballots_text})

settings = Settings(n=int(n), m=int(m), k=int(k), model=model, cohesion=int(cohesion), cross=int(cross), seed=int(seed), rule=rule, ballots=ballots_text)
with st.spinner("Rechne die Ausschüsse …"):
    a = _analysis(settings)
for message in a.errors:
    st.warning(message)
if a.note:
    st.info(a.note)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

r = a.results[rule]
st.markdown("## 🎯 Ergebnis")
m1, m2, m3 = st.columns(3)
m1.metric(f"Ausschuss ({C.RULE_SHORT[rule]})", ev.committee_text(r.committee), delta=f"{len(r.committee)} von {a.k} Sitzen, {a.n} Wähler, {a.m} Kandidaten", delta_color="off")
m2.metric("Vertretene Wähler", ev.pct(r.covered / a.n), delta=f"{r.covered} von {a.n}; PAV-Summe {ev.pct(r.pav_ratio)} des besten", delta_color="off")
violating = [x for x in ev.RULES if a.results[x].ejr is not None]
m3.metric("Regeln mit EJR-Verletzung", f"{len(violating)} von {len(ev.RULES)}", delta=ev.names(violating) if violating else "keine", delta_color="off")
if a.source == "eingegeben":
    st.caption(f"Die eingegebenen Stimmzettel bestimmen die Zahl der Wähler ({a.n}); Lager, Zustimmungswahrscheinlichkeiten und Zufalls-Seed haben keine Wirkung.")
st.markdown("**Stimmzettel und Ausschuss**")
st.plotly_chart(build_ballots(a, rule), width="stretch", key="ballots_chart")
st.caption("Jede Zeile ist ein Wähler, türkis die Kandidaten, denen er zustimmt; die letzte Zeile (orange) ist der Ausschuss der gewählten Regel.")
st.markdown("**Alle sieben Regeln**")
st.table(ev.committee_rows(a))
st.plotly_chart(build_coverage(a), width="stretch", key="coverage_chart")
st.caption("Säulen: Anteil der Wähler mit mindestens einem Gewählten. Rauten: PAV-Summe im Verhältnis zur größten (die exakte PAV-Regel erreicht 100 %).")
camp = ev.camp_rows(a)
if camp is not None:
    st.markdown("**Sitze je Lager**")
    st.table(camp)
    st.plotly_chart(build_camps(a), width="stretch", key="camps_chart")
    st.caption("Die linke Säule zeigt, wie die Sitze nach dem Wähleranteil der Lager (unabgerundet) verteilt wären; die Regeln runden verschieden und sind nur teils verhältnismäßig.")
with st.expander("So entscheidet Equal Shares in diesem Fall"):
    for line in ev.trace_lines(a):
        st.markdown(f"- {line}")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wer bleibt unvertreten, und wann hilft die Aufzählung?")
kind, text = ev.verdict_state(a)
getattr(st, kind)(text)
st.markdown(f"*Gewählte Regel:* {ev.verdict_rule(a, rule)}")
if r.ejr is not None:
    st.error(f"Gegenbeispiel zur erweiterten gerechtfertigten Repräsentation bei {C.RULE_SHORT[rule]}: {ev.witness_text(a, r.ejr)}.")

st.markdown("---")

# --- Reihen --------------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Feste Reihen")
st.caption(
    f"Feste Programme, unabhängig von den Reglern: je Zeile {C.SERIES_RUNS} Zufallsinstanzen mit festen Zufalls-Seeds ({C.SERIES_N} Wähler, {C.SERIES_M} Kandidaten, Zustimmung {C.DEFAULT_COHESION} % zum eigenen und {C.DEFAULT_CROSS} % zu fremden Lagern); "
    "alle Ausschüsse sind exakt gerechnet, die Anteile gezählt. Jede Reihe rechnet auf Klick in bis zu einer halben Minute."
)
tab1, tab2, tab3 = st.tabs(["Wie oft ist EJR verletzt?", "Wie gut ist die gierige Regel?", "Kleinste Gegenbeispiele"])
with tab1:
    st.markdown(f"**Verletzungen und Abdeckung je Lagermodell.** {C.SERIES_K} Sitze; je Regel die Zahl der Instanzen mit Verletzung der JR und der EJR, der mittlere Anteil vertretener Wähler, die mittlere PAV-Summe im Verhältnis zur besten und die mittlere Zahl besetzter Sitze.")
    if st.button("Reihe rechnen", key="violations_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_violations()
        st.session_state["violations_done"] = time.perf_counter() - t0
    if "violations_done" in st.session_state:
        rows = _series_violations()
        st.plotly_chart(build_violation_series(rows), width="stretch", key="violations_chart")
        st.table(ev.violation_table(rows))
        st.markdown("*Besetzte Sitze von Equal Shares*")
        st.plotly_chart(build_size_series(rows), width="stretch", key="size_chart")
        kind, text = ev.verdict_violations(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['violations_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab2:
    st.markdown("**Gierig gegen exakt.** Für 3 bis 6 Sitze: das Verhältnis der PAV-Summe des gierigen PAV zur exakten und der Abdeckung des gierigen Chamberlin–Courant zur exakten (Mittel, schlechtester Fall, Zahl der Instanzen mit gleichem Wert).")
    if st.button("Reihe rechnen", key="greedy_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_greedy()
        st.session_state["greedy_done"] = time.perf_counter() - t0
    if "greedy_done" in st.session_state:
        rows = _series_greedy()
        st.plotly_chart(build_greedy_series(rows), width="stretch", key="greedy_chart")
        st.table(ev.greedy_table(rows))
        kind, text = ev.verdict_greedy(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['greedy_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")
with tab3:
    st.markdown(f"**Wer verletzt was, und wie klein kann das Gegenbeispiel sein?** {C.SERIES_EXAMPLE_RUNS:,} kleine Zufallsinstanzen".replace(",", ".") + f" ({C.EXAMPLE_N[0]} bis {C.EXAMPLE_N[1]} Wähler, {C.EXAMPLE_M[0]} bis {C.EXAMPLE_M[1]} Kandidaten, 2 bis {C.EXAMPLE_K_MAX} Sitze, Zustimmung {round(100 * C.EXAMPLE_P)} %); die kleinste gefundene Instanz je Regel steht in der Tabelle (Stimmzettel durch | getrennt).")
    if st.button("Reihe rechnen", key="examples_button"):
        t0 = time.perf_counter()
        with st.spinner("Rechne die Reihe …"):
            _series_examples()
        st.session_state["examples_done"] = time.perf_counter() - t0
    if "examples_done" in st.session_state:
        rows = _series_examples()
        st.table(ev.example_table(rows))
        kind, text = ev.verdict_examples(rows)
        getattr(st, kind)(text)
        st.caption(f"Rechenzeit dieser Sitzung: {num(st.session_state['examples_done'], 1)} s (beim ersten Mal; danach liegt das Ergebnis im Zwischenspeicher).")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Zustimmungsstimmen mit gleichem Gewicht** | Wer Kandidaten ordnen will (Rangfolgen), braucht andere Regeln (übertragbare Einzelstimme); Zustimmung sagt nichts über Stärke der Präferenz. | `wahlregeln-demo` |
| **Ein Kandidat kostet einen Sitz** | Haben Projekte verschiedene Kosten, wird aus der Komitee-Wahl ein gemeinsames Budget. | `gemeinsames-budget-demo` |
| **Ehrliche Stimmzettel** | Wer die Regel kennt, kann taktisch zustimmen (zum Beispiel nur den aussichtsreichen Kandidaten); die Demo rechnet ehrlich. | `taktisch-waehlen-demo` |
| **Exakte Regeln durch Aufzählung** | Alle C(m, k) Ausschüsse werden durchprobiert (bei 12 Kandidaten und 6 Sitzen 924); für große Wahlen braucht es ganzzahlige Programme oder Näherungen. | – |
| **Gleichstand: kleinerer Buchstabe** | Bei Chamberlin–Courant entscheidet der Gleichstand mit, welcher Kandidat den „überflüssigen“ Sitz bekommt; echte Wahlen losen. | – |
| **Erzeugte Lager** | Die Befunde der Reihen gelten für diese Zufallsmodelle; echte Wahlen haben andere Strukturen, und Verletzungen sind in zufälligen Instanzen selten, außer bei der Zustimmungswahl mit deutlicher Mehrheit. | – |
| **Modell, kein Befund über Wahlen** | Die Zahlen sagen, was die Rechnung für erzeugte oder eingegebene Stimmzettel liefert, nicht, wie ein bestimmter Verein wählen sollte. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Stimmen.** Wähler $i \in N$ ($|N| = n$) stimmt der Menge $A_i \subseteq \{1, \dots, m\}$ zu; gesucht ist ein Ausschuss $W$ mit $|W| = k$. Die Zahl der Treffer ist $c_i(W) = |A_i \cap W|$.

**PAV.** $\max_W \sum_{i} H(c_i(W))$ mit $H(c) = 1 + \tfrac12 + \dots + \tfrac1c$ und $H(0) = 0$. **Chamberlin–Courant.** $\max_W |\{i : c_i(W) \ge 1\}|$. Beide sind im Allgemeinen NP-schwer; hier werden alle $\binom{m}{k}$ Ausschüsse aufgezählt.

**Equal Shares.** Budget $b_i = k/n$, Preis 1 je Sitz. Für Kandidat $c$ mit Unterstützern $N_c$ ist $\rho_c$ der kleinste Wert mit $\sum_{i \in N_c} \min(\rho_c, b_i) \ge 1$; gewählt wird der Kandidat mit dem kleinsten $\rho_c$, jeder Unterstützer zahlt $\min(\rho_c, b_i)$. Es endet, wenn kein $\rho_c$ existiert.

**JR und EJR.** Für $\ell \in \{1, \dots, k\}$ heißt eine Gruppe $S \subseteq N$ **$\ell$-berechtigt**, wenn $|S| \ge \ell\, n / k$ und $|\bigcap_{i \in S} A_i| \ge \ell$. $W$ erfüllt **EJR**, wenn es für jede $\ell$-berechtigte Gruppe ein $i \in S$ mit $c_i(W) \ge \ell$ gibt; **JR** ist der Fall $\ell = 1$.

**Literatur** (aus dem Gedächtnis, nicht im Original geprüft): Chamberlin und Courant (1983); Thiele (1895) zu PAV; Aziz, Brill, Conitzer, Elkind, Freeman, Walsh (2017) zu JR und EJR; Peters und Skowron (2020) zur Methode gleicher Anteile für Ausschüsse.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
