# EXP-011 — E7 Referee 15m-Domain Extension (referee renew, D-referee)

**Branch:** `main`. **Checkpoint:** Phase-003 CONC-1 (Track 2 critical path; `docs/experiments-docs/checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/design.md`). **Classification:** **analysis-only** (synthetic position substrates + planted edges + frozen referee primitives on aggregated 15m timebar extracts; generates **no** price edge — it calibrates a gate). **Reads/slots:** 0 counted TEST reads, 0 candidate slots; global holdout sealed. **Consumes (FROZEN, byte-unchanged):** E5 §10.3a `referee_adaptive.gate_stack_adaptive`/`adaptive_row` (sha256 `b4fd6cb1…ae847`), E6 `referee_pstar.gate_stack_pstar` (sha256 `1fd06b28…4f23`), `referee_calibration.DomainSpec`/battery. **Reuses:** the E2 synthetic-positive + dogfood battery (EXP-002 `edge_shapes`), the E3a 3-arm DET harness (EXP-003), the E4 sweep/robustness driver (EXP-004).

## Question (one, falsifiable)

**Does the frozen renewed referee (§10.3a q\*=0.75 + E6 P\*-gate), extended by a new 15m trading domain whose calibration constants are derived candidate-blind, retain FPR-control AND finite power on the 15m domain — licensing a freeze of the 15m-capable referee — while leaving every 1h/4h verdict bit-identical to E5/E6?**

