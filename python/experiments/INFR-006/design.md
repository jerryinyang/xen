# INFR-006 — XENA: Portfolio-Construction Workflow + Referee Framework

**Status:** DRAFT plan — operator review required before any implementation
**Type:** Major infrastructure (INFR). Successor pattern: INFR-001 (plan + locked decisions).
**Sources (verbatim inputs, operator-supplied):**
- `.ignore/temp/new-referee/main.md` (principles)
- `.ignore/temp/new-referee/problem-statement.md` (problem + ILS recommendation)
- `.ignore/temp/new-referee/xena-model.md` (full design spec: LAHC + noise-aware acceptance + plateau certification)

---

## 1. Objective

Replace per-candidate adjudication with a portfolio-level system:

1. **No per-candidate evaluation.** Every (model variant × parameters × instrument × domain)
   is a valid candidate; no qualification gates at candidate level.
2. **Candidates run in cTrader**, emitting per-bar portfolio/returns streams.
3. **XENA framework** (per `xena-model.md`) selects the subset: shared-capital event-driven
   portfolio oracle → bootstrap-P25 objective → LAHC search → plateau + temporal
   certification → walk-forward final gate.

This is the sanctioned **L-12 fix pathway**: the frozen conjunctive referee over-rejects and
mis-scales; XENA replaces per-candidate thresholds with portfolio-level selection + independent
certification. Per L-12 governance clause: the new adjudicator must itself be **predeclared,
FPR-calibrated (dogfood-negative + synthetic-positive), and frozen before it judges any live
candidate** — WS-6 below.

## 2. Lessons compliance map (KB → XENA design)

| Lesson | How XENA honours it | Residual risk |
|---|---|---|
| L-01/P-09 | Signal logic cTrader-only; Python never generates entries/exits | Oracle must not re-derive signals (WS-2 contract) |
| L-03 per-stratum | **TENSION** — portfolio verdict is inherently pooled. Resolution: portfolio IS the object (L-16-native); per-candidate attribution via drop-neighbor screen (§9 spec) replaces per-stratum reads | Operator Q3 |
| L-12 | Whole framework = the fix; calibration-before-use clause applied (WS-6) | — |
| L-13/L-16 | Estimand native to the P&L object: the shared-account portfolio path, incl. rejected signals | — |
| L-15 | Plateau screen reports collapse fractions (min drop-neighbor ratio), not binary-only | — |
| L-17 | Short-band adjudication replaced by block-bootstrap distribution + pre-registered threshold; no fixed-n readiness floor | — |
| L-18 | Portfolio accounting = ONE canonical module (`xen.xena.oracle` extending `xen.adjudication` invariants); `check_no_local_accounting` extended to it | — |
| L-19/L-20 | Spec already mandates seed batteries, common-random-numbers pairing, circular block bootstrap with n-safe blocks + seed aggregation (reuse INFR-004-hardened `xen.evaluation` primitives) | — |
| L-21/L-22 | Oracle sims in **money** (account currency); spread + commission charged in-sim via FTMO cost table; no dimensionless→bps seam | Cost injection point in oracle (WS-2) |
| L-23 | XENA parameter registry (§11 spec) frozen at pre-registration; any amendment carries LOOSER/TIGHTER tag + running count | — |
| L-24 F02 | Sequential-window decay inspection (§A.4.4) + chronological-thirds stability read on finalists | — |

Pitfalls: no P-01..P-15 direction is re-opened by this INFR itself (it builds apparatus, not
candidates). Candidate universes proposed later must still clear the pitfalls ledger.

## 3. Price-primary carve-out (needs codification)

Rule today: "Python backtest of a price strategy is REJECT-class." XENA needs a precise split:

- **cTrader (per candidate, once):** full signal logic; emits the **standard fills-based
  emission** under the `AnalysisEndUtc` fence (contract as built in WS-1, amended 2026-07-10
  from the earlier intent-stream sketch to match the implementation — fill-anchored is
  stronger): `positions.parquet` (per-bar `SourceCloseTime` + `RealOpen` mark grid) +
  `cis_trades.parquet` per-leg ledger (`EntryTime, ExitTime, Direction, EntryFillPrice,
  ExitFillPrice, RealizedBps, Censored`, **plus finite `SlPrice` on every leg** — stop
  distance `|EntryFill − SlPrice|` is the sizing denominator; no engine-declared stop ⇒
  candidate rejected at the gate). Candidate never sizes; never sees account.
