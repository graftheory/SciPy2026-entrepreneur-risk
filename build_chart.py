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
        "market_risk_score": 85,
        "technical_risk_score": 85,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs. market_risk here is driven primarily by FDA regulatory approval and payer/reimbursement gates, not end-patient demand uncertainty — patients want effective treatments; the customer segments that must actually be satisfied are regulators and payers. technical_risk reflects the historical ~90% clinical-trial failure rate for novel drug candidates. risk_pct is unchanged: Phase-1-to-approval DRUG failure rate (DiMasi/Tufts CSDD), used as a proxy — measures technical/regulatory failure of the lead program, not founder-level financial outcome. Capital reframed to seed-round scale per Definitions, not the full ~$2.6-2.9B lifecycle cost.",
    },
    {
        "id": 2,
        "name": "Medtech (PMA-track devices)",
        "capital_usd": 5_000_000,
        "capital_range": "3M-10M (illustrative — placeholder)",
        "time_months": 30,
        "time_range": "24-36",
        "risk_pct": 65,
        "market_risk_score": 75,
        "technical_risk_score": 60,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs. market_risk here is driven primarily by FDA PMA approval, payer reimbursement, and provider (hospital/clinician) adoption gates — not end-patient demand. technical_risk reflects device engineering/clinical-performance risk. risk_pct: PLACEHOLDER — no sourced founder-level or company-level exit-type data found. Full PMA-cycle cost is $94-118M (Stanford/PwC, HHS study) but that's total company spend, not founder-stability capital. Needs further research.",
    },
    {
        "id": 3,
        "name": "Deep tech (non-pharma, physical, non-defense)",
        "capital_usd": 4_000_000,
        "capital_range": "2M-5M",
        "time_months": 28,
        "time_range": "24-30",
        "risk_pct": 75,
        "market_risk_score": 40,
        "technical_risk_score": 80,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; technical_risk dominates (fundamental feasibility risk) with more modest market_risk (real, but more tractable once the technology works). risk_pct: PLACEHOLDER risk value. Capital/time anchored loosely to deep tech VC benchmarking (~24% of global VC in 2023, ~$79B, concentrated Series B+). No clean founder-level outcome dataset found.",
    },
    {
        "id": 4,
        "name": "Applied R&D physical product (inventor/engineer)",
        "capital_usd": 250_000,
        "capital_range": "100K-300K",
        "time_months": 18,
        "time_range": "12-24",
        "risk_pct": 55,
        "market_risk_score": 40,
        "technical_risk_score": 60,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; technical_risk (engineering/prototyping/manufacturing) somewhat exceeds market_risk here. Capital anchored to Kauffman Firm Survey high-tech-firm average (~$275K). risk_pct is a PLACEHOLDER.",
    },
    {
        "id": 5,
        "name": "Complex software (heavy R&D / large team)",
        "capital_usd": 4_000_000,
        "capital_range": "2.5M-6M (up to 6-10M for AI-flavored seeds)",
        "time_months": 20,
        "time_range": "18-24",
        "risk_pct": 75,
        "market_risk_score": 70,
        "technical_risk_score": 40,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; market_risk (product-market fit, competitive dynamics) clearly dominates — building the software is hard but usually achievable given enough R&D investment. Capital from 2025 YC/seed benchmarking data. risk_pct from Ghosh (HBS): ~75% of VC-backed companies never return capital — this is the CONDITIONAL rate (given funded). See category 7 note on the unconditional rate.",
    },
    {
        "id": 6,
        "name": "Brick & mortar (restaurant)",
        "capital_usd": 300_000,
        "capital_range": "95K-2M, average ~275K-425K",
        "time_months": 12,
        "time_range": "6-18 (note: some markets require ~18mo for liquor licensing alone)",
        "risk_pct": 28,
        "market_risk_score": 55,
        "technical_risk_score": 15,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; market_risk (will customers come, concept/location fit) clearly dominates — the operational/technical side of running a restaurant is well-understood. Capital from industry restaurant-opening-cost surveys. risk_pct is an estimate derived from SBA/Census closure-reason data (~25-30% of small-business closures are distress-driven; most restaurant closures are plausibly non-distress, e.g., planned concept changes) — not a restaurant-specific measured figure.",
    },
    {
        "id": 7,
        "name": "Average VC-track tech startup",
        "capital_usd": 1_000_000,
        "capital_range": "pre-seed 100K-1M (median ~500K), seed median $3.1M (2025)",
        "time_months": 15,
        "time_range": "12-18",
        "risk_pct": 75,
        "market_risk_score": 75,
        "technical_risk_score": 35,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; market_risk (product-market fit) clearly dominates for an 'average' (non-deep-tech) startup, where building the product itself is usually feasible. risk_pct: CONDITIONAL risk (given VC funding secured): ~75% of founders get zero equity payout even when funded (Hall & Woodward, n=22,004 VC-backed cos, 1987-2008). UNCONDITIONAL risk, including everyone who tries but never gets funded (~1% of aspiring VC-track founders raise VC at all): approx 99.75% get nothing. STRONGLY consider adding both a 'conditional' and 'unconditional' variant of this category, or a toggle — this distinction is a core teaching point of the talk.",
    },
    {
        "id": 8,
        "name": "Lightweight app (solo dev)",
        "capital_usd": 30_000,
        "capital_range": "near-$0 cash outlay; real cost is founder's foregone salary",
        "time_months": 12,
        "time_range": "6-18 (median 12-18mo to $10K MRR, for those who get there)",
        "risk_pct": 70,
        "market_risk_score": 70,
        "technical_risk_score": 20,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; market_risk (finding paying users in a crowded app market) clearly dominates — building a lightweight app solo is usually straightforward. risk_pct derived from indie-hacker/MicroConf community survey data (not peer-reviewed, but the best available for this population): ~40% never reach $1K MRR. See separate MRR dataset below for the fuller distribution — worth its own slide/chart per prior discussion.",
    },
    {
        "id": 9,
        "name": "Capital-heavier service (contracting, architecture, tax prep)",
        "capital_usd": 100_000,
        "capital_range": "50K-150K (illustrative)",
        "time_months": 9,
        "time_range": "6-12",
        "risk_pct": 40,
        "market_risk_score": 40,
        "technical_risk_score": 15,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; market_risk (finding/retaining clients) clearly dominates — delivering the professional service itself is low-uncertainty, established expertise. risk_pct: PLACEHOLDER. BLS shows this NAICS sector (Professional/Scientific/Technical Services) has an ABOVE-average closure rate (25.5% yr1, 65.7% yr10) — but likely disproportionately non-distress given low capital at risk. No sector-specific closure-reason breakdown found.",
    },
    {
        "id": 10,
        "name": "Virtual consulting (founder's education as sunk cost)",
        "capital_usd": 10_000,
        "capital_range": "under 10K",
        "time_months": 4,
        "time_range": "1-6",
        "risk_pct": 30,
        "market_risk_score": 40,
        "technical_risk_score": 10,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; market_risk (finding clients as a solo consultant) clearly dominates — delivering consulting from existing expertise is very low technical uncertainty. Capital figure sourced (solo remote consultancies startable under $10K). risk_pct is a PLACEHOLDER anchored loosely to general small-business distress rate (~25-30%, SBA/Census).",
    },
    {
        "id": 11,
        "name": "Small manufacturing / custom fabrication",
        "capital_usd": 100_000,
        "capital_range": "10K-50K bootstrap (used equipment) up to 500K+ (new commercial-grade)",
        "time_months": 12,
        "time_range": "6-12",
        "risk_pct": 45,
        "market_risk_score": 35,
        "technical_risk_score": 55,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs; technical_risk (fabrication process/equipment/yield reliability) somewhat exceeds market_risk here. Capital range sourced from practitioner accounts. risk_pct is a PLACEHOLDER.",
    },
    {
        "id": 12,
        "name": "AI / local-compute-heavy business",
        "capital_usd": 150_000,
        "capital_range": "near-$0 (cloud API/pay-as-you-go) up to 95K-255K (self-hosted multi-GPU inference server)",
        "time_months": 10,
        "time_range": "6-18",
        "risk_pct": 65,
        "market_risk_score": 65,
        "technical_risk_score": 60,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs, both comparably high (commoditizing/competitive AI product space drives market_risk; whether the system performs reliably at spec — especially the self-hosted variant — drives technical_risk). This replaces the old hand-assigned 'market/technical' hybrid label with a derived both-high classification. risk_pct is a PLACEHOLDER. Note this category is genuinely bimodal (cloud-API vs self-hosted) — consider splitting into two points before finalizing.",
    },
    {
        "id": 13,
        "name": "Software hosting company",
        "capital_usd": 100_000,
        "capital_range": "near-$0 (resell/managed hosting) up to 6-7 figures (own infrastructure/colocation)",
        "time_months": 10,
        "time_range": "6-18",
        "risk_pct": 60,
        "market_risk_score": 60,
        "technical_risk_score": 55,
        "data_quality": "market_risk_score and technical_risk_score are illustrative PLACEHOLDERs, both comparably high (commoditized/competitive hosting market drives market_risk; infrastructure reliability/uptime engineering drives technical_risk). This replaces the old hand-assigned 'market/technical' hybrid label with a derived both-high classification. risk_pct is a PLACEHOLDER. Structurally identical spectrum to #12 (rent-vs-own infrastructure); consider merging with #12 visually or keeping separate for narrative clarity.",
    },
]

