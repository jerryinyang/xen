# Candidate Family: CF-CAPGEO-001 — Data-Derived Exit / Capture Geometry on Frozen Entries

**Status:** `REGISTERED` (2026-06-20) — **SCREENING-UNBLOCKED 2026-06-21; Phase 018 OPEN (G0 PASS) —
HYP-001 readiness COMPLETE 2026-06-22 (EXP-080 READINESS_DELIVERED): 46-cell member set. HYP-002
characterization COMPLETE 2026-06-22 (EXP-081 CHARACTERISATION_DELIVERED, audit PASS): 184/184 cells,
D3 inputs locked & EXP-082-ready; gross capture availability ≈ random (move availability not the
differentiator), the only structure is the outcome shape — harami median-positive/mean-killed
(CF-HA-HARAMI-001 signature reproduced on 5-year data). 0 candidate slots / 0 counted TEST reads;
holdout sealed. Derivation (EXP-082, HYP-003) is next; family stays REGISTERED/SCREENING.** The family is registered (fixed first-branch definitions frozen;
multiplicity batch entered; governing checkpoint commenced). **Both screening preconditions have now
cleared:**

1. **G-017 — RESOLVED `DISCOVERY_ONLY` (2026-06-21).** Phase 017 validated the `ASS` qualifier and
   `WF-EXPANDING` protocol framework-style; 6 of 8 `ASS_VALIDATED` legs hold but **EXP-078's two binding
   legs FAIL** (shape diagnostic structurally blind to the subtle median-positive minority-catastrophe
   shape; shrunk edge-call FPR `k`-fragile), so the conjunction cannot hold. Per the predeclared D5
   routing, `ASS` is **demoted to non-binding discovery use** and the **frozen referee suite
   (EXP-003/012/018 + EXP-027/070-analog calibration) remains the binding gate** for this family. Not
   `PROTOCOL_DEFECT` (determinism held; accounting cap honored 8/8). Phase 018 therefore opens with the
   frozen suite binding and `ASS` as a discovery overlay only — **not** "once `ASS_VALIDATED`."
   (`checkpoints/2026-06-20-017-capgeo-qualifier-validation/G-017-gate-review.md`.)
2. **INFR-003 COMPLETE — ADMITTED via VAL-005 PASS (2026-06-21).** The 5-year 1-minute data upgrade
   was collected on **16 instruments** (DE30 dropped — broker m1 stale; design §3.1), VAL-005-validated
   (all 5 gates PASS), and the new final-30% holdout **re-sealed per file at first touch** (0 holdout
   rows read). `test-read-ledger.md` was **re-materialized** on the new 16×{15m,1h,4h} strata (all 0
   counted reads); the EURUSD old-dataset cap is carried as a disclosed caution, re-evaluated at the
   Phase 018 D0. Phase 018 screening runs on the new 5-year dataset using the holdout-fenced
   `build_domain_bars` domain construction (VAL-005 G1 finding). Phase 017 ran on synthetic substrates
   and the **current** first-70% analysis slice only. (VAL-005 report:
   `python/experiments/VAL-005/report.md`; master index Infrastructure Tasks.)

**Governing checkpoint (qualifier/protocol gate):**
`docs/experiments-docs/checkpoints/2026-06-20-017-capgeo-qualifier-validation/design.md`
**Primary registry:** `docs/signal-registry/multiplicity-registry.md` (Phase 017 + Phase 018 batches)
**Component specs:** `docs/signal-registry/components/global-techniques.md`
(`ASS` qualifier, expanding-window walk-forward protocol, volatility-adjusted sizing)
**Provenance:** `.ignore/dump/re.md` (final consolidated draft, 2026-06-20), with
`infrastruture+exit.md`, `ass.md`, `wf-model.md`, `discussion-1.md`, `mmm.md`; and the standing
reference `docs/experiments-docs/reflections/2026-06-19-two-family-retrospective-reflections.md`.

This is a candidate family, not a proven strategy. Phase-plan content (Phase 017/018 split, gate
definitions, slate) lives in the governing checkpoints, not here.

---

## Thesis

