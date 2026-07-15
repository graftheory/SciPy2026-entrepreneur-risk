"""Build chart.html: an interactive capital/time/risk explorer for the talk."""

import json
import math

import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Data (hand-edit this block as research refines the estimates; see claude.md
# for definitions and sourcing notes per category).
# ---------------------------------------------------------------------------

categories = [
    {
        "id": 1,
        "name": "Pharma (FDA-track)",
        "capital_usd": 15_000_000,
        "capital_range": "3M-20M (seed-to-Series A scale, biotech seed avg $12.1M in 2024, pacing ~$17M in 2025)",
        "time_months": 30,
        "time_range": "24-36",
        "risk_pct": 88,
        "risk_type": "regulatory",
        "data_quality": "risk_pct is Phase-1-to-approval DRUG failure rate (DiMasi/Tufts CSDD), used as a proxy — measures technical/regulatory failure of the lead program, not founder-level financial outcome. Capital reframed to seed-round scale per Definitions, not the full ~$2.6-2.9B lifecycle cost.",
    },
    {
        "id": 2,
        "name": "Medtech (PMA-track devices)",
        "capital_usd": 5_000_000,
        "capital_range": "3M-10M (illustrative — placeholder)",
        "time_months": 30,
        "time_range": "24-36",
        "risk_pct": 65,
        "risk_type": "regulatory",
        "data_quality": "PLACEHOLDER — no sourced founder-level or company-level exit-type data found. Full PMA-cycle cost is $94-118M (Stanford/PwC, HHS study) but that's total company spend, not founder-stability capital. Needs further research.",
    },
    {
        "id": 3,
        "name": "Deep tech (non-pharma, physical, non-defense)",
        "capital_usd": 4_000_000,
        "capital_range": "2M-5M",
        "time_months": 28,
        "time_range": "24-30",
        "risk_pct": 75,
        "risk_type": "technical",
        "data_quality": "PLACEHOLDER risk value. Capital/time anchored loosely to deep tech VC benchmarking (~24% of global VC in 2023, ~$79B, concentrated Series B+). No clean founder-level outcome dataset found.",
    },
    {
        "id": 4,
        "name": "Applied R&D physical product (inventor/engineer)",
        "capital_usd": 250_000,
        "capital_range": "100K-300K",
        "time_months": 18,
        "time_range": "12-24",
        "risk_pct": 55,
        "risk_type": "technical",
        "data_quality": "Capital anchored to Kauffman Firm Survey high-tech-firm average (~$275K). Risk_pct is a PLACEHOLDER.",
    },
    {
        "id": 5,
        "name": "Complex software (heavy R&D / large team)",
        "capital_usd": 4_000_000,
        "capital_range": "2.5M-6M (up to 6-10M for AI-flavored seeds)",
        "time_months": 20,
        "time_range": "18-24",
        "risk_pct": 75,
        "risk_type": "market",
        "data_quality": "Capital from 2025 YC/seed benchmarking data. Risk from Ghosh (HBS): ~75% of VC-backed companies never return capital — this is the CONDITIONAL rate (given funded). See category 7 note on the unconditional rate.",
    },
    {
        "id": 6,
        "name": "Brick & mortar (restaurant)",
        "capital_usd": 300_000,
        "capital_range": "95K-2M, average ~275K-425K",
        "time_months": 12,
        "time_range": "6-18 (note: some markets require ~18mo for liquor licensing alone)",
        "risk_pct": 28,
        "risk_type": "market",
        "data_quality": "Capital from industry restaurant-opening-cost surveys. Risk_pct is an estimate derived from SBA/Census closure-reason data (~25-30% of small-business closures are distress-driven; most restaurant closures are plausibly non-distress, e.g., planned concept changes) — not a restaurant-specific measured figure.",
    },
    {
        "id": 7,
        "name": "Average VC-track tech startup",
        "capital_usd": 1_000_000,
        "capital_range": "pre-seed 100K-1M (median ~500K), seed median $3.1M (2025)",
        "time_months": 15,
        "time_range": "12-18",
        "risk_pct": 75,
        "risk_type": "market",
        "data_quality": "CONDITIONAL risk (given VC funding secured): ~75% of founders get zero equity payout even when funded (Hall & Woodward, n=22,004 VC-backed cos, 1987-2008). UNCONDITIONAL risk, including everyone who tries but never gets funded (~1% of aspiring VC-track founders raise VC at all): approx 99.75% get nothing. STRONGLY consider adding both a 'conditional' and 'unconditional' variant of this category, or a toggle — this distinction is a core teaching point of the talk.",
    },
    {
        "id": 8,
        "name": "Lightweight app (solo dev)",
        "capital_usd": 30_000,
        "capital_range": "near-$0 cash outlay; real cost is founder's foregone salary",
        "time_months": 12,
        "time_range": "6-18 (median 12-18mo to $10K MRR, for those who get there)",
        "risk_pct": 70,
        "risk_type": "market",
        "data_quality": "Risk derived from indie-hacker/MicroConf community survey data (not peer-reviewed, but the best available for this population): ~40% never reach $1K MRR. See separate MRR dataset below for the fuller distribution — worth its own slide/chart per prior discussion.",
    },
    {
        "id": 9,
        "name": "Capital-heavier service (contracting, architecture, tax prep)",
        "capital_usd": 100_000,
        "capital_range": "50K-150K (illustrative)",
        "time_months": 9,
        "time_range": "6-12",
        "risk_pct": 40,
        "risk_type": "market",
        "data_quality": "PLACEHOLDER. BLS shows this NAICS sector (Professional/Scientific/Technical Services) has an ABOVE-average closure rate (25.5% yr1, 65.7% yr10) — but likely disproportionately non-distress given low capital at risk. No sector-specific closure-reason breakdown found.",
    },
    {
        "id": 10,
        "name": "Virtual consulting (founder's education as sunk cost)",
        "capital_usd": 10_000,
        "capital_range": "under 10K",
        "time_months": 4,
        "time_range": "1-6",
        "risk_pct": 30,
        "risk_type": "market",
        "data_quality": "Capital figure sourced (solo remote consultancies startable under $10K). Risk_pct is a PLACEHOLDER anchored loosely to general small-business distress rate (~25-30%, SBA/Census).",
    },
    {
        "id": 11,
        "name": "Small manufacturing / custom fabrication",
        "capital_usd": 100_000,
        "capital_range": "10K-50K bootstrap (used equipment) up to 500K+ (new commercial-grade)",
        "time_months": 12,
        "time_range": "6-12",
        "risk_pct": 45,
        "risk_type": "technical",
        "data_quality": "Capital range sourced from practitioner accounts. Risk_pct is a PLACEHOLDER.",
    },
    {
        "id": 12,
        "name": "AI / local-compute-heavy business",
        "capital_usd": 150_000,
        "capital_range": "near-$0 (cloud API/pay-as-you-go) up to 95K-255K (self-hosted multi-GPU inference server)",
        "time_months": 10,
        "time_range": "6-18",
        "risk_pct": 65,
        "risk_type": "mixed",
        "data_quality": "PLACEHOLDER risk. Note this category is genuinely bimodal (cloud-API vs self-hosted) — consider splitting into two points before finalizing.",
    },
    {
        "id": 13,
        "name": "Software hosting company",
        "capital_usd": 100_000,
        "capital_range": "near-$0 (resell/managed hosting) up to 6-7 figures (own infrastructure/colocation)",
        "time_months": 10,
        "time_range": "6-18",
        "risk_pct": 60,
        "risk_type": "mixed",
        "data_quality": "PLACEHOLDER. Structurally identical spectrum to #12 (rent-vs-own infrastructure); consider merging with #12 visually or keeping separate for narrative clarity.",
    },
]

# ---------------------------------------------------------------------------
# Axis definitions: key -> (label, values getter, is_log)
# ---------------------------------------------------------------------------

AXES = {
    "capital": {
        "label": "Capital needed to reach founder stability ($)",
        "values": [c["capital_usd"] for c in categories],
        "log": True,
    },
    "time": {
        "label": "Time to founder stability (months)",
        "values": [c["time_months"] for c in categories],
        "log": False,
    },
    "risk": {
        "label": "Risk of unplanned/distressed exit (%)",
        "values": [c["risk_pct"] for c in categories],
        "log": False,
    },
}

AXIS_ORDER = ["capital", "time", "risk"]

# Short labels for the dropdown buttons themselves (the full AXES labels are
# used for axis titles, but are far too long for a dropdown button — using
# them there was what made the X/Y axis menus so wide they threw off the
# spacing between all three dropdowns).
AXIS_SHORT_LABELS = {"capital": "Capital", "time": "Time", "risk": "Risk"}
SIZE_SHORT_LABELS = ["Uniform", "By capital"]

RISK_TYPE_COLORS = {
    "market": "#1f77b4",
    "technical": "#d62728",
    "regulatory": "#9467bd",
    "mixed": "#7f7f7f",
}

MIN_MARKER_SIZE = 14
MAX_MARKER_SIZE = 42
UNIFORM_MARKER_SIZE = 22

DIV_ID = "chart-div"

# Split so the title can wrap to two lines (client-side, based on measured
# text width vs. available plot width) when the window gets narrow.
TITLE_LINE1 = "Entrepreneurship: Capital / Time / Failure Risk"
TITLE_LINE2 = "by Business Category"

# customdata layout per point: [name, capital_usd, time_months, risk_pct, risk_type]
HOVERTEMPLATE = (
    "<b>%{customdata[0]}</b><br><br>"
    "Capital: $%{customdata[1]:,.0f}<br>"
    "Time: %{customdata[2]} months<br>"
    "Risk: %{customdata[3]}%<br>"
    "Risk type: %{customdata[4]}"
    "<extra></extra>"
)

risk_type_order = [rt for rt in RISK_TYPE_COLORS if any(c["risk_type"] == rt for c in categories)]


def build_traces(x_key, y_key):
    """One trace per risk type so the legend and color-by-risk-type both work."""
    traces = []
    for risk_type in risk_type_order:
        idx = [i for i, c in enumerate(categories) if c["risk_type"] == risk_type]
        traces.append(
            go.Scatter(
                x=[AXES[x_key]["values"][i] for i in idx],
                y=[AXES[y_key]["values"][i] for i in idx],
                customdata=[
                    [categories[i]["name"], categories[i]["capital_usd"],
                     categories[i]["time_months"], categories[i]["risk_pct"],
                     categories[i]["risk_type"]]
                    for i in idx
                ],
                mode="markers",
                name=risk_type,
                marker=dict(size=UNIFORM_MARKER_SIZE, color=RISK_TYPE_COLORS[risk_type], opacity=0.85),
                hovertemplate=HOVERTEMPLATE,
                hoverlabel=dict(font_size=24, font_family="Arial"),
            )
        )
    return traces


AXIS_TITLE_FONT_SIZE = 22
AXIS_TICK_FONT_SIZE = 18
TITLE_FONT_SIZE = 32
LEGEND_TITLE_FONT_SIZE = 20
LEGEND_ITEM_FONT_SIZE = 18
LEGEND_ITEM_GAP = 14  # vertical px between legend entries — a bit more than default, not double-spaced

# Fixed pixel row-heights for the header band (title / label row / dropdown
# row) stacked above the plot. These are deliberately plain pixels, not
# fractions — margin.t and the label/dropdown y-positions are then derived
# from them (in JS, recomputed on every resize) so the vertical rhythm stays
# constant regardless of window size, instead of drifting the way "paper"
# fractions do as the plot area's pixel height changes.
TOP_PADDING = 12
TITLE_LINE_HEIGHT = round(TITLE_FONT_SIZE * 1.3)
GAP_TITLE_LABEL = 22
LABEL_HEIGHT = 20
GAP_LABEL_DROPDOWN = 8
DROPDOWN_HEIGHT = 30
GAP_DROPDOWN_PLOT = 10
MARGIN_B = 60

MARGIN_T = TOP_PADDING + TITLE_LINE_HEIGHT + GAP_TITLE_LABEL + LABEL_HEIGHT + GAP_LABEL_DROPDOWN + DROPDOWN_HEIGHT + GAP_DROPDOWN_PLOT
MARGIN_T_WRAPPED = MARGIN_T + TITLE_LINE_HEIGHT


def axis_layout(key):
    axis = AXES[key]
    layout = dict(
        title=dict(text=axis["label"], font=dict(size=AXIS_TITLE_FONT_SIZE)),
        tickfont=dict(size=AXIS_TICK_FONT_SIZE),
    )
    if axis["log"]:
        layout["type"] = "log"
    return layout


def skip_buttons(labels):
    return [dict(label=label, method="skip", args=[]) for label in labels]


def build_post_script():
    """Client-side state machine driving the three dropdowns.

    Plotly's native updatemenu buttons are stateless (each fully re-specifies
    the resulting figure), which would make the X and Y dropdowns stomp on
    each other's current selection. Instead every button here uses
    method="skip" and a small JS state machine recomputes x/y/marker-size
    from each point's customdata (already carrying capital/time/risk) on every
    click, so the two axis dropdowns and the size toggle stay independent.
    """
    capital_sqrts = [math.sqrt(c["capital_usd"]) for c in categories]
    min_sqrt, max_sqrt = min(capital_sqrts), max(capital_sqrts)
    axis_meta = {k: {"label": AXES[k]["label"], "log": AXES[k]["log"]} for k in AXIS_ORDER}

    return f"""
    (function() {{
        var gd = document.getElementById("{DIV_ID}");
        var AXIS_ORDER = {json.dumps(AXIS_ORDER)};
        var AXIS_META = {json.dumps(axis_meta)};
        var MIN_SQRT = {json.dumps(min_sqrt)}, MAX_SQRT = {json.dumps(max_sqrt)};
        var MIN_SIZE = {json.dumps(MIN_MARKER_SIZE)}, MAX_SIZE = {json.dumps(MAX_MARKER_SIZE)}, UNIFORM_SIZE = {json.dumps(UNIFORM_MARKER_SIZE)};
        var currentX = "capital", currentY = "time", sizeByCapital = false;

        function valueFor(cd, key) {{
            if (key === "capital") return cd[1];
            if (key === "time") return cd[2];
            return cd[3];
        }}

        function sizeFor(capitalUsd) {{
            if (!sizeByCapital || currentX === "capital" || currentY === "capital") return UNIFORM_SIZE;
            if (MAX_SQRT === MIN_SQRT) return MIN_SIZE;
            var t = (Math.sqrt(capitalUsd) - MIN_SQRT) / (MAX_SQRT - MIN_SQRT);
            return MIN_SIZE + t * (MAX_SIZE - MIN_SIZE);
        }}

        function recompute() {{
            var xArrays = [], yArrays = [], sizeArrays = [];
            gd.data.forEach(function(trace) {{
                var xs = [], ys = [], sizes = [];
                trace.customdata.forEach(function(cd) {{
                    xs.push(valueFor(cd, currentX));
                    ys.push(valueFor(cd, currentY));
                    sizes.push(sizeFor(cd[1]));
                }});
                xArrays.push(xs); yArrays.push(ys); sizeArrays.push(sizes);
            }});
            Plotly.restyle(gd, {{x: xArrays, y: yArrays, "marker.size": sizeArrays}});
            Plotly.relayout(gd, {{
                "xaxis.title.text": AXIS_META[currentX].label,
                "xaxis.type": AXIS_META[currentX].log ? "log" : "linear",
                "yaxis.title.text": AXIS_META[currentY].label,
                "yaxis.type": AXIS_META[currentY].log ? "log" : "linear",
            }});
        }}

        gd.on("plotly_buttonclicked", function(evt) {{
            var menuIdx = gd._fullLayout.updatemenus.indexOf(evt.menu);
            if (menuIdx === 0) currentX = AXIS_ORDER[evt.active];
            else if (menuIdx === 1) currentY = AXIS_ORDER[evt.active];
            else if (menuIdx === 2) sizeByCapital = (evt.active === 1);
            recompute();
        }});

        // Lock the chart to a 16:9 box regardless of window/screen shape —
        // fills whichever dimension is the tighter constraint, letterboxing
        // the other (see body background) so it looks right on any laptop
        // and matches a 16:9 projector without relying on the browser window
        // itself being 16:9.
        var ASPECT = 16 / 9;

        // Header layout (title / "X axis"-etc. labels / dropdown row), all
        // stacked above the plot. Plotly only lets the title live in
        // "container" coordinates (a fraction of the *whole* canvas) while
        // the labels and dropdown menus only support "paper" coordinates (a
        // fraction of the plot area) — those two references don't scale
        // together as the window resizes, which is what caused the title to
        // drift into, or away from, the row below it. So instead we treat
        // each row's height as a fixed pixel constant, and on every resize
        // recompute both margin.t and every element's fractional position
        // from those fixed pixel heights and the current container size —
        // that keeps the physical (pixel) spacing constant regardless of
        // window size, rather than leaving it to drift.
        var TITLE_LINE1 = {json.dumps(TITLE_LINE1)};
        var TITLE_LINE2 = {json.dumps(TITLE_LINE2)};
        var TOP_PADDING = {json.dumps(TOP_PADDING)};
        var TITLE_LINE_HEIGHT = {json.dumps(TITLE_LINE_HEIGHT)};
        var GAP_TITLE_LABEL = {json.dumps(GAP_TITLE_LABEL)};
        var LABEL_HEIGHT = {json.dumps(LABEL_HEIGHT)};
        var GAP_LABEL_DROPDOWN = {json.dumps(GAP_LABEL_DROPDOWN)};
        var DROPDOWN_HEIGHT = {json.dumps(DROPDOWN_HEIGHT)};
        var GAP_DROPDOWN_PLOT = {json.dumps(GAP_DROPDOWN_PLOT)};
        var MARGIN_B = {json.dumps(MARGIN_B)};

        // Measure the ACTUAL rendered width of the single-line title once,
        // right after the initial draw (text width depends only on
        // font/content, not container size, so one measurement is reusable)
        // rather than estimating with an offscreen canvas: a canvas estimate
        // systematically under-measured versus Plotly's real SVG text
        // rendering, so the title kept overflowing the window before wrapping.
        var titleEl = gd.querySelector("text.gtitle");
        var titleOneLineWidth = titleEl ? titleEl.getBBox().width : 0;
        var titleWrapped = false;

        function layoutHeader(containerWidthPx, containerHeightPx) {{
            titleWrapped = titleOneLineWidth + 30 > containerWidthPx;
            var lineCount = titleWrapped ? 2 : 1;
            var titleHeight = lineCount * TITLE_LINE_HEIGHT;
            var marginT = TOP_PADDING + titleHeight + GAP_TITLE_LABEL + LABEL_HEIGHT
                + GAP_LABEL_DROPDOWN + DROPDOWN_HEIGHT + GAP_DROPDOWN_PLOT;
            var plotAreaHeight = containerHeightPx - marginT - MARGIN_B;

            var titleY = 1 - (TOP_PADDING / containerHeightPx);
            var labelCenterOffset = TOP_PADDING + titleHeight + GAP_TITLE_LABEL + LABEL_HEIGHT / 2;
            var labelY = 1 + (marginT - labelCenterOffset) / plotAreaHeight;
            var dropdownTopOffset = TOP_PADDING + titleHeight + GAP_TITLE_LABEL + LABEL_HEIGHT + GAP_LABEL_DROPDOWN;
            var dropdownY = 1 + (marginT - dropdownTopOffset) / plotAreaHeight;

            var text = titleWrapped
                ? "<b>" + TITLE_LINE1 + "<br>" + TITLE_LINE2 + "</b>"
                : "<b>" + TITLE_LINE1 + " " + TITLE_LINE2 + "</b>";

            Plotly.relayout(gd, {{
                "title.text": text,
                "title.y": titleY,
                "margin.t": marginT,
                "annotations[0].y": labelY, "annotations[1].y": labelY, "annotations[2].y": labelY,
                "updatemenus[0].y": dropdownY, "updatemenus[1].y": dropdownY, "updatemenus[2].y": dropdownY,
            }});
        }}

        // Lock the chart to a 16:9 box regardless of window/screen shape —
        // fills whichever dimension is the tighter constraint, letterboxing
        // the other (see body background) so it looks right on any laptop
        // and matches a 16:9 projector without relying on the browser window
        // itself being 16:9.
        var ASPECT = 16 / 9;
        function fitAspect() {{
            var vw = window.innerWidth, vh = window.innerHeight;
            var w = vw, h = vw / ASPECT;
            if (h > vh) {{ h = vh; w = vh * ASPECT; }}
            gd.style.width = w + "px";
            gd.style.height = h + "px";
            Plotly.Plots.resize(gd);
            layoutHeader(w, h);
        }}
        window.addEventListener("resize", fitAspect);
        fitAspect();
    }})();
    """


def main():
    default_x, default_y = "capital", "time"

    fig = go.Figure()
    for tr in build_traces(default_x, default_y):
        fig.add_trace(tr)

    fig.update_layout(
        # Static fallback values only — the post_script's layoutHeader() runs
        # immediately on load and recomputes title.y, margin.t, and the
        # label/dropdown y-positions from fixed pixel row-heights (see the
        # comment there for why), so these just need to be reasonable before
        # that first pass runs.
        title=dict(
            text=f"<b>{TITLE_LINE1} {TITLE_LINE2}</b>",
            x=0.5, xanchor="center",
            y=0.98, yanchor="top",
            font=dict(size=TITLE_FONT_SIZE),
        ),
        xaxis=axis_layout(default_x),
        yaxis=axis_layout(default_y),
        legend=dict(
            title=dict(text="<b>Risk Type</b>", font=dict(size=LEGEND_TITLE_FONT_SIZE)),
            font=dict(size=LEGEND_ITEM_FONT_SIZE),
            tracegroupgap=LEGEND_ITEM_GAP,
            # Pin the legend's top edge to the plot's top edge so it only
            # grows downward into the plot — otherwise its default vertical
            # anchor lets it bleed upward into the dropdown row above.
            x=1.02, xanchor="left", y=1, yanchor="top",
        ),
        template="plotly_white",
        margin=dict(t=MARGIN_T, b=MARGIN_B),
        # Evenly space all three dropdowns across the plot width using the
        # same "center" anchor for each, so — now that their button labels
        # are similar lengths (see AXIS_SHORT_LABELS/SIZE_SHORT_LABELS) — the
        # gaps between them come out even instead of lopsided.
        updatemenus=[
            dict(buttons=skip_buttons([AXIS_SHORT_LABELS[k] for k in AXIS_ORDER]),
                 direction="down", x=1 / 6, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, pad=dict(r=10, t=10)),
            dict(buttons=skip_buttons([AXIS_SHORT_LABELS[k] for k in AXIS_ORDER]),
                 direction="down", x=0.5, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, active=1, pad=dict(r=10, t=10)),
            dict(buttons=skip_buttons(SIZE_SHORT_LABELS),
                 direction="down", x=5 / 6, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, pad=dict(r=10, t=10)),
        ],
        annotations=[
            dict(text="X axis", x=1 / 6, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
            dict(text="Y axis", x=0.5, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
            dict(text="Point size", x=5 / 6, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
        ],
    )

    plot_fragment = fig.to_html(
        include_plotlyjs=True,
        full_html=False,
        div_id=DIV_ID,
        post_script=build_post_script(),
        # The modebar's zoom/pan/camera icons (top-right, shown on hover)
        # aren't part of the spec — only the dropdowns and hover tooltips are
        # — and they were overlapping the title whenever the presenter moved
        # the mouse to trigger a point's tooltip. Hiding it removes that
        # overlap entirely.
        config={"displayModeBar": False},
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Entrepreneurship: Capital / Time / Risk Explorer</title>
<style>
  html, body {{ margin: 0; height: 100%; background: #111; overflow: hidden; }}
  #{DIV_ID} {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #fff; }}
</style>
</head>
<body>
{plot_fragment}
</body>
</html>
"""

    with open("chart.html", "w", encoding="utf-8") as f:
        f.write(page)
    print("Wrote chart.html")


if __name__ == "__main__":
    main()
