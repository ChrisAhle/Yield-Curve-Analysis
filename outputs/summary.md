# Key results
Data: 5,167 trading days of FRED Treasury yields (1M–30Y), Mar 2006 to Oct 22, 2026.

## Nelson-Siegel
- Average fit error: **10.5 bp** (median 9.4 bp, 95th pct 20.7 bp)
- Level factor vs 30Y yield correlation: 0.99
- Slope factor vs 10Y–3M spread correlation: 1.00

## PCA on daily changes
- PC1: 65.9% of variance
- PC2: 17.8% of variance
- PC3: 8.3% of variance
- **First three PCs together: 92.0%**
- Correlation, PC1 vs level (daily changes): 0.83
- Correlation, PC2 vs slope (daily changes): 0.78
- Correlation, PC3 vs curvature (daily changes): 0.83

## Portfolios (priced off the latest curve)
- Short 1-3Y (SHY-like): effective duration 1.9
- Intermediate 7-10Y (IEF-like): effective duration 6.9
- Long 20-30Y (TLT-like): effective duration 13.7
- Barbell (short + long, same duration): effective duration 6.9 — 58% short / 42% long

## Stress P&L (% of value)
|  | Short 1-3Y (SHY-like) | Intermediate 7-10Y (IEF-like) | Long 20-30Y (TLT-like) | Barbell (short + long, same duration) |
|---|---|---|---|---|
| Parallel +100bp | -1.85 | -6.59 | -12.44 | -6.32 |
| Parallel -100bp | 1.90 | 7.16 | 15.16 | 7.49 |
| Level up (PC1 +2σ) | -2.61 | -11.43 | -18.07 | -9.13 |
| Level down (PC1 -2σ) | 2.72 | 13.25 | 24.38 | 11.86 |
| Steepener (PC2 +2σ) | 0.38 | -2.03 | -5.44 | -2.07 |
| Flattener (PC2 -2σ) | -0.38 | 2.08 | 5.91 | 2.27 |
| Belly up (PC3 +2σ) | -1.03 | 1.37 | 8.58 | 3.02 |
| Belly down (PC3 -2σ) | 1.05 | -1.34 | -7.63 | -2.61 |

## Headlines
- Under a +100bp parallel shock the barbell and the 7–10Y bullet lose almost the same (-6.32% vs -6.59%) because they have the same duration; the small gap is the barbell's extra convexity.
- Barbell P&L minus bullet P&L: -0.04 pts in a 2σ steepener, +0.19 pts in a 2σ flattener. A parallel stress test cannot see this difference.
- Largest parallel-shift miss in a historical replay: **Short 1-3Y (SHY-like)** in **2022 hiking cycle (Dec 2021-Oct 2022)** — actual -6.72% vs parallel -4.88% (-1.84 pts).

## Historical replays: actual curve move vs parallel shift
|  | portfolio | 10Y move (bp) | 2s10s change (bp) | actual P&L % | parallel P&L % | miss (pts) |
|---|---|---|---|---|---|---|
| 2008 crisis (Sep-Dec 2008) | Short 1-3Y (SHY-like) | -149.00 | -2.00 | 2.86 | 2.85 | 0.01 |
| 2008 crisis (Sep-Dec 2008) | Intermediate 7-10Y (IEF-like) | -149.00 | -2.00 | 10.74 | 10.89 | -0.14 |
| 2008 crisis (Sep-Dec 2008) | Long 20-30Y (TLT-like) | -149.00 | -2.00 | 23.58 | 23.78 | -0.20 |
| 2008 crisis (Sep-Dec 2008) | Barbell (short + long, same duration) | -149.00 | -2.00 | 11.60 | 11.68 | -0.08 |
| COVID crash (Feb-Mar 2020) | Short 1-3Y (SHY-like) | -102.00 | 2.00 | 1.98 | 1.94 | 0.04 |
| COVID crash (Feb-Mar 2020) | Intermediate 7-10Y (IEF-like) | -102.00 | 2.00 | 7.03 | 7.31 | -0.28 |
| COVID crash (Feb-Mar 2020) | Long 20-30Y (TLT-like) | -102.00 | 2.00 | 15.25 | 15.49 | -0.24 |
| COVID crash (Feb-Mar 2020) | Barbell (short + long, same duration) | -102.00 | 2.00 | 7.58 | 7.66 | -0.08 |
| 2022 hiking cycle (Dec 2021-Oct 2022) | Short 1-3Y (SHY-like) | 269.00 | -107.00 | -6.72 | -4.88 | -1.84 |
| 2022 hiking cycle (Dec 2021-Oct 2022) | Intermediate 7-10Y (IEF-like) | 269.00 | -107.00 | -16.95 | -16.56 | -0.39 |
| 2022 hiking cycle (Dec 2021-Oct 2022) | Long 20-30Y (TLT-like) | 269.00 | -107.00 | -27.30 | -28.77 | 1.48 |
| 2022 hiking cycle (Dec 2021-Oct 2022) | Barbell (short + long, same duration) | 269.00 | -107.00 | -15.40 | -14.96 | -0.44 |
| 2023 bear steepener (Jul-Oct 2023) | Short 1-3Y (SHY-like) | 101.00 | 75.00 | -0.61 | -1.87 | 1.26 |
| 2023 bear steepener (Jul-Oct 2023) | Intermediate 7-10Y (IEF-like) | 101.00 | 75.00 | -6.38 | -6.65 | 0.27 |
| 2023 bear steepener (Jul-Oct 2023) | Long 20-30Y (TLT-like) | 101.00 | 75.00 | -13.39 | -12.55 | -0.84 |
| 2023 bear steepener (Jul-Oct 2023) | Barbell (short + long, same duration) | 101.00 | 75.00 | -6.00 | -6.38 | 0.38 |

## Scenario shocks (bp by maturity)
|  | 1M | 3M | 6M | 1Y | 2Y | 3Y | 5Y | 7Y | 10Y | 20Y | 30Y |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Parallel +100bp | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 |
| Parallel -100bp | -100 | -100 | -100 | -100 | -100 | -100 | -100 | -100 | -100 | -100 | -100 |
| Level up (PC1 +2σ) | 42 | 49 | 62 | 90 | 143 | 163 | 182 | 186 | 174 | 157 | 148 |
| Level down (PC1 -2σ) | -42 | -49 | -62 | -90 | -143 | -163 | -182 | -186 | -174 | -157 | -148 |
| Steepener (PC2 +2σ) | -178 | -106 | -68 | -52 | -20 | -7 | 13 | 26 | 34 | 41 | 42 |
| Flattener (PC2 -2σ) | 178 | 106 | 68 | 52 | 20 | 7 | -13 | -26 | -34 | -41 | -42 |
| Belly up (PC3 +2σ) | -82 | 14 | 40 | 55 | 63 | 48 | 17 | -8 | -30 | -56 | -62 |
| Belly down (PC3 -2σ) | 82 | -14 | -40 | -55 | -63 | -48 | -17 | 8 | 30 | 56 | 62 |
