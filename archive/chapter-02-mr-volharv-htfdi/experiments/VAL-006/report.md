# Experiment Report: VAL-006 — Corrective re-derivation of multi-leg verdicts (critical-017 blast radius)

## Status: ANALYSIS COMPLETE — NOT SUPPORTED (operator verdict 2026-07-05)

**Date**: 2026-07-05
**Type**: VAL (infrastructure/validation) — corrective re-derivation; no candidate-family claim
**Root experiments**: EXP-014b, EXP-014c, EXP-016, EXP-017
**Slots**: 0 · **Counted TEST reads**: 0 (0 spent; corrective re-derivation, no new read) · **Holdout**: sealed, untouched
**Scope**: TRAIN band only — EXP-014b/c emissions end at TRAIN fence by construction (US2000 `analysis_end_utc` 2024-09-10T09:33 == EXP-016 `TRAIN_FENCE`). TEST band: EXP-016's 3 counted reads annotated `SPENT_ON_DEFECT` (ledger-marked). Corrected TEST read needs operator authorization.
**No design.md** — VAL carve-out (entered at analysis stage per operator D2).

---

## Question & Mechanism Summary

**Question.** Which multi-leg (allow/extend/both-leg) claims from EXP-014b, EXP-014c, EXP-016 and EXP-017 survive re-derivation from per-leg truth (`cis_trades.RealizedBps`) via the canonical `xen.adjudication` estimands, after critical-017 invalidated the per-bar series?

**Mechanism.** EXP-016/017's per-bar P&L series was corrupted (critical-017). Prior multi-leg adjudications (EXP-014b/c `NET_ADMIT`/`REJECT_LEAK`; EXP-016 `PERFORMANCE_RETAINED`; EXP-017 A1 Δ) were built on that corrupted foundation. This item re-derives every multi-leg cell from the uncorrupted per-leg ledger — the conserved quantity — via `xen.adjudication.per_leg_net` (canonical leg-building + moving-block bootstrap over time-ordered legs/episodes, block 5, 10k draws, seed 20260704). All code in `analysis_code/`; zero imports from any experiment's `code/`.

---

## Scope

| Dimension | Detail |
|-----------|--------|
| Roots | 25 family roots (23 from EXP-014b/c + 2 from EXP-016) |
| Raw cells | 207 (TRAIN) + 46 shift-twin cells |
| Instruments | 11 |
| Cost | Frozen per-instrument 4h costs (FP-001 at barrier P4 state) |
| Holdout | Sealed — every root fence-checked (last bar ≤ `analysis_end_utc`); no TEST-band bar read |
| Emissions | Data from engine `data/strategy_runs/` — price-primary, no signal regenerated |

---

## Integrity Gates


All gates PASS (VAL requirements per D2 carve-out).

| Check | Result | Evidence |
|-------|--------|----------|
| Estimand validation, all cells | **PASS** (25 roots, 271 cells) | `results/estimand_validation.json`; every cell reconciles per-bar↔per-leg within 1 bps (typ. ~1e-12) |
| Provenance — fills physical | **PASS** (spot) | Own fill-in-bar check: US2000 e0/e3 extend z15 entry+exit breach 0.0000 (n=1317 each); blmkt US500 0.0000 (n=58); full-sweep previously run per-cell in 014b/c |
| Leak tripwire | **DISCLOSED-ONLY** | Original phase-shift/permute controls documented invalid/vacuous (B-3/B-6); corrected-estimand shift disclosure in §4 P3 — informative, not a gate |
| Holdout | **PASS** | Every root fence-checked; no TEST-band bar read anywhere |
| Price-primary | **PASS** | All numbers from engine emissions; no signal regenerated |
| Shared-code boundary | **PASS** | `check_no_local_accounting(analysis_code)` → ok; all estimands via `xen.adjudication` |

**Gate incidents** (findings, not blockers — handled):
- **`partial_abort` legs**: 2 legs (bllim-z15 AUDUSD/US2000 ledgers) with no exit fill and NaN `RealizedBps` — NaN-poisoned totals until `xen.adjudication` learned to exclude+disclose them (`n_aborted`). Legacy path silently absorbed these.
- **Mixed-symbol censored marking**: both-leg ledgers carry mate-symbol legs; marking a censored EURUSD leg to USDJPY opened fabricated ±10⁶-bps artifacts. Fixed with `own_symbol` guard.

---

## Key Evidence

### Census Headline (corrected estimand, TRAIN)

| Bucket | Cells |
|--------|-------|
| Per-leg mean CI_low > 0 | **52** |
| …of which e1 (frozen-TP-only — survivorship, see P1) | **44** |
| …of which legitimate candidates | **8** |
| Per-leg mean CI_high < 0 | **27** |
| Total net < 0 (of 207) | **108** |

