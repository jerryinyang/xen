"""Third-barrier geometry for ``CF-HA-HARAMI-001`` (Phase 014-B, EXP-058).

The single new analysis module for the third-barrier surface read. It supplies
the per-event **window length** ``n_event`` (in real domain bars after entry)
that EXP-058 varies one-at-a-time against the frozen benchmark adaptive time cap,
while the favourable target (``fav = C + rd*0.5*M_sofar``), the adverse target
(benchmark 1:1), and the P15 path-ordered fills are held at benchmark and reused
from :mod:`xen.expectancy`.

Two registered branches are exercised:

1. **``/THIRD-TIME``** (no new mechanism) — the benchmark adaptive cap
   ``N = max(floor, round(1.5 * median(trailing-20 confirmed-move durations)))``
   with the **floor only** raised over the predeclared grid ``{6 (BENCH), 12, 24,
   48}``. Produced by re-calling :func:`xen.expectancy.adaptive_time_caps_by_epoch`
   with each ``floor``; ``k_mult``/``window``/``min_moves`` stay at benchmark, so
   the warmup mask (``< 5`` trailing durations) is **identical** across floors —
   only the horizon changes.
2. **``/THIRD-EVENT``** (the new causal helper :func:`third_event_caps`) — hold
   until the ZigZag confirms the **next reversal-direction move** (``Direction ==
   rd`` with ``ConfirmTime > entry``), exiting at that confirmation bar (the P15
   resolver returns ``TIMECAP`` at its real close if no target was hit first),
   backstopped at ``8 * bench_N`` so censoring is bounded. The exit is a *forward*
   event (known going forward in real time, exactly as a time cap resolves at a
   forward bar) — never an unconfirmed pivot, never a future-bar peek.

:func:`variant_caps` is the thin per-variant wrapper that returns every variant's
``n_event`` array (delegating the time variants to
:func:`xen.expectancy.adaptive_time_caps_by_epoch`). Real prices/timestamps only;
no Heiken Ashi value ever enters this module.
"""
from __future__ import annotations

import numpy as np

from xen.expectancy import adaptive_time_caps_by_epoch

# --------------------------------------------------------------------------- #
# Frozen EXP-058 predeclared third-barrier constants (no tuning)
# --------------------------------------------------------------------------- #
BENCH_FLOOR = 6                                  # P4 benchmark time-cap floor
THIRD_TIME_FLOORS: dict[str, int] = {            # /THIRD-TIME predeclared grid
    "BENCH": 6, "THIRD-TIME-T12": 12, "THIRD-TIME-T24": 24, "THIRD-TIME-T48": 48,
}
THIRD_EVENT_BACKSTOP_MULT = 8                    # /THIRD-EVENT backstop = 8 * bench_N


