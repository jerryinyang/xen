"""INFR-018 HYP-I3 — acceptance discriminator race (source Appendix B Phase 2).

Races the pre-registered A6 candidates — price-only and flow-augmented — on
their power to separate trap-type from acceptance-type boundary outcomes, using
the anchor frozen by HYP-I2. The winner is frozen and inherited by everything
downstream, which is why the source calls this its most-ordered item.

The separation read is a **report layer** with interpretation bands (L-32 /
INFR-016). It does not auto-stop the family: the layer is presented and the
operator signs the stop-or-proceed. Only the future-destroy tripwire is hard.

Usage
-----
    python python/experiments/INFR-018/code/hyp_i3_a6_race.py --band DESIGN
    python python/experiments/INFR-018/code/hyp_i3_a6_race.py --band DESIGN --workers 10
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    SEED_DERANGE,
    adjudicate_i3_survival,
    day_clustered_ci,
    mde_curve,
    out_dir,
    realise_universe,
    residualise_symbol,
    write_json,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.sigbar.acceptance import (  # noqa: E402
    LABEL_ACCEPTANCE,
    LABEL_UNRESOLVED,
    POKE_DELTAS,
    QUALIFY_MINUTES,
    Discriminator,
    assert_windows_disjoint,
    evaluate_discriminator,
    find_pokes,
    label_outcomes,
    race_grid,
    separation,
)
from xen.sigbar.fences import assert_frozen_inputs, band_window, load_bars, repo_root  # noqa: E402
from xen.sigbar.sessions import (  # noqa: E402
    CANDIDATE_ANCHORS,
    anchor_table,
    attach_sessions,
    session_breaks,
)

#: Interpretation bands for the separation statistic S (design.md §4.6).
#: LABELS FOR THE OPERATOR'S READ — never machine thresholds; nothing is dropped
#: at any of them and no candidate is hidden (retired `one_subset`, L-32).
BAND_SEPARATES_S = 0.15
BAND_SEPARATES_CI = 0.05
BAND_COLLAPSE_MAX = 0.25

#: Planted separations for the exit MDE curve, published before the real read.
SEP_MDE_GRID = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50]


def derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    """A permutation with zero fixed points (L-28).

    A uniform permutation has E[fixed points] = 1 for any n and leaves at least
    one about 63% of the time; VAL-008 shipped a destroy with 11.1% of slots
    still at true alignment, so the planted edge only partially collapsed.
    Rejection-sample until the draw is a true derangement, then assert it.
    """
    if n < 2:
        raise ValueError("a derangement needs n >= 2")
    for _ in range(10_000):
        p = rng.permutation(n)
        if not np.any(p == np.arange(n)):
            return p
    raise RuntimeError("could not draw a derangement")


def derange_within_blocks(
    df: pl.DataFrame, block_col: str, rng: np.random.Generator
) -> tuple[np.ndarray, dict]:
    """Positional derangement applied INSIDE each block, never across blocks.

    Design §4.4 specifies derangement *within calendar-day blocks*. Deranging
    across the whole panel would destroy the day-level common component as well
    as the rule-to-outcome pairing, so the control's separation is pushed closer
    to zero than the declared control would give — which flatters the collapse
    fraction the operator reads and inflates the real-vs-control contrast. It
    would also be inconsistent with the day-clustered inference used everywhere
    else in this item.

    Blocks of size 1 admit no derangement; they are left in place and COUNTED
    as ``n_unpermuted_singleton_rows``. Callers that form a destroy population
    MUST exclude those rows (path-swap does — I-57); they are never "spliced".
    """
    idx = np.arange(df.height)
    out = idx.copy()
    unpermuted = 0
    blocks = 0
    n_permutable = 0
    n_fixed_in_permutable = 0
    for _, sub in df.with_row_index("__i").group_by(block_col):
        pos = sub["__i"].to_numpy()
        blocks += 1
        if len(pos) < 2:
            unpermuted += len(pos)
            continue
        new_pos = pos[derangement(len(pos), rng)]
        out[pos] = new_pos
        n_permutable += len(pos)
        n_fixed_in_permutable += int(np.sum(new_pos == pos))
    return out, {
        "n_blocks": blocks,
        "n_unpermuted_singleton_rows": unpermuted,
        # I-33: rate only over rows that were eligible for derangement (block size ≥ 2).
        "fixed_point_rate_within_permutable": (
            float(n_fixed_in_permutable / n_permutable) if n_permutable else None
        ),
        "n_permutable_rows": n_permutable,
    }


def build_events(
    bars: pl.DataFrame, sessions: pl.DataFrame, delta_frac: float, ib_minutes: int
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Pokes and their outcome labels for one symbol at one poke depth."""
    pokes = find_pokes(bars, sessions, delta_frac)
    if pokes.height == 0:
        return pokes, pokes
    labels = label_outcomes(bars, pokes)
    return pokes, labels


