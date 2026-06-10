# Phase 008 — Clinical Tradability: Selectivity, Instrument Selection, and Capture Efficiency

**Checkpoint type:** Research phase design.
**Date finalized:** 2026-06-10.
**Status:** COMPLETED 2026-06-10 — CLINICAL_TRADABLE (G2 SATISFIED); holdout shot
subsequently spent INCONCLUSIVE in Phase 009; see [retrospective.md](retrospective.md).
Design opened 2026-06-10. Gate parameters (§8) and financing
values (§5/A1) are operator-amendable **until the corresponding Stage-1 scope
freeze**; frozen thereafter.
**Amendments:** §8.4 amended 2026-06-10 (pre-execution, F02): an A1 strict pass is
necessary-but-not-sufficient for G2 — a TEST-stratum confirmation is required.
EXP-034's binding test level clarified to a genuine one-sided α = 0.05 (F01).
EXP-033 containment rule corrected to include the lifetime-completion clause (F08).
**Revision R1 (2026-06-10, pre-execution adversarial review of EXP-037/EXP-038,
before any TEST read):** see §11 — phase-level G2 multiplicity family (R1.1),
small-n null calibration with predeclared margin (R1.2), unified TRAIN/TEST
boundary convention (R1.3), B2 H\*-tie-break authorization recorded (R1.4),
tie-break spill containment (R1.5), freeze-recovery semantics (R1.6), EXP-038
route relabeled with nomination precondition and LOCO diagnostic (R1.7).
**Candidate family:** `CF-AVWAP-001` — Anchored VWAP on regime pivots (continued
from Phases 004–007).
**Follows:** `2026-06-09-007-avwap-tradability-and-isolation` (COMPLETED —
NOT_TRADABLE; EXP-030 INCONCLUSIVE, EXP-031 ISOLATION_READ_UNRESOLVED).

## 1. Provenance

Phase 007 closed NOT_TRADABLE: under the predeclared CONSERVATIVE event-level cost
model, the faithful selective AVWAP strategy is net-negative on 5m/1h (EVIDENCE_AGAINST)
and power-unresolved on 4h (n=187). The edge is **real but cost-dominated and
relative**: gross absolute per-event returns (+0.76/+1.46/+10.10 bps) sit an order of
magnitude below the matched-control excess (+5.78/+23.38/+69.02 bps), and the
non-binding companion confirms the gross edge survives costs on the matched-control
structure (1h/4h). EXP-031 left attribution horizon-dependent: entry-dominant at H=6,
exit-dominant at H=1, on all domains.

Phase 007 disclosures that motivate (and partially scope) this phase — all recorded
here as **data-dependent design inputs** (guardrail §7.4):

- **Per-instrument headroom:** EURUSD-4h net_cons +12.38 bps [+2.67, +21.46]
  (descriptive, multiplicity-uncontrolled); break-even RTs range 15.4 bps
  (EURUSD-4h) down to −0.1 bps (EURUSD-1h).
- **Pyramid split (`pyramid_net_split`, verified from `run_metadata.json`):**
  5m pyramid −7.51 vs non-pyramid −7.50 net (tie); 1h −4.88 vs −8.74 (pyramids
  better; gross absolute +3.31 vs −0.72); 4h +15.44 vs −12.49 (pyramids much
  better). Pyramid legs carry the absolute edge on the slower domains.
- **Exit-substitution profile (EXP-031):** the band-target/trend-change (BTC) exit
  cuts early losers (H=1 benefit) but truncates trends (H=6 drag; 4h X_exit −27 bps).

## 2. Objective

When an edge is real but cost-dominated, the admissible levers are **selectivity**
(fewer, better events), **instrument selection** (cheaper venues), and **capture
efficiency** (more gross per position) — not new signal. This phase tests all three
on the existing, validated entry substrate, under the **frozen Phase 007 cost model
plus a predeclared financing layer**, using the nested TRAIN/TEST split inside the
analysis set as the anti-overfitting backbone. The global holdout stays sealed; a
single one-shot holdout release becomes admissible only behind the strict gate G2.

