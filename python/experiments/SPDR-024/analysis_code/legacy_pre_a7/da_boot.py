"""QUARANTINED pre-AMENDMENT-7. Do not use for emission or analysis.md."""
raise RuntimeError(
    "AMENDMENT_7_QUARANTINE: this script is legacy (pre R1-R5 floor fix). "
    "Use analysis_code/analyse.py emission only; see legacy_pre_a7/README.md."
)

"""Vectorised two-stage (symbol-cluster x block) bootstrap of a mean. Data-analyst's own."""
from __future__ import annotations
import numpy as np

CHUNK = 200


def two_stage_boot_mean(values: np.ndarray, sym: np.ndarray, blk: np.ndarray,
                        n_boot: int = 2000, seed: int = 0) -> np.ndarray:
    """Resample symbols with replacement, then blocks within each drawn symbol."""
    rng = np.random.default_rng(seed)
    key = np.stack([sym, blk])
    _, binv = np.unique(key, axis=1, return_inverse=True)
    nb = int(binv.max()) + 1
    bsum = np.bincount(binv, weights=values, minlength=nb)
    bcnt = np.bincount(binv, minlength=nb).astype(float)
    bsym = np.zeros(nb, dtype=np.int64)
    bsym[binv] = sym
    usym = np.unique(sym)
    ns = len(usym)
    sym_idx = [np.where(bsym == s)[0] for s in usym]
    out = np.empty(n_boot)
    done = 0
    while done < n_boot:
        nbch = min(CHUNK, n_boot - done)
        S = np.empty((ns, nbch, ns))
        C = np.empty((ns, nbch, ns))
        for i, idx in enumerate(sym_idx):
            m = len(idx)
            draw = rng.integers(0, m, size=(nbch, ns, m))
            S[i] = bsum[idx][draw].sum(axis=2)
            C[i] = bcnt[idx][draw].sum(axis=2)
        pick = rng.integers(0, ns, size=(nbch, ns))
        cols = np.arange(ns)[None, :]
        rows = np.arange(nbch)[:, None]
        out[done:done + nbch] = (S[pick, rows, cols].sum(axis=1)
                                 / C[pick, rows, cols].sum(axis=1))
        done += nbch
    return out
