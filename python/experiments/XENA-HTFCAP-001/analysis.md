# XENA-HTFCAP-001 — Re-analysis under INFR-016 report layers

**Run mode:** operator-authorized EXPLORATORY (TRAIN+TEST, no reserved OOS — AMENDMENT-4/5).
**NOT a certification, NOT a deployability claim.** Pin INFR-015 `abbb1842…` CLS-FILTER LOW-only.
HOLDOUT (≥ 2025-01-08) sealed throughout. Emission REUSED (engine runs only at emission; every
layer reads the emitted parquet). Prior gate-framed analysis archived at
`archive/pre-infr016/`. Framework: value/quality/significance reads are **report layers**
(`observed / ideal / interpretation` per candidate, no pass/fail); nothing machine-dropped;
operator authorises what advances. Artifacts: `results/layer_reports.json`,
`results/layer_tables.md`.

**Re-run 2026-07-19 under the structural-label update.** Framework follow-up retired the
machine-assigned p-cutpoint labels (STRONG/SUPPORTED/SUGGESTIVE/WASH) — a hardcoded-p label
re-imported the L-32 threshold trap in miniature. Labels are now **structural only**
(UNPOWERED / CONTRADICTED / —); the observed number + one-sided p + CI is the read, operator
judges. All numbers here are deterministic and **unchanged** from the 2026-07-18 run; only the
sign-battery label column changed.

## What changed vs the archived (gate-framed) read
The old read reported **one certified object** (binder top-1) and called the family
**NOT SUPPORTED / leak-class**. Retiring the three value gates flips two of those conclusions:

1. **`one_subset` top-1 hiding retired → stage-2 per cell.** The binder's `g_net` search + top-1
   pick landed on the **worst** cell (`v1.5/adx30/H64`, embargoed gross LCB −123). Reporting all
   72 binding cells shows **5 cells with a positive embargoed gross LCB**, and the strongest
   (`DI_ADX×VOL_HI adx25 H64/H32`) also **clear the sign-null and are gate-attributable.** The
   selection machinery hid the real gross edge.
2. **`hard_fail_leak` collapse<0.5 retired → reported fraction.** The old "top-1 is a leak,
   collapse 0.14" was a **near-zero-denominator artifact**: that cell's raw edge is ~1 bps
   (sign p=0.44 = pure noise), so `1 − deranged/raw` is undefined-noisy (now 0.90, band ±16).
   Nothing to attribute → not a leak, just no edge.
3. **`at_or_above_p95` boolean retired → 2000-seed p+CI.** 20/72 binding cells sit at
   one-sided sign-p ≤ 0.15; the strongest at p=0.017–0.043. Directional content is real in the
   mid-threshold BTC cells — the 25-seed P95 bar had mislabelled it "fail".

**The one thing that did NOT change:** net-of-cost, **zero cells and zero subsets** resolve
above zero on the embargoed band. Costs + funding bind at these hold lengths. So the family
shows a **real but sub-cost gross edge**, not a deployable one.

---

## Data-VALIDITY attestations (HARD — kept separate from the value layers)
These stay blocking; a failure means *fix the emission*, not *no edge*. All pass on the reused
emission (validity/provenance set retained in `results/`).

| Attestation | Result |
|---|---|
| Estimand reconciliation (gate v2) | PASS 108/108; max abs 8.2e-12 bps; coverage BTC+ETH+SOL |
| Emission fence (strict, < holdout_start) | PASS 72/72 binding after boundary-mark trim |
| Boundary-mark trim (holdout-adjacent) | receipt `boundary_trim_receipt.json`; last bar 2025-01-07 23:59; 0 trades, 0 data past boundary |
| Cadence coverage (LOW-only pin) | PASS — 108 emitted, 0 HIGH-shaped |
| Pin hash `abbb1842…` CLS-FILTER | PASS |
| Causal ≤ t−1 / non-STUB fence | PASS (design §14, gate v2) |

The design §8 gate-schedule derangement is a **within-sample attribution** control (entries stay
causal ≤ t−1); under INFR-016 §4c it is a **report layer** (below), not a hard leak gate. No
`future_destroy` control survived (none applies here — this is timing/alignment attribution).

---