def swap_outcome_paths(
    bars_by_symbol: dict[str, pl.DataFrame],
    pokes: pl.DataFrame,
    rng: np.random.Generator,
) -> tuple[pl.DataFrame, dict[str, pl.DataFrame], dict]:
    """Give each event a DIFFERENT event's outcome-window PRICE PATH, then relabel.

    Returns ``(labels, spliced_bars_by_symbol, stats)``. The spliced bars are the
    point of AMENDMENT-6: the destroy must reach the bars the DISCRIMINATOR reads,
    not only the labels.

    This is the item's hard future-destroy tripwire, and it has to swap paths
    rather than labels. QA run 1 (I-2) found it permuting ``label``/``t_accept``/
    ``t_trap`` — byte-identical to the soft control — which carries **zero**
    information: a label derangement collapses the separation whether or not a
    leak exists, because the calls are compared against labels that no longer
    belong to those events. So it "passes" under both hypotheses.

    A path swap destroys the rule-to-outcome pairing **at its source**: the
    labels are recomputed FROM the swapped path, so a discriminator that reads
    only pre-outcome bars keeps making the same calls against outcomes that are
    now unrelated to them, and its separation must vanish. A discriminator whose
    qualifying window reaches into outcome bars — an off-by-one, or a D3/D4
    window wider than ``QUALIFY_MINUTES`` — would still be correlated with the
    *true* path, and that is exactly what this destroys and a label swap does not.

    Donors are matched on remaining session length so the swapped path covers the
    same horizon, and the assignment is a derangement (zero fixed points among
    permutable rows; singletons are dropped from the destroy population — I-57).
    """
    ev = pokes.with_columns(
        ((pl.col("session_end") - pl.col("outcome_start")).dt.total_minutes()).alias("horizon")
    ).sort(["symbol", "anchor_ts"])
    if ev.height < 2:
        return ev.head(0), {}, {"status": "TOO_FEW_EVENTS"}

    # Bucket by horizon VALUE (average rank) so equal horizons share a bucket.
    # Ordinal rank put same-horizon events from different symbols into different
    # buckets purely by sort order, which made the same-symbol invariant
    # unfalsifiable under mutation (QA I-58). Derange WITHIN SYMBOL: a donor from
    # another instrument sits at a foreign price level and every label degenerates
    # by scale accident (QA run 6, I-45; operator-approved).
    ev = ev.with_columns(
        ((pl.col("horizon").rank("average") - 1.0) * 10 // max(ev.height, 1))
        .cast(pl.Int64)
        .alias("h_bucket")
    ).with_columns(
        (pl.col("symbol") + "|" + pl.col("h_bucket").cast(pl.String)).alias("swap_block")
    )
    perm, stats = derange_within_blocks(ev, "swap_block", rng)
    # L-28 / design §4.4: zero fixed points among rows that were eligible.
    fpr = stats.get("fixed_point_rate_within_permutable")
    if fpr is not None and fpr != 0.0:
        raise RuntimeError(
            f"path-swap derangement produced fixed points (rate={fpr}) — L-28 / design §4.4"
        )
    stats = {
        **stats,
        "block_definition": "symbol x horizon-value-decile (same-symbol donors only)",
    }

    # Materialise rows once. Polars `df[i]` rebuilds a frame per access and
    # dominated the tripwire wall-clock; dict rows are the same values, same
    # seed, same derangement — only the access path changes (PERF-NOTE).
    tgt_rows = ev.to_dicts()
    don_rows = ev[perm.tolist()].to_dicts()
    relabelled: list[pl.DataFrame] = []
    spliced_by_symbol: dict[str, list[pl.DataFrame]] = {}
    replaced_windows: dict[str, list[tuple]] = {}
    n_spliced = 0
    n_self_donor_skipped = 0
    n_no_donor_path = 0
    n_cross_symbol = 0
    level_offsets_ib: list[float] = []
    for i, tgt in enumerate(tgt_rows):
        # Singleton blocks (and any residual fixed point) are self-donors: splicing
        # them would leave the true path in the destroy arm and count them as
        # destroyed (I-57 / VAL-008 shape). Drop from the destroy population.
        if int(perm[i]) == i:
            n_self_donor_skipped += 1
            continue
        don = don_rows[i]
        tsym = tgt["symbol"]
        dsym = don["symbol"]
        if dsym != tsym:
            # Block key is supposed to make this impossible; assert rather than
            # silently accept a scale-degenerate destroy (I-58 / I-45).
            n_cross_symbol += 1
            raise RuntimeError(
                f"path-swap produced a cross-symbol donor ({dsym} → {tsym}); "
                "block_definition must keep donors same-symbol"
            )
        dbars = bars_by_symbol.get(dsym)
        if dbars is None:
            n_no_donor_path += 1
            continue
        path = dbars.filter(
            (pl.col("OpenTime") >= don["outcome_start"])
            & (pl.col("OpenTime") < don["session_end"])
        )
        if path.height == 0:
            n_no_donor_path += 1
            continue
        # Re-time the donor's bars onto the target's outcome window. Truncate to
        # the TARGET's [outcome_start, session_end) so a longer donor cannot
        # over-run into the next session (duplicate OpenTime / foreign session_end
        # — I-61). Under-runs leave a shorter window; label_outcomes sees what is
        # there. Overwrite session fields with the TARGET's so a bar-frame column
        # can never reintroduce the donor's clock (defense in depth for I-56).
        tgt_start = tgt["outcome_start"]
        tgt_end = tgt["session_end"]
        tgt_anchor = tgt["anchor_ts"]
        offset = tgt_start - don["outcome_start"]
        swapped_bars = path.with_columns(
            (pl.col("OpenTime") + offset).alias("OpenTime"),
            pl.lit(tgt_anchor).alias("anchor_ts"),
        )
        if "session_end" in swapped_bars.columns:
            swapped_bars = swapped_bars.with_columns(pl.lit(tgt_end).alias("session_end"))
        swapped_bars = swapped_bars.filter(
            (pl.col("OpenTime") >= tgt_start) & (pl.col("OpenTime") < tgt_end)
        )
        if swapped_bars.height == 0:
            n_no_donor_path += 1
            continue
        # One-row poke frame — same schema label_outcomes joins on.
        tgt_poke = pl.DataFrame([tgt])
        lab = label_outcomes(swapped_bars, tgt_poke)
        if lab.height:
            relabelled.append(lab.with_columns(pl.lit(tsym).alias("symbol")))
            # The SAME swapped bars are kept so the discriminator can be evaluated
            # on them. Relabelling alone left every rule reading the target's real
            # outcome path, so a leaky rule decorrelated from the donor-derived
            # labels exactly like an honest one and the gate could never fire
            # (QA run 6, I-45; AMENDMENT-6).
            spliced_by_symbol.setdefault(tsym, []).append(swapped_bars)
            replaced_windows.setdefault(tsym, []).append((tgt_start, tgt_end))
            n_spliced += 1
            # I-66: how far the donor path sits from the target's IB mid, in IB widths.
            # A large offset makes labels resolve almost immediately by price level.
            ib_w = tgt.get("ib_width")
            if ib_w and ib_w > 0 and tgt.get("ib_high") is not None and tgt.get("ib_low") is not None:
                ib_mid = 0.5 * (float(tgt["ib_high"]) + float(tgt["ib_low"]))
                donor_mid = float(path["Close"].mean())
                level_offsets_ib.append(abs(donor_mid - ib_mid) / float(ib_w))
    if not relabelled:
        return (
            ev.head(0),
            {},
            {
                **stats,
                "status": "NO_DONOR_PATHS",
                "n_self_donor_skipped": n_self_donor_skipped,
                "n_no_donor_path": n_no_donor_path,
                "n_cross_symbol_donors": n_cross_symbol,
            },
        )

    # Rebuild each symbol's bar frame: its own bars everywhere EXCEPT the replaced
    # outcome windows, plus the donor bars in them. Sessions are disjoint per
    # symbol, so the windows cannot overlap. One filter expression over all
    # windows (not N sequential copies of the frame).
    spliced_bars_by_symbol: dict[str, pl.DataFrame] = {}
    for sym, parts in spliced_by_symbol.items():
        base = bars_by_symbol[sym]
        drop = pl.lit(False)
        for start, end in replaced_windows[sym]:
            drop = drop | ((pl.col("OpenTime") >= start) & (pl.col("OpenTime") < end))
        keep = base.filter(~drop)
        donor_rows = pl.concat(parts, how="vertical").select(base.columns)
        spliced = pl.concat([keep, donor_rows], how="vertical").sort("OpenTime")
        # I-61: a well-formed splice has unique OpenTime per symbol.
        if spliced.select("OpenTime").n_unique() != spliced.height:
            raise RuntimeError(
                f"path-swap produced duplicate OpenTime rows for {sym} "
                f"(n={spliced.height}, n_unique={spliced.select('OpenTime').n_unique()})"
            )
        spliced_bars_by_symbol[sym] = spliced

    # Denominator for spliced_fraction is the destroy-eligible population (not
    # self-donors): design §4.4 publishes coverage of events that entered the
    # destroy, not of the full poke table (I-57).
    n_eligible = int(ev.height) - n_self_donor_skipped
    unres_rate = None
    if relabelled:
        labs = pl.concat(relabelled, how="vertical")
        if "label" in labs.columns and labs.height:
            unres_rate = float(labs.select((pl.col("label") == LABEL_UNRESOLVED).mean()).item())

    return (
        pl.concat(relabelled, how="vertical"),
        spliced_bars_by_symbol,
        {
            **stats,
            "status": "OK",
            "n_events_spliced": n_spliced,
            "n_events_total": int(ev.height),
            "n_events_eligible": n_eligible,
            "n_self_donor_skipped": n_self_donor_skipped,
            "n_no_donor_path": n_no_donor_path,
            "n_cross_symbol_donors": n_cross_symbol,
            "spliced_fraction": (n_spliced / n_eligible) if n_eligible else None,
            "n_symbols_spliced": len(spliced_bars_by_symbol),
            # I-66: disclose that the destroy partly randomises price level.
            "swapped_unresolved_rate": unres_rate,
            "median_donor_level_offset_ib_widths": (
                float(np.median(level_offsets_ib)) if level_offsets_ib else None
            ),
        },
    )


# ---------------------------------------------------------------------------
# Symbol-parallel event assembly (same integrity rules as HYP-I2 run_jobs)
#
# Symbols are independent until the race pools them. Workers build the same
# residualised bars / pokes / labels; the parent concatenates in sorted-symbol
# order so worker count cannot reorder an aggregate. --workers 1 is the serial
# path. See PERF-NOTE.md.
# ---------------------------------------------------------------------------

_EVENT_WORKER: dict = {}


def _init_event_worker(
    band: str,
    membership: pl.DataFrame,
    anchors: pl.DataFrame,
    ib_minutes: int,
) -> None:
    _EVENT_WORKER["band"] = band
    _EVENT_WORKER["root"] = repo_root()
    _EVENT_WORKER["anchors"] = anchors
    _EVENT_WORKER["ib_minutes"] = ib_minutes
    _EVENT_WORKER["members"] = {
        s: membership.filter(pl.col("symbol") == s).select("day").unique()
        for s in membership["symbol"].unique().to_list()
    }


def _symbol_event_job(symbol: str) -> tuple:
    """One symbol → attached bars + per-δ events/pokes, or a skip reason."""
    band = _EVENT_WORKER["band"]
    root = _EVENT_WORKER["root"]
    anchors = _EVENT_WORKER["anchors"]
    ib_minutes = _EVENT_WORKER["ib_minutes"]
    md = _EVENT_WORKER["members"].get(symbol)
    raw = load_bars(symbol, band, root=root)
    if raw.height == 0:
        return symbol, None, {}, {}, None
    try:
        res = residualise_symbol(raw, symbol)
    except RuntimeError as exc:
        return symbol, None, {}, {}, str(exc)
    sess = session_breaks(res, anchors, ib_minutes)
    if sess.height == 0:
        return symbol, None, {}, {}, None
    attached = attach_sessions(res, anchors, ib_minutes)
    events_by_d: dict[float, pl.DataFrame] = {}
    pokes_by_d: dict[float, pl.DataFrame] = {}
    for dfrac in POKE_DELTAS:
        pokes, labels = build_events(attached, sess, dfrac, ib_minutes)
        if pokes.height == 0:
            continue
        ev = (
            pokes.join(labels, on="anchor_ts", how="inner")
            .with_columns(
                pl.lit(symbol).alias("symbol"),
                pl.col("anchor_ts").dt.truncate("1d").alias("day"),
            )
        )
        if md is not None and md.height:
            ev = ev.join(md, on="day", how="semi")
        if ev.height == 0:
            continue
        events_by_d[dfrac] = ev
        pokes_by_d[dfrac] = pokes.join(
            ev.select("anchor_ts"), on="anchor_ts", how="semi"
        ).with_columns(
            pl.lit(symbol).alias("symbol"),
            pl.col("anchor_ts").dt.truncate("1d").alias("day"),
        )
    return symbol, attached, events_by_d, pokes_by_d, None


def assemble_events(
    symbols: list[str],
    band: str,
    membership: pl.DataFrame,
    anchors: pl.DataFrame,
    ib_minutes: int,
    *,
    workers: int,
) -> tuple[dict[str, pl.DataFrame], dict[float, list[pl.DataFrame]], dict[float, list[pl.DataFrame]], list[dict]]:
    """Build per-symbol bars and per-δ event lists in sorted-symbol order."""
    all_events: dict[float, list[pl.DataFrame]] = {d: [] for d in POKE_DELTAS}
    all_pokes: dict[float, list[pl.DataFrame]] = {d: [] for d in POKE_DELTAS}
    per_symbol_bars: dict[str, pl.DataFrame] = {}
    skipped: list[dict] = []

    if workers == 1:
        _init_event_worker(band, membership, anchors, ib_minutes)
        results = (_symbol_event_job(s) for s in symbols)
        ctx = None
    else:
        os.environ["POLARS_MAX_THREADS"] = "1"
        ctx = cf.ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_event_worker,
            initargs=(band, membership, anchors, ib_minutes),
        )
        # map preserves input order → sorted-symbol assembly matches serial.
        results = ctx.map(_symbol_event_job, symbols, chunksize=1)
    try:
        for sym, attached, events_by_d, pokes_by_d, skip in tqdm(
            results, total=len(symbols), desc="events"
        ):
            if skip is not None:
                skipped.append({"symbol": sym, "reason": skip})
                continue
            if attached is None:
                continue
            per_symbol_bars[sym] = attached
            for dfrac, ev in events_by_d.items():
                all_events[dfrac].append(ev)
                all_pokes[dfrac].append(pokes_by_d[dfrac])
    finally:
        if ctx is not None:
            ctx.shutdown()
    return per_symbol_bars, all_events, all_pokes, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", default="DESIGN", choices=["DESIGN", "CONFIRM"])
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 1,
        help="symbol-parallel event-assembly workers; --workers 1 is single-process",
    )
    args = ap.parse_args()

    frozen = assert_frozen_inputs()
    root = repo_root()

    freeze_path = out_dir() / "anchor_freeze.json"
    if not freeze_path.exists():
        raise RuntimeError(
            "HYP-I3 requires the frozen HYP-I2 anchor (results/anchor_freeze.json). "
            "Source Appendix B: a result obtained out of sequence is unattributable and re-runs."
        )
    frozen_anchor = json.loads(freeze_path.read_text())
    anchor_id = frozen_anchor["anchor_id"]
    ib_minutes = int(frozen_anchor["ib_minutes"])
    spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == anchor_id)

    if args.band == "CONFIRM" and not (out_dir() / "a6_freeze.json").exists():
        raise RuntimeError(
            "CONFIRM path invoked before results/a6_freeze.json exists — the CONFIRM bank stays "
            "untouched until the DESIGN winner is frozen"
        )

    # The frozen race grid is written and hashed BEFORE execution; QA diffs the
    # executed set against it (design.md §4.2).
    grid = race_grid()
    grid_path = out_dir() / "a6_race_grid.json"
    grid_obj = {
        "qualify_minutes": QUALIFY_MINUTES,
        "poke_deltas": list(POKE_DELTAS),
        "discriminators": [
            {"disc_id": d.disc_id, "family": d.family, "flow_augmented": d.flow_augmented,
             "params": d.params} for d in grid
        ],
        "n_cells": len(grid) * len(POKE_DELTAS),
    }
    grid_path.write_text(json.dumps(grid_obj, indent=2))

    membership, recon = realise_universe(args.band, limit=args.limit)
    # I-22: freeze_and_pin reads this and refuses a smoke-scale freeze.
    universe_scale = {
        "limit": args.limit,
        "workers": args.workers,
        "n_symbols_selected": int(recon.get("n_distinct_symbols_selected") or 0),
        "n_days": int(recon.get("n_days") or 0),
    }
    symbols = sorted(membership["symbol"].unique().to_list())
    start, end = band_window(args.band)
    anchors = anchor_table(spec, start, end)

    # ---- assemble the event table once; every candidate reads the SAME events ----
    per_symbol_bars, all_events, all_pokes, skipped = assemble_events(
        symbols, args.band, membership, anchors, ib_minutes, workers=args.workers
    )

    rng = np.random.default_rng(SEED_DERANGE)
    cells = []
    for dfrac in POKE_DELTAS:
        if not all_events[dfrac]:
            continue
        events = pl.concat(all_events[dfrac], how="vertical")
        assert_windows_disjoint(events)
        base_rate = (
            events.filter(pl.col("label") != LABEL_UNRESOLVED)
            .select((pl.col("label") == LABEL_ACCEPTANCE).mean())
            .item()
        )
        unresolved_rate = events.select((pl.col("label") == LABEL_UNRESOLVED).mean()).item()
        # Index once per δ — the race loops every disc over the same partition.
        events_by_sym = {
            s: g for s, g in events.partition_by("symbol", as_dict=True).items()
        }
        # partition_by as_dict keys may be tuples in some polars versions
        events_by_sym = {
            (k[0] if isinstance(k, tuple) else k): v for k, v in events_by_sym.items()
        }

        for disc in grid:
            calls = []
            for sym, attached in per_symbol_bars.items():
                ev_s = events_by_sym.get(sym)
                if ev_s is None or ev_s.height == 0:
                    continue
                c = evaluate_discriminator(attached, ev_s, disc)
                calls.append(c.with_columns(pl.lit(sym).alias("symbol")))
            if not calls:
                continue
            called = pl.concat(calls, how="vertical")
            joined = events.join(called, on=["anchor_ts", "symbol"], how="inner").with_columns(
                pl.col("says_accept").fill_null(False)
            )
            stat = separation(joined)

            # ---- within-sample attribution control: labels deranged WITHIN days ----
            res_only = joined.filter(pl.col("label") != LABEL_UNRESOLVED)
            ctrl_stat: dict = {"S": None}
            derange_stats: dict = {}
            if res_only.height >= 2:
                perm, derange_stats = derange_within_blocks(res_only, "day", rng)
                deranged = res_only.with_columns(
                    pl.Series("label", res_only["label"].to_numpy()[perm])
                )
                ctrl_stat = separation(deranged)

            # ---- day-clustered uncertainty on the per-day separation ----
            per_day_all = (
                res_only.group_by("day")
                .agg(
                    (pl.col("label") == LABEL_ACCEPTANCE).filter(pl.col("says_accept")).mean().alias("p_yes"),
                    (pl.col("label") == LABEL_ACCEPTANCE).filter(~pl.col("says_accept")).mean().alias("p_no"),
                )
                .sort("day")
            )
            # Days on which the rule made only one kind of call cannot yield a
            # difference of conditional rates. They are EXCLUDED FROM THE INTERVAL
            # but COUNTED, because for a low-call-rate discriminator this is a
            # selection effect on the very inference that places the cell in a
            # band, and design §7 forbids anything being machine-dropped silently.
            per_day = per_day_all.drop_nulls().with_columns(
                (pl.col("p_yes") - pl.col("p_no")).alias("s_day")
            )
            n_days_dropped_no_call = per_day_all.height - per_day.height
            ci = day_clustered_ci(per_day["s_day"].to_numpy()) if per_day.height else {"n": 0}

            # ---- power: a planted-separation curve at the realised n ----
            power = (
                mde_curve(per_day["s_day"].to_numpy(), SEP_MDE_GRID) if per_day.height
                else {"mde": None, "n_days": 0}
            )
            mde_here = power.get("mde")

            s_real, s_ctrl = stat.get("S"), ctrl_stat.get("S")
            collapse = (s_ctrl / s_real) if s_real not in (None, 0) and s_ctrl is not None else None
            ci_lo = ci.get("ci", [None, None])[0]
            ci_hi = ci.get("ci", [None, None])[1]

            # Band ladder in design §4.6's own order. UNPOWERED is tested FIRST:
            # an underpowered cell labelled WASH reads as "measured, cannot
            # distinguish" when the truth is "not measurable at this n" — that
            # collapse is how absence of evidence becomes evidence of absence
            # (L-32, and the XENA-HTFCAP-001 defect in miniature).
            if s_real is None:
                band = "DEGENERATE_CALL_RATE"
            elif mde_here is None or mde_here > BAND_SEPARATES_S:
                band = "UNPOWERED"
            elif (
                s_real >= BAND_SEPARATES_S
                and ci_lo is not None
                and ci_lo > BAND_SEPARATES_CI
                and collapse is not None
                and abs(collapse) <= BAND_COLLAPSE_MAX
            ):
                band = "SEPARATES"
            elif ci_lo is not None and ci_lo > 0:
                band = "SUGGESTIVE"
            elif ci_hi is not None and ci_hi < 0:
                band = "CONTRADICTED"
            elif abs(s_real) < mde_here:
                band = "WASH"
            else:
                band = "WASH"

            # The separation S and the collapse fraction are contrasts and stay
            # in the open. The absolute conditional hit rates are exactly what a
            # downstream reader would mistake for an edge claim, so they are
            # quarantined under the §0 label — the same treatment HYP-I2 gives
            # its absolute arm levels (QA run 1, I-21: applied to one gate out of
            # three, the label is decorative rather than load-bearing).
            calibration_only = {
                "note": "NOT_AN_EDGE_CLAIM — absolute conditional rates, for audit of S only",
                "p_accept_given_yes": stat.pop("p_accept_given_yes", None),
                "p_accept_given_no": stat.pop("p_accept_given_no", None),
                "base_rate": base_rate,
                "call_rate": stat.get("call_rate"),
            }
            cells.append({
                "disc_id": disc.disc_id,
                "family": disc.family,
                "flow_augmented": disc.flow_augmented,
                "params": disc.params,
                "poke_delta": dfrac,
                "separation": stat,
                "control_deranged": {
                    **ctrl_stat,
                    "class": "within_sample_attribution",
                    "enforcement": "REPORT LAYER — collapse fraction reported, operator judges",
                    "destroy_form": "DERANGEMENT within calendar-day blocks (zero fixed points)",
                    "derangement_stats": derange_stats,
                },
                "collapse_fraction": collapse,
                "day_clustered_ci": ci,
                "n_days_dropped_no_call": n_days_dropped_no_call,
                "power": power,
                "unresolved_rate": unresolved_rate,
                "interpretation_band": band,
                "band_note": "LABEL, NOT A GATE — nothing is dropped on it (L-32)",
                "CALIBRATION_ONLY": calibration_only,
            })

    ranked = sorted(
        [c for c in cells if c["separation"].get("S") is not None],
        key=lambda c: c["separation"]["S"], reverse=True,
    )

    # ---- future-destroy tripwire on the leading cell (HARD) ----
    def _run_disc(disc, ev_frame: pl.DataFrame, *, read_past_qualify: bool = False,
                  bars_by_symbol: dict | None = None) -> dict:
        """Evaluate one rule. ``bars_by_symbol`` defaults to the real bars; the
        path-swap tripwire passes the SPLICED bars so the destroy reaches what the
        rule reads, not only the labels (AMENDMENT-6)."""
        calls = []
        for sym, attached in (bars_by_symbol or per_symbol_bars).items():
            ev_s = ev_frame.filter(pl.col("symbol") == sym)
            if ev_s.height == 0:
                continue
            calls.append(
                evaluate_discriminator(
                    attached, ev_s, disc, read_past_qualify=read_past_qualify
                ).with_columns(pl.lit(sym).alias("symbol"))
            )
        if not calls:
            return {"S": None}
        called = pl.concat(calls, how="vertical")
        j = ev_frame.join(called, on=["anchor_ts", "symbol"], how="inner").with_columns(
            pl.col("says_accept").fill_null(False)
        )
        return separation(j)

    tripwire = None
    if ranked:
        top = ranked[0]
        dfrac = top["poke_delta"]
        pokes_all = pl.concat(all_pokes[dfrac], how="vertical")
        swapped_labels, swapped_bars, swap_stats = swap_outcome_paths(
            per_symbol_bars, pokes_all, rng
        )
        disc = next(d for d in grid if d.disc_id == top["disc_id"])
        if swapped_labels.height:
            swapped_events = pokes_all.join(
                swapped_labels, on=["anchor_ts", "symbol"], how="inner"
            )
            # I-60: collapse fraction must divide two reads over the SAME event set.
            # S_raw over the full race population and S_swapped over the spliced
            # subset mixes a population change with the destroy's effect.
            raw_events_all = pl.concat(all_events[dfrac], how="vertical")
            raw_on_spliced = raw_events_all.join(
                swapped_events.select("anchor_ts", "symbol"),
                on=["anchor_ts", "symbol"],
                how="semi",
            )
            st_swapped = _run_disc(disc, swapped_events, bars_by_symbol=swapped_bars)
            st_raw_spliced = _run_disc(disc, raw_on_spliced)
            s_raw_pooled = top["separation"]["S"]
            s_raw = st_raw_spliced.get("S")
            s_swapped = st_swapped.get("S")
            cf = (
                s_swapped / s_raw
                if s_raw not in (None, 0) and s_swapped is not None
                else None
            )
            try:
                i3_surv = adjudicate_i3_survival(
                    S_raw=s_raw, S_swapped=s_swapped, collapse_fraction=cf
                )
            except ValueError:
                i3_surv = {"survives": None, "same_sign_material": None}
            tripwire = {
                "class": "future_destroy",
                "enforcement": "HARD — survival means the emission is invalid, never 'it works'",
                "adjudication_kind": "i3_path_swap_survival",
                "cell": top["disc_id"],
                "S_raw": s_raw,
                "S_raw_pooled_race": s_raw_pooled,
                "S_raw_n": st_raw_spliced.get("n"),
                "S_swapped": s_swapped,
                "S_swapped_n": st_swapped.get("n"),
                "collapse_fraction": cf,
                "survives": i3_surv.get("survives"),
                "destroy_form": "OUTCOME PRICE PATH swapped between events (derangement within "
                                "horizon buckets), labels RECOMPUTED from the swapped path",
                "swap_stats": swap_stats,
            }

            # Positive control (I-30): a deliberately leaky discriminator that
            # REALLY reads past qualify_end (read_past_qualify=True). Without the
            # bypass, w=240 is capped by the 30-min qualify filter and the probe
            # cannot demonstrate tripwire sensitivity.
            # Same population discipline as the main arm (I-60): probe raw on the
            # spliced event keys, probe swapped on the spliced bars.
            leaky = Discriminator("LEAK-PROBE", "D4", False, {"tau": 0.5, "w": 240})
            leak_raw_events = raw_on_spliced
            probe_raw = _run_disc(leaky, leak_raw_events, read_past_qualify=True)
            probe_swapped = _run_disc(
                leaky, swapped_events, read_past_qualify=True, bars_by_symbol=swapped_bars
            )
            probe_cf = (
                probe_swapped["S"] / probe_raw["S"]
                if probe_swapped.get("S") is not None and probe_raw.get("S") not in (None, 0)
                else None
            )
            try:
                probe_surv = adjudicate_i3_survival(
                    S_raw=probe_raw.get("S"),
                    S_swapped=probe_swapped.get("S"),
                    collapse_fraction=probe_cf,
                )
                probe_survives = bool(probe_surv["survives"])
            except ValueError:
                probe_survives = False
            tripwire["positive_control"] = {
                "kind": "i3_leak_plant",
                "purpose": "a discriminator that CAN see outcome bars (w=240, read_past_qualify), "
                           "evaluated on the SAME spliced bars. It reads the donor outcome path "
                           "and the labels come from the donor outcome path, so its separation "
                           "MUST PERSIST. If it collapses, the destroy is not reaching what the "
                           "rule reads and the gate's pass carries no information (AMENDMENT-6).",
                "required_outcome": "SURVIVES",
                "read_past_qualify": True,
                "S_raw": probe_raw.get("S"),
                "S_swapped": probe_swapped.get("S"),
                "collapse_fraction": probe_cf,
                "survives": probe_survives,
            }
        else:
            tripwire = {
                "class": "future_destroy",
                "enforcement": "HARD",
                "status": "COULD_NOT_RUN",
                "swap_stats": swap_stats,
            }

    write_json(
        f"hyp_i3_a6_race_{args.band}.json",
        {
            "hypothesis": "HYP-I3",
            "phase": "source Appendix B Phase 2 — race the acceptance discriminator",
            "band": args.band,
            "band_label": (
                "TRAIN_INTERNAL_CONFIRMATION: not out-of-sample in the programme's sense"
                if args.band == "CONFIRM" else "DESIGN — all tuning and selection"
            ),
            "inherited_anchor": {"anchor_id": anchor_id, "ib_minutes": ib_minutes,
                                 "freeze_sha256": frozen_anchor.get("pin_sha256")},
            "frozen_inputs": {
                "baselines_sha256": frozen.baselines_sha256,
                "column_pins_sha256": frozen.column_pins_sha256,
            },
            "race_grid": grid_obj,
            "bands": {
                "SEPARATES": f"S >= {BAND_SEPARATES_S} and ci_low > {BAND_SEPARATES_CI} and "
                             f"|collapse| <= {BAND_COLLAPSE_MAX}",
                "note": "LABELS FOR THE OPERATOR — never gates; no candidate is hidden or dropped",
            },
            "universe_scale": universe_scale,
            "symbols_skipped_no_baseline": skipped,
            "cells": cells,
            "ranked_top": ranked[:15],
            "tripwire_outcome_path_swap": tripwire,
            "scope": "STAGE I — a frozen definition, never evidence that anything works",
        },
    )
    print(f"wrote {out_dir() / f'hyp_i3_a6_race_{args.band}.json'}  cells={len(cells)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