- **Python oracle (per subset evaluation):** chronological composition ONLY — free margin
  FM(t), sizing g(R_i, stop distance), open-risk accounting, R_max admission/rejection,
  cost charging, equity curve, segment-end censoring. It may not read prices to alter any
  entry/exit decision; admission (capacity rejection) is the single sanctioned interaction
  channel.

This preserves L-01 by construction (all look-ahead-capable logic stays in-engine) while
making the 2^N subset search feasible (one engine run per candidate, not per subset).
Codify as an amendment to `_pipeline-config.md` "Every experiment is price-primary".

**Consequence check (operator-visible):** sizing does not feed back into candidate
signals — a candidate's entry/exit timestamps are identical in every subset; only sizes,
admissions, and account path differ. This matches problem-statement §3 (B's *realized*
history differs via admission, not via signal change). If any future candidate's logic
depends on account state, it cannot use this carve-out.

## 4. Workstreams

### WS-1 — Candidate emission contract (cTrader side)
- Extend StrategyHost/ctrader-cli: batch mode over a candidate manifest (model × param grid ×
  instrument × domain), one emission dir per candidate under `data/strategy_runs/XENA-<univ>/`.
- Emission schema per §3 above; deterministic (seeded); fence-checked.
- `xen.estimand_validation` extended: per-candidate stream gate (schema, fence, causality,
  unit-position MTM reconciliation) — blocking before any candidate enters a universe.

### WS-2 — Portfolio oracle (`xen.xena.oracle`)
- Implements spec §3: chronological event-driven shared-capital sim; FM(t) compounding;
  `R_i = r·FM·w_i`; g() via stop distance; global R_max; **rejected signals logged as
  first-class events**; equal weights frozen.
- Deterministic: (bitmask, segment, seed) → bit-identical `{trade_ledger, equity_curve, F_point}`.
- Costs: spread + commission from the FTMO table charged in-sim (L-22 binding, not disclosure).
- Accounting: single canonical path; reconciliation invariant; `check_no_local_accounting`
  coverage extended (L-18).
- No additive shortcut anywhere, including screening (spec §3 invariant 1).

### WS-3 — Search stage (`xen.xena.search`)
- Bitmask representation; add/drop/swap/2-swap proposals (0.25/0.25/0.45/0.05).
- LAHC acceptance (L=150), stagnation kick (c=5, 2–4 bits, swap-biased).
- Objective: block-bootstrap P25 of F on **recorded ledger increments** (not re-sim) — the
  §7 approximation, discharged at deep validation.
- Paired evaluation: common segment + seed + common bootstrap block indices; sign-stability
  gate q=0.6 on marginal deltas.
- Append-only persisted evaluation cache (bitmask → F, boot dist, segment, seed, restart).
- Bootstrap primitives reuse INFR-004-hardened `xen.evaluation` (circular blocks, n-safe,
  seed battery, block-sensitivity sweep).

### WS-4 — Certification stage (`xen.xena.certify`)
- Plateau screen: all |S| single-drop neighbors + ~2|S| sampled swaps; score = min drop-
  neighbor F̂ ratio; **pre-registered threshold X, set before results**; keystone attribution
  logged (spec §9).
- Restarts (R=15): F-dispersion + Hamming-proximity diagnostics, mandatory in report.
- Ranking on disjoint contiguous purged folds (fresh account state per fold; median/worst-
  fold; PBO-style stat). CPCV excluded (Appendix A rationale — account-state path dependency).
- Deep validation of shortlist: full re-simulation, multi-segment multi-seed.
- Skepticism accounting: total evaluation count travels with every reported number (§10.4).

### WS-5 — Governance + pipeline integration
- Temporal mapping onto the fence (Operator Q1): search + selection folds inside ANALYSIS set;
  global 30% holdout untouched, as always.