Both prior families produced a real edge and both died downstream, on the **same** abstract
failure — *the lever that removes the binding obstacle also removes the edge* (retrospective §4.1).
CF-AVWAP-001 closed on **capture geometry** (the move was 5–9× the cost floor but no deterministic
exit realized it net-of-cost); CF-HA-HARAMI-001 closed on **entry bimodality** (a real median edge
whose mean could not be lifted at entry). The highest-leverage remaining unknown is therefore the
**peak → realizable-net-capture conversion** — the exit / position-management / capture geometry —
not another entry signal (retrospective §6.1).

CF-CAPGEO-001 is the first family **chosen for how a system exits, not how it enters.** It fixes
the entry side to known objects and makes exit / capture geometry the sole open axis, asking a
**reverse-direction** question:

> Not "how does this system perform under this arbitrary exit?" but **"what does a system's own
> realized return structure tell us about the exit geometry that captures it efficiently and
> realistically — and does a data-derived exit beat the conventional exits we already know?"**

The binding objective is **overall expectancy** (net, risk-aware), not raw per-signal return — an
explicit anti-overfitting posture carried from `re.md` and the retrospective.

### Methodological inheritance (not a follow-up)

This family is defined by its *exit-design posture and risk-aware evaluation*, not as a
continuation of either closed family. It deliberately reuses the two closed families' **frozen
final entry candidates as fixed substrates** so the prior families act as built-in benchmarks for
the question *"does the infrastructure/evaluation remodelling produce better interpretations or
uncover new insights?"* Reusing a closed family's entry as a **fixed, non-tuned substrate for an
off-surface exit-design method** is not a reopening of that family's exhausted registered surface;
the harami remains separately closed and reopenable only by its own scope/D0/G0.

## Brainstorming Provenance

Promoted from the operator's consolidated draft. Original ideas and their registry treatment:

| Original idea (`re.md` / dump) | Registry treatment |
| --- | --- |
| New family chosen for exit/capture geometry, entries frozen. | Adopted as the family thesis; entry substrates frozen as fixed first-branch primitives below. |
| Entry models = two frozen prior-family final candidates (AVWAP-final; Harami PARTIAL-V2A and V2A-ADVNONE). | Adopted **+ a Random-entry matched-control substrate** (operator decision 2026-06-20) for attribution discipline (retrospective §6.3). |
| Reverse-direction exit design: derive the exit from observed return structure, then benchmark known exits. | Adopted as the Phase 018 slate posture (characterize → derive → test + conventional benchmark). |
| New signal-qualification model: adaptive-bandwidth KDE + empirical-Bayes shrinkage + bootstrap CI, scored on expectancy (+ probability-of-return extension). | Registered as component **`ASS`** (Adaptive Signal Scoring) — **but scored on expectancy + median + an explicit tail/bimodality diagnostic** (retrospective §4.2), and **validate-first** (Phase 017) before it can adjudicate. |
| Risk-adjusted / volatility-adjusted returns before evaluation (vs raw returns). | Registered as component **volatility-adjusted sizing**; a registered Phase 018 variant, judged against the raw-return baseline as a hypothesis, never assumed superior. |
| Expanding-window walk-forward replacing single TRAIN/TEST split. | Registered as the **expanding-window walk-forward protocol** component; validated in Phase 017 (its interaction with the 2-read TEST-stratum cap is a binding design item, §Protocol below). |
| Multi-timeframe model; volatility-regime characterization (`mmm.md`). | Deferred backlog variants (`/MTF`, `/VOLREGIME`); not in the first branch, registered for later scopes. |
| 5 years of 1-minute data (cAlgo). | Routed to **INFR-003** (own infrastructure task; re-seals the holdout). Screening precondition. |

## Fixed First-Branch Definition

The "first branch" is a set of **frozen primitive definitions**, not a frozen end-to-end strategy.
Each parameter is a **governance parameter** fixed per scope and ratified at the Phase 018 D0/G0;
it is never tuned against analysis-set outcomes. Sensitivity over any parameter is a separate
registered branch, not an in-place revision.

### Entry substrates (FROZEN — the closed axis)

