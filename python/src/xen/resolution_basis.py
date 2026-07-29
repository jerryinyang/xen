"""Resolution basis: how finely a cell can resolve the payoff residual `log R`.

Why this module exists
----------------------
Design documents kept hand-computing required-sample tables and getting them wrong.
Three separate drafts of SPDR-019/020 quoted three different scaling constants, each
pairing a numerator and a denominator drawn from *different* populations, and a fourth
attempt mixed row counts across policy arms. Every one of those errors was arithmetic
typed into prose, where nothing could check it.

The fix is to make the derivation a function and the numbers an artifact. Designs state
the METHOD and pin the emitted JSON; they never type a resolution figure.

The quantity
------------
For a cell with `n` episodes, mean-MDE `block_mde_bps`, win rate `p` and mean loss `L`:

    mde_log = block_mde_bps / ((1 - p) * L)      # MDE expressed in log-residual units
    c       = mde_log * sqrt(n)                  # dimensionless, but reusable only
                                                 # under the same CI construction

`c` is flat across holding horizons -- `block_mde_bps` and `(1-p)*L` both rise with `h`
and cancel -- but it RISES with `n`, which is the block-dependence penalty. That rise is
the reason a single constant fitted on thin cells understates the requirement at scale.

`c` is only comparable across cells whose CIs were built the same way. It carries no
meaning if the block rule, block sweep or seed battery differ between the source emission
and the design reusing it, so `c_bands` records the source's rule and refuses to guess it.

Nothing here is a threshold. No function admits, excludes, labels or ranks a cell
(AMENDMENT-C7, INFR-016). `required_n` and `mde50` are descriptive conversions.
"""

from __future__ import annotations

import json
import hashlib
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

__all__ = [
    "DEFAULT_N_BANDS",
    "CellResolution",
    "c_per_cell",
    "c_bands",
    "build_expected_resolution",
    "required_n",
    "mde50",
    "write_basis",
    "write_expected_resolution",
]

# Band edges in episodes. Chosen to span the emitted range at roughly one decade per
# band; they partition cells for DISCLOSURE only and gate nothing.
DEFAULT_N_BANDS: tuple[float, ...] = (0.0, 100.0, 1_000.0, 5_000.0, 15_000.0, np.inf)


@dataclass(frozen=True)
class CellResolution:
    """Per-cell resolution terms, all measured -- none assumed."""

    n: float
    block_mde_bps: float
    p: float
    L: float
    mde_log: float
    c: float


def _terms(
    df: pd.DataFrame,
    *,
    n_col: str,
    mde_col: str,
    p_col: str,
    l_col: str,
) -> pd.DataFrame:
    missing = [c for c in (n_col, mde_col, p_col, l_col) if c not in df.columns]
    if missing:
        raise KeyError(f"resolution_basis: missing required columns {missing}")

    out = df.loc[:, [n_col, mde_col, p_col, l_col]].copy()
    out.columns = ["n", "block_mde_bps", "p", "L"]
    out = out.dropna()
    # (1-p)*L is the conversion denominator; it is undefined at p == 1 or L == 0, and a
    # cell with n <= 1 has no resolution to report. Dropping these is not a selection on
    # the outcome -- they are arithmetically undefined, and the count is returned so the
    # exclusion is visible rather than silent.
    denom = (1.0 - out["p"]) * out["L"]
    keep = (out["n"] > 1) & np.isfinite(denom) & (denom > 0) & (out["block_mde_bps"] > 0)
    out = out.loc[keep]
    denom = denom.loc[keep]
    out["mde_log"] = out["block_mde_bps"] / denom
    out["c"] = out["mde_log"] * np.sqrt(out["n"])
    return out


