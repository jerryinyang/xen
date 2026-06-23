# Phase 020 — Mean-Reversion Entry Availability Screen (CF-MR-001)

**Status:** **OPEN — G0 RATIFIED (2026-06-23, operator-authorized; D2b bite-check GREEN on the single-test
legs, sha256 `f01a000b…`).** The leg-2 conjunctive regime test (§3) is a design correction applied in place
(2026-06-23, operator-directed); its new per-cell statistic + regime-membership null require the **bite-check
to be extended and re-confirmed GREEN before EXP-089 runs**. First candidate family opened after the
Phase 019 terminal branch, by **explicit operator override** of the G-019 price→non-price routing (§1).
The phase's sole experiment is a **TRAIN-only availability screen** (EXP-089): **0 candidate slots, 0 counted
TEST reads, holdout never touched.**

**Family:** [`CF-MR-001`](../../../signal-registry/candidate-families/cf-mr-001.md) — RSI-2 mean-reversion
entry + global `/VOLREGIME` partition.
**Predecessor checkpoint:** [`2026-06-22-019-family-selection-availability-screen`](../2026-06-22-019-family-selection-availability-screen/retrospective.md)
(G-019 terminal; both screened axes NOT ADMITTED).
**Companion docs:** [`D0-predeclarations.md`](D0-predeclarations.md) · [`G-020-gate-criteria.md`](G-020-gate-criteria.md)
· [`bite-check/BITE-CHECK-PLAN.md`](bite-check/BITE-CHECK-PLAN.md).

---

## 1. Why this phase, and the override it carries

The mandate from the post-Phase-018 reflections: *the entry signal must have a better-than-random edge on its
own before any capture-geometry work.* Three closed families and the Phase 019 screens all return the same
mechanism — **single-instrument, event-driven, price-geometry entries carry no signal-conditional favourable
availability beyond a matched random control** (EXP-047, EXP-081, EXP-084). G-019 routed the programme off
price-derived information.

**The operator overrides that routing (2026-06-23)** to test **two things the programme has never tried**
(`cf-mr-001.md` §0):

1. **A mean-reversion (fade) entry mechanism** — the opposite of every continuation/pullback family tested so
   far. The "single-series directional is dead" verdict was earned only on continuation entries.
2. **A strategy-agnostic volatility-regime partition** — a filter *intrinsic to the market* (not native to any
   strategy) treated as part of the signal definition (cell = `asset+domain+regime`), i.e. a
   cell-differentiating factor of the core signal rather than a bolt-on plugin. The bet: making such an
   intrinsic filter part of the signal itself is the ingredient prior families lacked — a genuinely new lever,
   not a re-try of an add-on filter.

**The programme-level null is availability ≈ random** — the hypothesis the screen tries to reject, not a
prediction of failure; both legs carry the override on their own merits (leg 1 a new entry mechanism; leg 2 a
new *kind* of filter — strategy-agnostic, intrinsic to the market, made part of the signal definition rather
than bolted on as a plugin). So the phase is built as a **clean, fully-committed falsification attempt**: a
single TRAIN-only screen reusing the Phase-019 admission gate, costing 0 slots and 0 reads, that either finds
the first non-random price entry or drives one more nail and returns to the non-price frontier. The analysis
reads the realized numbers on their own terms, importing no prior family's outcome as an expectation.

## 2. The one question (single hypothesis)

`CF-MR-001/HYP-001` (EXP-089): **Does the RSI-2 mean-reversion entry — bare, partitioned by volatility regime,
or with a trend / RSI filter — produce favourable excursion beyond a regime- and direction-matched random
control, as adjudicated by the multiplicity-adjusted permuted-axis admission gate?**

This is an **availability disclosure**, not a tradability claim: no exit, cost, sizing, or P&L; no candidate
slot; no TEST read.

## 3. Method (frozen at D0; full detail in `D0-predeclarations.md`)

- **Dataset:** VAL-005 5-year 1m, 16 instruments, holdout-fenced `build_domain_bars`; domains {15m, 1h, 4h};
  **TRAIN sub-split `[0, int(analysis_rows·0.7))` only.** All metrics in ATR(14) units on real OHLC.
- **Entry:** `RSI(2)` Wilder on domain Close; long `RSI₂<10`, short `RSI₂>90` (frozen 2 / 10 / 90).
- **Global filter `/VOLREGIME`:** `ATR(14)` causal trailing rolling-50 percentile, 33/66 cuts → Low/Med/High;
  per-(instrument,domain) thresholds from past bars only; **partition on the bare core only**.
