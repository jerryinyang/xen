# Phase 021 D0 — Amendment 005 (correct the EXP-094 falsification null to a matched-distance oscillation null)

**Date:** 2026-06-24. **Status:** **FROZEN — RATIFIED 2026-06-24 (operator-authorized).** **Nature:** a
**methodology correction**, surfaced at EXP-094 Stage 3 (implementation) during fill-engine inspection: the
`D0-amendment-004` §4(c) binding falsification null (**SUB-RANDOM-entry RCT**) is **structurally biased toward
admitting 4h** and cannot falsify the oscillation hypothesis it was built to test. It is **replaced** as the
binding §4(c) leg by a **matched favourable-target-distance oscillation null**; the original SUB-RANDOM-entry
RCT null is retained as a **disclosed companion**. **Slot / read impact:** 0 candidate slots, 0 counted TEST
reads (EXP-094 is TRAIN-only). Holdout untouched. **Amends:** `D0-amendment-004` §4(c) and §5 (bite-check
target); EXP-094 `scope.md` / `analysis-plan.md` updated in the same change.

**Checkpoint:** `2026-06-23-021-mr-fade-capture-geometry`.

---

## The defect (verdict-material — would have biased admission)

`D0-amendment-004` §4(c) specified the falsification null as the EXP-089 **SUB-RANDOM-entry RCT** control: draw
random/shuffled entries at matched count + direction and resolve them through the **same RCT target**
`P*=Close+(AL−AG)`. Engine inspection (`xen/intrabar_fill.py:220`, `EXP-090 arm_levels` RCT branch) shows why
this is biased:

- The RCT favourable target is **signal-derived**: `P*=Close+(AL−AG)`. At a real RSI extreme (`AL≫AG`) it is a
  well-formed favourable target (~0.28 ATR). **At a random/non-extreme bar `AL−AG` is small or negative**, so
  `P*` lands at/below entry — the **wrong side** — and the frozen engine **instant-fills it on the first 1m bar**
  (`fav_hit = has_fav and mh >= fav`).
- Consequently the random arm has **no well-formed favourable target to capture, independent of whether the
  real 4h edge is signal or oscillation.** Real entries beat this null **even if the real edge is pure
  oscillation harvesting** (at real extremes a ~0.28-ATR limit is hit ~99% by noise; at random times there is no
  comparable target). Neither a wrong-side guard (sends random events to 2×ATR stops → more negative) nor the
  unguarded form (instant-fills near entry → mildly negative) repairs this — both make real trivially beat
  random.

The SUB-RANDOM-entry RCT null therefore **cannot distinguish "the entry signal is load-bearing" from "a
~0.28-ATR target is hit by noise regardless of signal"** — which is the exact EXP-089-reconciliation question
EXP-094 exists to answer. (This is the risk flagged in the EXP-094 analysis plan's "Methodology risk & routing
flag", now confirmed concrete at the engine level.)

## The correction — matched favourable-target-distance oscillation null (binding §4(c))

The binding falsification null becomes a **matched-distance oscillation null** that gives the random arm a
**genuine, comparable favourable target** by construction, so the test asks the real question:

**Per member cell, for EXIT-RCT:**
1. **Real arm (unchanged):** the frozen EXIT-RCT, resolved through the verbatim EXP-090 engine (leg (b) result).
   Record the per-event **favourable target-distance multiple** `μ_k = (P*_{entry_k} − Close_{entry_k}) ·
   direction_k / ATR(14)_{entry_k}` over the real resolved RCT events (favourable, positive by construction at
   real extremes).
2. **Matched-distance random arm (the null):** draw `n` = real RCT resolved count distinct bars via
   `xen.capgeo_substrates.random_entries` (SUB-RANDOM, look-ahead-safe); assign the **shuffled real direction
   multiset** (matched count + direction mix); place a **static favourable limit** `entry_close + direction ·
   m · ATR(14)_entry`, where `m` is **resampled with replacement from the real cell's `{μ_k}`** (seed-fixed) —
   so the limit is favourable by construction at a distance drawn from the real RCT target distribution. Resolve
   through the **identical** adverse side (`2.0×ATR` stop + MR-tempo cap) + 1m intrabar fill + `D0-amendment-003`
   cost. (Implementation reuses the EXP-090 `ATR-BARRIER` static-favourable-level construction with a per-event
   resampled multiple in place of the fixed `1.0×ATR`.) **No wrong-side / degenerate instant-fill is possible.**
3. **Paired Δ & quorum (unchanged form):** `Δ_cell = mean(real RCT net) − mean(matched-distance-random net)`;
   two-sample moving-block bootstrap difference-of-means one-sided lower bound `Δ_lo` (Z=1.645, `n_boot=10_000`);
   a cell **real-beats-random** iff `Δ_lo > 0`; real entry **passes the falsification** iff it beats in **≥5
   cells over ≥3 instruments**.

**Interpretation (unchanged routing, correct test):** real beats the matched-distance null in quorum ⇒ the 4h
edge reflects entry-at-extreme capture beyond a comparable target placed at random times ⇒ **ADMIT_4H**. Real
fails to beat it ⇒ a comparable favourable limit nets the same at random times ⇒ **oscillation harvesting, not
the fade** ⇒ **4H_CLOSED_OSCILLATION**, retained. The 1h positive control (EXP-091 clearing cells) uses this
**same** matched-distance null; failing it ⇒ INCONCLUSIVE.

## Retained as a disclosed companion (non-binding)

The original §4(c) **SUB-RANDOM-entry RCT** null (with the wrong-side guard: a non-favourable `P*` is not a
favourable target → resolve via stop/cap only, never instant-fill; report `wrongside_frac`) is **retained and
reported as a disclosed companion** — it answers the narrower "RCT rule at real extremes vs the rule fired at
random times" question. It **never gates** the verdict.

## Bite-check target (amends §4(e)/§5)

The **new selection statistic** is the **matched-distance paired-Δ quorum**; it (not the SUB-RANDOM-entry
statistic) must be **bite-checked GREEN** at EXP-094 D0 before any binding result run — FPR-controlled under a
real≡random (same-distribution) construction and powered at the planted per-cell MDE. RED/AMBER halts to the
pipeline.

## What this does NOT change

The §3 scope decision (4h opened, 0 new slots, gated behind EXP-094), the readiness leg (a), the net exit screen
leg (b), the ≥5/≥3 quorum shape, the cost model (`D0-amendment-003`), the frozen entry/RCT/adverse constants,
the TRAIN-only / holdout discipline, and the ADMIT_4H / 4H_CLOSED_OSCILLATION / 4H_EMPTY / INCONCLUSIVE routing —
all unchanged. Only the **construction of the random comparison arm** in §4(c) is corrected (signal-derived
target → matched-distance favourable target), with the original retained as a companion.

---

*FROZEN — RATIFIED 2026-06-24 (operator-authorized). EXP-094 `scope.md` / `analysis-plan.md` updated to the
matched-distance binding null in the same change; implementation (Stage 3) proceeds against this amendment. The
G-021 adjudication reads 4h only if EXP-094 admits it under this corrected null.*