- Registry semantics: registered object becomes a **XENA run** (universe manifest + frozen
  parameter registry + pre-registered thresholds), not a candidate family. Multiplicity ledger
  logs evaluation counts per run. Test-read ledger applies to the final-gate segment
  (Operator Q2).
- Skill updates: `_pipeline-config.md` (carve-out §3, XENA lane), `quant-designer`
  (XENA-run design template), `qa-compliance` (oracle determinism + fence + registry-freeze
  clauses), `data-analyst` (certification-report interrogation), documenter.
- Frozen legacy referee: stays byte-frozen for reproducibility; XENA does not touch it.

### WS-6 — Calibration & self-falsification (before any live use; L-12 clause)
- **Dogfood-negative:** universe of random-direction / permuted candidates (seed batteries,
  L-19 style). Requirement: certification stage rejects ~all portfolios; report the false-
  certification rate; final-gate pass rate under global null ≈ pre-registered α.
- **Synthetic-positive:** planted-edge candidates (known bps/trade, EXP-019-style) mixed in.
  Requirement: search finds them, certification retains them; MDE curve of the whole pipeline
  (what planted edge size survives end-to-end) — this is the framework's power statement.
- Diagnostics smoke tests: move-prob insensitivity, block-length insensitivity, L-range check
  (spec §11 "verify once, never tune").
- **Freeze:** parameter registry + thresholds hash-pinned after calibration; only then may a
  live universe be admitted. Tuning any XENA parameter after seeing a live universe's outcome
  = governance violation (same clause the old referee carried).

## 5. Operator decisions (LOCKED 2026-07-10; amended per external review 2026-07-10)

| # | Decision |
|---|---|
| Q1 | **(b, tightened)** TRAIN is **partitioned** into a SEARCH band and **disjoint** selection folds (contiguous, purged) — folds never overlap the search band (spec §10.1 invariant 6). Band boundaries are pre-registered quantities in the WS-6 doc; calibration mirrors the same partition (`SegmentLayout`). Final gate = TEST, once per run. |
| Q2 | **(b)** New portfolio-level gate ledger; cap 2 final gates per universe. **AMENDMENT (direction: LOOSER vs spec §A.5/invariant 10; running count for INFR-006: 1 LOOSER, 0 TIGHTER).** Rationale: per-universe cap replaces §A.5's one-shot-per-experiment because a universe is a long-lived object; but the second slot is **not a free retry** — it exists for a materially different certified subset or after new TEST data accrues. Enforced in code: `run_final_gate` refuses a subset identical to a FAILED ledger row absent an operator-signed `new_data_attestation` (recorded verbatim). WS-6 measures null gate FPR under this same protocol. |
| Q3 | XENA is the **default route** for all incoming ideas (operator presents an idea → XENA takes it). EXP/SPDR lanes are not retired but become operator-invoked-only for exploration/characterisation tasks. |
| Q4/Q5 | Deferred: first live universe + base objective F fixed at the WS-6 pre-registration doc, before freeze. |
| Exec | Approved: WS-2 → WS-1 → WS-3 → WS-4 → WS-6 → WS-5; toy/synthetic + TRAIN only. |

## 5b. Original open questions (resolved above)

| # | Question | Options | Recommendation |
|---|---|---|---|
| Q1 | Temporal mapping of XENA segments onto the TRAIN/TEST fence? | (a) search=TRAIN, selection folds=TRAIN-internal purged folds, final gate=TEST; (b) search+selection inside TRAIN, final gate=TEST; (c) reserve a new sub-split | **(b)** — TEST stays a pure once-per-run final gate; selection folds carved from TRAIN keep TEST unburned |
| Q2 | TEST-read accounting for a XENA final gate? | (a) one gate run = 1 counted read against every instrument-stratum it touches; (b) new portfolio-level ledger, cap N gates per universe | **(b)** — per-stratum caps don't fit a portfolio object; propose cap = 2 final gates per universe, ledgered |
| Q3 | Does XENA fully replace per-candidate lanes (SPDR, EXP referee reads) or run alongside? | (a) full replacement this chapter; (b) XENA lane added, legacy lanes retained for non-portfolio questions | **(b)** — characterisation/diagnostic experiments still need the EXP lane; XENA replaces *tradability adjudication* only |
| Q4 | First universe scope for WS-6 calibration + first live run? | needs operator direction (pitfalls ledger constrains candidates) | Calibration needs no live ideas; first live universe is a separate, later decision |
| Q5 | Base objective F (spec says orthogonal, pre-registered separately)? | e.g. log-wealth, expectancy/DD, MAR | Propose at pre-registration doc, before WS-6 freeze |

