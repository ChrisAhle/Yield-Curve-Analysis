"""Stress-test simple Treasury portfolios under different curve shocks.

Every portfolio is a basket of bullet bonds priced at par off today's curve.
Each scenario moves yields at the 11 FRED maturities by some number of basis
points; the shocked curve is interpolated linearly and every bond is fully
repriced. Full repricing (rather than a duration approximation) captures
convexity, which matters for the long end and for 100+ bp moves.
"""
import numpy as np
import pandas as pd

from .data import MATURITIES


# ---------------------------------------------------------------- bond math
def _interp(curve_pct: np.ndarray, t: np.ndarray) -> np.ndarray:
    return np.interp(t, MATURITIES, curve_pct)


def bond_price(coupon_pct, ytm_pct, maturity, freq: int = 2):
    """Price per 100 face of a bullet bond with whole coupon periods."""
    n = int(round(maturity * freq))
    c = coupon_pct / 100 / freq * 100
    y = ytm_pct / 100 / freq
    k = np.arange(1, n + 1)
    disc = (1 + y) ** -k
    return c * disc.sum() + 100 * disc[-1]


class Portfolio:
    """Equal-weighted basket of par bonds with the given maturities,
    optionally combined with other portfolios through `weights`."""

    def __init__(self, name, maturities=None, parts=None, note=""):
        self.name = name
        self.maturities = None if maturities is None else np.asarray(maturities, dtype=float)
        self.parts = parts  # list of (weight, Portfolio)
        self.note = note

    def value(self, base_curve, shocked_curve):
        """Market value (start = 100) after the shock."""
        if self.parts is not None:
            return sum(w * p.value(base_curve, shocked_curve) for w, p in self.parts)
        coupons = _interp(base_curve, self.maturities)  # par bonds today
        ytm_new = _interp(shocked_curve, self.maturities)
        prices = [bond_price(c, y, m) for c, y, m in zip(coupons, ytm_new, self.maturities)]
        return float(np.mean(prices))

    def pnl_pct(self, base_curve, shock_bp):
        shocked = base_curve + np.asarray(shock_bp, dtype=float) / 100
        return self.value(base_curve, shocked) - 100

    def duration(self, base_curve):
        """Effective duration from a +/-1bp parallel bump."""
        up = self.pnl_pct(base_curve, np.ones(len(MATURITIES)))
        dn = self.pnl_pct(base_curve, -np.ones(len(MATURITIES)))
        return (dn - up) / (2 * 0.0001 * 100)


def build_portfolios(base_curve):
    """Proxies for common Treasury ETFs plus a barbell and a bullet with equal duration."""
    short = Portfolio("Short 1-3Y (SHY-like)", np.arange(1.0, 3.01, 0.5))
    inter = Portfolio("Intermediate 7-10Y (IEF-like)", np.arange(7.0, 10.01, 0.5))
    long_ = Portfolio("Long 20-30Y (TLT-like)", np.arange(20.0, 30.01, 0.5))

    # Barbell of short + long weighted to match the intermediate's duration,
    # so a parallel shock treats the two identically.
    d_s, d_i, d_l = (p.duration(base_curve) for p in (short, inter, long_))
    w_long = (d_i - d_s) / (d_l - d_s)
    barbell = Portfolio(
        "Barbell (short + long, same duration)",
        parts=[(1 - w_long, short), (w_long, long_)],
        note=f"{1 - w_long:.0%} short / {w_long:.0%} long",
    )
    return [short, inter, long_, barbell]


# ---------------------------------------------------------------- scenarios
def parallel_shocks():
    n = len(MATURITIES)
    return {"Parallel +100bp": np.full(n, 100.0), "Parallel -100bp": np.full(n, -100.0)}


def pca_shocks(loadings: pd.DataFrame, scores: pd.DataFrame, n_sigma: float = 2.0, days: int = 252):
    """A 2-sigma, one-year move in each principal component (in bp by maturity)."""
    out = {}
    names = {
        "PC1": ("Level up (PC1 +2σ)", "Level down (PC1 -2σ)"),
        "PC2": ("Steepener (PC2 +2σ)", "Flattener (PC2 -2σ)"),
        "PC3": ("Belly up (PC3 +2σ)", "Belly down (PC3 -2σ)"),
    }
    for pc in loadings.columns:
        size = n_sigma * scores[pc].std() * np.sqrt(days)
        up, down = names[pc]
        out[up] = loadings[pc].values * size
        out[down] = -loadings[pc].values * size
    return out


EPISODES = {
    "2008 crisis (Sep-Dec 2008)": ("2008-09-12", "2008-12-31"),
    "COVID crash (Feb-Mar 2020)": ("2020-02-19", "2020-03-09"),
    "2022 hiking cycle (Dec 2021-Oct 2022)": ("2021-12-31", "2022-10-21"),
    "2023 bear steepener (Jul-Oct 2023)": ("2023-07-31", "2023-10-19"),
}


def historical_shocks(yields: pd.DataFrame, episodes=EPISODES):
    """The actual change in each maturity (bp) over each episode."""
    out = {}
    for name, (start, end) in episodes.items():
        if pd.Timestamp(start) < yields.index[0] or pd.Timestamp(end) > yields.index[-1]:
            continue
        a = yields.loc[:start].iloc[-1]
        b = yields.loc[:end].iloc[-1]
        out[name] = ((b - a) * 100).values
    return out


def run(portfolios, base_curve, scenarios: dict) -> pd.DataFrame:
    """P&L table: scenarios x portfolios, in percent of starting value."""
    rows = {name: [p.pnl_pct(base_curve, s) for p in portfolios] for name, s in scenarios.items()}
    return pd.DataFrame(rows, index=[p.name for p in portfolios]).T


def parallel_vs_actual(portfolios, base_curve, yields: pd.DataFrame, episodes=EPISODES) -> pd.DataFrame:
    """For each historical episode, compare the P&L from the actual curve move
    with the P&L from a parallel shift equal to the 10Y's move — which is what a
    'rates up X bp' stress test implicitly assumes."""
    hist = historical_shocks(yields, episodes)
    i10 = list(yields.columns).index("10Y")
    rows = []
    for name, shock in hist.items():
        flat = np.full(len(shock), shock[i10])
        for p in portfolios:
            actual = p.pnl_pct(base_curve, shock)
            parallel = p.pnl_pct(base_curve, flat)
            rows.append({
                "episode": name,
                "portfolio": p.name,
                "10Y move (bp)": shock[i10],
                "2s10s change (bp)": shock[i10] - shock[list(yields.columns).index("2Y")],
                "actual P&L %": actual,
                "parallel P&L %": parallel,
                "miss (pts)": actual - parallel,
            })
    return pd.DataFrame(rows)
