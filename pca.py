"""Principal component analysis of daily yield-curve changes."""
import numpy as np
import pandas as pd


def run_pca(yields: pd.DataFrame, n_components: int = 3):
    """PCA on daily changes in yields, measured in basis points.

    Returns
    -------
    loadings  : DataFrame (maturity x PC), each column is a unit-length shape
    explained : Series, share of total variance explained by each PC
    scores    : DataFrame (date x PC), the size of each PC's move every day
    """
    changes = yields.diff().dropna() * 100  # percent -> bp
    centered = changes - changes.mean()
    cov = np.cov(centered.values, rowvar=False)
    eigval, eigvec = np.linalg.eigh(cov)
    order = np.argsort(eigval)[::-1]
    eigval, eigvec = eigval[order], eigvec[:, order]

    names = [f"PC{i + 1}" for i in range(n_components)]
    vecs = eigvec[:, :n_components].copy()
    vecs = _fix_signs(vecs)

    loadings = pd.DataFrame(vecs, index=yields.columns, columns=names)
    explained = pd.Series(eigval[:n_components] / eigval.sum(), index=names)
    scores = pd.DataFrame(centered.values @ vecs, index=changes.index, columns=names)
    return loadings, explained, scores


def _fix_signs(vecs: np.ndarray) -> np.ndarray:
    """Eigenvectors have arbitrary signs. Fix them so the PCs read naturally:
    PC1 = yields up, PC2 = steepening (long end up vs short end),
    PC3 = belly up vs the wings."""
    v = vecs.copy()
    if v[:, 0].mean() < 0:
        v[:, 0] *= -1
    if v.shape[1] > 1 and v[-1, 1] - v[0, 1] < 0:
        v[:, 1] *= -1
    if v.shape[1] > 2:
        belly = v[5:8, 2].mean()  # 3Y, 5Y, 7Y
        wings = (v[0, 2] + v[-1, 2]) / 2
        if belly - wings < 0:
            v[:, 2] *= -1
    return v