## 6. Execution order

```
WS-2 oracle → verify: unit tests + reconciliation invariant + determinism (bit-identical reruns)
          [DONE 2026-07-10 — xen/xena/oracle.py; 13 tests (test_xena_oracle.py)]
WS-1 emission contract → verify: estimand gate passes on a toy 3-candidate universe
          [DONE 2026-07-10 — xen/xena/ingest.py: universe_manifest.json spec + run-dir→CandidateStream
           adapter + blocking candidate gate (files/schema/fence/causality/stop/fill-consistency/
           oracle-smoke) + stale-gate refusal; 11 tests. XENA contract addition: every leg needs
           finite SlPrice (StopDistance = |EntryFill − SlPrice| is the sizing denominator).
           C#-side batch manifest runner deferred to first live universe (models don't exist yet).]
WS-3 search → verify: recovers planted optimum on synthetic toy landscape
          [DONE 2026-07-10 — xen/xena/search.py: LAHC(L=150) + stagnation kick, add/drop/swap/2swap,
           bootstrap-P25 objective on common per-universe bar grid + common block starts, sign-stability
           gate q=0.6, append-only EvalCache (dedup/revisits/neighbors/eval-count); 9 tests incl.
           planted-optimum recovery + determinism.]
WS-4 certify → verify: rejects noise-only toy universe
          [DONE 2026-07-10 — xen/xena/certify.py: plateau cliff-screen (min drop-ratio, keystone
           attribution, swap floor), dispersion + Hamming diagnostics, contiguous purged fold ranking
           (fresh account state, median/worst, PBO-like stat), certify_and_rank evidence package with
           §10.4 eval count; 9 tests incl. keystone detection + noise-only certifies nothing.]
Final gate (Appendix A) [DONE 2026-07-10 — xen/xena/final_gate.py: walk-forward on gate segment,
           bootstrap P25/median/P75, decay windows + rank-corr trend, gap diagnostic (field names
           carry units: search-P25 claim vs gate median), blocking portfolio-level gate ledger cap
           2/universe with same-failed-subset retry refusal (Q2 amendment), slot spent on pass OR
           fail; n_seeds=1 default (v1 oracle deterministic).]
WS-6 calibration → verify: FPR/power report; operator sign-off; hash-pin freeze
          [MACHINERY DONE 2026-07-10, review-hardened — xen/xena/calibration.py: `SegmentLayout`
           (disjoint search/ranking/gate bands, mirrors live Q1 partition), costed nulls
           (DEFAULT_COST_BPS=2.0; zero-cost = anti-conservative MDE), planted edges reported net-
           of-cost, gate FPR MEASURED via real `run_final_gate` path (not analytic), §11
           insensitivity sweeps (`insensitivity_sweep`: L / block / move-probs), hash-pin freeze
           utilities (`freeze_registry`/`verify_frozen_registry` — pinning happens AT sign-off).
           FULL-SCALE RUN PENDING — blocked on operator pre-registration (see §7). Permutation-null
           battery from real gated candidate streams: promised, activates when first live
           candidates exist.]
WS-5 governance docs/skills → verify: QA clause-trace on the updated skills
          [DONE 2026-07-10 — `docs/references/xena-lane.md` (full lane spec: default route,
           carve-out, frozen registry values + sha256, Q1 partition, Q2 ledger + operator-only
           attestation, §10.4 accounting, v1 limits); `_pipeline-config.md` (XENA lane section +
           xen.xena module-table row); `research-pipeline/SKILL.md` (default entry point + lane
           block + reference row); `qa-compliance/SKILL.md` (5 XENA clauses a–e incl. registry
           byte-match = REJECT on mismatch, agent-authored attestation = REJECT);
           `quant-designer/SKILL.md` (universe-manifest declarations, no per-candidate gates,
           never re-derive pinned thresholds); `data-analyst/SKILL.md` (evidence-package
           interrogation + dual-count disclosure). Clause-trace script verified every skill-cited
           constant/symbol against code (ALL CLAIMS VERIFIED); full suite 95 pass.]

FREEZE v1 (2026-07-10, SUPERSEDED same day): operator signed off X=0.70 / F_floor=0.1811 /
gate=0.0046; sha256 97578c09…b8b63. Archived: `results/v1-costed-selection/`.

## 9. Amendment log (post-freeze-v1, 2026-07-10)

**A-1 Gross-selection cost policy (operator-directed). Direction: LOOSER (selection);
running count: 2 LOOSER / 0 TIGHTER.** Commissions/spread excluded from search +
certification (`OracleConfig.charge_costs=False`); the final gate FORCES costs on
(L-22 binding leg, `run_final_gate` internal `replace(config, charge_costs=True)`).
Regime change invalidates v1 thresholds → full battery rerun (v2) + re-freeze required.

**A-2 DD feasibility gate leg (item 3, was registered in §7).** `dd_feasibility` — FTMO
limits (5% daily vs day-start equity, 10% total vs initial) binding at the gate;
`passed = P25 ≥ threshold AND dd.feasible`. Direction: TIGHTER (gate); count 2L/1T.

**A-3 v2 calibration generators (operator-invited).** Flat grid replaced by
regime-switching GBM (shared path per universe → cross-candidate correlated noise),
coin-flip-direction nulls (E[gross]=0 exact on any path — EXP-019 analytic-null pattern),
planted edge = exact favourable exit shift, vol-clustered entries + vol-scaled stops
(regime concentration + admission contention now in the null). Calibration apparatus,
not a frozen value; strengthens the credential the thresholds freeze against. Addresses
3 of the 4 flat-grid limitations (remaining: real-market microstructure → permutation-null
battery at first live universe, unchanged).

**A-4 Dual-cost final gate (operator-directed at v2 sign-off). Direction: LOOSER
(binding gate leg gross > net); count 3L/1T.** The gate runs the §A.4 protocol twice:
GROSS run = binding (`passed` = gross P25 ≥ threshold AND gross-path DD feasible) —
validates the pure optimizer + walk-forward selection machinery on the scale selection
ran on; NET run = informational (`net_informational` block: full costs + own DD read).
L-22 retained clause: any deployability claim MUST cite the net block; deployability
stays operator-gated. Consequences: gate threshold re-derived from GROSS null gate P25s;
v2 pin (which the operator signed off) superseded before ever being written — v3 battery
rerun (v2 raw lacked `top_subset`, so a gates-only regate was impossible; search is
seed-deterministic, full rerun reproduces selection exactly). v2 results archived at
`results/v2-net-binding-gate/`.

**Items 4–6 built (2026-07-10):** run design template
(`docs/references/xena-run-design-template.md`); XENA run ledger
(`docs/signal-registry/xena-runs.md`); `xena_money_per_unit` (USD-quote whitelist, raises
without a pinned quote→USD rate — L-21 seam guard). Suite: 103 pass.

**FREEZE v3 (2026-07-10, ACTIVE):** X=0.70 / F_floor=0.4302 / gate=0.0558 (GROSS null-P95
rule, A-4 regime). sha256
`537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6`. Battery v3 (A-4 dual
gate, 550 universes): null 2/300 certified, **0/300 end-to-end** (gross threshold killed
both) → FPR ≤1%@95%. End-to-end power: 20→16%, 30→70%, 40→94%, 60→100% (gross bps);
`net_p25_nonneg_among_passers` = 1.0 at every edge (all machinery-passers also
net-positive — informational deployability preview). v2 archived
`results/v2-net-binding-gate/`.

**Battery v2 results (superseded by v3; gross selection + v2 realistic-null generators,
550 universes, 2026-07-10):**

| Quantity | v2 value | v1 (costed-selection, flat-grid) |
|---|---|---|
| Plateau X | 0.70 | 0.70 |
| F_floor | **0.4302** | 0.1811 (gross F̂ scale — expected shift) |
| Gate pass threshold | **0.0277** | 0.0046 (null-P95 rule; harder null) |

Null (n=300, correlated-noise, coin-flip exact): certification 2/300 (0.67%) — the harder
null DOES occasionally certify — but **end-to-end false passes 0/300** (the net+DD gate
killed both) → FPR ≤ 1% @95%. Layered defense observed working, not assumed.

MDE curve (net of 2 bps, end-to-end pass rate): 8 bps 0% · 18 bps 18% · 28 bps **66%** ·
38 bps **96%** · 58 bps 100%. Softer than v1's cliff (v1: 28 bps 88%) — the realistic
null costs ~20 pp power at the knee; 18–38 bps is now a partial-power region. Purity
~0.39 (correlated noise admits more passengers). Insensitivity: block/move within ~15%,
no sign flips; L drift 0.42→0.32 (budget-coupled, as v1).
```