Entries are **frozen and never tuned** in this family. Four substrates, run in parallel and
reported individually (never pooled across substrates without a demonstrated-homogeneity claim,
retrospective §2.5):

1. **`SUB-AVWAP`** — the CF-AVWAP-001 final candidate (faithful selective AVWAP bounce; the
   EXP-028/029 cTrader-confirmed entry, frozen parameters).
2. **`SUB-HARAMI-PARTIAL-V2A`** — the CF-HA-HARAMI-001 `N-PARTIAL-V2A` entry population
   (MA(20,50)-native `/STRONG-STAT`-conditioned HA harami), entry frozen.
3. **`SUB-HARAMI-V2A-ADVNONE`** — the CF-HA-HARAMI-001 `N-V2A×ADV-NONE` entry population, entry
   frozen.
4. **`SUB-RANDOM`** — a fixed-seed random-entry matched-control baseline (per substrate domain),
   the attribution null: a data-derived exit must beat what the same exit earns on random entries.

*The harami substrates carry the entry only; their prior exits (PARTIAL-V2A / V2A-ADVNONE) are
two of the conventional-benchmark exits in Phase 018, not the family's frozen exit.*

### Data views

- Base source: 1-minute time bars from `data/timebars/` (post-INFR-003: the 5-year collection).
- **Domains: 15m, 1h, 4h** (focused; reduces the parameter space per `re.md`). Domain
  construction follows the established `min_coverage=0.90` convention **plus the holdout-fence**
  (`build_domain_bars`: drop any window whose label crosses the analysis-slice boundary — VAL-005
  G1 finding); temporal-integrity validated by VAL-005 (PASS) before any analytical use.
- Instruments: **16** — the VAL-003-admitted universe **minus DE30** (dropped at INFR-003 §3.1;
  broker m1 history ended 2026-01-16 — stale, cannot supply current-edge rows). DE30 may be
  re-collected via an alternate broker symbol in a later INFR item; until then CF-CAPGEO-001 is a
  16-instrument universe (VAL-005-admitted).

### Exit / capture geometry (the OPEN axis)

The single open design axis. **Two postures, both required (retrospective §6.1 + `re.md`):**

- **Conventional benchmark exits** (the comparison reference): RR-based fixed favourable/adverse
  targets, market-structure / price trailing, volume-profile (POC / value-area) targets, partial
  position splits (all variants), and the two prior-family exits (PARTIAL-V2A, V2A-ADVNONE,
  AVWAP fixed-horizon FH). Recalibrated and retested per substrate.
