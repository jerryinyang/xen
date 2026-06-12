"""EXP-045 per-cell exit simulation, stability plane, and selection logic.

Pure, deterministic helpers for Phase 011 Track B exit training
(see analysis-plan.md). The only new logic in EXP-045 lives here:

  * per-event exit simulation for the two G0-frozen families — FH(H) by pure
    index arithmetic, MAD-band-target(m) by a bounded causal forward scan
    (first completed close at/beyond the frozen trigger-time target, or the
    first opposite-regime confirmation, whichever is earlier), with TRAIN-end
    forced closes flagged and included;
  * net per-event returns under the frozen P2 CONSERVATIVE cost model
    (round-trip cost + per-calendar-day financing);
  * the n-neighbour stability plane (k = 1, interior-only, design §6), the
    tunability rule (1×SE separation + split-half agreement, fail-closed),
    and the P4 membership floor S(θ*) ≥ +1×SE.

Discipline enforced here (each maps to a documented prior failure mode):

  * **per-EVENT** unit only — every denominator is an event count, never bars;
  * **look-ahead-safe** — exits scan strictly forward from the trigger using
    completed closes; targets/AVWAP/spread are frozen at trigger;
  * **no silent drops** — unfinished events are force-closed at the last
    completed TRAIN bar, flagged, and included in every score;
  * **frozen constants** — grids, k, the SE multiplier, and the P4 floor are
    G0 predeclarations; nothing here tunes or extends them.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen selection constants (design §5.4/§6; D0 P4/P6 — no tuning levers)
# --------------------------------------------------------------------------- #
FH_GRID: tuple[int, ...] = (2, 3, 4, 6, 8, 11, 16, 23)
MAD_GRID: tuple[float, ...] = (0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0, 5.7)
NEIGHBOUR_K: int = 1                       # 3-point neighbourhood, fixed
SE_SEPARATION_MULT: float = 1.0            # tunability separation (design §6)
P4_FLOOR_MULT: float = 1.0                 # membership floor S(θ*) ≥ +1×SE
SPLIT_HALF_MIN_EVENTS: int = 10            # fail-closed minimum per half
FORCED_CLOSE_DISCLOSURE_FRAC: float = 0.20

FAMILY_FH = "FH"
FAMILY_MAD = "MAD"

NS_PER_DAY = 86_400 * 1_000_000_000  # matches xen.financing.NS_PER_DAY


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CellEvents:
    """Per-cell event arrays needed by the exit simulation (TRAIN-only)."""

    instrument: str
    domain: str
    n_bars: int
    close: np.ndarray            # (n,) real domain Close
    close_time_ns: np.ndarray    # (n,) int64 epoch nanoseconds of CloseTime
    trigger_idx: np.ndarray      # (E,) int
    direction: np.ndarray        # (E,) int {-1, +1}
    regime_id: np.ndarray        # (E,) int
    avwap: np.ndarray            # (E,) AVWAP frozen at trigger
    spread: np.ndarray           # (E,) MAD band spread frozen at trigger
    trend_change_idx: np.ndarray  # (E,) first opposite-regime confirm bar > trigger; n (sentinel) if none
    rt_cost_bps: float           # P2 CONSERVATIVE round trip
    financing_bps_day: float     # P2 financing per calendar day


@dataclass(frozen=True)
class FamilyOutcome:
    """All per-event exit outcomes for one family over its full grid."""

    family: str
    grid: tuple[float, ...]
    net_bps: np.ndarray          # (E, G) net per-event return
    forced: np.ndarray           # (E, G) bool — TRAIN-end forced close


@dataclass(frozen=True)
class FamilyVerdict:
    """Per-cell, per-family selection record."""

    family: str
    theta_star: float | None     # interior stability argmax (grid value)
    theta_star_pos: int | None   # grid index of theta_star
    s_at_star: float | None      # stability score at theta_star
    se: float | None             # regime-cluster bootstrap SE at theta_star
    tunable: bool
    reason: str                  # "" when tunable; failure reason otherwise
    half1_pos: int | None        # split-half theta* grid indices
    half2_pos: int | None


# --------------------------------------------------------------------------- #
# Trend-change lookup (vectorized over events)
# --------------------------------------------------------------------------- #
def trend_change_lookup(
    trigger_idx: np.ndarray,
    direction: np.ndarray,
    confirm_idx: np.ndarray,
    confirm_dir: np.ndarray,
    n_bars: int,
) -> np.ndarray:
    """First opposite-regime confirmation bar **strictly after** each trigger.

    ``confirm_idx``/``confirm_dir`` come from the frozen regime table sorted by
    ``confirm_idx``. The strict-after convention (a confirmation on the trigger
    bar itself does not exit the event) is the scope's predeclared reading.
    Events with no later opposite confirmation map to the sentinel ``n_bars``
    (outside the bar range), so a genuine trend-change exit on the final TRAIN
    bar is distinguishable from a TRAIN-end forced close.
    """
    out = np.full(trigger_idx.shape[0], n_bars, dtype=np.int64)
    for d in (1, -1):
        opp = confirm_idx[confirm_dir == -d]
        if opp.size == 0:
            continue
        mask = direction == d
        pos = np.searchsorted(opp, trigger_idx[mask], side="right")
        found = pos < opp.size
        vals = out[mask]
        vals[found] = opp[pos[found]]
        out[mask] = vals
    return np.minimum(out, n_bars)


# --------------------------------------------------------------------------- #
# Net return (frozen P2 cost model)
# --------------------------------------------------------------------------- #
def net_from_exits(cell: CellEvents, exit_idx: np.ndarray) -> np.ndarray:
    """Direction-signed net log-bps from trigger close to each exit close.

    ``net = signed_log_bps − RT − financing × elapsed_calendar_days`` with
    exact fractional days from the bar ``CloseTime`` stamps (EXP-033
    convention).
    """
    t = cell.trigger_idx
    gross = cell.direction * (
        np.log(cell.close[exit_idx]) - np.log(cell.close[t])
    ) * 10_000.0
    days = (cell.close_time_ns[exit_idx] - cell.close_time_ns[t]) / NS_PER_DAY
    return gross - cell.rt_cost_bps - cell.financing_bps_day * days


def verify_financing() -> bool:
    """Regression guard for the timestamp-unit convention (ns, not µs).

    A 1-hour hold at 1.2 bps/day must charge 0.05 bps of financing. Run
    before any cell; raises on a unit mismatch.

    Raises
    ------
    ValueError
        If the financing charge deviates from the closed-form expectation.
    """
    one_hour_ns = 3_600 * 1_000_000_000
    cell = CellEvents(
        instrument="FIXTURE", domain="1h", n_bars=2,
        close=np.array([100.0, 100.0]),
        close_time_ns=np.array([0, one_hour_ns], dtype=np.int64),
        trigger_idx=np.array([0]), direction=np.array([1]),
        regime_id=np.array([0]), avwap=np.array([100.0]),
        spread=np.array([1.0]), trend_change_idx=np.array([2]),
        rt_cost_bps=0.0, financing_bps_day=1.2,
    )
    net = net_from_exits(cell, np.array([1]))
    expected = -1.2 / 24.0  # zero gross, financing for 1/24 day
    if abs(float(net[0]) - expected) > 1e-12:
        raise ValueError(
            f"financing unit regression FAILED: net={net[0]} != {expected} "
            "(expected 0.05 bps charge for a 1h hold at 1.2 bps/day)"
        )
    return True


# --------------------------------------------------------------------------- #
# Family 1 — FH(H): pure index arithmetic
# --------------------------------------------------------------------------- #
def simulate_fh(cell: CellEvents) -> FamilyOutcome:
    """Per-event FH exits for the full frozen grid (forced closes flagged)."""
    e = cell.trigger_idx.shape[0]
    g = len(FH_GRID)
    net = np.empty((e, g))
    forced = np.empty((e, g), dtype=bool)
    last = cell.n_bars - 1
    for j, h in enumerate(FH_GRID):
        raw = cell.trigger_idx + h
        forced[:, j] = raw > last
        net[:, j] = net_from_exits(cell, np.minimum(raw, last))
    return FamilyOutcome(FAMILY_FH, tuple(float(h) for h in FH_GRID), net, forced)


# --------------------------------------------------------------------------- #
# Family 2 — MAD-band-target(m): bounded causal forward scan
# --------------------------------------------------------------------------- #
def mad_exit_indices_one_event(
    close: np.ndarray, start: int, stop: int, targets: np.ndarray, direction: int
) -> np.ndarray:
    """First-crossing exit bar per target for one event (causal, bounded).

    Walks completed closes in ``(start, stop]`` once. Targets are monotone in
    the multiplier, so a single pointer over the sorted target ladder yields
    every grid point's first crossing in one pass — exactly equivalent to the
    naive per-(event, m) scan (asserted by ``verify_mad_scan``). Targets not
    hit by ``stop`` exit at ``stop`` (trend-change bar or TRAIN-end forced
    close — the caller distinguishes the two).
    """
    g = targets.shape[0]
    out = np.full(g, stop, dtype=np.int64)
    j = 0
    for i in range(start + 1, stop + 1):
        c = close[i]
        if direction == 1:
            while j < g and c >= targets[j]:
                out[j] = i
                j += 1
        else:
            while j < g and c <= targets[j]:
                out[j] = i
                j += 1
        if j == g:
            break
    return out


def naive_mad_exit_index(
    close: np.ndarray, start: int, stop: int, target: float, direction: int
) -> int:
    """Reference per-target scan for the equivalence fixture."""
    for i in range(start + 1, stop + 1):
        if (direction == 1 and close[i] >= target) or (
            direction == -1 and close[i] <= target
        ):
            return i
    return stop


def verify_mad_scan() -> bool:
    """Assert the ladder scan equals the naive per-target scan on fixtures.

    Self-contained guard (no market data); raises before any cell runs.

    Raises
    ------
    ValueError
        On any mismatch between the ladder and reference scans.
    """
    rng = np.random.default_rng(45)
    for trial in range(200):
        n = int(rng.integers(20, 80))
        close = 100.0 + np.cumsum(rng.normal(0, 0.5, size=n))
        start = int(rng.integers(0, n - 5))
        stop = int(rng.integers(start + 1, n))
        direction = 1 if rng.random() < 0.5 else -1
        base = close[start]
        ladder = np.sort(rng.uniform(0.1, 3.0, size=5))
        targets = base + direction * ladder
        got = mad_exit_indices_one_event(close, start, stop, targets, direction)
        for j, tgt in enumerate(targets):
            ref = naive_mad_exit_index(close, start, stop, float(tgt), direction)
            if got[j] != ref:
                raise ValueError(
                    f"MAD scan equivalence FAILED (trial {trial}, target {j}): "
                    f"ladder={got[j]} != reference={ref}"
                )
    return True


def simulate_mad(cell: CellEvents) -> FamilyOutcome:
    """Per-event MAD-band-target exits for the full frozen grid.

    Favorable target per multiplier m: ``avwap ± m × spread`` (frozen at
    trigger, direction-signed). Exit at the first completed close at/beyond
    the target or at the opposite-regime confirmation bar, whichever is
    earlier; TRAIN-end forced closes flagged.
    """
    e = cell.trigger_idx.shape[0]
    grid = np.asarray(MAD_GRID)
    g = grid.shape[0]
    exit_idx = np.empty((e, g), dtype=np.int64)
    last = cell.n_bars - 1
    for k in range(e):
        t = int(cell.trigger_idx[k])
        stop = int(min(cell.trend_change_idx[k], last))
        d = int(cell.direction[k])
        targets = cell.avwap[k] + d * grid * cell.spread[k]
        exit_idx[k] = mad_exit_indices_one_event(cell.close, t, stop, targets, d)
    # Forced only when the scan hit TRAIN end without a target or a valid
    # trend-change exit: the sentinel (trend_change_idx == n_bars) marks
    # "no opposite confirmation in TRAIN"; a genuine trend-change exit on the
    # final bar (trend_change_idx == last) is NOT forced.
    forced = (exit_idx == last) & (cell.trend_change_idx[:, None] > last)
    net = np.empty((e, g))
    for j in range(g):
        net[:, j] = net_from_exits(cell, exit_idx[:, j])
    return FamilyOutcome(FAMILY_MAD, tuple(float(m) for m in MAD_GRID), net, forced)


# --------------------------------------------------------------------------- #
# Stability plane (design §6) and selection
# --------------------------------------------------------------------------- #
def score_curve(net_bps: np.ndarray) -> np.ndarray:
    """Per-θ net mean over all events (the event-count denominator)."""
    return net_bps.mean(axis=0)


def stability_plane(scores: np.ndarray) -> np.ndarray:
    """Neighbourhood-mean stability score at every grid point.

    Interior points use the full 3-point (k = 1) neighbourhood. Endpoints use
    their truncated neighbourhood (2 points) — these values exist **only** so
    the design-§6 endpoint rule can be tested explicitly ("if the stability
    argmax lands on an endpoint, the family is non-tunable"); endpoints are
    never θ*-eligible.
    """
    g = scores.shape[0]
    s = np.empty(g)
    for i in range(g):
        lo = max(0, i - NEIGHBOUR_K)
        hi = min(g, i + NEIGHBOUR_K + 1)
        s[i] = scores[lo:hi].mean()
    return s


def interior_mask(g: int) -> np.ndarray:
    """Boolean θ*-eligibility mask: endpoints excluded (design §6)."""
    mask = np.ones(g, dtype=bool)
    mask[:NEIGHBOUR_K] = False
    mask[g - NEIGHBOUR_K:] = False
    return mask


def interior_argmax(s: np.ndarray) -> int:
    """Interior stability argmax; deterministic tie-break to the smaller θ."""
    interior = np.where(interior_mask(s.shape[0]))[0]
    best = interior[0]
    for i in interior[1:]:
        if s[i] > s[best]:
            best = i
    return int(best)


def endpoint_dominates(s: np.ndarray) -> bool:
    """True when an endpoint's (truncated-neighbourhood) stability strictly
    exceeds every interior stability score — the design-§6 endpoint failure
    ('the optimum lies outside the grid'; extending the grid would be tuning).
    """
    mask = interior_mask(s.shape[0])
    return bool(s[~mask].max() > s[mask].max())


def bootstrap_se(
    net_at_star: np.ndarray,
    direction: np.ndarray,
    regime: np.ndarray,
    rng: np.random.Generator,
    n_boot: int = 1_000,
) -> float:
    """Regime-cluster bootstrap SE of the per-event net mean at θ*.

    Resamples regime clusters with replacement within direction strata
    (frozen EXP-027 structure), event-weighted combined mean.
    """
    num = np.zeros(n_boot)
    den = np.zeros(n_boot)
    for d in (1, -1):
        mask = direction == d
        if not mask.any():
            continue
        _, inv = np.unique(regime[mask], return_inverse=True)
        sums = np.bincount(inv, weights=net_at_star[mask])
        cnts = np.bincount(inv).astype(float)
        r = sums.shape[0]
        sel = rng.integers(0, r, size=(n_boot, r))
        num += sums[sel].sum(axis=1)
        den += cnts[sel].sum(axis=1)
    means = np.divide(num, den, out=np.full(n_boot, np.nan), where=den > 0)
    finite = means[np.isfinite(means)]
    return float(finite.std(ddof=1)) if finite.size > 1 else float("nan")


def split_half_positions(
    net_bps: np.ndarray, trigger_time_ns: np.ndarray
) -> tuple[int | None, int | None, int, int]:
    """Interior stability argmax on each chronological event half.

    Events are ordered by trigger time; the first half receives the extra
    event when the count is odd (scope rule). Returns ``(pos1, pos2, n1, n2)``
    with positions ``None`` when a half is under the fail-closed minimum.
    """
    order = np.argsort(trigger_time_ns, kind="stable")
    e = order.shape[0]
    n1 = (e + 1) // 2
    halves = (order[:n1], order[n1:])
    out: list[int | None] = []
    for half in halves:
        if half.shape[0] < SPLIT_HALF_MIN_EVENTS:
            out.append(None)
            continue
        s = stability_plane(score_curve(net_bps[half]))
        out.append(interior_argmax(s))
    return out[0], out[1], n1, e - n1


def classify_family(
    outcome: FamilyOutcome,
    cell: CellEvents,
    trigger_time_ns: np.ndarray,
    rng: np.random.Generator,
) -> FamilyVerdict:
    """Full design-§6 verdict for one family in one cell (fail-closed)."""
    scores = score_curve(outcome.net_bps)
    s = stability_plane(scores)
    pos = interior_argmax(s)
    theta = outcome.grid[pos]
    se = bootstrap_se(outcome.net_bps[:, pos], cell.direction, cell.regime_id, rng)
    h1, h2, n1, n2 = split_half_positions(outcome.net_bps, trigger_time_ns)

    interior = s[interior_mask(s.shape[0])]
    if endpoint_dominates(s):
        # Design §6: the stability optimum lies on (or beyond) a grid edge —
        # the family fails outright; extending the grid would be tuning.
        reason = "endpoint_argmax"
    elif not np.isfinite(se):
        reason = "se_undefined"
    elif s[pos] - float(np.median(interior)) <= SE_SEPARATION_MULT * se:
        reason = "flat_plane"
    elif h1 is None or h2 is None:
        reason = "split_half_underpopulated"
    elif abs(h1 - pos) > 1 or abs(h2 - pos) > 1:
        reason = "split_half_disagreement"
    else:
        reason = ""
    return FamilyVerdict(
        family=outcome.family,
        theta_star=float(theta),
        theta_star_pos=pos,
        s_at_star=float(s[pos]),
        se=se,
        tunable=reason == "",
        reason=reason,
        half1_pos=h1,
        half2_pos=h2,
    )


def select_cell_exit(
    fh: FamilyVerdict, mad: FamilyVerdict
) -> tuple[str | None, FamilyVerdict | None]:
    """Cell exit = tunable family with higher S(θ*); exact tie → FH."""
    candidates = [v for v in (fh, mad) if v.tunable]
    if not candidates:
        return None, None
    if len(candidates) == 1:
        return candidates[0].family, candidates[0]
    if mad.s_at_star is not None and fh.s_at_star is not None and (
        mad.s_at_star > fh.s_at_star
    ):
        return FAMILY_MAD, mad
    return FAMILY_FH, fh


def is_member(leader: FamilyVerdict | None) -> bool:
    """P4 membership floor: S(θ*) ≥ +1 × SE of the leading family."""
    if leader is None or leader.s_at_star is None or leader.se is None:
        return False
    if not np.isfinite(leader.se):
        return False
    return leader.s_at_star >= P4_FLOOR_MULT * leader.se
