"""
Domestic Politics & Social Discontent Megatrend -- Data Fetcher
"""

import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe, fred_series, wb_series, latest, yoy_pct, trend_3m, theme_percentile, theme_direction, SPECS

OUTPUT = os.path.join(os.path.dirname(__file__), "../data/domestic_politics.json")

SERIES = [
    # FRED
    ("consumer_sent","Michigan Consumer Sentiment Index",             "index",  "FRED/UMCSENT",
     lambda: fred_series("UMCSENT", "2000-01-01")),
    ("unemployment", "Unemployment Rate (%)",                        "%",      "FRED/UNRATE",
     lambda: fred_series("UNRATE", "2000-01-01")),
    ("u6",           "U-6 Underemployment Rate (%)",                 "%",      "FRED/U6RATE",
     lambda: fred_series("U6RATE", "2000-01-01")),
    ("hourly_earn",  "Average Hourly Earnings - All Employees (USD)","USD",    "FRED/CES0500000003",
     lambda: fred_series("CES0500000003", "2010-01-01")),
    ("real_wages",   "Real Median Weekly Earnings (USD)",            "USD",    "FRED/LES1252881600Q",
     lambda: fred_series("LES1252881600Q", "2000-01-01")),
    ("labor_share",  "Labor Share of Income - Nonfarm Business",     "index",  "FRED/PRS85006173",
     lambda: fred_series("PRS85006173", "1990-01-01")),
    ("home_prices",  "Case-Shiller National Home Price Index",       "index",  "FRED/CSUSHPISA",
     lambda: fred_series("CSUSHPISA", "2000-01-01")),
    ("housing_starts","Housing Starts (thousands of units)",         "k units","FRED/HOUST",
     lambda: fred_series("HOUST", "2000-01-01")),
    ("median_income","Real Median Household Income (USD)",           "USD",    "FRED/MEHOINUSA672N",
     lambda: fred_series("MEHOINUSA672N", "1990-01-01")),
    ("cpi",          "Consumer Price Index (All Urban)",             "index",  "FRED/CPIAUCSL",
     lambda: fred_series("CPIAUCSL", "2000-01-01")),
    ("cpi_shelter",  "CPI: Shelter Component",                       "index",  "FRED/CUSR0000SAH1",
     lambda: fred_series("CUSR0000SAH1", "2000-01-01")),
    # World Bank
    ("wb_gini",      "Gini Coefficient - Income Inequality (US)",    "0-100",  "WB/SI.POV.GINI",
     lambda: wb_series("SI.POV.GINI", "US", 25)),
    ("wb_poverty",   "Poverty Headcount at $6.85/day (% pop) - US", "%",      "WB/SI.POV.UMIC",
     lambda: wb_series("SI.POV.UMIC", "US", 25)),
    ("wb_educ",      "Gov. Expenditure on Education (% GDP) - US",  "%",      "WB/SE.XPD.TOTL.GD.ZS",
     lambda: wb_series("SE.XPD.TOTL.GD.ZS", "US", 25)),
]


def compute_score(series):
    comp, _ = theme_percentile(series, SPECS["domestic_politics"])
    return comp


def fetch_all():
    print("\n[pol] Domestic Politics & Social Discontent")
    result = {
        "meta": {
            "trend": "domestic_politics", "label": "Domestic Politics & Social Discontent",
            "description": "Tracks consumer sentiment, wage growth, housing affordability, inequality, and social stress.",
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
    result["meta"]["score"]     = compute_score(s)
    result["meta"]["direction"] = theme_direction({k: v["data"] for k, v in result["series"].items()}, SPECS["domestic_politics"])
    return result


if __name__ == "__main__":
    data = fetch_all()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved -> {OUTPUT}")
    print(f"  Score: {data['meta']['score']}  |  Direction: {data['meta']['direction']}")
