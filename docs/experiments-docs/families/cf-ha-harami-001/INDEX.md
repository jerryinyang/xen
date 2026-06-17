# CF-HA-HARAMI-001 — Family Index

> Detailed per-experiment cards for the Heiken-Ashi harami candidate family (Phase 014).
> Live programme status and phase retrospectives: [master index](../../INDEX.md).
> Phase design/retrospective narratives: [`../../checkpoints/`](../../checkpoints/).
> Family spec: [`../../../signal-registry/candidate-families/harami.md`](../../../signal-registry/candidate-families/harami.md).
> Compact one-row registry of all experiments: [`python/experiments/INDEX.md`](../../../../python/experiments/INDEX.md).

**Status:** OPEN — **Phase 014 CLOSED at G2 2026-06-17 (NO_PROCEED_TO_SCREEN; family carried OPEN); MA-substrate follow-up next.** Heiken Ashi harami at trend exhaustion, via the Phase 013 pre-committed routing on ANCHOR_MOVE_FLAT. 014-A validated primitives + the unconditioned object (G1 2026-06-15); 014-B measured the conditioned signal across the full barrier + position-management surface under a single terminal G2. **G2 outcome:** no combined definition clears P11 vs the P13 two-baseline conjunction on the registered ZigZag substrate (champion A3 0/99 vs MA(20,50)) → `CHARACTERISED_NOT_VIABLE on ZigZag as configured`; but EXP-060B's SUBSTRATE_LEAD_FOUND (harami beats own-substrate random 85/99 on the MA substrate) forbids a clean close → **family OPEN** on a real, median-only (mean≈0) MA-substrate edge. 0 candidate slots, 0 TEST reads spent in all of 014-B; holdouts sealed. Detection on HA candles; every outcome metric on real prices. Routing: a scoped MA-substrate follow-up (new phase, own D0/G0) — bounded-downside adverse geometry (1:1, `/ADV-EXTREME-rr1`), **mean** as a co-primary endpoint, confronting the 8/14-low-n-4h lead concentration. See [`G2-gate-review.md`](../../checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/G2-gate-review.md) and the Phase 014 [`retrospective.md`](../../checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/retrospective.md).

> **014-A G1** ([`../../checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/G1-gate-review.md`](../../checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/G1-gate-review.md)): primitives READY; benchmark capture `CHARACTERISED_NOT_VIABLE` **on the unconditioned object only**. The **conditioned** family hypothesis (strong-move-qualified harami, anchored at the harami) was never run through an outcome read in 014-A → **untested**; family **OPEN**; operator directed proceed to **014-B** (no closure). Why, and the process lessons, are in [`../../checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md`](../../checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-A-conditioning-gap-and-validation-lessons.md) — **mandatory reading before scoping any 014-B experiment.** 014-B plan: [`014-B-design.md`](../../checkpoints/2026-06-14-014-ha-harami-substrate-and-capture/014-B-design.md) (EXP-053–060, median expectancy endpoint, full surface, no intermediate gates, single G2; **G0-B PASS 2026-06-15** — next: scope EXP-053).

> **Cross-experiment reconciliation caveat (014-B BENCH reads — for G2).** Where a 014-B card below states its BENCH arm "reproduces EXP-053 exactly (diff=0.0)", the reconciliation is on the **point estimates** (`m`, per-event `median`) — verified byte-identical (max |median diff| ≈ 1e-16, max |m diff| = 0). The **moving-block bootstrap CI is *not* reproduced across the experiment scripts**: BENCH `ci_low_1s` differs in ~41–42 of 99 cells (up to **0.115 ATR**) because the bootstrap RNG stream depends on execution context rather than a per-cell fixed seed. On low-n boundary cells this flips viability, so the BENCH *viable count* drifts **7 (EXP-053) → 8 (EXP-056/057/058) → 9 (EXP-059/059B) → 9 (EXP-060)** for the identical benchmark configuration (the flips are AUDUSD-4h, 73 events, ci_low −0.104→+0.010; and AUDUSD-5m, ci_low 0.000→+0.019). This changes **no** 014-B verdict — EVIDENCE_FOR margins clear the ≥5-cell quorum by 23–53 WIN cells, EVIDENCE_AGAINST tops out at 3 WINs, and within each experiment the variant-vs-BENCH paired contrasts share one RNG stream so the WIN logic is internally consistent. **Implication for the single 014-B G2 desk adjudication:** treat absolute BENCH viability on low-n cells as ±1–2 cells uncertain, and adopt a fixed per-cell bootstrap seed before any cross-read viability comparison is made load-bearing.

## Experiments

- **EXP-048** — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami, 102 Cells)
- **EXP-049** — Phase 014-A 3-Barrier Capture Readiness & Gross Capture Rate (ATR-ZigZag Reversals, 99 Cells)
- **EXP-050** — Phase 014-A Harami-in-Context Characterisation
- **EXP-051** — Phase 014-A Strong-Move Filter Characterisation
- **EXP-052** — Phase 014-A Signal-Interpretation Characterisation: Direct vs /CONFIRM Entry (HA Harami, 99 Cells)
- **EXP-053** — Conditioned-Signal Efficacy (HA Harami at Strong-Move Exhaustion, Harami-Anchored)
- **EXP-054** — Intrabar Fill-Model Correction (P15 vs EXP-049 Worst-Case Tie-Break)
- **EXP-055** — Long-Horizon Availability (Conditioned HA Harami; AVWAP-Analog Lifetime MFE/MAE)
- **EXP-056** — Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%)
- **EXP-057** — Adverse-Target Geometry (Conditioned HA Harami; `/ADV-EXTREME`, `/ADV-NONE` vs Benchmark 1:1)
- **EXP-058** — Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)
- **EXP-059B** — Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)
- **EXP-059** — Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)
- **EXP-060** — Combined Event System (Conditioned HA Harami; Best Per-Layer Geometry, 2×2 Favourable×Adverse Factorial + Champion)
- **EXP-060B** — MA(20,50) Substrate Dominance: Genuine Lead or Skew Artifact? (Conditioned HA Harami, EXP-060 gap-fill)
- **EXP-061** — MA(20,50)-Substrate Benchmark-Geometry Conditioned Efficacy (Dual Object: Hybrid + Native, Phase 015 L1)
- **EXP-062** — MA-Substrate Lifetime Availability (Conditioned HA Harami; AVWAP-Analog MFE/MAE, Hybrid, Phase 015 L2)
- **EXP-063** — MA(20,50)-Substrate Adverse Geometry & the Mean Investigation (Conditioned HA Harami; V-BENCH 1:1, V-RR1 `/ADV-EXTREME-rr1`, V-NONE `/ADV-NONE`, V-RAW `/ADV-EXTREME-raw`; Phase 015 L3)

---

## EXP-061 — MA(20,50)-Substrate Benchmark-Geometry Conditioned Efficacy (Dual Object: Hybrid + Native, Phase 015 L1)

**Status:** EVIDENCE_FOR (native) / EVIDENCE_AGAINST (hybrid) — phase verdict EVIDENCE_FOR (stronger object = native)
**Date:** 2026-06-17 (dual-object re-run, `D0-amendment-001-dual-parallel-substrate.md`; supersedes the prior single-object result in place)
**Instruments:** all 17; 99 EXP-060B member cells
**Data Views / Feature Categories:** 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; MA(20,50) crossover substrate (real close); `/STRONG-STAT` strong-move filter (computed on the **ZigZag move** for hybrid, on the **MA segment** for native); benchmark 3-barrier geometry (favourable 50%, adverse 1:1, adaptive time-cap); P15 path-ordered intrabar fills; P14 median ATR-normalised gross return endpoint

### Hypothesis Tests

1. **Hypothesis (HYP-014, Phase 015 L1, dual-object)**: For **each** conditioning object individually (never pooled), does the EXP-060B MA-substrate edge generalise beyond the V2A×ADV-NONE champion geometry to the benchmark 3-barrier geometry (50%×1:1×adaptive cap)? Binding discriminator per object: the signal arm (`H0` hybrid / `M0` native) must be median-viable AND beat its own matched-random null (`RH0`/`RM0`) AND clear P11 with the P6 non-4h rule (≥5 cells, ≥3 instruments, ≥3 cells outside 4h). The genuine **hybrid** object (ZigZag-`/STRONG-STAT` conditioning × MA geometry, 3202-class) is computed here for the first time; **native** (MA-segment `/STRONG-STAT`, 8360-class) is the object the prior EXP-061/EXP-060B `M`-arms actually measured.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: 6 real-domain OHLC views; HA candles for harami detection; MA(20,50) crossover substrate on real close (fixed, not swept); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20) — on ZigZag magnitudes (hybrid) / MA-segment magnitudes (native); benchmark 3-barrier geometry (P2 50%, P3 1:1, P4 adaptive cap `max(6, round(1.5·median(trailing-20 durations)))`); P15 path-ordered fills.
- **Features**: 6 computed objects — **H0** (BENCH-MA-hybrid, ZigZag-conditioned × MA geometry), **RH0** (its matched-random null on MA), **M0** (BENCH-MA-native, MA-segment-conditioned), **RM0** (its null), **Z0** (BENCH-ZZ, disclosed), **RZ0** (disclosed). Matched-random drawn from the in-regime causal pool (same segment/regime, direction, barrier geometry; non-harami timestamps), matched-count **per object** on independent dedicated RNG streams. Independence-assuming contrast CI for `H0−RH0`, `M0−RM0`, `Z0−RZ0`. Hybrid and native **never pooled**.
- **Parameter ranges**: P1 MA(20,50) on real close; P2 favourable 50%; P3 adverse 1:1; P4 adaptive cap; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P15 path-ordered fills; power floor 30; moving-block bootstrap 10,000 draws; per-cell fixed seed (BASE_SEED + cell_index + purpose).
- **Exclusions**: no V2A/ADV-NONE/favourable-alt/third-barrier/exit/horizon arms; no MA-parameter sweep; no costs; no TEST/holdout contact; no pooling of the two objects; 0 candidate slots, 0 TEST reads.
- **Constraints**: TRAIN-only (first 49%, F01 file-order prefix); holdout-safe loading; real-price discipline (HA for detection only); MA/ZigZag segments bounded by pre-entry confirmed pivots (causality gate).

### Results / Observations

- **Phase verdict**: EVIDENCE_FOR (stronger object = native). Native and hybrid diverge sharply.
- **Native `M0` — EVIDENCE_FOR**: generalises in 8 cells (EURUSD-15m/30m, GBPUSD-1h, USDCHF-2h, AUDUSD-30m, NZDUSD-1h/2h, GBPJPY-30m) over 6 instruments, all 8 non-4h. P11 PASS, not fragile. Byte-identical to the prior (mislabelled) EXP-061 result.
- **Hybrid `H0` — EVIDENCE_AGAINST**: generalises in only 1 cell (NZDUSD-5m, marginal contrast CI_low = 0.0035). Median-viable 3 cells, beats-null 2 cells. Powered grid composes (99 cells) ⇒ genuine negative, not power-limited.
- **Where the filter is computed matters**: only the matched-substrate (MA-segment-conditioned) object generalises; conditioning on ZigZag but scoring on MA does not.
- **P12 reconciliation (corrected roles)**: native `M0`↔EXP-060B BENCH-MA and `Z0`↔EXP-053/060B BENCH-ZZ 99/99 at 1e-9; anchorless hybrid `H0` conditioning mask verified via `Z0` 99/99. Matched-count per object OK.
- **Determinism**: 17/17 first-cell replays byte-identical; causality 0; invariants 0; is_defect false.
- **Substrate contrast**: native `M0` beats `RM0` in 8 cells; disclosed `Z0` beats `RZ0` in 7 (different cells, indices/higher TFs); hybrid `H0` beats `RH0` in 2 (does not compose).
- **P4 mean diagnostic**: native `M0` mean-viable in 10 cells; 10% trimmed mean positive in all 8 native binding cells; tail-share 0.23–0.28 (favourable for L3 mean-recovery). Hybrid mean-viable 5 cells (does not compose).
- **Negative/limiting**: MODERATE native breadth (8/99); FX-major concentration; hybrid lone cell marginal; TRAIN-only gross; P15 intrabar approximation.
- **Audit PASS**: 0 Critical, 0 Warning, 2 Info (P15 intrabar approximation — programme convention; DE30 truncated history — non-binding).

### Hypothesis-Specific Conclusion

**Native EVIDENCE_FOR / Hybrid EVIDENCE_AGAINST → phase EVIDENCE_FOR.** The MA-segment-conditioned (native) harami's edge generalises from the EXP-060B champion to the benchmark 3-barrier geometry (8 cells / 6 instruments, all non-4h; not fragile) — confirming the prior EXP-061 result, now correctly attributed to the native object. The genuinely-new hybrid (ZigZag-conditioned) object, computed here for the first time, does **not** generalise (1 cell): the edge depends on conditioning the strong-move filter on the same substrate (MA) whose geometry defines the outcome. Objects reported individually (never pooled); family stays OPEN; the surface runs regardless (P9). Characterisation readout feeds the terminal G-015 after the full Phase 015 slate.

---

## EXP-062 — MA-Substrate Lifetime Availability (Conditioned HA Harami; AVWAP-Analog MFE/MAE, Hybrid, Phase 015 L2)

**Status:** AVAILABILITY_GOOD
**Date:** 2026-06-17
**Instruments:** all 17; 99 EXP-060B member cells (3 COVERAGE_EXCLUDED: US500-4h, JP225-2h/4h)
**Data Views / Feature Categories:** 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; MA(20,50) crossover substrate (real close); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20); lifetime reversal-move (M_b) MFE/MAE excursion window (MA crossover → opposite crossover); 0.5×/1.0× ATR reference lines (reference-only, never subtracted)

### Hypothesis Tests

