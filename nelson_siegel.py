"""Nelson-Siegel curve fitting.

y(tau) = b1 + b2 * (1 - e^(-lam*tau)) / (lam*tau)
            + b3 * [(1 - e^(-lam*tau)) / (lam*tau) - e^(-lam*tau)]

b1 = level, b2 = slope (negative when the curve slopes up), b3 = curvature.

Following Diebold & Li (2006), lambda is fixed at 0.0609 per month (0.7308 per
year), which puts the curvature hump at about 2.5 years. With lambda fixed, each
day's fit is an ordinary least-squares regression, so fitting ~5,000 days takes
well under a second and never fails to converge.
"""
import numpy as np
import pandas as pd

LAMBDA = 0.0609 * 12  # per year


def loadings(tau: np.ndarray, lam: float = LAMBDA) -> np.ndarray:
    """Return the (n_maturities x 3) matrix of factor loadings."""
    x = lam * np.asarray(tau, dtype=float)
    slope = (1 - np.exp(-x)) / x
    curv = slope - np.exp(-x)
    return np.column_stack([np.ones_like(x), slope, curv])


def fit(yields: pd.DataFrame, tau: np.ndarray, lam: float = LAMBDA):
    """Fit every day at once.

    Returns
    -------
    betas : DataFrame with columns level, slope, curvature (percent)
    rmse_bp : Series, each day's fit error in basis points
    """
    X = loadings(tau, lam)
    Y = yields.values
    B, *_ = np.linalg.lstsq(X, Y.T, rcond=None)  # 3 x n_days
    betas = pd.DataFrame(B.T, index=yields.index, columns=["level", "slope", "curvature"])
    fitted = (X @ B).T
    rmse_bp = pd.Series(np.sqrt(((Y - fitted) ** 2).mean(axis=1)) * 100, index=yields.index)
    return betas, rmse_bp


def curve(beta_row, tau: np.ndarray, lam: float = LAMBDA) -> np.ndarray:
    """Evaluate a fitted curve at any maturities (years)."""
    return loadings(tau, lam) @ np.asarray(beta_row, dtype=float)