## 3. Tier and gate structure (LOCKED)

```
Tier 0 (desk, no runs, no EXP-ID)
  D0  Disclosure-synthesis memo (this checkpoint dir): per-instrument breakeven
      map + pyramid_net_split + EXP-031 exit-substitution profile → ranks cells,
      fixes the declared cell set for A1; records all data-dependent choices.
        │
        ▼
Tier A (parallel; one verdict-grade screen + two TRAIN-only diagnostics)
  A1 = EXP-034  Per-instrument cost-bearing tradability screen   [verdict-grade]
  A2 = EXP-033  Horizon sweep s_entry(H) + FH(H) net curve, TRAIN ONLY  [DIAG-004]
  A3 = EXP-035  Conditioning characterisation, TRAIN ONLY               [DIAG-005]
        │
        ▼  GATE G1 (lenient, §8.1): any qualifying A1 cell, A3 dimension,
        │  or A2/D0 capture-efficiency case → open Tier B for the
        │  qualifying item(s) only. Nothing qualifies → Tier C decision.
        ▼
Tier B (one-shot TEST confirmations; ≤2 registered variants; 1 slot each)
  B1 = EXP-036 (provisional)  /COND  conditioned "clinical" variant
  B2 = EXP-037 (provisional)  /EXIT-FH  fixed-horizon-exit variant
                              (incl. TRAIN-frozen pyramid policy)
        │
        ▼  GATE G2 (strict, §8.4): net CI_low > 0 (Holm) on TEST (Tier B)
        │  or on the A1 declared-cell family → ONE holdout-release
        │  checkpoint (EXP-032, reserved) becomes admissible.
        ▼
Tier C (fallback / parallel science)
  C1  Stage-C branches (/LB /MB /ATR /ANCHOR) — only on Tier A/B failure
  C2  HYP-001 direct S/R test (Phase 007 design §8 framing) — mechanism
      science; may run in parallel when resources allow; never gates A/B
```

- **A1, A2, A3 are mutually independent and may run in parallel.**
- **TRAIN/TEST discipline:** A2/A3 read TRAIN (first 70% of the analysis set) only.
  Tier B variants are frozen from TRAIN reads and evaluated **once** on TEST (last
  30% of the analysis set). TEST is honestly not pristine — aggregate-level results
  on the full analysis set are known from EXP-028/030/031 — but stratum/variant-level
  reads are fresh. Final arbiter remains the sealed holdout.
- **EXP-032 stays reserved for holdout release** and is registered only behind G2,
  with its own checkpoint and governance.

## 4. Scope discipline

**In scope:** D0 memo; EXP-034 (per-instrument net tradability, declared cells);
EXP-033 (TRAIN horizon sweep diagnostic); EXP-035 (TRAIN conditioning
characterisation diagnostic); up to two Tier-B TEST-confirmation variants
(/COND, /EXIT-FH) if G1 qualifies them.

**Out of scope (carried, not worked):** holdout release (reserved EXP-032, behind
G2, own checkpoint); Stage-C detectors/anchor (Tier-C fallback only); HYP-001
(Tier-C parallel science, separately scoped if opened); `/ALPHA` `/BAND` `/XTF`
`/MA-DOMAIN` parameter branches; any change to the frozen per-bar suite, the frozen
EXP-027 method, or the frozen EXP-030 cost constants.

## 5. Experiment specifications

### D0 — Disclosure-synthesis memo (Tier 0)

Desk artifact `D0-disclosure-synthesis.md` in this checkpoint directory. No new
computation beyond reading existing EXP-030/031 result artifacts. Deliverables:
(1) the **declared cell set** for A1 (see A1); (2) the verified pyramid-policy
table per domain; (3) the exit-substitution summary; (4) an explicit list of every
design choice in this phase that depends on a disclosure read.

### A1 / EXP-034 — Per-instrument cost-bearing tradability screen (verdict-grade)

- **Question:** does any declared instrument×domain cell retain positive **net**
  per-event expectancy (absolute estimand, EXP-030 definition) under frozen
  CONSERVATIVE costs **plus financing**, on the full analysis set?