1. **Hypothesis (HYP-015, Phase 015 L2)**: Does the hybrid `/STRONG`-conditioned HA harami on the MA(20,50) substrate show the AVWAP situation (a meaningful favourable reversal move is *available* but short-horizon capture missed it) rather than the worse alternative of no available reversal move? Mechanical MOVE_AVAILABLE leg: power ≥ 30, median-MFE CI_low > 1.0 ATR, median MFE > median MAE; AVAILABILITY_GOOD iff MOVE_AVAILABLE clears P11 (≥5 cells over ≥3 instruments, P6 non-4h). SIGNAL_ATTRIBUTABLE leg (disclosed secondary): A_MA beats RM_MA (same-regime matched-random on MA) on median-MFE contrast CI_low > 0, P11 quorum.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: 6 real-domain OHLC views; HA candles for harami detection via `xen.heiken_ashi_generator`; MA(20,50) crossover substrate on real close (fixed, not swept); `/STRONG-STAT` live magnitude-percentile filter (`live_in_progress_state` + `live_strong_stat`, window=20, q=0.75).
- **Features**: 4 arms — A_MA (MA-substrate lifetime MFE/MAE), RM_MA (matched-random on MA), A_ZZ (ZigZag reproduction of EXP-055), RM_ZZ (matched-random on ZigZag). Lifetime excursion window M_b = first MA crossover that confirms trend reversal after entry. Matched-random: in-regime non-harami timestamps within same MA segment, same `/STRONG-STAT` qualification. Independence-assuming contrast CI for A_MA−RM_MA. P4 MAE tail decomposition (trimmed mean, tail-share).
- **Parameter ranges**: P1 MA(20,50) on real close (fixed); P7 `/STRONG-STAT` window=20, min=5, q=0.75; reference lines 0.5×/1.0× ATR; power floor 30; moving-block bootstrap 10,000 draws; per-cell fixed seed (BASE_SEED + cell_index + purpose).
- **Exclusions**: no costs; no barrier/partial-exit/stop/trading rule; no candidate slot; no TEST/holdout contact. 0 candidate slots, 0 TEST reads.
- **Constraints**: TRAIN-only (first 49%, F01 file-order prefix); holdout-safe loading (scan+slice before collect); real-price discipline (HA for detection only); MA segments bounded by pre-entry confirmed crossovers (causality gate); P4 tail-share adapted from signed-return to non-negative-excursion context (documented).

### Results / Observations

- **Verdict**: AVAILABILITY_GOOD. **91/99 cells MOVE_AVAILABLE** over all 17 instruments, 77 non-4h. P11+P6 composed. Not fragile.
- **SIGNAL_ATTRIBUTABLE**: 4/99 cells beat RM_MA (EURUSD-4h, USDJPY-1h, GBPJPY-30m, AUDJPY-30m). Does NOT compose P11 (≥5 cells needed).
- **Power**: 99/99 cells powered (≥30 qualifying events); 0 NOT_VIABLE_BY_POWER.
- **Median MFE per cell**: median across cells ~3.84 ATR (range ~1.1–6.6 ATR). **Median MAE per cell**: median ~2.92 ATR. Median MFE > median MAE in 91/99 cells.
- **P4 MAE tail**: median MAE 2.92 < 10%-trimmed mean 3.52 < raw mean 4.60 ATR. Worst-5% tail-share ~0.229. rrADE ~1:1 — thin adverse tail, bounded-downside recovery sized for L3.
- **Reconciliation**: 99/99 cells exact vs EXP-055 (both A_MA/ma_seg and A_ZZ/stat; max |diff| = 0.0).
- **Determinism**: 17/17 first-cell replays byte-identical; causality violations 0.
- **Defect**: false — 0 non-deterministic, 0 causality violations, 0 reconciliation mismatches.
- **Audit PASS**: 0 Critical, 0 Warning, 2 Info (tail-share adaptation documented; determinism gate checks one cell per instrument).

### Hypothesis-Specific Conclusion

**AVAILABILITY_GOOD** — The predeclared branching conditions are met. Move is available on the MA substrate (91/99 cells, P11+P6) but NOT harami-specific (4/99 SIGNAL_ATTRIBUTABLE, below quorum). The MAE adverse tail is bounded-recoverable (tail-share ~0.23), directly sizing the EXP-063 bounded-downside opportunity. The branch reached is **"available but not signal-attributable"** — the favourable room is a generic property of MA-segment length, not harami-specific. Feeds the terminal G-015 after the full Phase 015 slate.

### Hypothesis-Agnostic Observations

- **Ambient MA-segment property**: The lifetime favourable excursion on the MA substrate exceeds 1.0 ATR in 91/99 cells, but this is a property of MA(20,50) segment length — any entry during an MA-trend segment captures the same ambient swing. Per-cell A_MA−RM_MA median −0.198 ATR confirms the harami adds no incremental room vs random MA entries.
- **MA substrate provides substantially more room than ZigZag**: median per-cell MFE ~3.84 ATR (MA) vs ~1.44 ATR (ZigZag, EXP-055). MA segments are ~2.7× longer in excursion units.
- **MAE tail is L3-sized**: The rrADE ≈ 1 confirms a bounded-downside arrangement would cut the adverse tail materially — directly quantifies the EXP-063 opportunity without prejudging its capture reality.
- **DE30 disclosure**: truncated broker history (ends 2026-01-16); DE30 MOVE_AVAILABLE in all 6 domains, consistent with the broad pattern — no material bias.

---

## EXP-063 — MA(20,50)-Substrate Adverse Geometry & the Mean Investigation (Conditioned HA Harami; V-BENCH 1:1, V-RR1 `/ADV-EXTREME-rr1`, V-NONE `/ADV-NONE`, V-RAW `/ADV-EXTREME-raw`; Phase 015 L3)

**Status:** EVIDENCE_FOR (nuanced)
**Date:** 2026-06-17
**Instruments:** all 17 VAL-003-admitted instruments; 96 member cells (3 COVERAGE_EXCLUDED: US500-4h, JP225-2h/4h)
**Data Views / Feature Categories:** 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; MA(20,50) crossover substrate (real close); `/STRONG-STAT` live magnitude-percentile filter (`live_in_progress_state` + `live_strong_stat`, window=20, q=0.75); 4 adverse-target variants via `xen.adverse_targets` (V-BENCH benchmark 1:1, V-RR1 `/ADV-EXTREME-rr1` extreme-anchored ≥1:1, V-NONE `/ADV-NONE` unbounded reference, V-RAW `/ADV-EXTREME-raw` buffered extreme); benchmark favourable 50% + MA adaptive cap (P15 path-ordered intrabar fills); P14 median ATR-normalised gross return (binding); P4 mean diagnostic (raw mean, 10% trimmed mean, worst-5% tail-share, bounded-downside recovery contrast)

### Hypothesis Tests

1. **Hypothesis (HYP-016, Phase 015 L3)**: On the MA(20,50)-substrate conditioned HA harami (hybrid mode), does varying only the adverse target — from the benchmark 1:1 model to the extreme-anchored ≥1:1 stop, to no stop at all, or to a tight buffered extreme stop — (i) preserve a median-viable, signal-attributable edge (P11+P6), and (ii) explain and/or repair the EXP-060B negative mean: is the V-NONE mean negativity a thin, truncatable adverse tail (bounded-downside-recoverable) or a broadly negative distribution (structural)?

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: 6 real-domain OHLC views; HA candles for harami detection via `xen.heiken_ashi_generator`; MA(20,50) crossover substrate on real close (fixed, not swept); `/STRONG-STAT` live magnitude-percentile filter.
- **Features**: 4 adverse variants (V-BENCH, V-RR1, V-NONE, V-RAW) each with its own matched-random-on-MA null (RM-BENCH, RM-RR1, RM-NONE, RM-RAW) through the identical 3-barrier pipeline. Per-cell per-variant: median (binding), raw mean + 10% trimmed mean + worst-5% tail-share (P4 diagnostic), variant−RM contrast CI (signal attribution), bounded-downside recovery contrast mean(V-BENCH/V-RR1) − mean(V-NONE). P11 composition with P6 non-4h rule. Instrument/domain/regime concentration table with low-n-4h flags.
- **Parameter ranges**: P1 MA(20,50) on real close (fixed); P2 favourable 50%; P4 adaptive cap `max(6, round(1.5·median(trailing-20 MA segment durations)))`; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P15 path-ordered fills; power floor 30; regime-clustered MBB bootstrap 10,000 draws; fixed per-cell seed (BASE_SEED + cell_index + purpose) — distinct purposes per variant/statistic so V-BENCH median path stays byte-identical to EXP-061 M0.
- **Exclusions**: no V2A; no favourable-alt/third-barrier/exit/horizon arms (S1–S4); no MA-native; no MA-parameter sweep; no costs; no TEST/holdout contact; 0 candidate slots, 0 TEST reads; `/STRONG-HA` + MAD + ZigZag-adverse secondaries deferred (runtime/budget, recorded in `run_metadata.json`).
- **Constraints**: TRAIN-only (first 49%, F01 file-order prefix); holdout-safe loading (scan+slice before collect); real-price discipline (HA for detection only, all metrics on real OHLC); causality discipline (MA segments bounded by pre-entry confirmed crossovers; `/ADV-EXTREME` faded extreme span `[ma_start_idx+1 … entry_idx]` — all bars at/before entry).

### Results / Observations

- **Verdict**: EVIDENCE_FOR (nuanced) — V-BENCH generalises (8 cells, 6 instruments, 8 non-4h) AND mean_viable composes (10 cells, 6 instruments, 7 non-4h).
- **Median lever**: V-BENCH generalises 8 cells (EURUSD-15m/30m, GBPUSD-1h, USDCHF-2h, AUDUSD-30m, NZDUSD-1h/2h, GBPJPY-30m). V-RR1 generalises 9 cells (adds BTCUSD-5m, EURUSD-30m, GBPUSD-30m, EURJPY-4h). Both clear P11+P6. V-RAW: 0 cells — tight stops clip the edge entirely.
- **Attribution gap**: V-RR1 has 24 median-viable cells but only 9 beat RM (62% drift). V-BENCH 0% drift (8/8). V-NONE 25% drift (72→54).
- **Mean investigation (P4)**: V-BENCH mean_viable 10 cells, V-RR1 mean_viable 11 cells, V-NONE mean_viable 12 cells. **Recovery_positive = 0 for all variants** — formal contrast mean(bounded)−mean(V-NONE) never crosses zero. Bounding does not repair the mean above NONE in any cell.
- **Mean decomposition**: V-NONE trimmed_mean > raw_mean systematically (left-tail-driven). V-BENCH trimmed_mean ≈ raw_mean (stop truncates the tail). V-NONE tail-share ~0.35 (worst 5% contribute ~35% of negative mass); V-BENCH tail-share ~0.22 (stop halves the tail contribution).
- **V-RAW**: 0 powered cells — the tight buffered-extreme stop (sub-1:1 R:R) eliminates all sufficient event counts on the MA substrate.
- **P12 reconciliation**: 99/99 cells match EXP-061 M0 to `1e-9` (reconciliation.csv: all `consistent=true`). V-NONE MAE/tail cross-check consistent with EXP-062.
- **Determinism**: 17/17 instruments byte-identical replay (composition_readout.json `defect.determinism_checked`).
- **Causality**: 96/96 member cells pass `_causality_ok` (readiness.csv `construction_pass=true`).
- **Invariants**: V-NONE 0 ADV outcomes, V-RAW adv_dist ≤ V-RR1 adv_dist event-wise, exit weights sum ≈ 1.0, matched-count holds — all pass.
- **Defect**: false — 0 non-deterministic, 0 causality violations, 0 invariant violations, 0 reconciliation mismatches.
- **Audit PASS**: 0 Critical, 0 Warning, 3 Info (V-BENCH excluded from `build_adverse` dispatch — intentional for M0 reconciliation; `_epochs_to_idx` silent -1 mapping — safe but documented; `_empty_arm` positional args — fragile but correct).

### Hypothesis-Specific Conclusion

**EVIDENCE_FOR** (nuanced) — The P4 closure rule yields EVIDENCE_FOR because V-BENCH generalises (8 cells, 6 instr, 8 non-4h — clears P11 5/3/3) AND mean_viable composes (10 cells, 6 instr, 7 non-4h). This is not the strongest EVIDENCE_FOR — recovery_positive is 0 for every cell — but meets the scope's "and/or" criterion. The median lever works under adverse geometry, and the bounded variants have positive raw means on their own terms, but the formal contrast over NONE never clears zero. The attribution gap (62% for V-RR1) confirms wide stops admit MA drift. Feeds the terminal G-015 after the full Phase 015 slate; no closure or candidate registration here. 0 slots, 0 TEST reads.

### Hypothesis-Agnostic Observations

- **The stop mechanism matters for signal attribution**: V-BENCH (1:1) has 0% attribution gap while V-RR1 (≥1:1) has 62% — narrower stops naturally filter out MA drift, producing a smaller but cleaner harami-signal edge.
- **Mean viability ≠ recovery**: The bounded variants have positive raw means in ~10 cells, but V-NONE also has positive raw means in ~12 cells (different cells). The contrast between them is too noisy to resolve — the mean is *self-viable* but not *recoverable above NONE*. This is a power/width limitation, not a mechanism failure.
- **V-RAW is structurally non-viable on MA**: The tight buffered-extreme stop eliminated all sufficient event counts — a design failure of the tight-stop model on this substrate (vs EXP-057 where it was viable on ZigZag).
- **EVIDENCE_FOR with caveat**: The verdict is real but nuanced — G-015 must weigh whether self-mean-viable (not recovery-positive) evidence is sufficient for PROCEED or requires the MEAN_RECOVERABLE demonstration.

---

## EXP-048 — Phase 014-A Substrate & Detector Readiness (ATR-ZigZag + HA Harami, 102 Cells)

