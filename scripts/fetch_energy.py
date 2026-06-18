"""
Energy Disruption & Transition Megatrend -- Data Fetcher
"""

import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe, fred_series, yf_series, wb_series, latest, yoy_pct, trend_3m, theme_percentile, theme_direction, SPECS

OUTPUT = os.path.join(os.path.dirname(__file__), "../data/energy.json")

SERIES = [
    # FRED
    ("energy_cpi",   "CPI: Energy (All Items)",                      "index",  "FRED/CPIENGSL",
     lambda: fred_series("CPIENGSL", "2000-01-01")),
    ("energy_svc",   "CPI: Energy Services",                         "index",  "FRED/CUSR0000SEHE",
     lambda: fred_series("CUSR0000SEHE", "2000-01-01")),
    ("wti_oil",      "WTI Crude Oil Price (USD/barrel)",             "USD",    "FRED/WTISPLC",
     lambda: fred_series("WTISPLC", "2005-01-01")),
    ("brent_oil",    "Brent Crude Oil Price (USD/barrel)",           "USD",    "FRED/DCOILBRENTEU",
     lambda: fred_series("DCOILBRENTEU", "2005-01-01")),
    ("natgas",       "Natural Gas Price: Henry Hub (USD/MMBtu)",     "USD",    "FRED/MHHNGSP",
     lambda: fred_series("MHHNGSP", "2005-01-01")),
    ("gas_price",    "US Regular Gas Price (USD/gallon)",            "USD",    "FRED/GASREGCOVW",
     lambda: fred_series("GASREGCOVW", "2005-01-01")),
    ("power_gen",    "Industrial Production: Electric Power",        "index",  "FRED/IPG2211A2N",
     lambda: fred_series("IPG2211A2N", "2000-01-01")),
    ("elec_price",   "Electricity Price: Residential (cents/kWh)",   "c/kWh",  "FRED/APU000072610",
     lambda: fred_series("APU000072610", "2005-01-01")),
    # yFinance
    ("icln",         "iShares Global Clean Energy ETF (ICLN)",       "USD",    "YF/ICLN",
     lambda: yf_series("ICLN", "5y")),
    ("xle",          "Energy Select Sector SPDR ETF (XLE)",          "USD",    "YF/XLE",
     lambda: yf_series("XLE", "5y")),
    ("tan",          "Invesco Solar ETF (TAN)",                      "USD",    "YF/TAN",
     lambda: yf_series("TAN", "5y")),
    ("fan",          "First Trust Global Wind Energy ETF (FAN)",     "USD",    "YF/FAN",
     lambda: yf_series("FAN", "5y")),
    ("lit",          "Global Lithium & Battery Tech ETF (LIT)",      "USD",    "YF/LIT",
     lambda: yf_series("LIT", "5y")),
    ("uso",          "US Oil Fund ETF (USO)",                        "USD",    "YF/USO",
     lambda: yf_series("USO", "5y")),
    # World Bank
    ("wb_renewables","Renewable Electricity (% total) - World",      "%",      "WB/EG.ELC.RNEW.ZS/WLD",
     lambda: wb_series("EG.ELC.RNEW.ZS", "WLD", 25)),
    ("wb_renew_us",  "Renewable Electricity (% total) - US",         "%",      "WB/EG.ELC.RNEW.ZS/US",
     lambda: wb_series("EG.ELC.RNEW.ZS", "US", 25)),
    ("wb_energy_int","Energy Intensity: MJ per 2017 PPP GDP - World","MJ/$",   "WB/EG.EGY.PRIM.PP.KD",
     lambda: wb_series("EG.EGY.PRIM.PP.KD", "WLD", 25)),
    ("wb_fossil",    "Fossil Fuels (% of total energy) - World",     "%",      "WB/EG.USE.COMM.FO.ZS",
     lambda: wb_series("EG.USE.COMM.FO.ZS", "WLD", 25)),
]


def compute_score(series):
    comp, _ = theme_percentile(series, SPECS["energy"])
    return comp


def fetch_all():
    print("\n[energy] Energy Disruption & Transition")
    result = {
        "meta": {
            "trend": "energy", "label": "Energy Disruption & Transition",
            "description": "Tracks fossil fuel dependence, renewable energy growth, energy prices, and clean energy transition speed.",
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
    raw = trend_3m(s.get("energy_cpi"))
    result["meta"]["direction"] = theme_direction({k: v["data"] for k, v in result["series"].items()}, SPECS["energy"])
    return result


if __name__ == "__main__":
    data = fetch_all()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved -> {OUTPUT}")
    print(f"  Score: {data['meta']['score']}  |  Direction: {data['meta']['direction']}")
