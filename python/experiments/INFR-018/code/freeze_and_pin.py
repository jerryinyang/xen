"""INFR-018 — freeze each gate's winner and emit the hash-pinned instrument registry.

Three entry points, run in the source's order and never out of it:

    freeze_and_pin.py anchor     # after HYP-I2 DESIGN, before the CONFIRM run
    freeze_and_pin.py a6         # after HYP-I3 DESIGN, before the CONFIRM run
    freeze_and_pin.py registry   # after HYP-I4 — the deliverable

The freeze files are what make the CONFIRM bank untouchable during tuning: each
runner refuses to open a CONFIRM path until the corresponding freeze exists, so
"select on DESIGN, verify once on CONFIRM" is enforced by the filesystem rather
than by discipline.

The registry is self-hashed the way INFR-017's ``column_pins.json`` is: the
sha256 is taken over the content with the ``pin_sha256`` field excluded, so the
hash and the artifact can never drift apart.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import adjudicate_i2_survival, adjudicate_i3_survival, out_dir  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from xen.estimand_validation import check_no_local_accounting  # noqa: E402
from xen.sigbar.data_types import SIGBAR_PIPELINE_VERSION  # noqa: E402
from xen.sigbar.fences import UNIVERSE_N, assert_frozen_inputs, repo_root  # noqa: E402


def _self_hash(obj: dict) -> str:
    """sha256 over the content with ``pin_sha256`` excluded."""
    body = {k: v for k, v in obj.items() if k != "pin_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


def _spot_check_divergence(spot: dict | None, top: dict) -> dict:
    """Classify the pooled winner against the per-instrument spot-check races.

    The rule is pre-declared in design §3.7 precisely so it cannot be argued
    after the table is seen, and it is evaluated in code so a run cannot quietly
    skip an operator control that was signed at checkpoint-014 (QA run 1, I-8):

      MATERIAL := the pooled winner ranks BELOW the local median of the 12 cells
                  on >= 2 of the 3 instruments, OR its local contrast is negative
                  on >= 2 of 3.

    This is a SENSITIVITY read, never a second selection budget: the pooled
    winner is not replaced by a local winner under any outcome. It can only
    confirm, or escalate.
    """
    if not spot:
        raise RuntimeError(
            "HYP-I2: the per-instrument spot-check is MANDATORY (checkpoint-014 §4, adherence "
            "resolution 2, operator-signed) and is absent from the race artifact"
        )
    rows, n_below, n_neg, n_inst = [], 0, 0, 0
    for sym, res in spot.items():
        cells = (res or {}).get("cells")
        if not cells:
            rows.append({"symbol": sym, "status": res.get("status", "NO_CELLS")})
            continue
        n_inst += 1
        vals = [c["contrast_median"] for c in cells if c.get("contrast_median") is not None]
        mine = next(
            (c["contrast_median"] for c in cells
             if c["anchor_id"] == top["anchor_id"] and c["ib_minutes"] == top["ib_minutes"]),
            None,
        )
        med = float(np.median(vals)) if vals else None
        below = mine is not None and med is not None and mine < med
        neg = mine is not None and mine < 0
        n_below += int(below)
        n_neg += int(neg)
        local_best = max(cells, key=lambda c: (c.get("contrast_median") is not None,
                                               c.get("contrast_median")))
        rows.append({
            "symbol": sym,
            "pooled_winner_local_contrast": mine,
            "local_median_contrast": med,
            "below_local_median": below,
            "locally_negative": neg,
            "local_winner": {"anchor_id": local_best["anchor_id"],
                             "ib_minutes": local_best["ib_minutes"],
                             "contrast_median": local_best.get("contrast_median")},
        })
    return {
        "rule": "MATERIAL if the pooled winner is below the local median on >=2 of 3 instruments, "
                "or locally negative on >=2 of 3",
        "classification": "MATERIAL" if (n_below >= 2 or n_neg >= 2) else "COSMETIC",
        "n_instruments": n_inst,
        "n_below_median": n_below,
        "n_negative": n_neg,
        "per_instrument": rows,
        "is_a_selection_budget": False,
    }


def _design_table(cells: list[dict]) -> list[dict]:
    """The full per-cell DESIGN table §9 requires the pin to carry.

    The ranking alone is three numbers per row and reads as a table of resolved
    effects. §9 asks for E, the control level, the collapse fraction and
    stability; the interval and the detectability floor are carried too, because
    without them a reader cannot see that a cell's measured contrast sits below
    what its own sample can resolve (QA run 5, I-38a).

    Report layer, not a gate: `below_own_mde` is computed and published, and it
    drops, hides and re-ranks nothing (L-32).
    """
    out = []
    for c in cells:
        cal = c.get("CALIBRATION_ONLY") or {}
        ci = c.get("contrast_ci") or {}
        stab = c.get("stability") or {}
        e = c.get("contrast_median")
        mde = (c.get("power") or {}).get("mde")
        out.append({
            "anchor_id": c.get("anchor_id"),
            "ib_minutes": c.get("ib_minutes"),
            "contrast_median": e,
            "contrast_ci": ci.get("ci"),
            "ci_excludes_zero": ci.get("ci_excludes_zero"),
            "block_fragile": ci.get("block_fragile"),
            "mde": mde,
            "mde_units": MDE_UNITS,
            "below_own_mde": None if e is None or mde is None else bool(abs(e) < mde),
            "CALIBRATION_ONLY_real_level": cal.get("asym_real_median"),
            "CALIBRATION_ONLY_control_level": cal.get("asym_control_median"),
            "CALIBRATION_ONLY_collapse_fraction": cal.get("collapse_fraction"),
            "n_days_paired": c.get("n_days_paired"),
            "n_real_sessions": c.get("n_real_sessions"),
            # Per-symbol detail is 140 rows per cell; the winner's full table is
            # carried separately under anchor.stability.
            "stability": {
                "thirds": stab.get("thirds"),
                "frac_symbols_positive": stab.get("frac_symbols_positive"),
                "n_symbols": len(stab.get("per_symbol") or []),
            },
        })
    return out


#: A per-symbol stratum below this many sessions is pre-declared UNPOWERED
#: (design §6.2) and can never be read as a negative.
MIN_SESSIONS_POWERED = 40


def _unpowered_strata(i2: dict, anchor: dict, i4: dict | None) -> dict:
    """Enumerate the realised UNPOWERED strata §9 requires the pin to list.

    §6.2 pre-declares the rules; the pin previously carried a pointer string
    instead of the strata themselves (QA run 5, I-38c). An unpowered stratum is
    never read as a negative, so naming them is what makes that rule checkable.
    """
    cells = i2.get("cells") or []
    top_cell = next(
        (c for c in cells
         if c.get("anchor_id") == anchor["anchor_id"] and c.get("ib_minutes") == anchor["ib_minutes"]),
        None,
    ) or {}
    thin = [
        {"symbol": p["symbol"], "n_days_paired": p["n_days"]}
        for p in ((top_cell.get("stability") or {}).get("per_symbol") or [])
        if p.get("n_days") is not None and p["n_days"] < MIN_SESSIONS_POWERED
    ]
    # §6.2 pre-declares the PER-SYMBOL third splits (~76 sessions each) as unpowered.
    # The thirds this item computes are POOLED across the panel (~202 days each) and
    # are a different object; listing those as unpowered would license dismissing a
    # pooled third that disagrees with the winner — the winner's middle third is
    # −0.68 (QA run 6, I-47). They are published, and explicitly NOT excused.
    pooled_thirds = [
        {"anchor_id": c["anchor_id"], "ib_minutes": c["ib_minutes"],
         "third": t["third"], "n_days": t["n_days"], "median": t["median"]}
        for c in cells if c.get("anchor_id") in ("A-USOPEN", "A-EUOPEN")
        for t in ((c.get("stability") or {}).get("thirds") or [])
    ]
    below_mde = [
        {"anchor_id": r["anchor_id"], "ib_minutes": r["ib_minutes"],
         "contrast_median": r["contrast_median"], "mde": r["mde"]}
        for r in _design_table(cells) if r["below_own_mde"]
    ]
    # The HYP-I4 emitter marks each class with a band_label, and UNPOWERED is one of
    # them; reading a non-existent `unpowered_classes` key left the pointer string as
    # the only reachable value (QA run 6, I-49).
    per_class = ((i4 or {}).get("exit_2_class_clustering") or {}).get("per_class") or {}
    classes = [
        {"class": cls, "n_event": v.get("n_event"), "mde": v.get("mde")}
        for cls, v in per_class.items() if v.get("band_label") == "UNPOWERED"
    ]
    return {
        "rule": "design §6.2 — a stratum below its published MDE floor, or below the "
                f"{MIN_SESSIONS_POWERED}-session per-symbol floor, is UNPOWERED and is never "
                "read as a negative",
        "per_symbol_below_session_floor": thin,
        "n_per_symbol_below_session_floor": len(thin),
        "spot_check_cells": {
            "instruments": sorted((i2.get("spot_check") or {}).keys()),
            "note": "pre-declared UNPOWERED for selection (§6.2); a SENSITIVITY read only",
        },
        "anchor_cells_below_own_mde": below_mde,
        "class_strata": classes,
        "class_strata_source": "HYP-I4 per_class band_label == UNPOWERED"
                               if per_class else "HYP-I4 artifact absent or carries no per_class",
        "NOT_unpowered_pooled_thirds": {
            "note": "§6.2 pre-declares the PER-SYMBOL third splits (~76 sessions). These pooled "
                    "thirds (~202 days) are NOT that stratum, are NOT unpowered, and may not be "
                    "dismissed as such. This item does not compute the per-symbol thirds.",
            "thirds": pooled_thirds,
        },
    }


def _load(name: str) -> dict:
    p = out_dir() / name
    if not p.exists():
        raise RuntimeError(f"missing prerequisite artifact {p}")
    return json.loads(p.read_text())


#: A tripwire has collapsed when the destroyed statistic is this fraction of the
#: raw one or less. NOT a value threshold — it adjudicates VALIDITY only
#: (design §7): failure means the emission is invalid and the code is fixed, not
#: that there is no effect.
TRIPWIRE_COLLAPSE_MAX = 0.25

#: AMENDMENT-5 / QA I-62: pin units for every published MDE so a reader never
#: confuses contrast units with the half-size drift plant.
MDE_UNITS = "contrast (E) units; the equivalent drift plant is half this"


def _rederive_i2_survival(tw: dict) -> dict:
    """Re-derive survival from tripwire primitives; refuse soft/null paths (I-34)."""
    try:
        return adjudicate_i2_survival(
            contrast_raw=tw.get("contrast_raw"),
            contrast_shifted=tw.get("contrast_shifted"),
            collapse_fraction=tw.get("collapse_fraction"),
            day_contrast_correlation=tw.get("day_contrast_correlation"),
        )
    except ValueError as exc:
        raise RuntimeError(
            f"HYP-I2 tripwire survival cannot be re-derived from primitives: {exc}. "
            "day_contrast_correlation is mandatory and finite; freeze does not trust a "
            "precomputed survives flag alone (QA run 3, I-34)."
        ) from exc


def _assert_tripwire(tw: dict | None, name: str) -> dict:
    """Refuse to freeze when the future-destroy tripwire fails its integrity check.

    HYP-I2 (I-29/I-34): survival adjudication re-derived from primitives; day_corr
    mandatory; positive-control leak plant must itself SURVIVE (bite).
    HYP-I3 (I-59): same-sign |cf| > 0.25 survival (not magnitude-only); leaky disc
    must SURVIVE on the spliced bars (AMENDMENT-6).
    """
    if not tw:
        raise RuntimeError(f"{name}: no tripwire result present — cannot freeze without it")
    if tw.get("status") == "COULD_NOT_RUN":
        raise RuntimeError(f"{name}: tripwire could not run ({tw.get('swap_stats')})")
    cf = tw.get("collapse_fraction")
    if cf is None:
        raise RuntimeError(f"{name}: tripwire collapse fraction is null — cannot attest validity")

    # Which adjudication applies is decided by what the ARTIFACT carries, not by
    # what the caller called it. The name is still matched (production passes
    # "HYP-I2 future_shift" — QA run 4, I-36) but only as one of three signals, and
    # it no longer decides whether a probe is required at all (QA run 6, I-53).
    use_i2 = (
        name.startswith("HYP-I2")
        or tw.get("adjudication_kind") == "i2_survival"
        or ("survives" in tw and "day_contrast_correlation" in tw)
    )

    if use_i2:
        derived = _rederive_i2_survival(tw)
        if tw.get("survives") is not None and bool(tw["survives"]) != derived["survives"]:
            raise RuntimeError(
                f"{name}: emitter survives={tw['survives']} disagrees with re-derived "
                f"survives={derived['survives']} (cf={cf}, day_corr="
                f"{tw.get('day_contrast_correlation')}). Freeze does not trust the flag alone."
            )
        if derived["survives"]:
            raise RuntimeError(
                f"{name}: FUTURE-DESTROY TRIPWIRE — EDGE SURVIVED THE DESTROY "
                f"(collapse_fraction={cf}, day_contrast_correlation="
                f"{tw.get('day_contrast_correlation')}, same_sign_material="
                f"{derived['same_sign_material']}). The construction is leaking "
                "future information. Fix the code and re-run. NEVER read as 'no effect'."
            )
        tw = {**tw, "survives_rederived": derived}
    else:
        # HYP-I3: design §4.4 SURVIVAL := |cf| > 0.25 with the same sign as S_raw
        # (QA I-59). Magnitude-only was the AMENDMENT-4 trap on this gate.
        try:
            derived = adjudicate_i3_survival(
                S_raw=tw.get("S_raw"),
                S_swapped=tw.get("S_swapped"),
                collapse_fraction=cf,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"{name}: I3 tripwire survival cannot be re-derived from primitives: {exc}. "
                "S_raw and S_swapped are mandatory for the sign clause (QA I-59)."
            ) from exc
        if tw.get("survives") is not None and bool(tw["survives"]) != derived["survives"]:
            raise RuntimeError(
                f"{name}: emitter survives={tw['survives']} disagrees with re-derived "
                f"survives={derived['survives']} (cf={cf}, S_raw={tw.get('S_raw')}, "
                f"S_swapped={tw.get('S_swapped')}). Freeze does not trust the flag alone."
            )
        if derived["survives"]:
            raise RuntimeError(
                f"{name}: FUTURE-DESTROY TRIPWIRE DID NOT COLLAPSE — same-sign "
                f"|collapse_fraction| {abs(float(cf)):.3f} > {TRIPWIRE_COLLAPSE_MAX} "
                f"(S_raw={tw.get('S_raw')}, S_swapped={tw.get('S_swapped')}). The emission "
                "is INVALID: the construction is leaking future information. Fix the code "
                "and re-run. This is NEVER read as 'no effect'."
            )
        tw = {**tw, "survives_rederived": derived}

    # EVERY future-destroy tripwire must show it has bite, whatever it is called.
    # Keying the requirement on the caller's name string was the I-36 defect one
    # layer down: a tripwire passed under the name "future_shift" with no probe at
    # all (QA run 6, I-53). There is no third caller and no exempt gate.
    probe = tw.get("positive_control")
    if probe is None:
        raise RuntimeError(
            f"{name}: positive_control leak plant is REQUIRED (QA runs 3–6, "
            "I-34/I-36/I-37/I-53). A tripwire that has never been shown to fire cannot "
            "attest validity: its pass on the real cell carries no information. Re-run the "
            "DESIGN race with the emitter that plants it."
        )
    if probe is not None:
        if probe.get("kind") == "i2_leak_plant" or (
            use_i2 and "day_contrast_correlation" in probe
        ):
            try:
                p_der = adjudicate_i2_survival(
                    contrast_raw=probe.get("contrast_raw"),
                    contrast_shifted=probe.get("contrast_shifted"),
                    collapse_fraction=probe.get("collapse_fraction"),
                    day_contrast_correlation=probe.get("day_contrast_correlation"),
                )
            except ValueError as exc:
                raise RuntimeError(
                    f"{name}: positive_control leak plant is incomplete: {exc}"
                ) from exc
            if not p_der["survives"]:
                raise RuntimeError(
                    f"{name}: the tripwire's POSITIVE CONTROL (future-IB leak plant) did NOT "
                    f"survive (cf={probe.get('collapse_fraction')}, day_corr="
                    f"{probe.get('day_contrast_correlation')}). The survival gate is "
                    "insensitive; its pass on the real cell carries no information."
                )
            # I-63: write the re-derived verdict back (I-52 for the I2 probe branch).
            probe = {**probe, "survives_rederived": p_der}
            tw = {**tw, "positive_control": probe}
        else:
            # HYP-I3 (AMENDMENT-6): the leaky probe is evaluated on the SAME
            # spliced bars as the real arm, so it reads the donor outcome path
            # that the labels were computed from. It must therefore SURVIVE.
            # Requiring it to COLLAPSE was the polarity that certified a toothless
            # gate — under the old label-only swap everything collapsed, honest or
            # leaky, and the probe's collapse was read as evidence (QA run 6, I-45).
            pcf = probe.get("collapse_fraction")
            s_raw, s_swapped = probe.get("S_raw"), probe.get("S_swapped")
            try:
                p_der = adjudicate_i3_survival(
                    S_raw=s_raw, S_swapped=s_swapped, collapse_fraction=pcf
                )
            except ValueError:
                p_der = {"survives": False, "same_sign_material": False}
            survives = bool(p_der["survives"])
            if probe.get("survives") is not None and bool(probe["survives"]) != survives:
                raise RuntimeError(
                    f"{name}: positive_control survives={probe['survives']} disagrees with the "
                    f"re-derived {survives} (cf={pcf}, S_raw={s_raw}, S_swapped={s_swapped}). "
                    "Freeze does not trust the emitter's flag."
                )
            if not survives:
                raise RuntimeError(
                    f"{name}: the tripwire's POSITIVE CONTROL did not survive (collapse_fraction "
                    f"{pcf}, S_raw={s_raw}, S_swapped={s_swapped}). A discriminator that reads "
                    "the donor outcome path, with labels computed from that same path, must keep "
                    "its separation. That it did not means the destroy is not reaching the bars "
                    "the rule reads, so the tripwire is insensitive and its pass on the real cell "
                    "carries no information."
                )
            probe = {**probe, "survives_rederived": p_der}
            tw = {**tw, "positive_control": probe}
    return tw


def _assert_full_universe(race: dict, name: str) -> None:
    """Refuse to freeze a race that ran on a smoke universe.

    The smoke and the real run write the SAME filenames, and the race artifact
    is read blindly by the freeze step, so without this a `--limit` run would
    silently freeze the anchor on a handful of symbols and the registry would
    carry no field revealing it (QA run 1, I-22).
    """
    scale = race.get("universe_scale") or {}
    if scale.get("limit") is not None:
        raise RuntimeError(
            f"{name}: race artifact was produced with --limit {scale['limit']} (a smoke run). "
            "Re-run the full race before freezing."
        )
    n = scale.get("n_symbols_selected")
    if n is None:
        raise RuntimeError(f"{name}: race artifact carries no universe_scale — cannot verify it")
    if n < UNIVERSE_N:
        raise RuntimeError(
            f"{name}: race ran on {n} distinct symbols, fewer than the declared n={UNIVERSE_N} "
            "panel; this is a smoke-scale artifact, not a full race"
        )


def freeze_anchor() -> Path:
    """Freeze the HYP-I2 winner: the highest contrast on the DESIGN bank.

    The rule is stated here and applied mechanically: the winner is the cell with
    the highest paired contrast. Stability is reported alongside but does not
    silently re-rank — a stability-weighted winner would be a second selection
    rule invented after seeing the table.

    Three things must hold before anything is written: the race ran at full
    scale, the future-destroy tripwire collapsed, and the mandatory
    per-instrument spot-check shows no material pooled-vs-local divergence.
    """
    race = _load("hyp_i2_anchor_race_DESIGN.json")
    ranked = race["ranked"]
    if not ranked:
        raise RuntimeError("no rankable HYP-I2 cell — nothing to freeze")
    _assert_full_universe(race, "HYP-I2")
    # Keep what the assertion returns: it carries `survives_rederived`, and pinning
    # the emitter's own flag instead was the whole point of I-34 going undone
    # (QA run 6, I-52).
    tripwire = _assert_tripwire(race.get("tripwire_future_shift"), "HYP-I2 future_shift")
    top = ranked[0]
    divergence = _spot_check_divergence(race.get("spot_check"), top)
    if divergence["classification"] == "MATERIAL":
        raise RuntimeError(
            "HYP-I2: MATERIAL pooled-vs-local divergence — the pooled winner "
            f"{top['anchor_id']}/L={top['ib_minutes']} ranks below the local median on "
            f"{divergence['n_below_median']} of {divergence['n_instruments']} spot-check "
            f"instruments and has a negative local contrast on {divergence['n_negative']}. "
            "Design §3.7 requires this be recorded as a SCOPE LIMIT and ESCALATED TO THE "
            "OPERATOR BEFORE FREEZING. Do not auto-freeze.\n"
            f"table: {json.dumps(divergence['per_instrument'], indent=2, default=str)}"
        )
    cell = next(
        c for c in race["cells"]
        if c["anchor_id"] == top["anchor_id"] and c["ib_minutes"] == top["ib_minutes"]
    )
    obj = {
        "item": "INFR-018",
        "gate": "HYP-I2",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "selection_rule": "highest paired day-clustered median contrast on the DESIGN bank; "
                          "stability is reported, never used to re-rank",
        "spot_check_divergence": divergence,
        "universe_scale": race.get("universe_scale"),
        "anchor_id": top["anchor_id"],
        "ib_minutes": top["ib_minutes"],
        "contrast_median": top["contrast_median"],
        "contrast_ci": cell["contrast_ci"],
        "stability": cell["stability"],
        "power": {**(cell["power"] or {}), "mde_units": MDE_UNITS},
        "multiplicity": race["multiplicity"],
        "full_table": race["ranked"],
        # §9 requires the pin to carry the full 12-cell table, not the ranking
        # alone (QA run 5, I-38a).
        "design_table": _design_table(race["cells"]),
        "tripwire_future_shift": tripwire,
        "break_rule_at_phase1": race["break_rule_at_phase1"],
        "scope": "STAGE I parameter — not evidence that anything works",
    }
    obj["pin_sha256"] = _self_hash(obj)
    p = out_dir() / "anchor_freeze.json"
    p.write_text(json.dumps(obj, indent=2, default=str))
    return p


def freeze_a6() -> Path:
    """Freeze the HYP-I3 winner: the highest separation on the DESIGN bank."""
    race = _load("hyp_i3_a6_race_DESIGN.json")
    ranked = race["ranked_top"]
    if not ranked:
        raise RuntimeError("no rankable HYP-I3 cell — nothing to freeze")
    _assert_full_universe(race, "HYP-I3")
    tripwire = _assert_tripwire(race.get("tripwire_outcome_path_swap"), "HYP-I3 outcome_path_swap")
    top = ranked[0]
    obj = {
        "item": "INFR-018",
        "gate": "HYP-I3",
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "selection_rule": "highest separation S on the DESIGN bank; bands are labels and do "
                          "not select",
        "disc_id": top["disc_id"],
        "family": top["family"],
        "flow_augmented": top["flow_augmented"],
        "params": top["params"],
        "poke_delta": top["poke_delta"],
        "separation": top["separation"],
        "collapse_fraction": top["collapse_fraction"],
        "day_clustered_ci": top["day_clustered_ci"],
        "interpretation_band": top["interpretation_band"],
        "inherited_anchor": race["inherited_anchor"],
        # §9's "full race table" for the A6 rule (QA run 5, I-38a).
        "full_table": ranked,
        "race_grid": race["race_grid"],
        "tripwire_outcome_path_swap": tripwire,
        "scope": "STAGE I parameter — not evidence that anything works",
    }
    obj["pin_sha256"] = _self_hash(obj)
    p = out_dir() / "a6_freeze.json"
    p.write_text(json.dumps(obj, indent=2, default=str))
    return p


def build_registry() -> Path:
    """Emit the deliverable: the hash-pinned instrument registry."""
    frozen = assert_frozen_inputs()

    # Machine-check the no-local-accounting guarantee rather than asserting it in
    # the pin. It is substantively trivial here (this item books no P&L at all),
    # but design §7 lists it as HARD and the registry states it as verified, so
    # it is verified (QA run 1, I-18).
    root = repo_root()
    accounting = check_no_local_accounting(root / "python/experiments/INFR-018/code")
    accounting_shared = check_no_local_accounting(root / "python/src/xen/sigbar")
    if not accounting["ok"] or not accounting_shared["ok"]:
        raise RuntimeError(
            "no-local-accounting check FAILED: "
            f"{accounting['banned_defs_found'] + accounting_shared['banned_defs_found']}"
        )

    anchor = _load("anchor_freeze.json")
    a6 = _load("a6_freeze.json")
    i4 = _load("hyp_i4_validation_DESIGN.json")
    i2 = _load("hyp_i2_anchor_race_DESIGN.json")
    # Band-suffixed, and the band is checked rather than assumed: the file used to
    # be written under one name by both bands, so the CONFIRM run overwrote it and
    # the pin would have carried the CONFIRM panel as "the universe" with nothing
    # revealing it (QA run 6, I-46).
    universe = _load("universe_reconciliation_DESIGN.json")
    got_band = (universe.get("reconciliation") or {}).get("band")
    if got_band != "DESIGN":
        raise RuntimeError(
            f"universe reconciliation carries band {got_band!r}, expected 'DESIGN' — the pin "
            "records the DESIGN panel; a CONFIRM panel here would misattribute the universe"
        )
    # I-31: refuse a smoke-scale I4 pin the same way I2/I3 freezes refuse smoke races.
    _assert_full_universe(i4, "HYP-I4")

    def _opt(name: str) -> dict | None:
        p = out_dir() / name
        return json.loads(p.read_text()) if p.exists() else None

    i2c = _opt("hyp_i2_anchor_race_CONFIRM.json")
    i3c = _opt("hyp_i3_a6_race_CONFIRM.json")

    obj: dict = {
        "item": "INFR-018",
        "family": "CF-SIGAUC-001",
        "checkpoint": "014 §4",
        "stage": "I — instrument building",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_inputs": {
            "seasonal_baselines_sha256": frozen.baselines_sha256,
            "column_pins_sha256": frozen.column_pins_sha256,
            "fence_manifest_sha256": frozen.fence_manifest_sha256,
            "sigbar_pipeline_version": SIGBAR_PIPELINE_VERSION,
        },
        "anchor": {
            "anchor_id": anchor["anchor_id"],
            "ib_minutes": anchor["ib_minutes"],
            "selection_rule": anchor["selection_rule"],
            "design_table": anchor["design_table"],
            "ranking": anchor["full_table"],
            "contrast_ci": anchor["contrast_ci"],
            "power": anchor["power"],
            # The ranking's resolution, stated in the pin rather than left for a
            # reader to reconstruct: the winner is a Stage I PARAMETER, and on this
            # bank the race does not resolve the candidates apart (QA run 5, I-38a).
            "resolution": {
                "winner_ci": (anchor["contrast_ci"] or {}).get("ci"),
                "winner_ci_excludes_zero": (anchor["contrast_ci"] or {}).get("ci_excludes_zero"),
                "winner_mde": (anchor["power"] or {}).get("mde"),
                "mde_units": MDE_UNITS,
                "winner_below_own_mde": next(
                    (r["below_own_mde"] for r in anchor["design_table"]
                     if r["anchor_id"] == anchor["anchor_id"]
                     and r["ib_minutes"] == anchor["ib_minutes"]),
                    None,
                ),
                # The count alone reads as "four effects were resolved". Every one
                # of them is NEGATIVE and none is the winner, which is the opposite
                # reading (QA run 6, I-50).
                "n_cells_ci_excludes_zero": sum(
                    1 for r in anchor["design_table"] if r["ci_excludes_zero"]
                ),
                "cells_ci_excludes_zero": [
                    {"anchor_id": r["anchor_id"], "ib_minutes": r["ib_minutes"],
                     "contrast_median": r["contrast_median"]}
                    for r in anchor["design_table"] if r["ci_excludes_zero"]
                ],
                "n_cells_ci_excludes_zero_positive": sum(
                    1 for r in anchor["design_table"]
                    if r["ci_excludes_zero"] and (r["contrast_median"] or 0) > 0
                ),
                "winner_ci_excludes_zero_flag": next(
                    (r["ci_excludes_zero"] for r in anchor["design_table"]
                     if r["anchor_id"] == anchor["anchor_id"]
                     and r["ib_minutes"] == anchor["ib_minutes"]),
                    None,
                ),
                "note": "a cell whose |E| is below its own MDE, or whose interval spans zero, "
                        "is NOT a resolved effect. The selection rule still applies — Stage I "
                        "needs a parameter — but the pin must not read as a ranking of "
                        "established effects.",
            },
            "stability": anchor["stability"],
            "confirm_train_internal": (
                {"note": "TRAIN_INTERNAL_CONFIRMATION: not out-of-sample in the programme's sense",
                 "ranked": i2c["ranked"]} if i2c else None
            ),
            "pooled_vs_spot_check": i2.get("spot_check"),
            "multiplicity": anchor["multiplicity"],
        },
        "a6_rule": {
            "disc_id": a6["disc_id"],
            "family": a6["family"],
            "flow_augmented": a6["flow_augmented"],
            "params": a6["params"],
            "poke_delta": a6["poke_delta"],
            "qualify_minutes": a6["race_grid"]["qualify_minutes"],
            "separation": a6["separation"],
            "day_clustered_ci": a6["day_clustered_ci"],
            "design_table": a6["full_table"],
            "interpretation_band": a6["interpretation_band"],
            "confirm_train_internal": (
                {"note": "TRAIN_INTERNAL_CONFIRMATION", "top": i3c["ranked_top"][:3]} if i3c else None
            ),
            "provisional_phase1_break_rule": anchor["break_rule_at_phase1"],
        },
        "kernel": i4["exit_1_kernel"],
        "class_thresholds": {
            "percentile_levels": i4["exit_2_class_clustering"]["percentile_levels"],
            "per_symbol_values": i4["exit_2_class_clustering"]["thresholds_per_symbol"],
            "event_counts": i4["exit_2_class_clustering"]["event_counts"],
            "clustering": i4["exit_2_class_clustering"]["per_class"],
        },
        "spread_regime_bands": i4["exit_3_bands"]["spread_regime_bands"],
        "universe": universe["reconciliation"],
        "validity_attestations": {
            "tripwire_future_shift_i2": anchor["tripwire_future_shift"],
            "tripwire_outcome_path_swap_i3": a6["tripwire_outcome_path_swap"],
            "bands_asserted": "every read path raises on any bar at or beyond its band end, "
                              "and on any bar at or beyond holdout_start",
            "holdout": "SEALED — never queried",
            "test_band": "RESERVED — 0 counted reads spent by this item",
            "per_level_delta": "BARRED — asserted in xen.sigbar.fences.assert_no_per_level_delta",
            "local_accounting": "NONE — this item books no P&L and defines no accounting primitive",
        },
        "scope_limits": {
            "survivorship": "the covered set is precisely the instruments listed before the bank "
                            "end, so it is a survivorship-shaped subset of the venue",
            "realised_design_span_days": "~229 for most instruments (4-year trailing cap; 120 of "
                                         "200 staged symbols begin 2022-07)",
            "confirmations": "TRAIN-INTERNAL — not out-of-sample in the programme's sense (D3)",
            "spread_layer": "§2.5 regime/veto layer unavailable — see spread_regime_bands",
            "unpowered_strata": _unpowered_strata(i2, anchor, i4),
            # The caveat travels with the published number rather than living only
            # in the source comment (QA run 6, I-27 residual).
            "incomplete_session_counts": "n_incomplete_sessions_band_total is counted before "
                                         "the membership restriction, so it spans the whole "
                                         "band for every panel symbol. A symbol whose sessions "
                                         "are ALL incomplete contributes zero to it, because "
                                         "there is no admitted row left to carry the count "
                                         "(known limitation, xen.sigbar.sessions).",
        },
        "not_evidence": "Nothing in this pin is evidence that any signal, grade, model or edge "
                        "works. Stage I outputs are parameters and validated instruments only "
                        "(source Appendix B). Stage II results computed against an unfrozen "
                        "instrument are unattributable and re-run.",
    }
    obj["pin_sha256"] = _self_hash(obj)
    p = out_dir() / "instrument_registry.json"
    p.write_text(json.dumps(obj, indent=2, default=str))
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["anchor", "a6", "registry"])
    args = ap.parse_args()
    p = {"anchor": freeze_anchor, "a6": freeze_a6, "registry": build_registry}[args.what]()
    obj = json.loads(p.read_text())
    print(f"wrote {p}  pin_sha256={obj['pin_sha256'][:16]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
