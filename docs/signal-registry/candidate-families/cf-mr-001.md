# CF-MR-001 — Mean-Reversion Entry (RSI-2), with Global Volatility-Regime Partition

**Status:** `CLOSED — REFUTED (2026-06-26): the net-tradable / deployment arc (EXP-091→098) rests on an
uncaught one-bar EXIT-RCT exit look-ahead; live-causal the bare fade is net-negative even gross. G-021 TRADABLE
and G-022 DEPLOYABLE_CONFIRMED are RETRACTED. Availability-only (EXP-089 / G-020 ADMITTED) stands. Family CLOSED,
not reopenable by re-parameterization; outcomes retained.` See **§CLOSURE (2026-06-26)** below.

> ### CLOSURE — REFUTED (2026-06-26): EXIT-RCT exit look-ahead invalidates the tradability/deployment arc
>
> **Source of truth:** `XRSI-V1/DIAGNOSIS-real-entry-slippage-omission.md` (final) +
> `XRSI-V1/ISSUE-booked-vs-real-feed-divergence.md` (initial), confirmed by an independent Xen-code trace.
>
> **Mechanism (the why).** The EXIT-RCT favourable limit is built with a one-bar look-ahead. `arm_levels`
> (`python/experiments/EXP-090/code/run_experiment.py:305-310`) sets the intrabar resting limit for the domain
> bar at offset `off` (`di = entry_idx+off`) to `ctx.rct_target[di]` — the reversion-completion target
> `P*_di = Close_di + (period-1)·(AL_di − AG_di)` computed from **bar `di`'s own close**
> (`reversion_completion_target`, `python/src/xen/mean_reversion.py:174`; the readiness invariant
> `EXP-090:~603` itself treats `rct_target[i]` as the *hypothetical next-bar close*, i.e. the target for bar
> `i+1`). A limit that can rest *during* bar `di` is only live-actable from `rct_target[di-1]`. `resolve_exit_paths`
> reads `fav_level[j, off-1]` (`intrabar_fill.py:212`), but the `off-1` is just the array slot for offset `off`
> — it does **not** shift the rct value back a bar, so the engine rests `rct[di]` during `di`. This off-by-one is
> the cBot's "booked-lookahead `rct[di]` gross +0.20 vs booked-causal `rct[di-1]` −0.05" gap, worth **~+0.25
> ATR/trade**. **Causalized (`rct[di-1]`) the bare RSI-2 fade + EXIT-RCT is net-negative even gross** — the
> captured "tradable edge" was the look-ahead. Exposed by porting to cTrader (XRSI-V1) and forward-testing:
> native execution can only rest `rct[di-1]`.
>
> **Secondary (compounding) defect, cBot-port-only.** The XRSI-V1 REAL execution stream also dropped the binding
> **v2 entry slippage** (0.05·ATR) that the research model charges (`Diagnostics.LogActualFill` referenced gross
> to the raw broker fill `v1`), making the live run look profitable (+$62.8k) when faithfully it is negative.
> This reinforces the refutation but is *not* the research-level cause — the EXIT-RCT exit look-ahead is.
>
> **Scope of invalidation.** EXP-091/092/094 (screen/sequence), **EXP-093 `TEST_CONFIRMED`** (11 counted TEST
> reads), EXP-095/096 (portfolio + v2 fill — "survives slippage" rests on the inflated look-ahead gross),
> **EXP-097 `DEPLOYABLE_CONFIRMED`** (the global-holdout shot), and EXP-098 robustness — **all net-tradable /
> deployment claims are REFUTED.** **NOT invalidated: EXP-089 availability / G-020 ADMITTED** — it used gross
> `MFE_med` favourable excursion with no RCT limit. The fade's favourable *availability* is real; what is refuted
> is that it was net-*capturable* live. HYP-002 and HYP-003 close REFUTED; HYP-001 (availability) stands.
>
> **Governance.** Family **CLOSED — REFUTED**. The **11 EXP-093 counted TEST reads and the EXP-097 global-holdout
> shot were spent on a look-ahead-biased construction** — reads/shots are non-refundable (a discovered defect does
> not restore them); they stay SPENT, now recorded as **spent-on-defect** in `test-read-ledger.md` +
> `multiplicity-registry.md`. **G-021 TRADABLE and G-022 DEPLOYABLE_CONFIRMED are RETRACTED** (checkpoint gate
> reviews superseded). Per registry rules all prior outcomes below are **retained, not deleted**; the family is
> **not reopenable by re-parameterization**. Live-backtest observations worth a fresh look (native-fill behaviour,
> slow-domain cost geometry) may seed a **new family** under its own D0 — only **after** a pipeline fix that
> causalizes the EXIT-RCT limit (`rct[di-1]`) — and are explicitly **out of scope** of this closure.
>
> *Everything below this banner is the prior (now superseded) DEPLOYABLE record, retained verbatim for
> file-drawer integrity.*