**Review-fix log (external review 2026-07-10, all applied same day):**
F1 segment-end censoring in the oracle (positions marked to last in-segment open; folds
P&L-disjoint at any holding horizon; `grid_increments` now raises on out-of-grid events instead
of clamping). F2 calibration segment partition + measured gate FPR. F3 plateau screen =
conjunction `F̂ ≥ F_floor AND min_drop_ratio ≥ X` (both pre-registered). F4 `kick()` now true
swap-pairs. F5 dual §10.4 counts (`evaluation_count` total oracle calls + `distinct_subsets`).
F6 gap-field labels, n_seeds conditional, decay rank-corr. §10.3 deep validation: **subsumed by
fold ranking** in v1 (full re-simulation per fold, fresh account state); the multi-seed leg is
vacuous while the oracle is deterministic — activates when the oracle gains stochastic elements.

**F7 (verification pass, 2026-07-10, PROCEED verdict):** grid/segment consistency — `run_restart`
and `plateau_screen` now restrict the bootstrap grid to the segment (mirroring `final_gate`), so
the search F̂ scale matches the gate scale that F_floor and the search-gap baseline freeze
against; applied to both call sites as one change (plateau ratio numerator/denominator stay in
lockstep) with tests asserting walk-F̂ == directly-computed segment-grid F̂ and plateau base ==
walk cache. Attestation field: free-form, ledgered verbatim; WS-5 names it operator-only.