def c_per_cell(
    df: pd.DataFrame,
    *,
    n_col: str = "gross_n",
    mde_col: str = "gross_block_mde_mean_bps",
    p_col: str = "gross_p",
    l_col: str = "gross_L",
    keep: Sequence[str] = (),
) -> pd.DataFrame:
    """Return `mde_log` and `c` for every cell, alongside any `keep` columns.

    Emitting this per cell is what turns resolution from a forecast into a measurement:
    a run reports the `c` it actually achieved, so the next design reads it instead of
    re-deriving it by hand.
    """
    terms = _terms(df, n_col=n_col, mde_col=mde_col, p_col=p_col, l_col=l_col)
    if keep:
        extra = [c for c in keep if c in df.columns]
        terms = terms.join(df.loc[terms.index, extra])
    return terms


def c_bands(
    df: pd.DataFrame,
    *,
    source_ci_rule: str,
    bands: Iterable[float] = DEFAULT_N_BANDS,
    group_col: str | None = None,
    **cell_kwargs,
) -> pd.DataFrame:
    """Summarise `c` by sample-size band.

    `source_ci_rule` is mandatory and free-text: the block rule, block sweep and seed
    battery the SOURCE emission used to build its CIs. A `c` measured under a min/max
    envelope over a block sweep is not interchangeable with one measured at a single
    block length, and a design that reuses `c` under a weaker rule will understate its
    own uncertainty. Recording the rule is what makes that mismatch checkable.

    Returns per band: `cells`, `distinct_n`, `distinct_groups`, and the median `c`.
    `distinct_n` and `distinct_groups` exist because a band holding 26 rows that are
    really 8 repeated cells cannot support a "range across bases" claim -- the spread is
    then noise, and the counts make that visible instead of flattering.
    """
    terms = c_per_cell(df, **cell_kwargs)
    if group_col is not None and group_col in df.columns:
        terms = terms.join(df.loc[terms.index, [group_col]])

    edges = list(bands)
    labels = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        lo_s = f"{int(lo):,}" if lo else "0"
        hi_s = "inf" if np.isinf(hi) else f"{int(hi):,}"
        labels.append(f"{lo_s}-{hi_s}")
    terms["n_band"] = pd.cut(
        terms["n"], bins=edges, labels=labels, right=True, include_lowest=True
    )

    rows = []
    for band, sub in terms.groupby("n_band", observed=True):
        rows.append(
            {
                "n_band": str(band),
                "cells": int(len(sub)),
                "distinct_n": int(sub["n"].nunique()),
                "distinct_groups": (
                    int(sub[group_col].nunique()) if group_col in sub.columns else None
                ),
                "c_median": float(sub["c"].median()),
                "c_p25": float(sub["c"].quantile(0.25)),
                "c_p75": float(sub["c"].quantile(0.75)),
                "n_median": float(sub["n"].median()),
            }
        )
    out = pd.DataFrame(rows)
    out.attrs["source_ci_rule"] = source_ci_rule
    return out


def required_n(c: float, delta: float) -> float:
    """Episodes needed to resolve `delta` log units at constant `c`. Descriptive."""
    if delta <= 0:
        raise ValueError("resolution_basis: delta must be positive")
    return float((c / delta) ** 2)


def mde50(c: float, n: float) -> float:
    """Effect size resolvable at sample size `n` and constant `c`. Descriptive."""
    if n <= 0:
        raise ValueError("resolution_basis: n must be positive")
    return float(c / np.sqrt(n))


def _band_for_n(n: float, bands: Sequence[dict]) -> dict:
    for row in bands:
        lo_text, hi_text = row["n_band"].replace(",", "").split("-", maxsplit=1)
        lo = float(lo_text)
        hi = np.inf if hi_text == "inf" else float(hi_text)
        if lo < n <= hi or (lo == 0 and 0 <= n <= hi):
            return row
    raise ValueError(f"resolution_basis: no c band contains n={n}")