## Layer 1 — Pre-search cost floor & breakeven (per cell)
Reported per cell; never a park gate. Binding median gross **2.77 bps/trade** vs measured
breakeven ~13–15 bps (taker + GAP + funding). 13/72 binding cells clear breakeven on the
full-window replay; 59 sit below. Entire binding mass is NOT sub-breakeven, so the XENA-003
park rule was not triggered. Full table: `layer_tables.md` (layer `cost_floor`).

## Layer 2 — Leg count & power (per cell) — retires `n_legs_floor` veto
Every binding cell is leg-rich over the full 2.46y window (min 119 / p50 463 / max 1857 legs).
Power is *reported*, never a floor veto. Note the **seam**: full-window leg counts are large,
but the **embargoed stage-2 band alone** thins each cell (top cells 17–89 legs), and per-leg
crypto vol is high (260–785 bps), so the full-window MDE labels the mid-threshold cells
"UNPOWERED" even though the studentized band LCB is positive (different estimator; both reported).

## Layer 3 — LAHC search + ranking-fold stability (all 10 finalists)
12 restarts, 1747 evals, 10 distinct terminals. In-search F 26.6–70.7 (median 61.5). **Every
finalist lives in H64 × vol≥1.5 × high-ADX** — the design's predeclared-UNPOWERED sparse corner
(§10). Ranking-fold `worst_F` is **negative for all 10** ranked subsets; fold Jaccard median 0.0
→ unstable selection, no shared structure across folds. Classic overfit signature: high search F
→ collapses out-of-band. This is *why* the top-1 pick is unreliable.

## Layer 4 — Stage-2 gross/net bounds, embargoed band (ALL cells + subsets) — retires `one_subset`
Embargoed gate band 2024-07-10 → 2025-01-08 (in TEST; spent — exploratory). Studentized leg
bootstrap (block_legs=1, n_boot 200). Full 72-cell + 10-subset table in `layer_tables.md`.

**Cells with positive GROSS LCB (5 of 72):**

| Cell | gross point | gross LCB | net point | **net LCB** | n_legs |
|---|---|---|---|---|---|
| BTC DI_ADX·VOL v1.25/adx25/H64 | 99.6 | **+17.5** | 81.8 | −4.6 | 34 |
| BTC DI_ADX·VOL v1.1/adx25/H64 | 58.0 | **+9.5** | 39.9 | −7.0 | 65 |
| BTC DI_ADX·VOL v1.25/adx25/H32 | 42.8 | **+7.8** | 26.0 | −17.8 | 64 |
| BTC DI_ADX·VOL v1.1/adx20/H64 | 51.4 | **+3.7** | 33.6 | −12.3 | 78 |
| BTC DI·VOL v1.1/adxna/H64 | 42.9 | **+1.5** | 24.9 | −15.7 | 89 |

**Net-of-cost: ZERO cells and ZERO subsets have net LCB > 0.** Best net point is +81.8
(v1.25/adx25/H64) but its net LCB is −4.6 — closest to zero, still below. Costs + funding erase
the gross edge at 8–16h holds.

**The binder's certified top-1** `BTC v1.5/adx30/H64`: gross point −13.2, **LCB −123.2** (se 71.8,
n 18), net LCB −140.5 — the *worst* corner, not representative of the family.

## Layer 5a — Sign battery (2000 seeds) — retires `at_or_above_p95` boolean
Rademacher sign-scramble on the fixed entry schedule; effect + one-sided p + CI. Across 72
binding cells: **20 at p ≤ 0.15, 40 at p ≤ 0.35**, median p 0.279. Strongest directional
content is exactly the mid-threshold BTC adx25 cells. **Label is structural only**
(UNPOWERED / CONTRADICTED / —); the one-sided p carries the strength and the operator reads it —
no STRONG/SUGGESTIVE/WASH cutpoint label (INFR-016 follow-up 2026-07-19: a hardcoded-p label
re-imports the L-32 threshold trap in miniature; the number is the honest read).

