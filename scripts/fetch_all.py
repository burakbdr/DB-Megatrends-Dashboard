"""
Megatrend Dashboard -- Master Data Updater

Usage:
    python scripts/fetch_all.py
"""

import json, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from fetch_technology        import fetch_all as fetch_tech
from fetch_sovereign_debt    import fetch_all as fetch_debt
from fetch_geopolitics       import fetch_all as fetch_geo
from fetch_domestic_politics import fetch_all as fetch_pol
from fetch_demography        import fetch_all as fetch_demo
from fetch_energy            import fetch_all as fetch_energy

DATA_DIR     = os.path.join(os.path.dirname(__file__), "../data")
SUMMARY_PATH = os.path.join(DATA_DIR, "summary.json")

FETCHERS = [
    ("technology",        fetch_tech,   "technology.json"),
    ("sovereign_debt",    fetch_debt,   "sovereign_debt.json"),
    ("geopolitics",       fetch_geo,    "geopolitics.json"),
    ("domestic_politics", fetch_pol,    "domestic_politics.json"),
    ("demography",        fetch_demo,   "demography.json"),
    ("energy",            fetch_energy, "energy.json"),
]


def score_bar(score):
    if score is None: return "N/A "
    if score >= 67:   return f"{score:4.1f} [+]"
    if score >= 34:   return f"{score:4.1f} [~]"
    return              f"{score:4.1f} [-]"


def run_all():
    os.makedirs(DATA_DIR, exist_ok=True)
    t0 = time.time()

    print("=" * 60)
    print("   Megatrend Dashboard  --  Data Update")
    print(f"   {datetime.utcnow().strftime('%Y-%m-%d  %H:%M UTC')}")
    print("=" * 60)

    summary = {
        "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "trends": {},
        "overall_score": None,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
    }
    errors = []

    for trend_id, fetch_fn, filename in FETCHERS:
        try:
            data = fetch_fn()
            out_path = os.path.join(DATA_DIR, filename)
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            meta = data["meta"]
            summary["trends"][trend_id] = {
                "label":        meta["label"],
                "description":  meta.get("description", ""),
                "score":        meta["score"],
                "direction":    meta["direction"],
                "series_count": len(data["series"]),
                "sources":      meta["sources"],
                "file":         f"data/{filename}",
            }
            d = meta["direction"]
            if d == "up":     summary["positive_count"] += 1
            elif d == "down": summary["negative_count"] += 1
            else:             summary["neutral_count"]  += 1
        except Exception as e:
            print(f"\n  [ERROR] {trend_id}: {e}")
            errors.append((trend_id, str(e)))
        time.sleep(0.5)

    scores = [t["score"] for t in summary["trends"].values() if t["score"] is not None]
    if scores:
        summary["overall_score"] = round(sum(scores) / len(scores), 1)

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Also copy data/ into docs/data/ for GitHub Pages
    import shutil
    docs_data = os.path.join(DATA_DIR, "../docs/data")
    os.makedirs(docs_data, exist_ok=True)
    for fname in os.listdir(DATA_DIR):
        if fname.endswith(".json"):
            shutil.copy2(
                os.path.join(DATA_DIR, fname),
                os.path.join(docs_data, fname)
            )

    elapsed = round(time.time() - t0, 1)
    arrows  = {"up": "^", "down": "v", "neutral": "-"}

    print()
    print(f"  {'Megatrend':<42} {'Score':>9}   Dir   Series")
    print("  " + "-" * 62)
    for tid, t in summary["trends"].items():
        arrow = arrows.get(t["direction"], "?")
        n     = t.get("series_count", "?")
        print(f"  {t['label']:<42} {score_bar(t['score']):>9}   {arrow}     {n}")
    print("  " + "-" * 62)
    if summary["overall_score"]:
        print(f"  {'OVERALL':<42} {score_bar(summary['overall_score']):>9}")

    print(f"\n  ^ Positive: {summary['positive_count']}   "
          f"v Negative: {summary['negative_count']}   "
          f"- Neutral: {summary['neutral_count']}")

    if errors:
        print(f"\n  [warn] {len(errors)} error(s): {[e[0] for e in errors]}")

    print(f"\n  Completed in {elapsed}s")
    print(f"  Summary -> {SUMMARY_PATH}")
    print("=" * 60)
    return summary


if __name__ == "__main__":
    run_all()
