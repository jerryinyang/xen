"""Arm C — the SPDR-014 residue (zone / mispricing event / post-event residual).

Residue inventory (design §2, complete — nothing narrowed):

  C1  the residual object itself      0 of 927 powered cells; MDE 20 / 172 / 796 bps vs a <=10 floor
  C2  shock-conditioned MOMO          ``|r_t|`` top decile on the decision bar, INSIDE the grid
  C3  ordered ``last_k`` L->H flip    and the ``LHL`` mirror, K in {1,2,3}, INSIDE the grid
  C4  E-TOUCH / E-CLOSE asymmetry     breach-type split of the same residual
  C5  magnitude scaling               ``mag_high`` / ``shock`` / vol-tercile lift MAGNITUDE
  C6  z / h dose-response             low-z + long-hold vs high-z
  C7  DESIGN->CONFIRM sign flip       12/17 symbols reversed; pooled +11.3 -> -4.3
  C8  pooled rate lean                ``p_momo`` 0.478 pooled vs the 18-vs-7 per-cell count
  C9  ``DA-STRADDLE``                 CHARACTERISATION ONLY (SoT §0 operator exception)

**C2 / C3 / C4 are measured INSIDE the event grammar, as registered.** No conditioner is lifted
out of its event to reach power — that is an estimand substitution and it is refused (§5, §13).
A cell that cannot reach its MDE in that nested form is reported ``NOT_RESOLVABLE`` with the
shortfall quantified, which is itself the answer to the 017 question.

C9 carries no strategy framing, no policy and no graduation path (design §13, SoT §0).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import cells
import parents
from config import BOOT_RESAMPLES

PANEL = "post_event.parquet"
GROSS, NET, TS, EXIT_TS = "c_gross_bps", "c_net_bps", "entry_ts", "exit_ts"

#: the parent's own registered residual grid — C1
GRID_KEYS = ("symbol", "source", "z", "H", "event_type", "h", "band", "clock", "policy")

#: the conditioner splits, each applied INSIDE the grid above (C2-C6)
CONDITIONERS = {
    "C2": ("shock_flag",),
    "C3": ("last_k_state_1", "last_k_state_2", "last_k_state_3"),
    "C4": ("event_type",),               # already a grid axis; split reported explicitly
    "C5": ("mag_high", "shock_flag", "vol_tercile"),
    "C6": ("z", "h"),                    # dose-response, read across the grid axes
}


def load_panel() -> pd.DataFrame:
    """The parent's post-event rows, with the gross/net pair made uniform across policies.

    SPDR-014 emitted ``r_h`` (the residual, signed by the breach side) for every row, but charged
    cost only on the money policies ``P-MOMO``/``P-MR`` — the ``P-NONE`` residual was a pure
    characterisation object with no money claim. §5.3 asks for gross AND net on every cell, so the
    net leg for ``P-NONE`` is built with **SPDR-014's own cost module** (``screen_code/costs.py``
    -> ``xen.evaluation`` fees + counted funding stamps + the 2.0 allowance). No accounting
    primitive is re-implemented here and no spread is charged (P-20 / L-36).
    """
    df = pd.read_parquet(parents.published("SPDR-014", PANEL))
    costs = parents.load("SPDR-014")["costs"]

    gross = np.array(df["r_h"].to_numpy(dtype=float), copy=True)
    money = df["policy"].isin(("P-MOMO", "P-MR")).to_numpy()
    gross[money] = df["gross_bps"].to_numpy(dtype=float)[money]
    df["c_gross_bps"] = gross

    net = df["partial_net_bps"].to_numpy(dtype=float).copy()
    need = ~money | ~np.isfinite(net)
    if need.any():
        ent = df["entry_ts"].to_numpy(dtype=np.int64)
        exi = df["exit_ts"].to_numpy(dtype=np.int64)
        # funding stamps depend only on the (entry, exit) pair — cache per distinct pair
        cache: dict[tuple[int, int], float] = {}
        vals = np.empty(int(need.sum()))
        for j, i in enumerate(np.where(need)[0]):
            k = (int(ent[i]), int(exi[i]))
            if k not in cache:
                cache[k] = costs.partial_net(0.0, k[0], k[1])["partial_net_bps"]
            vals[j] = gross[i] + cache[k]        # cache holds the negative cost total
        net[need] = vals
    df["c_net_bps"] = net
    return df


def load_straddle() -> pd.DataFrame:
    return pd.read_parquet(parents.published("SPDR-014", "straddle.parquet"))


def _clock_minutes(clock: str) -> int:
    return int(parents.const("SPDR-014", "CLOCKS")[clock]["minutes"])


def _score(g: pd.DataFrame, *, item: str, key: dict, levers_exhausted: bool = False,
           full: bool = False, n_boot: int = BOOT_RESAMPLES, sigma_bps=None) -> dict:
    h = int(key.get("h")) if key.get("h") is not None and np.isfinite(float(key.get("h", np.nan))) \
        else None
    clock = key.get("clock", "H1")
    return cells.score_signed_cell(
        g, arm="C", item=item, key=key, gross_col=GROSS, net_col=NET, ts_col=TS,
        exit_ts_col=EXIT_TS, h=h, clock_minutes=_clock_minutes(clock) if clock in ("H1", "H4")
        else None, levers_exhausted=levers_exhausted, full=full, n_boot=n_boot,
        sigma_bps=sigma_bps)


def sigma_normalised(df: pd.DataFrame, unit_pin: dict) -> pd.DataFrame:
    pooled = unit_pin.get("pooled_median_sigma_bps")
    per = unit_pin.get("per_symbol", {})
    if not pooled:
        return df
    scale = df["symbol"].map(
        lambda s: (pooled / per.get(s, {}).get("median_sigma_bps"))
        if per.get(s, {}).get("median_sigma_bps") else np.nan).to_numpy(dtype=float)
    out = df.copy()
    out[GROSS] = out[GROSS].to_numpy(dtype=float) * scale
    out[NET] = out[NET].to_numpy(dtype=float) * scale
    return out.loc[np.isfinite(scale)]


def tasks(unit_pin: dict) -> list[dict]:
    """Work units. Each stage is a disjoint slice of the cell grid, so the union of the units is
    identical to a sequential run — parallelism partitions work, it never changes a cell."""
    syms = sorted(load_panel()["symbol"].unique().tolist())
    t = [{"arm": "C", "stage": "c1_symbol", "symbol": s} for s in syms]
    for src in sorted(load_panel()["source"].unique().tolist()):
        t.append({"arm": "C", "stage": "c1_pooled", "source": src})
    for item, conds in CONDITIONERS.items():
        if item in ("C4", "C6"):
            continue
        for cond in conds:
            for band in ("TRAIN", "DESIGN", "CONFIRM"):
                t.append({"arm": "C", "stage": "cond", "item": item, "cond": cond, "band": band})
    t += [{"arm": "C", "stage": "c4"}, {"arm": "C", "stage": "c6"},
          {"arm": "C", "stage": "c7"}, {"arm": "C", "stage": "c8"}, {"arm": "C", "stage": "c9"}]
    return t


def run_task(task: dict, unit_pin: dict, *, n_boot: int = BOOT_RESAMPLES) -> list[dict]:
    """Dispatch one work unit. ``c7`` needs the C1 per-symbol records, so it recomputes them."""
    stage = task["stage"]
    if stage == "c9":
        return straddle_rows()
    panel = load_panel()
    pooled_sigma = unit_pin.get("pooled_median_sigma_bps")

    if stage == "c1_symbol":
        sub = panel[panel.symbol == task["symbol"]]
        return [_score(g, item="C1",
                       key={**dict(zip(GRID_KEYS, key)), "basis": "per_symbol"}, n_boot=n_boot)
                for key, g in sub.groupby(list(GRID_KEYS), sort=True, observed=True)]

    normed = sigma_normalised(panel, unit_pin)
    if stage == "c1_pooled":
        src = task.get("source")
        if src is not None:
            panel = panel[panel.source == src]
            normed = normed[normed.source == src]
        return _c1_pooled(panel, normed, pooled_sigma, n_boot=n_boot)
    if stage == "cond":
        return _conditioner_cells(panel, normed, pooled_sigma, task["item"], task["cond"],
                                  task["band"], n_boot=n_boot)
    if stage == "c4":
        return _c4(normed, pooled_sigma, n_boot=n_boot)
    if stage == "c6":
        return _c6(normed, pooled_sigma, n_boot=n_boot)
    if stage == "c7":
        c1 = [_score(g, item="C1", key={**dict(zip(GRID_KEYS, key)), "basis": "per_symbol"},
                     n_boot=n_boot)
              for key, g in panel.groupby(list(GRID_KEYS), sort=True, observed=True)]
        return sign_flip_rows(c1)
    if stage == "c8":
        return rate_lean_rows(panel)
    raise KeyError(stage)


def _c1_pooled(panel, normed, pooled_sigma, *, n_boot) -> list[dict]:
    out = []
    pool_keys = ("source", "z", "H", "event_type", "h", "clock", "policy")
    for band_name, src_raw, src_norm in (
            ("DESIGN", panel[panel.band == "DESIGN"], normed[normed.band == "DESIGN"]),
            ("CONFIRM", panel[panel.band == "CONFIRM"], normed[normed.band == "CONFIRM"]),
            ("TRAIN", panel, normed)):
        for basis, frame in (("pooled_raw", src_raw), ("pooled_sigma_normalised", src_norm)):
            exhausted = (band_name == "TRAIN" and basis == "pooled_sigma_normalised")
            for key, g in frame.groupby(list(pool_keys), sort=True, observed=True):
                k = dict(zip(pool_keys, key))
                out.append(_score(g, item="C1", key={**k, "symbol": "__POOLED__",
                                                     "band": band_name, "basis": basis},
                                  levers_exhausted=exhausted, full=exhausted, n_boot=n_boot,
                                  sigma_bps=pooled_sigma))
    return out


def _conditioner_cells(panel, normed, pooled_sigma, item, cond, band, *, n_boot) -> list[dict]:
    """A conditioner is an EXTRA split of the same nested cell — the event grid axes stay on the
    key. This is what "no un-nesting" means in code (design §2, §5, §13)."""
    nested = ("source", "z", "H", "event_type", "h", "clock", "policy")
    if cond not in panel.columns:
        return [{"arm": "C", "residue_item": item, "conditioner": cond, "band": band,
                 "status": "COLUMN_ABSENT_IN_PARENT_PANEL",
                 "note": "reported, not skipped (design §1.1)"}]
    frame = normed if band == "TRAIN" else normed[normed.band == band]
    out = []
    for key, g in frame.groupby([*nested, cond], sort=True, observed=True):
        k = dict(zip([*nested, "conditioner_value"], key))
        out.append(_score(g, item=item,
                          key={**k, "conditioner": cond, "symbol": "__POOLED__",
                               "band": band, "basis": "pooled_sigma_normalised"},
                          levers_exhausted=(band == "TRAIN"), n_boot=n_boot,
                          sigma_bps=pooled_sigma))
    return out


def _c4(normed, pooled_sigma, *, n_boot) -> list[dict]:
    keys = ("source", "z", "H", "h", "clock", "policy", "event_type")
    return [_score(g, item="C4",
                   key={**dict(zip(keys, key)), "symbol": "__POOLED__", "band": "TRAIN",
                        "basis": "pooled_sigma_normalised"},
                   levers_exhausted=True, n_boot=n_boot, sigma_bps=pooled_sigma)
            for key, g in normed.groupby(list(keys), sort=True, observed=True)]


def _c6(normed, pooled_sigma, *, n_boot) -> list[dict]:
    keys = ("source", "event_type", "clock", "policy", "z", "h")
    return [_score(g, item="C6",
                   key={**dict(zip(keys, key)), "symbol": "__POOLED__", "band": "TRAIN",
                        "basis": "dose_response"},
                   levers_exhausted=True, n_boot=n_boot, sigma_bps=pooled_sigma)
            for key, g in normed.groupby(list(keys), sort=True, observed=True)]


def run(unit_pin: dict, *, n_boot: int = BOOT_RESAMPLES) -> list[dict]:
    panel = load_panel()
    pooled_sigma = unit_pin.get("pooled_median_sigma_bps")
    normed = sigma_normalised(panel, unit_pin)
    out: list[dict] = []

    # --- C1: the parent's own residual grid, re-scored per symbol ---------------------------
    c1: list[dict] = []
    for key, g in panel.groupby(list(GRID_KEYS), sort=True, observed=True):
        k = dict(zip(GRID_KEYS, key))
        c1.append(_score(g, item="C1", key={**k, "basis": "per_symbol"}, n_boot=n_boot))
    out.extend(c1)

    # --- C1 under levers 1-3: pooled across symbols, per band and on the full TRAIN span ----
    pool_keys = ("source", "z", "H", "event_type", "h", "clock", "policy")
    for band_name, src_raw, src_norm in (
            ("DESIGN", panel[panel.band == "DESIGN"], normed[normed.band == "DESIGN"]),
            ("CONFIRM", panel[panel.band == "CONFIRM"], normed[normed.band == "CONFIRM"]),
            ("TRAIN", panel, normed)):
        for basis, frame in (("pooled_raw", src_raw), ("pooled_sigma_normalised", src_norm)):
            exhausted = (band_name == "TRAIN" and basis == "pooled_sigma_normalised")
            for key, g in frame.groupby(list(pool_keys), sort=True, observed=True):
                k = dict(zip(pool_keys, key))
                out.append(_score(g, item="C1", key={**k, "symbol": "__POOLED__",
                                                     "band": band_name, "basis": basis},
                                  levers_exhausted=exhausted, full=exhausted, n_boot=n_boot,
                                  sigma_bps=pooled_sigma))

    # --- C2-C5: conditioners INSIDE the event grammar ---------------------------------------
    # The conditioner is an EXTRA split of the same nested cell; the event grid axes stay on the
    # key. This is what "no un-nesting" means in code.
    nested = ("source", "z", "H", "event_type", "h", "clock", "policy")
    for item, conds in CONDITIONERS.items():
        if item in ("C4", "C6"):
            continue        # C4/C6 are grid axes already — handled explicitly below
        for cond in conds:
            if cond not in panel.columns:
                out.append({"arm": "C", "residue_item": item, "conditioner": cond,
                            "status": "COLUMN_ABSENT_IN_PARENT_PANEL",
                            "note": "reported, not skipped (design §1.1)"})
                continue
            for band_name, frame in (("TRAIN", normed), ("DESIGN", normed[normed.band == "DESIGN"]),
                                     ("CONFIRM", normed[normed.band == "CONFIRM"])):
                exhausted = band_name == "TRAIN"
                for key, g in frame.groupby([*nested, cond], sort=True, observed=True):
                    k = dict(zip([*nested, "conditioner_value"], key))
                    out.append(_score(
                        g, item=item,
                        key={**k, "conditioner": cond, "symbol": "__POOLED__",
                             "band": band_name, "basis": "pooled_sigma_normalised"},
                        levers_exhausted=exhausted, n_boot=n_boot, sigma_bps=pooled_sigma))

    # --- C4: E-TOUCH / E-CLOSE asymmetry, stated as its own contrast ------------------------
    for key, g in normed.groupby(["source", "z", "H", "h", "clock", "policy", "event_type"],
                                 sort=True, observed=True):
        k = dict(zip(("source", "z", "H", "h", "clock", "policy", "event_type"), key))
        out.append(_score(g, item="C4", key={**k, "symbol": "__POOLED__", "band": "TRAIN",
                                             "basis": "pooled_sigma_normalised"},
                          levers_exhausted=True, n_boot=n_boot, sigma_bps=pooled_sigma))

    # --- C6: z / h dose-response ------------------------------------------------------------
    for key, g in normed.groupby(["source", "event_type", "clock", "policy", "z", "h"],
                                 sort=True, observed=True):
        k = dict(zip(("source", "event_type", "clock", "policy", "z", "h"), key))
        out.append(_score(g, item="C6", key={**k, "symbol": "__POOLED__", "band": "TRAIN",
                                             "basis": "dose_response"},
                          levers_exhausted=True, n_boot=n_boot, sigma_bps=pooled_sigma))

    # --- C7: DESIGN -> CONFIRM sign flip, per symbol, as a measured contrast -----------------
    out.extend(sign_flip_rows(c1))

    # --- C8: the pooled rate lean vs the per-cell count --------------------------------------
    out.extend(rate_lean_rows(panel))

    # --- C9: DA-STRADDLE — CHARACTERISATION ONLY ---------------------------------------------
    out.extend(straddle_rows())
    return out


def sign_flip_rows(c1_records: list[dict]) -> list[dict]:
    """C7 — is the 12/17 DESIGN->CONFIRM reversal instability, or noise at the realised n?

    Reported as: each band's mean with its block CI, the difference, and whether the two CIs
    overlap. A sign flip whose two CIs overlap is not evidence of instability — it is the same
    unresolved cell twice.

    Built from the C1 per-symbol records so both bands are scored exactly once, with the same
    uncertainty treatment the rest of the arm uses.
    """
    rows = []
    keys = ("symbol", "source", "z", "H", "event_type", "h", "clock", "policy")
    by_key: dict[tuple, dict] = {}
    for rec in c1_records:
        if rec.get("band") not in ("DESIGN", "CONFIRM"):
            continue
        by_key.setdefault(tuple(rec.get(k) for k in keys), {})[rec["band"]] = rec

    for key, pair in sorted(by_key.items(), key=lambda kv: [str(x) for x in kv[0]]):
        kd, kc = pair.get("DESIGN"), pair.get("CONFIRM")
        if kd is None or kc is None:
            continue
        def _f(rec: dict, k: str) -> float:
            v = rec.get(k)
            return float(v) if isinstance(v, (int, float, np.floating)) else float("nan")

        md, mc = _f(kd, "net_mean"), _f(kc, "net_mean")
        lo_d, hi_d = _f(kd, "net_mean_ci_low"), _f(kd, "net_mean_ci_high")
        lo_c, hi_c = _f(kc, "net_mean_ci_low"), _f(kc, "net_mean_ci_high")
        overlap = (bool(np.isfinite([lo_d, hi_d, lo_c, hi_c]).all())
                   and not (hi_d < lo_c or hi_c < lo_d))
        rows.append({
            "arm": "C", "residue_item": "C7", **dict(zip(keys, key)), "basis": "sign_flip",
            "design_mean_bps": md, "design_ci": [lo_d, hi_d], "design_n": kd.get("n"),
            "confirm_mean_bps": mc, "confirm_ci": [lo_c, hi_c], "confirm_n": kc.get("n"),
            "sign_flipped": bool(np.isfinite(md) and np.isfinite(mc) and np.sign(md) != np.sign(mc)),
            "band_cis_overlap": bool(overlap),
            "delta_bps": float(mc - md) if np.isfinite([md, mc]).all() else float("nan"),
            "design_block_mde_bps": kd.get("net_block_mde_mean_bps"),
            "confirm_block_mde_bps": kc.get("net_block_mde_mean_bps"),
            "interpretation": ("overlapping CIs mean the flip is not distinguishable from noise "
                               "at this n — a power statement, never a negative (B-5)"),
        })
    return rows


def rate_lean_rows(panel: pd.DataFrame) -> list[dict]:
    """C8 — the two weightings disagree (pooled ``p_momo`` 0.478 vs the 18-vs-7 per-cell count).

    Both weightings are emitted side by side with their own uncertainty, because the disagreement
    IS the open question: neither was powered in 017.
    """
    rows = []
    keys = ("source", "z", "H", "event_type", "h", "clock", "policy", "band")
    for key, g in panel.groupby(list(keys), sort=True, observed=True):
        lab = g["label"].to_numpy()
        momo = (lab == "MOMO").sum()
        mr = (lab == "MR").sum()
        n_signed = momo + mr
        per_sym = []
        for _, gs in g.groupby("symbol", observed=True):
            l2 = gs["label"].to_numpy()
            a, b = (l2 == "MOMO").sum(), (l2 == "MR").sum()
            if a + b:
                per_sym.append(a / (a + b))
        per_sym = np.asarray(per_sym, dtype=float)
        rows.append({
            "arm": "C", "residue_item": "C8", **dict(zip(keys, key)), "basis": "rate_lean",
            "p_momo_pooled_row_weighted": float(momo / n_signed) if n_signed else float("nan"),
            "p_momo_mean_of_per_symbol": float(per_sym.mean()) if per_sym.size else float("nan"),
            "n_symbols_momo_leaning": int((per_sym > 0.5).sum()),
            "n_symbols_mr_leaning": int((per_sym < 0.5).sum()),
            "n_symbols": int(per_sym.size),
            "n_signed_rows": int(n_signed), "n_flat_rows": int((lab == "FLAT").sum()),
            "note": ("row-weighted and symbol-weighted rates answer different questions; both are "
                     "reported because 017 powered neither"),
        })
    return rows


def straddle_rows() -> list[dict]:
    """C9 — ``DA-STRADDLE``, CHARACTERISATION ONLY.

    Operator exception to the direction-agnostic deferral (SoT §0). No strategy framing, no
    policy, no graduation path. The parent emitted this arm already aggregated, so what is added
    here is the power statement against the parent's own target, not a re-specification.
    """
    df = load_straddle()
    rows = []
    for _, r in df.iterrows():
        n = int(r.get("n_episodes", 0))
        rows.append({
            "arm": "C", "residue_item": "C9", "basis": "characterisation_only",
            "symbol": r.get("symbol"), "source": r.get("source"), "z": r.get("z"),
            "H": r.get("H"), "band": r.get("band"), "straddle_arm": r.get("arm"),
            "n": n,
            "mean_partial_net_bps": float(r.get("mean_partial_net", np.nan)),
            "median_partial_net_bps": float(r.get("median_partial_net", np.nan)),
            "at_parent_target_precision": bool(n >= 80),
            "target_rule": "SPDR-014 §8.1 n_events >= 80",
            "framing": "CHARACTERISATION ONLY — not a strategy branch, no policy, no graduation",
            "scope_note": ("direction-agnostic strategies are DEFERRED (SoT §0); this cell is a "
                           "measured payoff, nothing more"),
        })
    return rows
