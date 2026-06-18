"""
monitor.py — descriptive monitor layer (percentile-of-own-history)
==================================================================

This does NOT predict and does NOT reproduce Deutsche Bank's model. It is a
post-processing layer that reads the raw series the fetchers already saved and
answers one descriptive question per series:

    "Where does this indicator sit RIGHT NOW within its own history?"
    → a 0-100 percentile (85 = higher than 85% of its own past).

Each series is oriented by a `sign` so that a HIGH composite means the theme's
named force is historically elevated (see READINGS). This is description, not a
market call: we say "historically high / low", never "good / bad for markets".

Run:  python scripts/monitor.py            # enrich every data/*.json + summary
"""

import json
import math
import os
import statistics

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

# What "higher" means for each theme's composite (shown in the dashboard).
READINGS = {
    "technology":        "Higher = technology/AI activity running hotter than its own history.",
    "sovereign_debt":    "Higher = sovereign-debt pressure elevated vs its own history.",
    "geopolitics":       "Higher = geopolitical & globalisation stress elevated vs its own history.",
    "domestic_politics": "Higher = social discontent elevated vs its own history.",
    "demography":        "Higher = demographic pressure (ageing / shrinking workforce) vs its own history.",
    "energy":            "Higher = energy-system stress / disruption elevated vs its own history.",
}

# Orientation per series: (key, mode, sign).
#   mode  "yoy"   for trending series (prices, $-levels, output/price indices)
#         "level" for already-stationary series (rates, ratios, %, sentiment)
#   sign  +1 if higher raw value = MORE of the theme's named force, else -1.
# These are explicit, editable judgement calls — flip a sign to re-orient.
SPECS = {
    "technology": [
        ("semi_ip", "yoy", +1), ("computer_ip", "yoy", +1), ("productivity", "yoy", +1),
        ("multifactor", "yoy", +1), ("info_invest", "level", +1), ("durable_goods", "yoy", +1),
        ("rd_business", "yoy", +1), ("soxx", "yoy", +1), ("qqq", "yoy", +1),
        ("nvda", "yoy", +1), ("smh", "yoy", +1), ("arkk", "yoy", +1),
        ("wb_rnd_gdp", "level", +1), ("wb_hitech", "level", +1), ("wb_internet", "level", +1),
    ],
    "sovereign_debt": [
        ("debt_gdp", "level", +1), ("deficit", "level", -1), ("outlays_gdp", "level", +1),
        ("receipts_gdp", "level", -1), ("net_interest", "level", +1), ("yield_10y", "level", +1),
        ("yield_30y", "level", +1), ("yield_2y", "level", +1), ("breakeven", "level", +1),
        ("real_rate", "level", +1), ("hy_spread", "level", +1), ("term_premium", "level", +1),
        ("tlt", "yoy", -1), ("hyg", "yoy", -1), ("tip", "yoy", -1),
        ("wb_debt_us", "level", +1), ("wb_gdp_growth", "level", -1),
    ],
    "geopolitics": [
        ("vix", "level", +1), ("us_epu", "level", +1), ("global_epu", "level", +1),
        ("mfg_ppi", "yoy", +1), ("stlfsi", "level", +1), ("eem", "yoy", -1),
        ("gld", "yoy", +1), ("wb_trade_gdp", "level", -1), ("wb_fdi", "level", -1),
        ("wb_tariff_us", "level", +1),
    ],
    "domestic_politics": [
        ("consumer_sent", "level", -1), ("unemployment", "level", +1), ("u6", "level", +1),
        ("real_wages", "yoy", -1), ("labor_share", "level", -1), ("home_prices", "yoy", +1),
        ("median_income", "yoy", -1), ("cpi", "yoy", +1), ("wb_gini", "level", +1),
        ("wb_poverty", "level", +1),
    ],
    "demography": [
        ("lfpr", "level", -1), ("prime_age", "level", -1), ("emp_pop", "level", -1),
        ("working_age", "yoy", -1), ("birth_rate", "level", -1), ("wb_pop_us", "level", -1),
        ("wb_work_us", "level", -1), ("wb_fertility_us", "level", -1), ("wb_old_dep_us", "level", +1),
    ],
    "energy": [
        ("energy_cpi", "yoy", +1), ("wti_oil", "yoy", +1), ("natgas", "yoy", +1),
        ("elec_price", "yoy", +1), ("xle", "yoy", +1), ("icln", "yoy", -1),
        ("tan", "yoy", -1), ("fan", "yoy", -1), ("lit", "yoy", -1),
        ("wb_renewables", "level", -1), ("wb_renew_us", "level", -1),
        ("wb_energy_int", "level", +1), ("wb_fossil", "level", +1),
    ],
}


