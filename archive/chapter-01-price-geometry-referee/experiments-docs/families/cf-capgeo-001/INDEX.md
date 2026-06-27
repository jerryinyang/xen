# CF-CAPGEO-001 — Family Index

> Detailed per-experiment cards for the data-derived exit / capture-geometry family (Phases 017–018).
> Live programme status and phase retrospectives: [master index](../../INDEX.md).
> Phase design/retrospective narratives: [`../../checkpoints/`](../../checkpoints/).
> Family spec: [`../../../signal-registry/candidate-families/cf-capgeo-001.md`](../../../signal-registry/candidate-families/cf-capgeo-001.md).
> Compact one-row registry of all experiments: [`python/experiments/INDEX.md`](../../../../python/experiments/INDEX.md).

**Status:** **`RETIRED` 2026-06-22 — SCREENED, CLOSED at G-018. Phase 018 ran the full registered slate
HYP-001→004 (EXP-080–085, all governance-APPROVE); HYP-004 returned `NOT_CONFIRM` (EXP-084, portfolio unit).
No net-tradable out-of-sample capture geometry found: the exit lever is empty *and* exit-invariant, so the
exit/capture-geometry axis is exonerated as the binding constraint — the bottleneck is upstream
signal-conditional favourable availability (EXP-081: gross availability ≈ random). 0 candidate slots / 0
counted TEST reads across the phase; holdout never touched; all 48 strata stay 0/2 open (the 3 AVWAP-4h basket
strata disclosed). Next work is a new entry-side family at its own G0/D0 — not a reopening of this exhausted
surface. See the [Phase 018 retrospective](../../checkpoints/2026-06-20-018-capgeo-exit-geometry/retrospective.md)
and the [EXP-084 card ↓](#exp-084-card). _Prior status retained below for record._**

**REGISTERED — SCREENING-GATED. Phase 017 (qualifier & protocol validation) CLOSED at G-017 2026-06-21 — `DISCOVERY_ONLY`** (slate COMPLETE, G0 PASS; **EXP-076 RECOVERY_VALIDATED_G017a** + **EXP-077 VALIDATED_WITH_GUARDS** + **EXP-078 DISCOVERY_ONLY (shape-discrimination double-FAIL + k-fragile, 2026-06-21)**). **G-017 outcome (`G-017-gate-review.md`):** 6 of 8 `ASS_VALIDATED` legs hold but EXP-078's two binding legs FAIL — `ASS`'s shape leg only PARTIALLY closes the EXP-074 gap: it catches gross bimodality / strong left-skew but is **structurally blind** to the subtle median-positive minority-catastrophe shape (`B_zero`/`B_pos`, the CF-HA-HARAMI-001 failure shape), clean-unimodal false-flag needs `n≥60`, and the shrunk edge-call FPR is `k`-fragile. Per the predeclared D5 routing the conjunction cannot hold → **`ASS` is non-binding (discovery use only); the frozen referee suite (EXP-003/012/018 + EXP-027/070-analog) remains the binding gate for Phase 018.** Not `PROTOCOL_DEFECT` (determinism held byte-identically; accounting cap honored 8/8). External-validity bound: the binding legs are i.i.d.-synthetic — the moving-block CI coverage on dependent real data is the least-validated component (gate §6.1), so the FAIL is a *lower bound*. Phase 018 therefore opens with the frozen suite binding and `ASS` as a discovery overlay — **not** "once `ASS_VALIDATED`." The first family chosen for its **exit / capture geometry**, not its entry signal (two-family retrospective §6.1). Entries are **frozen** to four substrates — `SUB-AVWAP` (CF-AVWAP-001 final candidate), `SUB-HARAMI-PARTIAL-V2A` and `SUB-HARAMI-V2A-ADVNONE` (CF-HA-HARAMI-001 final candidates), and `SUB-RANDOM` (matched control) — and exit / capture geometry is the sole open axis, asked in **reverse direction** (derive the exit from each system's realized return structure, then benchmark the known exits). Co-primary endpoint **expectancy + median + tail diagnostic** on real prices; binding qualifier is the new **`ASS`** (Adaptive Signal Scoring) **only if validated**; a binding **pre-TEST separability gate** (retrospective §4.1) is built in. **Two preconditions before any Phase 018 screening:** (1) **G-017 `ASS_VALIDATED`** — Phase 017 validates `ASS` + the expanding-window walk-forward protocol framework-style (else `ASS` is demoted to discovery-only and the frozen referee suite stays binding); (2) **INFR-003** — the 5-year 1-minute data upgrade is collected, VAL-validated, and the holdout **re-sealed** before Phase 018 (which runs on the new data; Phase 017 runs on synthetic substrates + current first-70% TRAIN only). 0 candidate slots, 0 TEST reads in Phase 017; holdout untouched. Governing design: [`../../checkpoints/2026-06-20-017-capgeo-qualifier-validation/design.md`](../../checkpoints/2026-06-20-017-capgeo-qualifier-validation/design.md).

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
- **EXP-082 — HYP-003** derive exits via the frozen D3 mechanical rule (3 derived candidates × 184 member cells, 5-year data, TRAIN-only, no market data read) — **DERIVATION_DELIVERED (2026-06-22)** — 552/552 valid triple-barrier exits; determinism/harami-identity/provenance all pass; `derive_barriers` sha256-pinned (binding artifact EXP-083 imports). Mechanism caveats: 3 candidates → 2 distinct exit definitions on this snapshot (D1≡D2 184/184, `m_anti` resolves 1/184 and <`MAE_q90`); catastrophe-engaging `m_anti` dormant 549/552 → adverse leg reverts to generic `MAE_q90` stop ~9 ATR sitting **at** the catastrophe edge `|q05|` in a wide-stop/modest-target geometry (`T_fav/S_adv`≈0.35) = CF-HA-HARAMI-001 trap geometry reproduced in the derived exit → **EXP-083 separability gate (S2) is the crux**. 0 slots, 0 counted TEST reads. [Detailed card ↓](#exp-082-card)
- **EXP-083 — HYP-004a** TRAIN-only candidate screen of the 3 derived + full benchmark exit grid behind the separability gate (D0-amendment-001; EXP-084 counted read deferred) — **SCREEN_DELIVERED (2026-06-22; re-audit PASS)** — TRAIN-only eligibility, NOT an edge claim; valid set hash-pinned (sha256 `fa4035f3…`) + Holm rule for EXP-084. n_valid=26 = **4 S2-PASS (all SUB-HARAMI-V2A × AUDUSD × 1h, n=988 — conventional AVWAP-FH + RR-1.5/2/3) + 22 S2-DEFERRED (SUB-AVWAP 4h NZDUSD/USDCAD/USTEC, n<120)**; 4 underlying cells, narrow breadth; 98.2% died at G-018a. **Central finding: the data-derived D1/D2/D3 earned NO distinctive TRAIN support** (none in the binding S2-passed set; survive only in deferred AVWAP-4h cells alongside conventional arms) → family thesis unsupported on TRAIN. Mechanism genuine favourable-capture attribution (x_fav>0 mean 1.33 ATR, x_tail≤0; 0 tail-truncation artifacts), NOT the EXP-082 trap. Audit fix-and-rerun: C1 (Critical — entry-identical harami pair drew different nulls → control-noise flipped a survivor → moved n_valid/sha256) + W1 (m_cell reuse) → operator-directed dedupe harami to 1 stratum (4→3 substrates) + per-candidate m_cell → re-run + re-audit PASS. 0 slots, 0 counted TEST reads. [Detailed card ↓](#exp-083-card)
- **EXP-085 — HYP-004 cost read-gate** TRAIN-only gross→net cost/slippage+financing screen on **all 26** EXP-083 hash-pinned survivors (4 S2-PASS + 22 S2-DEFERRED), 0 reads / 0 slots, run BEFORE any EXP-084 read as the G-018 read-gate ([D0-amendment-002](../../checkpoints/2026-06-20-018-capgeo-exit-geometry/D0-amendment-002-train-cost-readgate.md)) — **NET_SURVIVES (per-stratum-masked, 2026-06-22)** — 21/26 NET_POS but the pooled headline **masks heterogeneity**: all 21 NET_POS are S2-DEFERRED low-n 4h `SUB-AVWAP` cells (n=44–78, separability never adjudicated); the **only S2-PASS well-powered stratum (AUDUSD-1h `SUB-HARAMI-V2A`, n=988) is NET_INCONCLUSIVE in all 4 cells** (passes expectancy exp_lo +0.057…+0.081, fails median med_lo −0.020…−0.047). Cost did **not** kill the gross edge (contrast EXP-030/045) — 4h gross magnitudes (1–2 ATR mean) dwarf cost (~0.15–0.35 ATR) — but the edge lives entirely in shape-unadjudicated low-n cells. **Authorizes nothing — read-gate input to G-018.** Audit PASS (0C/2W/3I). 0 reads / 0 slots. [Detailed card ↓](#exp-085-card)
- **EXP-084 — HYP-004b** the single sanctioned OOS confirmation read, reframed to a **PORTFOLIO unit** (D0-amendment-003, both legs satisfied: EXP-085 NET_SURVIVES + operator ratification): one frozen `WF-EXPANDING` read of a hash-pinned basket = `SUB-AVWAP` 4h events pooled across NZDUSD+USDCAD+USTEC, exited by the pinned parameter-free `AVWAP-FH`, NET of the EXP-085 cost model, under the D4 G-018 conjunction — **NOT_CONFIRM (2026-06-22)** — the basket **separates on TRAIN** (S1 1.109>m; **S2 finally adjudicable at pooled n=152 and PASSES**, tailmass 0.0263 — validating the AVWAP-FH "genuine continuous tail" pin) **but all three economic OOS legs FAIL** (exp_lo −1.045<m −0.0396; med_lo −0.821<0; beats_lo −0.656<0). **Mechanism: the apparent edge is selection-region overlap and reverses OOS** (per-fold positive in non-fresh [50–70%] folds +1.866/+0.068, negative in all three fresh [70–100%] folds −1.002/−1.250/−0.754; Risk-1 realized). Not masking a positive stratum (all 3 net-neg); exit-invariant (no arm clears zero at CI_low). Well-powered → NOT_CONFIRM not INCONCLUSIVE. **HYP-004 CLOSES at G-018**; data-derived-beats-conventional thesis unsupported on TRAIN and now unconfirmed OOS as a portfolio; holdout untouched, NOT released. 0 slots, **0 counted TEST reads** (portfolio-aggregate disclosure; all 48 strata stay 0/2). Audit PASS (0C/0W/3I). [Detailed card ↓](#exp-084-card)

---

## Detailed cards

<a id="exp-084-card"></a>
### EXP-084 — AVWAP-4h Portfolio Confirmation Read of the Net-Surviving Capture Geometry (HYP-004b) — NOT_CONFIRM

**Status:** COMPLETED. **Date:** 2026-06-22. **Phase 018, the single sanctioned OOS confirmation read for HYP-004** ([D0-amendment-003](../../checkpoints/2026-06-20-018-capgeo-exit-geometry/D0-amendment-003-exp084-portfolio-read.md), operator-ratified — reframed from per-stratum to a **portfolio** unit; pinned exit `AVWAP-FH`; portfolio-disclosure accounting). 0 candidate slots, **0 counted TEST reads** (portfolio-aggregate disclosure). Artifacts: [`EXP-084/`](../../../../python/experiments/EXP-084/) (report · results.md · audit.md · governance/pre-execution-review.md). No new module — reuses `xen.wf` (frozen WF-EXPANDING), `xen.capgeo_screen` (S1/S2 + bootstrap), `xen.capgeo_cost` (EXP-085 cost overlay + exit mirrors), and the frozen EXP-083/VAL-005 orchestration unchanged.

**Design:** one hash-pinned basket = `SUB-AVWAP` 4h events pooled across NZDUSD+USDCAD+USTEC (ordered by event close-time, deterministic tie-break), exited by the a-priori-pinned parameter-free `AVWAP-FH`, NET of the EXP-085 per-instrument round-trip + bar-count financing cost (applied per-instrument before pooling). Binding **D4 G-018 conjunction**: WF expectancy `ci_low>m` (FPR-calibrated margin) ∧ WF median `ci_low>0` ∧ beats-matched-random `ci_low>0` ∧ TRAIN separability **S1 ∧ S2**. Binding suite = `xen.wf.aggregate_walk_forward(kind="block")` + FPR margin (EXP-070/077 instantiation), **not** the framework-era bps gate stack (unit-incompatible). Per-stratum (3) + per-arm (11) reads are **disclosure** (`binding=false`). The portfolio framing existed to make **S2 adjudicable** (its n≥120 floor blocked every per-cell read in EXP-083/085).

**Result — NOT_CONFIRM** (n_pool=303, n_train_sep=152, n_oos=151; 5 folds all ≥ MIN_FOLD=30, 0 subfloor):

- **Separability PASSES on TRAIN:** S1 attribution `s1_excess_lo=1.109 > m`; **S2 finally adjudicated at pooled n=152 and PASSES** — `tailmass 0.0263 ≤ 0.06` ∧ `q05 −5.049 ≥ q05_control−δ −8.430`. This validates the `AVWAP-FH` pin rationale (a genuine continuous-tail non-residual pass, not stop-truncation-to-point-mass).
- **All three economic OOS legs FAIL:** expectancy `exp_lo −1.045 < m −0.0396`; median `med_lo −0.821 < 0`; beats-random `beats_lo −0.656 < 0`. Pooled net expectancy −0.221 ATR; net median point estimate +0.058 but CI_low −0.821.

**Mechanism (headline):** the apparent edge is **selection-region overlap and reverses out-of-sample.** The frozen §D5 schedule tests on [50%,100%] of the analysis set, but EXP-083/085 selected the candidate on [0,70%]. Per-fold net expectancy is **positive in the two non-fresh [50–70%] selection-overlap folds** (fold0 +1.866, fold1 +0.068) and **negative in all three genuinely fresh [70–100%] held-back folds** (fold2 −1.002, fold3 −1.250, fold4 −0.754). The positive signal that motivated HYP-004 is an artifact of evaluating on the mined region — Risk-1 (flagged in scope/plan) realized in full.

**Verdict forensics (audit PASS):** **not masking a positive stratum** — NZDUSD/USDCAD/USTEC all net-negative on expectancy (−0.579/−0.484/−0.159), all exp_lo deeply negative (−2.100/−2.468/−2.949); USTEC median +0.925 (n=77) is a single-instrument quirk (mean still negative), disclosure-only. **Exit-invariant** — none of the 11 exit arms has a positive CI_low (best point estimates VP-POC +0.747, D1/D2 +0.505 still have exp_lo<0). **Gate-shape correct** — S2 genuinely saw the catastrophe tail and passed; both location measures non-positive at CI_low → "no OOS edge," not "wrong gate for the shape." **Power adequate** (n_oos=151 ≥ 2·MIN_FOLD, 0 subfloor) → `NOT_CONFIRM`, not `INCONCLUSIVE_SPANS_ZERO`.

**Audit (PASS, 0C/0W/3I):** the binding G-018 conjunction was re-derived leg-by-leg from `portfolio_confirm.parquet` and reproduces exactly; holdout exclusion (load_first70 first-70% only; OOS folds ⊂ analysis set), reconciliation (TRAIN gross to EXP-083 anchor n=46/gross 1.806 within 1e-9; exit-mirror reconcile), and determinism (two-pass fingerprint) confirmed; counted_test_reads=0/candidate_slots=0 and the EXP-083 sha `fa4035f3…` + EXP-085 cost + hash-pin-before-OOS asserted. **3 Info (none verdict-material):** (I1) the FPR margin came out mildly negative (m=−0.0396) — conservative-safe for a NOT_CONFIRM (loosens only the expectancy leg, which still fails by a wide margin); (I2) USTEC mean/median sign split (disclosure); (I3) the Stage-4 unadjudicable-S2 HALT did not fire (n=152 ≥ 120). See [`audit.md`](../../../../python/experiments/EXP-084/audit.md).

**Disposition (G-018):** **HYP-004 CLOSES at G-018.** The AVWAP-4h reversal capture geometry is **not net-tradable out-of-sample as a portfolio**; combined with EXP-083 (no distinctive TRAIN support for the derived exits) and EXP-085 (net edge only in shape-unadjudicated low-n cells), the family's "data-derived beats conventional" thesis is unsupported on TRAIN and now additionally **unconfirmed OOS**. The cross-exit invariance points away from exit design entirely. Global holdout never touched and **not** released. Registry disposition recorded (multiplicity-registry EXP-084 → COMPLETE/NOT_CONFIRM; candidate-family HYP-004 closed at G-018; test-read-ledger EXP-084 disclosure against the 3 strata — 0 counted, all 48 strata stay 0/2 open).

<a id="exp-085-card"></a>
### EXP-085 — TRAIN-Only Gross→Net Cost Read-Gate on the EXP-083 Valid-Candidate Set (HYP-004 cost read-gate) — NET_SURVIVES (per-stratum-masked)

**Status:** COMPLETED. **Date:** 2026-06-22. **Phase 018 read-gate** (D0-amendment-002, operator-directed; re-sequences the registered conditional cost layer to run TRAIN-only BEFORE any EXP-084 counted read). 0 candidate slots, 0 counted TEST reads (TRAIN-only disclosure). Artifacts: [`EXP-085/`](../../../../python/experiments/EXP-085/) (report · results.md · audit.md · governance/pre-execution-review.md). New code: `xen.capgeo_cost` (exit-bar mirrors of the 3 frozen resolver families + per-event ATR-unit cost/financing overlay). Reuses the frozen EXP-083 orchestration unchanged (the `ass_overlay.py` import pattern); no frozen module edited.

**Verdict:** `NET_SURVIVES` (predeclared rule: ≥1 of the 26 survivors with net expectancy `CI_low_1s>0` ∧ net median `CI_low_1s>0`, per stratum) — **21/26 NET_POS, 5 NET_INCONCLUSIVE_SPANS_ZERO, 0 NET_NEG.** Rule-correct, but **read per stratum** (the pooled count masks the binding picture). **Authorizes nothing** — a read-gate input to the operator's G-018 decision; an EXP-084 counted read opens only on (a) `NET_SURVIVES` (met) + (b) operator ratification at EXP-084's own D0.

**Scope / data:** the 4 survivor strata only — AUDUSD-1h (`SUB-HARAMI-V2A`, n=988) + NZDUSD/USDCAD/USTEC-4h (`SUB-AVWAP`, n=44–78). 5-year VAL-005 bars → holdout-fenced `build_domain_bars`; real OHLC, ATR(14) units; **TRAIN sub-split `[0, int(analysis_rows·0.7))` only.** Candidate set read verbatim from `valid_candidate_set.json` (internal content hash `fa4035f3…` asserted first).

**Cost model (operator-ratified Stage 4, frozen before the TRAIN read):** one round-trip `RT_i` (CONSERVATIVE = 2×BASE, EXP-030) + adverse-side financing `F_i × holding_days` (EXP-034), in ATR units: `cost_ATR = (RT/1e4 + F/1e4 × holding_days) × P_entry/ATR_entry`; `net = gross − cost`. RT/F bps: AUDUSD 4.0/0.8, NZDUSD 4.5/0.8, USDCAD 4.0/0.7, USTEC 5.0/1.2. Holding-days = **bar-count proxy** `(exit−entry)×domain_minutes/1440` (operator-ratified over the wall-clock alternative).

**Headline (read per-stratum, not flat):** **all 21 `NET_POS` are S2-DEFERRED low-n 4h `SUB-AVWAP` cells** (NZDUSD ×9, USDCAD ×11, USTEC ×1; n=44–78, separability never adjudicated, n<120). **The only S2-PASS, well-powered stratum — AUDUSD-1h (n=988) — is `NET_INCONCLUSIVE` in all 4 cells:** net expectancy positive (point +0.59…+0.65 ATR, exp_lo +0.057…+0.081 > 0) but the net **median** lower bound just below zero (med_lo −0.020…−0.047) → fails the conjunction (the CF-HA-HARAMI median-positive-but-not-quite signature in the one cell with power to resolve it). **Every net survivor is shape-unadjudicated low-n; the shape-guarded well-powered stratum is net-inconclusive.**

**Mechanism:** cost did **not** kill the gross edge (contrast EXP-030/045) because the 4h gross magnitudes (0.74–2.07 ATR mean, 1.2–4.4 ATR median) dwarf the ~0.15–0.35 ATR cost (~15–30% of gross) — a fixed price-bps round-trip ÷ a large 4h ATR is a small ATR-unit cost (`txn_share` ≈0.40–0.60 on 4h vs **0.72** on the smaller-ATR 1h cell). Partly a genuine economic effect, partly an ATR-normalization property; the favourable magnitudes sit entirely in n=44–78 cells the EXP-083 ASS overlay already flagged as small-n-inflated. Net matched-random excess positive in all 26 cells (non-binding companion).

**Gate-shape:** the binding **expectancy ∧ median** gate is appropriately **tail-aware** — the mean leg incorporates the catastrophe losers, so `net_exp_lo>0` means the mean survives the tail+cost (the 4h `net_med ≫ net_exp` shows the tail persists). Unlike the EXP-074 tail-blind consistency gate, the gate **sees** the shape; the limitation is **power / separability adjudication** (S2 deferred at n<120), not gate shape.

**Audit (PASS, 0C/2W/3I):** numerics independently reproduced for two survivors to full float precision (gross, holding, cost, net_exp, net_med); the three reconciliation guards (valid-set sha re-derivation == `fa4035f3…`; per-survivor gross to 1e-9 — which also proves the cell_index/seed grid matches EXP-083; exit-mirror ret 1e-9 + cls/mask exact) confirmed real; the three exit mirrors confirmed **line-faithful** to `capgeo_screen.resolve_*` by diff. **W1** the per-stratum masking (forensic disclosure — the code faithfully implemented the predeclared rule; moves no verdict-bearing number) and **W2** small-n expectancy CI under-coverage at n<60 (non-material — those cells also clear the robust median leg; both-legs rule is conservative) are both shown unable to move any verdict. Determinism byte-identical; `holdout_untouched`; 0 counted TEST reads; 0 slots.

**Disposition (G-018, operator decision):** EXP-085 sharpens the read decision — the net survivors (shape-unadjudicated low-n 4h) and the shape-guarded well-powered stratum (AUDUSD-1h, net-inconclusive) are **disjoint**; neither is a clean confirm target. Routes: **(1)** decline EXP-084, close HYP-004 at G-018, 0 lifetime reads; **(2)** ratify a narrow EXP-084 with the binding stratum + Holm family fixed in its own D0. Registry disposition recorded (multiplicity-registry EXP-085 → COMPLETE/NET_SURVIVES, EXP-084 still leg-(b)-gated; test-read-ledger unchanged, all 48 strata 0/2; candidate-family HYP-004 line updated).

<a id="exp-083-card"></a>
### EXP-083 — TRAIN-Only Candidate Screen of Derived + Benchmark Exits Behind the Separability Gate (HYP-004a) — SCREEN_DELIVERED

**Status:** COMPLETED. **Date:** 2026-06-22. **Phase 018, fourth experiment** (HYP-004a TRAIN screen per D0-amendment-001; the counted-read confirmation is the deferred reserved-conditional EXP-084). 0 candidate slots, 0 counted TEST reads (TRAIN-only disclosure). Artifacts: [`EXP-083/`](../../../../python/experiments/EXP-083/) (report · results.md · audit.md [binding verdict = the **Re-Audit** section] · governance/pre-execution-review.md). New code: `xen.capgeo_screen` (pure screen/separability harness — causal exit resolvers, moving-block bootstrap, S1/S2 legs). Imports the sha256-pinned `xen.capgeo_exits.derive_barriers` unchanged; reuses `xen.capgeo_substrates`, `xen.capgeo_geometry`, `xen.domain_bars`, `xen.favourable_targets`, `xen.expectancy`, `xen.zigzag`.

**Verdict:** `SCREEN_DELIVERED` — ≥1 `{candidate × stratum}` survives both TRAIN gates. **TRAIN-only eligibility, NOT an edge / tradability / referee-suite-pass claim** (gross screen; cost-calibrated referee suite + counted read are EXP-084). Hand-off (frozen): `valid_candidate_set.json` **sha256 `fa4035f3…`** + Holm-over-grid rule, imported verbatim and hash-asserted by EXP-084.

**Scope / data:** 5-year post-INFR-003 VAL-005-admitted 1-minute bars → holdout-fenced `build_domain_bars`; real OHLC, ATR units; **TRAIN sub-split `[0, int(analysis_rows·0.7))` only** (analysis-TEST + final-30% holdout never sliced). Frozen substrates `SUB-AVWAP`, the harami entry population (see consolidation below), `SUB-RANDOM`. GROSS (operator 2026-06-22); `ASS` non-binding (G-017). 46 member cells × {3 derived + enumerated benchmark grid}.

**Gates:** **G-018a** gross screen (expectancy + median + matched-random excess, moving-block bootstrap one-sided lower bounds) → **S1** attribution (`X_full = X_fav + X_tail`; PASS iff the no-stop `X_fav` beats the per-cell matched-random control by the synthetic-null-calibrated margin `m_cell`) → **S2** tail non-residual (post-exit `tailmass ≤ 0.06` ∧ `q05 ≥ q05_control − 0.40` ATR; deferred + disclosed below `n ≥ 120`). Frozen `K_tail=3.0, τ_tail=0.06, δ=0.40, EVENT_FLOOR=30`; `derive_barriers` sha256 `34d03f45…` asserted == EXP-082 pin.

**Headline (read per-stratum, not flat):** `n_valid = 26` of 2070 rows. **4 S2-PASS — all `SUB-HARAMI-V2A × AUDUSD × 1h` (n=988): `AVWAP-FH`, `RR-1.5`, `RR-2`, `RR-3` (all conventional).** **22 S2-DEFERRED — `SUB-AVWAP × {NZDUSD, USDCAD, USTEC} × 4h` (n=44–78 < 120, binding S2 not evaluated).** All 26 trace to **4 underlying cells** (narrow breadth). **98.2% (2033/2070) died at the cheap G-018a gross screen**; the binding separability gate decided only 8 strata (7 fail@S2, 1 fail@S1).

**Mechanism:** all 26 survivors have `x_fav > 0` (min 0.81, mean 1.33 ATR) and `x_tail ≤ 0` (−0.199…0.0) — **genuine favourable-capture attribution, 0 tail-truncation artifacts**; the adverse stop subtracts (never manufactures) expectancy. **NOT the EXP-082 "harvest-median-leave-catastrophe" trap.** **Central finding: the data-derived `D1/D2/D3` earned no distinctive TRAIN support** — none in the binding S2-passed set; they survive only in the deferred AVWAP-4h cells alongside (not over) the conventional arms. On the one S2-adjudicated cell, conventional fixed-horizon/RR exits cleared the full gate and the bespoke derived exits did not → **the family's "data-derived beats conventional" thesis is unsupported on TRAIN.**

**Gate-shape caveat (carried to EXP-084 / cost layer):** the 3 RR S2-passers clear S2 by mechanical stop-truncation-to-point-mass (`tailmass = 0`, `q05_post = q05_control = −MAE_q90 ≈ −7.28 ATR`); S2 certifies "no separated continuous catastrophe mode" but is **silent on the −7.28-ATR-per-stop magnitude**, correctly deferred to EXP-084's cost-calibrated referee suite. `AVWAP-FH` passes S2 on a genuine continuous-tail measurement (`tailmass 0.022`).

**Audit (fix-and-rerun cycle):** first pass (28 survivors, sha `0796530c…`) **REVISE** on **C1 (Critical, verdict-material):** the two registered harami substrates have byte-identical entries (gross_exp diff 0.0) yet drew **different** matched-random nulls (control seeded by substrate index), and that control-draw noise alone flipped `AVWAP-FH` between them → moved `n_valid` and the pinned sha256. **W1 (Warning):** per-cell `m_cell` reuse anti-conservative for large-target RR arms. **Operator-directed fixes:** dedupe the entry-identical harami pair to one canonical screened stratum `SUB-HARAMI-V2A` (4→3 screened substrates) + recompute `m_cell` per candidate. **Re-run + Re-Audit PASS** (`fa4035f3…`): inconsistency gone, mechanism unchanged; per-candidate `m_cell` flipped **no** prior survivor (RR-3 survives correct calibration; one new *deferred* USTEC-4h RR-1 appears). Remaining non-blocking **W2:** `/EXIT-VP` (VP-POC) scored on a geometry-selected subsample → 1 deferred survivor (USDCAD-4h), not in the binding set, carried to EXP-084/parity work. Determinism byte-identical; holdout sealed; `derive_barriers` hash + EXP-080/081/082 provenance asserted.

**Disposition (G-018, operator decision):** weak-to-marginal case for the counted read — EXP-084 would test conventional exits on one cell, not the derived-exit thesis. Two routes: **(1) decline EXP-084, close HYP-004 at G-018, 0 lifetime reads spent** (falsification-first / file-drawer posture); **(2) ratify a narrowly-scoped EXP-084** on the 4 conventional AUDUSD-1h survivors under the pinned Holm rule + cost-calibrated referee suite, framed as conventional-exit testing, not derived-exit vindication. The 22 deferred AVWAP-4h candidates should not anchor a read. Registry disposition recorded (candidate-family HYP-004a outcome; multiplicity-registry EXP-083 item outcomes + harami consolidation; test-read-ledger disclosure, all strata stay 0/2 open).

<a id="exp-082-card"></a>
### EXP-082 — Mechanical Exit Derivation from the Frozen D3 Rule (HYP-003) — DERIVATION_DELIVERED

**Status:** COMPLETED. **Date:** 2026-06-22. **Phase 018, third experiment** (HYP-003 derive; 0 candidate slots, 0 counted TEST reads — derivation off TRAIN-only inputs, no market data read). Artifacts: [`EXP-082/`](../../../../python/experiments/EXP-082/) (report · results.md · audit.md · governance/pre-execution-review.md). New code: `xen.capgeo_exits` (the frozen, pure, sha256-pinnable `derive_barriers` — the binding artifact EXP-083 imports and re-fits per WF fold-TRAIN). Consumes only EXP-081 `substrate_cell_summary.parquet` + `run_metadata.json` (no `data/timebars/`, no domain build, no substrate regen).

**Instruments / Data Views:** 16 (VAL-003 universe minus DE30), via the EXP-081 TRAIN-derived per-cell statistics; no market data read here. Barriers in **ATR units** (EXP-081 norm); `H_cap` in **domain bars**.

#### Hypothesis Tests

1. **Frozen D0 §D3 rule application (deterministic, 0 stat tests):** per cell, emit `(T_fav, S_adv, H_cap)` for D1-MEDIAN-CAPTURE (`MFE_med`/`m_anti else MAE_q90`/`TTP_q75`), D2-TAIL-ROBUST (`MFE_med`/`min(m_anti,MAE_q90) else MAE_q90`/`TTP_q75`), D3-CAPTURE-EFFICIENT (`MFE_q40`/`m_anti else MAE_q90`/`TTP_med`). `H_cap = max(1, round-half-even(ttp_quantile))`.
2. **Validity / estimability / degeneracy gates:** ≥30-event floor, `T_fav>0`, `S_adv>0`, `H_cap≥1`, non-degenerate quantiles → `OK`/`UNDERPOWERED_DISCLOSED`/`DEGENERATE_DISCLOSED`.
3. **Integrity:** EXP-081 provenance fingerprint, byte-identical determinism replay, harami-substrate triple identity, `derive_barriers` sha256 pin.

No edge/pass verdict — the verdict is completeness (DERIVATION_DELIVERED). Per stratum; the structural-guard read (`T_fav` vs `S_adv` vs `|q05|`) is **disclosure only**, non-adjudicative.

#### Scope

- **Candidates (3, frozen at D0 §D2/§D3):** `D1-MEDIAN-CAPTURE`, `D2-TAIL-ROBUST`, `D3-CAPTURE-EFFICIENT` under `/EXIT-DERIVED`. No new countable item — locks the parameterization of items registered at the Phase 018 D0.
- **Grid:** 3 candidates × **184 member substrate-cells** = **552 barrier triples** (4 substrates × 46 EXP-080-READY cells; US500-4h, JP225-4h `COVERAGE_EXCLUDED`; no DE30).
- **D2 "tightened to the dip" operationalization (frozen at D0 §D3 prose):** `S_adv(D2) = min(m_anti, MAE_q90)` when the dip resolves, else `MAE_q90` — the only parameter-free, column-computable reading that adds no constant, reduces to `MAE_q90` when unimodal, and is tighter-or-equal to D1. Distinct function from D1 (diverges iff `m_anti > MAE_q90`).
- **Exclusions:** no exit applied, no return/P&L/expectancy, no G-018a screen, no separability gate (S1/S2), no WF fold, no `ASS` adjudication (all EXP-083); no grid search/tuning (barriers *are* the measured quantiles); no pooling as a binding statistic; no market data; TRAIN-only inputs; holdout sealed.

#### Results / Observations

- **DERIVATION_DELIVERED: 552/552 valid.** 0 underpowered, 0 degenerate (`derivation_validity.json`). Barriers comfortably interior: `T_fav` med 3.31 ATR (D1/D2) / 2.56 (D3); `S_adv` med 9.21 ATR; `H_cap` 34–73 bars (D1/D2, q75-based) / 17–41 (D3, median-based).
- **`s_adv_source`: 1 `m_anti` / 183 `MAE_q90` per candidate** (3/552 rows `m_anti` — only US500-1h `SUB-AVWAP`, `m_anti`=1.79). `m_anti` resolves 1/184 because the catastrophe is a heavy **continuous** tail (EXP-081 `dip_p` median 0.976), not a separated mode — `MAE_q90` fallback dominates, exactly as D9 anticipated.
- **D1 ≡ D2 on 184/184 cells** (`n_d1_ne_d2 = 0`): the lone resolved `m_anti` (1.79) is `< MAE_q90` (9.00), so `min()` returns `m_anti` = D1's value; everywhere else both use `MAE_q90`. **3 registered candidates = 2 distinct exit definitions on this snapshot.** D1/D2 remain distinct *functions* (audit: synthetic `m_anti=6>MAE_q90=4` → D1 keeps 6.0, D2 tightens to 4.0); EXP-083's per-fold re-fit could separate them.
- **Structural-guard disclosure (the crux read):** `S_adv` (~9.2 ATR `MAE_q90`) sits **at** the catastrophe edge `|q05|` (~9 ATR) — median `S_adv − |q05| = −0.008 ATR`, stop *outside* the catastrophe in ~50% of cells; `T_fav/S_adv ≈ 0.35` (D1/D2) / 0.28 (D3). Per substrate uniform (median `S_adv−|q05|`: AVWAP +0.06, both harami −0.0001, random −0.08). **The CF-HA-HARAMI-001 "harvest the median, leave the catastrophe" geometry reproduced in the derived exit.**
- **Integrity:** determinism byte-identical; harami triple-identity 46×3 bit-identical; EXP-081 provenance 8/8; `derive_barriers` sha256 `34d03f45…` matches on-disk (EXP-083 hash-pin will hold); EXP-081 summary sha256 pinned; `holdout_untouched`, `counted_test_reads=0`, `candidate_slots=0`. Audit independently re-derived all 552 triples from raw EXP-081 data with **0 mismatches**.

#### Hypothesis-Specific Conclusion

- **DERIVATION_DELIVERED.** The frozen D3 rule produces a well-defined, estimable triple-barrier exit for every member cell, deterministically and holdout-clean; the binding rule function is hash-pinned for EXP-083. **No edge claim.** The informative content is structural: the derived exits are a **wide generic-quantile stop behind a modest target**, with the rule's intended catastrophe-engaging instrument dormant — so **EXP-083's separability gate (S2) is the crux**, pre-loaded toward the derived stops doing little tail truncation.

#### Hypothesis-Agnostic Observations

- The derivation *built* exactly the guard the D3 rule specified and, in doing so, exposed that on this data the guard's tail-engaging instrument (`m_anti`, a separated-mode dip detector) is the wrong instrument for the *shape EXP-081 found* (a continuous heavy tail) — the same blind-spot family G-017 flagged for `ASS`. The rule degrades gracefully to `MAE_q90`, so no EXP-082 number moves, but the intended D2-vs-D1 differentiation is inactive on this snapshot.
- The derived exit reproducing the prior family's failure geometry sharpens the family's central question to a single test: is a *continuous* catastrophe tail cuttable by *any* barrier without destroying the median edge? EXP-083 (separability) answers it.

#### Audit / governance

- **Audit PASS (0C/1W/3I).** Verdict forensics independently re-derived all 552 triples from raw EXP-081 data to full float precision (0 mismatches), recounted the per-stratum `m_anti`/`MAE_q90` and D1-vs-D2 splits (no masking), proved purity/determinism, and confirmed the D2-distinct-from-D1 faithfulness + both sha256 pins. **W1** (the derived adverse stop does not engage the catastrophe it was designed to cut — gate-shape/mechanism) is shown to **move no EXP-082 verdict-bearing number** (the rule is faithfully applied; the dormancy is the honest, D9-anticipated output) → document-and-proceed, carried to Stage 6 / EXP-083, no rerun. I1 3 candidates → 2 distinct definitions; I2 `H_cap` banker's-rounding+floor deterministic; I3 plots are disclosure of definitions, not results. See [`audit.md`](../../../../python/experiments/EXP-082/audit.md).
- **Pre-execution governance** APPROVE (no revision cycle); two Info transparency flags (D2 operationalization, anticipated D1≡D2 coincidence) documented in scope/plan.

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