- **Data-derived exits** (the family's hypothesis): exits derived from each substrate's observed
  return-structure features (capture-time geometry, time-to-peak, exhaustion, bimodality) via
  **predeclared mechanical derivation rules** — *freeze the rule, not the story* (retrospective
  §2.1). The derivation rule is frozen at D0; the narrative it produces is not.

### Evaluation posture (binding)

- **Co-primary endpoint: expectancy + median + an explicit tail/bimodality diagnostic** — never
  any one alone (retrospective §4.2). Expectancy is the binding economic endpoint; the median and
  tail diagnostic are emitted from the start because the entries sit over asymmetric/bimodal
  geometry.
- **Binding qualifier:** `ASS` **only if** G-017 `ASS_VALIDATED`; otherwise the frozen referee
  suite is binding and `ASS` is discovery-only.
- **Matched-random null in every read** (`SUB-RANDOM` and per-cell matched-random controls):
  signal attribution requires beating the same-substrate random control, not just clearing zero.
- **Risk-aware returns:** volatility-adjusted sizing is a registered variant tested as a
  hypothesis against the raw-return baseline.
- **Default to per-stratum adjudication;** any pooled statistic is a disclosure until
  cross-cell homogeneity is itself demonstrated (retrospective §2.5).

### Separability gate (binding, pre-TEST — the single most actionable inherited lesson)

Before any counted TEST read, every candidate must pass a **separability check** (retrospective
§4.1): demonstrate that the binding net-expectancy leg and the favourable signal are **not** driven
by the same unfilterable mechanism — i.e., the obstacle can be moved without moving the edge. A
candidate that fails separability is a median-only / capture-bound artifact, however real, and is
not carried to a TEST read. This gate is predeclared at the Phase 018 D0.

## Evaluation Protocol — Expanding-Window Walk-Forward (binding design item)

Phase 018 replaces the single chronological TRAIN/TEST split with an **expanding-window
walk-forward** (component spec; `wf-model.md`): `Train A → Test_A`, then
`Train A + Test_A + Train B → Test_B`, … Rolling windows (1y/2y/3y) are a disclosed comparison.

**Governance interaction (must be resolved in Phase 017 / at Phase 018 D0):** the TEST-read ledger
caps each instrument×domain stratum at **2 lifetime counted reads**. A multi-fold walk-forward can
consume many reads per stratum. The expanding-window protocol's counted-read accounting — what
constitutes a counted stratum-specific read vs an in-protocol fold disclosure, and how the lifetime
cap is honored on the new 5-year strata — is a **binding predeclaration**, validated as part of
G-017 before any Phase 018 TEST contact. The final-30% global holdout is **never** part of any
walk-forward fold.

## Hypotheses and Experiment Sequence

Registry HYP numbering is local to this family. The qualifier/protocol validation lives in
**Phase 017** (component validation; see the Phase 017 batch — not family candidate screening).
The Phase 018 family slate (EXP-IDs assigned in the Phase 018 design, after INFR-003 + VAL-005; G-017
resolved `DISCOVERY_ONLY` 2026-06-21 → the frozen referee suite is the binding gate, `ASS` a discovery
overlay) is sketched below; gate definitions and outcome criteria live in the Phase 018 design.

| HYP | Question | Phase | Gate | Status |
| --- | --- | --- | --- | --- |
| (gate) | Does `ASS` recover known expectancy/median/tail across unimodal/skewed/bimodal/sparse synthetic types, control FPR/MDE under the walk-forward protocol, and discriminate bimodal vs unimodal shape? | 017 | **G-017 `ASS_VALIDATED` → binding-eligible; else DISCOVERY_ONLY** | **G-017 ADJUDICATED 2026-06-21 — `DISCOVERY_ONLY`** (`ASS` non-binding; frozen referee suite stays the binding gate for Phase 018; no PROTOCOL_DEFECT). — **EXP-076 G-017a RECOVERY_VALIDATED (2026-06-20):** `ASS` recovers ground truth (recovery PASS all 198 cells; coverage in-band ∀ n≥30; shrinkage as designed). Caveat: expectancy-CI under-covers at **n<30** (intrinsic small-sample percentile-bootstrap floor of the mean — disclosed sparse-stress diagnostic, not a defect; median CI in-band at all n). Two dispositions to G-017: (a) coverage binding n≥30 (n=15 expectancy diagnostic), (b) downstream guard — **no expectancy edge-calls at effective n<30** (weakened-evidence) + EXP-077 adds a small-n FPR stratum; n=2000 rich-pull marginal read monotone-decreasing. **EXP-077 VALIDATED_WITH_GUARDS (2026-06-20):** error-control + protocol legs validated under `WF-EXPANDING` — MDE finite ∀ n≥30; `P(>X)` reliability holds X=0/0.05/1.0; counted-read accounting honors the 2-read cap (8/8); real-bar dogfood 12/12 cells, first-49% fence held, 0 counted reads; determinism+anchor exact. Two bounded per-stratum guards: **(i)** the small-n FPR check closes — expectancy-FPR inflates mildly on the **bimodal mean-null at effective n≤60** (B_zero 0.059 at n=30/60, decays to ~0 by n≥120) → defer to median there (location-null `U0` controlled: point crossings are MC noise around a 0.05-calibrated margin, all Wilson-hi≤0.075); **(ii)** the D2.4 calibration **slope** sub-gate is inapplicable when predicted `P(>X)` is compressed (X=2.0 max-gap 0.017/corr 0.934 but slope 0.652) → bind on max-gap. No PROTOCOL_DEFECT; gates not retro-edited; audit PASS (0C/1W/3I). **EXP-078 SHAPE_DISCRIMINATION_FAIL + k_FRAGILE → DISCOVERY_ONLY (2026-06-21):** the shape diagnostic does **not** discriminate the full target shape — it catches gross bimodality / strong left-skew (`B_strong`, `B_neg`) but is **structurally blind** to the subtle median-positive minority-catastrophe shape (`B_zero` true \|g\|=0.25 / `B_pos` \|g\|=0.067 — the CF-HA-HARAMI-001 failure shape; detection decays to 0 with n because true \|g\|<τ_gap=0.30 AND not dip-bimodal, dip_p≈0.99). **Documented qualifier limitations carried to G-017/Phase 018:** (1) **`ASS`'s shape leg only PARTIALLY closes the EXP-074 tail-shape-blind gap** — a subtle-bimodal blind spot remains; (2) clean-unimodal false-flag is controlled only at **n≥60** (the n=30 floor false-flags 0.135–0.152); (3) the shrunk-expectancy edge-call **FPR is `k`-fragile** (K2 flips CONTROLLED→INFLATED at the 2× multiplier k=240; K1 shrinkage behaviour invariant). Determinism held (no PROTOCOL_DEFECT); audit PASS-trust (0C/2W/4I), double-FAIL implementation-faithful. **Pre-registered routing: the shape FAIL means `ASS_VALIDATED` cannot hold → terminal G-017 `DISCOVERY_ONLY`** (`ASS` non-binding; the frozen referee suite stays the binding gate for Phase 018; adjudicated at the checkpoint gate review). Family status **unchanged** (`REGISTERED — SCREENING-GATED`): this is a qualifier-validation outcome, not a candidate screen. |
| HYP-001 | Substrate/exit readiness: are all four entry substrates deterministic, look-ahead-safe, with adequate per-cell coverage on the 5-year data × {15m,1h,4h}? `SUB-RANDOM` seed fixed. | 018 | Readiness; required before any characterization. | **EXP-080 COMPLETE 2026-06-22 — READINESS_DELIVERED (re-audit PASS).** 184/192 substrate-cells READY (16 instruments). 2 cells `COVERAGE_EXCLUDED` (retained): US500-4h (0.251), JP225-4h (0.281) — genuine 4h cash-equity-index coverage sparsity (invariants+determinism pass; EXP-043 precedent) → excluded from EXP-081 with record. **Member set for EXP-081 = 46 instrument×domain cells.** D7 192/192 IN_BRACKET [15,8000]; null-FPR machinery controlled in the binding operating regime n≥120 (validated m_cell scale); 0 nondeterministic, 0 invariant failures; harami entry-identity holds ∀ cells; regression vs VAL-005 frame-identical. 0 slots / 0 counted TEST reads (readiness = disclosure); holdout sealed. |
| HYP-002 | Characterize (TRAIN-only, gross): per-substrate realized return-structure features — capture-time geometry, time-to-peak, exhaustion, bimodality — that "expose the features defining what exit fits." | 018 | Characterization; 0 slots, feeds derivation. | **EXP-081 COMPLETE 2026-06-22 — CHARACTERISATION_DELIVERED (audit PASS 0C/1W/3I).** 184/184 member substrate-cells; **D3 inputs locked & EXP-082-ready** (T_fav=MFE_med/MFE_q40, S_adv=m_anti else MAE_q90 — m_anti NaN 183/184 → MAE_q90 fallback by D9, H_cap=TTP_q75/TTP_med); no cell below the 30-event floor. **Gross capture availability ≈ random** (per-cell paired vs within-cell SUB-RANDOM: harami median MFE below random 17/46, AVWAP coin-flip 28/46, outcome-median edge ~chance 23–25/46) — move availability is not the differentiator (AVWAP-situation/EXP-047 echo). Only structure = outcome shape: harami **median +0.135 / mean ≈ 0.000, 33/46 cells median>mean** (catastrophic left-tail drag, tailmass 0.0526 > random 0.0437) — CF-HA-HARAMI-001 signature reproduced on disjoint 5-year data; AVWAP roughly symmetric; random baseline. ASS discovery NON-BINDING. Family stays REGISTERED/SCREENING (characterization only — 0 slots, 0 counted TEST reads, holdout sealed). → HYP-003 (EXP-082). |
| HYP-003 | Derive exits from HYP-002 behavior via predeclared mechanical derivation rules (freeze the rule). | 018 | Derivation; 0 slots. | **GATED** |
| HYP-004 | Test derived exits **+ conventionally benchmark the known exits**, judged under `ASS` (binding iff validated) + frozen suite, expectancy+median+tail co-primary, per substrate, with the pre-TEST separability gate. | 018 | Candidate screening (slots spent here, per variant). | **GATED** |

## Registered Non-Baseline Branches

Each requires a dedicated scope and EXP-ID before measurement; negative, blocked, and inconclusive
outcomes remain in the file-drawer ledger.

- `CF-CAPGEO-001/EXIT-DERIVED` — data-derived exit from the substrate's return structure
  (predeclared mechanical derivation rule).
- `CF-CAPGEO-001/EXIT-RR` — risk-reward fixed favourable/adverse target exits (benchmark).
- `CF-CAPGEO-001/EXIT-TRAIL` — market-structure / price trailing exits (benchmark).
- `CF-CAPGEO-001/EXIT-VP` — volume-profile (POC / value-area) target exits (`TickVolume` proxy
  disclosed).
- `CF-CAPGEO-001/EXIT-PARTIAL` — partial / scaled position-split exits, all variants (benchmark;
  includes the prior-family PARTIAL-V2A, V2A-ADVNONE, AVWAP-FH as named reference arms).
- `CF-CAPGEO-001/SIZE-VOLADJ` — volatility-adjusted position sizing (tested vs raw-return baseline).
- `CF-CAPGEO-001/MTF` — multi-timeframe model (deferred; `mmm.md`).
- `CF-CAPGEO-001/VOLREGIME` — volatility-regime signal characterization (deferred; `mmm.md`).

## Exclusions

- **No entry tuning.** Entry substrates are frozen; only exit / capture geometry and sizing are
  explored. Any entry-parameter change is out of family scope.
- No reopening of CF-AVWAP-001 or CF-HA-HARAMI-001 registered surfaces; reusing their frozen
  entries as fixed substrates is not a reopening.
- No frozen end-to-end strategy screen before each exit primitive is measured separately.
- No qualitative claim without a predeclared mechanical threshold and a declared baseline; prefer
  **calibrated / data-derived thresholds** over magic numbers (retrospective §5.3).
- No counted TEST read before the separability gate passes (§Separability gate).
- No pooling across substrates (or across cells) without a demonstrated-homogeneity claim.

## Real-Price and Holdout Discipline

- **All return, expectancy, capture-rate, and P&L figures use real time-bar prices**
  (`RealOpen/High/Low/Close`). HA prices and Renko brick prices are synthetic and **never** valid
  for any strategy P&L, signal-quality, or return outcome in this family. The harami substrates
  detect on HA candles but every outcome is on real prices.
- Cross-view comparisons align by timestamp (`CloseTime` / `SourceCloseTime`), never by bar index.
- The final-30% **global holdout is excluded from all analysis and from every walk-forward fold.**
  INFR-003 re-collects the dataset and **re-seals the holdout per file at first touch** on the new
  5-year data before any Phase 018 analytical read. Phase 017 touches no holdout (synthetic +
  current first-70% TRAIN only).

## Implementation Path

1. **INFR-003** (5-year 1-minute collection + VAL + holdout re-seal) — infrastructure precondition.
2. **Phase 017** — Python validation of the `ASS` qualifier and the expanding-window walk-forward
   protocol on synthetic substrates + a current-data dogfood (TRAIN-only). G-017 decides binding
   vs discovery-only.
3. **Phase 018** — Python characterization (readiness → characterize → derive → test) on the
   four frozen substrates over the 5-year data; conventional-exit benchmark in parallel; candidate
   registration only at the Phase 018 PROCEED gate.
4. cTrader strategy-host parity and the one-shot holdout follow the established pipeline once a
   candidate reaches suite qualification (no cTrader parity exists yet for the harami entry).
