"""
Geopolitics & Globalisation Megatrend -- Data Fetcher
"""

import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from utils import safe, fred_series, yf_series, wb_series, latest, yoy_pct, trend_3m, theme_percentile, theme_direction, SPECS

OUTPUT = os.path.join(os.path.dirname(__file__), "../data/geopolitics.json")

SERIES = [
    # FRED
    ("vix",          "CBOE Volatility Index (VIX)",                   "index",  "FRED/VIXCLS",
     lambda: fred_series("VIXCLS", "2005-01-01")),
    ("us_epu",       "US Economic Policy Uncertainty Index",          "index",  "FRED/USEPUINDXD",
     lambda: fred_series("USEPUINDXD", "2005-01-01")),
    ("global_epu",   "Global Economic Policy Uncertainty Index",      "index",  "FRED/GEPUCURRENT",
     lambda: fred_series("GEPUCURRENT", "2005-01-01")),
    ("mfg_ppi",      "PPI: Manufacturing (supply chain proxy)",        "index",  "FRED/PCUOMFGOMFG",
     lambda: fred_series("PCUOMFGOMFG", "2005-01-01")),
    ("trade_balance","US Goods Trade Balance (M USD)",                "M USD",  "FRED/BOPGSTB",
     lambda: fred_series("BOPGSTB", "2005-01-01")),
    ("usd_broad",    "USD Broad Trade-Weighted Exchange Index",       "index",  "FRED/DTWEXBGS",
     lambda: fred_series("DTWEXBGS", "2005-01-01")),
    ("wti_oil",      "WTI Crude Oil Price (USD/barrel)",              "USD",    "FRED/WTISPLC",
     lambda: fred_series("WTISPLC", "2005-01-01")),
    ("brent_oil",    "Brent Crude Oil Price (USD/barrel)",            "USD",    "FRED/DCOILBRENTEU",
     lambda: fred_series("DCOILBRENTEU", "2005-01-01")),
    ("stlfsi",       "St. Louis Fed Financial Stress Index",          "index",  "FRED/STLFSI4",
     lambda: fred_series("STLFSI4", "2000-01-01")),
    # yFinance
    ("eem",          "Emerging Markets ETF (EEM)",                    "USD",    "YF/EEM",
     lambda: yf_series("EEM", "5y")),
    ("dxy",          "US Dollar Index (DXY)",                         "index",  "YF/DX-Y.NYB",
     lambda: yf_series("DX-Y.NYB", "5y")),
    ("gld",          "Gold ETF (GLD) - safe-haven demand",           "USD",    "YF/GLD",
     lambda: yf_series("GLD", "5y")),
    ("xme",          "Metals & Mining ETF (XME)",                    "USD",    "YF/XME",
     lambda: yf_series("XME", "5y")),
    # World Bank
    ("wb_trade_gdp", "Trade Openness: Exports+Imports % GDP - World","%",      "WB/NE.TRD.GNFS.ZS",
     lambda: wb_series("NE.TRD.GNFS.ZS", "WLD", 25)),
    ("wb_fdi",       "Foreign Direct Investment (% GDP) - World",    "%",      "WB/BX.KLT.DINV.WD.GD.ZS",
     lambda: wb_series("BX.KLT.DINV.WD.GD.ZS", "WLD", 25)),
    ("wb_tariff_us", "Tariff Rate: Applied Mean - US (%)",           "%",      "WB/TM.TAX.MRCH.WM.AR.ZS",
     lambda: wb_series("TM.TAX.MRCH.WM.AR.ZS", "US", 25)),
]


def compute_score(series):
    comp, _ = theme_percentile(series, SPECS["geopolitics"])
    return comp


def fetch_all():
    print("\n[geo] Geopolitics & Globalisation")
    result = {
        "meta": {
            "trend": "geopolitics", "label": "Geopolitics & Globalisation",
            "description": "Tracks geopolitical risk, trade openness, financial stress, and supply chain pressures.",
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
    raw = trend_3m(s.get("vix"))
    result["meta"]["direction"] = theme_direction({k: v["data"] for k, v in result["series"].items()}, SPECS["geopolitics"])
    return result


if __name__ == "__main__":
    data = fetch_all()
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved -> {OUTPUT}")
    print(f"  Score: {data['meta']['score']}  |  Direction: {data['meta']['direction']}")
