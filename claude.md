# Project: Entrepreneurship Capital/Time/Risk Explorer

## Context

This is a data visualization for a conference talk on entrepreneurship, aimed at scientists and software developers deciding whether/how to start a company. The audience spans tracks in: medical/biotech, physics and astronomy, data-driven discovery/ML/AI, environmental/earth/climate science, and general scientific software development.

The chart compares business categories on three axes: **capital needed to reach founder financial stability** (not total company capitalization — see Definitions below), **time to reach that stability**, and **risk of an unplanned/distressed exit before getting there**. A fourth dimension (risk type: market vs. technical/regulatory) is shown via color.

**This is a first working prototype.** The risk percentages in particular are a mix of directly-sourced figures and informed placeholder estimates (flagged in the `data_quality` field below). Expect another pass to refine these after the prototype is validated — build the tool to make updating the data trivial (single data block, not scattered magic numbers).

## Definitions (important — do not silently redefine these)

- **Capital needed to reach founder financial stability**: the amount of outside capital raised (or personal capital spent) by the point the founder is drawing something like a market-rate salary — NOT the total capital the company will ever raise or need to reach full commercialization/exit. E.g., pharma's famous "$2.6B to bring a drug to market" figure is explicitly *not* used here; we use the seed-round scale instead, since founders are typically salaried well before their drug/product reaches market.
- **Time to founder stability**: months from founding decision to that same salary milestone.
- **Risk**: probability of an *unplanned, distress-driven* exit before reaching founder stability — explicitly excludes planned/voluntary closures (retirement, planned wind-down of a single-purpose vehicle, selling a mature practice, "project ended" in the SBA's own closure-reason taxonomy). Where the underlying source doesn't distinguish distress from planned closure, this is noted in `data_quality`.
- **Risk type**: `market` (would the product find paying customers, assuming it works as designed), `technical` (can it be built/proven to work at all), or `regulatory` (gated by an external approval process, e.g., FDA) — categories can blend; pick the dominant one.

## Tech stack requirements

- **Python + Plotly** (`plotly.graph_objects`, not just `plotly.express`, since we need full control over `updatemenus`).
- Output must be a **single, fully self-contained HTML file** — no CDN references, no internet connection needed to view it, no Python kernel needed to run it. Use `fig.write_html("chart.html", include_plotlyjs=True)` explicitly (don't rely on the default without stating it — make it explicit in code so it's never accidentally left as `'cdn'`).
- **No permanent point labels.** Points are unlabeled dots by default; the category name and full data (capital, time, risk, risk type) appear in a **large-font hover tooltip** via `hovertemplate`. Set `hoverlabel=dict(font_size=24, font_family="Arial")` (or similar) — default Plotly hover font (~13px) is too small to read from the back of a conference room; go big.
- **Axis-switching dropdowns** via `layout.updatemenus`, so during the talk I can click a dropdown to change what's on the X axis and what's on the Y axis, choosing from: Capital (log scale), Time to stability (months), Risk (%). Also include a toggle for whether point size encodes capital (only meaningful when capital isn't already on an axis — disable/ignore it otherwise, don't double-encode).
- **Color** encodes risk type (market / technical / regulatory) as a categorical variable — hold this constant across all axis combinations, with a visible legend.
- Capital axis should be **log-scaled** (values span ~$10K to ~$20M+); time and risk axes are linear.
- When encoding capital as point size, scale by **square root of capital**, not raw value, and clamp the min/max radius so the largest point doesn't visually overwhelm the smallest (target something like a 3–4x size ratio between smallest and largest, not the raw ratio in the data).
- Keep all data in one clearly-structured block (Python dict/list or a loaded CSV) at the top of the script — I will be hand-editing risk values after further research, so the data needs to be trivially editable without touching plotting logic.
- Test the exported HTML with the network disabled before considering it done.

## Data

Point estimates below are for plotting. Ranges and sourcing notes are in `data_quality` / `notes` — keep these as comments or a secondary data structure so they don't clutter the plot logic but aren't lost either.

```python
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
```

### Cross-cutting notes (not yet separate data points — flag for follow-up)

- **Defense/dual-use relevance** is a cross-cutting modifier, not its own category — it can attach to #3, #11, #12, or a future "science-track" category. Where it applies: DoD is 46% of all federal SBIR spending (~$1.1B/yr), success rate ~15% for DoD SBIR Phase I despite huge volume (1,440 awards/yr); OTAs via DIU move much faster (3-6mo vs 12-18mo) and larger ($500K-5M+) than standard SBIR; defense tech VC hit $49.9B in 2025 (2x 2024). Commercialization for this path often means "sell to government," not "sell to an open market" — a distinct concentration-risk dimension not currently captured by `risk_type`.
- **Grant-funded science-startup path** (SBIR/STTR ladder, relevant to medtech/deep-tech/physics-astronomy/climate-hardware, less so to pure pharma): Phase I ~$150K-314K over 6-12mo (~14% award rate), Phase II ~$750K-2.2M over 24mo (60%+ conversion given Phase I win). Derived estimate: ~8-9% of applicants ever reach Phase II funding levels. Time to a genuinely market-level salary is realistically 2-3 years; personal out-of-pocket before any funding (provisional patent + incorporation, DIY-leaning) is roughly $2K-$25K.
- **ML/AI and scientific software** are financially closer to categories 5/7/8 than to "deep tech" — AI captured ~$211B in VC in 2025 (~50% of global VC), meaning this population can often skip non-dilutive funding entirely, unlike physics/astronomy hardware or climate hardware.
- **Climate/earth science** is bimodal: hardware sub-fields behave like deep tech (long timelines, DOE/ARPA-E-scale non-dilutive funding, poor fit for standard VC fund horizons); software/analytics sub-fields behave like ordinary SaaS (#5/#7/#8).

## Phase 2 (not part of this prototype, but keep data structure ready for it)

Bookmarked for a follow-up slide/chart: bootstrapped solo SaaS/app outcome distribution, from Indie Hackers / MicroConf community survey data:

```python
mrr_distribution = [
    {"bucket": "Never reach $1K MRR", "pct": 40},
    {"bucket": "$1K-5K MRR (side income)", "pct": 30},
    {"bucket": "$5K-20K MRR (salary replacement)", "pct": 20},
    {"bucket": "$20K+ MRR (real business)", "pct": 10},
]
# Median time to $10K MRR (for those who get there): 12-18 months.
# Opportunity cost framing: 2 years unpaid full-time bootstrapping ≈ $266K
# foregone income at a mid-level dev salary (~$133K/yr).
# Source: Indie Hackers / MicroConf community surveys — NOT peer-reviewed,
# but the best available data for this specific population.
```

## Deliverable

A single `chart.html` in the project root, self-contained, tested offline, built from the `categories` data block above with dropdown-driven X/Y axis selection (Capital / Time / Risk), risk-type color coding with legend, optional size-as-capital toggle, and large-font hover tooltips as the only labeling mechanism.