**Corrected 8 legitimate CI-positive cells:**

| Exit | Arm | Z | Inst | n_legs | Net/leg [CI] | Epi CI_low | Peak legs | Occupancy |
|------|-----|---|------|--------|--------------|------------|-----------|-----------|
| e0 | extend | z15 | US2000 | 1317 | +56.8 [+31.5, +82.6] | **+42.5** | 47 | 0.54 |
| e0 | extend | z20 | US2000 | 771 | +74.5 [+39.0, +110] | −20.6 | 34 | 0.41 |
| e0 | allow | z20 | US2000 | 442 | +78.8 [+42.6, +115] | **+128.7** | 18 | 0.41 |
| e0 | allow | z15 | US2000 | 642 | +32.1 [+0.5, +64] | −80.0 | 20 | 0.53 |
| e2 | extend | z20 | US2000 | 771 | +56.3 [+12.5, +100] | +45.3 | 28 | 0.75 |
| e0 | extend | z20 | JP225 | 542 | +48.4 [+9.1, +88] | −85.6 | 40 | 0.34 |
| e0 | blmkt | z15 | US500 | 232 | +41.4 [+2.3, +80] | +14.5 | 4 | n/a |
| e0 | blmkt | z20 | US500 | 156 | +56.1 [+5.1, +107] | +33.8 | 4 | n/a |

### Probes

**P1 — e1 positives are survivorship artifacts.** e1 has no SL and no time-stop: legs exit only on frozen TP fill → completed legs are **winners by construction**; losers ride to fence as "censored" (up to 194/388 legs, USDJPY z15). Including censored MTM: **16 of 44 e1 cells flip sign outright** (e.g. US500 e1/extend/z20: realized +185.8k, censored MTM −336.3k → honest **−150.9k bps**). Remainder shrink to arbitrary residues of unbounded-inventory grid. **No e1 cell is evidence of edge.**

**P2 — Exposure normalisation deflates the legitimate 8.** Per exposure-bar and peak concurrent exposure:
- Best cell (e0/allow/z20 US2000): 2.8 bps/exposure-bar, ~5.1%/yr on peak
- e0/extend/z15 US2000: 2.2 bps/exposure-bar, ~4.2%/yr, maxDD −29.9k bps (≈ −64% of 47-leg capital base)
- JP225 e0/z20: 1.5 bps/exposure-bar, ~1.7%/yr, episode CI **not** positive
- blmkt US500: 0.8-1.0 bps/exposure-bar, 4 legs peak → ~5.7-6.2%/yr — cleanest profile

**P3 — Corrected shift-collapse is incoherent noise.** Per-leg shift/raw fractions: **−3.0 to +13.8** (not 50-85%). Shifted twin frequently *beats* raw (US2000 e3/z15: raw +4.5 vs shift +22.9/leg). Prior "50-85% survives the shift" was corrupted-series artifact.

**P4 — The named candidate dies.** US2000 e3/extend/z15: gross **+9.53 bps/leg, CI [−15.9, +32.0]** (n=1317) — indistinguishable from zero **even at zero cost**. No cost at which CI_low > 0. EXP-016's `PERFORMANCE_RETAINED`, already void for spending reads on corrupted series, has no valid TRAIN-side edge behind it.

**P5 — No year stability.** Surviving cluster is 2021-22-concentrated. 2023 negative in **5/6 probed cells** (US2000 e0/extend/z15: 2021 +23.5k, 2022 +51.9k, 2023 **−11.1k**, 2024 +10.5k). 2022 dislocation regime supplies bulk of P&L.


---

## Evidence FOR

1. **Clean principled census**: 207 cells re-derived via canonical `xen.adjudication`; per-bar↔per-leg reconciliation ~1e-12; fills physical (0.0000 breach on spot-check).
2. **8 legitimate CI-positive survivors** survive the e1 survivorship filter — US2000 e0/e2 cluster (5 cells, consistent CI_low>0 across exits/arms/z) and US500 both-leg cluster (all 4 both-leg variants positive: +9.6k/+8.8k/+6.8k/+5.0k total net, bounded 4-leg peak exposure).
3. **Both-leg arms hold up**: US500 blmkt cells CI-positive per leg; bounded exposure (peak 4 legs) makes these structurally the cleanest positive in the census.
4. **Accounting, not artifact**: fills physical, reconciliation exact, positives net of frozen costs.

## Evidence AGAINST

