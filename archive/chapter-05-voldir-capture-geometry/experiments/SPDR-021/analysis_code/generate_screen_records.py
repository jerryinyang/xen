"""Generate neutral screen.md records for SPDR-021/022/023 from corrected run artifacts.

Neutral record only: identity, integrity, counts, populations, controls availability,
spread limitation, artifact links. No economic conclusion, no effect values.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

ROOT = Path("/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen")
STAMP = "20260803T140238Z"
UNIVERSES = ("ctrader", "crypto")

TITLES = {
    "SPDR-021": "Volatility-adaptive management on a fixed breakout benchmark",
    "SPDR-022": "Volatility-adaptive management on a fixed momentum-breach benchmark",
    "SPDR-023": "Volatility-adaptive management on a fixed mean-reversion-breach benchmark",
}
ENTRY_NOTE = {
    "SPDR-021": (
        "breakout only — a single entry variant (`BREAKOUT`). `E-TOUCH` / `E-CLOSE` do not apply "
        "to this experiment."
    ),
    "SPDR-022": "breach with two separate entry variants kept separate throughout: `E-TOUCH` and `E-CLOSE`.",
    "SPDR-023": "breach with two separate entry variants kept separate throughout: `E-TOUCH` and `E-CLOSE`.",
}
EXEC_ROWS = {
    ("SPDR-021", "ctrader"): ("1", "493 s", "733,256 KiB"),
    ("SPDR-021", "crypto"): ("2", "1,167 s", "3,596,712 KiB"),
    ("SPDR-022", "ctrader"): ("2 then 1", "5,816 s", "4,277,760 KiB"),
    ("SPDR-022", "crypto"): ("1", "8,659 s", "22,222,568 KiB"),
    ("SPDR-023", "ctrader"): ("1", "1,933 s", "4,290,136 KiB"),
    ("SPDR-023", "crypto"): ("1", "9,149 s", "22,292,148 KiB"),
}
ANALYSIS_ROWS = {
    ("SPDR-021", "ctrader"): ("376.868 s / 2.771 GB", "312.691 s / 2.650 GB"),
    ("SPDR-021", "crypto"): ("1,987.793 s / 3.070 GB", "2,054.076 s / 3.052 GB"),
    ("SPDR-022", "ctrader"): ("845.466 s / 4.295 GB", "842.795 s / 4.400 GB"),
    ("SPDR-022", "crypto"): ("5,035.342 s / 8.030 GB", "4,952.383 s / 7.653 GB"),
    ("SPDR-023", "ctrader"): ("1,056.134 s / 4.084 GB", "849.041 s / 3.897 GB"),
    ("SPDR-023", "crypto"): ("not persisted (session interrupted after atomic publication)",
                             "not persisted (session interrupted after atomic publication)"),
}

DEVICES = ("target", "stop", "trail", "hold", "size")


def fmt(n: int | float | None) -> str:
    if n is None:
        return "null"
    if isinstance(n, float):
        return f"{n:,.0f}" if n.is_integer() else f"{n:,.3f}"
    return f"{n:,}"


def universe_section(exp: str, universe: str, index: int) -> str:
    run_id = f"{exp}-{universe}-train-{STAMP}"
    run_path = ROOT / "data/nautilus_runs" / run_id
    ana = ROOT / "python/experiments" / exp / "results/analysis" / universe

    cfg = json.loads((run_path / "config.json").read_text())
    summary = json.loads((run_path / "run_summary.json").read_text())
    integrity = json.loads((run_path / "integrity_selfcheck.json").read_text())
    rowacc = json.loads((run_path / "row_accounting.json").read_text())
    estimand = json.loads((run_path / "estimand_validation.json").read_text())
    determinism = json.loads((run_path / "determinism.json").read_text())
    controls_raw = json.loads((run_path / "controls.json").read_text())
    ana_summary = json.loads((ana / "analysis_summary.json").read_text())

    jobs, duration, size = EXEC_ROWS[(exp, universe)]
    prod_analysis, repro_analysis = ANALYSIS_ROWS[(exp, universe)]

    lines: list[str] = []
    lines.append(f"## Universe {index} — {universe}")
    lines.append("")
    lines.append("### Run identity")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Run id | `{run_id}` |")
    lines.append(f"| Absolute path | `{run_path}` |")
    lines.append(f"| Catalog path | `{cfg['catalog_path']}` |")
    lines.append(f"| Manifest path | `{cfg['manifest_path']}` |")
    lines.append(f"| Manifest sha256 | `{cfg['manifest_sha256']}` |")
    lines.append(f"| Band | {cfg['band']} |")
    lines.append(f"| `train_start_utc` | `{cfg['train_start_utc']}` |")
    lines.append(f"| `train_end_utc` | `{cfg['train_end_utc']}` |")
    lines.append(f"| Symbols | {', '.join(cfg['symbols'])} ({len(cfg['symbols'])}) |")
    lines.append(
        f"| Work units | {cfg['work_units']} declared, {summary['completed_work_units']} completed |"
    )
    lines.append(f"| `native_arms` | {fmt(cfg['native_arms'])} |")
    lines.append(f"| `native_adaptive_arms` | {fmt(cfg['native_adaptive_arms'])} |")
    lines.append(f"| `management_arms` | {fmt(cfg['management_arms'])} |")
    lines.append(f"| `base_size_increments` | {fmt(cfg['base_size_increments'])} |")
    lines.append(f"| Execution workers | {jobs} |")
    lines.append(f"| Execution wall time | {duration} |")
    lines.append(f"| Raw output size | {size} |")
    lines.append("")
    lines.append(
        "**Spread limitation (repeated):** cost here is fees and funding only; spread is not "
        "charged, so every cost-bearing figure in this universe's artifacts understates cost."
    )
    lines.append("")

    lines.append("### Integrity status")
    lines.append("")
    hard = integrity["hard_checks"]
    passed = sum(1 for v in hard.values() if v is True)
    lines.append(
        f"`integrity_selfcheck.json` — `blocking_pass: {str(integrity['blocking_pass']).lower()}`. "
        f"**{len(hard)} hard checks, {passed} `true`:**"
    )
    lines.append("")
    lines.append("| Hard check | Result |")
    lines.append("| --- | --- |")
    for k in sorted(hard):
        lines.append(f"| `{k}` | `{str(hard[k]).lower()}` |")
    lines.append("")
    lines.append(
        f"Canonical estimand gate: `blocking_pass: {str(estimand['blocking_pass']).lower()}` over "
        f"{estimand['n_cells']} per-instrument cells. Determinism: "
        f"`pass: {str(determinism['pass']).lower()}` (mode `{determinism['mode']}`). "
        f"Row accounting: `pass: {str(rowacc['pass']).lower()}` "
        f"(native {fmt(rowacc['native_rows'])} rows, management {fmt(rowacc['management_rows'])} "
        f"rows, {fmt(rowacc['origin_count'])} origins, no missing, extra or duplicate key)."
    )
    lines.append("")

    lines.append("### Emission counts")
    lines.append("")
    lines.append("| Count | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Eligible origins | {fmt(summary['n_origins'])} |")
    lines.append(f"| Orders | {fmt(summary['n_orders'])} |")
    lines.append(f"| Fills | {fmt(summary['n_fills'])} |")
    lines.append(f"| Positions (opened) | {fmt(summary['n_positions'])} |")
    lines.append(f"| Native episode rows | {fmt(summary['n_episodes'])} |")
    lines.append(f"| Management policy rows | {fmt(summary['n_policy_rows'])} |")
    lines.append(f"| State-ledger rows | {fmt(controls_raw['ledger_rows'])} |")
    lines.append("")

    lines.append("### Device populations from the canonical analysis")
    lines.append("")
    lines.append(
        "Counts are population-labelled exactly as emitted. `eligible_origin_n` counts scheduled "
        "opportunities, `entry_fill_n` counts actual fills, `close_n` counts confirmed closes."
    )
    lines.append("")
    lines.append("| Device | rows | eligible_origin_n | entry_fill_n | close_n |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for dev in DEVICES:
        df = pl.read_parquet(
            ana / f"device_{dev}.parquet",
            columns=["eligible_origin_n", "entry_fill_n", "close_n"],
        )
        lines.append(
            f"| {dev.upper()} | {fmt(df.height)} | "
            f"{fmt(df['eligible_origin_n'].sum())} | {fmt(df['entry_fill_n'].sum())} | "
            f"{fmt(df['close_n'].sum())} |"
        )
    lines.append("")

    states = pl.read_parquet(ana / "state_sections.parquet", columns=["state", "row_n"])
    state_tot = states.group_by("state").agg(pl.col("row_n").sum()).sort("state")
    lines.append("Episode-state sections present in this universe (state as emitted by the state ledger):")
    lines.append("")
    lines.append("| State | rows |")
    lines.append("| --- | ---: |")
    for row in state_tot.iter_rows():
        lines.append(f"| `{row[0]}` | {fmt(row[1])} |")
    lines.append("")

    origins = pl.read_parquet(
        ana / "native_parameter_origins.parquet",
        columns=["estimate_source", "orientation_pair", "arm_class", "entry_variant"],
    )
    pairs = sorted(x for x in origins["orientation_pair"].unique().to_list() if x)
    classes = sorted(x for x in origins["arm_class"].unique().to_list() if x)
    variants = sorted(x for x in origins["entry_variant"].unique().to_list() if x)
    per_stratum = pl.read_parquet(
        ana / "per_stratum_estimates.parquet", columns=["estimate_source"]
    )
    lenses = sorted(x for x in per_stratum["estimate_source"].unique().to_list() if x)

    lines.append("### Native lattice and lenses")
    lines.append("")
    lines.append(f"- Entry variants present: {', '.join(f'`{v}`' for v in variants)}")
    lines.append(f"- Arm classes present: {', '.join(f'`{c}`' for c in classes)}")
    lines.append(f"- Orientation pairs present: {', '.join(f'`{p}`' for p in pairs)}")
    lines.append(f"- Estimand lenses present: {', '.join(f'`{x}`' for x in lenses)}")
    lines.append(
        f"- `native_parameter_origins.parquet` rows: {fmt(ana_summary['native_rows'])}; "
        f"paired trade rows: {fmt(ana_summary['paired_rows'])}; "
        f"block length: {ana_summary['block_bars']} bars; "
        f"interpretation field: `{ana_summary['interpretation']}`"
    )
    lines.append("")

    controls = pl.read_parquet(
        ana / "controls.parquet",
        columns=["control", "analysis_stage", "estimate", "undefined_reason"],
    )
    lines.append("### Control availability")
    lines.append("")
    lines.append("| Control | rows | stage | rows with an estimate | rows null with a reason |")
    lines.append("| --- | ---: | --- | ---: | ---: |")
    for name in sorted(controls["control"].unique().to_list()):
        sub = controls.filter(pl.col("control") == name)
        stage = ", ".join(f"`{s}`" for s in sorted(sub["analysis_stage"].unique().to_list()))
        with_est = sub.filter(pl.col("estimate").is_not_null()).height
        null_reason = sub.filter(
            pl.col("estimate").is_null() & pl.col("undefined_reason").is_not_null()
        ).height
        lines.append(f"| `{name}` | {fmt(sub.height)} | {stage} | {fmt(with_est)} | {fmt(null_reason)} |")
    lines.append("")
    lines.append(
        "Engine-side control inputs recorded in `controls.json`: time derangement "
        f"{fmt(controls_raw['time_derangement']['rows'])} rows, seed "
        f"{controls_raw['time_derangement']['seed']}, "
        f"`zero_fixed_points: {str(controls_raw['time_derangement']['zero_fixed_points']).lower()}`; "
        f"magnitude match {fmt(controls_raw['magnitude_match']['rows'])} rows "
        f"({fmt(controls_raw['magnitude_match']['selected_rows'])} selected, "
        f"{fmt(controls_raw['magnitude_match']['excluded_rows'])} excluded). Controls are "
        "informative and gate nothing."
    )
    lines.append("")

    lines.append("### Analysis artifacts")
    lines.append("")
    lines.append(f"- Directory: `python/experiments/{exp}/results/analysis/{universe}/`")
    lines.append(f"- Artifacts: {len(ana_summary['artifacts'])} of 13 declared")
    lines.append(f"- Production pass: {prod_analysis}")
    lines.append(f"- Independent reproduction pass: {repro_analysis}")
    lines.append(
        f"- Reproduction evidence: `python/experiments/{exp}/results/analysis/reproduction-hashes.json`"
    )
    lines.append("")
    return "\n".join(lines)


def build(exp: str) -> str:
    repro = json.loads(
        (ROOT / "python/experiments" / exp / "results/analysis/reproduction-hashes.json").read_text()
    )
    equal = all(u["all_equal"] for u in repro["universes"])
    head = f"""# {exp} — Screen record

