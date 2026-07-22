"""Proxy volume profile kernels and their calibration (INFR-018 HYP-I4 exit 1).

Source ``SIGNAL-SIGNED.md`` §2.1: *"For any window, distribute each bar's volume
across its range and stack per level. Kernel is a test parameter — uniform,
body-weighted, or path-based … calibrated once against any finer-grained
reference (Part 6.4)."*

A finer reference **is** obtainable here: the Bybit public trade archive gives
trade-level volume-at-price, which is the truth this proxy stands in for. So the
kernel is calibrated rather than frozen blind, and ``SKIP-NO-REFERENCE`` is not
taken (checkpoint-014 §4 HYP-I4.1 bans a silent uncalibrated freeze).

**Volume only.** Distributing *delta* by the same kernels produces a
pseudo-signed profile that inherits the sign-placement problem in full — per-bar
delta is exact, per-level delta is not (§2.1, Part 5, card ban 2). Every entry
point calls :func:`xen.sigbar.fences.assert_no_per_level_delta`, so a signed
column cannot reach a kernel even by accident.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from xen.sigbar.fences import assert_no_per_level_delta

#: Number of price bins spanning a window's full range.
N_BINS = 200

#: Share of a bar's volume assigned inside the body by ``K-BODY``. Declared, not
#: tuned: the wicks are where price traded without settling, so the split is a
#: stated modelling choice that the calibration then judges.
BODY_SHARE = 0.70

KERNELS: tuple[str, ...] = ("K-UNIFORM", "K-BODY", "K-PATH")


def price_grid(low: float, high: float, n_bins: int = N_BINS) -> np.ndarray:
    """Bin edges spanning ``[low, high]``.

    A relative grid, not a tick grid: tick size is unrecoverable for the
    ``SPEC_INCOMPLETE`` part of the universe, and the calibration only needs the
    proxy and the truth to share one grid.
    """
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        raise ValueError(f"degenerate price window [{low}, {high}]")
    return np.linspace(low, high, n_bins + 1)


def _accumulate(edges: np.ndarray, lo: float, hi: float, vol: float, out: np.ndarray) -> None:
    """Spread ``vol`` uniformly over ``[lo, hi]``, proportional to overlap."""
    if hi <= lo:
        idx = int(np.clip(np.searchsorted(edges, lo, side="right") - 1, 0, len(out) - 1))
        out[idx] += vol
        return
    left = np.clip(edges[:-1], lo, hi)
    right = np.clip(edges[1:], lo, hi)
    overlap = np.maximum(right - left, 0.0)
    total = overlap.sum()
    if total > 0:
        out += vol * overlap / total


def build_profile(
    bars: pl.DataFrame,
    kernel: str,
    *,
    n_bins: int = N_BINS,
    edges: np.ndarray | None = None,
    weight_col: str = "Volume",
) -> tuple[np.ndarray, np.ndarray]:
    """Stack a window's bar volume into a volume-by-price profile.

    Parameters
    ----------
    bars :
        Bars of one window, with ``Open High Low Close Volume``.
    kernel :
        One of :data:`KERNELS`.
    n_bins :
        Grid resolution, used only when ``edges`` is not supplied.
    edges :
        An explicit grid. Required whenever two profiles must be comparable —
        deriving the grid from each subset's own range would silently put them
        on different axes.
    weight_col :
        The column distributed across price. **Volume only** — the parameter
        exists so the per-level-delta ban is checked against the column actually
        being spread, not against a constant. QA run 1 (I-16) found the guard
        called as ``assert_no_per_level_delta(pl.Series("Volume", []))``, a
        literal that evaluates the same way on every call and can never fail;
        a frame whose ``Volume`` column held ``|Δ|`` built a profile with no
        exception, so GT-3(d) was unsatisfied and three artifacts asserted a
        verification that was never performed.

    Returns
    -------
    (edges, profile)
        Bin edges and the per-bin volume.
    """
    if kernel not in KERNELS:
        raise ValueError(f"unknown kernel {kernel!r}; declared kernels are {KERNELS}")
    if weight_col not in bars.columns:
        raise ValueError(f"weight column {weight_col!r} not present")
    # Checked against the REAL column name being distributed (source §2.1 /
    # Part 5, card ban 2): per-bar delta is exact, per-level delta is not.
    assert_no_per_level_delta(bars[weight_col])
    if edges is None:
        lo, hi = float(bars["Low"].min()), float(bars["High"].max())
        edges = price_grid(lo, hi, n_bins)
    prof = np.zeros(len(edges) - 1, dtype=float)

    o = bars["Open"].to_numpy()
    h = bars["High"].to_numpy()
    low = bars["Low"].to_numpy()
    c = bars["Close"].to_numpy()
    v = bars[weight_col].to_numpy()

    for i in range(len(v)):
        if v[i] <= 0:
            continue
        if kernel == "K-UNIFORM":
            _accumulate(edges, low[i], h[i], v[i], prof)
        elif kernel == "K-BODY":
            b_lo, b_hi = min(o[i], c[i]), max(o[i], c[i])
            _accumulate(edges, b_lo, b_hi, v[i] * BODY_SHARE, prof)
            _accumulate(edges, low[i], h[i], v[i] * (1.0 - BODY_SHARE), prof)
        else:  # K-PATH — weight by how often the assumed intra-bar path crosses a level
            up_first = c[i] >= o[i]
            legs = (
                [(o[i], low[i]), (low[i], h[i]), (h[i], c[i])]
                if up_first
                else [(o[i], h[i]), (h[i], low[i]), (low[i], c[i])]
            )
            per_leg = v[i] / len(legs)
            for a, b in legs:
                _accumulate(edges, min(a, b), max(a, b), per_leg, prof)
    return edges, prof


def trade_truth_profile(
    trades: pl.DataFrame, edges: np.ndarray
) -> np.ndarray:
    """Bin raw trade volume onto the same grid — the calibration reference.

    Parameters
    ----------
    trades :
        Raw archive rows with ``price`` and ``size``.
    edges :
        Grid from :func:`build_profile`, so proxy and truth are comparable.
    """
    p = trades["price"].to_numpy()
    s = trades["size"].to_numpy()
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2)
    prof = np.zeros(len(edges) - 1, dtype=float)
    np.add.at(prof, idx, s)
    return prof


def poc_and_value_area(
    edges: np.ndarray, prof: np.ndarray, share: float = 0.685
) -> tuple[float, float, float]:
    """Point of control and value-area edges.

    ``share`` defaults to the source's ~68-70% value area (§2.1). The area is
    grown outward from the POC by repeatedly taking the richer neighbouring bin
    — the standard construction, stated because a symmetric quantile band would
    give a different object on a skewed profile.
    """
    mids = (edges[:-1] + edges[1:]) / 2
    total = prof.sum()
    if total <= 0:
        return float("nan"), float("nan"), float("nan")
    k = int(np.argmax(prof))
    lo = hi = k
    acc = prof[k]
    while acc < share * total and (lo > 0 or hi < len(prof) - 1):
        left = prof[lo - 1] if lo > 0 else -1.0
        right = prof[hi + 1] if hi < len(prof) - 1 else -1.0
        if right >= left:
            hi += 1
            acc += prof[hi]
        else:
            lo -= 1
            acc += prof[lo]
    return float(mids[k]), float(mids[lo]), float(mids[hi])


def displacement(
    edges: np.ndarray,
    proxy: np.ndarray,
    truth: np.ndarray,
    *,
    ib_width: float,
    tick: float | None,
) -> dict:
    """Compare a proxy profile against trade truth on one window.

    Every normalised figure names its divisor object in its own key, because
    this is exactly the seam where the programme has been burned before: the
    EXP-025 screen→graduation handoff inflated a target 4.1x by asserting the
    wrong ATR divisor from memory (L-21 / P-15). QA run 1 (I-17) found
    displacements normalised by the full calibration DAY's range while the
    design and the registry labelled them IB-width units.

    Parameters
    ----------
    ib_width :
        The session IB high-low in price units — the divisor design §5.1 names.
    tick :
        Instrument tick size in price units, where recoverable; ``None`` for
        SPEC_INCOMPLETE instruments, whose tick figures are then null rather
        than silently computed against a guessed tick.

    Returns
    -------
    dict
        POC and value-area-edge displacements in price units, in ticks, and in
        IB-width units, plus total-variation distance between the normalised
        profiles.
    """
    poc_p, val_p, vah_p = poc_and_value_area(edges, proxy)
    poc_t, val_t, vah_t = poc_and_value_area(edges, truth)
    sp, st = proxy.sum(), truth.sum()
    tv = float(np.abs(proxy / sp - truth / st).sum() / 2) if sp > 0 and st > 0 else float("nan")

    def _norm(x: float, d: float | None) -> float:
        return x / d if d and d > 0 else float("nan")

    poc_d, val_d, vah_d = abs(poc_p - poc_t), abs(val_p - val_t), abs(vah_p - vah_t)
    return {
        "poc_proxy": poc_p,
        "poc_truth": poc_t,
        "poc_disp_price": poc_d,
        "poc_disp_ticks": _norm(poc_d, tick),
        "poc_disp_norm_ib_width": _norm(poc_d, ib_width),
        "val_disp_norm_ib_width": _norm(val_d, ib_width),
        "vah_disp_norm_ib_width": _norm(vah_d, ib_width),
        "tv_distance": tv,
        "divisor_objects": {
            "ib_width": ib_width,
            "tick": tick,
            "note": "poc_disp_norm_ib_width divides by the SESSION IB high-low of the frozen "
                    "anchor on that day; poc_disp_ticks divides by the instrument tick size "
                    "(null where tick is unrecoverable)",
        },
    }


def level_confidence(bars: pl.DataFrame, edges: np.ndarray, kernel: str) -> np.ndarray:
    """Share of each level's volume contributed by NARROW-range bars.

    Source §2.1: *"attach per-level confidence … a POC or void detected mostly
    from fast bars is an artifact candidate."* Emitted as a **definition** in the
    pin, not applied as a filter — filtering here would be a value judgement,
    and Stage I does not make those.
    """
    rng = (bars["High"] - bars["Low"]).to_numpy()
    med = float(np.median(rng[rng > 0])) if (rng > 0).any() else 0.0
    narrow = bars.filter((pl.col("High") - pl.col("Low")) <= med)
    _, prof_all = build_profile(bars, kernel, edges=edges)
    if narrow.height == 0:
        return np.zeros_like(prof_all)
    _, prof_narrow = build_profile(narrow, kernel, edges=edges)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(prof_all > 0, prof_narrow / prof_all, 0.0)
