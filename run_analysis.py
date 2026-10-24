"""Treasury Yield Curve Analysis: Nelson-Siegel, PCA and curve stress tests.

Usage
-----
    python run_analysis.py            # use cached data (downloads it the first time)
    python run_analysis.py --refresh  # re-download the latest data from FRED
    python run_analysis.py --demo     # synthetic data, just to test the code offline

Outputs go to outputs/: charts in outputs/figures/, tables as CSV, and
outputs/summary.md with the key numbers.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src import data, nelson_siegel as ns, pca, plots, stress

OUT = Path(__file__).resolve().parent / "outputs"
FIG = OUT / "figures"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-download data from FRED")
    ap.add_argument("--demo", action="store_true", help="use synthetic data (offline test only)")
    ap.add_argument("--start", default=data.DEFAULT_START)
    args = ap.parse_args()
    FIG.mkdir(parents=True, exist_ok=True)

    # 1. Data --------------------------------------------------------------
    if args.demo:
        print("DEMO MODE: synthetic yields. Do not use these results.")
        yields = data.synthetic_yields(args.start)
    else:
        yields = data.load_yields(args.start, refresh=args.refresh)
    tau = data.MATURITIES
    start, end = yields.index[0], yields.index[-1]
    print(f"{len(yields):,} trading days, {start:%Y-%m-%d} to {end:%Y-%m-%d}")

    # 2. Nelson-Siegel -----------------------------------------------------
    betas, rmse = ns.fit(yields, tau)
    betas.assign(fit_rmse_bp=rmse).to_csv(OUT / "nelson_siegel_factors.csv")
    corr_level = betas["level"].corr(yields["30Y"])
    corr_slope = (-betas["slope"]).corr(yields["10Y"] - yields["3M"])

    # 3. PCA ---------------------------------------------------------------
    loadings, explained, scores = pca.run_pca(yields)
    loadings.to_csv(OUT / "pca_loadings.csv")
    # Do the statistical PCs line up with the Nelson-Siegel factors?
    d_betas = betas.diff().dropna().loc[scores.index]
    pc_ns_corr = {
        "PC1 vs level": scores["PC1"].corr(d_betas["level"]),
        "PC2 vs slope": scores["PC2"].corr(-d_betas["slope"]),
        "PC3 vs curvature": scores["PC3"].corr(d_betas["curvature"]),
    }

    # 4. Stress tests on today's curve -------------------------------------
    base = yields.iloc[-1].values
    ports = stress.build_portfolios(base)
    durations = {p.name: p.duration(base) for p in ports}

    scen = {**stress.parallel_shocks(), **stress.pca_shocks(loadings, scores)}
    shocks_df = pd.DataFrame(scen, index=yields.columns).T.round(1)
    shocks_df.to_csv(OUT / "scenario_shocks_bp.csv")
    pnl = stress.run(ports, base, scen)
    pnl.round(2).to_csv(OUT / "stress_pnl.csv")

    hist = stress.parallel_vs_actual(ports, base, yields)
    hist.round(2).to_csv(OUT / "historical_vs_parallel.csv", index=False)

    # 5. Charts ------------------------------------------------------------
    plots.curve_snapshots(yields, FIG / "1_curve_snapshots.png")
    plots.ns_factors(betas, yields, FIG / "2_nelson_siegel_factors.png")
    plots.pca_loadings(loadings, explained, FIG / "3_pca_loadings.png")
    plots.stress_bars(pnl, FIG / "4_stress_pnl.png",
                      "Same duration, different curve risk: P&L under each scenario")
    if len(hist):
        plots.parallel_vs_actual(hist, FIG / "5_parallel_vs_actual.png")

    # 6. Summary -----------------------------------------------------------
    write_summary(yields, rmse, corr_level, corr_slope, explained, pc_ns_corr,
                  durations, ports, pnl, hist, shocks_df, demo=args.demo)
    print(f"Done. See {OUT / 'summary.md'} and {FIG}/")


def _md_table(df: pd.DataFrame, fmt="{:.2f}") -> str:
    cols = [""] + list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.iterrows():
        cells = [fmt.format(v) if isinstance(v, (float, np.floating)) else str(v) for v in row]
        lines.append("| " + " | ".join([str(idx)] + cells) + " |")
    return "\n".join(lines)


def write_summary(yields, rmse, corr_level, corr_slope, explained, pc_ns_corr,
                  durations, ports, pnl, hist, shocks_df, demo):
    start, end = yields.index[0], yields.index[-1]
    barbell = ports[-1]
    inter, long_ = ports[1].name, ports[2].name
    L = []
    if demo:
        L.append("> **DEMO MODE — synthetic data. These numbers are not real.**\n")
    L += [
        "# Key results",
        f"Data: {len(yields):,} trading days of FRED Treasury yields (1M–30Y), "
        f"{start:%b %Y} to {end:%b %d, %Y}.\n",
        "## Nelson-Siegel",
        f"- Average fit error: **{rmse.mean():.1f} bp** (median {rmse.median():.1f} bp, "
        f"95th pct {rmse.quantile(0.95):.1f} bp)",
        f"- Level factor vs 30Y yield correlation: {corr_level:.2f}",
        f"- Slope factor vs 10Y–3M spread correlation: {corr_slope:.2f}\n",
        "## PCA on daily changes",
    ]
    for pc, v in explained.items():
        L.append(f"- {pc}: {v:.1%} of variance")
    L.append(f"- **First three PCs together: {explained.sum():.1%}**")
    for k, v in pc_ns_corr.items():
        L.append(f"- Correlation, {k} (daily changes): {v:.2f}")
    L += ["", "## Portfolios (priced off the latest curve)"]
    for p in ports:
        extra = f" — {p.note}" if p.note else ""
        L.append(f"- {p.name}: effective duration {durations[p.name]:.1f}{extra}")
    L += ["", "## Stress P&L (% of value)", _md_table(pnl), ""]

    # Headline comparisons
    par_ief = pnl.loc["Parallel +100bp", inter]
    par_bar = pnl.loc["Parallel +100bp", barbell.name]
    steep_gap = pnl.loc["Steepener (PC2 +2σ)", barbell.name] - pnl.loc["Steepener (PC2 +2σ)", inter]
    flat_gap = pnl.loc["Flattener (PC2 -2σ)", barbell.name] - pnl.loc["Flattener (PC2 -2σ)", inter]
    L += [
        "## Headlines",
        f"- Under a +100bp parallel shock the barbell and the 7–10Y bullet lose almost the "
        f"same ({par_bar:.2f}% vs {par_ief:.2f}%) because they have the same duration; the small "
        f"gap is the barbell's extra convexity.",
        f"- Barbell P&L minus bullet P&L: {steep_gap:+.2f} pts in a 2σ steepener, "
        f"{flat_gap:+.2f} pts in a 2σ flattener. A parallel stress test cannot see this difference.",
    ]
    if len(hist):
        h = hist.copy()
        h["abs miss"] = h["miss (pts)"].abs()
        worst = h.sort_values("abs miss", ascending=False).iloc[0]
        L.append(
            f"- Largest parallel-shift miss in a historical replay: **{worst['portfolio']}** in "
            f"**{worst['episode']}** — actual {worst['actual P&L %']:.2f}% vs parallel "
            f"{worst['parallel P&L %']:.2f}% ({worst['miss (pts)']:+.2f} pts)."
        )
        L += ["", "## Historical replays: actual curve move vs parallel shift",
              _md_table(hist.set_index("episode"))]
    L += ["", "## Scenario shocks (bp by maturity)", _md_table(shocks_df, "{:.0f}")]
    (OUT / "summary.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[: 12 + len(explained)]))


if __name__ == "__main__":
    main()