Full python suite 2026-07-10 (post-review): 93 passed (45 XENA tests).

**Review-fix log 2 (compliance review vs originating docs, 2026-07-10):**
F01 pre-registration now code-enforced: `run_final_gate` + `certify_and_rank` take
`registry_path` (mandatory for live universes); hash-verify the pin and refuse
thresholds/SearchParams that differ; operator-only `threshold_override_attestation`
escape hatch; `registry_sha256` recorded in artifacts + gate ledger. F02 operator
decision: dual gross/net gate KEPT — rationale documented (separates model/signal-quality
characterisation from failure-by-cost; net strictly informational; verdict operator's).
F03 operator decision: exact-identity refusal KEPT (per-candidate qualifying rules are
against XENA principles); `max_jaccard_vs_prior_failed` now reported in the gate artifact,
informational only. F04 §14 ledger-resampling detector activated: `certify_and_rank`
emits `resim_divergence` rows (search-band bootstrap claim vs full re-sim fold scores;
labelled not-like-for-like). F05 registry-completeness: clear_win_sds=2.0, init_size=5,
gate decay windows=4, gate boot seed added to the lane doc's frozen table. F06 ΔF̂-vs-
ΔF_point clear-win reinterpretation + zero-spread exactness documented in code (no
behavior change — calibration credential preserved). F07 R_max fraction-of-FM(t)
interpretation documented in the oracle docstring (scale unspecified in
problem-statement §3; changing the reading = calibration-invalidating regime change).

Nothing in WS-1..4 touches live candidate ideas; all development on toy/synthetic data +
existing admitted instruments' TRAIN segments only.

## 7. WS-6 pre-registration (PROPOSED — operator sign-off required before the freeze run)

Reviewer-endorsed procedures; thresholds come OUT of the batteries (legitimate: L-23 forbids
tuning on *live* outcomes, not on synthetic-truth calibration):

| Item | Proposal |
|---|---|
| Base objective F (Q5) | **Log-wealth, keep.** Kelly-consistent; bootstrap-P25 wrapper supplies the tail penalty; richer composites introduce penalty weights (§11 forbids). FTMO-style DD limits handled as **feasibility check in oracle/gate** (constraint-as-gate), never inside F. |
| Plateau X + F_floor | From batteries: largest X retaining ≥90% of planted-battery certifications at target edge, sanity-checked vs null FPR; F_floor chosen the same way. Expected 0.4–0.7 but the battery decides. |
| Gate pass threshold | **Registered rule, not bare number**: `P25(log-wealth) ≥ max(0, null-battery gate P95)`, measured at freeze under the two-attempt Q2 protocol. |
| Battery scale | **300 null universes** (rule of three: 0/300 ⇒ FPR ≤ 1% @95%) + **planted sweep 5 edges × 50 universes** (10/20/30/40/60 bps gross vs 30 bps noise, reported net of 2 bps cost) → MDE curve. Per-universe settings proportional to live: live N, 10–15 restarts, budget where smoke shows best-F̂ flattened (~300–500 iters). Under-scaling restarts/budget vs live = anti-conservative FPR; match live on that axis. |
| Segment layout | `SegmentLayout.from_span` boundaries (default 50/30/20 search/ranking/gate) pre-registered here; calibration and live runs share the same partition shape. |

## 8. WS-6 battery results (2026-07-10 — full registered scale, RUN COMPLETE)

Runner: `ws6_battery.py`; raw: `results/ws6_battery_raw.jsonl` (550 lines);
summary: `results/ws6_battery_summary.json`. Protocol: permissive provisional screen,
raw stats recorded, thresholds derived post-pass by the §7 registered rules.

**Derived thresholds (await operator sign-off → `freeze_registry` hash-pin):**

| Quantity | Value | Rule |
|---|---|---|
| Plateau X | **0.70** | largest X (0.05 grid) retaining ≥90% of 30 bps-edge certifications |
| F_floor | **0.1811** | same retention rule at X=0.70 |
| Gate pass threshold | **0.0046** | max(0, P95 of 300 null-universe gate bootstrap P25s) |

**Null battery (n=300, costed 2 bps):** certification rate **0/300**; end-to-end false
pass **0/300** → rule-of-three **FPR ≤ 1% at 95% confidence**. The framework's headline
credential.

**MDE curve (5 planted among 24, 60 trades each, 30 bps noise; edges net of 2 bps cost):**

| Net edge (bps/trade) | Certified | End-to-end pass |
|---|---|---|
| 8 | 0% | 0% |
| 18 | 0% | 0% |
| 28 | **90%** | **88%** |
| 38 | 100% | 100% |
| 58 | 100% | 100% |

Sharp knee between 18 and 28 bps net/trade **at this configuration** (power scales with
trade count/noise; live MDE must be restated per live universe's trade density).
Top-portfolio planted fraction ≈ 0.5 across edges ≈ all 5 plants recovered + ~5 noise
passengers (24-candidate universe, ~10-strategy portfolios).

**§11 insensitivity (3 seeds/config, terminal best-F̂):** block 32/64/128 medians
0.247/0.245/0.255 (tight); move-prob variants 0.245/0.257/0.246 (tight); L 50/150/500
medians 0.263/0.245/0.233 — mild monotone drift ≈12%, consistent with convergence-speed
(smaller L converges faster within budget 400), no sign flips, no order-of-magnitude
sensitivity. Registry annotation "insensitivity verified" supported; L drift noted as
budget-coupled, not terminal-quality.

Wall: mean 39.8 s/universe, 550 universes, 8 workers (~45 min wall).