# --------------------------------------------------------------------------- #
# Pure computation — /THIRD-EVENT per-event cap (causal forward event locator)
# --------------------------------------------------------------------------- #
def third_event_caps(
    entry_idx: np.ndarray,
    entry_epoch: np.ndarray,
    move_confirm_epoch: np.ndarray,
    move_confirm_idx: np.ndarray,
    move_direction: np.ndarray,
    rd: np.ndarray,
    bench_n_event: np.ndarray,
    bench_warmup: np.ndarray,
    backstop_mult: int = THIRD_EVENT_BACKSTOP_MULT,
) -> dict[str, np.ndarray]:
    """Per-event ``/THIRD-EVENT`` window length, availability, and event/backstop flag.

    For each entry ``t_i`` the exit is the **next** confirmed move with
    ``Direction == rd`` **and** ``ConfirmTime > t_i`` (the substrate confirming the
    faded reversal), capped at ``backstop = backstop_mult * bench_N``. The cap is
    expressed as a bar count ``n_event_evt = min(confirm_idx[j] - entry_idx,
    backstop)`` fed to :func:`xen.expectancy.resolve_path_ordered`, whose
    ``TIMECAP`` exit at ``close[entry + n_event_evt]`` *is* the event/backstop
    close-out. An entry that is benchmark-warmup (``bench_N`` undefined) has no
    defined backstop and is excluded (``avail = False``).

    The forward scan is bounded by the backstop horizon and stops at the first
    ``rd``-direction move (ZigZag moves alternate direction, so this is at most a
    couple of confirmations past the strict-after lower bound). Causality: the
    lower bound is ``searchsorted(confirm_epoch, t_i, side="right")`` so the exit
    move always confirmed strictly after entry.

    Parameters
    ----------
    entry_idx, entry_epoch : np.ndarray
        Entry-bar domain indices and ``CloseTime`` epochs (length ``n``).
    move_confirm_epoch, move_confirm_idx, move_direction : np.ndarray
        Confirmed-move ``ConfirmTime`` epochs (ascending), their domain-bar
        indices, and ``Direction`` (``+1``/``-1``), in confirmation order.
    rd : np.ndarray
        Reversal trade direction per entry (``= Direction_k`` of the last
        confirmed move).
    bench_n_event, bench_warmup : np.ndarray
        The BENCH (floor=6) adaptive cap and warmup mask per entry.
    backstop_mult : int, default 8
        Backstop multiple of ``bench_N``.

    Returns
    -------
    dict[str, np.ndarray]
        ``n_event`` (int64, 0 where unavailable), ``avail`` (bool, ``~bench_warmup``),
        ``event_bound`` (bool, True where an ``rd``-confirm bound within the backstop).
    """
    n = int(entry_idx.shape[0])
    n_event = np.zeros(n, dtype=np.int64)
    avail = np.zeros(n, dtype=bool)
    event_bound = np.zeros(n, dtype=bool)
    n_moves = int(move_confirm_epoch.shape[0])
    if n == 0:
        return {"n_event": n_event, "avail": avail, "event_bound": event_bound}
    # First confirmed move strictly after each entry (causal forward lower bound).
    lb = np.searchsorted(move_confirm_epoch, entry_epoch, side="right")
    for e in range(n):
        if bool(bench_warmup[e]):
            continue                                   # bench_N undefined -> no backstop
        avail[e] = True
        backstop = backstop_mult * int(bench_n_event[e])
        ei = int(entry_idx[e])
        rd_e = int(rd[e])
        j = int(lb[e])
        found = -1
        while j < n_moves and (int(move_confirm_idx[j]) - ei) <= backstop:
            if int(move_direction[j]) == rd_e:
                found = j
                break
            j += 1
        if found >= 0:
            n_event[e] = int(move_confirm_idx[found]) - ei
            event_bound[e] = True
        else:
            n_event[e] = backstop                      # no rd-confirm within backstop
    return {"n_event": n_event, "avail": avail, "event_bound": event_bound}


# --------------------------------------------------------------------------- #
# Pure computation — per-variant n_event wrapper (time variants delegate)
# --------------------------------------------------------------------------- #
def variant_caps(
    entry_idx: np.ndarray,
    entry_epoch: np.ndarray,
    move_confirm_epoch: np.ndarray,
    move_confirm_idx: np.ndarray,
    move_direction: np.ndarray,
    rd: np.ndarray,
    variant_ids: list[str],
) -> dict[str, dict[str, np.ndarray]]:
    """Per-variant ``n_event`` / ``avail`` / ``event_bound`` for the requested ids.

    ``/THIRD-TIME`` variants (incl. ``BENCH``) delegate to
    :func:`xen.expectancy.adaptive_time_caps_by_epoch` with the variant's floor and
    every other knob at benchmark; their availability is ``~warmup`` (the warmup
    mask is floor-independent). ``/THIRD-EVENT`` uses :func:`third_event_caps` with
    the BENCH cap as the backstop base. ``event_bound`` is all-``False`` for time
    variants (not applicable).

    Returns a dict keyed by variant id; each value has ``n_event`` (int64),
    ``avail`` (bool), ``event_bound`` (bool).
    """
    n = int(entry_idx.shape[0])
    # BENCH cap first — it is the backstop base and the warmup reference.
    bench_n, bench_warmup = adaptive_time_caps_by_epoch(
        entry_epoch, move_confirm_epoch, move_confirm_idx, floor=BENCH_FLOOR)
    out: dict[str, dict[str, np.ndarray]] = {}
    for vid in variant_ids:
        if vid in THIRD_TIME_FLOORS:
            floor = THIRD_TIME_FLOORS[vid]
            if vid == "BENCH":
                n_event, warmup = bench_n, bench_warmup
            else:
                n_event, warmup = adaptive_time_caps_by_epoch(
                    entry_epoch, move_confirm_epoch, move_confirm_idx, floor=floor)
            out[vid] = {"n_event": n_event, "avail": ~warmup,
                        "event_bound": np.zeros(n, dtype=bool)}
        elif vid == "THIRD-EVENT":
            out[vid] = third_event_caps(
                entry_idx, entry_epoch, move_confirm_epoch, move_confirm_idx,
                move_direction, rd, bench_n, bench_warmup)
        else:
            raise ValueError(f"third_barrier.variant_caps: unknown variant id {vid!r}")
    return out