# ── quarterly + transforms ───────────────────────────────────────────
def _to_quarterly(data):
    if not data:
        return None
    buckets = {}
    for d, v in zip(data["dates"], data["values"]):
        if v is None or not d:
            continue
        ds = str(d)
        y = int(ds[:4])
        mm = ds[5:7]
        m = int(mm) if len(mm) == 2 and mm.isdigit() else 12   # annual (YYYY) → Q4
        buckets[(y, (m - 1) // 3 + 1)] = v
    return [buckets[k] for k in sorted(buckets)]


def _transform(qvals, mode, lag=4):
    if mode == "yoy":
        return [(qvals[i] / qvals[i - lag] - 1) * 100
                for i in range(lag, len(qvals)) if qvals[i - lag] not in (0, None)]
    return qvals


def _pct_rank(ref, current):
    n = len(ref)
    below = sum(1 for x in ref if x < current)
    eq = sum(1 for x in ref if x == current)
    return 100.0 * (below + 0.5 * eq) / n


def percentile_of_history(data, mode, sign, smooth=8, lag=4):
    """Oriented 0-100 percentile of the current (smoothed) value vs own history."""
    q = _to_quarterly(data)
    if not q or len(q) < lag + 12:
        return None
    s = _transform(q, mode, lag)
    if len(s) < 12:
        return None
    cur = statistics.fmean(s[-smooth:])
    p = _pct_rank(s, cur)
    return p if sign > 0 else 100.0 - p


def momentum(data, mode, sign, smooth=8, lag=4, look=4):
    """Recent movement of the oriented metric: 'up' / 'down' / 'flat'."""
    q = _to_quarterly(data)
    if not q:
        return "flat"
    s = _transform(q, mode, lag)
    if len(s) < smooth + look:
        return "flat"
    cur = statistics.fmean(s[-smooth:])
    prev = statistics.fmean(s[-smooth - look:-look])
    d = (cur - prev) * (1 if sign > 0 else -1)
    sd = statistics.pstdev(s) or 1.0
    if d > 0.15 * sd:
        return "up"
    if d < -0.15 * sd:
        return "down"
    return "flat"


def level_label(score):
    if score is None:
        return "No data"
    if score >= 80:
        return "Historically high"
    if score >= 60:
        return "Above its historical norm"
    if score > 40:
        return "Around its historical norm"
    if score > 20:
        return "Below its historical norm"
    return "Historically low"


# ── enrichment ───────────────────────────────────────────────────────
def enrich(trend_key, trend):
    spec = SPECS.get(trend_key, [])
    pcts, arrows = [], []
    for key, mode, sign in spec:
        entry = trend["series"].get(key)
        if not entry or "data" not in entry:
            continue
        p = percentile_of_history(entry["data"], mode, sign)
        if p is None:
            continue
        entry["pct"] = round(p, 1)
        entry["mode"] = mode
        entry["oriented"] = "higher" if sign > 0 else "lower"
        entry["arrow"] = momentum(entry["data"], mode, sign)
        pcts.append(p)
        arrows.append({"up": 1, "down": -1, "flat": 0}[entry["arrow"]])
    score = round(statistics.fmean(pcts), 1) if pcts else None
    meta = trend.setdefault("meta", {})
    meta["score"] = score                       # now a percentile, 0-100
    meta["pct"] = score
    meta["level_label"] = level_label(score)
    meta["reading"] = READINGS.get(trend_key, "")
    meta["n_series_scored"] = len(pcts)
    if arrows:
        avg = statistics.fmean(arrows)
        meta["direction"] = "up" if avg > 0.2 else "down" if avg < -0.2 else "flat"
    else:
        meta["direction"] = "flat"
    return trend


def run():
    summary = {"trends": {}, "metric": "percentile-of-own-history",
               "note": "Descriptive monitor. Higher = the theme's named force is "
                       "historically elevated vs its own past. Not a forecast, not "
                       "a market call, not a replication of Deutsche Bank's model."}
    counts = {"high": 0, "elevated": 0, "average": 0, "subdued": 0, "low": 0}
    scored = []
    for key in SPECS:
        path = os.path.join(DATA_DIR, f"{key}.json")
        if not os.path.exists(path):
            print(f"  [skip] {key}.json not found")
            continue
        trend = json.load(open(path, encoding="utf-8"))
        enrich(key, trend)
        json.dump(trend, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        sc = trend["meta"]["score"]
        lab = trend["meta"]["level_label"]
        print(f"  [ok] {key:<18} pct={sc}  [{lab}]  {trend['meta']['direction']}")
        summary["trends"][key] = {"score": sc, "label": lab,
                                  "direction": trend["meta"]["direction"],
                                  "reading": trend["meta"]["reading"]}
        if sc is not None:
            scored.append(sc)
            band = ("high" if sc >= 80 else "elevated" if sc >= 60 else
                    "average" if sc > 40 else "subdued" if sc > 20 else "low")
            counts[band] += 1
    summary["overall"] = round(statistics.fmean(scored), 1) if scored else None
    summary["bands"] = counts
    out = os.path.join(DATA_DIR, "summary.json")
    json.dump(summary, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n  overall percentile = {summary['overall']}  ->  {out}")


if __name__ == "__main__":
    run()