1. **Prior record collapse**: corrected census leaves 8/207 legitimate CI-positive; 44 e1 survivorship artifacts; AUDUSD (−7…−14/leg) and NZDUSD (−25…−33/leg) extend confirmed outright losers.
2. **Named candidate dead** (P4): US2000 e3/extend/z15 CI [−15.9, +32.0] — ≈0 even at zero cost.
3. **Small magnitudes** (P2): 1-3 bps/exposure-bar, 2-5%/yr on peak exposure, against single-unit maxDD −10k…−30k bps.
4. **Regime-concentrated** (P5): 2022 supplies bulk; 2023 negative in 5/6 probed cells.
5. **No mechanism story**: corrected shift (P3) incoherent noise (−3.0 to +13.8 fractions); CF-MR-005 mechanism question open on thinner base.
6. **Multiple-comparison context**: 8/207 CI-positive at α=0.05 with heavy cross-cell correlation ≈ expected chance level (~10 false positives).

## Operator Verdict

**NOT SUPPORTED** (recorded 2026-07-05)

*"The prior multi-leg record does not survive re-derivation."*

| Prior adjudication | Corrected status |
|--------------------|------------------|
| EXP-014b/c multi-leg `NET_ADMIT`/`REJECT_LEAK` | **Superseded** — corrected per §3 (most cells null/negative; 8 CI-positive remainder listed) |
| EXP-016 `PERFORMANCE_RETAINED` | **No valid basis** — reads spent-on-defect; no TRAIN edge in the read arm |
| EXP-017 A1 Δ | **Corrupted net side confirmed** — episode objects must be rebuilt from `xen.adjudication.build_episodes` if rerun |

Analyst recommendation and operator verdict agree ([analysis.md](analysis.md) §8).

## GATE Block (post-exec inline governance)

| Gate | Verdict |
|------|---------|
| blocking_pass (271 cells, 25 roots) | **PASS** |
| check_no_local_accounting | **PASS** |
| Holdout seal | **PASS** (no TEST read consumed) |
| Price-primary provenance | **PASS** |
| Fills physical (spot) | **PASS** (0.0000 breach) |
| Registry disposition | **N/A** — corrective re-derivation; no candidate-family claim, no TEST read, no status transition |

**GATE: APPROVE** — all checks pass. No Critical or Warning findings. 

The report records: (1) operator verdict NOT SUPPORTED recorded ✓; (2) analysis completed with evidence for/against ✓; (3) integrity gate PASS ✓; (4) holdout sealed ✓; (5) registry disposition stated (N/A) ✓; (6) index updates applied (python/experiments/INDEX.md + docs/experiments-docs/INDEX.md Current Infrastructure Tasks) ✓.

**Governance note**: VAL-006 is a VAL item (infrastructure/validation), not a candidate-family experiment. No design.md exists (VAL carve-out — entered at analysis stage per operator D2). All analysis code in `analysis_code/` is self-contained; zero imports from any experiment's `code/`.

## Residual & Follow-up

**Residual (WASH-to-weak-positive, unadjudicated):**
- US2000 e0/e2 cluster (5 cells, ~2-5%/yr on peak exposure, 2022-concentrated)
- US500 both-leg cluster (all 4 variants positive, bounded 4-leg peak, cleanest exposure profile)

**Would change if:** a predeclared, exposure-honest read of the US2000/US500 clusters on fresh data (or operator-authorized TEST band) showed the 2023 drawdown to be non-structural.

**Suggested probes (operator-gated):**
1. Episode-level deep-dive on US2000 e0/allow/z20 (strongest cell: epi CI [+128.7, …], 88 episodes).
2. US500 both-leg mechanism look (4-leg bounded exposure — cheap to reason about).
3. Authorize a corrected TEST-band read policy before anything touches TEST.

**Anomalies:**
- e1 engine design (no loss exit) makes realized-only statistics meaningless. If e1 revisited, estimand must be inventory-marked.
- 2 `partial_abort` legs + 2 missing US500 emissions (e2/extend/z15, e3/allow/z20 roots have 10 cells) — surfaced by manifest; harmless here.
- JP225 e0/z20: leg-CI-positive but episode-CI-negative — episode aggregation absorbs positive legs; object-identity question for follow-up.

## Artifacts

[analysis.md](analysis.md) · [analysis_code/run_gate.py](analysis_code/run_gate.py) · [analysis_code/census.py](analysis_code/census.py) · [analysis_code/probes.py](analysis_code/probes.py) · [results/estimand_validation.json](results/estimand_validation.json) · [results/census.parquet](results/census.parquet) · [results/census_summary.json](results/census_summary.json) · [results/probes_p1_p2.parquet](results/probes_p1_p2.parquet) · [results/probes_p3_shift.parquet](results/probes_p3_shift.parquet) · [results/probes_p4_us2000.json](results/probes_p4_us2000.json) · [plots/](plots/) · Emissions: `data/strategy_runs/` (EXP-014b/c/016)