- **Declared cells (FIXED by D0, 2026-06-10 — amends the original 6-cell default
  within the pre-freeze window; see `D0-disclosure-synthesis.md` §1.1–1.2):**
  three cells by the mechanical rule "EXP-030 disclosure net_cons point > 0" —
  **EURUSD-4h (primary), USTEC-4h, XAUUSD-1h**, tested in that **fixed-sequence
  order** (each at one-sided α = 0.05, stop at first failure; FWER = 0.05 —
  replaces Holm for this family). All 5m and BTCUSD cells excluded by the
  break-even map; per-cell descriptive CIs disclosed for all 12 cells regardless.
- **Financing layer (predeclared; operator-amendable until this scope freezes):**
  bps per calendar day held, adverse-side regardless of direction —
  EURUSD **0.6**, USTEC **1.2**, XAUUSD **1.2**, BTCUSD **10.0**.
  Charge per position: `financing_bps = rate_i × holding_days` with fractional
  calendar days from entry-confirmation bar close to exit bar close; added to
  RT_i once. Triple-swap-day effects are averaged into the daily rate. Once
  frozen, **no post-result iteration of any cost component** (Phase 007 rule
  carries forward).
- **Power statement (mandatory in scope.md):** minimal detectable net effect per
  declared cell from the EXP-030 bootstrap dispersion (4h cells have n≈47/instrument;
  state explicitly which cells can and cannot resolve, before reading results).
