# Family Index — CF-MR-003 (Cross-Domain Mean-Reversion, deviation-from-higher-domain-anchor)

Operator-ratified probe against the terminal-branch prior (Phase 001 §6), admitted only for a
distinguishing information source: **cross-domain deviation + MR-screen-as-selector**, gated
availability-first at zero cost. Registry: `docs/signal-registry/candidate-families/cf-mr-003.md`.
Governing checkpoint: `docs/experiments-docs/checkpoints/2026-07-01-002-cross-domain-mean-reversion/`.

**Status:** **RETIRED — SCREENED-ADMIT (availability) → CONC-1 NOT-TRADABLE (net), family CONCLUDED
(2026-07-01, Phase-003 retrospective).** Arc: EXP-008 methodology finding (vehicle mismatch, L-13; verdict
held) → **EXP-009 SCREENED-ADMIT** (native target-based re-screen: price does return to the higher-domain
anchor beyond a dislocation-matched control, per-stratum, leak-clean) → **CONC-1 NOT-TRADABLE at both
execution horizons**: T1 exec-1h (EXP-010, UNPOWERED) + T2 exec-15m (EXP-012, **POWERED** — 24/24 powered,
0/24 admit, every CI_low ≤ 0). **Availability is real but does not survive to net** — the capturable
reversion move is smaller than the round-trip cost at every horizon tested (the same cost/capture veto that
closed CF-MR-002 and AVWAP). CONC-2+ axis sweep is **moot** (no tradable base; no P-02 dead-entry rescue).
Referee untouched throughout (L-12); 1 candidate slot consumed, 0 counted TEST reads, holdout sealed.
Retained in the registry; re-opening requires a genuinely cheaper capture mechanism or lower-cost universe,
not a re-parameterization. Full arc: [Phase-003 retrospective](../../checkpoints/2026-07-01-003-cf-mr-003-tradability-concretization/retrospective.md).

## Exploration axes & concretization roadmap

Full family surface registered post-ADMIT (2026-07-01). Authoritative detail + dispositions:
`docs/signal-registry/candidate-families/cf-mr-003.md` (§Exploration axes, §Concretization roadmap).
Origin: operator dumps `.ignore/dumps/0-phase002-thoughts.md`, `0-mean-reversion-screening-framework.md`.

**Axes.** A `MR-screen stack` (VR + half-life in use; Hurst-DFA REFUTED-on-levels A1; ADF/KPSS AVOID
parametric; lag-1 autocorr / LOESS deferred; OU characterisation-only). B `/SERIES` (S5 SPREAD ADMIT-robust,
S3 DETREND ADMIT-moderate, S4 OU weak, S1/S2 positive-hint precision-limited, new constructions OPEN).
C `/EXTREME` (robust-z/z/quantile — sweep deferred). D `/DIRECTION` (extreme-primary used; trend/regime
secondary open). E execution machinery **DEFERRED to price-primary**: live-limit entries, `/REENTRY`
none/allow/extend, `/TARGET` mean(screened)/opposite-extreme(deferred), `/EXIT` form-1/form-2/plane.

**Roadmap.** (1) **CONC-1 T1 DONE (EXP-010, 2026-07-01) — NOT-TRADABLE (UNPOWERED)**: 5 distinct S5 exec-1h
cells, exec-grid-β in-engine, form-2 limit; 0/5 powered/admit under the frozen 1h referee (episode sparsity <
min_state 20); availability does not survive to net. 1 slot consumed. **CONC-1b/T2b (S5 exec-15m) + T2a (S3
exec-15m) DONE (EXP-012, 2026-07-01) — NOT-TRADABLE (POWERED)**: 24 exec-15m admits (T2a 14 S3 + T2b 10 S5) under
the frozen 15m referee, 24/24 powered (episodes 70–390 ≥ floor 25), **0/24 admit**, every CI_low ≤ 0 — the powered
definitive close the LOW prior predicted; **F-1 vehicle fidelity PASS all 24 (1.00 / 0.97–0.99) — EXP-010 gate-debt
discharged**; F-2 plant 24/24 + valid live phase-shift future-destroy clean. **⇒ CF-MR-003 TRADABILITY CLOSED**
(availability does not survive to net at 1h or 15m). 0 new slots. (2) **CONC-2+** — sweep deferred axes on a tradable
base (no dead-entry rescue, P-02) — **moot** (no tradable CONC-1 base). (3) **Methodology follow-up** — a Python-side
leak control for a mean referee must break position↔return alignment causally (permute positions + re-assemble), never
permute P&L (which is mean-invariant); or standardize on the in-engine phase-shift shuffle as the sole future-destroy.