**Status**: READINESS_DELIVERED
**Date**: 2026-06-14
**Instruments**: all 17 (BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225)
**Data Views / Feature Categories**: 1-minute time bars aggregated to 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`) OHLC domains; Heiken Ashi candles from domain bars via `xen.heiken_ashi_generator`; ATR-ZigZag sequential streaming substrate on real bars (Wilder ATR-14, `ATR_MULT=1.0`); HA harami shift-1 vectorized detector on HA candles; no chart-type views

### Hypothesis Tests

1. **Hypothesis** (exploratory readiness, no market-edge claim): For every one of the 102 cells (17 instruments × {5m, 15m, 30m, 1h, 2h, 4h}), the ATR-ZigZag trend substrate (real bars) **and** the HA harami detector (HA candles) can each be computed deterministically, look-ahead-safe, and invariant-clean on the TRAIN analysis stratum; and their measured per-cell move/event rates and `/BARCFG` coverage quantify per-cell context for the downstream capture read (EXP-049).

### Scope

- **Instruments**: all 17 VAL-003/VAL-004-admitted instruments (4 core + 13 new-universe). DE30 with truncated history disclosure.
- **Data Views / Feature Categories**: 6 OHLC domains (5m strict; 15m/30m/1h/2h/4h at 0.90 coverage). HA candles per cell.
- **Primitives** (two independent, frozen defaults): ATR-ZigZag (Wilder ATR-14, `ATR_MULT=1.0`, real bars, sequential streaming) — proof that the substrate is causal and deterministic; HA harami detector (body-inside-prior-body, reduced-form `HAClose₀ ∈ (PrevBodyMin, PrevBodyMax)`, shift-1 vectorized) — proof the detector is invariant-clean.
- **Per-cell checks**: construction integrity (OHLC consistency, monotonic `CloseTime`, dropped-fraction gate); ZigZag invariant battery (alternation, causality, timestamps, threshold breach, monotonic confirmation, no NaN); HA harami invariant battery (reduced-form agreement, adjacency, monotonicity, no NaN); determinism replay (full second pass, frame-identical comparison).
- **Parameters**: `ATR_MULT=1.0`, `atr_period=14`. No sweep, no tuning, no combined event.
- **Time range**: TRAIN only (first 49% via F01 prefix; nested analysis-set TEST + final-30% holdout sealed).
- **Exclusions**: no combined harami-at-trend-exhaustion event (014-B / EXP-050+); no 3-barrier capture, returns, MFE/MAE, expectancy, or edge of any kind; no strong-move filters; no sweep or selection; no TEST/holdout contact; no outcome metrics.

### Results / Observations

- **Status distribution**: 86 READY, 13 READY_FLAGGED, 3 COVERAGE_EXCLUDED (US500-4h, JP225-2h, JP225-4h), 0 CONSTRUCTED_EMPTY, 0 NOT_READY (any type).
- **COVERAGE_EXCLUDED**: US500-4h (dropped 0.286), JP225-2h (0.257), JP225-4h (0.297) — market-hour gap × longest aggregation windows.
- **READY_FLAGGED**: 13 cells across US500, US2000, DE30, JP225, XAUUSD, USTEC — dropped ∈ [0.10, 0.25], all well below the 0.25 exclusion gate.
- **All invariant violations**: 0 on every cell (12 invariant keys, both primitives).
- **All determinism failures**: 0 (102/102 cells PASS frame-identical replay).
- **Move rates** (ATR-ZigZag confirmed moves per 1k domain bars): range [170.2, 207.0] across all non-excluded cells. All 99 cells ≥30 moves (minimum 336).
- **Harami event rates** (per 1k HA candles): range [229.6, 261.4]. All 99 cells ≥30 events (minimum 401).
- **`/BARCFG` coverage** (pooled fractions across domains): UP_UP ~33–35%, DN_DN ~31–34%, UP_DN ~16–18%, DN_UP ~15–17%. Near-symmetric same-direction dominance, consistent with the family's construction-derived reduction.
- **DE30 disclosure**: truncated history (broker ends 2026-01-16); all counts/rates from its own timeline. Rates per 1k comparable; absolute counts systematically lower.
- **SUBSTRATE_REFUTED criteria**: unmet (no non-determinism, no systematic invariant failure on ≥3 instruments).
- **Audit PASS**: 0 Critical, 1 Warning (latent `/BARCFG` null bug — zero-harami guard not exercised in this run), 2 Info.

### Hypothesis-Specific Conclusion

**READINESS_DELIVERED**

Both primitives are mechanically valid across all 99 non-excluded cells: zero invariant violations (both batteries), zero determinism failures (102/102), and the per-cell readiness map, move/event-rate table, and `/BARCFG` coverage table are produced as scoped. The 13 READY_FLAGGED and 3 COVERAGE_EXCLUDED cells are coverage outcomes (dropped-fraction disclosures), not primitive defects. The 99 non-excluded cells clear the substrate/detector gate for EXP-049 capture read. No market-edge claim is tested or implied.

### Hypothesis-Agnostic Observations

- **COVERAGE_EXCLUDED follow EXP-043 pattern**: US500-4h, JP225-2h/4h — market-hour gap × longest aggregation windows. Consistent with the EXP-043 convention; these are permanent cell-level exclusions under the frozen coverage gate.
- **Move rates are instrument-stable**: ATR-ZigZag at `ATR_MULT=1.0` on Wilder ATR-14 produces a narrow 170–207/1k range across 17 instruments × 6 domains — a fixed-parameter pivot-threshold property, not market-structure variation.
- **Harami incidence is near-constant**: ~230–261/1k across all cells — a construction-derived consequence of the reduced-form constraint on `HAClose₀`, not a market signal. Incidence is independent of instrument, domain, or volatility regime.
- **`/BARCFG` near-symmetric**: UP_UP ~33–35% vs DN_DN ~31–34% dominance, expected from the family's reduced-form proof. UP_UP > DN_DN asymmetry consistent with mild bullish TRAIN-period drift.
- **DE30 short history**: Truncated broker history means DE30 bar counts are ~20–30% lower than full-history instruments, though rates per 1k remain comparable. All DE30 cells are READY or READY_FLAGGED (no exclusions from span alone); DE30 pass-through to EXP-049 with disclosure.

---

## EXP-049 — Phase 014-A 3-Barrier Capture Readiness & Gross Capture Rate (ATR-ZigZag Reversals, 99 Cells)

**Status**: CAPTURE_READINESS_DELIVERED
**Date**: 2026-06-15
**Instruments**: all 17; 99 member cells = EXP-048 READY ∪ READY_FLAGGED (3 COVERAGE_EXCLUDED cells excluded per scope)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; ATR-ZigZag trend-change confirmation anchor (Wilder ATR-14, `ATR_MULT=1.0`); P1–P5 Phase 014 benchmark 3-barrier system on real bars; no HA candles, no harami detector

### Hypothesis Tests

1. **Hypothesis (HYP-002)**: For every EXP-048-READY cell, the 3-barrier capture system (P2 favourable, P3 1:1 adverse, P4 adaptive time cap, P5 LOOKBACK=1) can be constructed deterministically and causally on real prices; and the per-cell gross favourable-before-adverse capture rate `r = P(fav before adv | resolved)` is measured under the predeclared default barriers (two geometries: G1 distance-based primary, G2 retracement-level secondary), with P12 viability (`r ≥ 0.55`, `CI_low > 0.50`, `resolved ≥ 30`) and P11 composition (≥5 cells over ≥3 instruments) applied as a mechanical readout.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: 6 real-domain OHLC views (5m strict; 15m/30m/1h/2h/4h at `min_coverage=0.90`); ZigZag trend-change substrate (frozen `xen.zigzag`, unchanged); barrier module `xen.capture_barriers` (new).
- **Features**: per-event favourable/adverse/time-cap/data-censored outcome on real High/Low; per-cell capture rate `r` with regime-clustered moving-block bootstrap CI (MBB, `b=round(m^(1/3))`, `N_BOOT=10_000`); invariant battery (causality, fence, determinism, NaN, G1 well-formedness).
- **Parameter ranges**: P1 ATR-14/1.0; P2 X=50%; P3 1:1; P4 `N=max(6,round(1.5·median(trailing-20 durations)))`; P5 LOOKBACK=1; G1 (distance-based, primary), G2 (retracement-level, secondary).
- **Exclusions**: no HA harami detector or combined harami entry (014-B); no `/CONFIRM` model; no alternative barrier variants (`/VPTARGET`, `/MAGTARGET`, etc.); no strong-move filters; no costs; no TEST/holdout contact; no candidate slot consumption; no returns or edge claims.

### Results / Observations

- **CAPTURE_READINESS_DELIVERED**: 99/99 member cells pass all invariant batteries (0 causality, 0 fence, 0 NaN, 0 G1 fav_dist violations); 0 non-deterministic cells (frame-identical second-pass replay); 0 systematic invariant failures.
- **G1 capture rate (primary/distance-based)**: `r` ranges [0.4545, 0.5343] across all 99 cells, tightly clustered around the 0.50 symmetric-barrier null. **0/99 cells VIABLE** — all `BELOW_R` (r < 0.55). `composition_met = false` (0 cells, 0 instruments). Sensitivity at relaxed bars also `false`.
- **G2 capture rate (secondary/retracement-level)**: `r` ranges [0.3257, 0.4389]. **0/99 VIABLE**. 52–60% of events degenerate (entry at/through midpoint), correctly excluded and disclosed.
- **Power**: all member cells `resolved ≥ 30` (min 128). **0 NOT_VIABLE_BY_POWER** cells.
- **Time-cap censoring (unresolved fraction)**: 22–33% across cells. Data-truncation < 0.5%. Adaptive P4 cap binds at 6-bar floor in 96/99 cells.
- **Determinism**: PASS (full-frame replay, identical CI bounds, 0 degenerate bootstrap resamples in any cell).
- **Audit PASS**: 0 Critical, 0 Warning, 4 Info notes.
- **Verdict stage**: the experiment does not self-adjudicate G1; `composition_met = false` is consistent with design §10 CHARACTERISED_NOT_VIABLE on the capture leg. Desk adjudication combining EXP-048 (leg a), EXP-049 (leg b), and future 014-B (leg c) is pending.

### Hypothesis-Specific Conclusion

**CAPTURE_READINESS_DELIVERED**

Barrier construction is valid on 99/99 cells. The G1 capture-rate readout is uniform negative: 0 VIABLE cells under P12. The capture geometry under benchmark defaults (50% favourable fraction, 1:1 R:R, adaptive time-cap) does not produce a favourable-before-adverse bias above the 0.55 viability bar in any cell of the 17×6 grid. The G2 secondary geometry is systematically weaker due to ~52–60% degeneracy and also 0/99 VIABLE.

### Hypothesis-Agnostic Observations

- **r ≈ 0.50 is a genuine null, not a power failure**: with symmetric equidistant barriers on either side of a ZigZag-confirmation entry, price has approximately equal probability of hitting either target first on this substrate. The null is consistent with a near-random-walk path.
- **G2 degeneracy is structural**: the entry-mostly-inside-midpoint pattern means ZigZag confirmations occur after ~50% giveback of the prior move, so the midpoint is often inside the entry-exit range. This is not a model defect but a property of the `ATR_MULT=1.0` pivot threshold.
- **Adaptive cap binds at floor**: median N_event = 6.0 (floor) in 96/99 cells. The P4 adaptive mechanism delivers no per-cell variation beyond the floor for this substrate — the `/THIRD-TIME` sensitivity branch would be informative only at barrier ratios or k-values above the floor.
- **Barrier system is reusable**: `xen.capture_barriers` passed construction validation and determinism on 99 cells × 2 geometries. Any 014-B variant can reuse it without re-validation.

---

## EXP-050 — Phase 014-A Harami-in-Context Characterisation

**Status**: CONTEXT_CHARACTERISATION_DELIVERED
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-048-READY cells)
**Data Views / Feature Categories**: 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`); HA candles for harami detection; real domain prices for all metrics

### Hypothesis Tests

1. **Hypothesis / exploratory question**: For each EXP-048-READY cell, where in a ZigZag move do raw HA harami signals occur, and does the per-cell final-third rate FT exceed the direction-matched random-timing baseline FT_rand by ≥ 10pp (P9 materiality)?

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: HA candles (via `xen.ha_candles`); real-domain OHLC for positioning; ZigZag moves via `xen.zigzag` (ATR 14/1.0, unchanged).
- **Features**: harami detection (`xen.ha_harami`); pivot-tiling interval join for move-assignment; price-excursion position `pos = (P − S_i) / (E_i − S_i)`; FT = P(pos ≥ 0.67); direction-stratified random baseline FT_rand; regime-clustered MBB CI on Δ = FT − FT_rand; P9/P11 mechanical readout; MA(20,50) alternative-segmentation secondary.
- **Parameter ranges**: P3 position-in-move with D0-ratified 0.67 threshold; P4 ZigZag ATR 14/1.0; P5 direction-matched random baseline (in-move cardinality, 2,000 bootstrap draws); P6 OFF (no /BARCFG filter); P7 `cluster_by_move` bootstrap; P8 two-pass deterministic replay; P9 materiality 10pp; P11 composition ≥5 cells ≥3 instruments FT ≥ 0.50; P13.2 MA(20,50) secondary segmentation.
- **Exclusions**: no ZigZag confirmation filter; no /BARCFG or strong-move filter; no combined harami+barrier event (014-B); no costs; no TEST/holdout contact; no candidate consumption; no returns or edge claims; no direction differentiation in FT (pooled across up/down).

### Results / Observations

- **Verdict**: CONTEXT_CHARACTERISATION_DELIVERED. **0/99 cells CLUSTERED** (all NOT_CLUSTERED). Composition readout: 0 cells, 0 instruments, `composition_met = false` at every support tier and every sensitivity threshold.
- **FT**: range [0.210, 0.312] across 99 cells. FT_rand: range [0.334, 0.432]. Δ = FT − FT_rand: every cell negative; median approximately −0.12 to −0.18 across domains.
- **MA(20,50) secondary (P13.2)**: Δ_ma_vs_rand ≈ 0 (range [−0.041, +0.010]). Front-loading attenuates under MA regime segmentation — it is a ZigZag-specific phenomenon.
- **All invariants pass**: 0 detector self-check, 0 assignment well-formedness, 0 TRAIN fence violations; all 99 cells deterministic; all reportable (min n_assigned = 393).
- **P11 composition**: not met at any sensitivity threshold (strawman 0.50 fails on both FT and FT_rand for every cell).
- **Secondary disclosure**: FT, FT_rand, Δ, FT_ma, FT_rand_ma, Δ_ma recorded per cell in `secondary_disclosure.csv`.

### Hypothesis-Specific Conclusion

**CONTEXT_CHARACTERISATION_DELIVERED.** The raw unfiltered HA harami signal does not cluster near exhaustion on the ATR-ZigZag substrate. Harami timing is systematically front-loaded relative to random in-move timing. This is a clean baseline measurement: the null landscape any filter or confirmation rule must beat is known (Δ ≈ −0.12 to −0.18).

### Hypothesis-Agnostic Observations

- **Front-loading is ZigZag-specific**: under MA(20,50) segmentation, delta clusters near zero. ZigZag defines move starts at pivot extremes; haramis (small consolidations) appear soon after. MA regimes define moves by crossover timing — haramis have no systematic position bias there.
- **Selection force requirement**: a filter must shift the position distribution rightward by ~12–18pp just to reach Δ = 0, and ~22–28pp to meet the P9 materiality threshold.
- **FT never reaches 0.50**: even the unconditioned raw-timing baseline FT_rand is typically 0.33–0.43 (direction-matched uniform draw is the third of the move ≈ 1 − 0.67). The deterministic position-in-move metric therefore cannot resolve a cell in the upper half of the unit interval for this ZigZag geometry.
- **Implication for 014-B**: any combined harami+barrier event definition cannot rely on harami position-in-move as a timing filter — capture barriers (EXP-049/014-B) must manage outcome structurally. EXP-051 (strong-move filters) and EXP-052 (confirmation) should test whether selection can shift the distribution rightward.

---

## EXP-051 — Phase 014-A Strong-Move Filter Characterisation

