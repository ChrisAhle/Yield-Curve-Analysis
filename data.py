"""Download and cache daily U.S. Treasury constant-maturity yields from FRED.

No API key is needed: FRED serves each series as a CSV at fredgraph.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

# FRED series id -> maturity in years
SERIES = {
    "DGS1MO": 1 / 12,
    "DGS3MO": 0.25,
    "DGS6MO": 0.5,
    "DGS1": 1.0,
    "DGS2": 2.0,
    "DGS3": 3.0,
    "DGS5": 5.0,
    "DGS7": 7.0,
    "DGS10": 10.0,
    "DGS20": 20.0,
    "DGS30": 30.0,
}
LABELS = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
MATURITIES = np.array(list(SERIES.values()))

# The 30Y was discontinued from Feb 2002 to Feb 2006, so 2006-03 is the first
# month with the full 1M-30Y curve. That still covers 2008, 2020 and 2022.
DEFAULT_START = "2006-03-01"

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CACHE = DATA_DIR / "treasury_yields.csv"


def _fetch_series(sid: str) -> pd.Series:
    df = pd.read_csv(FRED_URL.format(sid=sid), na_values=["."])
    df.columns = ["date", sid]
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")[sid]


def download_yields() -> pd.DataFrame:
    """Download every maturity from FRED and save the raw panel to data/."""
    print("Downloading Treasury yields from FRED...")
    frames = [_fetch_series(sid) for sid in SERIES]
    raw = pd.concat(frames, axis=1)
    DATA_DIR.mkdir(exist_ok=True)
    raw.to_csv(CACHE)
    return raw


def load_yields(start: str = DEFAULT_START, refresh: bool = False) -> pd.DataFrame:
    """Return a clean daily panel of yields in percent, columns labeled 1M..30Y.

    Uses the cached CSV unless refresh=True or no cache exists.
    """
    if refresh or not CACHE.exists():
        raw = download_yields()
    else:
        raw = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    df = raw[list(SERIES)].copy()
    df.columns = LABELS
    df = df.loc[start:]
    # Holidays show as blank rows for every maturity: drop them.
    df = df.dropna(how="all")
    # Fill the rare single-maturity gap with the prior day, then drop anything left.
    df = df.ffill(limit=3).dropna()
    return df


def synthetic_yields(start: str = DEFAULT_START, end: str = "2026-10-23", seed: int = 7) -> pd.DataFrame:
    """Fake but realistic-looking yields, used only by `--demo` to test the code
    without internet access. Never use these numbers in the README or resume."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, end)
    n = len(dates)
    lam = 0.0609 * 12
    tau = MATURITIES
    x = lam * tau
    l2 = (1 - np.exp(-x)) / x
    l3 = l2 - np.exp(-x)
    level, slope, curv = np.empty(n), np.empty(n), np.empty(n)
    level[0], slope[0], curv[0] = 5.0, -0.2, 0.0
    for t in range(1, n):
        level[t] = level[t - 1] + 0.002 * (4.0 - level[t - 1]) + rng.normal(0, 0.05)
        slope[t] = slope[t - 1] + 0.003 * (-1.5 - slope[t - 1]) + rng.normal(0, 0.04)
        curv[t] = curv[t - 1] + 0.01 * (0.0 - curv[t - 1]) + rng.normal(0, 0.08)
    y = level[:, None] + slope[:, None] * l2 + curv[:, None] * l3
    y += rng.normal(0, 0.02, y.shape)
    return pd.DataFrame(np.round(y, 2), index=dates, columns=LABELS)
