"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import kom_constants as C
import kom_evaluation as ev


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.28), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_ballots(a, rule):
    """Stimmzettel als Raster (Zeile = Wähler, Spalte = Kandidat): Zustimmungen türkis, in der letzten Zeile der Ausschuss der gewählten Regel orange."""
    winners = a.results[rule].committee
    z = [[1 if c in b else 0 for c in range(a.m)] for b in a.ballots] + [[2 if c in winners else 0 for c in range(a.m)]]
    ylabels = [f"Wähler {i + 1}" for i in range(a.n)] + [f"Ausschuss ({C.RULE_SHORT[rule]})"]
    hover = [[("stimmt zu" if v == 1 else "") for v in row] for row in z[:-1]] + [["gewählt" if v == 2 else "" for v in z[-1]]]
    fig = go.Figure(go.Heatmap(z=z, x=[ev.cand(c) for c in range(a.m)], y=ylabels, zmin=0, zmax=2, showscale=False, xgap=2, ygap=2, text=hover, hovertemplate="%{y}, Kandidat %{x}: %{text}<extra></extra>",
                               colorscale=[[0, "rgba(128,128,128,0.12)"], [0.5, C.HIGHLIGHT_COLORS["voter"]], [1, C.HIGHLIGHT_COLORS["winner"]]]))
    fig.update_yaxes(autorange="reversed", type="category")
    fig.update_xaxes(title_text="Kandidat", side="top")
    return _base(fig, height=min(620, 150 + 18 * (a.n + 1)))


def build_coverage(a):
    """Vertretene Wähler je Regel (Säulen) und PAV-Summe im Verhältnis zur besten (Rauten)."""
    fig = go.Figure()
    xs = [C.RULE_SHORT[r] for r in ev.RULES]
    fig.add_trace(go.Bar(x=xs, y=[a.results[r].covered / a.n for r in ev.RULES], name="Vertretene Wähler", marker_color=[C.RULE_COLORS[r] for r in ev.RULES],
                         hovertemplate="%{x}: %{y:.1%} der Wähler vertreten<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[a.results[r].pav_ratio for r in ev.RULES], mode="markers", name="PAV-Summe (Anteil am besten)", marker=dict(symbol="diamond", size=11, color="#222", line=dict(color="white", width=1)),
                             hovertemplate="%{x}: PAV-Summe %{y:.1%} des besten<extra></extra>"))
    fig.update_yaxes(title_text="Anteil", tickformat=".0%", range=[0, 1.05])
    fig.update_xaxes(type="category")
    return _base(fig, height=360)


def build_camps(a):
    """Sitze je Lager und Regel als gestapelte Säulen; die erste Säule ist der Verhältnisanteil (Wähleranteil mal Sitze)."""
    groups = len(C.MODEL_SHARES[a.settings.model])
    voters = [sum(1 for v in a.voter_camp if v == g) for g in range(groups)]
    xs = ["Anteil der Wähler × Sitze"] + [C.RULE_SHORT[r] for r in ev.RULES]
    fig = go.Figure()
    for g in range(groups):
        ys = [voters[g] / a.n * a.k] + [a.results[r].seats_by_camp[g] for r in ev.RULES]
        fig.add_trace(go.Bar(x=xs, y=ys, name=f"Lager {g + 1} ({voters[g]} Wähler)", marker_color=C.CAMP_COLORS[g], hovertemplate="%{x}: %{y:.1f} Sitze<extra>Lager " + str(g + 1) + "</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Sitze", range=[0, a.k + 0.3])
    fig.update_xaxes(type="category")
    return _base(fig, height=360)


def build_violation_series(rows):
    """Instanzen mit Verletzung der erweiterten gerechtfertigten Repräsentation je Regel, gruppiert nach Lagermodell."""
    fig = go.Figure()
    colors = {"zwei": "#4c78a8", "drei": "#e8a838", "keine": "#2F6B65"}
    for model in C.MODELS:
        sel = [r for r in rows if r["model"] == model]
        fig.add_trace(go.Bar(x=[C.RULE_SHORT[r["rule"]] for r in sel], y=[r["ejr"] / r["runs"] for r in sel], name=C.MODEL_SHORT[model], marker_color=colors[model],
                             hovertemplate="%{x}: %{y:.1%}<extra>" + C.MODEL_SHORT[model] + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Instanzen mit EJR-Verletzung", tickformat=".0%", rangemode="tozero")
    fig.update_xaxes(type="category")
    return _base(fig, height=340)


def build_size_series(rows):
    """Besetzte Sitze von Equal Shares ohne und mit Auffüllen je Lagermodell (Mittel), gegen die fünf Sitze der Reihe."""
    fig = go.Figure()
    for rule in ("es", "esfill"):
        sel = [r for r in rows if r["rule"] == rule]
        fig.add_trace(go.Bar(x=[C.MODEL_SHORT[r["model"]] for r in sel], y=[r["size_mean"] for r in sel], name=C.RULE_SHORT[rule], marker_color=C.RULE_COLORS[rule],
                             hovertemplate="%{x}: %{y:.2f} Sitze<extra>" + C.RULE_SHORT[rule] + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Besetzte Sitze (Mittel)", range=[0, C.SERIES_K + 0.4])
    fig.update_xaxes(type="category")
    return _base(fig, height=320)


def build_greedy_series(rows):
    """Wie nah das gierige Verfahren an das exakte kommt: Mittel (Linie) und schlechtester Fall (Rauten) je Zahl der Sitze, für PAV und Chamberlin–Courant."""
    fig = go.Figure()
    xs = [f"{r['k']} Sitze" for r in rows]
    for key, name, color in (("pav", "Seq. PAV gegen PAV", C.RULE_COLORS["pav"]), ("cc", "Seq. CC gegen CC", C.RULE_COLORS["cc"])):
        fig.add_trace(go.Scatter(x=xs, y=[r[f"{key}_mean"] for r in rows], mode="lines+markers", name=f"{name}: Mittel", line=dict(color=color, width=2.5), hovertemplate="%{x}: %{y:.2%}<extra>" + name + "</extra>"))
        fig.add_trace(go.Scatter(x=xs, y=[r[f"{key}_min"] for r in rows], mode="markers", name=f"{name}: schlechtester Fall", marker=dict(symbol="diamond", size=10, color=color, line=dict(color="#222", width=1)),
                                 hovertemplate="%{x}: %{y:.1%} (schlechtester Fall)<extra>" + name + "</extra>"))
    fig.update_yaxes(title_text="Anteil des exakten Werts", tickformat=".0%", range=[0.88, 1.01])
    fig.update_xaxes(type="category")
    return _base(fig, height=340)