(EXP-089 `SCREEN_DELIVERED`, 2026-06-23; G-020 ADMITTED.) First candidate family
opened **after** the Phase 019 terminal branch, by **explicit operator override** of the G-019 price→non-price
routing (see §0). The family's first read was a **TRAIN-only availability screen** (EXP-089, `CF-MR-001/HYP-001`):
**0 counted TEST reads, holdout never touched.** **G-020 ADMITTED** (`S_fam=28 > S*=7`, axis perm-p≈0.0002,
FWER-robust, MC-stable) — **CF-MR-001 has now consumed its first candidate slot** and is the programme's first
non-random price entry to clear the family-selection availability gate. See
[`G-020-gate-review.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md).

> **AMENDED — `D0-amendment-001` (2026-06-23).** The first EXP-089 run was a deviation (audit C-1
> ATR-normalization confound + C-2 trend-length horizon). The leg-2 **beats-CORE conjunction and the
> regime-membership-shuffle null are RETIRED**; the endpoint is measured over a **causal MR-tempo cap** and the
> `/VOLREGIME` controls are **regime-matched**; all 6 sub-screens are single-test leg-1. The §"Global
> volatility filter" leg-2 description below is **superseded** by the amendment. **Realized outcome (§Outcome):
> the lever is the bare RSI-2 fade; the vol-regime partition is inert.**

**Governing phase (batch 1, CLOSED at G-020 ADMIT):** [`../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/design.md)
· D0 [`D0-predeclarations.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/D0-predeclarations.md)
· gate [`G-020-gate-criteria.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-criteria.md)
· review [`G-020-gate-review.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md).
**Prior phase (batch 2 — availability→tradability): CLOSED — G-021 TRADABLE 2026-06-24.** [`Phase 021 design`](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/design.md)
· [D0-predeclarations](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-predeclarations.md)
· [G-021 gate review](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/G-021-gate-review.md).
EXP-090→094 (TRAIN) → EXP-093 (one-shot TEST): bare RSI-2 fade + **EXIT-RCT** confirms net-tradable OOS on the
analysis-TEST stratum — **8/11 carried cells CONFIRM** (six 4h mean-AND-median-positive robust core + USTEC-1h/
US2000-1h mean-carried); the programme's first net-positive price entry. 11 counted TEST reads spent (each
carried stratum 0→1, now 1/2); final-30% global holdout never loaded. EXIT-ERT + the conventional arms died at
the screen (file drawer).

**Active phase (batch 3 — deployment economics & global-holdout-final):** [`Phase 022 design`](../../experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/design.md)
· [D0-predeclarations](../../experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-predeclarations.md)
*(FROZEN, G0-RATIFIED 2026-06-24)* — **HYP-003**: deploy the 8 confirmed cells as a time-aligned, causal,
parameter-free **ERC portfolio** with cross-instrument correlation + an online performance **circuit-breaker**
(EXP-095), stress it under a realistic **1-minute entry-fill noise** model (EXP-096), then **release the
final-30% global holdout** as the single sanctioned one-shot deployment confirmation (EXP-097, gated behind the
G-022a freeze). 0 new slots; EXP-095/096 are 0 counted TEST reads (portfolio-aggregate disclosure reusing the
EXP-093 series); **EXP-097 spends the global-holdout shot** (outside the analysis-TEST ledger). The deferred
levers (regime, contrarian, 25/75, 15m, cross-cuts, tuning, expansion) are NOT in Phase 022 — each needs its own
dated `D0-amendment-*` + slot decision. **The 4h domain was OPENED 2026-06-24 (`D0-amendment-004`, 0 new
slots), gated behind the EXP-094 falsification re-screen** (see the EXP-094 outcome section below).
**Real-price / holdout discipline (binding):** all excursion/range metrics on real prices
(`RealOpen/High/Low/Close`); the final-30% global holdout is never read in screening or any future
readiness/characterization; counted TEST reads are spent only at a future binding confirmation under the
2-lifetime-per-stratum cap.

---

## 0. Provenance and the operator override (recorded, not implied)

Phase 019 (G-019, 2026-06-23) adjudicated the family-agnostic availability slate and routed the programme to
a **terminal branch**: *price-derived information — single-series magnitude and cross-sectional relational —
exhausted on this dataset; frontier = non-price data acquisition.* The single-series × **directional**
price-geometry cell is dead three families over (CF-AVWAP-001, CF-HA-HARAMI-001, CF-CAPGEO-001); the
magnitude cell (CF-VOLEXP-001) and the cross-sectional cell (CF-XSECT-001) closed at G-019.

**This family reopens the price-derived surface by explicit operator decision (2026-06-23).** The registry
rule is that a closed cell reopens only on a **genuinely new lever**, never a re-parameterization. The stated
new-lever basis is **two** items, and the family's honesty depends on holding to them:

1. **Mean-reversion entry mechanism (the strong leg).** Every prior family was **continuation / trend /
   pullback** (AVWAP pullback, HA-harami in trend, capgeo on those substrates). A **fade** entry — buy
   oversold, sell overbought — is the *opposite* signal generator and has **never been screened**. The
   "single-series directional is dead" verdict was established only on continuation entries.
2. **Strategy-agnostic volatility-regime partition as signal definition (a co-primary new lever).** A
   **strategy-agnostic** ATR regime filter — one *intrinsic to the market* rather than native to any strategy
   (unlike a strategy-fitted conditioner) — is applied as a *partition* of the entry population, so "RSI-MR in
   high-vol" is treated as a **distinct core signal** (cell = `asset+domain+regime`), not a post-hoc plugin.
   The bet is that making such an intrinsic filter a **cell-differentiating factor of the core signal itself**,
   rather than an add-on bolted onto a finished entry, is the ingredient prior families lacked. This is a
   genuinely new lever — not a re-try of an add-on filter — and the phase exists to disprove (or not) exactly
   that bet.

**Honest prior (binding on interpretation).** The programme-level null is **availability ≈ random** — the
hypothesis the screen tries to reject, not a prediction of failure. **Both** legs carry the override on their
own merits: leg 1 a genuinely new entry mechanism (fade), leg 2 a genuinely new *kind* of filter
(strategy-agnostic, intrinsic to the market, made part of the signal definition rather than bolted on). The
screen is therefore a **fully-committed falsification attempt at 0 reads / 0 slots**: if bare MR and its
vol-regime partitions come out ≈ random, that is a strong additional nail and the single-series-directional
cell is then dead under *both* continuation and mean-reversion; if any sub-screen admits, it is the
programme's first non-random price entry. The analysis and documentation read the realized numbers on their
own terms — no prior family's outcome is imported as an expectation that biases this verdict in either
direction.

---

## CF-MR-001 — definition (frozen at Phase 020 D0)

**2×2 cell:** single-series × directional, via a **mean-reversion (fade)** mechanism (distinct generator from
the dead continuation entries) + a **global volatility-regime partition**.

**Thesis (one falsifiable sentence):** *A short-period RSI mean-reversion entry — alone, or partitioned by a
strategy-agnostic ATR volatility regime that becomes part of the signal definition — produces
signal-conditional favourable excursion beyond a regime- and direction-matched random control.*

### Entry — RSI-2 mean reversion (frozen)

- **Indicator:** `RSI(2)`, Wilder smoothing, on domain `Close`. Parameters frozen: period **2**, extremes
  **10 / 90**. No tuning until the first batch shows promise (D0 §D6).
- **Long signal** at bar *t*: `RSI₂(t) < 10` (fade oversold; favourable = upward excursion).
- **Short signal** at bar *t*: `RSI₂(t) > 90` (fade overbought; favourable = downward excursion).
- **Availability endpoint (this family's screen):** signed favourable excursion `MFE_med` over the
  per-event adaptive cap (EXP-081 geometry), **ATR(14)-normalised, real OHLC**, vs the matched random
  control. The RSI exit (cross to the opposite extreme) is **not used** in the availability screen — it is a
  capture-geometry question deferred to a future post-admission phase (§exclusions).

### Global volatility filter — `/VOLREGIME` (frozen; distinct from the closed CF-VOLEXP-001)

- **Estimator:** `ATR(14)`, Wilder, on domain bars.
- **Regime:** causal trailing **rolling-50-domain-bar** percentile rank of the current `ATR(14)`; cuts at
  **33 / 66** → `LOW (<p33) / MED / HIGH (>p66)`. **Strategy-agnostic rule**; the percentile thresholds are
  computed **per (instrument, domain)** from **past bars only** (no future bar enters a regime label —
  streaming-safe). Window **50**, **33/66** scheme, **no tuning** in batch 1.
- **Applied as a PARTITION on the bare core only** (batch 1): each core entry is assigned to its regime. The
  regime sub-screen is tested by a **binding additive-edge conjunction** — a cell counts only if the regime
  subset **beats the standard direction-matched random control (`Δ̂_rand > 0`) AND beats the pooled CORE
  (`Δ̂_core > 0`)**, under a **regime-membership-shuffle-within-CORE** null. This operationalizes leg 2 *at
  full strength in batch 1, no deferral*: the regime must **add** favourable availability the unconditioned
  entry lacks, not merely inherit the core's. The control is the **same all-bars direction-matched
  `SUB-RANDOM`** as every other sub-screen — **no regime-matched control** (the endpoint is ATR(14)-normalised,
  so a regime's larger absolute moves are already divided out; the regime's additive value is what `Δ̂_core`
  isolates).
- **Distinct from CF-VOLEXP-001** (closed): that axis asked whether *volatility magnitude itself* predicts
  forward realized range (volatility as the signal); here volatility is a **signal-defining partition of a
  different entry** (RSI-MR), tested for the *additive* directional-favourable availability it contributes
  over the unconditioned core within each regime.

### Variant toggles (frozen definitions; batch-1 scope = pooled, NOT regime-cross-cut)

| Toggle | Long rule | Short rule | Batch-1 scope |
| --- | --- | --- | --- |
| **TREND** (`EMA(20)`) | `RSI₂<10 ∧ Close>EMA₂₀` | `RSI₂>90 ∧ Close<EMA₂₀` | pooled sub-screen `CORE+TREND` |
| **RSI-FILTER** (`RSI(5)`) | `RSI₂<10 ∧ RSI₅>50` | `RSI₂>90 ∧ RSI₅<50` | pooled sub-screen `CORE+FILTER` |

### Batch-1 sub-screens (the 6 reads → joint-max family statistic)

`CORE-pooled`, `CORE-VOL-LOW`, `CORE-VOL-MED`, `CORE-VOL-HIGH`, `CORE+TREND-pooled`, `CORE+FILTER-pooled`.
Per-sub-screen `S` = `#cells beats-random` for `CORE`/variants (leg 1) and `#cells (beats-random ∧
beats-CORE)` for the three `/VOLREGIME` sub-screens (leg 2, binding). Within-family multiplicity over the 6
sub-screens is controlled by the **joint max** of the permuted-axis null
(`xen.availability_gate.combine_axis`) — the EXP-086/087 machinery, with a thin extension for the leg-2
conjunctive statistic and the regime-membership null (re-confirmed by the extended bite-check). No cross-axis
Holm (single family).

## Hypotheses (registered; EXP-IDs assigned at promotion)

- `CF-MR-001/HYP-001` — *Availability screen* (Phase 020, **EXP-089**): does the bare RSI-MR core, any of its
  three vol-regime partitions, or either pooled variant beat the multiplicity-adjusted admission gate
  (`S_fam > S*` ∧ axis perm_p ≤ 0.05)? Admit/exonerate, **0 slots, 0 reads**.
- `CF-MR-001/HYP-002` — *Capture-geometry / tradability* (Phase 021, EXP-090→094 TRAIN + **EXP-093** one-shot
  TEST): does the bare fade's gross availability survive a real exit + conservative cost as a positive net
  expectancy clearing the frozen referee, and hold on a counted TEST read? **REFUTED (2026-06-26) — G-021
  RETRACTED** (the EXP-093 "8/11 confirm OOS" was inflated by the EXIT-RCT `rct[di]` exit look-ahead; live-causal
  net-negative — see §CLOSURE).
- `CF-MR-001/HYP-003` — *Deployment economics & global-holdout-final* (Phase 022, EXP-095/096 analysis-set +
  **EXP-097** global-holdout): deployed as a time-aligned, causal, parameter-free ERC portfolio (with an online
  circuit-breaker) under a realistic 1-minute entry fill, does the confirmed fade retain a positive
  risk-adjusted edge that confirms on the final-30% global holdout? 0 new slots; the binding read is the
  single sanctioned global-holdout shot (EXP-097), gated behind the G-022a freeze.
  - **EXP-095 COMPLETE 2026-06-25 (D0-amendment-001 amend-in-place rerun; analysis-set, noise-free — no holdout
    verdict; re-audit PASS).** The rerun restored the D0 §D2.1 **intra-1h mark-to-market** (the prior flat-at-exit
    booking inflated Sharpe/MaxDD differentially across 1h/4h — a verdict-material defect), re-specified the benefit
    criterion (like-for-like LB + cross-cell-median baseline), made Calmar/CVaR/Ulcer co-binding, and replaced the
    fixed-Sharpe=1.0 bite with an MDE-curve. Causal parameter-free ERC portfolio: A Sharpe **11.69 (MBB lo 10.24)**
    / B **11.57 (lo 10.19)** / naive-IV **11.55 (lo 10.07)** / best cell US2000-1h **8.73 (lo 7.53)**.
    **(1) Portfolio benefit SUPPORTED** (corrects the prior flat-at-exit "NOT MET"): A/B Sharpe LB clears every
    baseline (median-cell LB 4.99 +5.25; best-cell point 8.73; best-cell LB 7.53 +2.71; naive-IV LB 10.07) +
    co-binding Calmar LB (+53); mechanism = genuine moment-to-moment diversification of 8 low-correlation cells
    (mean |corr| 0.10) → portfolio MaxDD 0.034 below every constituent. **(2) ERC ≈ naive-IV** (prior refutation
    overturned). **(3) Circuit-breaker NEUTRAL** — A ≈ B within noise (MaxDD 3.44% vs 3.75%; B marginally better on
    Ulcer), no material de-risking (prior "de-risks −22.4%" was a flat-at-exit artifact; a wash, not a
    degradation; B still de-allocates fragile cells). **(4) Gate statistic
    READY** — FPR controlled (A 0.000/B 0.002), MDE m*=1.75/2.00 finite, realized LB 10.24 ≫ m* ⇒
    `statistic_ready_for_g022a=true`; G-022a must freeze the band ≥ m*. **Scale caveat:** Sharpe ~11-12 is
    in-sample favorable-selected, not deployment-realistic; binding read = EXP-097. **Status unchanged: ADMITTED
    (BINDING)/TRADABLE; 0 new slots, 0 counted reads** (11 carried strata stay 1/2). Next: EXP-096 noise infusion
    → G-022a freeze (band ≥ m*; decide A vs B) → EXP-097.
  - **EXP-096 COMPLETE 2026-06-25 (noise infusion / realistic 1-minute entry fill; analysis-set, NO holdout
    verdict; re-audit PASS 0C/0W/5I; 0 reads/0 slots, holdout untouched).** The fill-realism leg of HYP-003: a
    **pure entry-leg perturbation** of the EXP-095 construction (only the entry execution price changes; exit
    target/stop/cost frozen; exit path + keep mask reused verbatim from EXP-093; new
    `xen.intrabar_fill.resolve_entry_fills`), re-derived under the binding v2 fill (next-1m-open + 0.05×ATR
    adverse slippage) with intra-1h MTM; m* **inherited** from EXP-095 (not recomputed). **The diversification
    benefit SURVIVES the binding v2 fill:** A v2 Sharpe 6.50 (MBB LB **5.147**) / B 6.29 (LB 4.90) / naive-IV 6.44
    (LB 5.09); benefit (like-for-like LB vs cross-cell-median single-cell LB **2.554**) A **+2.59 > sampling band
    1.35 = ADDS_VALUE**, co-binding Calmar LB +4.28; **broad-based** (all 8 per-cell v2 Sharpe LBs positive
    0.13–3.65; portfolio LB > best cell — no broken cell masked); ERC ≈ naive-IV. **Mechanism:** v1 latency-neutral
    + a flat 0.05×ATR tick subtracting an EXACT −0.05 ATR/event uniformly → halves BOTH the portfolio LB AND the
    baseline → relative margin preserved (keep mask byte-identical to EXP-093; not variance hiding). **Ladder (A
    Sharpe LB):** ideal 10.28 → v1 10.31 → v2 5.15 → v3 **−1.65** (A BREAKS, MaxDD 40.9%); **v3 B +1.83 (MaxDD
    6.0%)** — v3 a deliberately harsh STRESS CEILING (disclosure-only). **A-vs-B (G-022a input):** circuit-breaker
    NEUTRAL at the binding v2 (A≈B; reproduces EXP-095) but large TAIL-INSURANCE at v3 (de-allocates fragile 1h
    cells USTEC 26.1%/US2000 21.7%; prevents 40.9%→6.0% MaxDD) — real edge-decay-threshold effect → argues for
    Portfolio **B**. **Gate re-check (inherited m*):** v2 A LB 5.15 ≥ 1.75 (+3.40), B LB 4.90 ≥ 2.00 (+2.90) →
    `statistic_clearable_under_noise=true` → G-022a band ≥ m*. **EURJPY-4h flagged NOISE_DEGRADED** (v2 net
    ci_low 0.0079 < 0.025 margin) but net-positive, **RETAINED** (operator portfolio-only membership; G-022a
    decides the holdout-frozen set). Integrity: provenance abs_diff 0.0 vs EXP-093 all 8; MTM conservation
    ≤1.4e-14; determinism/causal-fill/causal-weight PASS; ideal variant reproduces EXP-095 A Sharpe point 11.691
    exactly. Scale caveat: Sharpe ~6-12 in-sample favorable-selected; binding read = EXP-097. **Status unchanged:
    ADMITTED (BINDING)/TRADABLE; 0 new slots, 0 counted reads** (11 carried strata stay 1/2). Next: G-022a freeze
    (band ≥ m*; A-vs-B leans B; decide EURJPY-4h carry) → EXP-097 global-holdout release.

## Kill / pass

- **EXONERATE** the family iff every batch-1 sub-screen `S` falls within the D2a noise band (no sub-screen
  beats the permuted-axis null) → the single-series-directional cell is dead under mean-reversion too; the
  programme returns to the G-019 terminal frontier (non-price data). 0 reads / 0 slots.
- **ADMIT** iff `S_fam > S*` ∧ axis perm_p ≤ 0.05; the winning sub-screen names the lever (bare MR vs a
  specific vol regime vs a variant). CF-MR-001 then consumes its first candidate slot and opens batch 2 at a
  future G0/D0.
- **INCONCLUSIVE** iff the permuted null cannot separate at the realized cell count (no power) — disclosed,
  neither admitted nor exonerated.

## Multiplicity caution (BINDING)

Six sub-screens × 46 cells manufactures cells; the **joint-max permuted-axis null** (D2b) is the binding
control — a lucky single cell or sub-screen must not admit the family. The batch-1 surface is held
deliberately small (one entry, one regime scheme, two variants, partition on the bare core only). All
**deferred** branches are registered now in the multiplicity ledger and consume no count until scoped:
**CONTRARIAN toggle** (flip direction on the RSI-filter axis), **25/75 regime scheme**, **regime × variant
cross-cuts**, **RSI/EMA/ATR/window parameter tuning**, and **instrument/domain/variant expansion**. Adding
any of them requires a dated `D0-amendment-*` and states whether it consumes a new slot.

## Exclusions / deferred

- **No exit / capture-geometry / sizing / cost / P&L work** until availability is admitted (the downstream
  stack is exonerated upstream — EXP-084 — and returns only after a first-order availability edge exists).
- The RSI mean-reversion exit, parameter tuning, the contrarian arm, the 25/75 scheme, and any regime×variant
  cross-cut are **registered-but-deferred** (multiplicity ledger), opened only on ADMIT at a future D0.
- A regime partition earns a leg-2 win only by the **binding beats-random ∧ beats-CORE conjunction** — it must
  *add* favourable availability over the unconditioned core (`Δ̂_core > 0`), never inherit it; the control is
  the standard all-bars direction-matched `SUB-RANDOM` (no regime-matched control — ATR-normalisation removes
  the regime scale).

## G-020 adjudication (BINDING) — 2026-06-23

**ADMITTED.** The predeclared D5 mechanical rule resolves in favour of admission on the realized EXP-089
statistics: `S_fam = 28 > S* = 7` **and** axis perm-p ≈ 0.0002 ≤ 0.05 (FWER 0.05, no cross-axis Holm — single
family). The argmax sub-screen — and therefore the admitted **lever** — is **CORE, the bare RSI-2 fade**.
**CF-MR-001 consumes its first candidate slot.** The vol-regime partition is **inert** (low-priority follow-up);
the TREND/FILTER variants are dead-by-absence and not carried. On admit, the next scope opens the **bare RSI-2
fade, intraday (15m/1h), first** at a future G0/D0 — the availability→tradability (capture-geometry / exit /
cost) step. Admission consumes a **candidate slot, not a counted TEST read**; the holdout stays sealed and
`test-read-ledger.md` is unchanged (all 48 strata 0/2 open). Full adjudication:
[`G-020-gate-review.md`](../../experiments-docs/checkpoints/2026-06-23-020-mean-reversion-entry-availability/G-020-gate-review.md).

## Outcome — EXP-089 (`CF-MR-001/HYP-001`), amended run, 2026-06-23

**`SCREEN_DELIVERED` · provisional ADMITTED (NON-BINDING at screen time; made BINDING ADMITTED at G-020 above).**
Joint-max availability gate:
`S_fam = 28 > S* = 7`, axis perm-p ≈ 0.0002, ADMITTED across FWER {0.025, 0.05, 0.10}, MC-stable. Per sub-screen
`S`: **CORE 28**, CORE-VOL-LOW 22, CORE-VOL-MED 25, CORE-VOL-HIGH 20, CORE+TREND 0, CORE+FILTER 1.

- **Lever = the bare RSI-2 fade (CORE), not the regime partition.** The argmax sub-screen is CORE (z=17.3). The
  three `/VOLREGIME` sub-screens pass uniformly with flat per-cell `Δ̂_rand` (LOW 0.050 / MED 0.080 / HIGH 0.045
  ATR ≈ CORE's 0.060): conditioning on the volatility regime **adds nothing** the unconditioned entry lacks.
  **Leg 2 (the "filter-becomes-the-signal" bet) is empirically inert** on this evidence.
- **Variants are counter-productive:** TREND S=0, FILTER S=1 (trend/momentum agreement contradicts the fade).
- **Effect is intraday and short-lived:** CORE passes 15m 16/16, 1h 11/16, 4h 1/14 (all 16 instruments
  represented); effective ~3-bar horizon; favourable `MFE_med` ≈ 0.75 ATR (Δ̂ ≈ 0.06), measured conservatively.
- **Availability, not tradability** — no exit/cost, gross, TRAIN-only. The binding admit/exonerate is **G-020**.

This is the programme's first non-random price entry to (provisionally) clear the family-selection availability
gate after the Phase 019 terminal branch. On ADMIT, G-020 would open the **bare RSI-2 fade, intraday, first**;
the vol-regime lever is a low-priority follow-up given its inertness here. Artifacts:
[`../../../python/experiments/EXP-089/report.md`](../../../python/experiments/EXP-089/report.md).

## Outcome — EXP-090 (`CF-MR-001/HYP-002`, Phase 021 batch 2), 2026-06-24

**`READINESS_CALIBRATION_DELIVERED` · 20 MEMBER / 12 COVERAGE_EXCLUDED · 0 slots · 0 counted TEST reads · holdout
sealed · audit PASS · AMENDED `D0-amendment-002`.** The availability→tradability step's first experiment: the
bare-fade entry substrate, the new 1-minute intrabar exit-fill engine (`xen.intrabar_fill`), and the binding
mean net-expectancy referee are constructible, deterministic, causal, timestamp-aligned, holdout-fenced, and
**powered** on **20 of 32** cells (10 × 15m + 10 × 1h), which carry to EXP-091 with calibrated margins (RCT
0.0125 / ERT 0.025 ATR = the EXP-093 margins).

- **The 12 excluded cells all fail for the same power reason** — *no finite MDE on either native arm* (cannot
  bound a confirmation at their realized count). NOT an FPR, engine, or coverage failure: every cell is
  `IN_FLOOR`, fill-validity/timestamp/determinism are TRUE on every cell × arm, and the per-cell FPR is
  symmetric and controlled (native-arm median 0.048–0.051; every member's carried arm ≤ 0.050 under **both**
  nulls).
- **No edge is claimed or computed.** The real fade outcomes were never resolved
  (`real_fade_outcomes_resolved: false`) — EXP-091 is the first to read them. The calibration certifies the
  *estimator*, cost-free by translation-equivariance (a valid net margin).
- **Audit trail (3 runs; `D0-amendment-002`):** Run 1 HALTed on a 1-minute fill-engine bug (per-bar window
  over-assignment across dropped/session-gap windows + limit/stop gap-throughs → fills outside `[Low,High]`);
  Run 2 found the analysis-plan's Null B (block-rotated **path**) pathological — it matched entries to wrong-era
  prices, inflating ATR-normalised return variance 30–145× (mean exactly 0), wrongly excluding 14 cells on the
  binding mean. Both fixed and fully re-run: window anchored to each bar's own `(close − period, close]`,
  gap-throughs fill at the touching 1m **open**; Null B reverted to block-permuted **resolved returns** (the
  EXP-001/027/044 form `scope.md` originally specified). The disclosed median leg (D5, non-binding) was dropped
  for performance (binding mean bit-identical to `xen.ass`; runtime 8 h → 67 min).
- **Member-set note vs the intermediate broken-Null-B run (12 members):** 9 robust (member in both), 11
  newly-admitted (the rotation-artifact casualties), 3 boundary-noise dropouts (Null B FPR 0.051–0.057). The
  hard ≤ 0.05 gate (±0.014 Wilson noise at 1000 draws) flips marginal cells; the 9 robust cells are the safest
  EXP-091 evidence.

No countable exit item is screened or refuted here (that is EXP-091). Artifacts:
[`../../../python/experiments/EXP-090/report.md`](../../../python/experiments/EXP-090/report.md) · amendment
[`../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-002.md`](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-002.md).

## Outcome — EXP-091 (`CF-MR-001/HYP-002`, Phase 021 batch 2), 2026-06-24

**`SCREEN_DELIVERED` — non-empty (one exit passes) · 0 slots · 0 counted TEST reads · holdout sealed · audit PASS
(0C/3W/3I).** The first Phase-021 experiment to resolve the **real** bare-fade exit outcomes (EXP-090 never read
them). Over the frozen D2 exit slate on the 20 EXP-090 member cells, net of the operator-ratified Phase-021
conservative cost (`D0-amendment-003`, F=0):

- **EXIT-RCT (native reversion-completion target) is the only arm to pass the frozen D6 quorum** — net-clears
  (`net ci_low_1s>0`) in **5 cells / 5 instruments, all 1h** (EURUSD/GBPUSD/NZDUSD/US2000/USTEC-1h). **EXIT-ERT,
  ATR triple-barrier, RSI-revert-on-close, fixed-bar, and favourable partial/trail each net-clear 0 cells → die
  at the screen** (retained in the file drawer, not reopened by re-parameterization).
- **Mechanism — pure ATR-normalized cost geometry, not signal strength.** Both natives gross-clear 20/20
  (availability real and broad; RCT hits its target ~99% of events, gross ~0.27–0.30 ATR on every cell). But the
  fixed-bps round-trip ÷ entry ATR(14) costs ~0.6 ATR on 15m vs ~0.24–0.30 on 1h, so net is deeply negative on
  every 15m cell (cost ≈ 2× gross) and positive only on the cheapest 1h cells. RCT clears 0/10 on 15m, 5/10 on
  1h — the honest prior *availability ≠ capturable edge* realized exactly for a short ~3-bar, ~0.28-ATR geometry.
- **Native intrabar machinery beats reactive exit-on-close (RCT vs RSI-revert-on-close)** in 20/20 cells (per-cell
  net Δ median +0.261 ATR, Wilcoxon p≈1.9e-6, descriptive) — but RCT-specific; the far native ERT (return to
  EMA10) holds longer into adverse moves and fails entirely.
- **Three caveats binding on EXP-092 (audit verdict forensics):** the pass is (1) **domain-conditional** (1h-only,
  0/10 on 15m); (2) **boundary-fragile** (GBPUSD-1h `net_ci_low` +0.0043 — drop it → 4 cells → fails the quorum);
  (3) **mean/tail-carried on 3 of 5** (net_median<0 on EURUSD/GBPUSD/NZDUSD-1h; only **USTEC-1h & US2000-1h** are
  mean-and-median-positive = the defensible robust core). Faster-cost companion (RT/2): RCT clears 14 cells →
  cost-dominated, not signal-absent.

**Routing: the screen is NON-EMPTY, so Phase 021 ADVANCES to EXP-092** (per-instrument cost-bearing sequence,
TRAIN-only, 0 reads / 0 slots → hash-pinned candidate set + Holm rule), 1h-scoped and centered on the robust
core, rather than closing at G-021 NOT_TRADABLE. The cost table is Phase-021-local (`D0-amendment-003`, hash
`fa7c887…`); the shared `xen.capgeo_cost.COST_CONSTANTS` was not mutated (Phase-018 integrity). Artifacts:
[`../../../python/experiments/EXP-091/report.md`](../../../python/experiments/EXP-091/report.md).

## Outcome — `D0-amendment-004` (4h domain opened, gated behind EXP-094), 2026-06-24

**4h OPENED as a domain expansion of the admitted CORE-fade + EXIT-RCT lever · 0 new candidate slots · 4h NOT
yet admitted.** Triggered by an operator hunch — the **archived, unaudited** side-test `TEMP-091` (EXP-091
frozen slate on 4h only, 13 cost-table instruments, TRAIN-only): **EXIT-RCT net-clears 12/12 instruments on 4h,
every clearing cell mean *and* median positive** (more robust than the 1h EXP-091 pass), while the reactive
RSI-revert-on-close analog of the same entry is net-negative on all 12.

- **The contradiction that gates admission:** EXP-089 found 4h **dead-by-absence (1/14)** — the fade *entry*
  has no favourable-excursion edge above a direction-matched random clock on 4h. On 4h only the proactive
  small resting-limit (RCT) is positive; the reactive same-signal analog and all other arms are negative —
  consistent with RCT harvesting **generic short-horizon oscillation** that nets positive only because
  ATR-normalized cost is tiny on 4h, **not** the RSI-2 fade. TEMP-091's RCT-vs-RSI-revert A/B is an
  *exit-mechanism* contrast and does not discriminate signal from oscillation.
- **Resolution (binding):** 4h is **opened, not admitted**. A new TRAIN-only governed experiment **EXP-094**
  must clear a falsification re-screen — (a) 4h member readiness + finite RCT MDE (EXP-090 analog); (b) the
  frozen net exit screen on 4h (EXP-091 analog, `D0-amendment-003` cost); (c) a **matched-random /
  shuffled-entry RCT null** (EXP-089 `SUB-RANDOM` construction, exit geometry held identical) in which the
  **real-fade entry must beat random entry** on net per-event expectancy (paired Δ, one-sided lower bound > 0)
  in a **≥5-cell / ≥3-instrument quorum**. Admit ⇒ 4h RCT cells become eligible for EXP-092/093 (no new slot);
  (c) fails ⇒ 4h stays **closed, retained** (dead-by-absence reaffirmed, mechanistically explained). A 1h
  positive control assures the test has power. The §4(c) paired-Δ statistic is bite-checked GREEN at EXP-094
  D0 before running.
- **No constant re-tuned;** all other deferred levers remain deferred. TEMP-091 archived to
  `python/experiments/_archive/temp-exp-091/`, recorded in the file drawer regardless of outcome. Amendment:
  [`../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-004.md`](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-004.md).

## Outcome — EXP-094 (`CF-MR-001/HYP-002`, 4h falsification re-screen), 2026-06-24

**`ADMIT_4H` · 4h ADMITTED as a domain expansion · 0 new candidate slots · 0 counted TEST reads · holdout sealed
· audit PASS (re-audit).** EXP-094 cleared the `D0-amendment-004` falsification gate — with the binding null
**corrected by `D0-amendment-005`** to a **matched favourable-target-distance oscillation null** (the original
SUB-RANDOM-entry RCT null was found at Stage 3 to be structurally biased toward admission and was demoted to a
non-binding companion).

- **Readiness corrected the hunch:** **6 MEMBER / 7 COVERAGE_EXCLUDED** on 4h. TEMP-091's naive "RCT net-clears
  12/12" over-claimed — six of those cells (AUDUSD/GBPUSD/NZDUSD/US2000/USDJPY/USTEC-4h) have **no finite RCT
  MDE** (cannot bound a confirmation; JP225-4h build-fails). The powered set is FX-cross/major + gold;
  **the indices TEMP-091 highlighted (USTEC/US2000-4h) are unpowered.** Excluded cells retained in the file drawer.
- **On the 6 powered cells (AUDJPY/EURJPY/EURUSD/GBPJPY/USDCHF/XAUUSD-4h):** real EXIT-RCT beats the **binding
  matched-distance oscillation null 6/6** (`delta_lo` 0.19–0.27) **and** the **realized-capture sensitivity null
  6/6** → the 4h edge is the **fade entry signal, not generic oscillation harvesting**, robust to the
  matched-distance choice. **Mechanism:** entering at a real RSI extreme lifts the reversion-completion hit rate
  **~65% (random timing) → ~99% (real)** for an identical target/stop/fill/cost — the null nets negative
  (−0.09…−0.18), real nets positive (+0.07…+0.16). EXP-089's 4h dead-by-absence is, on these cells, a
  metric-specific false negative of the ~3-bar MFE_med statistic. Net screen 6/6; 1h positive control 5/5;
  **bite-check GREEN** (per-cell power leg corrected after a first-run RED miscalibration). All 6 members
  **mean-AND-median net-positive** (a defensible robust core, unlike the median-fragile 1h EXP-091 pass).
- **Next:** EXP-092 carries the 6 powered 4h cells (smallest-defensible) into the per-instrument cost-bearing
  sequence alongside the 1h survivors; 0 new slots; the counted TEST read is EXP-093 (4h strata 0/2). Amendments:
  [`D0-amendment-004.md`](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-004.md)
  · [`D0-amendment-005.md`](../../experiments-docs/checkpoints/2026-06-23-021-mr-fade-capture-geometry/D0-amendment-005.md).
  Artifacts: [`../../../python/experiments/EXP-094/report.md`](../../../python/experiments/EXP-094/report.md).

## Outcome — EXP-092 (`CF-MR-001/HYP-002`, Phase 021 batch 2), 2026-06-24

**`SEQUENCE_DELIVERED` · candidate set hash-pinned · 0 slots · 0 counted TEST reads · holdout sealed · audit PASS
(0C/0W/4I).** The per-instrument cost-bearing tradability sequence (design §4, D0 §D6/4b; analog EXP-034/083).
EXIT-RCT — the **only** exit to survive the EXP-091 (1h) / EXP-094 (4h) screen (EXIT-ERT + 4 conventional arms
died, retained in the file drawer) — was sequenced on its 11 carried cells: 1h {EURUSD, GBPUSD, NZDUSD, US2000,
USTEC} + 4h {AUDJPY, EURJPY, EURUSD, GBPJPY, USDCHF, XAUUSD}.

- **All 11 carried cells `SEQUENCE_PASS`** (net `ci_low_1s` +0.0044…+0.135 ATR > 0 at α=0.05, power-confirmed by
  the EXP-090/094 MDE) → **hash-pinned candidate set (sha256 `f6427e8342400d46…`) + sized phase Holm rule** for
  the one-shot EXP-093 TEST. Non-empty ⇒ Phase 021 advances to EXP-093 (not G-021 NOT_TRADABLE). This is a
  TRAIN eligibility set, **not** an out-of-sample edge claim.
- **Faithful re-derivation:** each cell's `net_ci_low` reproduces its EXP-091/094 value within ≤6.2e-4
  (independent bootstrap seeds, all same-sign) on byte-identical resolved-event populations — confirms the
  verbatim substrate reuse, not a coincidental pass.
- **Disclosed two-tier quality split (the EXP-093 selection signal):** the 11/11 count masks — but the per-cell
  margin + mean/median flags expose — a **robust core (8)**: all six 4h members + USTEC-1h + US2000-1h
  (margin-clearing AND mean-AND-median positive); a **mean-carried 1h tier (2)**: EURUSD-1h, NZDUSD-1h
  (median<0); and **GBPUSD-1h** (net_ci_low 0.0044 < its 0.0125 margin, median −0.052 → pinned for completeness
  but should NOT be carried to TEST). 4h dominates the ranking because ATR-normalized cost is smaller on the
  slower domain (the EXP-091/094 mechanism). The binding gate is the mean (location); the median is co-reported
  (D5 shape read) — gate-shape OK.
- **Next:** EXP-093 carries the **smallest-defensible robust core** (mean-AND-median-positive, margin-clearing:
  USTEC-1h, US2000-1h, and the six 4h members), ≤1–2 cells per surviving exit/domain at EXP-093's D0, sized to
  the phase Holm rule; **GBPUSD-1h excluded**. Each carried `(instrument, domain)` stratum spends 1 counted TEST
  read (0→1; EURUSD-1h and EURUSD-4h are distinct strata). Artifacts:
  [`../../../python/experiments/EXP-092/report.md`](../../../python/experiments/EXP-092/report.md).

## Outcome — EXP-093 (`CF-MR-001/HYP-002`, Phase 021 batch 2 — the one-shot TEST), 2026-06-24

**`TEST_CONFIRMED` · HYP-002 tradability SUPPORTED · routes G-021 TRADABLE · 11 counted TEST reads (first of the
family) · 0 candidate slots · final-30% global holdout never loaded · audit PASS (0C/1W non-material/3I).** The
phase's single binding tradability read: real EXIT-RCT exits resolved on the **analysis-TEST stratum** of all 11
carried cells (`D0-amendment-006`: full SEQUENCE_PASS set, Holm-11, operator-ratified — superseding the §8.3
smallest-defensible sizing), adjudicated by the frozen D6/4c rule (`CONFIRM iff Holm-adj p ≤ 0.05 ∧ net ci_low_1s
> margin`).

- **8 of 11 cells CONFIRM** at `Holm-adj p = 0.0011`, across **7 instruments and both domains** — the
  **programme's first net-positive out-of-sample price entry**, reversing (for this lever) the G-019
  price→non-price routing. **Robust core = the six 4h cells, mean-AND-median positive** (`net ci_low_1s`
  0.039–0.094 vs the 0.025 margin: EURUSD/XAUUSD/USDCHF/AUDJPY/EURJPY/GBPJPY-4h); plus **two mean-carried 1h**
  confirms (US2000-1h +0.073, USTEC-1h +0.046; USTEC TEST median −0.026 — the binding mean gate passes, median
  fragile).
- **Non-confirm (3, retained):** **GBPUSD-1h** (net_mean −0.080, ci_low −0.103, n=1653) and **EURUSD-1h**
  (−0.010, −0.032, n=1619) are **well-powered net-negative — EVIDENCE_AGAINST** (genuine OOS reversal);
  **NZDUSD-1h** (+0.003, −0.015) is near-zero — **INCONCLUSIVE**. GBPUSD-1h was pre-flagged
  (`D0-amendment-006 §2`) as a near-certain non-confirm (below margin on TRAIN); its read was spent as ratified.
- **Mechanism:** the RCT reversion-completion target is reached ~99% of events; 4h cells clear the net gate by
  the widest margin via **cost geometry** (fixed-bps cost is a smaller ATR fraction on the larger-ATR domain —
  the EXP-091/092 mechanism reproduced OOS, **not** a stronger 4h signal). Every cell shrank TRAIN→TEST (Δ
  net_ci_low −0.005…−0.107, the expected selection-overlap shrinkage); the robust core's larger TRAIN bounds
  absorbed it, the thin-margin 1h tier reversed. Numbers reproduced from raw data; determinism PASS.
- **Reads / holdout:** **11 counted TEST reads, one per carried (instrument, domain) stratum, each 0→1** (cap
  2/stratum; one read preserved); recorded in [`../test-read-ledger.md`](../test-read-ledger.md) in the same
  change. EURUSD-1h and EURUSD-4h are distinct strata. The other 37 strata stay 0/2; the **final-30% global
  holdout is untouched** (a global-holdout release is a separate, later gate).
- **Next (separate gates / scopes):** a sanctioned global-holdout release decision for the mean-AND-median-
  positive 4h core; a 1h median-fragility diagnostic; the deferred levers (vol-regime, contrarian, 25/75, 15m,
  faster-cost sensitivity) each under their own dated `D0-amendment-*` + slot decision. Artifacts:
  [`../../../python/experiments/EXP-093/report.md`](../../../python/experiments/EXP-093/report.md).

## Outcome — EXP-097 (`CF-MR-001/HYP-003`, Phase 022 batch 3 — the global-holdout release), 2026-06-25

**`DEPLOYABLE_CONFIRMED` · HYP-003 deployment leg SUPPORTED OOS-final · the single sanctioned global-holdout shot
SPENT (non-repeatable, non-upgradable, à la EXP-032) · 0 counted TEST reads · 0 candidate slots · audit PASS
(0C/0W/4I) · pre/post-exec governance APPROVE.** The programme's first new-dataset global-holdout read. Deployed as
the G-022a-frozen carry-8 binding-v2 causal ERC portfolio with intra-1h MTM, the primary **Portfolio B** confirms
on the fully-fresh final-30% global holdout:

- **Binding (n=80 holdout weeks):** B holdout ann Sharpe **6.639 (MBB LB 4.762) > band 2.00** (+2.76, 2.4×) AND
  co-binding **Calmar LB 10.731 > 0** → CONFIRM. A co-adjudicated on the same single materialization (one read):
  Sharpe 6.055, LB 4.250 > 1.75, CONFIRM — but **no OR rescue** (terminal keys off B only). naive-IV LB 4.261
  (non-binding contrast).
- **Masking check (broad-based):** 7 of 8 cells carry a positive holdout net ci_low; the only net-negative cell,
  **EURJPY-4h** (net mean −0.006, ci_low −0.031), is exactly the cell pre-flagged `NOISE_DEGRADED` at G-022a and the
  smallest contributor — dropping it would *improve* the book. No broken cell hidden; no one-cell-driven verdict.
- **Mechanism:** the ~6.6 Sharpe is structural (diversified ERC of 8 low-correlation cells, vol-anchored 10%;
  in-family with the analysis-set LB ≈4.9 the band was calibrated against — not a bug). The portfolio did **not**
  decay (B LB 4.897→4.762, Δ−0.135) because per-cell decay was heterogeneous — the three strongest 4h cells
  (EURUSD/XAUUSD/USDCHF) *improved* OOS-final while JPY/index cells decayed — and the **circuit breaker drove B≫A**
  (A LB 5.147→4.250, Δ−0.897) by de-allocating the fragile 1h cells during weak stretches (the tail-insurance role
  EXP-096's v3 probe predicted, and the reason B was primary).
- **Reads / holdout:** the final-30% global holdout was loaded for the first and only time here; recorded as a
  **holdout-governance event** in [`../test-read-ledger.md`](../test-read-ledger.md) +
  [`../multiplicity-registry.md`](../multiplicity-registry.md) in the same change; outside the analysis-TEST
  48-stratum ledger (the 11 carried strata stay 1/2, the other 37 stay 0/2); `counted_test_reads=0`,
  `candidate_slots=0`. Non-repeatable, non-upgradable.
- **Next (separate scopes, post-G-022; each its own dated `D0-amendment-*` + slot decision):** an EURJPY-4h
  drop/book-trim re-cost (deployment engineering, not a holdout re-read); the deferred levers (vol-regime,
  contrarian, 25/75 sizing, 15m domain, regime×variant cross-cuts, faster-cost, instrument/domain expansion).
  Artifacts: [`../../../python/experiments/EXP-097/report.md`](../../../python/experiments/EXP-097/report.md).

## Outcome — EXP-098 (`CF-MR-001/HYP-003`, Phase 022 batch 3 — robustness companion), 2026-06-25

**`CROSS_BROKER_ROBUST` ∧ `AGGREGATION_ROBUST` · non-binding robustness disclosure · 0 candidate slots · 0 counted
TEST reads · INFR-003 holdout NOT loaded · audit PASS (0C/0W/3I) · opened by
[`D0-amendment-002`](../../experiments-docs/checkpoints/2026-06-24-022-portfolio-noise-holdout/D0-amendment-002.md).**
The G-022a-frozen deployment portfolio rerun **verbatim** on an **independent broker's** 1-minute data
(`data/timebars/pps/`, the 8 carry-8 instruments + same span) under two bar-aggregation timestamping methods —
**Arm 1 `PPS-CANON`** (deployed bucket-boundary label) and **Arm 2 `PPS-ALTAGG`** (`AGG-LASTCLOSE` last-source-close
label) — over the full PPS timeline (after the covariance burn-in; operator decision, model fully frozen).

- **Both arms ROBUST:** primary Portfolio B PPS Sharpe LB **5.97 (CANON) / 6.10 (ALTAGG) > band 2.00**, co-binding
  Calmar LB **12.5 / 13.3 > 0** (n=251 evaluable weeks; A co-confirms LB 6.15 / 6.30) → `CROSS_BROKER_ROBUST`
  (Arm 1) ∧ `AGGREGATION_ROBUST` (both). The two overfitting hypotheses EXP-097 could not separate —
  **broker-feed overfit** and **aggregation-method overfit** — are both rejected.
- **Broad-based, no masking:** all **8/8 cells net-positive on both arms** (PPS net ci_low +0.0105…+0.0941);
  **EURJPY-4h** (net-negative −0.006 on the INFR-003 holdout, pre-flagged NOISE_DEGRADED) **recovers to +0.026** on
  PPS; drop-one masking (removes largest contributor US2000-1h) still confirms B (LB 5.48 / 5.57), no flip.
- **Aggregation near-inert:** the arms are near-identical (domain-bar counts equal except USTEC-1h/US2000-1h ±1
  trailing bar; 4h per-cell nets identical to ~1e-5) — the last-source-close relabel can only move the
  trailing/incomplete window, which rarely changes the resolved event population.
- **Mechanism:** the cost-geometry edge (ATR-normalized cost small on the slower domain) is **price-structural,
  not feed-specific**, so it reproduces on PPS (per-cell nets within ~10–25% of INFR-003); the ~7 Sharpe is
  structural diversification of 8 low-correlation cells vol-anchored to 10% (in-family with EXP-097's ~4.9 LBs).
- **Integrity:** MTM conservation ≤2.8e-14; determinism + causal-weight/causal-fill PASS in the evaluable region;
  real-price only; `infr003_holdout_loaded=false`. **EXP-097 `DEPLOYABLE_CONFIRMED` UNCHANGED** — EXP-098 is a
  strengthening robustness companion, **non-upgradable** of the deployment verdict. **PPS now "touched" as a
  robustness dataset** (future binding use needs its own governance). Artifacts:
  [`../../../python/experiments/EXP-098/report.md`](../../../python/experiments/EXP-098/report.md).

---

*All outcomes — admit, exonerate, inconclusive — are **retained** in this file and the Phase 020
multiplicity-registry batch, never deleted or reused. A refuted family is closed and not silently reopened by
re-parameterization.*
