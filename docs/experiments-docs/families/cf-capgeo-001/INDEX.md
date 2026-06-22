# CF-CAPGEO-001 — Family Index

> Detailed per-experiment cards for the data-derived exit / capture-geometry family (Phases 017–018).
> Live programme status and phase retrospectives: [master index](../../INDEX.md).
> Phase design/retrospective narratives: [`../../checkpoints/`](../../checkpoints/).
> Family spec: [`../../../signal-registry/candidate-families/cf-capgeo-001.md`](../../../signal-registry/candidate-families/cf-capgeo-001.md).
> Compact one-row registry of all experiments: [`python/experiments/INDEX.md`](../../../../python/experiments/INDEX.md).

**Status:** **REGISTERED — SCREENING-GATED. Phase 017 (qualifier & protocol validation) CLOSED at G-017 2026-06-21 — `DISCOVERY_ONLY`** (slate COMPLETE, G0 PASS; **EXP-076 RECOVERY_VALIDATED_G017a** + **EXP-077 VALIDATED_WITH_GUARDS** + **EXP-078 DISCOVERY_ONLY (shape-discrimination double-FAIL + k-fragile, 2026-06-21)**). **G-017 outcome (`G-017-gate-review.md`):** 6 of 8 `ASS_VALIDATED` legs hold but EXP-078's two binding legs FAIL — `ASS`'s shape leg only PARTIALLY closes the EXP-074 gap: it catches gross bimodality / strong left-skew but is **structurally blind** to the subtle median-positive minority-catastrophe shape (`B_zero`/`B_pos`, the CF-HA-HARAMI-001 failure shape), clean-unimodal false-flag needs `n≥60`, and the shrunk edge-call FPR is `k`-fragile. Per the predeclared D5 routing the conjunction cannot hold → **`ASS` is non-binding (discovery use only); the frozen referee suite (EXP-003/012/018 + EXP-027/070-analog) remains the binding gate for Phase 018.** Not `PROTOCOL_DEFECT` (determinism held byte-identically; accounting cap honored 8/8). External-validity bound: the binding legs are i.i.d.-synthetic — the moving-block CI coverage on dependent real data is the least-validated component (gate §6.1), so the FAIL is a *lower bound*. Phase 018 therefore opens with the frozen suite binding and `ASS` as a discovery overlay — **not** "once `ASS_VALIDATED`." The first family chosen for its **exit / capture geometry**, not its entry signal (two-family retrospective §6.1). Entries are **frozen** to four substrates — `SUB-AVWAP` (CF-AVWAP-001 final candidate), `SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` (CF-HA-HARAMI-001 final candidates), and `SUB-RANDOM` (matched control) — and exit / capture geometry is the sole open axis, asked in **reverse direction** (derive the exit from each system's realized return structure, then benchmark the known exits). Co-primary endpoint **expectancy + median + tail diagnostic** on real prices; binding qualifier is the new **`ASS`** (Adaptive Signal Scoring) **only if validated**; a binding **pre-TEST separability gate** (retrospective §4.1) is built in. **Two preconditions before any Phase 018 screening:** (1) **G-017 `ASS_VALIDATED`** — Phase 017 validates `ASS` + the expanding-window walk-forward protocol framework-style (else `ASS` is demoted to discovery-only and the frozen referee suite stays binding); (2) **INFR-003** — the 5-year 1-minute data upgrade is collected, VAL-validated, and the holdout **re-sealed** before Phase 018 (which runs on the new data; Phase 017 runs on synthetic substrates + current first-70% TRAIN only). 0 candidate slots, 0 TEST reads in Phase 017; holdout untouched. Governing design: [`../../checkpoints/2026-06-20-017-capgeo-qualifier-validation/design.md`](../../checkpoints/2026-06-20-017-capgeo-qualifier-validation/design.md).

> **Provenance.** Promoted from `.ignore/dump/re.md` (final consolidated draft, 2026-06-20) with `infrastruture+exit.md`, `ass.md`, `wf-model.md`, `discussion-1.md`, `mmm.md`, and the standing reference [`../../reflections/2026-06-19-two-family-retrospective-reflections.md`](../../reflections/2026-06-19-two-family-retrospective-reflections.md). Operator decisions (2026-06-20): four substrates (two frozen prior candidates + Random control); two-phase split (017 validate → 018 family); 5-year data as a separate INFR-003 precondition; family name CF-CAPGEO-001.

## Why this family (inherited diagnosis)

Both prior families produced a real edge and both died downstream on the same abstract failure — *the lever that removes the binding obstacle also removes the edge*. CF-AVWAP-001 closed on **capture geometry** (move 5–9× the cost floor, no exit realizes it net); CF-HA-HARAMI-001 closed on **entry bimodality** (real median edge, mean unliftable at entry). The highest-leverage remaining unknown is the **peak → realizable-net-capture conversion** — so this family fixes the entry side to known objects and makes exit/capture geometry the only open axis, judged on overall **expectancy** (anti-overfitting), with the bimodality/tail shape emitted from the start.

## Experiments

### Phase 017 — Qualifier & Protocol Validation (qualifier = methodology, not candidate screening)

- **EXP-076** — `ASS` Synthetic-Substrate Recovery (`ASS/VAL-001`; expectancy/median/tail recovery + shrinkage behaviour across unimodal/skewed/bimodal/sparse types) — **RECOVERY_VALIDATED_G017a (2026-06-20)** — `ASS` recovers ground truth; expectancy-CI sparse-floor caveat at n<30; two dispositions to G-017. [Detailed card ↓](#exp-076-card)
- **EXP-077** — Dogfood + Calibration under `WF-EXPANDING` (`ASS/VAL-002`; FPR/MDE/`P(return>X)` reliability + counted-read accounting vs the 2-read cap; current-data TRAIN-only dogfood) — **VALIDATED_WITH_GUARDS (per-stratum, 2026-06-20)** — error-control + protocol legs validated under `WF-EXPANDING`; MDE/accounting/dogfood/determinism PASS; FPR & reliability each carry one bounded per-stratum guard (B_zero effective-n≤60 defer-to-median; D2.4 slope inapplicable at compressed P(>2R)). No PROTOCOL_DEFECT. [Detailed card ↓](#exp-077-card)
- **EXP-078** — Shape Discrimination + `k`-Sensitivity (`ASS/VAL-003`; bimodal-vs-unimodal flag, closing the EXP-074 tail-shape-blind-guard gap; one-knob sensitivity) — **DISCOVERY_ONLY (binding double-FAIL, per-stratum, 2026-06-21)** — shape diagnostic structurally blind to the subtle median-positive minority-catastrophe shape (`B_zero`/`B_pos`); U false-flag fails at the n=30 floor only; K2 shrunk edge-call FPR k-fragile (K1 invariant). `ASS` shape leg only PARTIALLY closes the EXP-074 gap → feeds terminal G-017 `DISCOVERY_ONLY`. [Detailed card ↓](#exp-078-card)
- *(EXP-079 reserved-inactive for a dedicated `WF-EXPANDING` isolation read if needed.)*
- **G-017** — terminal gate, **ADJUDICATED 2026-06-21 — `DISCOVERY_ONLY`** ([`G-017-gate-review.md`](../../checkpoints/2026-06-20-017-capgeo-qualifier-validation/G-017-gate-review.md); predeclared D5 routing). 6/8 `ASS_VALIDATED` legs hold; EXP-078's two binding legs FAIL ⇒ the conjunction cannot hold ⇒ **`ASS` non-binding (discovery use only); the frozen referee suite stays the binding gate for Phase 018.** No `PROTOCOL_DEFECT` (determinism held byte-identically; accounting cap honored 8/8). Phase 017 CLOSED; see [`retrospective.md`](../../checkpoints/2026-06-20-017-capgeo-qualifier-validation/retrospective.md).

### Phase 018 — CF-CAPGEO-001 Family Screening (OPEN; G0 PASS 2026-06-21; G-017 resolved `DISCOVERY_ONLY` → frozen referee suite binding, `ASS` discovery overlay)

- **EXP-080 — HYP-001** readiness (4 substrates × {15m,1h,4h} × **16** instruments, 5-year data) — **READINESS_DELIVERED (2026-06-22)** — 184/192 substrate-cells READY; US500-4h + JP225-4h `COVERAGE_EXCLUDED` (genuine 4h index sparsity, with record); member set for EXP-081 = 46 instrument×domain cells; D7 192/192 IN_BRACKET; null-FPR machinery controlled (operating regime n≥120); harami entry-identity holds ∀ cells. [Detailed card ↓](#exp-080-card)
- **EXP-081 — HYP-002** characterize realized return structure (4 substrates × 46 member cells, 5-year data, TRAIN-only gross) — **CHARACTERISATION_DELIVERED (2026-06-22)** — 184/184 cells delivered; D3 inputs locked & EXP-082-ready; **gross capture availability ≈ random** (move availability not the differentiator — AVWAP-situation/EXP-047 echo); the only structure is the **outcome shape** (harami median +0.135 / mean ≈ 0.000, 33/46 median>mean — CF-HA-HARAMI-001 signature reproduced on 5-year data); m_anti resolves 1/184 (heavy tail, not a separated mode). 0 slots, 0 counted TEST reads. [Detailed card ↓](#exp-081-card)
- **HYP-003** derive exits via the frozen D3 mechanical rule — *next (EXP-082)*
- **HYP-003** derive exits via predeclared mechanical rules (freeze the rule) — *GATED*
- **HYP-004** test derived exits + benchmark known exits; separability gate; candidate screening — *GATED*

---

## Detailed cards

<a id="exp-081-card"></a>
### EXP-081 — Per-Substrate Realized Return-Structure Characterization (HYP-002) — CHARACTERISATION_DELIVERED

**Status:** COMPLETED. **Date:** 2026-06-22. **Phase 018, second experiment** (HYP-002 characterize; 0 candidate slots, 0 counted TEST reads — TRAIN-only disclosure). Artifacts: [`EXP-081/`](../../../../python/experiments/EXP-081/) (report · results.md · audit.md · governance/pre-execution-review.md). New code: `xen.capgeo_geometry` (adaptive-cap path geometry MFE/MAE/TTP/outcome on real OHLC, MFE/MAE floored ≥0 per EXP-055; shape diagnostics — Hartigan-dip+KDE `m_anti`, `tailmass`/`q05`). Reuses `xen.capgeo_substrates`, `xen.domain_bars`, `xen.expectancy` (adaptive cap), `xen.ass` (KDE/dip/score/bootstrap), `xen.zigzag` unchanged.

**Instruments / Data Views:** 16 (VAL-003 universe minus DE30), VAL-005-admitted 5-year dataset, first-70%-of-analysis **TRAIN sub-split** only (`[0, int(analysis_rows*0.7))`); analysis-TEST + holdout never sliced. Holdout-fenced 15m/1h/4h domain bars; HA candles for harami entry detection only. All MFE/MAE/TTP/outcome/ATR on **real prices**.

#### Hypothesis Tests

1. **Per-substrate-cell D3 inputs (descriptive quantiles):** `MFE_med`/`MFE_q40` (favourable capture), `TTP_med`/`TTP_q75` (capture time), `MAE_q90` (adverse) over each event's adaptive cap.
2. **Bimodality / catastrophe boundary (Hartigan dip — one of two stat tests):** `m_anti` = MAE antimode where dip_p<0.05 (KDE antimode between top-2 modes), else NaN.
3. **Minority-mass / left-tail read (descriptive):** `tailmass` = fraction of realized outcomes below `median − 3·MAD`; `q05`.
4. **`ASS` discovery disclosure (the second stat test — NON-BINDING, G-017 DISCOVERY_ONLY):** per-cell expectancy + median + tail, moving-block bootstrap CIs; D6 Guard (i) wired (fired 0×, all cells n≫60).

No edge/pass verdict — the verdict is completeness (CHARACTERISATION_DELIVERED). Per stratum; per-substrate medians are disclosures only (LESSON-001).

#### Scope

- **Member set:** 4 substrates × **46** EXP-080-READY instrument×domain cells = **184 substrate-cells** (US500-4h, JP225-4h `COVERAGE_EXCLUDED`). Frozen entries reused from EXP-080 (`SUB-AVWAP`, `SUB-HARAMI-PARTIAL-V2A` ≡ `SUB-HARAMI-V2A-ADVNONE`, `SUB-RANDOM`).
- **Lookforward:** per-event **adaptive time cap** (validated `adaptive_time_caps_by_epoch`, cell MA-segment tempo) applied uniformly to all 4 substrates; warmup disclosed+excluded.
- **Frozen constants:** ATR(14); `K_tail=3.0`; ≥30-event floor; `TIMECAP_*` (EXP-068); quantile linear; seeds recorded.
- **Exclusions:** no exit/barrier/target/stop/P&L (EXP-082/083); no separability gate or screening; no cross-substrate pooling as a binding statistic; TRAIN-only; holdout never read.

#### Results / Observations

- **CHARACTERISATION_DELIVERED: 184/184 cells.** 0 underpowered (`n_usable` 46–5535, median 1083), 0 nondeterministic (two-pass fingerprint exact), harami PARTIAL-V2A ≡ V2A-ADVNONE on all D3 cols, EXP-080 entry reconciliation 184/184 (TRAIN ≤ full), holdout untouched.
- **D3 inputs EXP-082-ready:** `T_fav`=`MFE_med`/`MFE_q40` (~3.2–3.4 ATR); `S_adv`=`m_anti` else `MAE_q90` (~9–9.7 ATR); `H_cap`=`TTP_q75`/`TTP_med` (~37–52 bars, median ~44). No cell below the 30-event floor → a derived candidate can be formed for every member cell.
- **Gross capture availability ≈ random** (per-cell paired vs within-cell `SUB-RANDOM`, 46 cells): harami median `MFE_med` *below* random (17/46 above), AVWAP coin-flip (28/46); outcome-median edge ~chance (23–25/46). **Move availability is not the differentiator** (AVWAP-situation/EXP-047 echo, now on 5-year data).
- **The only structure is the OUTCOME SHAPE:** harami **median-of-cell-medians +0.135 but median-of-cell-means ≈ 0.000**; **33/46 cells median>mean** (catastrophic left-tail drag); `tailmass` harami 0.0526 > random 0.0437 (31/46 cells); `q05` ≈ −9 ATR. **CF-HA-HARAMI-001 median-positive/mean-killed signature reproduced on disjoint 5-year data.** AVWAP roughly symmetric (mean +0.157 ≈ median +0.150); random baseline median +0.085.
- **`m_anti` resolves 1/184** (US500-1h AVWAP, dip_p 0.032, m_anti 1.79); dip_p median 0.976 (MAE predominantly unimodal). Catastrophe is a heavy **continuous** tail, not a separated mode → `MAE_q90` fallback dominates 183/184, exactly as D9 designed. Dip genuinely exercised (184 finite, 136 unique p-values).

#### Hypothesis-Specific Conclusion

- **CHARACTERISATION_DELIVERED.** The frozen entries' realized return structures are fully characterized and the D3 inputs are locked for EXP-082. The exit-relevant structure is concentrated in the **outcome tail/shape**, not gross favourable availability (≈ random). **No edge claim.** Consequence (next-scope): EXP-082's derived-exit value must come from the **adverse/tail leg** (`S_adv` truncating the catastrophe); **EXP-083's separability gate is the crux** — does cutting the tail also remove the median edge?

#### Hypothesis-Agnostic Observations

- Two inherited lessons co-locate on fresh 5-year data in one experiment: capture availability is not the lever (CF-AVWAP-001/EXP-047), and the conditioned harami's mean is killed by a catastrophic minority while its median is positive (CF-HA-HARAMI-001). The harami substrate carries the failure shape **at the entry level**, before any exit — so it is a property of the entry population, not an exit artifact.
- The catastrophe is a **heavy continuous left tail**, not a separated second mode (dip-invisible) — a separated-mode detector (`m_anti`, and by extension `ASS`'s dip leg) is structurally the wrong instrument; minority-**mass** (`tailmass`) is the read that sees it. Carry this into EXP-083's separability S2 design.

#### Audit / governance

- **Audit PASS (0C/1W/3I).** Verdict forensics independently re-derived D3 inputs from raw bars to full precision, confirmed the per-cell paired real-vs-random mechanism (not pooled masking), proved the dip is genuinely exercised, and confirmed the gate-shape coherence (`tailmass` on outcome vs `m_anti` on MAE — different distributions by design). W1 (entries ≈ random / median-positive-mean-killed shape) is **mechanistic, moves no D3 number** — raised for Stage 6 / EXP-082-083, no rerun. I1 `m_anti` 1/184 (by design), I2 AVWAP direction re-derived on domain bars (frozen module unedited), I3 SUB-RANDOM = random-timing/same-regime-direction null. See [`audit.md`](../../../../python/experiments/EXP-081/audit.md).
- **Pre-execution governance** APPROVE (no revision cycle).

<a id="exp-080-card"></a>
### EXP-080 — Phase 018 Substrate/Exit Readiness (HYP-001) — READINESS_DELIVERED

**Status:** COMPLETED. **Date:** 2026-06-22. **Phase 018, first experiment** (HYP-001 readiness; 0 candidate slots, 0 counted TEST reads — readiness/coverage exposure = disclosure). Artifacts: [`EXP-080/`](../../../../python/experiments/EXP-080/) (report · results.md · audit.md (+ Re-Audit) · governance/pre-execution-review.md). New code: `xen.domain_bars.build_domain_bars` (promoted verbatim from VAL-005, regression-checked frame-identical) + `xen.capgeo_substrates` (uniform `entries()` over AVWAP final + EXP-068 conditioned-harami port + fixed-seed matched-random).

**Instruments / Data Views:** 16 (VAL-003 universe minus DE30), VAL-005-admitted 5-year dataset (2021-06-02 → 2026-06-21), first-70% analysis slice; holdout-fenced 15m/1h/4h domain bars; HA candles for harami detection. No edge/return/capture/P&L computed.

#### Hypothesis Tests

1. **Readiness (per substrate-cell, deterministic):** construction integrity (OHLC, sortedness, holdout-fence, coverage-based dropped fraction vs frozen <0.10/0.10–0.25/>0.25 bands) ∧ entry-detector invariant battery (causality, on-close, structural) ∧ exact two-pass determinism.
2. **D7 bracket (descriptive):** realized entry count vs the Phase-017-validated `[15,8000]` `ASS`-discovery span.
3. **Null-FPR machinery sanity (the one statistical test):** moving-block bootstrap one-sided `CI_low>0` FPR on a non-tradable, mean-centered, block-permuted carrier; CONTROLLED (wilson_hi ≤ 0.075) binding only in the operating regime n≥120 (D0 §D9), small-n disclosed.
4. **Harami entry-population identity (disclosure).**

All reported per stratum (no pooled verdict); the `SUBSTRATE_REFUTED` halt is a disjunction of predeclared systematic triggers (non-determinism any cell; same invariant ≥3 instruments; operating-regime null-FPR uncontrolled).

#### Scope

- **Substrates (4, frozen, never tuned):** `SUB-AVWAP` (CF-AVWAP-001 final), `SUB-HARAMI-PARTIAL-V2A` & `SUB-HARAMI-V2A-ADVNONE` (CF-HA-HARAMI-001 finals, EXP-068 entry ported), `SUB-RANDOM` (matched control). 192 substrate-cells = 4 × 16 × {15m,1h,4h}.
- **Frozen constants:** D7 bracket [15,8000]; drop bands 0.10/0.25; seeds recorded; null-FPR gate wilson_hi≤0.075 at floor n≥120; null-FPR machinery scale N_NULL=5000/N_BOOT=10000 (validated m_cell scale).
- **Exclusions:** no exit/return/capture/MFE/MAE/expectancy/tail metric; no exit derivation/application; no separability gate or screening; no pooling; first-70% only; holdout never read.

#### Results / Observations

- **Readiness: 184/192 READY.** 8 NOT_READY = **US500-4h** (dropped 0.251) + **JP225-4h** (0.281), ×4 substrates, `COVERAGE_EXCLUDED` on the >0.25 band; both pass all invariants + determinism → genuine 4h cash-equity-index coverage sparsity (EXP-043 precedent), excluded from EXP-081 with record. US500-4h borderline. **Member set for EXP-081 = 46 instrument×domain cells.**
- **Coverage-based dropped fraction** (validated `(candidate−retained)/candidate`): @15m BTCUSD 0.013, USTEC 0.002, forex/gold ~0.02, US500 0.091, JP225 0.161 — tracks coverage, not session structure. Only 2/48 cells > 0.25.
- **Determinism / causality:** 0 nondeterministic cells; 0 invariant-battery failures across 192 cells; SUB-RANDOM byte-identical from its seed; domain-bar regression vs VAL-005 frame-identical (85,839 rows).
- **D7 bracket: 192/192 IN_BRACKET** — AVWAP 78–2,641 (sparser); harami(both)/random 284–7,657. `ASS` discovery in its validated regime for every cell (frozen suite binding regardless).
- **Null-FPR:** operating regime n≥120 all CONTROLLED (wilson_hi n120 0.0642, n250 0.0680, n500 0.0657, n2000 0.0555) at the validated scale; small-n n<120 inflation disclosed (0.081–0.091), non-binding (D0 §D6 Guard (i)/§D9).
- **Harami entry identity:** identical entries in all cells (shared MA-native conditioned HA-harami detector by construction; differ only by later exit) → entry-level counted-read accounting coincides.

#### Hypothesis-Specific Conclusion

- **READINESS_DELIVERED.** The four frozen entries reproduce deterministically, look-ahead-safe, and invariant-clean on the new 5-year data with adequate coverage; the moving-block inference machinery is controlled at the operating scale. Two 4h index cells excluded on coverage with record. Phase 018 proceeds to EXP-081 characterization on the 46-cell member set. **No edge claim.**

#### Hypothesis-Agnostic Observations

- The coverage-based dropped fraction cleanly stratifies by each instrument's traded fraction (24/7 crypto < forex < cash-equity index), so the >0.25 band binds only at the coarse 4h domain for session instruments — relevant to any future coarse-domain index work.
- The null-FPR operating-floor decision is **scale-sensitive**: the n=120 boundary resolved to controlled only at the validated N_BOOT=10000 scale (a bounded probe gave a spurious halt). Carry the validated scale into EXP-083.

#### Audit / governance

- **Re-audit PASS** (0C/0W). The **initial run returned `SUBSTRATE_REFUTED`** on two verdict-material defects: (Critical-1) the dropped-fraction metric was mis-denominatored against a continuous 24/7 clock (excluding all session instruments, leaving only BTCUSD READY) → fixed to the validated coverage-based definition; (Critical-2) the null-FPR probe ran below the validated machinery scale, making the n=120 gate noise-dominated (spurious halt) → Stage-5 governance ruled re-scale to the validated m_cell scale (gate/floor unchanged). Both fixed, re-run, re-audited PASS. See [`audit.md`](../../../../python/experiments/EXP-080/audit.md).
- **Pre-execution governance** APPROVE after one REVISE cycle (reconciled the predeclared null-FPR halt criterion to the ratified D0 §D9 operating floor).

<a id="exp-078-card"></a>
### EXP-078 — Shape Discrimination + `k`-Sensitivity (`ASS`/VAL-003) — DISCOVERY_ONLY (binding double-FAIL, per-stratum)

**Status:** COMPLETED. **Date:** 2026-06-21. **Phase 017 G-017 shape-discrimination + `k`-sensitivity legs — the last experiment owed before terminal G-017.** Synthetic only — 0 candidate slots, 0 counted TEST reads, holdout untouched. Artifacts: [`EXP-078/`](../../../../python/experiments/EXP-078/) (report · results.md · audit.md · verdict.json). New code: `xen.ass.shape_diagnostic` + `ShapeDiag` (in-family extension; existing `score`/`bootstrap_cis` unchanged); new dependency `diptest` 0.11.0.

**Instruments / Data Views:** none — synthetic return populations (ATR units), frozen D1 DGPs reused from EXP-076 (unimodal `U0–U3`; skew `Splus/Sminus/Sminus0`; bimodal `B_neg/B_zero/B_pos/B_strong`) × `n ∈ {15,30,60,120,250,500,1000,2000,8000}`, `R_REP=2000`.

#### Hypothesis Tests

1. **Shape discrimination (binding, D2.5):** at `τ_gap=0.30`, combined `flag = (dip_p<0.05) OR (|g|>τ_gap)` gives false-flag ≤ 0.05 (Wilson-hi ≤ 0.075) on every `U` stratum **and** detection ≥ 0.80 on every `B` stratum, for each `n≥30`. Per-leg (dip vs gap) decomposed.
2. **`k`-sensitivity (binding, D3):** across `k ∈ {30,60,120,240,500}` (= {0.5×,1×,2×}·deployed median-n=120 ∪ {30,500}), the `ASS` binding routing (K1 shrinkage behaviour; K2 shrunk-expectancy null edge-call FPR) is invariant or bounded-and-disclosed.
3. **`S`-family asymmetry characterization (disclosed, non-binding).**

All reported PER STRATUM (LESSON-001; D0 §8) — no collapsed boolean is binding (`collapsed_convenience_flag=false`).

#### Scope

- **Instruments:** none (synthetic). **Features:** `dip_p` (Hartigan dip-test), `g=(mean−median)/MAD`; shrinkage `n/(n+k)`; shrunk-expectancy bootstrap edge-call.
- **Parameters frozen at D0:** `τ_gap=0.30`, `dip_alpha=0.05`, `MASTER_SEED=20260620`, `N_BOOT=10_000`; deployed `k=median(SP population n)=120` (= EXP-076 `k_shrink`).
- **Exclusions:** no `τ_gap` re-tuning, no `k` selection, no FPR/MDE/reliability re-measurement (EXP-077), no market data, no candidate screening, no TEST/holdout contact.

#### Results / Observations

- **Shape — U false-flag (`shape_rates.csv`): FAIL at the n=30 binding floor only.** All four `U` types 0.135–0.152 @ n=30 (Wilson-hi up to 0.168); pass cleanly n≥60 (≤0.046) and n≥120 (≤0.007). Small-sample noise floor of the OR-rule at `τ_gap=0.30`; the D0 bite-check's 0.000 was at a single larger `n`.
- **Shape — B detection (`shape_rates.csv`): FAIL, driven by a 2-way shape split.** Strongly-separated bimodals detect (`B_strong` |g|=0.60, dip_p≈0: 0.875→1.0 PASS; `B_neg` |g|=0.50: 0.7595@n30 miss→1.0). **Subtle median-positive bimodals are undetectable and decay to 0 with n:** `B_zero` (|g|=0.25, dip_p≈0.99) 0.4145→0.0; `B_pos` (|g|=0.067, dip_p≈0.99) 0.1885→0.0@n500+.
- **`k`-sensitivity (`k_sensitivity*.csv`): K1 INVARIANT, K2 ROUTING_FLIP.** K1 shrinkage behaviour `SHRINK_OK` at all 5 `k`. K2 null edge-call FPR flips `CONTROLLED→INFLATED` at the **2× multiplier k=240** (FPR 0.39–0.87) and k=500 (1.0) — shrinkage pulls the null estimate toward the positive SP prior (`pool_mean=+0.518`) against a margin frozen at k=120.
- **Integrity (`integrity.json`):** anchor diff 0.0 to **both** EXP-076 and EXP-077; determinism shape/K1/K2 all hash-match; `mad_zero_total=0`; `diptest 0.11.0`. Not a `PROTOCOL_DEFECT`.

#### Hypothesis-Specific Conclusion

**REFUTED on both binding legs → DISCOVERY_ONLY.** The frozen `ASS` shape diagnostic catches gross bimodality and strong left-skew but is **structurally blind** to the subtle median-positive minority-catastrophe shape (`B_zero`/`B_pos`) — the exact CF-HA-HARAMI-001 / EXP-074 tail-shape-blind-guard shape it was commissioned to catch. Clean-unimodal false-flag needs `n≥60`; the shrunk edge-call FPR is `k`-fragile. `ASS` only **PARTIALLY** closes the EXP-074 gap. Per the pre-registered interpretation, the shape-discrimination FAIL means the `ASS_VALIDATED` conjunction cannot hold → terminal **G-017 `DISCOVERY_ONLY`** (`ASS` non-binding for Phase 018; frozen referee suite stays binding). No `PROTOCOL_DEFECT`.

#### Hypothesis-Agnostic Observations

- A two-leg shape gate (Hartigan dip ∪ robust mean–median gap) has a **blind region**: a population with a small/broad minority catastrophic mode (10%/5% at σ=0.6) is neither dip-bimodal (no antimode) nor robust-gap-flagged (true `|g|`<0.30) — yet it is precisely the dangerous mean-weak shape. Detectability requires the minority mode to either carve an antimode (dip) or push the robust gap past `τ_gap` (gap); the subtle CF-HA-HARAMI-001 shape does neither.
- A self-calibrated margin (Q95 of the same null at the deployed `k`) pins the deployed-`k` FPR to ≈target by construction; only the **across-`k`** movement is an informative robustness read. (Audit Warning 1.)

**Audit / governance:** Audit **PASS-trust** (0 Critical / 2 Warning / 4 Info) — the double-FAIL is **implementation-faithful** (audit independently reproduced mixture means to 1e-4, U0 false-flag rates exactly, the sub-0.30 true gaps, and the K2 shrink-toward-prior mechanism); no verdict-material defect → no fix-and-rerun. W1: K2 deployed-`k` per-cell labels are self-calibration MC noise (read across-`k` fragility, not per-cell labels) — non-material. W2: the pre-registered `k`-sweep swept 2 of 3 dispositions (CI-coverage leg omitted) — cannot move the FLIP verdict, partial disclosure. Post-experiment governance: see `governance/post-experiment-review.md`.

<a id="exp-077-card"></a>
### EXP-077 — Dogfood + Calibration under `WF-EXPANDING` (`ASS`/VAL-002) — VALIDATED_WITH_GUARDS (per-stratum)

**Status:** COMPLETED. **Date:** 2026-06-20. **Phase 017 G-017 error-control + protocol legs.** Synthetic
binding legs + current-data **TRAIN-only** (first-49%) dogfood — 0 candidate slots, 0 counted TEST reads,
holdout untouched. Artifacts: [`EXP-077/`](../../../../python/experiments/EXP-077/) (report · results.md ·
audit.md · verdict.json). New reusable module: `python/src/xen/wf.py`; `xen.ass` moving-block extension.

**Instruments / Data Views:** none for the binding synthetic legs; dogfood = 4-core (EURUSD, XAUUSD,
BTCUSD, USTEC) × {15m, 1h, 4h}, real `Close`/ATR forward returns on the first-49% TRAIN slice.

#### Hypothesis Tests

1. **FPR (D2.2, binding):** margin-calibrated `expectancy CI_low > m` FPR ≤ 0.05 (Wilson-hi ≤ 0.075) on
   every null stratum (`U0`, `B_zero`) and the small-`n` stratum; `m = Q95(ci_low_1s | null)` on TAG_CAL,
   FPR on independent TAG_VAL.
2. **MDE (D2.3, binding):** `MDE(N)` finite/non-degenerate for every `N ≥ 30`.
3. **`P(>X)` reliability (D2.4, binding):** decile max|pred−real| ≤ 0.10 AND slope ∈ [0.85,1.15] per
   `X ∈ {0, 0.05, 1.0, 2.0}`.
4. **Counted-read accounting (D4.1, binding):** one frozen WF run = +1 counted read; cap honored.
5. **Dogfood (D4.2):** real-bar TRAIN-only pipeline completes, 0 counted reads, first-49% cutoff asserted.
6. **Determinism (D6):** byte-identical second pass.

All reported PER STRATUM (LESSON-001; D0 §8) — no collapsed PASS/FAIL is binding.

#### Scope

- **Instruments:** synthetic legs none; dogfood 4-core × {15m,1h,4h} (smoke subset).
- **Features:** synthetic `N(μ,1)`/skew/bimodal return populations (frozen D1, reused from EXP-076);
  dogfood ATR(14)-normalised forward-H=6 real-`Close` returns.
- **Parameters:** `N ∈ {15,30,60,120,250,500,1000,2000,8000}`, `R_REP=2000`, `N_BOOT=10_000`, master
  seed 20260620; `WF-EXPANDING` 0.50 initial + 5×0.10 folds, min fold 30; margin Q95.
- **Exclusions:** no shape/`k` sweep (EXP-078); no candidate screening; no real TEST/holdout contact; no
  MDE-magnitude gate (finiteness only); no `ASS`-parameter tuning.
- **Constraints:** synthetic iid → flat-iid WF bootstrap; real dogfood → fold-clustered moving-block;
  TAG_CAL/TAG_VAL disjoint; first-49% lazy fence asserted in code.

#### Results / Observations

- **FPR** (`fpr.csv`): binding fails = 5 cells. **U0 wf** n=120/1000/2000 = 0.0515/0.051/0.052
  (z=+0.31/+0.21/+0.41; binomial P(≥edges|p=0.05)=0.39/0.43/0.36); all other U0 binding cells pass.
  **B_zero wf** n=30/60 = 0.059 (z=+1.85), decaying 0.050(n=120)→0.001(n=8000). Every binding-fail cell
  Wilson-hi ≤ 0.0702. Non-binding single_window B_zero n=30 = 0.071 (Wilson 0.083).
- **MDE** (`mde.csv`): finite ∀ N≥30; 0.644/0.459/0.324/0.230/0.171/0.133/0.085/0.050 (n=30…8000); 0
  degenerate cells.
- **Reliability** (`reliability_verdict.csv`): X=0/0.05/1.0 PASS (slope 0.923/0.926/0.950, max-gap
  ≤0.029); X=2.0 FAIL on slope 0.652 only (max-gap 0.0168, corr 0.934, 6 of 10 deciles populated,
  predicted ptp 0.056).
- **Accounting** (`accounting.csv`): 8/8 scenarios pass; cap-honoring trace blocks the 3rd read.
- **Dogfood** (`dogfood.csv`): 12/12 cells complete, finite, every `train_cutoff = int(int(total·0.7)·0.7)`
  (frac 0.4900), 0 counted reads.
- **Integrity** (`integrity.json`): determinism 5/5 True, persisted-CSV hashes match, anchor diff 0.0.

> Audit independently re-derived every headline; `verdict.json` is a faithful pure function of the tables
> (0 mismatches once single_window-non-binding-by-design semantics are applied).

#### Hypothesis-Specific Conclusion

**PARTIALLY SUPPORTED (per stratum) — VALIDATED_WITH_GUARDS.** `ASS` error control, detection power,
`P(>X)` reliability, counted-read accounting, dogfood, determinism, and anchor hold under `WF-EXPANDING`
subject to two bounded per-stratum guards: (i) defer expectancy edge-calls to the median for
bimodal/asymmetric mean-null strata at effective-`n` ≤ 60 (the EXP-076 small-`n` under-coverage); (ii)
treat the D2.4 slope sub-gate as inapplicable when predicted-probability range is compressed (bind on
max-gap), as at X=2.0. No `PROTOCOL_DEFECT`. Feeds G-017; G-017 adjudicated after EXP-078.

#### Hypothesis-Agnostic Observations

- A margin calibrated to a 0.05 construction target makes the bare **point-≤-0.05 FPR sub-gate** a
  ~coin-flip: a correctly-calibrated estimator exceeds 0.05 on ~half of independent draws by chance. The
  **Wilson-hi sub-gate** is the uncertainty-aware binding test (satisfied on all binding cells here).
- **Decile-based slope calibration is structurally ill-conditioned at compressed probabilities**
  (predicted P(>2R) tied near zero collapses the quantile bins); the max-gap remains the trustworthy
  calibration statistic there. Relevant to any future `P(>X)` reliability read at extreme `X`.

**Audit / governance:** Audit PASS (0 Critical / 1 Warning / 3 Info). Warning: reliability predicted uses
un-pooled `shrink=False` vs the plan's "shrinkage-weighted" wording — shown non-material (cannot flip the
leg verdict; shrinkage is structurally inapplicable per single-type fold). No verdict-material findings →
no fix-and-rerun. Post-experiment governance: see `governance/post-experiment-review.md`.

<a id="exp-076-card"></a>
### EXP-076 — `ASS` Synthetic-Substrate Recovery (`ASS`/VAL-001) — RECOVERY_VALIDATED_G017a

**Date:** 2026-06-20. **Phase 017 G-017a cheap screen.** Synthetic only — 0 candidate slots, 0 counted
TEST reads, holdout untouched. Artifacts: [`EXP-076/`](../../../../python/experiments/EXP-076/)
(report · results.md · audit.md · verdict.json). New reusable module: `python/src/xen/ass.py`.

**Hypothesis Tests**
- **H-recovery (binding):** un-pooled `ASS` recovers expectancy *and* median to `median|est−truth| ≤
  0.85·SE_true(n)` on every `(type, n)` cell.
- **H-coverage:** the 90% bootstrap CI covers truth in `[0.86, 0.94]` for both estimands per type.
- **H-shrinkage:** weight `n/(n+k)` monotone in n; sparse (n≤30) pull ≥0.25; rich (n≥2000) pull <0.05.

**Scope**
- 11 synthetic types (U0–U3 unimodal; Splus/Sminus/Sminus0 skew-normal; B_neg/B_zero/B_pos/B_strong
  bimodal) × `n ∈ {15,30,60,120,250,500,1000,2000,8000}`; `R_REP=2000`; `N_BOOT=10_000`;
  `k = median-n = 120`. Returns in ATR units. No market data; frozen D0 §D1/§D2.1/§D3/§D6.

**Results / Observations**
- **Recovery — PASS all 198 cells** (99 expectancy + 99 median). Worst `median|err|/SE`: 0.722
  (expectancy, Sminus0/n=500), 0.702 (median, U2/n=250) — both < 0.85 and above the unbiased floor
  0.6745·SE.
- **Coverage — in-band ∀ n≥30** (0/176 out of band, `verdict_n_ge_30=PASS`). Sub-band only at **n=15
  expectancy**: U0 0.8595, B_neg 0.833, B_zero 0.857, B_pos 0.8565 (whole n=15 expectancy row depressed,
  mean 0.864); **median in-band at every n** (n=15 min 0.876). Converges to ~0.90 by n≥120.
- **Shrinkage — monotone; sparse pull 0.889 (n=15)/0.80 (n=30) ≥0.25**; implemented pull matches
  `k/(n+k)` to ~1e-16; sole literal rich-pull breach the **predeclared** n=2000 marginal (0.0566); n=8000
  pull 0.0148.
- **Integrity:** anchor `direct==numpy.mean` (diff 0.0); KDE-vs-direct gap 1.2e-8 (<0.02·σ); determinism
  byte-identical (3/3 hashes); CSV hashes match `integrity.json`.

**Hypothesis-Specific Conclusion**
- **RECOVERY_VALIDATED (G-017a): `ASS` recovers ground truth.** Estimator core unbiased for expectancy
  and median across the full shape span (incl. negative-median skews); CIs calibrated where used (n≥30);
  shrinkage behaves as designed. The two open items are governance dispositions on disclosed,
  mechanism-explained boundary behaviour, not recovery failures. EXP-077 (FPR/MDE/reliability) and
  EXP-078 (shape + `k`) remain owed before **G-017 `ASS_VALIDATED`**.

**Hypothesis-Agnostic Observations**
- The n=15 expectancy under-coverage is the **intrinsic small-sample percentile-bootstrap floor of the
  mean** (shape-ordered: near-nominal on clean normals, worst on bimodal `B_neg`; median robust). This
  is a property of the percentile bootstrap, independent of `ASS` — relevant to any small-n expectancy
  edge-call downstream.

**Audit / governance**
- **Audit CONDITIONAL PASS (1C-resolved / 2W / 3I).** **C1** (collapsed `overall_pass_literal` violated
  the per-stratum doctrine `cf-capgeo-001.md:137,204`; D0 §D1/§D4) RAISED → fixed representation-only →
  `verdict.json` regenerated per-stratum via `--rebuild-verdict` (no recompute; tables byte-identical) →
  re-audited RESOLVED.
- **Dispositions to G-017:** (a) ratify coverage binding at **n≥30**, n=15 expectancy as disclosed
  sparse-stress diagnostic (dated D0-amendment); (b) downstream guard — no expectancy edge-calls at
  effective **n<30** (weakened-evidence) + **EXP-077 adds a small-n FPR stratum**; n=2000 rich-pull read
  monotone-decreasing or set `k`/anchor explicitly.
- **Anti-reversion:** per-stratum verdict guard added to `research-pipeline/governance-constraints.md`
  (Stage 4/8) + `checkpoints/2026-06-20-017-…/LESSON-001-per-stratum-verdict.md`.
