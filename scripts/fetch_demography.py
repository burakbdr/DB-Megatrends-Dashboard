"""
Demography Megatrend -- Data Fetcher
"""

import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe, fred_series, wb_series, latest, yoy_pct, trend_3m, theme_percentile, theme_direction, SPECS

OUTPUT = os.path.join(os.path.dirname(__file__), "../data/demography.json")

SERIES = [
    # FRED
    ("lfpr",         "Labor Force Participation Rate (%)",            "%",      "FRED/CIVPART",
     lambda: fred_series("CIVPART", "2000-01-01")),
    ("prime_age",    "Prime-Age Labor Force Participation 25-54 (%)", "%",      "FRED/LNS11300060",
     lambda: fred_series("LNS11300060", "2000-01-01")),
    ("emp_pop",      "Employment-Population Ratio (%)",               "%",      "FRED/EMRATIO",
     lambda: fred_series("EMRATIO", "2000-01-01")),
    ("population",   "US Total Population (thousands)",               "k",      "FRED/POPTHM",
     lambda: fred_series("POPTHM", "1990-01-01")),
    ("birth_rate",   "Birth Rate per 1,000 People - US",             "per 1k", "FRED/SPDYNCBRTINUSA",
     lambda: fred_series("SPDYNCBRTINUSA", "1990-01-01")),
    ("life_expect",  "Life Expectancy at Birth (years) - US",        "years",  "FRED/SPDYNLE00INUSA",
     lambda: fred_series("SPDYNLE00INUSA", "1990-01-01")),
    ("housing_starts","Housing Starts (household formation proxy)",   "k units","FRED/HOUST",
     lambda: fred_series("HOUST", "2000-01-01")),
    ("house_price",  "Median Sales Price of Houses Sold (USD)",       "USD",    "FRED/MSPNHSUS",
     lambda: fred_series("MSPNHSUS", "1990-01-01")),
    ("working_age",  "Working Age Population 15-64 (thousands) - US","k",      "FRED/LFWA64TTUSM647S",
     lambda: fred_series("LFWA64TTUSM647S", "2000-01-01")),
    # World Bank
    ("wb_pop_us",    "Population Growth Rate (%) - US",              "%",      "WB/SP.POP.GROW/US",
     lambda: wb_series("SP.POP.GROW", "US", 30)),
    ("wb_pop_wld",   "Population Growth Rate (%) - World",           "%",      "WB/SP.POP.GROW/WLD",
     lambda: wb_series("SP.POP.GROW", "WLD", 30)),
    ("wb_work_us",   "Working Age Pop 15-64 (% total) - US",         "%",      "WB/SP.POP.1564.TO.ZS/US",
     lambda: wb_series("SP.POP.1564.TO.ZS", "US", 30)),
    ("wb_work_eu",   "Working Age Pop 15-64 (% total) - Europe",     "%",      "WB/SP.POP.1564.TO.ZS/EU",
     lambda: wb_series("SP.POP.1564.TO.ZS", "EUU", 30)),
    ("wb_fertility_wld","Fertility Rate (births/woman) - World",     "births", "WB/SP.DYN.TFRT.IN/WLD",
     lambda: wb_series("SP.DYN.TFRT.IN", "WLD", 30)),
    ("wb_fertility_us", "Fertility Rate (births/woman) - US",        "births", "WB/SP.DYN.TFRT.IN/US",
     lambda: wb_series("SP.DYN.TFRT.IN", "US", 30)),
    ("wb_old_dep_wld",  "Old-Age Dependency Ratio - World",          "%",      "WB/SP.POP.DPND.OL/WLD",
     lambda: wb_series("SP.POP.DPND.OL", "WLD", 30)),
    ("wb_old_dep_us",   "Old-Age Dependency Ratio - US",             "%",      "WB/SP.POP.DPND.OL/US",
     lambda: wb_series("SP.POP.DPND.OL", "US", 30)),
    ("wb_urban",        "Urban Population (% of total) - World",     "%",      "WB/SP.URB.TOTL.IN.ZS",
     lambda: wb_series("SP.URB.TOTL.IN.ZS", "WLD", 30)),
]


def compute_score(series):
    comp, _ = theme_percentile(series, SPECS["demography"])
    return comp


def fetch_all():
    print("\n[demo] Demography")
    result = {
        "meta": {
            "trend": "demography", "label": "Demography",
            "description": "Tracks workforce participation, aging, household formation, fertility, and migration.",
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
    result["meta"]["direction"] = theme_direction({k: v["data"] for k, v in result["series"].items()}, SPECS["demography"])
    return result


if __name__ == "__main__":
    data = fetch_all()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved -> {OUTPUT}")
    print(f"  Score: {data['meta']['score']}  |  Direction: {data['meta']['direction']}")