**Status**: STRONG_FILTER_CHARACTERISATION_DELIVERED
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-048-READY cells)
**Data Views / Feature Categories**: 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`); HA candles for /STRONG-HA impulse-run detection; real domain prices for all magnitude metrics

### Hypothesis Tests

1. **Hypothesis / exploratory question**: For each EXP-048-READY cell, do /STRONG-STAT (p75) and /STRONG-HA (primary same-direction) each carve a materially different move sub-population by P10 (ρ ≥ 1.5 and f ∈ [0.10, 0.50]), and does each meet P11 (≥5 cells over ≥3 instruments)?

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ZigZag moves via `xen.zigzag` (ATR 14/1.0, unchanged); new `xen.strong_move` module for both filter forms.
- **Features**: /STRONG-STAT trailing-window p75 filter (window ≤20, warmup 5; binding form) + median+1×MAD alternative (disclosed); /STRONG-HA qualifying 3-bar impulse-run detection + run→move mapping (primary same-direction binding; any-direction sensitivity disclosed); per-cell ρ/f/P10 point criterion; P11 composition readout; moving-block bootstrap CI on ρ (disclosed); harami-overlap secondary (disclosed); two-pass determinism replay.
- **Parameter ranges**: P7 trailing window 20, warmup floor 5, p75 (binding) + median+1×MAD (disclosed); P8 run length X=3, HA trailing body-median window 20, warmup floor 5 HA bars; P10 ρ ≥ 1.5 ∧ f ∈ [0.10, 0.50]; P11 composition ≥5 cells ≥3 instruments; P6 OFF (no /BARCFG filter).
- **Exclusions**: no 3-barrier capture geometry (EXP-049), no position-in-move (EXP-050), no /CONFIRM entry model (EXP-052), no combined harami+barrier event, no /BARCFG isolation, no costs, no returns/P&L, no TEST/holdout contact, no candidate consumption.

### Results / Observations

- **Verdict**: STRONG_FILTER_CHARACTERISATION_DELIVERED. **Both binding forms clear P11** with 99/99 MATERIAL cells across all 17 instruments.
- **/STRONG-STAT (p75)**: ρ range [1.72, 2.19], median 1.92, IQR [1.86, 1.97]; f range [0.25, 0.32], median 0.27. 99/99 MATERIAL, 17/17 instruments.
- **/STRONG-HA (primary)**: ρ range [1.62, 2.08], median 1.80, IQR [1.76, 1.86]; f range [0.15, 0.24], median 0.20. 99/99 MATERIAL, 17/17 instruments.
- **Alternative-form agreement**: 0 flips between p75↔MAD; 0 flips between primary↔sensitivity. Disclosed forms agree exactly on materiality status.
- **All invariants pass**: 0 filter well-formedness, 0 magnitude validity, 0 HA self-consistency, 0 causality/TRAIN fence violations; determinism PASS; all 99 cells reportable (n_defined 331–31,431).
- **Harami overlap (disclosed)**: overlap_A 65–87% (/STRONG-STAT) and 74–91% (/STRONG-HA); overlap_B 24–46% across both filters.
- **P11 composition**: material_per_domain = 17/17/17/17/16/15 (5m/15m/30m/1h/2h/4h); 3 COVERAGE_EXCLUDED cells (US500-4h, JP225-2h/4h) not in member-cell set.

### Hypothesis-Specific Conclusion

**STRONG_FILTER_CHARACTERISATION_DELIVERED.** Both /STRONG-STAT (p75) and /STRONG-HA (primary) filters identify materially different move populations from the ATR-ZigZag confirmed-move substrate, meeting the P10 bar in every cell and clearing P11 with 99 material cells across all 17 instruments. The disclosed alternative forms agree (0 flips). The experiment verdict is delivery; G1 adjudication is checkpoint desk work.

### Hypothesis-Agnostic Observations

- **p75 mechanical selectivity**: The trailing-window p75 retains ~25% (modulo ties), mechanically inside [0.10, 0.50]. ρ ≥ 1.5 reflects the heavy right tail of move magnitudes — the median of the top quartile is ~1.9× the full median. Uniform 99/99 materiality may partly be a property of the substrate's magnitude distribution, not a special filter property.
- **HA impulse runs as large-move proxy**: The /STRONG-HA detector selects moves containing 3 consecutive strong HA impulse bars. Lower ρ (~1.80 vs ~1.92) suggests HA impulse bars can occur mid-move without the move being in the top magnitude quartile.
- **Both filters viable for 014-B**: The narrow cross-cell IQR (ρ ~0.06–0.10, f ~0.01–0.02 within each form) suggests uniform behaviour across instruments/domains, allowing simpler global parameterisation in 014-B.
- **Overlap_B baseline**: Most haramis (54–76%) occur outside strong moves. A combined-event definition must handle this asymmetry — either by filtering harami detection to strong-move windows or using the strong-move condition as a post-hoc selector on captured haramis.

---

## EXP-052 — Phase 014-A Signal-Interpretation Characterisation: Direct vs /CONFIRM Entry (HA Harami, 99 Cells)

**Status**: CONFIRM_CHARACTERISATION_DELIVERED
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-048-READY cells)
**Data Views / Feature Categories**: 5m (strict), 15m/30m/1h/2h/4h (`min_coverage=0.90`); HA candles for harami detection; real domain prices for all entries, stops, and outcome metrics

### Hypothesis Tests

1. **Hypothesis (HYP-005)**: For each EXP-048-READY cell, both the direct harami entry and the /CONFIRM stop-order entry can be computed deterministically and causally, and their per-cell frequency (fill rate), timing (lead in bars), and subsequent outcome distribution (direction-signed MFE/MAE primary; symmetric fav-before-adv `r` secondary) are measured and compared. No viability threshold — descriptive characterisation only. A non-binding P11-style readout flags where CONFIRM's outcome distribution exceeds DIRECT's.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: 6 OHLC domains; HA candles via `xen.heiken_ashi_generator` (detection only); ATR-ZigZag substrate via `xen.zigzag` (ATR 14/1.0, unchanged); new `xen.confirm_entry` module for reversal-direction assignment, stop level, causal fill scan, and direction-signed MFE/MAE.
- **Features**: per-cell `n_signals` (qualifying haramis), `n_fills`, `fill_rate`; lead times (`lead_direct`, `lead_confirm`, time-to-fill); per-arm direction-signed MFE/MAE ATR-normalized; paired CONFIRM−DIRECT shift on median((MFE−MAE)/ATR); secondary symmetric fav-before-adv `r` (EXP-049-comparable, disclosed); moving-block bootstrap CIs (fixed seed, `B=10_000`); P11 non-binding composition readout; two-pass determinism replay; 4 invariant battery items.
- **Parameter ranges**: P1 ATR 14/1.0; P4 adaptive cap `max(6, round(1.5×median(trailing≤20 durations)))`; P5 LOOKBACK=1; P6 OFF (no strong-move filter); power floor 30; P11 5 cells/3 instruments.
- **Exclusions**: no 3-barrier capture geometry (EXP-049), no position-in-move (EXP-050), no strong-move filters (EXP-051), no combined harami+barrier event (014-B), no /BARCFG isolation, no costs, no returns/P&L, no TEST/holdout contact, no candidate consumption, no viability gate.

### Results / Observations

- **Verdict**: CONFIRM_CHARACTERISATION_DELIVERED. The /CONFIRM arm is deterministic and measurable across all 99 cells, but universally underperforms DIRECT on gross excursion balance.
- **Determinism**: PASS — 0 non-deterministic cells.
- **Invariants**: all 4 battery items pass on all 99 cells (0 violations).
- **Audit**: PASS (0 Critical, 0 Warnings, 3 Info).
- **Fill rate**: median 32.8% (Q25–Q75 30.8–35.4%, range 27.2–42.1%).
- **Lead DIRECT**: median 3 bars, Q25–Q75 [3, 4], range [3, 4].
- **Lead CONFIRM**: median 3 bars, Q25–Q75 [3, 3], range [2, 4].
- **Time-to-fill**: median ~1 bar.
- **DIRECT median((MFE−MAE)/ATR)**: ~0.00 (near zero, replicates EXP-049 null).
- **CONFIRM median((MFE−MAE)/ATR)**: ~−0.58 (systematically negative).
- **Paired Δ (CONFIRM − DIRECT)**: median −0.62, Q25–Q75 [−0.68, −0.54], range [−0.95, −0.35].
- **P11 composition**: 0 positive-shift cells, 99 negative-shift cells, 17 instruments. `p11_neg_readout: true`.
- **DIRECT secondary `r`**: median 0.49 (null, replicates EXP-049).
- **CONFIRM secondary `r`**: median 0.32 (adverse bias, corroborates primary).
- **Per-domain breakdown**: all 6 domains 0 positive, 0 flat; unanimous negative.

### Hypothesis-Specific Conclusion

**CONFIRM_CHARACTERISATION_DELIVERED.** The descriptive comparison of DIRECT vs /CONFIRM entry is complete across all 99 cells. The CONFIRM arm is universally worse than DIRECT on the gross excursion balance — 99/99 cells show a negative paired shift (median −0.62 ATR units). The P11 readout flags a unanimous negative composition (99 cells, 17 instruments). The /CONFIRM stop-order rule (stop at the signal bar's real extreme) is structurally harmful on this substrate under the tested parameters. Fill rate is moderate (~33%); lead times are near-identical between arms.

### Hypothesis-Agnostic Observations

- **Structural adverse mechanism**: The stop level is set at the signal bar's real extreme in the predicted reversal direction. This requires the market to trade through a level that has already rejected the harami direction — the stop systematically selects for adverse entry timing. This is inherent to any stop-order approach that derives its level from the signal bar's range.
- **DIRECT arm confirms EXP-049 null**: DIRECT median((MFE−MAE)/ATR) ≈ 0.00 across all cells is consistent with EXP-049's `r ≈ 0.50` finding — raw HA harami entry with mechanical reversal-direction assignment carries no systematic gross excursion bias.
- **Fill rate is moderate and informative**: ~67% of haramis are not confirmed before the ZigZag's own trend-change confirmation fires. This means the `next_confirm_idx` window is the binding constraint, not the per-bar fill scan — most stops expire because the ZigZag flips first.
- **Implication for 014-B**: Any combined-event definition incorporating a confirmation trigger must account for (a) the moderate fill rate and (b) the structural adverse excursion shift. The DIRECT arm's ~zero gross balance suggests edge must come from filtering (EXP-051 /STRONG variants) or from target geometry (014-B capture), not from the entry interpretation alone.

---

## EXP-053 — Conditioned-Signal Efficacy (HA Harami at Strong-Move Exhaustion, Harami-Anchored)

**Status**: CONDITIONED_EFFICACY_DELIVERED — EVIDENCE_FOR
**Date**: 2026-06-15
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-049 member cells)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection; ATR-ZigZag substrate (ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20); benchmark 3-barrier system (P2 50%/P3 1:1/P4 adaptive time-cap) re-anchored at the harami entry; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised gross return endpoint

### Hypothesis Tests

1. **Hypothesis (HYP-006, the conditioned family hypothesis)**: A HA harami at the probabilistic exhaustion of a strong impulsive move (`/STRONG-STAT` p75), entered at the harami confirmation-bar close and traded as a reversal under benchmark 3-barrier geometry with P15 path-ordered fills, produces positive gross per-event median expectancy (P14) that clears P11 (≥5 viable cells over ≥3 instruments with CI_low > 0 and ≥30 events) and exceeds both P13 matched-control baselines.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain real OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile (p75 of trailing-20 confirmed moves, current-price `M_sofar = |C − StartPrice_inprogress|`); `/STRONG-HA` (X=3 same-direction HA impulse runs) as disclosed secondary; live in-progress state from last confirmed move at each harami timestamp.
- **Features**: per-event median ATR-normalised gross return (P14 endpoint, binding); regime-clustered moving-block bootstrap (10,000 draws; block length `b = round(m^(1/3))`, fixed seed); P15 path-ordered intrabar fill resolution; matched-random and MA(20,50)-segmentation baselines through identical pipeline; P11 composition ≥5 cells ≥3 instruments.
- **Parameter ranges**: P1 ATR 14/1.0; P2 favourable 50%; P3 adverse 1:1; P4 adaptive time-cap `max(6, round(1.5·median(trailing-20 confirmed-move durations)))`, `<5` trailing → warmup-excluded; P5 LOOKBACK=1; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P8 `/STRONG-HA` run_len=3, window=20, min_window=5; P14 median binding (mean disclosed); P15 path-ordered fill model (bullish O→L→H→C; bearish O→H→L→C); power floor 30; N_BOOT=10_000.
- **Exclusions**: no costs; no `/BARCFG` or `/CONFIRM` overlays; no alternative barrier geometries (EXP-056–058); no position-management exits (EXP-059); no parameter tuning; no post-result variant selection; no gate adjudication (single 014-B G2 after full slate); no TEST/holdout contact; 0 candidate slots, 0 TEST reads.
- **Constraints**: TRAIN-only (first 49%); holdout-safe loading (scan+slice before collect); real-price discipline (HA for detection only, all metrics on real OHLC); causality discipline (in-progress state from moves confirmed ≤ t_i, time-cap from moves confirmed strictly < t_i, M_sofar from C and known start pivot); P15 fill model is a documented approximation (EXP-054 bounds its effect).

### Results / Observations

- **Verdict**: CONDITIONED_EFFICACY_DELIVERED — **EVIDENCE_FOR**.
- **P11 viability**: 7 viable cells (CI_low > 0, m ≥ 30) over **6 instruments**. Composition: BTCUSD-5m, BTCUSD-30m, EURUSD-1h, GBPUSD-4h, USDCHF-4h, USDCAD-15m, EURJPY-15m. `composition_met = true`.
- **Baseline beat**: 6/7 viable cells beat **both** matched-control baselines (all except USDCAD-15m), over **5 instruments**. `composition_met = true`.
- **Power**: 99/99 cells powered (all ≥30 qualifying events). Retained fraction ~0.08–0.16.
- **Defect**: false — determinism OK (17 replays), reconciliation OK (17/17).
- **Non-viable**: 92/99 cells CI_SPANS_0 — individually non-viable, concentrated effect pattern.
- **Secondaries**: win rates ~0.46–0.63; r_firsthit ~0.33–0.63; timecap fraction 0.15–0.82 (domain-dependent). Consistent with symmetric 1:1 barriers — positive median expectancy arises from asymmetric return magnitudes, not higher FAV count.
- **Audit PASS**: 0 Critical, 0 Warning, 1 Info (DE30 disclosure — immaterial, DE30 not among viable cells).

### Hypothesis-Specific Conclusion

**EVIDENCE_FOR** — The conditioned family's central efficacy claim is supported on benchmark geometry. Mechanical: `signal P11 = (7 ≥ 5) AND (6 ≥ 3) = True; beats-both P11 = (6 ≥ 5) AND (5 ≥ 3) = True; EVIDENCE_FOR = both True`. The `/STRONG`-conditioned HA harami, anchored at the harami confirmation-bar close and traded as a reversal under benchmark 3-barrier geometry with P15 path-ordered fills, produces positive gross per-event median expectancy that clears programme composition thresholds and exceeds matched controls. This is the first outcome read of the actual conditioned family hypothesis — what 014-A left untested.

### Hypothesis-Agnostic Observations

- **Concentration pattern**: Viable cells cluster in BTCUSD short-term (5m, 30m), EURUSD-1h, and EURUSD/GBPUSD/USDCHF/EURJPY longer-term domains (4h/15m). Non-viable cells include most indices, JPY crosses, and AUD/NZD pairs — the signal is instrument-dependent.
- **Power is robust**: Even with `/STRONG-STAT` retaining ~8–16% of unconditioned haramis, every cell clears the 30-event floor. Conditioning narrows but does not deplete the population.
- **P15 fills are benchmark**: The path-ordered fill model replaces the EXP-049 worst-case tie-break on a near-0.50 r substrate. Positive expectancy under P15 validates the mechanism against a more realistic fill assumption; EXP-054 will quantify the difference from the worst-case baseline.
- **G1 ≡ G2 collapsed**: Under the current-price magnitude-so-far reference, both favourable constructions produce the identical target — a proof that EXP-053's single geometry is complete for this anchor.
- **Audit info note (DE30)**: DE30 truncated history (broker ends 2026-01-16). DE30 is not among the viable cells, so the disclosure is immaterial to the verdict.

---

## EXP-054 — Intrabar Fill-Model Correction (P15 vs EXP-049 Worst-Case Tie-Break)

**Status**: FILL_MODEL_CHARACTERISED (IMMATERIAL)
**Date**: 2026-06-16
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-049 member cells)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; ATR-ZigZag substrate; benchmark 3-barrier geometry (P2 50%/P3 1:1/P4 adaptive time-cap); P15 path-ordered intrabar fills (bullish O→L→H→C, bearish O→H→L→C); EXP-049 worst-case tie-break baseline

### Hypothesis Tests

1. **Hypothesis (HYP-007, the fill-model method-validation hypothesis)**: Replacing EXP-049's worst-case tie-break with the P15 path-ordered intrabar fill model does not materially change the benchmark capture readout — the r~0.50 null across 99 cells is a genuine property of symmetric 1:1 barriers on the unconditioned ZigZag substrate, not a fill-rule artifact.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain real OHLC; ATR-ZigZag substrate (Wilder ATR 14/1.0); benchmark 3-barrier system (P2 50%/P3 1:1/P4 adaptive time-cap); P15 path-ordered intrabar fill resolution applied alongside worst-case tie-break in a single pass.
- **Features**: per-cell Δr = r_P15 − r_wc (binding); same-bar double-touch fraction dt_frac; regime-clustered moving-block bootstrap CI (10,000 draws; block length `b = round(m^(1/3))`) for r under P15; per-cell median expectancy under both fill rules (disclosed secondary); EXP-049 reconciliation (integer and float match); monotonicity (Δr ≥ 0, FAV_P15 ≥ FAV_wc).
- **Parameter ranges**: P1 ATR 14/1.0; P2 favourable 50%; P3 adverse 1:1; P4 adaptive time-cap `max(6, round(1.5·median(trailing-20 confirmed-move durations)))`; P15 path-ordered fill model; EXP-049 worst-case tie-break; power floor 30; N_BOOT=10_000.
- **Exclusions**: no HA harami detector, no `/STRONG` filters, no `/CONFIRM` entry model, no harami anchor, no position-in-move filter, no `/BARCFG`, no alternative barrier models, no costs, no TEST/holdout contact; 0 candidate slots, 0 TEST reads.
- **Constraints**: TRAIN-only (first 49%); holdout-safe loading (scan+slice before collect); real-price discipline; P15 is a documented approximation; DE30 disclosure verified at runtime.

### Results / Observations

- **Verdict**: FILL_MODEL_CHARACTERISED — **IMMATERIAL**.
- **Δr (G1 binding)**: median 0.0101 (IQR 0.0051), range [0.0029, 0.0374]. All cells Δr ≥ 0.
- **dt_frac (G1)**: median 0.0212 (IQR 0.0112), range [0.0029, 0.0794]. Only ~2% of resolved events have tie exposure.
- **P15 G1 viability**: 0/99 VIABLE (identical to worst-case). P11 not met.
- **P15 G2 viability**: 1/99 VIABLE (USDCAD-2h) — isolated cell below P11 3-instrument threshold.
- **TIE_BREAK_SENSITIVE**: 0 cells. No viability flip, no Δr ≥ 0.05.
- **Reconciliation**: all 99 cells PASS — max_abs_diff = 0.0 on counts and CI bounds vs EXP-049.
- **Monotonicity**: all 99 cells PASS — Δr ≥ 0, FAV_P15 ≥ FAV_wc, resolved counts equal.
- **Determinism**: 99/99 cells PASS (two-pass frame-identical).
- **Audit PASS**: 0 Critical, 0 Warning, 2 Info (code hardening between review and execution; G2 isolated viable cell).

### Hypothesis-Specific Conclusion

**SUPPORTED (IMMATERIAL)** — The method-validation hypothesis is supported: the P15 fill model does not materially change the benchmark capture readout. P15 G1 composition is 0/99 VIABLE, P11 is not met, and no cell is TIE_BREAK_SENSITIVE. The fill-model effect is quantified at ~1% median Δr, bounded by ~2% median tie exposure. The EXP-049 benchmark null stands as a genuine substrate property, not a fill-rule artifact. The P15 fill model is adopted as the 014-B fill standard with its effect bounded and documented.

### Hypothesis-Agnostic Observations

- **Low dt_frac is systematic**: ~2% median tie exposure across all 99 cells means that even a perfect intrabar model could shift at most 2% of resolved events on this substrate. The fill-model lever is structurally small on ZigZag-anchored, symmetric-barrier, short-horizon reads — any symmetric-barrier study of ZigZag events will have a similarly bounded fill-model effect.
- **P15 monotonicity is mechanical**: Every cell shows Δr ≥ 0 because the P15 path order can only reassign ties from ADV→FAV. The maximum Δr of 0.037 (US2000-2h) corresponds to the cell with the highest dt_frac (0.079) × ~0.5 reassignment rate — consistent with the mechanism.
- **G2 isolated cell is not actionable**: USDCAD-2h under retracement geometry is VIABLE at r=0.55. A single cell across 99 at the 5% CI threshold is consistent with expected false-positive variation. No family-level implication.
- **Audit info note (code hardening)**: The version that produced results includes DE30 runtime verification, session-model microstructure caveat, and loud-failing CSV schema checking — improvements over the pre-execution-reviewed version. None affect analytical correctness.

---

## EXP-055 — Long-Horizon Availability (Conditioned HA Harami; AVWAP-Analog Lifetime MFE/MAE)

**Status**: AVAILABILITY_GOOD
**Date**: 2026-06-16
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter; lifetime reversal-move (M_b) MFE/MAE excursion window; 0.5×/1.0× ATR reference lines (reference-only, never subtracted)

### Hypothesis Tests

1. **Hypothesis (HYP-008, long-horizon availability)**: For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close), over the full reversal move (M_b) that follows it, does the lifetime favourable-excursion (MFE) vs adverse-excursion (MAE) distribution show the AVWAP situation — a meaningful favourable move is *available* but short-horizon capture (EXP-049/053) missed it — rather than the worse alternative of no available reversal move? Mechanical MOVE_AVAILABLE leg: power ≥ 30, median-MFE CI_low > 1.0 ATR, median MFE > median MAE; AVAILABILITY_GOOD iff MOVE_AVAILABLE clears P11 (≥5 cells over ≥3 instruments).

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain real OHLC; HA candles via `xen.heiken_ashi_generator` (detection only); ATR-ZigZag substrate (`xen.zigzag`, ATR 14/1.0, unchanged); `/STRONG-STAT` live magnitude-percentile filter (`xen.expectancy.live_in_progress_state` + `live_strong_stat`); EXP-047 `move_size.py` lifetime-boundary / excursion / matched-control machinery (reused per P19).
- **Features**: per-event ATR-normalised lifetime MFE and MAE over the reversal-move window `[harami entry+1 → 2nd confirmed ZigZag pivot at/after the harami]` (M_b); regime-clustered moving-block bootstrap (10,000 draws) on median MFE and MAE; mechanical 3-leg MOVE_AVAILABLE test + P11 composition; matched-random and MA(20,50)-segmentation baselines on median MFE (disclosed secondary); two-pass determinism replay; window-invariant battery; EXP-053 population reconciliation.
- **Parameter ranges**: P1 ATR 14/1.0; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P8 `/STRONG-HA` (disclosed secondary); P19 lifetime-availability endpoint; reference lines 0.5×/1.0× ATR (never subtracted); power floor 30; N_BOOT=10_000.
- **Exclusions**: no costs; no barrier, partial exit, stop, or trading rule (EXP-056–060); no first-hit `r` endpoint (excursion endpoint only, per P19); no `/BARCFG` or `/CONFIRM` overlays; no candidate slot; no TEST/holdout contact. 0 candidate slots, 0 TEST reads.

### Results / Observations

- **Verdict**: AVAILABILITY_GOOD. **74/99 cells MOVE_AVAILABLE** over all 17 instruments; `composition_met = true`.
- **Power**: 99/99 cells powered (≥30 qualifying events); pooled qualifying events 89,378; 0 NOT_VIABLE_BY_POWER.
- **Median MFE**: range ~0.90–2.02 ATR units. **Median MAE**: range ~0.65–1.34 ATR. The 74 MOVE_AVAILABLE cells have median-MFE CI_low > 1.0 ATR **and** median MFE > median MAE.
- **NOT_AVAILABLE**: 25 cells, clustered in longer domains (1h/2h/4h) and index instruments (US500, US2000), where wider CIs from fewer events keep CI_low below the 1.0 ATR reference.
- **Baseline beat (disclosed secondary)**: 0 cells beat matched-random or MA(20,50) on median MFE (`beats_both_mfe` empty); all `contrast_low` values negative — the favourable excursion is an ambient reversal-regime property, not entry-specific. (This is a disclosed secondary, not a binding MOVE_AVAILABLE leg.)
- **Defect**: false — 0 non-deterministic, 0 causality/window-invariant violations, 0 EXP-053 reconciliation mismatches (population byte-identical to EXP-053).
- **Audit PASS**: 0 Critical, 0 Warning, 2 Info.

### Hypothesis-Specific Conclusion

**AVAILABILITY_GOOD** — The conditioned harami's predicted reversal move offers a meaningful favourable excursion that robustly clears 1.0 ATR and exceeds adverse excursion across a P11 quorum (74 cells, 17 instruments). This settles the open AVWAP parallel from the 014-A G1 desk: the situation is **move available, capture missing** (keep iterating geometry/exits across EXP-056–060), not the worse alternative of no available move. No edge claim is made (gross; availability is a ceiling on capture). No gate is self-adjudicated (routing is the single 014-B G2).

### Hypothesis-Agnostic Observations

- **Ambient regime property**: the lifetime favourable excursion belongs to the ZigZag-defined reversal-move structure, not to the conditioned harami entry timing — any entry during a strong move captures the same ambient swing (matched-random MFE is comparable or larger; MA(20,50) substantially larger because its segments are longer trends). The question asked was move *existence*, not entry uniqueness, so this contextualises rather than weakens the finding.
- **Availability is broad but not uniform**: most reliable on shorter domains (5m–1h) and major forex pairs; weakest on indices and longer domains where power, not move absence, drives NOT_AVAILABLE.
- **Gross ceiling**: MFE/MAE represent *available* excursion, not capturable return — capture friction (barrier placement, spread, slippage) and the short benchmark cap are what EXP-056–060 measure against this ceiling.
- **DE30 disclosure**: truncated broker history (ends 2026-01-16); DE30 MOVE_AVAILABLE in 4/6 domains, consistent with the broad pattern — no material bias.

---

## EXP-056 — Favourable-Target Geometry (Conditioned HA Harami; `/VPTARGET`, `/MAGTARGET` vs Benchmark 50%)

**Status**: FAVOURABLE_TARGET_CHARACTERISED — EVIDENCE_AGAINST
**Date**: 2026-06-16
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter; `/VPTARGET` volume-profile levels (prior completed move); `/MAGTARGET` trailing-magnitude distances; benchmark 3-barrier geometry (1:1 adverse, adaptive time-cap); P15 path-ordered intrabar fills

### Hypothesis Tests

1. **Hypothesis (HYP-009)**: For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move), at least one alternative favourable-target geometry (`/VPTARGET` volume-profile levels of the prior completed move; `/MAGTARGET` trailing-magnitude distances) produces higher gross per-event median expectancy (P14, ATR-normalised, P15 fills) than the benchmark 50%-of-`M_sofar` favourable target (P2), on the binding `/STRONG-STAT` arm, with the adverse target held at the benchmark 1:1 model and the third barrier at the benchmark adaptive cap (OAT on favourable geometry).

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ATR-ZigZag via `xen.zigzag` (ATR 14/1.0); live magnitude-percentile filter via `xen.expectancy.live_in_progress_state` + `live_strong_stat`; new `xen.favourable_targets` module for `/VPTARGET` volume profile and `/MAGTARGET` trailing magnitude; benchmark barriers, adaptive cap, P15 fills, and bootstrap from `xen.expectancy`.
- **Features**: per-cell per-variant median ATR-normalised gross return (P14 binding endpoint); regime-clustered MBB (10,000 draws; block length `b = round(m^(1/3))`, fixed seed); P15 path-ordered intrabar fill resolution; paired variant-benchmark contrast on the common qualifying subset; matched-random and MA(20,50)-segmentation baselines through identical pipeline (disclosed); P11 composition readout (≥5 cells ≥3 instruments, WIN = viable + beats benchmark).
- **Variant grid (predeclared, 8 binding + 1 disclosed)**: BENCH (50%-of-`M_sofar`); VP-POC, VP-NEAR, VP-FAR (prior completed move volume profile, 70% VA, bin width = 0.10 × `ATR_entry`); MAG-0.5×5, MAG-1.0×5, MAG-0.5×20, MAG-1.0×20 (trailing magnitude `frac × median(W)`); disclosed secondary: in-progress VP-POC.
- **Parameter ranges**: P1 ATR 14/1.0; P2 BENCH 50%; P3 1:1 (benchmark adverse, fixed); P4 adaptive cap `max(6, round(1.5·median(trailing-20 confirmed-move durations)))`; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P14 median binding; P15 path-ordered fill model; P11 composition; VP bin width 0.10×ATR, VA 70%, insufficient-profile floor 3 bars; MAG grid `frac∈{0.5,1.0}×W∈{5,20}`; power floor 30; N_BOOT=10_000.
- **Precommitments**: no post-result variant selection; all 8 variants reported; no gate adjudication (single 014-B G2 after full slate); 0 candidate slots, 0 TEST reads.
- **Exclusions**: no costs; no `/ADV-EXTREME`/`/ADV-NONE` (EXP-057); no `/THIRD-EVENT`/`/THIRD-TIME` (EXP-058); no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-059); no combined system (EXP-060). No `/BARCFG` or `/CONFIRM` overlays. No TEST/holdout contact. No candidate consumption. TickVolume broker proxy disclosed per scope.

### Results / Observations

- **Verdict**: FAVOURABLE_TARGET_CHARACTERISED — **EVIDENCE_AGAINST**. No variant clears P11 WIN (≥5 cells over ≥3 instruments). `n_pass = 0`, `passing_variants = []`.
- **BENCH viability**: 8 cells, 7 instruments — reproduces EXP-053 exactly (99/99 cells m+median match to machine precision).
- **VP-POC**: 7 viable cells / 6 instruments; **0 WIN cells**.
- **VP-NEAR**: 6 viable cells / 4 instruments; **0 WIN cells**.
- **VP-FAR**: 5 viable cells / 5 instruments; **0 WIN cells**.
- **MAG-0.5x5**: 4 viable cells / 4 instruments; **2 WIN cells** on 2 instruments (USDCHF-4h, AUDJPY-30m).
- **MAG-1.0x5**: 5 viable cells / 5 instruments; **0 WIN cells**.
- **MAG-0.5x20**: 4 viable cells / 3 instruments; **2 WIN cells** on 2 instruments (USDCHF-4h, AUDJPY-30m).
- **MAG-1.0x20**: 8 viable cells / 6 instruments; **1 WIN cell** on 1 instrument (USDCHF-5m, marginal +0.000165 ATR units).
- **Power**: 99/99 cells powered (≥30 qualifying events) on all 8 variants. Exclusion counts (VP: insufficient profile, level on wrong side; MAG: warmup) do not deplete power.
- **All invariants pass**: 0 variant-construction, 0 paired-contrast, 0 causality, 0 TRAIN fence violations.
- **Determinism**: 17/17 cells (first usable per instrument) PASS byte-identical.
- **Reconciliation vs EXP-053**: 99/99 cells PASS — diff = 0.0 on m and median.
- **Defect**: false — 0 non-deterministic, 0 causality violations, 0 reconciliation mismatches.
- **Audit PASS**: 0 Critical, 0 Warning, 0 Info.

### Hypothesis-Specific Conclusion

**EVIDENCE_AGAINST** — The hypothesis is conclusively not supported at any of the 8 tested alternative favourable-target geometries. The falsifiable condition (no alternative clears P11 WIN) is met. Favourable-target geometry — whether derived from the prior move's volume profile or from trailing-magnitude estimates — is not a lever that systematically improves conditioned capture on this surface under the benchmark 1:1 adverse model and adaptive time cap. The 50%-of-`M_sofar` benchmark is competitive with or superior to all tested alternatives.

### Hypothesis-Agnostic Observations

- **The adaptation-enriched benchmark is hard to beat**: The 50%-of-in-progress-magnitude-so-far level adapts to the current move's size in real time. Every alternative tested (static VP levels, trailing magnitude) lacks this in-event adaptation — and the 50% benchmark won in every comparison.
- **VP prior-completed-move profiles are structurally orthogonal**: Volume profile levels track where price *was* in the completed move, not where the reversal's favourable target *will be*. The POC often lies near the move's midpoint (similar to 50%), but the far edge pushes too far out. This is not a parameter issue — it is a structural misalignment.
- **MAG trailing-magnitude 0.5× fraction is the closest competitor**: The two sparse WIN concentrations (USDCHF-4h, AUDJPY-30m) both come from `frac=0.5` — the median trailing magnitude halved. A smaller fraction than the benchmark's implicit fraction is directionally interesting but far below P11.
- **Implication for 014-B**: The favourable-target leg is measured and closed on 8 distinct geometries + 1 disclosed secondary, all negative at P11. This does not short-circuit the remaining surface reads — the binding constraint may sit in the adverse model (EXP-057), the third barrier / time horizon (EXP-058), or position management (EXP-059).

---

## EXP-057 — Adverse-Target Geometry (Conditioned HA Harami; `/ADV-EXTREME`, `/ADV-NONE` vs Benchmark 1:1)

**Status**: ADVERSE_TARGET_CHARACTERISED — EVIDENCE_FOR
**Date**: 2026-06-16
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter; 4 predeclared adverse-target variants; benchmark 3-barrier geometry (P2 50%/P4 adaptive time-cap); P15 path-ordered intrabar fills; P14 median per-event ATR-normalised gross return endpoint

### Hypothesis Tests

1. **Hypothesis (HYP-010)**: For the live `/STRONG-STAT`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move), at least one alternative adverse-target geometry (`/ADV-EXTREME` raw or ≥1:1-constrained; `/ADV-NONE`) produces higher gross per-event median expectancy (P14, ATR-normalised, P15 fills, real prices) than the benchmark 1:1 adverse target (P3), on the binding `/STRONG-STAT` arm, with the favourable target (50%-of-`M_sofar`) and third barrier (adaptive time cap) held at benchmark (OAT on adverse geometry).

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ATR-ZigZag via `xen.zigzag` (ATR 14/1.0); live magnitude-percentile filter via `xen.expectancy.live_in_progress_state` + `live_strong_stat`; new `xen.adverse_targets` module for faded-move extreme scan, raw/rr1 adverse builders, and ADV-NONE sentinel.
- **Features**: per-cell per-variant median ATR-normalised gross return (P14 binding endpoint); regime-clustered MBB (10,000 draws; block length `b = round(m^(1/3))`, fixed seed); P15 path-ordered intrabar fill resolution; paired variant-benchmark contrast on the common qualifying subset; matched-random and MA(20,50)-segmentation baselines through identical pipeline (disclosed); P11 composition readout (≥5 cells ≥3 instruments, WIN = viable + beats benchmark).
- **Parameter ranges**: P1 ATR 14/1.0; P2 favourable 50%; P3 1:1 (benchmark adverse, fixed); P4 adaptive cap `max(6, round(1.5·median(trailing-20 confirmed-move durations)))`; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P14 median binding; P15 path-ordered fill model; P11 composition; `/ADV-EXTREME` buffer = 0.25·ATR_entry, ADV_FLOOR = 0.10·ATR_entry (raw only); power floor 30; N_BOOT=10_000.
- **Precommitments**: no post-result variant selection; all 4 binding variants reported; family-wise correction deferred to single 014-B G2; 0 candidate slots, 0 TEST reads.
- **Exclusions**: no costs; no `/VPTARGET`/`/MAGTARGET` (EXP-056); no `/THIRD-EVENT`/`/THIRD-TIME` (EXP-058); no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-059); no combined system (EXP-060). No `/BARCFG` or `/CONFIRM` overlays. No TEST/holdout contact. No candidate consumption.

### Results / Observations

- **Verdict**: ADVERSE_TARGET_CHARACTERISED — **EVIDENCE_FOR**. One alternative passes P11 WIN: ADV-NONE (23 cells, 15 instruments).
- **ADV-NONE**: 99/17 powered, 27 viable cells/15 instruments, **23 WIN cells over 15 instruments** — P11 met robustly (not fragile). Paired contrast vs BENCH CI_low > 0 in 23 cells. BTCUSD-5m: median +0.163 ATR (benchmark +0.057), contrast_bench_low = +0.083. r = 1.0 (degenerate by construction — no ADV possible with ±∞ sentinel).
- **BENCH (1:1)**: 99/17 powered, 8 viable/7 instruments (reference, 0 WIN). r ≈ 0.506 — replicates EXP-053/049 null.
- **ADV-EXTREME-raw**: 99/17 powered, **0 viable cells, 0 WIN cells**. Median negative in every cell. BTCUSD-5m: median −0.368 ATR, r ≈ 0.28.
- **ADV-EXTREME-rr1**: 99/17 powered, 8 viable/7 instruments, **0 WIN cells**. Median ≈ BENCH (BTCUSD-5m: +0.059 vs +0.057) — extreme-anchoring alone at ≥1:1 does not beat benchmark.
- **Defect**: false — 0 non-deterministic, 0 causality violations, 0 reconciliation mismatches (99/99 BENCH cells match EXP-053 exactly), 0 invariant violations.
- **Determinism**: 17/17 cells PASS byte-identical replay.
- **Reconciliation vs EXP-053**: 99/99 cells PASS — diff = 0.0 on m and median.
- **Secondaries**: ADV-NONE also passes on `/STRONG-HA` arm; effect robust to STAT-MAD sensitivity. Matched-random baselines show conditioned ADV-NONE beats random entries under same geometry.
- **Audit PASS**: 0 Critical, 0 Warning, 2 Info (duplicated `_zero_reasons` helper; TickVolume loaded for aggregation parity pre-approved).

### Hypothesis-Specific Conclusion

**EVIDENCE_FOR** — One alternative adverse-target geometry (`/ADV-NONE`) improves conditioned capture over the 1:1 benchmark, clearing P11 with 23 cells over 15 instruments. The tight extreme-anchored stop (`/ADV-EXTREME-raw`) is destructive (0 viable). The extreme stop widened to 1:1 R:R (`/ADV-EXTREME-rr1`) ties the benchmark (0 WIN) — isolating the mechanism: removing the stop entirely is what helps, not repositioning it. Characterization readout feeding the single 014-B G2; no candidate registration.

### Hypothesis-Agnostic Observations

- **The r-expectancy divergence is the headline lesson**: ADV-EXTREME-raw pushes r well below 0.50 yet expectancy is negative; ADV-NONE produces degenerate r = 1.0 yet expectancy is positive. The median endpoint (P14) correctly captures what r misses.
- **The lever is structural, not parametric**: The raw/rr1 pair shows extreme-anchoring itself does not matter when R:R is equated. The effect comes from removing the stop's presence entirely.
- **ADV-NONE is breadth-robust**: 15 of 17 instruments have at least one WIN cell. The effect is not concentrated in a single sector.
- **DE30 has WIN cells (DE30-5m, DE30-15m)** despite truncated history — encouraging but carries the VAL-003 disclosure.

## EXP-058 — Third-Barrier Geometry (Conditioned HA Harami; `/THIRD-TIME`, `/THIRD-EVENT` vs Benchmark Adaptive Cap)

**Status**: THIRD_BARRIER_CHARACTERISED — EVIDENCE_AGAINST
**Date**: 2026-06-16
**Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter; 5 predeclared third-barrier variants; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised gross return endpoint

### Hypothesis Tests

1. **Hypothesis (HYP-011)**: For the live `/STRONG-STAT`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move), at least one alternative third-barrier geometry (`/THIRD-TIME` floor ∈ {12, 24, 48}; `/THIRD-EVENT` with ZigZag `rd`-confirm and 8× backstop) produces higher gross per-event median expectancy (P14, ATR-normalised, P15 fills, real prices) than the benchmark floor-6 adaptive time cap (P4), with the favourable target (50%-of-`M_sofar`) and adverse target (1:1) held at benchmark (OAT on third-barrier geometry).

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ATR-ZigZag via `xen.zigzag` (ATR 14/1.0); live magnitude-percentile filter via `xen.expectancy.live_in_progress_state` + `live_strong_stat`; new `xen.third_barrier` module for adaptive time-cap variants and event-based caps.
- **Features**: per-cell per-variant median ATR-normalised gross return (P14 binding endpoint); regime-clustered MBB (10,000 draws; block length `b = round(m^(1/3))`, fixed seed); P15 path-ordered intrabar fill resolution; paired variant-benchmark contrast on the common qualifying subset; P11 composition readout (≥5 cells ≥3 instruments, WIN = viable + beats benchmark).
- **Parameter ranges**: P1 ATR 14/1.0; P2 favourable 50%; P3 1:1 (fixed); P4 benchmark adaptive cap `max(6, round(1.5·median(trailing-20 confirmed-move durations)))`; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P14 median binding; P15 path-ordered fill model; P11 composition; `/THIRD-TIME` floors {12,24,48}; `/THIRD-EVENT` definition (next `rd`-confirm exit, 8× bench_N backstop); power floor 30; N_BOOT=10_000.
- **Precommitments**: no post-result variant selection; all 5 binding variants reported; family-wise correction deferred to single 014-B G2; 0 candidate slots, 0 TEST reads.
- **Exclusions**: no costs; no `/VPTARGET`/`/MAGTARGET` (EXP-056); no `/ADV-EXTREME`/`/ADV-NONE` (EXP-057); no `/EXIT-PARTIAL`/`/EXIT-TRAIL-STRUCT` (EXP-059); no combined system (EXP-060). No `/BARCFG` or `/CONFIRM` overlays. No TEST/holdout contact. No candidate consumption.

### Results / Observations

- **Verdict**: THIRD_BARRIER_CHARACTERISED — **EVIDENCE_AGAINST**. No alternative clears P11 WIN (max 3 cells, need ≥5 over ≥3 instruments).
- **BENCH (floor=6)**: 99/17 powered, 8 viable/7 instruments (reference, 0 WIN). Replicates EXP-053 exactly (99/99 cells diff ≤ 1e-9).
- **THIRD-TIME-T12**: 99/17 powered, 6 viable, **3 WIN** (BTCUSD-30m, XAUUSD-1h, USDCAD-5m) — closest but below quorum.
- **THIRD-TIME-T24**: 99/17 powered, 4 viable, **2 WIN** (XAUUSD-15m, USDCAD-5m).
- **THIRD-TIME-T48**: 99/17 powered, 2 viable, **2 WIN** (BTCUSD-30m, USDCAD-5m).
- **THIRD-EVENT**: 99/17 powered, 1 viable, **0 WIN** — weakest performer.
- **Censoring narrative**: viable counts deplete 8→6→4→2→1 as floor rises 6→12→24→48→event. Longer horizons admit symmetric noise under 1:1 geometry — TIMECAP exit prices drift toward zero or negative. Not a power failure (99/99 powered across all variants).
- **Defect**: false — 0 non-deterministic, 0 causality violations, 0 reconciliation mismatches (99/99 BENCH cells match EXP-053 exactly), 0 invariant violations (cap monotonicity holds, `/THIRD-EVENT` bounds satisfied, warmup masks identical across time variants).
- **Determinism**: 17/17 cells PASS byte-identical replay on all 5 variants.
- **Reconciliation vs EXP-053**: 99/99 cells PASS — diff = 0.0 on `m` and `median` and `r_firsthit`.
- **Secondaries**: `/STRONG-HA` arm, STAT-MAD sensitivity, matched-random baselines, first-hit `r` all reported per scope. Pattern consistent across arms.
- **Audit PASS**: 0 Critical, 0 Warning, 2 Info (DE30 truncated-history disclosure; P15 fill approximation documented).

### Hypothesis-Specific Conclusion

**EVIDENCE_AGAINST** — No alternative third-barrier geometry clears P11. Raising the timecap floor systematically depletes viability (8→6→4→2→1 viable cells as floor rises 6→12→24→48). THIRD-EVENT is the weakest (1 viable, 0 WIN). The benchmark floor-6 adaptive cap is apparently optimal on this axis: longer horizons admit symmetric noise under the 1:1 adverse model, eroding expectancy from the "left on close" TIMECAP exit. Characterization readout feeding the single 014-B G2 alongside EXP-056 and EXP-057; no candidate registration.

### Hypothesis-Agnostic Observations

- **The censoring narrative is the headline diagnostic**: longer time horizons do not transform TIMECAP'd events into favourable outcomes often enough. The lever works through exit price, not the FAV/ADV ratio (first-hit `r` stays ≈0.50 across all variants).
- **Pattern mirrors EXP-056**: the benchmark geometry (50% / 1:1 / floor-6) is a local optimum on at least two orthogonal axes. Combined levers (EXP-060) are the remaining path.
- **THIRD-EVENT is structurally disadvantaged**: the ZigZag `rd`-confirm exit arrives too late; the 8× backstop dominates, making it a worse time cap, not a superior structural alternative.
- **Power is not the constraint**: all 99 cells remain powered (≥30 events) for every variant. The negative result is a measured property, not a sensitivity limitation.

---

## EXP-059B — Uncapped Structure Trailing (Conditioned HA Harami; `/EXIT-TRAIL-UNCAPPED`)

**Status**: UNCAPPED_TRAILING_CHARACTERISED — EVIDENCE_AGAINST
**Date**: 2026-06-16
**Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); secondary ZigZag (`atr_mult=0.5`) for trailing ratchet; `/STRONG-STAT` live magnitude-percentile filter; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised gross return endpoint

### Hypothesis Tests

1. **Hypothesis (HYP-012b)**: For the live `/STRONG-STAT`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move), an **uncapped structure trailing adverse-exit model** — no benchmark time-cap backstop and no initial 1:1 stop — either standalone (`TRAIL-PURE-UNCAPPED`) or combined with V2A partial favourable legs (`COMBINED-UNCAPPED-V2A`), produces **higher gross per-event median expectancy** (P14, ATR-normalised, position-weighted, P15 fills, real prices) than the **benchmark single fixed exit** (50% fav / 1:1 stop / adaptive cap, single leg) on the binding `/STRONG-STAT` arm.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); primary ATR-ZigZag (ATR 14/1.0); secondary trailing ZigZag (ATR 14/0.5); live magnitude-percentile filter via `xen.expectancy.live_in_progress_state` + `live_strong_stat`; benchmark barriers via `xen.expectancy`; new uncapped entry point in `xen.position_exits` (`resolve_legs_uncapped` + lazy trailing-stop helper).
- **Features**: per-cell per-arm median ATR-normalised gross return (P14 binding endpoint); regime-clustered MBB (10,000 draws; block length `b = round(m^(1/3))`, fixed seed); P15 path-ordered intrabar fill resolution; paired arm-BENCH contrast on common qualifying subset; cap-isolation divergent-subset contrast (uncapped − capped no-init sibling, events held past `bench_n`); P11 composition readout (≥5 cells ≥3 instruments, WIN = viable + beats benchmark, uncapped arms only).
- **Parameter ranges**: P1 ATR 14/1.0; P18 `ATR_MULT_TRAIL = 0.5` (frozen); P2 favourable 50% (benchmark, where present); P3 1:1 (BENCH only); P4 adaptive cap `max(6, round(1.5·median(trailing-20 confirmed-move durations)))` (BENCH + capped siblings only); P7 `/STRONG-STAT` window=20, min=5, q=0.75; P14 median binding; P15 path-ordered fill model; P11 composition; V2A fractions {1/3, 2/3, 1}; power floor 30; N_BOOT=10_000.
- **Precommitments**: no post-result variant selection; all 5 arms reported; family-wise correction deferred to single 014-B G2; 0 candidate slots, 0 TEST reads.
- **Exclusions**: no costs; no `/VPTARGET`/`/MAGTARGET` (EXP-056); no `/ADV-EXTREME`/`/ADV-NONE` (EXP-057); no `/THIRD-EVENT`/`/THIRD-TIME` (EXP-058); no combined system (EXP-060). No `/BARCFG` or `/CONFIRM` overlays. No TEST/holdout contact. No candidate consumption.

### Results / Observations

- **Verdict**: UNCAPPED_TRAILING_CHARACTERISED — **EVIDENCE_AGAINST**. No binding arm clears P11 (0 WIN cells). `n_pass = 0`, `passing_arms = []`.
- **BENCH**: 99/17 powered, 9 viable/7 instruments (reference, 0 WIN by design). Replicates EXP-053 exactly (99/99 cells diff ≤ 1e-9).
- **TRAIL-PURE-UNCAPPED**: 99/17 powered, **0 viable cells, 0 WIN cells**. Median uniformly negative. BTCUSD-5m: median −0.41 ATR, mean +0.10 — fat right tail does not offset adverse excursion damage.
- **COMBINED-UNCAPPED-V2A**: 99/17 powered, **1 viable cell** (BTCUSD-5m), **0 WIN cells**. BTCUSD-5m median +0.08 ATR (CI_low 0.01), but paired vs-BENCH contrast negative (CI_low < 0).
- **TRAIL-PURE-NOINIT-CAPPED (disclosed sibling)**: 99/17 powered, 0 viable, 0 WIN — cap alone does not rescue the no-init trailing scheme.
- **COMBINED-V2A-NOINIT-CAPPED (disclosed sibling)**: 99/17 powered, 2 viable (BTCUSD-5m, USDCAD-15m), 0 WIN.
- **Cap-isolation divergent contrast**: TRAIL-PURE: 48.3% median divergent share, **0/96 divergent-positive cells**. COMBINED: 35.8% median divergent share, **2/89 divergent-positive cells** (BTCUSD-30m, US2000-2h) — cap was not the constraint; the trailing mechanism is the bottleneck.
- **Censoring**: total DATA_CENSORED across all cells: 22 (TRAIL-PURE-UNCAPPED), 15 (COMBINED-UNCAPPED-V2A). The INCONCLUSIVE_POWER_LIMITED scenario did not materialize — the trailing stop fills before the TRAIN edge in virtually every cell.
- **Holding durations**: uncapped arms hold 7–8 bars (median p50) up to 66 bars (max) vs BENCH/capped siblings at 4–7 bars (p50=6). Longer holds with worse outcomes consistent with "let it run never helps on these events."
- **Defect**: false — 0 non-deterministic, 0 causality violations, 0 invariant violations (all 7 pass), EXP-053 reconciliation exact (99/99 cells diff = 0.0).
- **Determinism**: 17/17 cells PASS byte-identical replay.
- **Reconciliation vs EXP-053**: 99/99 cells PASS — diff = 0.0 on m, median, and first-hit r.
- **Secondaries**: `/STRONG-HA` arm, STAT-MAD sensitivity, matched-random and MA(20,50) baselines all reported per scope. Pattern consistent across arms.
- **Audit PASS**: 0 Critical, 1 Warning (BENCH itself weak — viable in only 9/99 cells; interpretation caveat for G2, not a code defect), 5 Info.

### Hypothesis-Specific Conclusion

**EVIDENCE_AGAINST** — The hypothesis is falsified. Neither binding arm clears P11 (0 WIN for both). Removing the benchmark time cap and initial stop does not improve conditioned capture on any lever. The pure trailing arm is uniformly negative because removing the initial 1:1 stop exposes every position to unbounded adverse excursions before the first secondary ZigZag pivot ratchets. The V2A combined arm recovers partially (1 viable cell) but still fails to beat the benchmark. The cap-isolation contrast confirms the cap was not the constraint — the trailing mechanism's secondary-pivot ratchet is the binding bottleneck. Characterization readout feeding the single 014-B G2 alongside EXP-056/057/058; no candidate registration.

### Hypothesis-Agnostic Observations

- **The no-initial-stop effect dominates the pure trailing result**: Without the benchmark 1:1 initial stop, early adverse excursions before the first secondary confirmation are unbounded. The median is uniformly negative; the fat right tail from rare runners makes the mean positive in some cells — a textbook case for the P14 median endpoint.
- **V2A partial legs shift the median directionally but cannot overcome the trailing stop on remaining weight**: The 1/3 and 2/3 fraction targets capture partial favourable excursion, but when the trailing stop binds on the open leg, it fills at a worse level than the fixed 1:1 exit for the position as a whole.
- **The cap binds frequently but removing it doesn't help**: ~35–48% of events are held past the benchmark cap. On those events, the uncapped version rarely beats its capped sibling (0/96 pure, 2/89 combined) — the trailing stop eventually fills at a worse price, not better. The constraint is the ratchet mechanism, not the horizon.
- **The capped no-init siblings confirm the finding**: Even with the cap backstop, the no-init trailing model rarely beats 1:1 (0/99 TRAIL-PURE-NOINIT-CAPPED WIN, 0/99 COMBINED-V2A-NOINIT-CAPPED WIN). Cap and init-stop are orthogonal to the fundamental problem: the secondary pivot ratchet is too slow or structurally misaligned with the signal's MFE timing.
- **The weak BENCH baseline contextualizes the result**: BENCH is viable in only 9/99 cells. The EVIDENCE_AGAINST verdict should be read in G2 alongside BENCH's own viability and the positive ADV-NONE result (EXP-057), which shows the conditioned signal can produce expectancy when the stop is removed entirely under the benchmark horizon.

## EXP-059 — Position-Management Exits (Conditioned HA Harami; `/EXIT-PARTIAL`, `/EXIT-TRAIL-STRUCT`, individually and combined)

**Status**: POSITION_MGMT_CHARACTERISED — EVIDENCE_FOR
**Date**: 2026-06-16
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20); 12 predeclared position-management exit arms; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised position-weighted gross return endpoint

### Hypothesis Tests

1. **Hypothesis (HYP-012)**: For the live `/STRONG`-conditioned HA harami (anchored at the harami confirmation-bar close, faded against the in-progress strong move, third barrier held at the benchmark adaptive time cap), at least one position-management exit scheme — favourable-side scaled exits (`/EXIT-PARTIAL` V1, V2A, V2B, V2C), adverse-side structure trailing (`/EXIT-TRAIL-STRUCT` PURE, TP-INIT, TP-NOINIT), or their combination (COMBINED-V1/V2A/V2B/V2C) — produces higher gross per-event median expectancy (P14, ATR-normalised, position-weighted realised return, P15 fills, real prices) than the benchmark single fixed exit (50% fav / 1:1 stop / adaptive cap, single leg), on the binding `/STRONG-STAT` arm.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED).
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ATR-ZigZag via `xen.zigzag` (ATR 14/1.0) + secondary trailing ZigZag (`atr_mult=0.5`); live magnitude-percentile filter via `xen.expectancy.live_in_progress_state` + `live_strong_stat`; new `python/src/xen/position_exits.py` module.
- **Features**: per-cell per-arm median ATR-normalised position-weighted gross return (P14 binding endpoint); regime-clustered MBB (10,000 draws; block length `b = round(m^(1/3))`, fixed seed); P15 path-ordered intrabar fill resolution; paired arm-benchmark contrast on the common qualifying subset; P11 composition readout (≥5 cells ≥3 instruments, WIN = viable + beats benchmark); exit-reason composition (binding mechanism diagnostic).
- **Parameter ranges**: P1 ATR 14/1.0; P2 favourable 50%; P3 1:1 (or trail init); P4 adaptive cap `max(6, round(1.5·median(trailing-20)))`; P7 `/STRONG-STAT` window=20, min=5, q=0.75; P14 median binding; P15 path-ordered fill model; P11 composition; 3 equal legs w=1/3; V2A fracs {1/3,2/3,1}; V2B fracs {0.5,1.0,1.5}; V2C {1/3,2/3,reversal-event}; reversal-event = first of {primary-ZigZag Direction==rd, opposing-conditioned-harami reversal-dir -rd}; trailing atr_mult_trail=0.5; monotone ratchet; power floor 30; N_BOOT=10_000.
- **Precommitments**: no post-result variant selection; all 12 binding arms reported; family-wise correction deferred to single 014-B G2; 0 candidate slots, 0 TEST reads.
- **Exclusions**: no costs; no `/VPTARGET`/`/MAGTARGET` (EXP-056); no `/ADV-EXTREME`/`/ADV-NONE` (EXP-057); no `/THIRD-EVENT`/`/THIRD-TIME` (EXP-058); no combined event system (EXP-060). No `/BARCFG` or `/CONFIRM` overlays. No TEST/holdout contact. No candidate consumption.

### Results / Observations

- **Verdict**: POSITION_MGMT_CHARACTERISED — **EVIDENCE_FOR**. 4 PARTIAL arms clear P11 WIN: PARTIAL-V1 (25 wins/14 instr), V2A (53 wins/17 instr), V2B (27 wins/14 instr), V2C (45 wins/17 instr). All TRAIL and COMBINED arms: 0 viable cells. `n_pass = 4`.
- **PARTIAL-V2A (strongest)**: 57 viable cells, 53 WIN over benchmark — broadest adoption across the grid (all 17 instruments). Even-thirds fractional targets provide the most consistent value by diversifying exit across price-space within the short cap window.
- **PARTIAL-V1**: 40 viable, 25 WIN. Event-trigger (first-profitable-close + 50% target + reversal-event) gives selective but still P11-clearing coverage.
- **PARTIAL-V2B**: 33 viable, 27 WIN. The 1.5× runner leg constrained by ~6-bar cap (ew_TIMECAP ≈ 48.5% for BTCUSD-5m).
- **PARTIAL-V2C**: 56 viable, 45 WIN. Hybrid (fixed targets + reversal runner) performs between V2A and V2B.
- **BENCH**: 99/17 powered, 9 viable/7 instruments, 0 WIN. Reproduces EXP-053 exactly (99/99 cells, diff=0.0).
- **TRAIL-PURE/TP-INIT/TP-NOINIT**: 99/99 powered each, **0 viable cells** each. The 0.5×ATR ZigZag retracement fires too frequently within the 6-bar cap.
- **COMBINED-V1/V2A/V2B/V2C**: 99/99 powered each, **0 viable cells** each. Trailing stop destroys partial-exit advantage.
- **Defect**: false — 0 non-deterministic, 0 causality violations, 0 reconciliation mismatches (99/99 BENCH cells match EXP-053 exactly), 0 invariant violations (leg weights sum to 1.0, degenerate 3-leg match, shared-stop closes all legs, trailing monotone).
- **Determinism**: 17/17 cells (first usable per instrument) PASS byte-identical replay across all 12 arms.
- **Exit-reason composition**: PARTIAL arms show dominant exit reasons are fractional-target touches and the time cap (reversal legs seldom fire within ~6 bars). TRAIL arms show trailing stop binds more often than favourable exits.
- **Secondaries**: `/STRONG-HA` arm, STAT-MAD sensitivity, matched-random baselines all reported per scope. Pattern consistent across arms.
- **Audit PASS**: 0 Critical, 0 Warning, 3 Info (F01 file-order convention; TRAIL/COMBINED 100% CI_SPANS_0 is genuine scoped measurement, not a defect; float precision in leg weights).

### Hypothesis-Specific Conclusion

**EVIDENCE_FOR** — At least one position-management exit scheme (`/EXIT-PARTIAL`) clears P11 on its own median expectancy and beats the benchmark on the paired contrast within the quorum. Specifically, 4 of 4 PARTIAL arms clear P11 with 25–53 wins over benchmark. The `/EXIT-TRAIL-STRUCT` branch (adverse-side structure trailing) is uniformly detrimental within the benchmark horizon — a measured-negative characterization that is a valid input to G2. Characterization readout feeding the single 014-B G2 alongside EXP-056, EXP-057, and EXP-058; no candidate registration.

### Hypothesis-Agnostic Observations

- **Partial exits capture mean reversion, not sustained trend**: In a ~6-bar cap window, the conditioned move may peak early and reverse. Partial exits bank at intermediate levels before reversal; the single benchmark exit waits for 50% and reverts before filling. This result may be partly driven by the cap window being too short for single-exit expression. EXP-060 (with longer horizons) will disambiguate.
- **The trailing ZigZag may be too tight at 0.5×ATR**: A secondary `atr_mult=0.5` ZigZag in a short window fires on noise-level pullbacks. A coarser threshold or different trailing construction might behave differently. This is a registered but untested sensitivity.
- **The 3-leg equal-weight structure is arbitrary**: Leg count and equal weighting are a fixed governance constant. Different weightings could produce different readouts.

---

## EXP-060 — Combined Event System (Conditioned HA Harami; Best Per-Layer Geometry, 2×2 Favourable×Adverse Factorial + Champion)

**Status**: COMBINED_SYSTEM_CHARACTERISED — CHARACTERISED_NOT_VIABLE_ELIGIBLE
**Date**: 2026-06-17
**Instruments**: BTCUSD, EURUSD, USTEC, XAUUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD, EURJPY, GBPJPY, AUDJPY, US500, US2000, DE30, JP225 (99 EXP-053 member cells; 3 COVERAGE_EXCLUDED: US500-4h, JP225-2h/4h)
**Data Views / Feature Categories**: 5m/15m/30m/1h/2h/4h real domain OHLC; HA candles for harami detection only; ATR-ZigZag substrate (Wilder ATR 14/1.0); `/STRONG-STAT` live magnitude-percentile filter (p75, trailing 20); 2×2 favourable×adverse factorial across 5 arms + champion; P15 path-ordered intrabar fills; P14 median per-event ATR-normalised position-weighted gross return endpoint

### Hypothesis Tests

1. **Hypothesis (HYP-013, the combined event system)**: For the live `/STRONG`-conditioned HA harami at strong-move exhaustion, entered at the harami confirmation-bar close, faded against the in-progress strong move, the **champion A3** (V2A 3-leg scaled partial take-profits `{1/3,2/3,1}×0.50·M_sofar` × `/ADV-NONE` unbounded adverse × benchmark adaptive cap floor=6) produces positive gross per-event median expectancy (P14) that clears P11 (≥5 cells ≥3 instruments with CI_low > 0, ≥30 events) and beats BOTH matched-random AND MA(20,50) P13 baselines in that quorum — the two-baseline IUT conjunction for G2 PROCEED.

### Scope

- **Instruments**: all 17 VAL-003-admitted instruments; DE30 with truncated-history disclosure.
- **Data Views / Feature Categories**: domain OHLC via `xen.bar_aggregator`; HA candles via `xen.heiken_ashi_generator` (detection only); ATR-ZigZag via `xen.zigzag` (ATR 14/1.0); live magnitude-percentile filter via `xen.expectancy.live_in_progress_state` + `live_strong_stat`; multi-leg resolver via `xen.position_exits`; ADV-NONE sentinel via `xen.adverse_targets.adverse_none_sentinel`.
- **Features**: per-cell per-arm median ATR-normalised position-weighted gross return (P14 binding); regime-clustered MBB (10,000 draws; `b = round(m^(1/3))`, fixed seed); P15 intrabar fills; paired arm-vs-baseline contrasts (`contrast_ci`) for binding champion; paired-median contrasts (`paired_median_contrast_ci`) for factorial decomposition; exit-reason composition (mechanism diagnostic).
- **Arm set (5 configs)**: A0 BENCH (50% single-leg / 1:1 / floor=6 — reference), A1 50%×NONE (50% single-leg / ADV-NONE / floor=6), A2 V2A×1:1 (V2A {1/3,2/3,1} / 1:1 / floor=6), **A3 V2A×NONE champion** (V2A / ADV-NONE / floor=6 — the single binding G2 candidate), A4 V2A×NONE@T48 (V2A / ADV-NONE / floor=48 — disclosed horizon sibling).
- **Parameter ranges**: P1 ATR 14/1.0; P2 favourable 50%-of-`M_sofar`; P3 1:1 (benchmark adverse, where present); P4 adaptive cap floor=6 (floor=48 for A4 only); P7 `/STRONG-STAT` window=20, q=0.75; P14 median binding (mean disclosed); P15 path-ordered fills; P11 composition; V2A fractions {1/3,2/3,1}, equal weights w=1/3; power floor 30; N_BOOT=10_000.
- **Precommitments**: no post-result variant selection; only A3 drives the binding G2 fork; 0 candidate slots, 0 TEST reads.
- **Exclusions**: no costs; no `/VPTARGET`/`/MAGTARGET` (EXP-056); no `/ADV-EXTREME` (EXP-057); no `/THIRD-EVENT` or other `/THIRD-TIME` floors (EXP-058); no `/EXIT-TRAIL-STRUCT`/`/EXIT-TRAIL-UNCAPPED` (EXP-059/059B). No TEST/holdout contact. No candidate consumption.

### Results / Observations

- **Verdict**: COMBINED_SYSTEM_CHARACTERISED — **CHARACTERISED_NOT_VIABLE_ELIGIBLE** (mechanical, for the single 014-B G2). Champion A3 produces **0 champion_wins** across all 99 cells.
- **Two-baseline IUT conjunction**: 69/99 cells VIABLE individually (median CI_low > 0, m ≥ 30). 3/99 beat matched-random (GBPUSD-4h, USDCHF-4h, US2000-4h). **0/99 beat MA(20,50)** — `contrast_ma_low` negative in every cell (range −0.569 to −2.404 ATR). MA(20,50) captures structurally longer multi-leg swings that no single-entry reversal can match.
- **Both geometric levers independently improve expectancy**: favourable main effect CI_low > 0 in 90+/99 cells; adverse main effect CI_low > 0 in 75+/99 cells. Interaction near zero — levers are additive, not synergistic. A3 − A0 (champion vs BENCH) positive in 99/99 cells (~0.20–0.35 ATR in high-power cells).
- **Exit-reason composition**: A3 ~58% FAV (split across V2A legs), 0% ADV, ~42% TIMECAP — mechanism operates as designed.
- **Horizon sensitivity (A4, floor=48)**: `A4 − A3` positive in ~85/99 cells but does not close the MA gap.
- **All invariants pass**: 0 determinism/causality/reconciliation failures. A0 reproduces EXP-053 exactly. ADV-NONE fires 0 adverse exits. Population byte-identical to EXP-053.
- **Audit PASS**: 0 Critical, 0 Warning, 0 Info.

### Hypothesis-Specific Conclusion

**CHARACTERISED_NOT_VIABLE_ELIGIBLE** — The champion A3 is powered (99/99) and **median-viable** (69/99), but the two-baseline IUT conjunction fails on every cell. The MA(20,50) bar is only one of two independent failures: (i) A3 beats the matched-random null in just **3/99** cells, so 66 of the 69 "viable" cells produce a positive median that is **statistically indistinguishable from a random entry** on the same ZigZag substrate (the median is mostly substrate drift/geometry, not signal); and (ii) "viable" is median-only — A3's **gross mean is ≈0/negative** (median-of-means −0.018 ATR; negative in 60/99 cells; ≈0 even among the 69 median-viable cells) under the capped-up (V2A) / uncapped-down (ADV-NONE) left skew. The conditioned signal's **median** expectancy is real; its **mean** (the bankable, tradeable quantity) is not, and this is gross of costs. So the result is a signal weakness on ZigZag, not merely an unreachable MA baseline. Mechanical readout feeding the single 014-B G2; no candidate registration.

### Hypothesis-Agnostic Observations

- **The two-baseline IUT may be too conservative, but the random null is the load-bearing failure here**: The MA(20,50) baseline is an independent segmentation producing longer trend definitions than any single-entry reversal can claim, and "can this entry beat holding the whole MA-defined trend?" is structurally negative for any single-point ZigZag entry. But the more basic signal-vs-null test (matched-random) already fails in 96/99 cells (only 3/99 pass) — so A3 does not establish a programme-scale edge over noise on its own substrate, independent of the MA bar.
- **The 2×2 factorial design paid off — on the median only**: Both main effects are independently positive and additive, and the median improvement over BENCH (A3 − A0 ≈ +0.20–0.35 ATR, positive in 99/99) is consistent. But "validated" applies to the **median endpoint alone**: the geometry lifts the median, not the bankable mean. A3's **gross mean is ≈0/negative** (median-of-means −0.018; negative in 60/99 cells; ≈0 even within the 69 median-viable cells), and it beats the matched-random null in just 3/99. The binding constraint is therefore **not only** the MA baseline bar — A3 is not viable on its own as configured (median-only, gross, mostly random-indistinguishable).
- **Horizon is not the binding constraint**: A4 (floor=48) improves expectancy modestly but does not close the MA gap (0/99 beat MA at 48 bars). The mechanism-horizon confound is resolved: the mechanism itself cannot match the MA baseline.
- **ADV-NONE unbounded adverse**: The median is robust but the mean diverges under left skew. Costs out of 014-B scope; flagged for any future tradability screen.

---

## EXP-060B — MA(20,50) Substrate Dominance: Genuine Lead or Skew Artifact? (Conditioned HA Harami, EXP-060 gap-fill)

**Status:** `SUBSTRATE_LEAD_FOUND` · Audit PASS (0C/2W/3I) · 2026-06-17 · HYP-013b (diagnostic addendum to EXP-060) · 0 slots / 0 TEST.

### Hypothesis Tests

- **Confound the addendum exists to resolve:** EXP-060 read MA(20,50)'s ~3–4× median advantage over the ZigZag champion as a "substrate property," but emitted MA's median only (not mean/exit-composition) and never tested MA against a matched-random control on the MA substrate. EXP-060B asks whether the MA median dominance is a genuine signal edge or the same capped-up (V2A) / uncapped-down (`/ADV-NONE`) left-skew + entry-redundant artifact as the ZigZag champion.
- **Binding discriminator (D2):** does the MA harami (M3) clear P11 median viability **and** beat its own-substrate matched-random (RM3, independent contrast CI_low>0) **and** clear P11 on the mean → SUBSTRATE_LEAD_FOUND; else ARTIFACT_CONFIRMED.

### Scope

- **Population**: identical conditioned `/STRONG-STAT` HA-harami, byte-identical to EXP-053/060 (reconciliation exact 99/99). 99-cell TRAIN grid, gross, real prices (MA(20,50) on real close; HA for detection only).
- **Objects (10)**: 8 signal arms — ZigZag {Z0–Z3}, MA {M0–M3} — + 2 matched-random nulls RZ3 (ZigZag, reproduces EXP-060) and RM3 (MA, the one new computation). Binding endpoint median (P14); mean disclosed (characterisation lens). Diagnostics D1 skew (median vs mean), D2 M3−RM3, D3 exit composition.
- **Exclusions**: no floor=48 horizon arm, no factorial, no new geometry/substrate beyond ZigZag + the registered MA(20,50) baseline, no costs, no TEST/holdout, no candidate consumption.

### Results / Observations

- **D2 (binding):** M3 median-viable 89/99; **M3 beats RM3 85/99** (P11 ✓); M3 mean-viable **14/99**; **M3 lead cells 14/99 over 9 instruments (P11 ✓) → SUBSTRATE_LEAD_FOUND**. RM3 median ≈ 0.380 (the geometry drift baseline — non-degenerate control); M3 median ≈ 1.158; M3−RM3 median contrast CI_low median 0.551 (only 4/89 ≤0). **Reverses ZigZag** (EXP-060: champion beat matched-random in only 3/99).
- **D1 (skew):** M3 gross mean median = **−0.065** (≈0/negative); ADV-NONE-driven — median−mean gap **1.20 ATR** for ADV-NONE arms vs 0.49 for 1:1 arms on MA (ZigZag: 0.16 vs 0.11).
- **D3 (mechanism):** Z3 TIMECAP 0.64 / FAV 0.36; M3 0.41 / 0.59; RM3 0.18 / 0.82 — M3 less TIMECAP-bound than Z3 but hits FAV *less* than RM3; M3's median edge is larger magnitude-per-resolution (strong-conditioning pushes targets further), not a higher hit-rate.
- **Integrity:** reconciliation exact 99/99 (Z3↔EXP-060-A3, M3↔EXP-060-maseg, exit weights); determinism ✓, causality ✓ (0 violations), invariants ✓ (ADV-NONE 0 ADV exits; matched-count holds; weights sum 1.0); holdout fence respected.
- **Audit caveats:** W1 lead narrow/4h-concentrated (8/14 lead cells are 4h, n=108–194; high-count leads have mean CI_low 0.037–0.088); W2 median overstates tradeable expectancy (mean ≈0); I2 analysis-plan mislabeled the M3−RM3 contrast as paired — code correctly used independent `contrast_ci`; I3 attribution is to the combined harami+strong signal.

### Hypothesis-Specific Conclusion

**SUBSTRATE_LEAD_FOUND** — audit-validated and mechanically met, but a **median-only, narrow** lead. The conditioned harami is *not* redundant on the MA substrate (it lifts the median from ~0.38 to ~1.16 and beats its matched-random control broadly) — qualifying EXP-060's "substrate property" reading: the MA advantage is partly a real signal effect, not solely geometry/drift. But it is **not tradeable as configured** — M3's gross mean is ≈0/negative across most of the grid (ADV-NONE uncapped-downside skew). The binding obstacle shifts from "does the signal work" (it does, on MA) to "does the no-stop geometry leave a positive mean" (it does not, except marginally). **G2 consequence:** do not close CF-HA-HARAMI-001 without a scoped MA-substrate follow-up targeting the **skew/mean**, not the signal's existence. Family stays REGISTERED/OPEN; no candidate registered here.

### Hypothesis-Agnostic Observations

- **The matched-random control is substrate-decisive.** The identical signal+geometry is entry-redundant on ZigZag (3/99) yet beats its matched-random broadly on MA (85/99). The trend-segmentation substrate, not the harami detector or the exit geometry, determines whether the signal expresses an edge — a first-class lesson for any future capture work in this family.
- **Median and mean disagree by construction under no-stop geometry.** A capped-upside + uncapped-downside scheme can make the median look strong while the mean sits at zero; viability read on the median alone overstates tradeable expectancy. Reporting the mean alongside the median is necessary, not optional, for any ADV-NONE arm.
- **COMBINED arms vs standalone PARTIAL**: The trailing adverse stop antagonises partial-leg favourable exits within the benchmark cap. The 1:1 fixed stop is the superior adverse-side treatment at this horizon.