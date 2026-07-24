# SPDR-014 — Report (Zone → mispricing event → post-event MOMO vs MR)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D1` (O3 Group 1)
- **Checkpoint:** `2026-07-23-017-structural-vol-direction-programme`
- **Lane:** SPDR TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Status:** SCREEN COMPLETE (re-emitted + corrected) — **OPERATOR DISPOSITION RECORDED (2026-07-24)**
- **Analyst recommendation:** INCONCLUSIVE — reason class UNPOWERED_NOT_NULL (B-5: unpowered ≠ negative)
- **Operator verdict:** **OPEN SPDR-016 by signed override** (§8.3) — on the coherent SUGGESTIVE leads,
  NOT on a powered residual (0 powered cells; `residual_status` stays NONE). Follow-up residual object /
  policy deferred to 016 design.
- **SPDR-016 gate:** **OPEN by operator override** (`016_start_allowed=true`, `016_start_basis=OPERATOR_OVERRIDE`)
- **Binding analysis of record:** `analysis.md` (this report synthesises it; `screen.md` is subordinate)

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: partial_net overstated vs full cost
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## 1. Question

Given a horizon band from proven absolute-vol / ZZ-magnitude forecasts, does price **breach** that
band at a non-ambient rate, and after breach does the path **continue (MOMO)** or **revert (MR)** with
**conditional residual ≠ ambient** — without assuming either? Residual `r_h` = side-signed
open-to-open bps. Z-VOL width normaliser = `LTF H1 Parkinson EWMA(λ=0.94) × frozen s_symbol`.

---

## 2. Provenance — this is a corrected re-analysis

This report reflects a full redo prompted by two framing faults in the first analysis (adversarial
pooling; judging measured leans against unrealistic expectations). The redo was run neutrally
(per-stratum magnitudes, quantify-not-qualify, B-5) and exposed several bugs that were fixed and the
screen re-emitted. Changes made:

| # | Change | Class |
|---|---|---|
| 1 | Control battery: true derangements (incl. n=2), matched-random ±1 exclusion, causal within-third tripwire re-pair, gate-shuffle 200 seeds | integrity-neutral null fix |
| 2 | Derangement helper infinite-loop (n=2) → rejection sampling | bug |
| 3 | Pin-builder powered gate: enforce full §8.1 (MDE≤10 + median + thirds) — was mislabeling a tail-driven UNPOWERED cell as "powered", wrongly opening 016 | bug |
| 4 | Pin-builder rate-lean: 0 powered → `residual_status=NONE`; rate lean kept as SUGGESTIVE disclosure (was overstating `MOMO_DOMINANT` + reverting a hand-patch each re-run) | honesty fix |
| 5 | **AMENDMENT-S2:** last-k conditioner corrected to O3 intent — ordered state sequence, K∈{1,2,3} (was a bare HIGH-count that hid the structure) | design↔O3 fidelity |
| 6 | Parallelised over symbols (849s → 180s), bit-identical | perf |

QA: run 1 REVISE → run 2 APPROVE (fixes 1–3) → **run 3 APPROVE** (fixes 4–5; S2 O3-consistent, pin
builder independently reproduced, no regression). Integrity + golden pass on the final emission. Core
estimands are unchanged by S2 (stratification column only).

---

## 3. Integrity (HARD — all pass)

| Check | Result |
|---|---|
| `integrity_selfcheck.all_pass` | **true** |
| Golden traces G1–G4 | pass |
| Universe pin equality (top-25) | pass |
| TRAIN fence (every exit open < 2023-12-18) | pass |
| Causal ≤t-1 construction (width ≤t; anchor open[t+1]; breach entry open[j+1]; exit open[entry+h]) | verified |
| O3-SOT: no signed product; shock not a regime; both MOMO+MR emitted; straddle secondary | pass |
| Future-destroy tripwire positive survivors above null p95 | none (non-vacuous, uninformative-by-absence) |
| No local accounting (screen = availability/residual bps, not booked P&L) | pass |
| Holdout / TEST | untouched |