# ---------------------------------------------------------------------------
# Axis definitions: key -> (label, values getter, is_log)
# ---------------------------------------------------------------------------

AXES = {
    "capital": {
        "label": "Capital needed to reach founder stability ($)",
        "values": [c["capital_usd"] for c in categories],
        # Starts linear; toggled live via the Capital scale dropdown (see
        # capitalLog in build_post_script) rather than fixed — this "log"
        # flag is just capital's *initial* state, unlike time/risk below
        # where it's permanent.
        "log": False,
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
    "market_risk": {
        "label": "Market risk score (0-100, illustrative)",
        "values": [c["market_risk_score"] for c in categories],
        "log": False,
    },
    "technical_risk": {
        "label": "Technical risk score (0-100, illustrative)",
        "values": [c["technical_risk_score"] for c in categories],
        "log": False,
    },
}

AXIS_ORDER = ["capital", "time", "risk", "market_risk", "technical_risk"]

# The X/Y dropdowns additionally offer "None" (see build_post_script's
# recompute() for what that triggers); the Size dropdown does not, so it
# keeps using AXIS_ORDER directly.
AXIS_ORDER_XY = AXIS_ORDER + ["none"]

# Short labels for the dropdown buttons themselves (the full AXES labels are
# used for axis titles, but are far too long for a dropdown button — using
# them there was what made the X/Y axis menus so wide they threw off the
# spacing between all three dropdowns). "Mkt risk"/"Tech risk" are kept
# short rather than "Market risk"/"Technical risk" for the same reason —
# the widest option in a dropdown's list sets that dropdown's width, and a
# much-wider option would throw off the five-way even spacing again.
AXIS_SHORT_LABELS = {
    "capital": "Capital", "time": "Time", "risk": "Risk",
    "market_risk": "Mkt risk", "technical_risk": "Tech risk", "none": "None",
}
SIZE_SHORT_LABELS = ["Uniform", "By capital"]
CAPITAL_SCALE_LABELS = ["Linear", "Log"]
COLOR_TOGGLE_LABELS = ["Off", "On"]

# Flat marker color used for every point when the color-by-risk-type toggle
# is off. Distinct from the "regulatory" gray (#7f7f7f) so neutral mode
# doesn't look like a risk-type color itself.
NEUTRAL_MARKER_COLOR = "#404040"

# When one axis is "None", the remaining data axis renders as a horizontal
# dot plot (categorical rows on Y, sorted by this data axis's value; see
# recompute() in build_post_script). Descending for all five — largest value
# at the top row, decreasing as you read down — matching the standard
# ranked-bar-chart/leaderboard convention, and consistent across axes rather
# than flipping direction depending on which one is selected.
SORT_DIRECTION = {"capital": "desc", "time": "desc", "risk": "desc", "market_risk": "desc", "technical_risk": "desc"}

# Color is now DERIVED from market_risk_score/technical_risk_score at build
# time, rather than a hand-assigned category — see classify_quadrant().
# Threshold/margin are named constants specifically so they're easy to tune
# per the spec; both are on the 0-100 score scale.
QUADRANT_THRESHOLD = 50  # "high" vs "low" boundary for a single score
QUADRANT_MARGIN = 15  # point gap beyond which one score counts as "clearly" higher than the other


def classify_quadrant(market_score, technical_score):
    """market-dominant / technical-dominant / both-high / both-low.

    Dominance (a >15-point gap either way) is checked before the high/low
    split, so e.g. a 40 vs 80 pair is technical-dominant even though 40 is
    itself below the threshold — relative gap wins over absolute level.
    Only once the two scores are within the margin of each other (neither
    clearly dominant) do both-high/both-low apply; the spec doesn't say
    what happens if that "comparable" pair straddles the threshold (e.g.
    55 vs 48), so that edge case is resolved here by comparing their
    average to the threshold.
    """
    diff = market_score - technical_score
    if diff > QUADRANT_MARGIN:
        return "market-dominant"
    if diff < -QUADRANT_MARGIN:
        return "technical-dominant"
    if (market_score + technical_score) / 2 >= QUADRANT_THRESHOLD:
        return "both-high"
    return "both-low"


# Dict order is also legend order. Colors reused 1:1 from the old
# risk_type scheme (see prior color-toggle work) so the visual language
# doesn't change mid-talk: gray/red/blue/purple in the same relative slots.
QUADRANT_COLORS = {
    "both-low": "#7f7f7f",  # gray — repurposed from "regulatory"; no category maps to gray for regulatory reasons anymore
    "market-dominant": "#d62728",  # red, same as old "market"
    "technical-dominant": "#1f77b4",  # blue, same as old "technical"
    "both-high": "#9467bd",  # purple, same as old "market/technical" hybrid — now a precise quadrant instead of a hand-picked label
}

# Legend text — wrapped with <br> since these phrases are too wide for the
# legend's margin as a single line (worse than the old "market/technical").
QUADRANT_LEGEND_LABELS = {
    "both-low": "Low market +<br>low technical",
    "market-dominant": "Market-dominant<br>risk",
    "technical-dominant": "Technical-dominant<br>risk",
    "both-high": "High market +<br>high technical",
}

# Hover tooltip text — same phrases, unwrapped (hover has more room, and a
# literal "<br>" would just show as a mid-sentence break there).
QUADRANT_HOVER_LABELS = {
    "both-low": "Low market + low technical",
    "market-dominant": "Market-dominant risk",
    "technical-dominant": "Technical-dominant risk",
    "both-high": "High market + high technical",
}

MIN_MARKER_SIZE = 14
MAX_MARKER_SIZE = 42
UNIFORM_MARKER_SIZE = 22

DIV_ID = "chart-div"

# Wrapped client-side into as many lines as the window width needs (greedy
# word-wrap, not a single fixed break point — see build_post_script).
TITLE_TEXT = "Entrepreneurship: Capital / Time / Failure Risk by Business Category"

# customdata layout per point:
# [name, capital_usd, time_months, risk_pct, market_risk_score, technical_risk_score, quadrant_hover_label]
HOVERTEMPLATE = (
    "<b>%{customdata[0]}</b><br><br>"
    "Capital: $%{customdata[1]:,.0f}<br>"
    "Time: %{customdata[2]} months<br>"
    "Risk: %{customdata[3]}%<br>"
    "Market risk: %{customdata[4]}<br>"
    "Technical risk: %{customdata[5]}<br>"
    "Classification: %{customdata[6]}"
    "<extra></extra>"
)

category_quadrants = [classify_quadrant(c["market_risk_score"], c["technical_risk_score"]) for c in categories]
quadrant_order = [q for q in QUADRANT_COLORS if q in category_quadrants]


def build_traces(x_key, y_key):
    """One trace per quadrant so the legend and color-by-quadrant both work."""
    traces = []
    for quadrant in quadrant_order:
        idx = [i for i, q in enumerate(category_quadrants) if q == quadrant]
        traces.append(
            go.Scatter(
                x=[AXES[x_key]["values"][i] for i in idx],
                y=[AXES[y_key]["values"][i] for i in idx],
                customdata=[
                    [categories[i]["name"], categories[i]["capital_usd"],
                     categories[i]["time_months"], categories[i]["risk_pct"],
                     categories[i]["market_risk_score"], categories[i]["technical_risk_score"],
                     QUADRANT_HOVER_LABELS[quadrant]]
                    for i in idx
                ],
                mode="markers",
                name=QUADRANT_LEGEND_LABELS[quadrant],
                marker=dict(size=UNIFORM_MARKER_SIZE, color=QUADRANT_COLORS[quadrant], opacity=0.85),
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
        var AXIS_ORDER_XY = {json.dumps(AXIS_ORDER_XY)};
        var AXIS_META = {json.dumps(axis_meta)};
        var SORT_DIRECTION = {json.dumps(SORT_DIRECTION)};
        var AXIS_TICK_FONT_SIZE = {json.dumps(AXIS_TICK_FONT_SIZE)};
        var MIN_SQRT = {json.dumps(min_sqrt)}, MAX_SQRT = {json.dumps(max_sqrt)};
        var MIN_SIZE = {json.dumps(MIN_MARKER_SIZE)}, MAX_SIZE = {json.dumps(MAX_MARKER_SIZE)}, UNIFORM_SIZE = {json.dumps(UNIFORM_MARKER_SIZE)};
        var NEUTRAL_MARKER_COLOR = {json.dumps(NEUTRAL_MARKER_COLOR)};
        var currentX = "capital", currentY = "time", sizeByCapital = false;
        // Global — capital's scale, independent of whether it's currently on
        // X, Y, or the sole data axis in a dot plot, and independent of
        // whatever the presenter does with the other dropdowns afterward.
        var capitalLog = false;
        // Updated by layoutHeader() on every resize so recompute() can size
        // dot-plot row labels against the *current* plot area, not a stale one.
        var currentPlotAreaHeight = 300;

        // Color-by-risk-type toggle. Captures each trace's ACTUAL current
        // marker color at load — rather than hardcoding the four category
        // names/colors — so this keeps working unmodified if the underlying
        // categorical field is later replaced by a derived classification
        // (e.g. a market/technical-score quadrant): whatever traces and
        // colors exist at load time is what gets restored when toggled back
        // on. Starts off (per spec), so this is applied once immediately.
        var colorOn = false;
        var originalColors = gd.data.map(function(trace) {{ return trace.marker.color; }});

        function applyColorMode() {{
            var colors = colorOn
                ? originalColors
                : gd.data.map(function() {{ return NEUTRAL_MARKER_COLOR; }});
            Plotly.restyle(gd, {{"marker.color": colors}});
            Plotly.relayout(gd, {{showlegend: colorOn}});
        }}

        function valueFor(cd, key) {{
            if (key === "capital") return cd[1];
            if (key === "time") return cd[2];
            if (key === "risk") return cd[3];
            if (key === "market_risk") return cd[4];
            if (key === "technical_risk") return cd[5];
        }}

        // Time/risk are permanently linear; capital's type follows the
        // live toggle instead of the static AXIS_META flag.
        function axisTypeFor(key) {{
            if (key === "capital") return capitalLog ? "log" : "linear";
            return AXIS_META[key].log ? "log" : "linear";
        }}

        function sizeFor(capitalUsd) {{
            if (!sizeByCapital || currentX === "capital" || currentY === "capital") return UNIFORM_SIZE;
            if (MAX_SQRT === MIN_SQRT) return MIN_SIZE;
            var t = (Math.sqrt(capitalUsd) - MIN_SQRT) / (MAX_SQRT - MIN_SQRT);
            return MIN_SIZE + t * (MAX_SIZE - MIN_SIZE);
        }}

        // Plain 2D scatter: both axes are a real data key.
        function recomputeScatter() {{
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
                "xaxis.type": axisTypeFor(currentX),
                "yaxis.title.text": AXIS_META[currentY].label,
                "yaxis.type": axisTypeFor(currentY),
                "yaxis.tickvals": null, "yaxis.ticktext": null, "yaxis.range": null,
                "yaxis.tickfont.size": AXIS_TICK_FONT_SIZE, "yaxis.automargin": false,
            }});
        }}

        // Horizontal dot plot: exactly one axis is "none". The remaining
        // data axis always renders along X (reoriented there even if it was
        // picked via the Y dropdown) with category-name rows on Y, sorted by
        // that data axis's value — this keeps the category names horizontal
        // and legible however the user got here, rather than a vertical
        // dot plot with rotated/truncated labels when X is the one set to
        // "none".
        function recomputeDotPlot(dataKey) {{
            var xArrays = [], yArrays = [], sizeArrays = [];
            var allPoints = [];
            gd.data.forEach(function(trace, traceIdx) {{
                var xs = [], ys = [], sizes = [];
                trace.customdata.forEach(function(cd, pointIdx) {{
                    var val = valueFor(cd, dataKey);
                    xs.push(val);
                    ys.push(0); // placeholder; filled in below once rows are sorted
                    sizes.push(sizeFor(cd[1]));
                    allPoints.push({{traceIdx: traceIdx, pointIdx: pointIdx, name: cd[0], value: val}});
                }});
                xArrays.push(xs); yArrays.push(ys); sizeArrays.push(sizes);
            }});

            var dir = SORT_DIRECTION[dataKey];
            allPoints.sort(function(a, b) {{ return dir === "asc" ? a.value - b.value : b.value - a.value; }});
            var n = allPoints.length;
            var tickvals = [], ticktext = [];
            allPoints.forEach(function(p, rank) {{
                var row = (n - 1) - rank; // rank 0 (first in sorted order) sits at the top row
                yArrays[p.traceIdx][p.pointIdx] = row;
                tickvals.push(row);
                ticktext.push(p.name);
            }});

            // Shrink (never enlarge) the row-label font if there isn't
            // enough vertical room for all n rows to stay legible without
            // overlapping, given the plot's *current* pixel height.
            var rowHeight = currentPlotAreaHeight / n;
            var rowFontSize = Math.max(9, Math.min(AXIS_TICK_FONT_SIZE, Math.floor(rowHeight * 0.55)));

            Plotly.restyle(gd, {{x: xArrays, y: yArrays, "marker.size": sizeArrays}});
            Plotly.relayout(gd, {{
                "xaxis.title.text": AXIS_META[dataKey].label,
                "xaxis.type": axisTypeFor(dataKey),
                "yaxis.title.text": "",
                "yaxis.type": "linear",
                "yaxis.tickvals": tickvals,
                "yaxis.ticktext": ticktext,
                "yaxis.range": [-0.5, n - 0.5],
                "yaxis.tickfont.size": rowFontSize,
                // Reserve however much left margin the longest category name
                // needs, rather than a fixed margin that would truncate it.
                "yaxis.automargin": true,
            }});
        }}

        function recompute() {{
            var noneX = currentX === "none", noneY = currentY === "none";
            if (noneX && noneY) return; // guarded against at the click handler; no-op if reached anyway
            if (!noneX && !noneY) {{ recomputeScatter(); return; }}
            recomputeDotPlot(noneX ? currentY : currentX);
        }}

        gd.on("plotly_buttonclicked", function(evt) {{
            var menuIdx = gd._fullLayout.updatemenus.indexOf(evt.menu);
            if (menuIdx === 0) {{
                var newX = AXIS_ORDER_XY[evt.active];
                if (newX === "none" && currentY === "none") {{
                    // Both axes "none" would be a degenerate plot — keep the
                    // last valid single-axis view and undo the dropdown's
                    // own highlight so the UI doesn't show a selection we
                    // didn't actually apply.
                    Plotly.relayout(gd, {{"updatemenus[0].active": AXIS_ORDER_XY.indexOf(currentX)}});
                    return;
                }}
                currentX = newX;
            }} else if (menuIdx === 1) {{
                var newY = AXIS_ORDER_XY[evt.active];
                if (newY === "none" && currentX === "none") {{
                    Plotly.relayout(gd, {{"updatemenus[1].active": AXIS_ORDER_XY.indexOf(currentY)}});
                    return;
                }}
                currentY = newY;
            }} else if (menuIdx === 2) {{
                sizeByCapital = (evt.active === 1);
            }} else if (menuIdx === 3) {{
                capitalLog = (evt.active === 1); // 0 = Linear, 1 = Log
            }} else if (menuIdx === 4) {{
                colorOn = (evt.active === 1); // 0 = Off, 1 = On
                applyColorMode(); // touches marker.color/showlegend only — no need to recompute x/y/size
                return;
            }}
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
        var TITLE_TEXT = {json.dumps(TITLE_TEXT)};
        var TITLE_FONT_SIZE = {json.dumps(TITLE_FONT_SIZE)};
        var TOP_PADDING = {json.dumps(TOP_PADDING)};
        var TITLE_LINE_HEIGHT = {json.dumps(TITLE_LINE_HEIGHT)};
        var GAP_TITLE_LABEL = {json.dumps(GAP_TITLE_LABEL)};
        var LABEL_HEIGHT = {json.dumps(LABEL_HEIGHT)};
        var GAP_LABEL_DROPDOWN = {json.dumps(GAP_LABEL_DROPDOWN)};
        var DROPDOWN_HEIGHT = {json.dumps(DROPDOWN_HEIGHT)};
        var GAP_DROPDOWN_PLOT = {json.dumps(GAP_DROPDOWN_PLOT)};
        var MARGIN_B = {json.dumps(MARGIN_B)};
        var TITLE_SIDE_PADDING = 40; // px reserved on each side so the title never touches the edges

        // Greedy word-wrap into as many lines as the container width needs —
        // a single fixed break point (tried previously) leaves the first
        // "half" too long to fit on its own once the window gets narrow
        // enough to need wrapping at all, since the title's words aren't
        // evenly sized. Wrapping requires measuring candidate line widths;
        // an offscreen canvas estimates that, but canvas measureText()
        // measurably under-reports versus Plotly's real SVG text rendering —
        // so we calibrate it against one real measurement (the actual
        // rendered width of the unwrapped title, taken right after the
        // initial draw) and scale every canvas measurement by that factor.
        var titleWords = TITLE_TEXT.split(" ");
        var titleCtx = document.createElement("canvas").getContext("2d");
        titleCtx.font = "bold " + TITLE_FONT_SIZE + "px Arial, sans-serif";
        var canvasFullWidth = titleCtx.measureText(TITLE_TEXT).width;
        var titleEl = gd.querySelector("text.gtitle");
        var realFullWidth = titleEl ? titleEl.getBBox().width : canvasFullWidth;
        var fudge = canvasFullWidth > 0 ? (realFullWidth / canvasFullWidth) : 1;
        function measureWidth(text) {{ return titleCtx.measureText(text).width * fudge; }}

        function wrapTitle(maxWidthPx) {{
            if (measureWidth(TITLE_TEXT) <= maxWidthPx) return [TITLE_TEXT];
            var lines = [], current = "";
            titleWords.forEach(function(word) {{
                var candidate = current ? current + " " + word : word;
                if (current && measureWidth(candidate) > maxWidthPx) {{
                    lines.push(current);
                    current = word;
                }} else {{
                    current = candidate;
                }}
            }});
            if (current) lines.push(current);
            return lines;
        }}

        // Plotly's title, even with yanchor="top", renders its topmost ink
        // noticeably higher than the "y" position we ask for — consistently
        // about one title-font-size unit higher, regardless of container
        // size or line count (confirmed by comparing requested vs. actual
        // rendered position). Rather than hardcode that as a guess, measure
        // the real gap once after the first layout pass and fold it into
        // TOP_PADDING from then on, so the title's actual rendered position
        // matches what we intended instead of drifting above the container.
        var titlePaddingCorrection = 0;
        var titleCalibrated = false;

        function layoutHeader(containerWidthPx, containerHeightPx) {{
            var lines = wrapTitle(containerWidthPx - 2 * TITLE_SIDE_PADDING);
            var lineCount = lines.length;
            var titleHeight = lineCount * TITLE_LINE_HEIGHT;
            var marginT = TOP_PADDING + titleHeight + GAP_TITLE_LABEL + LABEL_HEIGHT
                + GAP_LABEL_DROPDOWN + DROPDOWN_HEIGHT + GAP_DROPDOWN_PLOT;
            var plotAreaHeight = containerHeightPx - marginT - MARGIN_B;
            currentPlotAreaHeight = plotAreaHeight;

            var effectiveTopPadding = TOP_PADDING - titlePaddingCorrection;
            var titleY = 1 - (effectiveTopPadding / containerHeightPx);
            var labelCenterOffset = TOP_PADDING + titleHeight + GAP_TITLE_LABEL + LABEL_HEIGHT / 2;
            var labelY = 1 + (marginT - labelCenterOffset) / plotAreaHeight;
            var dropdownTopOffset = TOP_PADDING + titleHeight + GAP_TITLE_LABEL + LABEL_HEIGHT + GAP_LABEL_DROPDOWN;
            var dropdownY = 1 + (marginT - dropdownTopOffset) / plotAreaHeight;

            Plotly.relayout(gd, {{
                "title.text": "<b>" + lines.join("<br>") + "</b>",
                "title.y": titleY,
                "margin.t": marginT,
                "annotations[0].y": labelY, "annotations[1].y": labelY, "annotations[2].y": labelY, "annotations[3].y": labelY, "annotations[4].y": labelY,
                "updatemenus[0].y": dropdownY, "updatemenus[1].y": dropdownY, "updatemenus[2].y": dropdownY, "updatemenus[3].y": dropdownY, "updatemenus[4].y": dropdownY,
            }}).then(function() {{
                if (titleCalibrated) return;
                titleCalibrated = true;
                var titleEl2 = gd.querySelector("text.gtitle");
                if (!titleEl2) return;
                var actualTopOffset = titleEl2.getBoundingClientRect().top - gd.getBoundingClientRect().top;
                titlePaddingCorrection = actualTopOffset - TOP_PADDING;
                layoutHeader(containerWidthPx, containerHeightPx);
            }});

            // Debug snapshot: run window.__chartDebug() in the console to see
            // everything this function just computed, next to what Plotly
            // and the DOM actually did with it.
            window.__chartDebug = function() {{
                var titleEl2 = gd.querySelector("text.gtitle");
                return {{
                    containerWidthPx: containerWidthPx, containerHeightPx: containerHeightPx,
                    lines: lines, lineCount: lineCount, titleHeight: titleHeight,
                    computed: {{marginT: marginT, plotAreaHeight: plotAreaHeight, titleY: titleY, labelY: labelY, dropdownY: dropdownY}},
                    fudge: fudge, canvasFullWidth: canvasFullWidth, realFullWidth: realFullWidth,
                    titlePaddingCorrection: titlePaddingCorrection, titleCalibrated: titleCalibrated,
                    actualMarginT: gd._fullLayout.margin.t,
                    actualTitleY: gd._fullLayout.title.y, actualTitleYref: gd._fullLayout.title.yref,
                    actualTitleYanchor: gd._fullLayout.title.yanchor,
                    divRect: gd.getBoundingClientRect(),
                    titleRect: titleEl2 ? titleEl2.getBoundingClientRect() : null,
                }};
            }};
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
            // Re-run whichever mode (scatter or dot plot) is active so a
            // dot plot's row-label font size stays matched to the plot's
            // current pixel height as the window resizes.
            recompute();
        }}
        window.addEventListener("resize", fitAspect);
        fitAspect();
        applyColorMode(); // establishes the default OFF state (neutral color, no legend)
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
            text=f"<b>{TITLE_TEXT}</b>",
            x=0.5, xanchor="center",
            y=0.98, yanchor="top",
            font=dict(size=TITLE_FONT_SIZE),
        ),
        xaxis=axis_layout(default_x),
        yaxis=axis_layout(default_y),
        legend=dict(
            title=dict(text="<b>Risk Classification</b>", font=dict(size=LEGEND_TITLE_FONT_SIZE)),
            font=dict(size=LEGEND_ITEM_FONT_SIZE),
            tracegroupgap=LEGEND_ITEM_GAP,
            # Pin the legend's top edge to the plot's top edge so it only
            # grows downward into the plot — otherwise its default vertical
            # anchor lets it bleed upward into the dropdown row above.
            x=1.02, xanchor="left", y=1, yanchor="top",
        ),
        template="plotly_white",
        margin=dict(t=MARGIN_T, b=MARGIN_B),
        # Evenly space all five dropdowns across the plot width using the
        # same "center" anchor for each (tenths: 1/10, 3/10, 5/10, 7/10,
        # 9/10), so — given their button labels are all similar, short
        # lengths (see AXIS_SHORT_LABELS/SIZE_SHORT_LABELS/
        # CAPITAL_SCALE_LABELS/COLOR_TOGGLE_LABELS) — the gaps between them
        # come out even instead of lopsided.
        updatemenus=[
            dict(buttons=skip_buttons([AXIS_SHORT_LABELS[k] for k in AXIS_ORDER_XY]),
                 direction="down", x=1 / 10, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, pad=dict(r=10, t=10)),
            dict(buttons=skip_buttons([AXIS_SHORT_LABELS[k] for k in AXIS_ORDER_XY]),
                 direction="down", x=3 / 10, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, active=1, pad=dict(r=10, t=10)),
            dict(buttons=skip_buttons(SIZE_SHORT_LABELS),
                 direction="down", x=5 / 10, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, pad=dict(r=10, t=10)),
            dict(buttons=skip_buttons(CAPITAL_SCALE_LABELS),
                 direction="down", x=7 / 10, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, pad=dict(r=10, t=10)),
            dict(buttons=skip_buttons(COLOR_TOGGLE_LABELS),
                 direction="down", x=9 / 10, xanchor="center", y=1.05, yanchor="top",
                 showactive=True, pad=dict(r=10, t=10)),
        ],
        annotations=[
            dict(text="X axis", x=1 / 10, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
            dict(text="Y axis", x=3 / 10, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
            dict(text="Point size", x=5 / 10, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
            dict(text="Capital scale", x=7 / 10, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
            dict(text="Color", x=9 / 10, xref="paper", y=1.10, yref="paper", showarrow=False, xanchor="center"),
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
