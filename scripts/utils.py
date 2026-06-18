"""
utils.py -- Shared helpers for all megatrend fetchers.
"""

import os
import sys
import time
import requests
from pathlib import Path
import pandas as pd

# ── Force UTF-8 stdout ───────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Load .env FIRST, before anything else ────────────────────────
def _load_dotenv():
    try:
        from dotenv import load_dotenv
        # Search: scripts/../.env  (project root)
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
            _p(f"  [key] Loaded .env -> {env_path}")
        else:
            # fallback: current working directory
            cwd_env = Path(os.getcwd()) / ".env"
            if cwd_env.exists():
                load_dotenv(cwd_env, override=True)
                _p(f"  [key] Loaded .env -> {cwd_env}")
            else:
                _p(f"  [warn] No .env found (checked {env_path})")
                _p( "         Create one with: echo 'FRED_API_KEY=yourkey' > .env")
    except ImportError:
        pass  # python-dotenv not installed, rely on shell env vars


def _p(msg):
    """Print with ASCII fallback."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))


_load_dotenv()  # Must run before Fred() is instantiated


# ── FRED client (initialized AFTER dotenv) ───────────────────────
def _init_fred():
    try:
        from fredapi import Fred
        key = os.environ.get("FRED_API_KEY", "").strip()
        if not key:
            _p("  [warn] FRED_API_KEY not set -- FRED series will be skipped.")
            _p("         Get a free key: https://fred.stlouisfed.org/docs/api/api_key.html")
            _p("         Then add to .env:  FRED_API_KEY=your_key_here")
            return None
        _p(f"  [fred] API key found ({key[:6]}...)")
        return Fred(api_key=key)
    except ImportError:
        _p("  [warn] fredapi not installed: pip install fredapi")
        return None

fred = _init_fred()


# ── yFinance ─────────────────────────────────────────────────────
try:
    import yfinance as yf
    _YF_OK = True
except ImportError:
    _YF_OK = False

# A curl_cffi session that impersonates a real browser's TLS fingerprint is
# the known-effective way to dodge Yahoo's aggressive rate limiting. If
# curl_cffi isn't installed we fall back to plain yfinance.
_YF_SESSION = None
def _yf_session():
    global _YF_SESSION
    if _YF_SESSION is not None:
        return _YF_SESSION
    try:
        from curl_cffi import requests as _cffi
        _YF_SESSION = _cffi.Session(impersonate="chrome")
    except Exception:                 # noqa — curl_cffi missing or version mismatch
        _YF_SESSION = False           # sentinel: "tried, unavailable"
    return _YF_SESSION


# ── Helpers ──────────────────────────────────────────────────────

def _to_series(index, values):
    if hasattr(index, "strftime"):
        dates = index.strftime("%Y-%m-%d").tolist()
    else:
        dates = [str(d) for d in index]
    vals = [round(float(v), 4) if v is not None else None for v in values]
    while vals and vals[-1] is None:
        vals.pop(); dates.pop()
    return {"dates": dates, "values": vals}


def safe(name, fn, delay=0.3):
    """Run fn(), log result, return value or None. Never raises."""
    try:
        result = fn()
        if result is None:
            raise ValueError("returned None")
        _p(f"    [ok] {name}")
        time.sleep(delay)
        return result
    except Exception as e:
        err = str(e)
        # Suppress rate limit noise — not important
        if "Too Many Requests" in err or "Rate limit" in err.lower():
            _p(f"    [--] {name}: rate limited (skipped)")
        else:
            _p(f"    [xx] {name}: {err}")
        return None


# ── FRED ─────────────────────────────────────────────────────────

def fred_series(series_id, start="2005-01-01"):
    if not fred:
        return None
    s = fred.get_series(series_id, observation_start=start).dropna()
    if s.empty:
        raise ValueError("empty series")
    return _to_series(s.index, s.values)


# ── yFinance ─────────────────────────────────────────────────────

def yf_series(ticker, period="3y", field="Close", retries=4):
    if not _YF_OK:
        raise ImportError("yfinance not installed")
    sess = _yf_session()                     # curl_cffi session, or False if unavailable
    last_err = None
    for attempt in range(retries):
        try:
            # Actually USE the browser-impersonating session (this was the bug:
            # the session was built but never passed in). Some yfinance versions
            # don't accept `session`, so fall back gracefully.
            try:
                t = yf.Ticker(ticker, session=sess) if sess else yf.Ticker(ticker)
            except TypeError:
                t = yf.Ticker(ticker)
            df = t.history(period=period, auto_adjust=True)
            if df is None or df.empty:
                raise ValueError("no data returned")
            s = df[field].dropna()
            if s.empty:
                raise ValueError("empty after dropna")
            return _to_series(s.index, s.values)
        except Exception as e:               # noqa
            last_err = e
            msg = str(e).lower()
            rate = "too many requests" in msg or "rate" in msg
            time.sleep((2 ** attempt) * (1.5 if rate else 0.5))   # exp backoff
    raise ValueError(f"{ticker}: failed after {retries} attempts ({last_err})")


# ── World Bank ───────────────────────────────────────────────────

WB_BASE = "https://api.worldbank.org/v2"

def wb_series(indicator, country="US", mrv=20):
    url = (f"{WB_BASE}/country/{country}/indicator/{indicator}"
           f"?format=json&mrv={mrv}&per_page=100")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    payload = r.json()
    if len(payload) < 2 or not payload[1]:
        raise ValueError("empty World Bank response")
    records = [
        (item["date"], item["value"])
        for item in payload[1]
        if item["value"] is not None
    ]
    if not records:
        raise ValueError("all values null")
    records.sort(key=lambda x: x[0])
    return _to_series([r[0] for r in records], [r[1] for r in records])


def wb_multi_country(indicator, countries, mrv=20):
    country_str = ";".join(countries)
    url = (f"{WB_BASE}/country/{country_str}/indicator/{indicator}"
           f"?format=json&mrv={mrv}&per_page=500")
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    payload = r.json()
    if len(payload) < 2 or not payload[1]:
        raise ValueError("empty World Bank response")
    from collections import defaultdict
    buckets = defaultdict(list)
    for item in payload[1]:
        if item["value"] is not None:
            buckets[item["countryiso3code"]].append((item["date"], item["value"]))
    result = {}
    for code, recs in buckets.items():
        recs.sort(key=lambda x: x[0])
        result[code] = _to_series([r[0] for r in recs], [r[1] for r in recs])
    return result


# ── Derived helpers ──────────────────────────────────────────────

def get_data(series_entry):
    if series_entry is None:
        return None
    if "data" in series_entry:
        return series_entry["data"]
    if "values" in series_entry:
        return series_entry
    return None


def latest(series_entry):
    d = get_data(series_entry)
    if not d:
        return None
    for v in reversed(d["values"]):
        if v is not None:
            return v
    return None


def yoy_pct(series_entry, lag=12):
    d = get_data(series_entry)
    if not d:
        return None
    v = d["values"]
    if len(v) < lag + 1 or v[-lag - 1] in (None, 0):
        return None
    return round((v[-1] / v[-lag - 1] - 1) * 100, 2)


# ── Percentile engine (descriptive monitor: where is each series vs its
#    own history?). No prediction, no outcome correlation — just "this
#    indicator sits at the Nth percentile of its own past." ──────────────

def _to_quarterly(data):
    """Collapse any frequency to quarter-end. Handles FRED 'YYYY-MM-DD' and
    World Bank annual 'YYYY' dates; last observation in a quarter wins."""
    if not data:
        return None
    buckets = {}
    for d, v in zip(data["dates"], data["values"]):
        if v is None or not d:
            continue
        ds = str(d)
        y = int(ds[:4])
        mm = ds[5:7]
        m = int(mm) if len(mm) == 2 and mm.isdigit() else 12   # annual → Q4
        buckets[(y, (m - 1) // 3 + 1)] = v
    return [buckets[k] for k in sorted(buckets)]


def _transform_quarterly(data, mode="level", smooth=8, lag=4):
    """Quarterly, optionally year-on-year %, then trailing-smoothed."""
    q = _to_quarterly(data)
    if not q or len(q) < lag + 6:
        return None
    if mode == "yoy":
        s = [(q[i] / q[i - lag] - 1) * 100 for i in range(lag, len(q)) if q[i - lag] not in (0, None)]
    else:
        s = q
    if len(s) < 6:
        return None
    return [sum(s[max(0, i - smooth + 1): i + 1]) / (i - max(0, i - smooth + 1) + 1) for i in range(len(s))]


def percentile_latest(data, mode="level", smooth=8, offset=0):
    """Empirical percentile (0–100) of the current value within the series'
    own transformed history. offset>0 looks back that many quarters."""
    s = _transform_quarterly(data, mode, smooth)
    if not s or len(s) < 8 or offset >= len(s):
        return None
    target = s[-1 - offset]
    below = sum(1 for x in s if x < target)
    equal = sum(1 for x in s if x == target)
    return round((below + 0.5 * equal) / len(s) * 100, 1)


def theme_percentile(series_dict, spec, smooth=8, offset=0):
    """Composite 0–100 = mean of each series' percentile, oriented so that
    HIGHER = this theme's indicators are historically strong. Returns
    (composite, {key: oriented_percentile})."""
    parts = {}
    for key, mode, sign in spec:
        p = percentile_latest(series_dict.get(key), mode, smooth, offset)
        if p is None:
            continue
        parts[key] = round(100 - p, 1) if sign < 0 else p     # orient toward theme
    if not parts:
        return None, {}
    return round(sum(parts.values()) / len(parts), 1), parts


def theme_direction(series_dict, spec, smooth=8):
    """Recent momentum of the composite: now vs ~1 year (4 quarters) ago.
    Describes what HAS happened, not a forecast."""
    now, _ = theme_percentile(series_dict, spec, smooth, 0)
    prior, _ = theme_percentile(series_dict, spec, smooth, 4)
    if now is None or prior is None:
        return "neutral"
    d = now - prior
    return "up" if d > 3 else "down" if d < -3 else "neutral"


# Orientation specs: (series_key, mode, sign).
#   mode  — "yoy" for trending/price series, "level" for stationary rates,
#           ratios, %-of-GDP and annual World Bank series.
#   sign  — +1 if a HIGHER reading means this theme's conditions are
#           historically stronger; -1 if higher means more stress/weakness.
# These are DESCRIPTIVE orientation choices for a monitor, not predictions.
SPECS = {
    "technology": [
        ("semi_ip", "yoy", +1), ("computer_ip", "yoy", +1), ("productivity", "yoy", +1),
        ("info_invest", "level", +1), ("durable_goods", "yoy", +1), ("rd_business", "yoy", +1),
        ("soxx", "yoy", +1), ("qqq", "yoy", +1), ("nvda", "yoy", +1),
        ("wb_rnd_gdp", "level", +1), ("wb_hitech", "level", +1),
    ],
    "sovereign_debt": [
        ("debt_gdp", "level", -1), ("deficit", "level", +1), ("receipts_gdp", "level", +1),
        ("net_interest", "level", -1), ("yield_10y", "level", -1), ("yield_2y", "level", -1),
        ("breakeven", "level", -1), ("real_rate", "level", -1), ("hy_spread", "level", -1),
        ("tlt", "yoy", +1), ("hyg", "yoy", +1),
    ],
    "geopolitics": [
        ("vix", "level", -1), ("us_epu", "level", -1), ("global_epu", "level", -1),
        ("stlfsi", "level", -1), ("mfg_ppi", "yoy", -1),
        ("wb_trade_gdp", "level", +1), ("wb_fdi", "level", +1), ("wb_tariff_us", "level", -1),
    ],
    "domestic_politics": [
        ("consumer_sent", "level", +1), ("unemployment", "level", -1), ("u6", "level", -1),
        ("real_wages", "yoy", +1), ("labor_share", "level", +1), ("median_income", "yoy", +1),
        ("home_prices", "yoy", -1), ("cpi", "yoy", -1),
    ],
    "demography": [
        ("lfpr", "level", +1), ("prime_age", "level", +1), ("emp_pop", "level", +1),
        ("working_age", "yoy", +1), ("birth_rate", "level", +1),
        ("wb_fertility_us", "level", +1), ("wb_old_dep_us", "level", -1),
    ],
    "energy": [
        ("energy_cpi", "yoy", -1), ("elec_price", "yoy", -1),
        ("wb_renewables", "level", +1), ("wb_renew_us", "level", +1),
        ("wb_fossil", "level", -1), ("wb_energy_int", "level", -1),
        ("icln", "yoy", +1), ("tan", "yoy", +1),
    ],
}


def trend_3m(series_entry):
    d = get_data(series_entry)
    if not d:
        return "neutral"
    v = [x for x in d["values"] if x is not None]
    if len(v) < 6:
        return "neutral"
    recent = sum(v[-3:]) / 3
    older  = sum(v[-6:-3]) / 3
    if older == 0:
        return "neutral"
    chg = (recent - older) / older
    if chg > 0.01:  return "up"
    if chg < -0.01: return "down"
    return "neutral"