- **Matched-random control:** the established EXP-080/081 `SUB-RANDOM` — random-timing entries matched on
  **count and direction**, the same all-bars control for every sub-screen (no regime-matching:
  ATR-normalisation removes the regime scale). The regime's *additive* edge is isolated by the binding leg-2
  `Δ̂_core` differential, not the control.
- **Member cells:** the EXP-080-READY 46 instrument×domain cells (US500-4h, JP225-4h `COVERAGE_EXCLUDED`);
  RSI-MR event coverage re-confirmed in-experiment against a **≥15-event floor** (no upper bound — the EXP-080
  8000 ceiling is dropped for this dense oscillator entry); any new coverage failure excluded with record.
- **Endpoint:** per-cell favourable `MFE_med`, two reads — `Δ̂_rand` vs `SUB-RANDOM` (leg 1, all sub-screens)
  and `Δ̂_core` vs pooled CORE (leg 2, the `/VOLREGIME` sub-screens, binding); "beats" = one-sided lower bound > 0.
- **Binding gate (D2b, reused `xen.availability_gate`):** six sub-screens
  `{CORE, CORE-VOL-LOW/MED/HIGH, CORE+TREND, CORE+FILTER}`. Per-sub-screen `S` = `#beats-random` for
  CORE/variants and `#(beats-random ∧ beats-CORE)` for the three `/VOLREGIME` sub-screens (leg 2 binding — the
  regime must *add* edge over CORE). Per-sub-screen null = signal-shuffle (CORE/variants) /
  regime-membership-shuffle-within-CORE (`/VOLREGIME`). **Family statistic `S_fam = max_sub S`** under the
  **joint** permuted null across the six sub-screens; `ADMITTED iff S_fam > S* (Q95) ∧ axis perm_p ≤ 0.05`
  (FWER 0.05). No cross-axis Holm (single family). N_PERM = 5000 production (1000 bite, MC-stable).
- **Bite-check (precondition for the run):** GREEN at the 6-sub-screen structure and C=46, **extended to the
  leg-2 conjunctive statistic + regime-membership null** (a noise regime adds 0 conjunctive wins; a planted
  additive-edge regime is detected) — re-confirmed before EXP-089 runs (`bite-check/BITE-CHECK-PLAN.md`).

## 4. Complexity budget

| Item | Budget |
| --- | --- |
| Binding statistical tests | 1 (the D2b admission gate) + descriptive companions |
| Visualisations | ≤ 4 (per-cell Δ map; regime split; sub-screen S vs S*; permutation null) |
| New code modules | ≤ 2 (`xen.mean_reversion` entry+indicators; `xen.vol_regime` filter); reuse
  `availability_gate`, `domain_bars`/`bar_aggregator`, geometry/expectancy, `SUB-RANDOM` |

## 5. Verdict and routing (mechanical — see `G-020-gate-criteria.md` §2)

| Adjudicated state | Consequence |
| --- | --- |
| **ADMITTED** (`S_fam > S* ∧ perm_p ≤ 0.05`) | The argmax sub-screen names the lever — bare MR (leg 1), a **vol regime** (leg 2, i.e. the regime *added* edge over CORE via the binding beats-CORE conjunction), or a variant. **CF-MR-001 consumes its first candidate slot**; a future G0/D0 opens batch 2 (readiness → characterization → capture geometry → TEST), expanding to regime×variant cross-cuts, the 25/75 scheme, and the contrarian arm. |
| **EXONERATED** (every sub-screen within the D2a noise band) | Mean-reversion + the global vol filter carry no availability beyond noise on this dataset. The single-series-directional cell is dead under **both** continuation and mean-reversion; the programme returns to the **G-019 terminal frontier (non-price data acquisition)**. 0 reads / 0 slots. |
| **INCONCLUSIVE** (permuted null cannot separate) | Disclosed; neither admitted nor exonerated; a finer re-scope is a separate future decision. |

## 6. Discipline (binding throughout Phase 020)

TRAIN sub-split only on VAL-005 data; all excursion/range metrics on real prices (HA prices never enter a
metric); deterministic (fixed seeds, byte-identical second pass including the permutation stream); no
parameter tuned against any TEST or holdout data; per-stratum reporting (LESSON-001 — no collapsed cross-cell
boolean is binding); **0 candidate slots, 0 counted TEST reads** (availability disclosure; `test-read-ledger.md`
unchanged, all 48 strata stay 0/2 open); holdout sealed.