- **Inference:** frozen EXP-027 regime-cluster bootstrap CI + one-sided bootstrap p
  (EXP-030's absolute-estimand substitution), Holm across the declared family.
- **Slot:** 0 — per-instrument estimand of the registered HYP-004 baseline + frozen
  cost layer; registry-noted.

### A2 / EXP-033 — Horizon sweep (TRAIN only; DIAG-004, 0 slots)

- **Outputs:** (1) the attribution map s_entry(H) over H ∈ {1,2,3,4,6,8,12,24}
  domain bars per domain — closes EXP-031's unresolved read by locating the
  crossover and testing whether attribution stabilizes; (2) the **FH(H) net curve**:
  TRAIN per-event absolute net expectancy of the fixed-horizon-exit variant at each
  H under frozen costs + financing — the design input for B2.
- **H\* selection rule (mechanical, predeclared):** per domain,
  `H*_d = smallest H whose TRAIN net is within one bootstrap SE of the grid
  maximum` (one-SE rule; prefers shorter holds → less financing; resolves
  multi-modal or knee-shaped curves with zero discretion). If the grid maximum is
  ≤ 0 for a domain, **B2 does not run on that domain.** The s_entry(H) attribution
  map never enters the H\* rule.

### A3 / EXP-035 — Conditioning characterisation (TRAIN only; DIAG-005, 0 slots)

- **Question (exploratory):** does per-event **net** expectancy (frozen costs +
  financing) vary materially and stably across three predeclared event-time
  dimensions?
- **Dimensions and bins (frozen before any TRAIN read):**
  1. **%completion-to-target at confirmation** — signed fraction of the
     entry→band-target distance already covered at the confirmation bar close
     (causal; both quantities known at confirmation). TRAIN-quantile terciles.
     Outcome must be **net expectancy**, never hit rate (the covariate is
     mechanically coupled to remaining-move size).
  2. **Session** — fixed UTC bins: Asia [00:00, 08:00), London [08:00, 16:00),
     NY [16:00, 24:00).
  3. **Trailing volatility regime** — ATR(14, domain bars) percentile within a
     trailing 90-day window, computed strictly from data ≤ event timestamp;
     TRAIN-quantile terciles.
- **Tests per domain×dimension:** ordered dims (1, 3) — top-vs-bottom tercile
  contrast Δ with regime-cluster bootstrap CI + one-sided permutation p; session —
  omnibus permutation heterogeneity test with the candidate bin = max-net bin.
  Split-half stability check (chronological halves of TRAIN).
- **Hard no-selection rule:** this experiment outputs characterisation only. No
  stratum is promoted inside A3; qualification happens at G1 and rule-freezing at
  Tier-B scope time.

### B1 / EXP-036 (provisional) — /COND conditioned variant (1 slot)

- At most **one frozen rule per G1-qualifying dimension**, frozen from TRAIN,
  evaluated **once** on TEST under frozen costs + financing, per-instrument verdicts
  with Holm across the declared TEST family. If ≥2 dimensions qualify in a domain, a
  single conjunctive rule is admissible **only if predeclared at Tier-B scope time
  before any TEST read** — no post-result mixing.

### B2 / EXP-037 (provisional) — /EXIT-FH capture-efficiency variant (1 slot)

- Exit replaced by FH(H\*_d) per domain (H\* from A2's mechanical rule).
- **Pyramid policy as a TRAIN-frozen composition element:** policy ∈ {all-legs,
  first-leg-only, pyramid-legs-only}, selected **per domain** on TRAIN by the same
  one-SE rule on net expectancy, frozen before TEST. (This subsumes the "no-pyramid"
  idea; under current disclosures pyramids are the stronger legs on 1h/4h and a
  blanket drop would not fire. Data-dependent design, registry-recorded.)
- **Honest expectation set:** the FH-exit prize on 5m/1h is small (exit-substitution
  dH ≈ +0.6/+0.8 bps absolute) — the realistic case is 4h, where the BTC exit's
  matched-control drag was −27 bps. A null result on 5m/1h is expected, not failure.
- Note: an FH exit does **not** reduce trade count or cost — entries and pyramids set
  position count. Its case is capture efficiency (gross per position). Trade-count
  reduction comes from B1's selectivity and the pyramid policy.

## 6. Multiplicity & registry gate

The first Phase 008 artifact is a registry amendment in
`docs/signal-registry/multiplicity-registry.md` that:

1. opens a Phase 008 batch section recording the Phase 007 close (NOT_TRADABLE);
2. registers **EXP-033** (DIAG-004, horizon sweep) and **EXP-035** (DIAG-005,
   conditioning characterisation) as diagnostics — 0 candidate slots;
3. registers **EXP-034** as a per-instrument tradability screen of the registered
   HYP-004 baseline + frozen cost layer — 0 candidate slots, declared-cell family
   fixed by D0;
4. reserves **EXP-036 `/COND`** and **EXP-037 `/EXIT-FH`** as Tier-B registered
   variants (1 slot each), to be activated only on G1 qualification;
5. keeps **EXP-032 (holdout release) DEFERRED / NOT REGISTERED**, admissible only
   behind G2 with its own checkpoint and governance;
6. records every data-dependent design choice (A1 cell declaration, pyramid-policy
   menu, B2 expectation set) as disclosure-derived.

## 7. Methodological guardrails

1. The final 30% global holdout is excluded from all Phase 008 analysis.
2. **The cost model is frozen** at EXP-030 CONSERVATIVE values; the financing layer
   is predeclared in §5/A1 and frozen at A1 scope freeze. A net-negative result is
   never permission to try another cost model.
3. **TRAIN-only characterisation; TEST touched once per registered variant.** All
   selection (strata, H\*, pyramid policy) happens on TRAIN via mechanical
   predeclared rules; TEST reads are one-shot confirmations.
4. **Every disclosure-derived design choice is registry-recorded** as
   data-dependent.
5. At most one frozen rule per conditioning dimension; **≤2 Tier-B variants**; no
   post-result recombination; conjunctive rules predeclared before TEST.
6. Time bars order by `CloseTime`; all outcomes use real OHLC; no look-ahead — all
   conditioning covariates are computable at the event confirmation timestamp.
7. **Two-speed gating:** exploration-continuation gates (G1) are lenient;
   resource-spending gates (G2, holdout) are strict. A branch is never closed on a
   wide CI; it is only promoted on a tight one.
8. 5m expectation set: with +0.76 bps gross absolute against ≥3 bps RT, 5m survives
   only under extreme selectivity; 1h/4h (EURUSD especially) are the realistic
   carriers. A 5m wipe-out anywhere in this phase is an expected outcome.

## 8. Gate specifications (predeclared; amendable only until the first Tier-A scope freeze)

### 8.1 G1-A3 — conditioning dimension qualification (lenient)

Per domain d and dimension k, dimension k **qualifies** on d iff ALL of:

- **(i) Material:** top-vs-bottom contrast Δ ≥ its own 95% bootstrap CI half-width
  (signal-to-noise ≥ 1), **and** the top/candidate bin's TRAIN **net** expectancy
  point estimate > 0 under frozen costs + financing.
- **(ii) Structured:** ordered dimensions (%completion, vol) show weak monotone
  ordering of bin net point estimates; session passes its omnibus permutation
  heterogeneity test.
- **(iii) Stable:** chronological split-half of TRAIN — same top/candidate bin in
  both halves **and** Δ > 0 in both halves.
- **(iv) Multiplicity:** the dimension's permutation p survives Holm across the
  **3 dimensions within domain d** at **α_G1 = 0.10**.

### 8.2 G1-A1 — instrument-cell continuation (lenient)

A declared cell continues to Tier-B/G2 consideration if its net point estimate > 0
and its CI is not entirely below 0. (Verdict-grade EVIDENCE_FOR additionally
requires the strict §8.4 criterion — a cell can *continue* leniently and still not
*pass* strictly.)

### 8.3 G1-B2 — capture-efficiency case (lenient)

B2 opens on domain d iff A2's FH net curve has a grid maximum > 0 on TRAIN for d
(§5/A2 rule). The pyramid-policy menu is selected on TRAIN regardless.

### 8.4 G2 — holdout-release admissibility (strict; AMENDED 2026-06-10, pre-execution)

**Amendment (F02, adversarial review 2026-06-10, before any Tier-A execution):**
the original §8.4 allowed an A1 fixed-sequence pass *alone* to make EXP-032
admissible. That route selects its cell family from EXP-030 disclosures and tests
on the same analysis data — no out-of-sample read — so the weakest evidential path
would have carried the most expensive consequence. A1 is therefore demoted to
necessary-but-not-sufficient.

G2 is satisfied **only by a TEST-stratum result**:

- a Tier-B variant (EXP-036 `/COND`, EXP-037 `/EXIT-FH`) shows net CI_low > 0 on
  TEST with Holm across its declared TEST family; or
- an **A1-cell TEST confirmation**: an A1 strict pass (one-sided α = 0.05
  fixed-sequence, D0 §1.2) routes the passing cell into a one-shot evaluation of
  the same registered baseline estimand on the held-back TEST stratum (registered
  within Tier B; 0 new slots; predeclared before the TEST read), and that
  confirmation shows net CI_low > 0 at one-sided α = 0.05.

An A1 strict pass without TEST confirmation is recorded as
`A1_STRICT_PASS_TEST_CONFIRMATION_REQUIRED` and does not open the holdout. If
multiple candidates pass G2, the operator selects **one** fully predeclared package
for the single holdout shot. The holdout is never released to confirm gross,
descriptive, lenient-gate, or in-sample-only results.

**R1.1 — phase-level G2 multiplicity family (AMENDED 2026-06-10, pre-execution,
before any TEST read).** The two G2 routes above are NOT independent (EXP-038's
TEST stratum and EXP-037's EURUSD-4h TEST cell are essentially the same events
under different exit rules); leaving each route at its own α would put the union
false-pass probability of "holdout becomes admissible" near 2α. Therefore all
**realized binding one-sided TEST p-values of Phase 008 form a single Holm family
at α = 0.05** — up to 4 members: the 3 EXP-037 cells (EURUSD/USTEC/XAUUSD-4h) and
the 1 EXP-038 cell (EURUSD-4h). Family membership is fixed before any TEST read:
EXP-038's read is always in; EXP-037's 3 reads are in iff its TRAIN-only freeze
selects an H\* (a `B2_NO_ROBUST_HSTAR` freeze shrinks the family to 1 — a
TRAIN-determined event, fixed before any TEST contact). Each experiment emits its
**raw** one-sided bootstrap p and a clearly labeled **provisional** route-level
flag; the **binding G2 verdict is adjudicated once, mechanically, in a desk
artifact `G2-gate-review.md`** in this checkpoint directory after both experiments
complete: a cell passes G2 iff its phase-family Holm-adjusted one-sided p ≤ 0.05
AND its margin-adjusted one-sided lower bound clears (R1.2). No code in either
experiment may declare `g2_satisfied`; both emit `PENDING_PHASE_FAMILY_HOLM`.

**R1.2 — small-n null calibration with predeclared margin (AMENDED 2026-06-10,
pre-execution).** The frozen EXP-027 bootstrap was FPR-calibrated at domain-level
populations (4h n≈187 pooled), never at ~11–13-event single cells; percentile
bootstrap on a handful of regime clusters is typically anti-conservative. Before
its TEST read, each binding experiment runs a **synthetic-null calibration of the
frozen bootstrap at the matched cell structure** (no TEST-outcome contact):
cluster sizes and direction labels taken from the TEST stratum's **entry
attributes**; null returns generated from a zero-mean Gaussian cluster model
(r = a_c + e_i) with between/within variance components estimated from
TRAIN-stratum nets (method of moments; predeclared in each plan); R = 2000 null
replicates, each scored by the frozen 1000-resample bootstrap. Outputs (persisted
**before** the freeze/TEST read): the measured null FPR of the uncorrected rule
and the **binding margin** `m_cell = max(0, Q95 of the null ci_low_1s
distribution)`. The binding bound rule becomes **`ci_low_1s > m_cell`** (reduces
to the original `> 0` whenever the cell is not anti-conservative). The margin is
mechanical — no operator discretion, no post-result iteration.

**R1.3 — unified TRAIN/TEST boundary convention (AMENDED 2026-06-10,
pre-execution).** The binding TEST-stratum boundary for ALL Phase 008 TEST reads
is the **1-minute-row timestamp convention**: boundary = CloseTime of the last
TRAIN 1-minute analysis row (`train_rows = int(analysis_rows × 0.7)`, the shared
loader's `train_end_ts`); an event is TEST iff its trigger close time > boundary
(ties → TRAIN). A domain-bar-index rule (floor(0.7 × n_domain_bars)) is admissible
only inside reproduction anchors of prior experiments that used it (EXP-037
guard 1 vs EXP-033); it must not define any binding TEST membership. EXP-037
discloses the membership divergence between the two conventions per cell. With one
boundary, EXP-037-TRAIN ∩ EXP-038-TEST = ∅ on EURUSD-4h by construction, so
execution order cannot leak EXP-038 TEST events into EXP-037's selection.

## 9. Phase outcome criteria

| Outcome | Criteria | Consequence |
| --- | --- | --- |
| CLINICAL_TRADABLE | ≥1 A1 cell or Tier-B variant passes G2 (strict). | First net-positive AVWAP candidate. Holdout-release checkpoint (EXP-032) admissible; operator selects the one-shot package. |
| CHARACTERISED_NOT_CONFIRMED | G1 qualified ≥1 item but nothing passed G2. | Heterogeneity/efficiency structure documented; family review with sharply better priors; Tier C opens. |
| FLAT | Nothing qualifies at G1. | Selectivity/efficiency levers exhausted on this entry substrate; Tier C (Stage-C branches, HYP-001) is the path. |

## 10. Non-goals

- Holdout release (reserved EXP-032; strictly behind G2, own checkpoint).
- Any cost-model iteration after freeze.
- Parameter sweeps against TEST or analysis-set verdicts (TRAIN-only selection via
  mechanical rules is the sole admissible selection).
- New detectors/anchors inside Tiers A/B (Tier C only).
- Re-running EXP-025's confounded HYP-001 metric.
- Any change to the frozen per-bar suite, the frozen EXP-027 method, or the frozen
  EXP-030 cost constants.
- Any use of the global holdout.

## 11. Amendment record — Revision R1 (2026-06-10, pre-execution adversarial review of EXP-037/EXP-038)

Recorded before any Tier-B TEST read; both experiments were approved but unexecuted.
Findings map: EXP-037 review F01–F06; EXP-038 review F01–F05.

- **R1.1 (EXP-037 F04 / EXP-038 F03 — Major):** phase-level G2 Holm family across
  all realized binding TEST p-values; binding adjudication moved to
  `G2-gate-review.md`. Full text in §8.4.
- **R1.2 (EXP-037 F01 / EXP-038 F02 — Major):** synthetic-null small-n calibration
  of the frozen bootstrap at matched TEST cell structure, with the mechanical
  margin `m_cell = max(0, Q95 null ci_low_1s)` on the binding bound. Full text in
  §8.4. The calibration is selection/verification machinery of the existing frozen
  family, not a new test family.
- **R1.3 (EXP-037 F03 / EXP-038 F04 — Major/Minor):** one TEST-stratum boundary
  for the phase — the 1-minute-row timestamp (`train_end_ts`); bar-index cutoffs
  confined to reproduction anchors; divergence disclosed. Full text in §8.4.
- **R1.4 (EXP-037 F02 — Major):** the §5/B2 sentence "Exit replaced by FH(H\*_d)
  per domain (H\* from A2's mechanical rule)" is **amended**: after EXP-033
  disclosed `h_star_stable = false` (split-half argmaxes 24 vs 12), the operator
  replaced A2's one-SE pick with a TRAIN-only robustness tie-break over
  H ∈ {4,6,8,12} (stability filter N, N₁, N₂ > 0; max-min worst-half selection;
  smaller-H tie rule; empty set → `B2_NO_ROBUST_HSTAR`). This amendment records
  that replacement with the same standing as the F02/F08 amendments and classifies
  the H\* rule as **second-generation data-dependent** (crafted after a TRAIN
  disclosure read): the registry entry must carry that label, and the
  slot-consumption probability (`B2_NO_ROBUST_HSTAR` vs a TEST read) is
  acknowledged as a data-shaped quantity. The tie-break itself remains mechanical
  and TRAIN-only; verdict validity on TEST is unaffected.
- **R1.5 (EXP-037 F05 — Minor):** the H\* tie-break objective is computed on the
  **contained TRAIN subset**: events whose FH window at the grid maximum
  (H = 12) exits at or before the boundary timestamp (mirrors EXP-033's F08
  containment, fixed across candidate H so the selection population is constant).
  Boundary-spill events are **excluded from selection** (count disclosed), so the
  freeze is strictly TEST-price-blind; TRAIN/TEST membership and the binding TEST
  population are unchanged.
- **R1.6 (EXP-037 F06 — Minor):** (a) pre-freeze feasibility — a pyramid policy is
  a selection candidate only if every TEST cell remains non-empty under it, checked
  from **entry attributes only** (`is_pyramid_bounce` composition of TEST events);
  (b) recovery semantics — if a run halts after `frozen_selection.json` exists but
  **before any verdict artifact** (`test_verdicts.csv` / EXP-038
  `test_inference.csv`) is emitted, a rerun is **not** a second read; the rerun
  must reproduce the existing freeze/partition record exactly (content-hash
  assert) or hard-stop, and any run finding an existing verdict artifact must
  refuse to recompute TEST inference.
- **R1.7 (EXP-038 F01/F05 — Major/Minor):** the EXP-038 route is **relabeled** from
  "out-of-sample confirmation" to **"TEST-stratum temporal-stability subsample
  check"** — its TEST events are a dependent subsample of the data that both
  selected the cell (D0's rule on EXP-030 full-analysis disclosures) and produced
  the EXP-034 pass (~30% of that estimate), so stratum-level freshness is real but
  weaker than "out-of-sample" implies. Two predeclared additions: (a) **nomination
  precondition** — the operator may nominate the EXP-038 package for the holdout
  shot only if the non-binding TRAIN-stratum net point estimate is also > 0
  (directional consistency on the only disjoint complement available); (b) a
  **leave-one-cluster-out (LOCO) fragility diagnostic** — does the margin-adjusted
  bound stay clear when each TEST regime cluster is dropped — must **accompany**
  (never gate) any `A1_CELL_TEST_PASS`.
