"""INFR-018 HYP-I2 — anchor selection (source Appendix B Phase 1).

Races 4 candidate session clocks x 3 IB lengths against matched random-offset
pseudo-anchors of the same session shape, on the DESIGN bank, pooled across the
online top-20 universe with calendar-day-clustered inference.

**What this produces is a parameter, not a result.** The reported quantity is
always the paired contrast ``E = A_real - A_control``; the absolute per-anchor
level is written to the artifact under ``CALIBRATION_ONLY`` and is barred from
any headline. Nothing here is evidence that a breakout signal works.

Usage
-----
    python python/experiments/INFR-018/code/hyp_i2_anchor_race.py --band DESIGN
    python python/experiments/INFR-018/code/hyp_i2_anchor_race.py --band CONFIRM  # after freeze
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import sys
from pathlib import Path

import numpy as np
import polars as pl
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    SEED_PSEUDO_DAILY,
    SEED_PSEUDO_FUND,
    adjudicate_i2_survival,
    day_clustered_ci,
    mde_curve,
    out_dir,
    paired_day_contrast,
    realise_universe,
    write_json,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.sigbar.fences import (  # noqa: E402
    assert_frozen_inputs,
    band_window,
    load_bars,
    repo_root,
)
from xen.sigbar.sessions import (  # noqa: E402
    CANDIDATE_ANCHORS,
    IB_LENGTHS,
    N_PSEUDO,
    anchor_table,
    assert_no_fixed_points,
    pseudo_offsets,
    pseudo_spec,
    session_breaks,
)

#: Pre-declared liquid set for the mandatory per-instrument spot-check
#: (checkpoint-014 §4, adherence resolution 2). n = 3 <= 5.
SPOT_CHECK = ("BTCUSDT", "ETHUSDT", "SOLUSDT")

#: Planted-effect grid for the MDE curve, in CONTRAST (E) units (AMENDMENT-5).
#: The equivalent post-break drift plant is half each value.
MDE_GRID = [0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.75, 1.00]

#: The only bar columns the race reads. ``session_breaks`` touches OpenTime,
#: High, Low and Close and nothing else, so the remaining staging columns are
#: dead weight carried through every join and group-by. Projecting here halves
#: the per-call cost and is output-identical (verified frame-equal).
RACE_COLUMNS = ("OpenTime", "High", "Low", "Close")

#: Anchor tables are symbol-independent, so building one per (symbol, cell) —
#: which is what the naive loop did ~79,000 times — is pure waste. Keyed on the
#: SPEC, not on ``anchor_id``: two candidate anchors' control ensembles reuse the
#: same pseudo ids (``PSEUDO-1x-00``) at different offsets, so an id-keyed cache
#: would silently hand one anchor's controls to another.
_ANCHOR_CACHE: dict[tuple, pl.DataFrame] = {}


def _anchors_for(spec, band: str) -> pl.DataFrame:
    key = (spec, band)
    tbl = _ANCHOR_CACHE.get(key)
    if tbl is None:
        start, end = band_window(band)
        tbl = anchor_table(spec, start, end)
        _ANCHOR_CACHE[key] = tbl
    return tbl


def _sessions_for(bars: pl.DataFrame, spec, ib_minutes: int, band: str, *, ib_shift: int = 0) -> pl.DataFrame:
    s = session_breaks(bars, _anchors_for(spec, band), ib_minutes, ib_shift=ib_shift)
    if s.height == 0:
        return s
    return s.with_columns(pl.col("anchor_ts").dt.truncate("1d").alias("day"))


def _restrict_to_members(sessions: pl.DataFrame, member_days: pl.DataFrame) -> pl.DataFrame:
    """Keep only sessions on days this symbol was in the online top-20 panel."""
    if sessions.height == 0:
        return sessions
    return sessions.join(member_days, on="day", how="semi")


def symbol_frames(
    bars: pl.DataFrame,
    member_days: pl.DataFrame,
    spec,
    ib_minutes: int,
    band: str,
    controls: list,
    symbol: str,
    *,
    ib_shift: int = 0,
    want_control: bool = True,
) -> tuple[pl.DataFrame | None, pl.DataFrame | None, int]:
    """One symbol's contribution to a race cell: real rows, control rows, count.

    Only the columns the cell statistic consumes are carried forward
    (``day, asym, break_ts, symbol``); the session table's remaining columns are
    never read downstream, and dropping them is what makes the pooled frames
    small enough to ship between processes.

    ``want_control=False`` is used by the tripwire, whose control arm does not
    depend on ``ib_shift`` — the same control clocks at the same ``L`` produce
    the same rows, so they are built once and reused across the shifted arms
    rather than rebuilt three times.
    """
    r_full = _sessions_for(bars, spec, ib_minutes, band, ib_shift=ib_shift)
    # Incomplete count is a constant column on admitted rows (design §3.2 /
    # I-27). Summed across symbols so the cell record surfaces the total.
    n_incomplete = 0
    if r_full.height and "n_incomplete_sessions" in r_full.columns:
        n_incomplete = int(r_full["n_incomplete_sessions"][0])
    r = _restrict_to_members(r_full, member_days)
    real = (
        r.select("day", "asym", "break_ts").with_columns(pl.lit(symbol).alias("symbol"))
        if r.height
        else None
    )
    ctrl_parts = []
    if want_control:
        for cspec in controls:
            c = _restrict_to_members(_sessions_for(bars, cspec, ib_minutes, band), member_days)
            if c.height:
                ctrl_parts.append(
                    c.select("day", "asym").with_columns(
                        pl.lit(symbol).alias("symbol"), pl.lit(cspec.anchor_id).alias("clock")
                    )
                )
    ctrl = pl.concat(ctrl_parts, how="vertical") if ctrl_parts else None
    return real, ctrl, n_incomplete


def finalise_cell(
    real_frames: list[pl.DataFrame],
    ctrl_frames: list[pl.DataFrame],
    *,
    n_controls: int,
    n_incomplete_sessions_band_total: int,
) -> dict:
    """One race cell: real arm, pooled control arm, contrast, stability, power."""
    if not real_frames or not ctrl_frames:
        return {
            "n_real": 0,
            "n_control": 0,
            "unpowered": True,
            "n_incomplete_sessions_band_total": n_incomplete_sessions_band_total,
        }

    real = pl.concat(real_frames, how="vertical")
    ctrl = pl.concat(ctrl_frames, how="vertical")
    contrast, days = paired_day_contrast(real, ctrl, "asym")
    ci = day_clustered_ci(contrast)

    # Stability: sign of the contrast across chronological thirds and across
    # per-symbol strata. Reported as a layer; nothing is dropped on it.
    thirds = []
    if len(contrast) >= 6:
        for k, chunk in enumerate(np.array_split(contrast, 3)):
            thirds.append({"third": k + 1, "n_days": len(chunk), "median": float(np.median(chunk))})
    per_symbol = []
    for sym in sorted(real["symbol"].unique().to_list()):
        rs = real.filter(pl.col("symbol") == sym)
        cs = ctrl.filter(pl.col("symbol") == sym)
        v, _ = paired_day_contrast(rs, cs, "asym")
        if len(v):
            per_symbol.append(
                {"symbol": sym, "n_days": len(v), "median_contrast": float(np.median(v))}
            )

    n_break = real.filter(pl.col("break_ts").is_not_null()).height
    real_med = real["asym"].drop_nulls().median()
    ctrl_med = ctrl["asym"].drop_nulls().median()
    return {
        "n_real_sessions": real.height,
        "n_real_with_break": n_break,
        "break_rate": n_break / real.height if real.height else None,
        "n_control_sessions": ctrl.height,
        "n_control_clocks": n_controls,
        "n_days_paired": len(days),
        # Counted BEFORE the membership restriction, so it spans the whole band
        # for every panel symbol and is NOT the incomplete count of the sessions
        # reported beside it. Named accordingly (QA run 5, I-39).
        "n_incomplete_sessions_band_total": n_incomplete_sessions_band_total,
        "contrast_median": float(np.median(contrast)) if len(contrast) else None,
        "contrast_ci": ci,
        # CALIBRATION_ONLY — absolute arm levels. Not an edge claim; present so
        # the contrast can be audited, barred from any headline (design.md §0).
        # Explicit ``is None`` tests, never truthiness: a median of exactly 0.0 is
        # a measured level, and `x or nan` reported it as missing (QA run 5, I-44).
        "CALIBRATION_ONLY": {
            "note": "NOT_AN_EDGE_CLAIM — absolute arm levels, for audit of the contrast only",
            "asym_real_median": float(real_med) if real_med is not None else None,
            "asym_control_median": float(ctrl_med) if ctrl_med is not None else None,
            "collapse_fraction": (
                float(ctrl_med / real_med)
                if real_med is not None and ctrl_med is not None and real_med != 0
                else None
            ),
        },
        "stability": {"thirds": thirds, "per_symbol": per_symbol,
                      "frac_symbols_positive": (
                          sum(1 for p in per_symbol if p["median_contrast"] > 0) / len(per_symbol)
                          if per_symbol else None)},
        "power": mde_curve(contrast, MDE_GRID),
    }


def run_cell(
    bars_by_symbol: dict[str, pl.DataFrame],
    members_by_symbol: dict[str, pl.DataFrame],
    spec,
    ib_minutes: int,
    band: str,
    *,
    controls: list,
    ib_shift: int = 0,
) -> dict:
    """Serial single-process race cell (used by the per-instrument spot-check)."""
    real_frames, ctrl_frames = [], []
    n_incomplete_sessions_band_total = 0
    for sym, bars in bars_by_symbol.items():
        md = members_by_symbol.get(sym)
        if md is None or md.height == 0:
            continue
        real, ctrl, n_inc = symbol_frames(
            bars, md, spec, ib_minutes, band, controls, sym, ib_shift=ib_shift
        )
        n_incomplete_sessions_band_total += n_inc
        if real is not None:
            real_frames.append(real)
        if ctrl is not None:
            ctrl_frames.append(ctrl)
    return finalise_cell(
        real_frames, ctrl_frames,
        n_controls=len(controls),
        n_incomplete_sessions_band_total=n_incomplete_sessions_band_total,
    )


# ---------------------------------------------------------------------------
# Symbol-parallel execution
#
# Symbols are independent by construction — a cell pools them only after every
# session row exists — so the per-symbol work is distributed across processes.
# Nothing about the estimand changes: workers run the same ``symbol_frames`` on
# the same fenced bars, results are reassembled in sorted-symbol order (the
# order the serial loop produced), and every cell statistic is an order-free
# aggregate (median / min / max / count). Set ``--workers 1`` to reproduce the
# single-process path exactly.
# ---------------------------------------------------------------------------

_WORKER: dict = {}


def _init_worker(band: str, membership: pl.DataFrame, controls_by_anchor: dict) -> None:
    _WORKER["band"] = band
    _WORKER["root"] = repo_root()
    _WORKER["controls"] = controls_by_anchor
    _WORKER["members"] = {
        s: membership.filter(pl.col("symbol") == s).select("day").unique()
        for s in membership["symbol"].unique().to_list()
    }
    _WORKER["bars"] = (None, None)


def _worker_bars(symbol: str) -> pl.DataFrame:
    """This worker's fenced, projected bars, cached one symbol deep.

    Tasks are dispatched symbol-major in chunks of one symbol's whole job list,
    so a one-deep cache means each symbol's parquet is read exactly once.
    """
    cached_sym, cached = _WORKER["bars"]
    if cached_sym == symbol:
        return cached
    bars = (
        load_bars(symbol, _WORKER["band"], root=_WORKER["root"])
        .select(RACE_COLUMNS)
        .with_columns(pl.col("OpenTime").set_sorted())
    )
    _WORKER["bars"] = (symbol, bars)
    return bars


def _worker_job(task: tuple) -> tuple:
    symbol, anchor_id, ib_minutes, ib_shift, want_control = task
    key = (anchor_id, ib_minutes, ib_shift)
    md = _WORKER["members"].get(symbol)
    if md is None or md.height == 0:
        return key, None, None, 0
    spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == anchor_id)
    real, ctrl, n_inc = symbol_frames(
        _worker_bars(symbol), md, spec, ib_minutes, _WORKER["band"],
        _WORKER["controls"][anchor_id]["specs"], symbol,
        ib_shift=ib_shift, want_control=want_control,
    )
    return key, real, ctrl, n_inc


def run_jobs(
    symbols: list[str],
    jobs: list[tuple],
    band: str,
    membership: pl.DataFrame,
    controls_by_anchor: dict,
    *,
    workers: int,
    desc: str,
) -> dict:
    """Run ``jobs`` (anchor, L, ib_shift, want_control) over every symbol.

    Returns ``{(anchor_id, L, ib_shift): {real, ctrl, n_incomplete}}`` with the
    per-symbol frames appended in sorted-symbol order.
    """
    tasks = [(s, a, L, sh, wc) for s in symbols for (a, L, sh, wc) in jobs]
    acc = {
        (a, L, sh): {"real": [], "ctrl": [], "n_incomplete": 0} for (a, L, sh, _wc) in jobs
    }
    if workers == 1:
        _init_worker(band, membership, controls_by_anchor)
        results = (_worker_job(t) for t in tasks)
        ctx = None
    else:
        # Each worker re-imports polars; pinning it to one thread stops N
        # processes from each spawning a full thread pool. Aggregations here are
        # order-free, so thread count cannot move a number.
        os.environ["POLARS_MAX_THREADS"] = "1"
        ctx = cf.ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(band, membership, controls_by_anchor),
        )
        results = ctx.map(_worker_job, tasks, chunksize=len(jobs))
    try:
        for key, real, ctrl, n_inc in tqdm(results, total=len(tasks), desc=desc):
            slot = acc[key]
            slot["n_incomplete"] += n_inc
            if real is not None:
                slot["real"].append(real)
            if ctrl is not None:
                slot["ctrl"].append(ctrl)
    finally:
        if ctx is not None:
            ctx.shutdown()
    return acc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--band", default="DESIGN", choices=["DESIGN", "CONFIRM"])
    ap.add_argument("--limit", type=int, default=None, help="smoke: cap staging files scanned")
    ap.add_argument(
        "--no-spot-check",
        action="store_true",
        help="skip the per-instrument spot-check (CONFIRM only; DESIGN always runs it)",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 1,
        help="symbol-parallel worker processes; --workers 1 runs the single-process path",
    )
    args = ap.parse_args()

    frozen = assert_frozen_inputs()
    root = repo_root()

    if args.band == "CONFIRM" and not (out_dir() / "anchor_freeze.json").exists():
        raise RuntimeError(
            "CONFIRM path invoked before results/anchor_freeze.json exists — the CONFIRM bank "
            "stays untouched until the DESIGN winner is frozen (checkpoint-014 §5)"
        )

    membership, recon = realise_universe(args.band, limit=args.limit)
    # Band-suffixed: one shared filename meant the CONFIRM run silently replaced
    # the DESIGN panel the pin cites (QA run 6, I-46).
    write_json(f"universe_reconciliation_{args.band}.json", {"reconciliation": recon})
    membership.write_parquet(out_dir() / f"universe_membership_{args.band}.parquet")

    symbols = sorted(membership["symbol"].unique().to_list())
    members_by_symbol = {
        s: membership.filter(pl.col("symbol") == s).select("day").unique() for s in symbols
    }

    # I-22: freeze_and_pin reads this and refuses a smoke-scale freeze.
    # ``workers`` is recorded so the artifact fully describes the run that made it
    # (QA run 5, I-43); it cannot move a number — every cell statistic is an
    # order-free aggregate — but an undescribed run is not reproducible on paper.
    universe_scale = {
        "limit": args.limit,
        "workers": args.workers,
        "n_symbols_selected": int(recon.get("n_distinct_symbols_selected") or 0),
        "n_days": int(recon.get("n_days") or 0),
    }

    # Control clocks: one stratified set per (anchor, shape). What actually keeps
    # two anchors from sharing an ensemble is `feasible_offsets`, which differs per
    # anchor because the exclusion zone is scoped to the anchor under test
    # (AMENDMENT-1) — NOT the seed: `SEED_PSEUDO_FUND == SEED_PSEUDO_DAILY + 2`, so
    # `+ i` makes A-FUND and A-EUOPEN collide on 20180104 (QA run 5, I-42). The
    # seeds are frozen and regenerable; they are not re-picked after seeing results.
    controls_by_anchor = {}
    for i, spec in enumerate(CANDIDATE_ANCHORS):
        shape = spec.sessions_per_day
        seed = (SEED_PSEUDO_FUND if shape == 3 else SEED_PSEUDO_DAILY) + i
        offs = pseudo_offsets(spec.anchor_id, shape, N_PSEUDO, seed)
        assert_no_fixed_points(spec.anchor_id, offs, shape)
        controls_by_anchor[spec.anchor_id] = {
            "seed": seed,
            "offsets": offs,
            "specs": [pseudo_spec(shape, o, j) for j, o in enumerate(offs)],
        }

    main_jobs = [
        (spec.anchor_id, L, 0, True) for spec in CANDIDATE_ANCHORS for L in IB_LENGTHS
    ]
    acc = run_jobs(
        symbols, main_jobs, args.band, membership, controls_by_anchor,
        workers=args.workers, desc="race cells",
    )

    cells = []
    for spec in CANDIDATE_ANCHORS:
        for L in IB_LENGTHS:
            slot = acc[(spec.anchor_id, L, 0)]
            res = finalise_cell(
                slot["real"], slot["ctrl"],
                n_controls=len(controls_by_anchor[spec.anchor_id]["specs"]),
                n_incomplete_sessions_band_total=slot["n_incomplete"],
            )
            cells.append({"anchor_id": spec.anchor_id, "ib_minutes": L, **res})
            print(
                f"  {spec.anchor_id:10s} L={L:3d}  contrast={res.get('contrast_median')}  "
                f"n_days={res.get('n_days_paired')}"
            )

    # Future-destroy tripwire on the leading cell (HARD — validity, not value).
    ranked = sorted(
        [c for c in cells if c.get("contrast_median") is not None],
        key=lambda c: c["contrast_median"], reverse=True,
    )
    tripwire = None
    if ranked:
        top = ranked[0]
        spec = next(s for s in CANDIDATE_ANCHORS if s.anchor_id == top["anchor_id"])
        ctrl_specs = controls_by_anchor[spec.anchor_id]["specs"]
        L = top["ib_minutes"]

        # The control arm does not depend on ib_shift — same clocks, same L, same
        # bars — so it is built once with the unshifted arm and reused by the
        # shifted arms rather than rebuilt for each.
        tw_acc = run_jobs(
            symbols,
            [
                (spec.anchor_id, L, 0, True),
                (spec.anchor_id, L, 1, False),
                (spec.anchor_id, L, 2, False),
            ],
            args.band, membership, controls_by_anchor,
            workers=args.workers, desc="tripwire arms",
        )
        tw_ctrl_frames = tw_acc[(spec.anchor_id, L, 0)]["ctrl"]

        def _arm_day_contrast(ib_shift: int) -> tuple[float | None, np.ndarray, np.ndarray, dict]:
            """Paired day contrast for real arm at ib_shift vs the same controls."""
            slot = tw_acc[(spec.anchor_id, L, ib_shift)]
            cell = finalise_cell(
                slot["real"], tw_ctrl_frames,
                n_controls=len(ctrl_specs),
                n_incomplete_sessions_band_total=slot["n_incomplete"],
            )
            if not slot["real"] or not tw_ctrl_frames:
                return cell.get("contrast_median"), np.array([]), np.array([]), cell
            real = pl.concat(slot["real"])
            ctrl = pl.concat(tw_ctrl_frames)
            vals, days = paired_day_contrast(real, ctrl, "asym")
            return cell.get("contrast_median"), vals, days, cell

        def _day_corr(v_a: np.ndarray, d_a: np.ndarray, v_b: np.ndarray, d_b: np.ndarray) -> float:
            if len(v_a) == 0 or len(v_b) == 0:
                raise RuntimeError("empty day contrast series — cannot compute day_corr")
            a = pl.DataFrame({"day": d_a, "v": v_a})
            b = pl.DataFrame({"day": d_b, "v": v_b})
            both = a.join(b, on="day", how="inner", suffix="_s")
            if both.height < 5:
                raise RuntimeError(
                    f"only {both.height} common days for day_corr (need ≥5) — cannot adjudicate"
                )
            corr = float(np.corrcoef(both["v"].to_numpy(), both["v_s"].to_numpy())[0, 1])
            if not np.isfinite(corr):
                raise RuntimeError(f"day_corr is not finite ({corr})")
            return corr

        # Causal raw (shift 0) vs destroy (shift 1). Shift-1 series is reused as
        # the leak plant's "raw" so we do not rebuild it twice.
        raw, v0, d0, _raw_cell = _arm_day_contrast(0)
        sh, v1, d1, sh_cell = _arm_day_contrast(1)
        cf = (sh / raw) if raw not in (None, 0) and sh is not None else None
        day_corr = _day_corr(v0, d0, v1, d1)
        adj = adjudicate_i2_survival(
            contrast_raw=raw,
            contrast_shifted=sh,
            collapse_fraction=cf,
            day_contrast_correlation=day_corr,
        )

        # Positive control (I-34): force the "raw" arm to use future IB levels
        # (ib_shift=1) and destroy with a further shift (ib_shift=2). A rule with
        # bite must mark that plant as SURVIVES — freeze refuses if it does not.
        leak_raw, vl0, dl0 = sh, v1, d1
        leak_sh, vl1, dl1, _ = _arm_day_contrast(2)
        leak_cf = (
            (leak_sh / leak_raw)
            if leak_raw not in (None, 0) and leak_sh is not None
            else None
        )
        leak_day_corr = _day_corr(vl0, dl0, vl1, dl1)
        leak_adj = adjudicate_i2_survival(
            contrast_raw=leak_raw,
            contrast_shifted=leak_sh,
            collapse_fraction=leak_cf,
            day_contrast_correlation=leak_day_corr,
        )

        tripwire = {
            "class": "future_destroy",
            "adjudication_kind": "i2_survival",
            "enforcement": "HARD — SURVIVAL means the emission is invalid, never 'no effect'",
            "adjudication": (
                "SURVIVAL := (same-sign collapse_fraction with |cf| > 0.25) OR "
                "(|day_contrast_correlation| > 0.5). A large opposite-sign E_shift is the "
                "destroy's non-zero null (foreign IB → fake break → revert), not survival "
                "(QA run 2–3, I-29/I-34). Freeze re-derives from primitives."
            ),
            "cell": {"anchor_id": top["anchor_id"], "ib_minutes": L},
            "contrast_raw": raw,
            "contrast_shifted": sh,
            "collapse_fraction": cf,
            "day_contrast_correlation": day_corr,
            "same_sign_material": adj["same_sign_material"],
            "survives": adj["survives"],
            "shifted_ci": sh_cell.get("contrast_ci"),
            "CALIBRATION_ONLY_shift_arm": sh_cell.get("CALIBRATION_ONLY"),
            "positive_control": {
                "kind": "i2_leak_plant",
                "purpose": (
                    "raw arm deliberately uses next-session IB (ib_shift=1); destroy uses "
                    "ib_shift=2. Must SURVIVE under the same adjudicator, else the gate "
                    "has no bite (I-34)."
                ),
                "contrast_raw": leak_raw,
                "contrast_shifted": leak_sh,
                "collapse_fraction": leak_cf,
                "day_contrast_correlation": leak_day_corr,
                "same_sign_material": leak_adj["same_sign_material"],
                "survives": leak_adj["survives"],
            },
        }

    # Spot-check is MANDATORY on DESIGN (checkpoint-014 §4, adherence resolution 2).
    # freeze_anchor refuses a null table. CONFIRM may skip (--no-spot-check) because
    # the freeze already consumed the DESIGN table.
    run_spot = args.band == "DESIGN" or not args.no_spot_check
    spot = None
    if run_spot:
        spot = {}
        for sym in SPOT_CHECK:
            if sym not in members_by_symbol:
                spot[sym] = {"status": "NOT_IN_PANEL"}
                continue
            spot_bars = (
                load_bars(sym, args.band, root=root)
                .select(RACE_COLUMNS)
                .with_columns(pl.col("OpenTime").set_sorted())
            )
            rows = []
            for spec in CANDIDATE_ANCHORS:
                for L in IB_LENGTHS:
                    r = run_cell(
                        {sym: spot_bars}, {sym: members_by_symbol[sym]}, spec, L, args.band,
                        controls=controls_by_anchor[spec.anchor_id]["specs"],
                    )
                    rows.append(
                        {"anchor_id": spec.anchor_id, "ib_minutes": L,
                         "contrast_median": r.get("contrast_median"),
                         "n_days_paired": r.get("n_days_paired")}
                    )
            spot[sym] = {"cells": rows}

    write_json(
        f"hyp_i2_anchor_race_{args.band}.json",
        {
            "hypothesis": "HYP-I2",
            "phase": "source Appendix B Phase 1 — anchor selection",
            "band": args.band,
            "band_label": (
                "TRAIN_INTERNAL_CONFIRMATION: not out-of-sample in the programme's sense"
                if args.band == "CONFIRM" else "DESIGN — all tuning and selection"
            ),
            "frozen_inputs": {
                "baselines_sha256": frozen.baselines_sha256,
                "column_pins_sha256": frozen.column_pins_sha256,
                "fence_manifest_sha256": frozen.fence_manifest_sha256,
            },
            "multiplicity": {
                "k_cells": len(cells),
                "declared": "4 anchors x 3 IB lengths, pre-registered; no cell added or "
                            "re-parameterised after any result was seen",
            },
            "break_rule_at_phase1": "FIRST_CLOSE_BEYOND (pre-A6, provisional, race-internal only)",
            "controls": {
                a: {"seed": c["seed"], "n_clocks": len(c["offsets"]), "offsets": c["offsets"],
                    "fixed_points": 0}
                for a, c in controls_by_anchor.items()
            },
            "universe": recon["rule"],
            "universe_scale": universe_scale,
            "cells": cells,
            "ranked": [
                {"anchor_id": c["anchor_id"], "ib_minutes": c["ib_minutes"],
                 "contrast_median": c["contrast_median"]} for c in ranked
            ],
            "tripwire_future_shift": tripwire,
            "spot_check": spot,
            "scope": "STAGE I — a parameter, never evidence that anything works",
        },
    )
    print(f"\nwrote {out_dir() / f'hyp_i2_anchor_race_{args.band}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
