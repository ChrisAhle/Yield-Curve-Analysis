"""Charts for the README. Each function saves one PNG."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import MATURITIES
from .stress import EPISODES

# Fixed categorical order (colorblind-checked palette); never cycled.
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SHADE = "#f0efec"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 10,
    "legend.frameon": False, "lines.linewidth": 2,
})


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _shade_episodes(ax):
    for start, end in EPISODES.values():
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color=SHADE, zorder=0, lw=0)


def curve_snapshots(yields: pd.DataFrame, path):
    picks = {
        "Jun 2007 (pre-crisis)": "2007-06-29",
        "Dec 2020 (zero rates)": "2020-12-31",
        "Oct 2022 (hiking)": "2022-10-21",
        "Jul 2023 (deep inversion)": "2023-07-03",
    }
    fig, ax = plt.subplots(figsize=(8, 4.6))
    i = 0
    for label, d in picks.items():
        if pd.Timestamp(d) < yields.index[0] or pd.Timestamp(d) > yields.index[-1]:
            continue
        row = yields.loc[:d].iloc[-1]
        ax.plot(MATURITIES, row.values, color=C[i], marker="o", ms=4, label=label)
        i += 1
    last = yields.iloc[-1]
    ax.plot(MATURITIES, last.values, color=INK, marker="o", ms=4,
            label=f"Latest ({yields.index[-1]:%b %d, %Y})")
    ax.set_xscale("log")
    ax.set_xticks(MATURITIES)
    ax.set_xticklabels(yields.columns)
    ax.minorticks_off()
    ax.set_ylabel("Yield (%)")
    ax.set_title("The Treasury curve has taken very different shapes")
    ax.legend(loc="best", fontsize=9)
    _save(fig, path)


def ns_factors(betas: pd.DataFrame, yields: pd.DataFrame, path):
    """Nelson-Siegel factors next to the simple market measures they track."""
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    pairs = [
        ("Level (β1)", betas["level"], "30Y yield", yields["30Y"]),
        ("Slope (−β2, positive = upward sloping)", -betas["slope"], "10Y − 3M", yields["10Y"] - yields["3M"]),
        ("Curvature (β3)", betas["curvature"], "2×5Y − 3M − 30Y", 2 * yields["5Y"] - yields["3M"] - yields["30Y"]),
    ]
    for ax, (name, factor, pname, proxy) in zip(axes, pairs):
        _shade_episodes(ax)
        ax.plot(proxy.index, proxy.values, color=INK2, lw=1, alpha=0.6, label=pname)
        ax.plot(factor.index, factor.values, color=C[0], lw=1.5, label="Nelson-Siegel factor")
        ax.axhline(0, color=INK2, lw=0.6)
        ax.set_title(name, fontsize=11)
        ax.set_ylabel("%")
        ax.legend(loc="upper right", fontsize=8.5, ncol=2)
    axes[0].text(0.0, 1.32, "Nelson-Siegel factors vs. simple curve measures (shaded = stress episodes)",
                 transform=axes[0].transAxes, fontsize=12, fontweight="bold", color=INK)
    _save(fig, path)


def pca_loadings(loadings: pd.DataFrame, explained: pd.Series, path):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    names = {"PC1": "Level", "PC2": "Slope", "PC3": "Curvature"}
    for i, pc in enumerate(loadings.columns):
        ax.plot(MATURITIES, loadings[pc].values, color=C[i], marker="o", ms=4,
                label=f"{pc} – {names.get(pc, pc)} ({explained[pc]:.1%} of variance)")
    ax.axhline(0, color=INK2, lw=0.6)
    ax.set_xscale("log")
    ax.set_xticks(MATURITIES)
    ax.set_xticklabels(loadings.index)
    ax.minorticks_off()
    ax.set_ylabel("Loading")
    ax.set_title(f"Three shapes explain {explained.sum():.1%} of daily curve moves")
    ax.legend(loc="lower right", fontsize=9)
    _save(fig, path)


def stress_bars(table: pd.DataFrame, path, title):
    """Grouped horizontal bars: one group per scenario, one bar per portfolio."""
    scen = list(table.index)[::-1]
    ports = list(table.columns)
    n_s, n_p = len(scen), len(ports)
    h = 0.8 / n_p
    fig, ax = plt.subplots(figsize=(9, 0.55 * n_s * n_p * 0.45 + 1.6))
    y = np.arange(n_s)
    for j, p in enumerate(ports):
        vals = table.loc[scen, p].values
        # first portfolio on top within each group, matching the legend order
        ax.barh(y - (j - (n_p - 1) / 2) * h, vals, height=h * 0.85, color=C[j], label=p)
    ax.axvline(0, color=INK2, lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(scen)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Instant P&L (% of value)")
    ax.set_title(title)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, fontsize=9)
    _save(fig, path)


def parallel_vs_actual(df: pd.DataFrame, path):
    episodes = df["episode"].unique()
    fig, axes = plt.subplots(1, len(episodes), figsize=(4 * len(episodes), 4.4), sharey=False)
    axes = np.atleast_1d(axes)
    ports = df["portfolio"].unique()
    short = [p.split(" (")[0] for p in ports]
    for ax, ep in zip(axes, episodes):
        sub = df[df["episode"] == ep].set_index("portfolio").loc[ports]
        x = np.arange(len(ports))
        ax.bar(x - 0.2, sub["actual P&L %"], 0.38, color=C[0], label="Actual curve move")
        ax.bar(x + 0.2, sub["parallel P&L %"], 0.38, color="#86b6ef", label="Parallel shift (= 10Y move)")
        ax.axhline(0, color=INK2, lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(short, rotation=30, ha="right", fontsize=8.5)
        ax.grid(axis="x", visible=False)
        ax.set_title(ep, fontsize=10)
    axes[0].set_ylabel("P&L on today's portfolio (%)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=9)
    fig.suptitle("What a parallel-shift stress test misses", x=0.01, ha="left",
                 fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(path, dpi=160)
    plt.close(fig)