## Experiments
- [EXP-008 — cross-domain MR availability screen (HYP-001; methodology finding)](#exp-008)
- [EXP-009 — native re-screen: does price return to the anchor? (HYP-001; SCREENED-ADMIT)](#exp-009)
- [EXP-010 — CONC-1 T1: form-2 limit-at-anchor tradability screen (price-primary; NOT-TRADABLE)](#exp-010)
- [EXP-012 — CONC-1 T2: form-2 limit-at-anchor exec-15m (price-primary; NOT-TRADABLE, POWERED — tradability CLOSED)](#exp-012)

---

## EXP-012 {#exp-012}

**Status**: COMPLETED — **NOT-TRADABLE (POWERED)** · **Date**: 2026-07-01 · audit PASS, 0 Critical ·
price-primary, cTrader in-engine (L-01) · frozen 15m referee (EXP-011, L-12).

### Hypothesis Tests
1. **CF-MR-003 CONC-1 Track 2 (net, TRAIN)** — does the concretized **form-2 limit-at-anchor fade** on the
   EXP-009-admitted **exec-15m** cells earn a net-positive per-15m-bar edge (binding-leg cost charged) that
   clears the **frozen 15m referee** (`gate_stack_pstar`, domain="15m"), per stratum? Two arms, one Holm
   family: T2a = 14 S3_DETREND single-symbol (rolling-OLS trendline residual anchor), T2b = 10 S5_SPREAD
   multi-symbol basket.

### Scope
- **24 cells** = EXP-009 exec-15m admits (`any_pass`). T2a: AUDJPY AUDUSD BTCUSD EURJPY EURUSD GBPJPY GBPUSD
  NZDUSD US2000 USDCAD USDCHF USDJPY USTEC XAUUSD. T2b: AUDUSD EURUSD GBPUSD NZDUSD US2000 US500 USDCAD USDCHF
  USDJPY USTEC. Per-symbol TRAIN fence (first-49% cutoff); holdout sealed.
- Anchor/selector/limit logic in the C# engine (`CrossDomainMrLimitModel.cs`, `--CdmSeries`); S3 OLS anchor
  bit-parity vs `cross_domain_mr.rolling_ols_fit` (Δ 1.8e-15). Python ingest-only (no vectorized backtest).
- Cost = frozen per-instrument 15m round-trip (= 1h value). Intra-position MTM (L-09), one RT/entry (L-02).

### Results / Observations
- **24/24 POWERED** (reversion episodes 70–390 ≥ 15m floor min_state 25) — converts EXP-010's UNPOWERED gap
  into a **definitive powered close**. **0/24 admit, 0/24 Holm-admit.**
- Every CI_lower ≤ 0; net −0.77…+0.04 bps/active (best GBPUSD +0.04 / US2000 +0.02, both CI_low<0; worst
  BTCUSD −0.77, USTEC(T2b) −0.54). T2a 0/14, T2b 0/10 — sub-families agree, no pooled masking.
- **F-1 vehicle fidelity PASS all 24** (z_corr 1.00, Jaccard 0.97–0.99) — clears tightened tol
  (0.90/0.70), **discharges EXP-010 T1's loose-vehicle debt** (0.67/0.30).
- **Power real:** F-2 planted-positive (+8 bps/active) detected 24/24. **Valid future-destroy** (live
  phase-shifted-basket shuffle) CLEAN — 0 survivors, `tripwire_pass=True`.
- **Caveat (see audit.md):** raw-script `REJECT_LEAK` is a **false trip** from a mean-invariant Python
  permutation-destroy (a mean statistic cannot collapse under a mean-preserving permutation) → superseded by
  `verdict_corrected.json`; no verdict-bearing number moves; no re-run (verdict NOT-TRADABLE either way).

### Hypothesis-Specific Conclusion
**NOT-TRADABLE (POWERED).** The form-2 limit-at-anchor MR fade earns no net-positive edge on any exec-15m
admit; the vehicle is faithful (F-1) and adequately powered (plant 24/24), and the valid leak control is
clean. Mechanism: shorter-horizon reversion captures a smaller favourable move against the **same**
round-trip cost. With EXP-010 (exec-1h) + CF-MR-002 exoneration, **CF-MR-003 tradability is CLOSED** —
availability (EXP-009 SCREENED-ADMIT) does **not** survive to net at 1h or 15m. Not a P-02 rescue; LOW prior
held. 0 counted reads (TRAIN disclosure), 0 new slots, holdout sealed, referee untouched (L-12).

### Hypothesis-Agnostic Observations
- Extra 15m bars do clear the higher 15m power floor (episodes 70–390 vs EXP-010's 10–32) — the
  more-episodes-vs-higher-floor tradeoff resolved in favour of powered testability, as the E7 prior expected.
- A permutation of realized P&L is mean-invariant → it is a **vacuous future-destroy for a mean referee**;
  a valid Python-side leak control must break the position↔return alignment causally (methodology follow-up).

**Links**: [design.md](../../../../python/experiments/EXP-012/design.md) ·
[report.md](../../../../python/experiments/EXP-012/report.md) ·
[audit.md](../../../../python/experiments/EXP-012/audit.md)

---

## EXP-010 {#exp-010}

**Status**: COMPLETED — **NOT-TRADABLE (UNPOWERED)** · **Date**: 2026-07-01 · audit PASS, 0 Critical ·
PRICE-PRIMARY in-engine, TRAIN-only, **1 candidate slot**, 0 counted TEST reads, holdout sealed, referee
untouched (L-12).

### Hypothesis Tests
1. **CF-MR-003 CONC-1 (net, TRAIN)** — does the concretized **form-2 limit-at-anchor fade** on the EXP-009-admitted
   S5_SPREAD exec-1h strata produce a **net-positive** per-bar realized edge (binding-leg cost) clearing the frozen
   referee (§10.3a q\*=0.75 + E6 P\*-gate, domain=1h), per stratum?

### Scope
- **5 distinct S5 exec-1h cells** — AUDUSD/GBPUSD/NZDUSD (FX_MAJORS basket), US2000/US500 (INDICES). The EXP-009
  "S5 20 admits" collapse to **15 distinct** (exec-1h 1D/4h-anchor labels are byte-identical for exec-grid-β S5:
  max|Δn_events|=0; the design's earlier 10-cell T1 was corrected to 5 — substrate override of prose).
- In-engine (L-01): S5 anchor = **exec-grid rolling-β** (W_Z=200, class-mate mean log-Close, class−self) via
  multi-symbol `MarketData.GetBars` (XRSI pattern); `StrategyHost/CrossDomainMrLimitModel.cs`. Python adjudicates
  only. First-49% fence; frozen referee domain=1h; Holm(5). Leak tripwire = phase-shifted basket.

### Results / Observations
- **0/5 powered, 0/5 admit.** Per cell (entries · episodes · net bps/active · ci_low · min_state):
  AUDUSD 77·10·−0.26·−0.19·3 · GBPUSD 116·23·+0.10·−0.04·11 · NZDUSD 89·22·−0.26·−0.11·7 ·
  US2000 119·18·−0.70·−0.56·7 · US500 157·32·−0.61·−0.16·15.
- L1 fails on the 1h floor `min_state_count≥20` (all cells 3–17); `min_effective_n=60` met (eff_n≈5000) — power
  fails on **episode count**, not series length. Net ~null-to-negative; only GBPUSD fractionally + (CI covers 0).
- Leak tripwire `surviving-under-shuffle=[]` → PASS **but vacuous** (null live edge; phase-shifted control more
  positive, unpowered noise) → leak-resistance UNTESTED.
- Causal-provenance PASS (decide-before-fold `≤ t-1`; fills executable in-range after the smoke-caught gap-through
  fix; fence sealed). Anchor parity vs `cross_domain_mr`: level corr **0.99** (β correct), dev corr 0.73 / z corr
  0.67 (loose vehicle fidelity — F-1).

> No interpretation in this block — see report.md.

### Hypothesis-Specific Conclusion
**NOT-TRADABLE (UNPOWERED).** The S5_SPREAD availability edge (EXP-009 anchor-hit / fraction-recovered) does **not**
survive to a net-tradable per-bar edge — the VR∧HL∧|z|≥2 conjunction yields too few reversion episodes to power the
1h referee. Read as "could not test at power," not a positive refutation. Consistent with the honest LOW prior +
CF-MR-002 exoneration. Family **retained**.

### Hypothesis-Agnostic Observations
- Concretizing a screened availability vehicle in-engine on **real execution bars** (cTrader 1h) diverges from the
  m1-aggregated screen vehicle (z-selector corr 0.67, |z|≥2 Jaccard 0.30) — the anchor level is faithful (0.99) but
  the residual/extreme is hypersensitive. A tradability concretization is not automatically a tight replica of its
  availability screen (carry as gate-debt F-1).
- A leak tripwire is only informative against a **non-null live edge**; on a null result it is vacuously satisfied
  (F-2) — leak-resistance must be re-established on any future powered positive.

**Links**: [design.md](../../../../python/experiments/EXP-010/design.md) ·
[report.md](../../../../python/experiments/EXP-010/report.md) ·
[audit.md](../../../../python/experiments/EXP-010/audit.md)

---

## EXP-009 {#exp-009}

**Status**: COMPLETED — SCREENED-ADMIT (per-stratum, native vehicle) · **Date**: 2026-07-01 · audit PASS,
0 Critical · ANALYSIS-ONLY, TRAIN-only, 0 counted reads, holdout sealed.

### Hypothesis Tests
1. **CF-MR-003/HYP-001 (native)** — among `|z|≥2` bars at matched dislocation, does the VR∧HL screen pick
   entries whose price **returns to the higher-domain anchor** more (anchor-hit / fraction-recovered /
   time-to-anchor) than a dislocation+regime-matched **screen-fail** control?

### Scope
- 16 inst × 5 anchor series × 3 domain pairs. Selector = 2-leg VR∧HL (from EXP-008 A1). Event-specific
  horizon `H_i=min(48,3·half-life_i)`, horizon-matched control pairing. Endpoint floors E1 hit 0.03 / E2
  frac 0.05 (Amendment B2). Binding leak = pass/fail label-permutation; time-reversal diagnostic-only (B1).
- Exclusions: no strategy/entry/exit/P&L (availability only); TEST + holdout never loaded.

### Results / Observations
- **36 leak-clean per-stratum passes** (any_pass, label-perm collapses): **S5_SPREAD 20** (EURUSD, USDJPY,
  NZDUSD, USDCHF, GBPUSD across pairs), **S3_DETREND 14**, **S4_OU 2**.
- Positive hit-Δ medians all 5 series: S1 +5.2pp, S2 +8.2pp, S3 +6.2pp, S4 +8.8pp, S5 +2.2pp.
- Dispositions: POWERED_PASS 49, POWERED_FAIL 26, UNPOWERED_HINT 253, UNPOWERED_NULL 104.
- Null contrast (passing cells): screen-fail +5pp / random-extreme +2.5pp / random-timing −29pp.
- Sole binding gate = precision (6-gate cascade: Gates 1–4 ≈0; Gate 5 MDE the bottleneck). Screen-fail
  "starvation" hypothesis empirically refuted (fail pool 2000+, D>0 drop 0%).
- Robustness: S5_SPREAD 18–20 (robust), S3_DETREND 8–16 (moderate) across m/H_CAP/z-edges/horizon-method;
  recent-third → 0 (power).

> No interpretation — see report.md.

### Hypothesis-Specific Conclusion
**SCREENED-ADMIT (per-stratum, native vehicle).** CF-MR-003 not exonerated; a broad leak-clean
reversion-to-anchor availability edge (robust S5_SPREAD, moderate S3_DETREND). Availability, not
tradability. EXP-008's EXONERATE was a vehicle artifact (L-13).

### Hypothesis-Agnostic Observations
- Evaluation-vehicle choice (metric + null) determined the sign: MR-native (target-based, dislocation-
  matched, half-life horizon) surfaced the edge the EXP-008 excursion/random-timing vehicle masked.
- S1/S2 UNPOWERED = binary-hit precision at low extreme counts, not no-signal (positive hints).

---

## EXP-008 {#exp-008}

**Status**: INCONCLUSIVE (underpowered) · **Date**: 2026-07-01 · **Instruments**: 16 (INFR-003 5-year,
VAL-003 minus DE30) · **Data Views**: real time-bar OHLC → domain bars {15m,1h,4h,1D}; analysis-only,
TRAIN-only.

### Hypothesis Tests

1. **CF-MR-003/HYP-001** — Do exec-domain entries conditioned on a cross-domain deviation series
   characterised mean-reverting at `≤ t-1` show a favourable reversion excursion toward the
   higher-domain anchor exceeding a matched-random, matched-count, matched-regime within-instrument
   control — for **any** of 5 anchor constructions × 3 domain pairs, per stratum? Edge = Δ-over-random.

### Scope

- **Instruments**: 16-instrument INFR-003 5-year canonical.
- **Anchor-series axis (5)**: S1 CENTER (rolling median), S2 RANGE (Donchian midline), S3 DETREND
  (rolling-OLS-trendline residual), S4 OU (Ornstein-Uhlenbeck equilibrium on HLC3, `0<φ<1` guard),
  S5 SPREAD (rolling-β asset-class basket, cross-instrument).
- **Domain-pair axis (3)**: 4h/1h, 4h/15m, 1D/1h (anchor:exec 4:1 / 16:1 / 24:1).
- **MR screen (selector, `≤ t-1`)**: `VR(q=4)<0.90 ∧ half-life∈(0,48] ∧ Hurst-DFA<0.45`; extreme probe
  `|robust-z| ≥ 2.0`. ADF/KPSS dropped (parametric).
- **Endpoints (per stratum, L-03)**: (L) median excursion; (S) upper-tailmass `#{θ≥1 ATR}/n`.
- **Control**: within-instrument regime-matched (ATR tercile) random timing, matched count.
- **Multiplicity**: cross-axis Holm max-statistic permuted-axis over 15 series×domain axes
  (`xen.availability_gate`). **Effect floor** Δ*=0.10 ATR; `N_min=100`; axis eligible at ≥4 powered cells.
- **Exclusions**: no strategy machinery / cost / P&L / in-engine run; TEST band + global holdout never
  loaded; final-30% sealed.
- **Leak tripwires**: conditioning-label permutation; forward-excursion time-reversal.

### Results / Observations

- **0 / 15 axes eligible; 0 powered instrument-cells** (both endpoints); per-cell **max 18 events**
  (median 7.5); only 33/240 cells cleared the ≥2-event inclusion floor (S3:1, S4:30, S5:1; S1/S2: 0).
- **Drop-one-leg disclosure** (total events over 240 cells / cells ≥100 events): VR 433,790 / 222; HL
  609,626 / 234; **VR+HL 315,644 / 216**; **Hurst-only 792 / 0**; VR+Hurst 528 / 0; HL+Hurst 339 / 0;
  **ALL3 (design) 280 / 0**. On EURUSD·4h/1h S1 the extreme-bar per-leg passes: VR=446, HL=1202,
  **Hurst=0**.
- DFA validated correct (white noise α≈0.52, random walk α≈1.48).
- Leak tripwires shipped + wired (100% finite); no admitting cell to fire on. Holdout sealed; every
  decision input `≤ t-1` (audit provenance trace PASS). Audit **PASS, 0 Critical**.

> No interpretation in this block — see report.md.

### Hypothesis-Specific Conclusion

**INCONCLUSIVE (underpowered).** Per design §7 (`>½ axes ineligible-UNPOWERED`), the MR-screen selects
too few events to test availability. Not EXONERATE — the axes were never powered. CF-MR-003 is neither
admitted nor exonerated; the terminal-branch prior is untested on this vehicle.

### Hypothesis-Agnostic Observations

- The **Hurst-DFA<0.45 leg** is the sole binding constraint: `Hurst<0.5` (increment anti-persistence)
  is mis-applied to mean-reverting deviation **level** series, which are locally **persistent**
  (Hurst>0.5) — contradicting the VR/half-life legs. This is the **L-12 §3 near-impossible-conjunctive-leg**
  pattern reappearing **inside the screen** (not the referee).
- Dropping Hurst (2-leg VR ∧ half-life) powers **216/240** cells — the availability question is testable
  under a corrected selector (new dated-D0 experiment; §7 forbids a goalpost move here).

**Links**: [design.md](../../../../python/experiments/EXP-008/design.md) ·
[report.md](../../../../python/experiments/EXP-008/report.md) ·
[audit.md](../../../../python/experiments/EXP-008/audit.md)
