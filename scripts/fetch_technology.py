"""
Technology Megatrend -- Data Fetcher
Sources: FRED (primary) . yFinance . World Bank
"""

import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe, fred_series, yf_series, wb_series, latest, yoy_pct, trend_3m, theme_percentile, theme_direction, SPECS

OUTPUT = os.path.join(os.path.dirname(__file__), "../data/technology.json")

SERIES = [
    # FRED
    ("semi_ip",      "Semiconductor Industrial Production",             "index",  "FRED/IPG3344S",
     lambda: fred_series("IPG3344S", "2005-01-01")),
    ("computer_ip",  "Computer & Electronic Products IP",              "index",  "FRED/IPMINE",
     lambda: fred_series("IPMINE", "2005-01-01")),
    ("productivity", "Nonfarm Business Labor Productivity",            "index",  "FRED/OPHNFB",
     lambda: fred_series("OPHNFB", "1995-01-01")),
    ("multifactor",  "Multifactor Productivity - Nonfarm Business",     "index",  "FRED/PRS85006092",
     lambda: fred_series("PRS85006092", "1995-01-01")),
    ("info_invest",  "Real Investment: Info Processing Equipment",     "% chg",  "FRED/Y006RX1Q020SBEA",
     lambda: fred_series("Y006RX1Q020SBEA", "2000-01-01")),
    ("durable_goods","Durable Goods Orders",                          "M USD",  "FRED/DGORDER",
     lambda: fred_series("DGORDER", "2005-01-01")),
    ("rd_business",  "R&D Spending: Business Sector",                 "B USD",  "FRED/Y694RX1A020NBEA",
     lambda: fred_series("Y694RX1A020NBEA", "2000-01-01")),
    # yFinance
    ("soxx",         "Philadelphia Semiconductor ETF (SOXX)",         "USD",    "YF/SOXX",
     lambda: yf_series("SOXX", "5y")),
    ("qqq",          "Nasdaq-100 ETF (QQQ)",                          "USD",    "YF/QQQ",
     lambda: yf_series("QQQ", "5y")),
    ("nvda",         "NVIDIA - AI chip bellwether",                   "USD",    "YF/NVDA",
     lambda: yf_series("NVDA", "5y")),
    ("smh",          "VanEck Semiconductor ETF (SMH)",                "USD",    "YF/SMH",
     lambda: yf_series("SMH", "5y")),
    ("arkk",         "ARK Innovation ETF (ARKK)",                    "USD",    "YF/ARKK",
     lambda: yf_series("ARKK", "5y")),
    # World Bank
    ("wb_rnd_gdp",   "R&D Expenditure (% of GDP) - US",              "%",      "WB/GB.XPD.RSDV.GD.ZS",
     lambda: wb_series("GB.XPD.RSDV.GD.ZS", "US", 20)),
    ("wb_hitech",    "High-Technology Exports (% manufactured)",      "%",      "WB/TX.VAL.TECH.MF.ZS",
     lambda: wb_series("TX.VAL.TECH.MF.ZS", "US", 20)),
    ("wb_internet",  "Internet Users (% population) - US",           "%",      "WB/IT.NET.USER.ZS",
     lambda: wb_series("IT.NET.USER.ZS", "US", 20)),
]


def compute_score(series):
    comp, _ = theme_percentile(series, SPECS["technology"])
    return comp


def fetch_all():
    print("\n[tech] Technology")
    result = {
        "meta": {
            "trend": "technology", "label": "Technology",
            "description": "Tracks AI adoption, semiconductor activity, productivity growth, and tech investment.",
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
    result["meta"]["score"]     = compute_score({k: v["data"] for k, v in result["series"].items()})
    result["meta"]["direction"] = theme_direction({k: v["data"] for k, v in result["series"].items()}, SPECS["technology"])
    return result


if __name__ == "__main__":
    data = fetch_all()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved -> {OUTPUT}")
    print(f"  Score: {data['meta']['score']}  |  Direction: {data['meta']['direction']}")
    print(f"  Series: {list(data['series'].keys())}")