Concretely, on 16 instruments × 15m (16 new strata), at the frozen operating point: is the 15m dogfood-negative FPR controlled (Wilson-upper ≤ frozen control, E4/E5 `MIN_FPR_PASSES=2` / `2α` rule) **and** is there a finite 15m MDE on the shapes the frozen gate is built to see (DENSE at minimum; the §10.3a adaptive legs' STATE/SPARSE recovery retained) — with the future-destroying control collapsing every planted 15m detection? If yes → freeze + hash-pin the 15m-extended referee. If 15m FPR is uncontrolled, or a shape the gate should see has **no finite MDE** structurally (a near-impossible leg at 15m, L-12 §2), or a future-destroyed edge survives → **do NOT freeze**; record + diagnose.

**Why now.** EXP-010 (CONC-1 T1) is done; Track 2 (T2a 14 S3_DETREND single-symbol + T2b 10 S5_SPREAD multi-symbol, all **exec-15m**) is blocked because the frozen referee has no 15m domain (`ADAPTIVE_DOMAINS=("1h","4h")`). E7 delivers that domain. **L-12 discipline (the whole reason the referee-renew ladder exists):** the referee is FROZEN — a domain extension is itself a predeclared experiment, FPR-recalibrated on the dogfood-negative + synthetic-positive battery and **frozen before it adjudicates any CF-MR-003 exec-15m cell**; it must **not** be tuned on the candidate it will judge.

## What E7 changes (exact code surface) — and what it must NOT

E7 **adds one domain row** to three frozen dicts + one tuple. The stack **logic** is byte-unchanged (dict lookups keyed by domain; a new `"15m"` key leaves `"1h"`/`"4h"` byte-identical).

| Target (`python/src/xen/…`) | Change | Frozen / unchanged |
|---|---|---|
| `referee_calibration.DOMAIN_SPECS` | add `"15m": DomainSpec("15m", 15, 0.90, min_effective_n=N15, min_state_count=S15)` | `1h`/`4h`/`5m` rows untouched |
| `referee_calibration.MATERIALITY_BPS` | add `"15m": M15` | `1h=1.5`, `4h=3.0` untouched |
| `referee_adaptive.ROUND_TRIP_COST_BPS_17` | add a `"15m"` entry per instrument | every `1h`/`4h` value untouched |
| `referee_adaptive.ADAPTIVE_DOMAINS` | `("1h","4h") → ("15m","1h","4h")` | — |
| §10.3a / E6 gate-stack **logic**, `q*`, `Q_STUD_MIN`, `ALPHA`, `POWER_TARGET`, L1/coverage legs | **NONE** | byte-frozen (regression anchor below) |

**No new referee logic.** No leg is added, removed, or re-thresholded. E7 is a *domain-parameter* extension + its calibration, not a gate redesign.

## Derivation rule for each 15m constant (candidate-blind, mechanical — NOT a magic constant)

Every constant gets (a) a **mechanical prior** from the domain's own scale (never from CF-MR-003 events), (b) **battery confirmation** that the prior yields the FPR-control + finite-power property the frozen 1h/4h domains earned, and (c) a **pre-registered sensitivity band** shown to leave the FPR/DET verdict invariant. This satisfies the gate-threshold-calibration governance check three ways over.

| Constant | Frozen anchors | Mechanical prior (rule) | Sensitivity band |
|---|---|---|---|
| `MATERIALITY_BPS["15m"]` = **M15** | 5m 0.5 · 1h 1.5 · 4h 3.0 | **√-period scaling.** materiality ≈ `k·√(period_min)` reproduces the frozen 1h/4h (`k=1.5/√60=0.1936`; `0.1936·√240=3.0` ✓) and 5m to rounding (`0.1936·√5=0.43≈0.5`). → **M15 = 0.1936·√15 = 0.75**. Economic reading: a per-bar bps floor scaling with the typical per-bar move (vol ~ √time). | {0.5, **0.75**, 1.0} |
| `DOMAIN_SPECS["15m"].min_effective_n` = **N15** | 5m 120 · 1h 60 · 4h 25 | **log-period interpolation** between 5m and 1h: `frac=(ln15−ln5)/(ln60−ln5)=0.442`; `120+0.442·(60−120)=93.5` → **N15 = 90**. | {75, **90**, 105} |
| `DOMAIN_SPECS["15m"].min_state_count` = **S15** | 5m 30 · 1h 20 · 4h 8 | same log-interp: `30+0.442·(20−30)=25.6` → **S15 = 25**. Floor on per-direction episode count guaranteeing finite sub-pop MDE. | {20, **25**, 30} |
| `min_coverage` | 1h/4h = 0.90 | **inherit 0.90** (domain-construction fence, dataset-reference.md). Not swept. | — |
| `ROUND_TRIP_COST_BPS_17["…"]["15m"]` | 1h==4h per instrument (domain-invariant) | **inherit the per-instrument round-trip** (spread+commission is a per-*trade* charge, domain-invariant). E1 (EXP-001) found the per-*held-bar* cost over-charges turnover — round-trip is per-trade → **unaffected**; the higher 15m turnover is handled by the referee's E1 amortized turnover accounting, not this constant. | inheritance is the rule; no band (turnover disclosed) |

The battery (below) is the **binding** calibration: if the mechanical prior fails FPR-control or finite-power on 15m, the licensed value is the band member that restores the frozen-domain property — recorded honestly, still candidate-blind (chosen on synthetic + dogfood, never on CF-MR-003).

## Data views / substrate (reuse E2/E4 exactly, at 15m)

- **Real returns:** open-to-open `≤t-1` (E0) per instrument × **15m**, **first-70% analysis slice only**, 16-instrument 5-year era (DE30 absent). 15m domain bars via `aggregate_ohlc(min_coverage=0.90)` + the analysis-boundary fence (dataset-reference.md "Deployed domain-construction fence"). Holdout never loaded.
- **Real-bar dogfood** additionally restricted to the **first-49% TRAIN region** (`int(int(N·0.7)·0.7)`) — the analysis-TEST band + final-30% holdout are **never sliced** (EXP-002/004 precedent; a calibration/dogfood exposure is a **disclosure**, not a counted read).
- **Synthetic position substrates (per shape):** blockwise-persistent at the 15m episode length `L₁₅` (`estimate_block_length` on the 15m train P&L, frozen rule) for DENSE/TAIL/STATE; the sparse low-activity substrate for SPARSE. Shapes DENSE / TAIL / SPARSE / STATE, **matched-magnitude** (mean drift = `e` over each shape's declared denominator, L-08/L-11); constants `f_tail=0.10`, `a_sparse=0.06`, `frac_A=0.5` reused verbatim from E2 (pre-registered, never tuned on outcomes).
- **Null families (dogfood-negative):** block-permute returns (L-07); reblock-random positions on real 15m returns; causally-lagged real dogfood signals `donchian_breakout_positions` + `ma_crossover_positions(20,50)`; **plus the E4 R3 skew-stressed null** (right-skew/fat-tail, a genuine no-edge null — verify frozen arms also ≈0 on it). No planted edge.

## Method — the E2/E3a/E4 battery, re-pointed at the 15m domain

Reuse the EXP-003 3-arm harness (`frozen` / `frozen_amortized` / `adaptive` = §10.3a) + the E6 P\*-gate, at the **E5-frozen operating point** (`q*=0.75`, `Q_STUD_MIN=Φ⁻¹(0.75)=0.6745`, `N_BOOTSTRAP=500`, `ALPHA=0.05`, `MIN_EPISODES_SUBPOP=5`). Wrap in an E7 driver that sets `domain="15m"` with the derived `DomainSpec`/materiality/cost, per (band-point × stratum × shape):

1. **15m FPR** per stratum (16) per null family (4) — detection rate under each no-edge null; Wilson half-width + explicit draw count (`referee_calibration.wilson_interval`/`verdict_rate_rows`; never "≈0"). Binds on dogfood + abstract + skew nulls jointly.
2. **15m power / MDE** per shape — detection rate over `EDGE_GRID_BPS` (0→32); **MDE = smallest `e>0` with detection ≥ `POWER_TARGET=0.5`**; no finite MDE on the grid ⇒ **UNPOWERED** for that cell (reported, **never** "fail" — L-12 §2).
3. **15m blindness/recovery classification** per stratum × shape: DETECTED / UNPOWERED / DENSE-ONLY-BLIND — confirms the §10.3a adaptive legs carry their E3a STATE/SPARSE recovery into 15m (or localizes where they don't).

**Binding endpoints (per stratum — non-pooled, L-03):** the per-(stratum) 15m FPR and the per-(stratum,shape) MDE/UNPOWERED label. **Pooled/aggregate** counts are **disclosure-only** until cross-stratum homogeneity is shown. **Freeze-adjudication FPR rule (E4/E5, candidate-blind):** a stratum's dogfood-FPR is "broken" only if it clears **`MIN_FPR_PASSES=2`** at `2α` (a single 1/N Wilson artifact is not a break — the E4 lesson).

## Regression anchor (binding correctness gate — run FIRST)

Adding the `"15m"` key must not perturb 1h/4h. Re-run the **E5 (§10.3a) + E6 (P\*-gate) 32-stratum (16×{1h,4h}) suite** through the 15m-extended modules — it **must reproduce E5/E6 bit-for-bit**: 32/32 DET_DOMINANT, dogfood FPR 0/32, E6 Arm-R reduction identity 32/32 bit-identical, future-destroy `fd_max≤0.050`, and the `referee_adaptive`/`referee_pstar`/`referee_calibration` gate-stack hashes byte-unchanged **except** the additive `15m` dict rows. A mismatch ⇒ the extension leaked into 1h/4h ⇒ **fix + rerun before any 15m result is interpreted.** (This is the whole safety claim of "adds a domain, changes nothing else.")

## Leak tripwire(s) — applied at every band-point

1. **Future-destroy collapse (critical, incl. the studentized sub-pop path):** plant shape-`e` at 15m, **block-permute the returns** (destroy position↔return alignment), re-run adaptive + P\*-gate — 15m detection **must collapse to FPR**. A surviving future-destroyed pass at any band-point = noise-mining ⇒ **REJECT-class** (the 15m calibration is compromised; do not freeze).
2. **Dogfood-negative = standing FPR null:** the four no-edge null families must stay controlled (a null family that *passes* materially is a 15m calibration break, not a positive).
3. **No-plant guard:** `e=0` / no drift ⇒ 15m PASS rate ≈ FPR on every shape (no phantom positive from the 15m substrate or the new constants).

## Predeclared interpretation criteria

- **FREEZE LICENSED (15m) — success:** on the 16 15m strata at the mechanical-prior constants, **(i)** dogfood + abstract + skew FPR not Wilson-resolved above frozen control (`MIN_FPR_PASSES=2`/`2α`); **(ii)** DENSE has a finite 15m MDE on every powered stratum, and the §10.3a adaptive STATE/SPARSE recovery is retained (not newly UNPOWERED vs the E2/E3a 1h pattern); **(iii)** future-destroy collapses everywhere; **(iv)** the regression anchor is bit-identical; **(v)** the verdict is invariant across the sensitivity band. → **freeze + hash-pin** the 15m-extended referee (new `freeze_manifest.json` + byte-freeze check), unblocking EXP-010 T2a/T2b.
- **RANGE-BOUNDED (partial, still licenses freeze):** the mechanical prior holds but a band extreme degrades (e.g. `S15=20` widens FPR toward control on *k* strata, or `N15=105` suppresses recovery on *m* strata) → freeze at the **validated prior** with the safe band recorded. Not freeze-blocking unless the prior itself fails.
- **FREEZE NOT LICENSED (failure):** 15m dogfood-FPR Wilson-resolved above control (a near-impossible leg / miscalibrated floor at 15m, L-12 §2/§3), OR DENSE has no finite 15m MDE structurally, OR a future-destroyed edge survives, OR the regression anchor breaks → **do NOT freeze**; record the diagnosis (which constant / which leg), route the fix, rerun. T2a/T2b stay blocked.
- **Inconclusive:** bootstrap/seed noise swamps the DETECTED/UNPOWERED or FPR boundary at `N_BOOTSTRAP=500`/`N_PLANT`/`N_NULL` → raise resamples (E4 `N_BOOTSTRAP=1000` fallback) or report the bound (UNPOWERED-with-CI); do not over-claim the freeze.

**Shape-aware read (L-12 §1):** report 15m `MDE(shape) − MDE(DENSE)` per stratum and the UNPOWERED-rate per shape across the 16 strata; relate to instrument cost and `L₁₅`. The E2 finding was that the *frozen conjunctive* gate is SPARSE/STATE-blind and §10.3a (adaptive) recovers it — E7 must show that recovery survives the domain change, not just DENSE detection.

## Complexity budget (comparative — analogous to E2/E4)

- **New code modules: 0–1** — an E7 driver in `code/` that imports the EXP-003 3-arm harness + E6 P\*-gate + the E4 sweep scaffolding and re-runs them at `domain="15m"` over the derived constants + sensitivity band; the 15m parameter-derivation helper (mechanical rules above); and — **only after FREEZE LICENSED** — the additive edits to `DOMAIN_SPECS`/`MATERIALITY_BPS`/`ROUND_TRIP_COST_BPS_17`/`ADAPTIVE_DOMAINS` + `freeze_manifest.json`. Reuses `edge_shapes`, `wilson_interval`, `permuted_returns`, the substrate, the arm functions. No new referee leg.
- **Stat tests: 3** — (1) 15m FPR per stratum × null family; (2) 15m MDE-curve per stratum × shape; (3) sensitivity-band invariance (FPR/DET across the {M15,N15,S15} bands). Within comparative (2–4).
- **Visualisations: 3** — (1) 15m blindness/recovery map (stratum × shape → MDE/UNPOWERED heatmap); (2) 15m FPR-vs-stratum with Wilson bars (4 null families, control line); (3) sensitivity-band verdict surface (constant-band × stratum). Regression-anchor reproduction is a table disclosure. Within comparative (3–5).
- **One falsifiable question** (freeze licensed: yes / range-bounded / no). One rung.

## Metric denominators / zero-baseline

MDE in bps on `EDGE_GRID_BPS` (UNPOWERED=inf, reported never failed). FPR a Wilson-bounded proportion over a stated draw count. Each shape's mean-edge denominator fixed per the E2 menu (active bars; sparse-active; state-A-active). `e=0` / no-plant = the null guard. No percentage-of-zero metrics.

## Implementation safety constraints (for `experiment-developer`)

- **Regression anchor first, bit-identical:** prove 32/32 1h/4h reproduction of E5/E6 before interpreting any 15m cell. The additive dict rows must be the *only* diff to the frozen modules (byte-freeze check on the stack logic + hashes).
- **Candidate-blindness (L-12, hard guard):** the 15m constants are derived from the mechanical rules + the synthetic/dogfood battery **only** — no code path reads CF-MR-003 S3/S5 exec-15m events, and no CF-MR-003 timebar/event file is loaded. The freeze is written **before** any T2a/T2b adjudication.
- **Frozen legs untouched:** §10.3a/E6 stack logic, `q*`, `Q_STUD_MIN`, `ALPHA`, `POWER_TARGET`, L1/coverage — byte-frozen. E7 injects a domain row only (thread `domain="15m"` + the derived `DomainSpec`/materiality/cost; do not edit any gate leg).
- Open-to-open `≤t-1`; first-70% minute slice + domain fence before aggregation; dogfood restricted to first-49% TRAIN; never collect the final 30%; `CloseTime` ordering, no bar-index alignment.
- All shape/null generators **deterministic** under explicit seeds (reused from E2/E4 per draw); matched-magnitude asserted at construction. Reuse `wilson_interval`/`verdict_rate_rows` (no local Wilson). `tqdm` on the (band-point × stratum) loop; bounded `N_PLANT=20`, `N_NULL=80`, `N_BOOTSTRAP∈{500,1000}` predeclared.
- **Freeze mechanics (post-license):** emit `results/freeze_manifest.json` mirroring E5/E6 (operating point + the new 15m `DomainSpec`/materiality/cost + sha256 of the extended `referee_calibration.py`/`referee_adaptive.py`) + a `byte_freeze_check.json` asserting the 1h/4h stack logic + E5/E6 hashes are unchanged. Hash-pin before Stage-5 close.

This experiment extends the frozen referee to a 15m domain and licenses (or withholds) its freeze via the reused dogfood-negative + synthetic-positive battery. It does **not** redesign any gate leg, adjudicate any CF-MR-003 cell, tune any constant on the candidate, or touch the global holdout.

---

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-01)

Checked against `references/governance-constraints.md` + Phase-003 checkpoint (Track 2 = E7/EXP-011, 15m referee) + the D-referee ladder precedents (E2/E4/E5/E6):

- **Single falsifiable question** — freeze the 15m-extended referee: yes / range-bounded / no. The regression anchor + sensitivity band are gates on the *same* question, not new questions. ✓
- **Classification** analysis-only — correct (synthetic substrates + frozen primitives + aggregated 15m timebar extracts; no price→signal, no in-engine run). ✓
- **Holdout** sealed; first-70% minute slice + domain fence; dogfood restricted to first-49% TRAIN; analysis-TEST + final-30% never sliced. **Reads/slots** 0; referee-renew methodological branch (no candidate screened → **no registry precondition**, no TEST-read tally to state). ✓
- **Gate-threshold calibration (scrutinized — the crux)** — every new 15m constant (`M15`, `N15`, `S15`, cost) ships all three governance-accepted justifications: a **mechanical prior** (√-period materiality reproducing frozen 1h/4h to rounding; log-period-interpolated floors; per-trade cost inheritance), **battery confirmation** on the 15m dogfood+synthetic layout, and a **pre-registered sensitivity band** shown to leave the FPR/DET verdict invariant. No magic constant. ✓
- **L-12 candidate-blindness (hard guard)** — constants derived from domain-scale rules + synthetic/dogfood battery only; **no CF-MR-003 exec-15m event is read**; freeze written **before** any T2a/T2b adjudication. This is the entire point of the renew ladder — honored. ✓
- **Frozen-leg discipline** — §10.3a/E6 stack logic, `q*`, `Q_STUD_MIN`, `ALPHA`, `POWER_TARGET`, L1/coverage byte-unchanged; E7 adds only additive domain rows to 3 dicts + 1 tuple. **Regression anchor** (32/32 1h/4h bit-identical to E5/E6, E6 Arm-R reduction identity, hashes unchanged bar the additive rows) is run FIRST and is fix+rerun-blocking. ✓
- **Per-stratum binding** (L-03) — 15m FPR per stratum, MDE per (stratum,shape); pooled disclosure-only. **Shape-aware read** (L-12 §1: §10.3a STATE/SPARSE recovery must survive the domain change, not just DENSE detection). ✓
- **FPR rule** — E4/E5 `MIN_FPR_PASSES=2` / `2α`, candidate-blind (a single Wilson artifact ≠ break). Matched-magnitude shapes + block-permute nulls (L-07/L-08). ✓
- **Leak tripwires (3)** predeclared + applied at every band-point: future-destroy collapse incl. the studentized path (REJECT-class if it survives); dogfood-negative standing FPR null; no-plant guard. ✓
- **Budget** — 0–1 new module (E7 driver reusing the E2/E3a/E4 harness + post-license additive edits/manifest); 3 tests; 3 plots. Within comparative. ✓

**Info (non-blocking):**
1. `min_effective_n`/`min_state_count` frozen anchors (5m/1h/4h) are operator-ratified hand-set values, not a closed formula; the log-period interpolation is a *defensible prior*, and the **battery is the binding calibration** — if the prior fails FPR/power on 15m, the licensed value is the band member restoring the frozen-domain property (recorded honestly, still candidate-blind). The developer should treat the prior as the anchor and the band as the search set, not assume the prior passes.
2. Compute multiplies (band-points × 16 strata × 4 shapes × arms + 4 null families + regression anchor 32 strata). Reuse the E3a early-stop + ProcessPool; the future-destroy control may run at detected-MDE + one super-MDE level per shape (E2 efficiency), collapse requirement unchanged.
3. If FREEZE NOT LICENSED, **T2a/T2b stay blocked** and Phase-003 Track 2 does not advance — surface that outcome to the operator (it changes the critical path), do not silently retry.

No REVISE issues. **Proceed to Stage 2** (build the E7 driver in `code/` reusing the E2/E3a/E4 battery at `domain="15m"` + the mechanical 15m-parameter derivation; the additive module edits + `freeze_manifest.json` are emitted only after FREEZE LICENSED).