**Emission size:** 8,450 cell-strata · 749,456 zones/events · 560,652 post-event rows · 25 symbols
(17 with DESIGN Z-VOL data; 8 empty on warm-up: ORDI, TIA, BIGTIME, 1000PEPE, SEI, WLD, PYTH, 1000RATS).

---

## 4. Per-stratum breakdowns

### 4.1 Observations by source × event (DESIGN, decided)

| Source | E-TOUCH | E-CLOSE | E-HORIZON |
|---|---:|---:|---:|
| Z-VOL | 94,010 | 75,072 | 52,575 |
| Z-MAG | 8,036 | 4,968 | 3,492 |
| Z-MAG-SENS | 2,628 | — | — |

**Source meaning:** Z-VOL = band width from range vol (Parkinson→EWMA). Z-MAG = width from ZigZag
next-swing magnitude forecast. Z-MAG-SENS = Z-MAG with width/2 (sensitivity co-report; Z-MAG sparse
because a confirmed swing forecast isn't always available).
**Event meaning:** E-TOUCH = intrabar high/low pierces band (earliest). E-CLOSE = bar closes outside
(sustained). E-HORIZON = close outside only at the last bar of H (slowest).

### 4.2 Primary characterisation cell — per symbol (Z-VOL · z1.5 · H12 · E-TOUCH · h12 · DESIGN · P-NONE)

| Symbol | n | mean r_h | median | MDE bps | p_momo | p_mr | label |
|---|---:|---:|---:|---:|---:|---:|---|
| MATIC | 517 | −10.2 | −4.5 | 61 | 0.482 | 0.499 | UNPOWERED |
| SOL | 197 | +43.7 | +18.2 | 105 | 0.518 | 0.462 | UNPOWERED |
| BTC | 196 | +2.4 | +3.3 | 38 | 0.474 | 0.464 | UNPOWERED |
| ETH | 194 | +26.2 | +15.1 | 49 | 0.531 | 0.443 | UNPOWERED |
| XRP | 193 | +16.5 | +12.5 | 55 | 0.518 | 0.466 | UNPOWERED |
| ADA | 193 | +20.9 | +22.0 | 52 | 0.528 | 0.446 | UNPOWERED |
| BNB | 189 | −24.3 | −20.5 | 47 | 0.429 | 0.556 | UNPOWERED |
| OP | 189 | −20.9 | −11.2 | 102 | 0.481 | 0.508 | UNPOWERED |
| LINK | 188 | +11.8 | +2.1 | 64 | 0.495 | 0.479 | UNPOWERED |
| AVAX | 180 | −7.5 | −11.6 | 86 | 0.483 | 0.511 | UNPOWERED |
| DOGE | 175 | −15.6 | +4.5 | 59 | 0.497 | 0.474 | UNPOWERED |
| GALA | 169 | +26.4 | +40.1 | 98 | 0.521 | 0.467 | UNPOWERED |
| DYDX | 119 | +76.5 | +57.6 | 174 | 0.546 | 0.454 | UNPOWERED |
| LUNC | 111 | +58.6 | +16.9 | 198 | 0.514 | 0.486 | UNPOWERED |
| INJ | 103 | +36.4 | +71.4 | 193 | 0.524 | 0.466 | UNPOWERED |
| BONK | 41 | −22.0 | −119.8 | 289 | 0.463 | 0.537 | UNPOWERED |
| BLUR | 10 | +491.1 | +546.5 | 764 | 0.700 | 0.300 | UNPOWERED |

**Powered cells: 0 / 17** — every MDE 38–764 bps ≫ the 10-bps bar. p_event 0.995–1.0 (band not selective).

### 4.3 MOMO vs MR per source × event (DESIGN, z1.5 · H12 · h12, pooled decided — DISCLOSURE-ONLY, L-03)

| Source | Event | n | mean | median | p_momo | p_mr | p_flat | lean |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Z-VOL | E-TOUCH | 4220 | 0.0 | −0.0 | 0.489 | 0.494 | 0.017 | ~flat |
| Z-VOL | E-CLOSE | 2799 | −6.8 | −15.8 | 0.458 | 0.519 | 0.022 | MR |
| Z-VOL | E-HORIZON | 1937 | +4.5 | −8.7 | 0.480 | 0.506 | 0.013 | mild MR |
| Z-MAG | E-TOUCH | 223 | +22.4 | −17.8 | 0.466 | 0.516 | 0.018 | mild MR |
| Z-MAG | E-CLOSE | 148 | −44.2 | −74.2 | 0.385 | 0.588 | 0.027 | MR (strong) |
| Z-MAG | E-HORIZON | 106 | −68.2 | −54.7 | 0.462 | 0.538 | 0.000 | MR |
| Z-MAG-SENS | E-TOUCH | 876 | +0.9 | −20.9 | 0.466 | 0.526 | 0.008 | mild MR |

Every source × event leans MR-or-flat on the rate; the close-beyond-band events (E-CLOSE) lean MR
hardest (Z-MAG E-CLOSE p_mr 0.588, median −74). E-TOUCH is the flattest (least directional). Pooled
obs-weighted (MATIC-heavy) tilts MR; the per-cell count leans MOMO (18 vs 7) — different weightings,
neither powered.

### 4.4 Last-k state-sequence arms (AMENDMENT-S2, ordered; Z-VOL · E-TOUCH · z1.5 · H12 · h12 · DESIGN · n=4220)

`last_k_state_K` = ordered slow-regime label sequence over the last K bars (chronological; last char =
decision bar; 'H'=HIGH-vol, 'L'=LOW-vol; causal ≤t). Order + run-length preserved (a bare HIGH-count
collapses these arms and hides the structure).

**k=1** — H: n1721 mean −11.7 p_momo 0.493 · L: n2499 mean +8.1 p_momo 0.487 → flat (single label conditions little).

**k=2:**

| arm | n | mean | median | p_momo | p_mr | lean |
|---|---:|---:|---:|---:|---:|---|
| LH | 202 | +22.2 | +40.4 | 0.554 | 0.426 | **MOMO** |
| HL | 210 | +25.8 | −16.5 | 0.476 | 0.510 | mixed |
| HH | 1519 | −16.3 | −2.8 | 0.485 | 0.497 | flat |
| LL | 2289 | +6.5 | −2.7 | 0.488 | 0.497 | flat |

**k=3:**

| arm | n | mean | median | p_momo | p_mr | lean |
|---|---:|---:|---:|---:|---:|---|
| HLH | 33 | +27.7 | +45.6 | 0.576 | 0.424 | MOMO (thin) |
| HLL | 149 | +49.4 | +24.6 | 0.550 | 0.436 | **MOMO** |
| LLH | 169 | +21.2 | +40.3 | 0.550 | 0.426 | **MOMO** |
| HHL | 159 | +46.9 | +4.6 | 0.491 | 0.491 | flat mean+ |
| LHH | 179 | −19.2 | +2.8 | 0.497 | 0.492 | flat |
| LLL | 2140 | +3.5 | −5.1 | 0.483 | 0.501 | flat |
| HHH | 1340 | −15.9 | −3.4 | 0.484 | 0.498 | flat |
| LHL | 51 | −40.2 | −73.4 | 0.431 | 0.569 | **MR** (thin) |

**Structure:** arms ending in `…LH` (a fresh flip *into* high-vol on the decision bar) lean **MOMO**
(p_momo 0.55–0.58, median ~+40 bps), consistent across k=2 and k=3; `HLL` also MOMO; `LHL` is the
mirror (MR, median −73, n=51 thin); persistent `HHH`/`LLL` and k=1 alone are flat. Direction lives in
the **transition**, not the level or the count. All discriminating arms are small (n 33–210) → UNPOWERED.

---

## 5. Observations

1. **Band is not selective** — p_event ≈ 1.0 at the primary pins; the "mispricing event" is nearly every
   zone. Residual ≈ side-signed 12h path after first touch, not a rare dislocation.
2. **Continuation is a coin-flip** at the primary cell (p_momo 0.489 vs p_mr 0.494); the modal *rate*
   tilt across cells is a mild MOMO (18 MOMO-rate vs 7 MR-rate cells), but the obs-weighted pooled tilt
   is a mild MR.
3. **Event definition changes the sign** — E-TOUCH ≈ flat/mild-MOMO vs E-CLOSE clearly MR. A durable
   residual should not flip under a nearby event rule.
4. **Magnitude scales with vol, direction does not** — shock / mag_high / MID-vol strata lift residual
   *magnitude* (+20…+72 bps) while p_momo stays ~0.50.
5. **The one order-conditional direction signal** is the L→H vol-flip → MOMO (+40 bps median) — new
   from S2, invisible under the count reading, but UNPOWERED.
6. **Money does not graduate** — P-MOMO / P-MR medians negative under partial cost; gross ≈ 0; straddle
   ≈ −29 bps (2× cost on a ~0 path). No tripwire survivor.

---

## 6. Evidence FOR residual ≠ ambient (each a magnitude; none clears §8.1 SUPPORTED)

- **Shock-conditioned MOMO:** mean +71.6 / median +29.3 bps, p_momo 0.56 vs 0.41, pooled block-CI
  **[+11.9, +134.9]** (block-stable), n=235 — the only pooled read whose CI excludes 0 (named shock,
  not a regime).
- **Event-definition asymmetry:** E-TOUCH-MOMO vs E-CLOSE-MR — a consistent ~18–20 bps split by breach type.
- **z / h dose:** low-z + long-hold → positive tail-driven mean (h=24 +21.4); high-z (z=2.0) → negative
  median — a coherent MR-at-large-breach pattern.
- **Directional tilt:** 11/17 symbols positive mean; +1.7 pp MOMO rate tilt; 18 MOMO-rate vs 7 MR cells.
- **Band geometry:** forecast width measurably tighter than unconditional σ (Δ p_event +0.05..+0.11).
- **Order-conditional vol-flip (§4.4):** L→H transition (`LH`/`LLH`/`HLH`) leans MOMO, p_momo ~0.55,
  median +40; mirror `LHL` leans MR. Coherent across k=2 and k=3.

## 7. Evidence AGAINST (equal diligence)

- **Zero powered SUPPORTED cells** — every primary MDE 38–764 bps ≫ 10; no symbol's residual CI-low
  clears its control null.
- **Even pooled DESIGN residual CI straddles 0** ([−4.0, +26.6]); the MOMO rate lean CI straddles 0
  ([−0.021, +0.055]).
- **DESIGN→CONFIRM sign flip:** 12/17 symbols reverse; pooled +11.3 → −4.3 — the DESIGN tilt does not
  reproduce out-of-DESIGN.
- **Band non-selectivity:** p_event ≈ 1.0 — not a rare mispricing.
- **Tail-driven means:** medians ≈ 0 / negative where means are positive; BLUR (+491, n=10) not portable.
- **Money arms all negative** at the median on partial cost; gross ≈ 0.
- **Every FOR signal is UNPOWERED / disclosure-only** — pooled or thin-bucket, none per-symbol powered.

---

## 8. Power (the load-bearing facet — B-5)

- **0 powered residual cells of 927** (rule: n_events≥80 AND n_dates≥30 AND MDE≤10 bps).
- MDE bps min / median / max ≈ 20 / 172 / 796. Per-event dispersion σ_r ≈ 187 bps.
- **UNPOWERED ≠ dead.** A ±5 bps object is structurally invisible at this per-symbol cell; power is not
  reachable here without variance reduction (normalise r_h by σ̂; pooled/hierarchical estimand) — a
  design question for a follow-up, not a data defect.

---

## 9. Residual pin & disposition

```json
{ "residual_status": "NONE", "016_start_allowed": false, "policy_for_016": "NONE",
  "n_powered_momo": 0, "n_powered_mr": 0,
  "rate_lean": "MOMO_SUGGESTIVE", "n_rate_momo_suggestive": 18, "n_rate_mr_suggestive": 7 }
```

`residual_status=NONE` is **code-generated** (not a hand-patch → stable). `016_start_allowed` is set
**true by operator override** (see `operator_override` block); the builder default is false and the
override is the authority — it must be re-asserted if the screen is re-emitted.

| Field | Value |
|---|---|
| Analyst recommendation | INCONCLUSIVE — reason class UNPOWERED_NOT_NULL (not NOT_WORTH; B-5) |
| **Operator verdict (2026-07-24)** | **OPEN SPDR-016 by signed override** (§8.3), on the SUGGESTIVE leads |
| Basis of override | UNPOWERED but coherent leads — shock-MOMO (CI excl 0), E-TOUCH/E-CLOSE asymmetry, L→H vol-flip MOMO — **not** a powered SUPPORTED residual |
| residual_status / n_powered | NONE / 0 (unchanged — override does not assert a powered object) |
| 016 residual object + policy | **DEFERRED** to 016 design (operator: follow-up decisions after opening) |
| Scope | Experiment hypothesis only. NOT family status. NOT tradability. |

---

## 10. Open threads / leads for a powered follow-up

Three UNPOWERED structural signals worth a targeted, powered re-test (need larger n per stratum via
pooling/hierarchy + a paired-Δ-vs-control block-bootstrap CI):

1. **Shock-conditioned MOMO** (+72/+29 bps, CI excludes 0).
2. **E-TOUCH-MOMO / E-CLOSE-MR asymmetry** (~18–20 bps).
3. **Order-conditional vol-flip** (§4.4, L→H → MOMO ~+40 bps median) — the cleanest new lead from S2.

Other: last-k K=12 raw pattern is sparse (analysis uses K∈{1,2,3}); 8 symbols lost to warm-up; the
pin's per-cell CI/median are raw-cell proxies (a paired-Δ CI is required before any SUPPORTED claim).

---

## 11. Amendments

- **AMENDMENT-S1** (per-symbol sufficiency; multi-symbol = credibility only) — NEUTRAL.
- **AMENDMENT-S2** (2026-07-24, NEUTRAL) — last-k conditioner corrected from a HIGH-count to the ordered
  state sequence (O3 §2.1/§2.2 intent; K∈{1,2,3} operator-directed). Stratification column only; no
  estimand/pin/verdict change.
- Interpretation notes IN-1 (money zone H=12), IN-2 (Z-MAG expanding ridge), IN-3 (last-k = ordered
  slow_regime labels), **IN-4 (residual_status = powered residual object only; rate lean is
  disclosure-only — QA-run-3 tightening, operator-ratifiable).**

## 12. Artifact map

| Path | Role |
|---|---|
| `results/integrity_selfcheck.json` / `golden_traces.json` | HARD integrity |
| `results/014_residual_pin.json` | 016 start gate (NONE) |
| `results/expectancy_by_cell.parquet` | full cell grid |
| `results/post_event.parquet` | per-event r_h / labels / conditioners (incl. `last_k_state_1/2/3`) |
| `results/controls.json` | corrected null battery + tripwire |
| `results/perstratum_final.parquet` / `final_magnitudes.json` | full per-stratum magnitude table |
| `analysis.md` | binding neutral analysis (of record) |
| `screen.md` | subordinate quantification |
| `qa-review.md` | QA runs 1–3 (append-only) |
| `_archive_v1/` | first (adversarial) analysis + pre-fix emission, retained for provenance |

**Operator verdict (2026-07-24):** SPDR-016 **OPENED by signed override** (§8.3) on the three coherent
SUGGESTIVE leads — explicitly not on a powered residual (0 powered cells, `residual_status=NONE`). The
016 residual object and policy are deferred to 016 design. The analyst's own recommendation was
INCONCLUSIVE / UNPOWERED_NOT_NULL; the override is the operator's authority, honestly attributed.