def build_expected_resolution(
    prior: dict,
    basis: dict,
    *,
    generated_at_utc: str,
    source_hashes: dict[str, str],
) -> dict:
    """Expand declared axes and attach only genuinely available parent priors.

    Missing parent cells remain explicit nulls. They are never imputed from a pooled
    row count or a neighbouring stratum.
    """
    grain = prior["grain"]
    axes = prior["declared_axes"]
    missing_axes = [name for name in grain if name not in axes]
    if missing_axes:
        raise KeyError(f"resolution_basis: missing declared axes {missing_axes}")

    known = {
        tuple(row[name] for name in grain): row
        for row in prior.get("known_parent_cells", [])
    }
    rows = []
    for values in itertools.product(*(axes[name] for name in grain)):
        row = dict(zip(grain, values, strict=True))
        parent = known.get(values)
        if parent is None:
            row.update(
                {
                    "prior_status": "UNKNOWN_NO_PARENT_SIGNED_ARM",
                    "expected_n": None,
                    "n_band": None,
                    "c_median": None,
                    "expected_mde50": None,
                }
            )
        else:
            n = float(parent["expected_n"])
            band = _band_for_n(n, basis["n_bands"])
            row.update(
                {
                    "prior_status": "KNOWN_PARENT_SIGNED_ARM",
                    "expected_n": int(n) if n.is_integer() else n,
                    "n_band": band["n_band"],
                    "c_median": band["c_median"],
                    "expected_mde50": mde50(float(band["c_median"]), n),
                }
            )
        rows.append(row)

    return {
        "artifact_version": 1,
        "generated_at_utc": generated_at_utc,
        "grain": grain,
        "provenance": (
            "Expanded deterministically from declared axes. Nulls mean the parent "
            "did not run that signed-arm stratum; no value is imputed."
        ),
        "gating": "NONE. Expected resolution never admits, excludes, labels or ranks a cell.",
        "source_sha256": dict(sorted(source_hashes.items())),
        "row_count": len(rows),
        "strata": rows,
    }


def write_expected_resolution(
    prior_path: str | Path,
    basis_path: str | Path,
    out_path: str | Path,
    *,
    generated_at_utc: str,
    source_hashes: dict[str, str],
) -> dict:
    """Write a deterministic pre-run resolution forecast from pinned JSON inputs."""
    prior_path = Path(prior_path)
    basis_path = Path(basis_path)
    prior_bytes = prior_path.read_bytes()
    basis_bytes = basis_path.read_bytes()
    payload = build_expected_resolution(
        json.loads(prior_bytes),
        json.loads(basis_bytes),
        generated_at_utc=generated_at_utc,
        source_hashes=source_hashes,
    )
    payload["input_sha256"] = {
        "prior": hashlib.sha256(prior_bytes).hexdigest(),
        "basis": hashlib.sha256(basis_bytes).hexdigest(),
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def write_basis(
    df: pd.DataFrame,
    out_path: str | Path,
    *,
    source: str,
    source_ci_rule: str,
    ladder: Sequence[float],
    group_col: str | None = None,
    **cell_kwargs,
) -> dict:
    """Compute the basis and write it to JSON. Designs pin this file, not its numbers.

    The emitted object carries the band table, the required-`n` grid over `ladder`, and
    the source CI rule, so a reader can see what was measured, on how many genuinely
    distinct cells, and under which uncertainty construction.
    """
    bands = c_bands(
        df, source_ci_rule=source_ci_rule, group_col=group_col, **cell_kwargs
    )
    grid = {
        f"{d:g}": {
            row["n_band"]: round(required_n(row["c_median"], d))
            for _, row in bands.iterrows()
        }
        for d in ladder
    }
    payload = {
        "source": source,
        "source_ci_rule": source_ci_rule,
        "provenance": "COMPUTED from the source emission by xen.resolution_basis; never typed",
        "definition": "c = (block_mde_bps / ((1-p)*L)) * sqrt(n); dimensionless",
        "caveat": (
            "c is comparable only across cells whose CIs used the SAME block rule, "
            "block sweep and seed battery. Reusing c under a weaker rule understates "
            "uncertainty. Bands whose distinct_n or distinct_groups is small do not "
            "support a range claim -- the spread there is noise."
        ),
        "gating": "NONE. No band, rung or value admits, excludes, labels or ranks any cell.",
        "n_bands": bands.to_dict(orient="records"),
        "required_n_by_band": grid,
        "ladder": list(ladder),
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload
