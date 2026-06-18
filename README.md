# Megatrend Dashboard

An **independent, transparent hard-data monitor** of six structural megatrends,
with a thematic structure *inspired by* Deutsche Bank Research Institute's
**"Megatrends: AI vs the decade's structural headwinds"** (May 2026).

> ### What this is — and is not
>
> **It is:** a reproducible, free, auditable monitor that asks one question per
> theme — *"where do the hard macro/market indicators sit today relative to their
> own history?"* — using public data (FRED, World Bank, market prices),
> standardised with z-scores.
>
> **It is *not*** a replication of Deutsche Bank's model. We do **not** have their
> dataset, their ~100 series, their AI-quantified *qualitative* signals, or their
> proprietary survey data, and we do not know their cleaning or aggregation steps.
> Our indicators are built from different, purely quantitative inputs and are our
> own. Because hard data is largely *coincident/lagging* (it lacks the qualitative
> and survey layer that gives the original its *leading* property), and because our
> usable history is far shorter than their ~70 years, this monitor **cannot and does
> not claim to reproduce their figures or conclusions.** Any directional labels and
> correlations here are **illustrative and sample-limited**, describe *conditions
> not forecasts*, and are not investment advice.
>
> Where the report is quoted, it is attributed to Deutsche Bank — those are *their*
> claims, presented as context, not as outputs validated by this tool.

---

## The 6 Megatrends

Thematic structure follows the report; the *current signal* below is this monitor's
own hard-data reading, not Deutsche Bank's, and is illustrative.

| # | Megatrend | This monitor's signal | Key Question |
|---|-----------|----------------|--------------|
| 1 | **Technology** | 🟢 Positive | Will AI productivity gains materialise fast enough? |
| 2 | **Sovereign Debt** | 🔴 Negative | Can governments avoid a debt spiral? |
| 3 | **Geopolitics & Globalisation** | 🔴 Negative | Will trade reorganise without a hard break? |
| 4 | **Domestic Politics & Social Discontent** | 🔴 Negative | Will populism crowd out long-term policy? |
| 5 | **Demography** | 🔴 Negative | Can immigration and tech offset ageing workforces? |
| 6 | **Energy Disruption & Transition** | 🟡 Neutral | Will the clean transition reduce energy risk? |

---

## Data Sources

| Source | Used for | API Key? |
|--------|----------|----------|
| **FRED** (Federal Reserve) | Macro: yields, debt, wages, productivity, inflation | ✅ Required (free) |
| **yFinance** | Market proxies: ETFs, sector indices | ❌ No key needed |
| **World Bank** | Global structural: demographics, trade, renewables | ❌ No key needed |

Total: ~80 data series across 6 megatrends.

---

## Setup

```bash
# 1. Clone / unzip the project
cd megatrend_dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Get a free FRED API key (takes ~2 minutes)
#    → https://fred.stlouisfed.org/docs/api/api_key.html

# 5. Create your .env file from the template
cp .env.example .env

# 6. Open .env and paste your key
#    FRED_API_KEY=your_actual_key_here
```

> **Security note:** `.env` is listed in `.gitignore` and will never be committed to git.
> Never share or hard-code your API key in source files.

---

## Usage

### Update all data
```bash
python scripts/fetch_all.py
```

Output:
```
════════════════════════════════════════════════════════════════
   Megatrend Dashboard  —  Data Update
   2026-06-08  07:00 UTC
════════════════════════════════════════════════════════════════

🔬  Technology
    ✓  Semiconductor Industrial Production
    ✓  NVIDIA — AI chip bellwether
    ✓  R&D Expenditure (% of GDP)
    ...

  Megatrend                               Score   Dir   Series
  ────────────────────────────────────────────────────────────
  Technology                               71.4   ↑     14
  Sovereign Debt                           28.3   ↓     18
  Geopolitics & Globalisation              41.2   →     15
  Domestic Politics & Social Discontent    38.6   ↓     13
  Demography                               32.1   ↓     17
  Energy Disruption & Transition           52.8   ↑     19
  ────────────────────────────────────────────────────────────
  OVERALL                                  44.1
```

### Update a single megatrend
```bash
python scripts/fetch_technology.py
python scripts/fetch_sovereign_debt.py
python scripts/fetch_geopolitics.py
python scripts/fetch_domestic_politics.py
python scripts/fetch_demography.py
python scripts/fetch_energy.py
```

---

## Output Files

```
data/
├── summary.json          ← Scores & directions for all 6 trends (used by dashboard)
├── technology.json
├── sovereign_debt.json
├── geopolitics.json
├── domestic_politics.json
├── demography.json
└── energy.json
```

Each JSON file has the structure:
```json
{
  "meta": {
    "trend": "technology",
    "label": "Technology",
    "score": 71.4,
    "direction": "up",
    "updated_at": "2026-06-08T07:00:00Z",
    "sources": ["FRED/IPG3344S", "YF/SOXX", "WB/GB.XPD.RSDV.GD.ZS"]
  },
  "series": {
    "semi_ip": {
      "label": "Semiconductor Industrial Production",
      "unit": "index",
      "source": "FRED/IPG3344S",
      "data": { "dates": ["2005-01-01", ...], "values": [98.2, ...] }
    }
  }
}
```

---

## Scoring System

Each megatrend is scored **0–100** based on its current impact on economies & markets:

| Score | Interpretation | Color |
|-------|---------------|-------|
| 67–100 | **Positive tailwind** — supporting growth & markets | 🟢 |
| 34–66  | **Neutral / mixed** — no clear directional force | 🟡 |
| 0–33   | **Negative headwind** — dragging on growth & markets | 🔴 |

Direction arrows show recent momentum vs prior period:
- **↑** Improving trend  
- **↓** Deteriorating trend  
- **→** Stable / neutral

> **Methodology caveats (read before trusting a number).** Each score is a
> *percentile* of a theme's public indicators within their **own available
> history** — which is shorter and more recent than the report's ~70 years, and
> dominated by the 2008 and COVID regimes. A score is therefore a statement about
> the present relative to a limited past, not a forecast and not a market call.
> The 34/67 colour bands are presentational, not calibrated thresholds. This is a
> deliberately descriptive monitor: it reports where indicators sit and how they
> have moved, and makes no prediction.

---

## Project Structure

```
megatrend_dashboard/
├── scripts/
│   ├── utils.py                   ← Shared FRED / yFinance / WB helpers
│   ├── fetch_all.py               ← Master runner
│   ├── fetch_technology.py
│   ├── fetch_sovereign_debt.py
│   ├── fetch_geopolitics.py
│   ├── fetch_domestic_politics.py
│   ├── fetch_demography.py
│   └── fetch_energy.py
├── data/                          ← Auto-generated (git-ignored in dev)
├── docs/
│   └── index.html                 ← Dashboard UI (GitHub Pages)
├── requirements.txt
└── README.md
```

---

## Next Step: GitHub Pages Dashboard

Once data looks correct locally, the next phase deploys the visual dashboard:

1. Push to GitHub
2. `Settings → Pages → Source: /docs`
3. Add `.github/workflows/update_data.yml` for daily auto-update via GitHub Actions