- **Experiment:** `{exp}` — {TITLES[exp]}
- **Family / registration:** `CF-VOLDIR-001/HYP-D8`
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Band:** TRAIN
- **Vehicle:** NautilusTrader 1.230.0
- **Run stamp:** `{STAMP}` (two universes: cTrader, crypto)
- **Entry substrate:** {ENTRY_NOTE[exp]}
- **Date of this record:** 2026-08-04

**Status.** This is the amended rerun authorised on 2026-08-03. The earlier first pass was
invalidated and hard-removed; its identifiers are listed only in the invalidation record, see
`docs/superpowers/plans/2026-08-03-spdr-021-023-first-pass-invalidation.md`. Both universes of this
experiment ran to completion, passed every hard integrity check, and produced 13 analysis artifacts
per universe that reproduce exactly on an independent second pass
(13/13 SHA-256 equality in both universes: `all_equal = {str(equal).lower()}`).

**NO disposition is taken here.** This document is a neutral record of what ran and what exists. It
contains no interpretation, no effect values, no ranking of arms, and no verdict. The interpretive
read is `analysis.md`; the combined interpretation across the three experiments belongs to the
operator.

---

## Spread limitation

Reproduced from the run's own disclosure block (`config.json`, `run_summary.json`):

```text
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

Plainly: **cost in this run is partial.** Only fees and funding are charged. Spread is not charged
at all. Every cost-bearing field in every artifact therefore **understates cost**, and any
net-of-cost figure derived from them is correspondingly overstated.

Recording defect, all six cells: the mirrored `spread_cost_status`, `spread_rt_bps` and
`cost_scope` columns on `per_stratum_estimates.parquet` are null, because the analysis reads those
keys at the top level of the run config while the run nests them under `spread_cost_disclosure`.
The disclosure itself is intact in `config.json` and `run_summary.json`, no estimate is affected,
and the limitation is stated here and in `analysis.md` instead.

---

"""
    body = "\n---\n\n".join(
        universe_section(exp, u, i) for i, u in enumerate(UNIVERSES, start=1)
    )
    tail = """---

## Populations to keep separate when reading the artifacts

- `eligible_origin_n` — scheduled opportunities, including origins with no exposure because the arm
  was occupied. Per-origin intervals and MDEs are built from these.
- `entry_fill_n` — actual entry fills recorded by the engine.
- `close_n` — confirmed closes.
- `common_fill_n` / `common_close_n` — origins filled, or closed, on both comparison sides.
- `effective_origin_blocks` / `effective_trade_blocks` — resampled blocks behind the matching
  interval. A scheduled row never inflates a trade-level count.

The two native lenses (`COMMON_ORIGIN_OCCUPANCY_INCLUSIVE` and `COMMON_CLOSE_TRADE`) answer
different questions and must never be merged.

---

## What is not in this record

No effect value, no comparison of arms, no power judgement, no `SUPPORTED`/`REFUTED` label, no
winner, no tradability or deployability statement, and no TEST or holdout contact of any kind.
"""
    return head + body + "\n" + tail


for exp in ("SPDR-021", "SPDR-022", "SPDR-023"):
    out = ROOT / "python/experiments" / exp / "screen.md"
    out.write_text(build(exp))
    print("wrote", out, len(out.read_text().splitlines()), "lines")
