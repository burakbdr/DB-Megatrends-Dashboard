"""
Sovereign Debt Megatrend -- Data Fetcher
Sources: FRED (primary) . yFinance . World Bank
"""

import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe, fred_series, yf_series, wb_series, latest, yoy_pct, trend_3m, theme_percentile, theme_direction, SPECS

OUTPUT = os.path.join(os.path.dirname(__file__), "../data/sovereign_debt.json")

SERIES = [
    # FRED
    ("debt_gdp",     "Federal Debt as % of GDP",                      "%",      "FRED/GFDEGDQ188S",
     lambda: fred_series("GFDEGDQ188S", "2000-01-01")),
    ("deficit",      "Federal Surplus / Deficit (M USD)",             "M USD",  "FRED/MTSDS133FMS",
     lambda: fred_series("MTSDS133FMS", "2010-01-01")),
    ("outlays_gdp",  "Federal Outlays as % of GDP",                   "%",      "FRED/FYONGDA188S",
     lambda: fred_series("FYONGDA188S", "1990-01-01")),
    ("receipts_gdp", "Federal Receipts as % of GDP",                  "%",      "FRED/FYFRGDA188S",
     lambda: fred_series("FYFRGDA188S", "1990-01-01")),
    ("net_interest", "Net Interest Payments as % of GDP",             "%",      "FRED/FYOIGDA188S",
     lambda: fred_series("FYOIGDA188S", "1990-01-01")),
    ("yield_10y",    "10-Year Treasury Yield (%)",                    "%",      "FRED/DGS10",
     lambda: fred_series("DGS10", "2010-01-01")),
    ("yield_30y",    "30-Year Treasury Yield (%)",                    "%",      "FRED/DGS30",
     lambda: fred_series("DGS30", "2010-01-01")),
    ("yield_2y",     "2-Year Treasury Yield (%)",                     "%",      "FRED/DGS2",
     lambda: fred_series("DGS2", "2010-01-01")),
    ("breakeven",    "10-Year Breakeven Inflation Rate (%)",          "%",      "FRED/T10YIE",
     lambda: fred_series("T10YIE", "2010-01-01")),
    ("real_rate",    "10-Year Real Interest Rate / TIPS (%)",         "%",      "FRED/DFII10",
     lambda: fred_series("DFII10", "2010-01-01")),
    ("hy_spread",    "High Yield Option-Adjusted Spread (%)",         "%",      "FRED/BAMLH0A0HYM2",
     lambda: fred_series("BAMLH0A0HYM2", "2010-01-01")),
    ("term_premium", "10-Year minus 2-Year Treasury Spread",           "%",      "FRED/T10Y2Y",
     lambda: fred_series("T10Y2Y", "2010-01-01")),
    # yFinance
    ("tlt",          "iShares 20yr Treasury Bond ETF (TLT)",          "USD",    "YF/TLT",
     lambda: yf_series("TLT", "5y")),
    ("hyg",          "iShares High Yield Corporate Bond ETF (HYG)",   "USD",    "YF/HYG",
     lambda: yf_series("HYG", "5y")),
    ("tip",          "iShares TIPS Bond ETF (TIP)",                   "USD",    "YF/TIP",
     lambda: yf_series("TIP", "5y")),
    # World Bank
    ("wb_debt_us",   "Central Gov. Debt % GDP - United States",       "%",      "WB/GC.DOD.TOTL.GD.ZS/US",
     lambda: wb_series("GC.DOD.TOTL.GD.ZS", "US", 25)),
    ("wb_gdp_growth","GDP Growth Rate - US (%)",                      "%",      "WB/NY.GDP.MKTP.KD.ZG/US",
     lambda: wb_series("NY.GDP.MKTP.KD.ZG", "US", 25)),
]


def compute_score(series):
    comp, _ = theme_percentile(series, SPECS["sovereign_debt"])
    return comp


def fetch_all():
    print("\n[debt] Sovereign Debt")
    result = {
        "meta": {
            "trend": "sovereign_debt", "label": "Sovereign Debt",
            "description": "Tracks government debt levels, deficits, yield curves, and fiscal stress across developed economies.",
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "score": None, "direction": None, "sources": [],
        },
        "series": {},
    }
    for key, label, unit, source, fn in SERIES:
        data = safe(label, fn)
        if data:
            result["series"][key] = {"label": label, "unit": unit, "source": source, "data": data}
            result["meta"]["sources"].append(source)
    s = {k: v["data"] for k, v in result["series"].items()}
    result["meta"]["score"] = compute_score(s)
    raw = trend_3m(s.get("yield_10y"))
    result["meta"]["direction"] = theme_direction({k: v["data"] for k, v in result["series"].items()}, SPECS["sovereign_debt"])
    return result


if __name__ == "__main__":
    data = fetch_all()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved -> {OUTPUT}")
    print(f"  Score: {data['meta']['score']}  |  Direction: {data['meta']['direction']}")