| Cell | raw med gross | one-sided p | structural label |
|---|---|---|---|
| BTC DI_ADX·VOL v1.25/adx25/H32 | 10.8 | **0.017** | — (powered, +sign) |
| BTC DI_ADX·VOL v1.25/adx25/H64 | 22.2 | **0.043** | — (powered, +sign) |
| BTC DI_ADX·VOL v1.1/adx25/H64 | 9.7 | 0.179 | — (powered, +sign) |
| SOL DI·VOL v1.5/adxna/H64 | 24.9 | 0.224 | — (powered, +sign) |
| BTC DI_ADX·VOL v1.5/adx25/H64 (#2) | 10.7 | 0.232 | — (powered, +sign) |
| BTC DI_ADX·VOL v1.5/adx30/H64 (top-1) | 1.0 | 0.441 | — (powered, +sign) |

Reading the numbers (no label): the two BTC `adx25` H32/H64 cells sit at p 0.017–0.043 — well
inside the sign null's tail, real direction content. The mid-p cells (0.18–0.23) reproduce the
corrected baseline (SOL / BTC#2). The top-1's p=0.441 sits mid-null — no direction content, as
expected for a ~1 bps raw edge. 23 of 72 cells are CONTRADICTED (wrong-sign raw); the remaining
49 are positive-sign with the p read directly.

## Layer 5b — Attribution derangement (collapse fraction) — retires `hard_fail_leak`
Block-derangement on the 15m open grid (blocks ≥ 16h = max hold; L-28 zero-fixed-point; 25-seed
battery). Reports how much edge is timing/construction-attributable; operator judges. For the
cells with a real raw edge, collapse is high (edge IS the gate construction, not base drift):

| Cell | collapse median | p05–p95 |
|---|---|---|
| BTC DI_ADX·VOL v1.25/adx25/H64 | 0.96 | 0.54–1.49 |
| BTC DI_ADX·VOL v1.25/adx25/H32 | 0.92 | 0.43–1.31 |
| BTC DI_ADX·VOL v1.1/adx25/H64 | 0.87 | 0.20–1.47 |
| SOL DI·VOL v1.5/adxna/H64 | 0.78 | −0.37–2.84 |
| BTC DI_ADX·VOL v1.5/adx30/H64 (top-1) | 0.90 | **−13.1–16.3** (raw≈1 bps: undefined-noisy) |

The old "top-1 leak collapse 0.14" was an artifact of dividing by a ~1 bps raw edge. With the
edge essentially zero, the collapse fraction is meaningless (band ±16). Not a leak — no edge.
For cells with a real edge, high collapse means the edge is **gate-attributable**, not base drift.

## Layer 6 — Cost/funding sensitivity, spread routing, net deployability
- **Net deployability (the binding read):** every cell's net LCB ≤ 0 on the embargoed band. The
  gross→net gap is ~18 bps/round-trip (taker + GAP spread + funding). At 8–16h holds the
  edge that exists gross does not survive cost.
- **Spread routing (T1):** per-symbol spread pin deferred; a conservative GAP (5 bps) is folded
  into breakeven. BTC/SOL 4h/15m gross edges (best cell gross point ~100 bps) exceed the 3× GAP
  scale, so the reads are not spread-undecidable at the gross level; the kill is funding+taker,
  not micro-spread. MBP confirm (T2) is deferred and moot here (net negative regardless).
- **Funding** binds at XENA (family decision) and is the dominant slice of the ~18 bps gap at
  these hold lengths.

## ETH disclosure (off the binding path)
12 ETH `v1.1` cells fail the candidate gate's `oracle_smoke` (`NaN→int` on the densest streams);
estimand gate passes them (data sound). ETH is disclosure-only and never entered search or
stage-2. Reported, not blocking.

---

## Recommended (non-final) read — operator decides
**Exploratory, in-sample, NOT deployable.** Under the honest layer framing:
- **A real, gate-attributable, sign-null-clearing GROSS edge exists** on BTC mid-threshold
  `DI_ADX×VOL_HI adx25` H32/H64 holds (embargoed gross LCB +8 to +18; sign p 0.02–0.05;
  derangement collapse ~0.9). This is a genuine finding the old top-1 framing hid.
- **Net-of-cost it does not resolve above zero** — no cell, no subset. Costs + funding at 8–16h
  holds are the wall. Best net LCB is −4.6 (tantalisingly close, one cell).
- **SOL v1.5/adxna/H64** looked suggestive on the full window (24.9 bps, p=0.224) but is
  **strongly negative on the embargoed band** (gross point −154) — its edge does not transfer.
- The binder's certified top-1 is a **selection artifact** (worst corner); its "leak" label was
  a near-zero-denominator artifact.

Plain verdict: **the HTF-interaction filter carries a real directional edge on BTC that is too
small to beat cost at these holds.** Not "dead", not "deployable". Follow-ups the operator may
weigh: shorter-cost venues / maker entries, or denser-cadence variants where a smaller edge can
compound — both are NEW designs, not this run. Family status changes only at a checkpoint.
