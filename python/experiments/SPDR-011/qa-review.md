## QA run 1 — 2026-07-22T22:30:46Z — mode: subagent — HEAD 495c83ae34e76cda93f35e888e2d4039fafefbdf

Verdict: REVISE

Reviewed git state: dirty. Modified: `docs/experiments-docs/INDEX.md`, checkpoint-016 `design.md`, `docs/knowledge-base/data-architecture.md`, `docs/knowledge-base/memory/chapter05-entry-gate.md`, `docs/references/{architecture,chapter-05-governance,dataset-reference}.md`, `docs/signal-registry/{candidate-families/cf-volconv-001,multiplicity-registry,test-read-ledger}.md`, `python/experiments/INDEX.md`, `python/tests/test_chapter05_preflight.py`. Untracked: SPDR-011 `design.md`, `design_derivations/census.py`, `results/census.json`, and `python/tests/test_spdr011_census.py`. The ignored `results/census_event_keys.parquet` was also reviewed. No TEST/holdout artifact or outcome price was opened.

### Design-fidelity trace

| Design clause (§ref) | Code / artifact | Verdict | Notes |
|---|---|---|---|
| TRAIN fence; TEST/holdout zero reads (§3.1, §4, §13) | `design_derivations/census.py:502-519`; `results/census.json:5-15` | MATCHES | `fenced_bar_query(..., band="TRAIN")`; maximum query end is the pinned TRAIN end. |
| Daily `rv20`, prior-only percentile, 60-return warm-up, terciles (§5.1) | `design_derivations/census.py:249-320` | MATCHES | Current `rv20` is excluded from the prior ≤252 history; state is assigned to the next UTC day. |
| `drift20`, `beta60`, five-name rank and lexical tie-break (§5.1–5.2) | `design_derivations/census.py:278-320` | MATCHES | BTC beta is fixed at 1; incomplete cross-sections receive no executable rank. |
| Completed 4h strict range break; equality is no event (§5.2) | `design_derivations/census.py:131-154` | MATCHES | Strict `>` / `<`; event timestamp is the completed boundary. |
| Entry timestamp at boundary; fixed exit timestamp +4h (§4, §5.2) | `design_derivations/census.py:147-150,333-370` | MATCHES FOR CENSUS | Census emits timestamps only. Fill resolution is not implemented. |
| One row per located event; no post-event completeness filter (§6) | `design_derivations/census.py:333-373,502-585` | MATCHES | 3,606 unique keys; no outcome-availability filter is applied. |
| Outcome-isolated census schema (§3.1, §6) | `design_derivations/census.py:41-80,112-123`; event-key parquet | MATCHES | Parquet contains 24 causal/key columns and no price, return, path, cost or P&L field. |
| Counts, clustering and date-based prospective MDE (§3.2–3.3, §9–10) | `design_derivations/census.py:376-428`; `results/census.json:128-390` | MATCHES | 1,390 DESIGN + 2,216 CONFIRM; counts and stated MDEs reconcile from emitted keys. Parametric curves are explicitly assumed-sigma planning approximations; final inference is date-block based. |
| Signed-flow feature (§5.3, L5) | no outcome implementation | MISSING — DATA-BLOCKED | Correctly withheld because the five full signed TRAIN histories and required attestation are absent. Not a census defect; execution remains prohibited. |
| Outcome emission, availability flags, 1h/2h/4h outcomes, fees/funding/allowance (§6, §11, §13) | no `code/` runner | MISSING — IMPLEMENTATION NOT YET AUTHORED | Expected at this stopped stage, but it prevents pre-execution approval. Fresh QA must review the eventual runner. |
| Matched timing, unconditional breakout, direction derangement, future destroy (§8) | no outcome implementation | MISSING — IMPLEMENTATION NOT YET AUTHORED | Design intent exists; zero-fixed-point regeneration and ≥2,000-seed behavior cannot yet be verified. |
| Bootstrap, concentration, ordered L1–L5 reveal and sealed CONFIRM (§7, §9, §13) | no outcome/analysis implementation | MISSING — IMPLEMENTATION NOT YET AUTHORED | Must be traced after implementation; CONFIRM outcomes remain unopened. |
| Located-event missing-path policy (§5.1, §6, amendment A3) | family contract `cf-volconv-001.md:75-77`; governing brief `intraday-way-forward-plan.md:175-179` | DEVIATES | Experiment retains located rows with null outcomes; registered sources require excluding unavailable entry/full-path episodes before outcome access. A3 records direction but not operator approval or an aligned family/checkpoint amendment. |

### Golden-trace diff

| Trace | Design expectation | Implemented logic | Verdict |
|---|---|---|---|
| GT-1 LONG | strict upper break; long; 107→104; −280.374 bps | Census long/strict-break semantics covered; no fill/outcome runner | MISSING — implementation |
| GT-2 SHORT | strict lower break; short; 88→84; +454.545 bps | Census short/strict-break semantics covered; no fill/outcome runner | MISSING — implementation |
| GT-3 EQUALITY | close equal to prior high; no event | Strict comparators in locator; no dedicated equality fixture | MATCHES logic; test coverage incomplete |
| Three no-price membership anchors | BTC `2022-09-17T16:00Z` long; DOGE `2022-10-27T04:00Z` long; ETH `2022-09-25T20:00Z` short | IDs/timestamps/directions match `census.json` and event-key parquet | MATCHES (prices not inspected) |

### Governance & boundary

- PASS — Family `CF-VOLCONV-001` is registered; route is the operator-approved TRAIN-only `SPDR-011 → EXP-099` exception; XENA is out of scope.
- PASS — Artifact SHA-256 values match design §3.1: census JSON `d2dcb9…6fa5`, event keys `d1299a…fdfd`, census code `8c1a57…dca5`.
- PASS — Event-key checks: 3,606 rows, zero duplicate IDs, zero `known_ts > trigger_ts`, valid ranks/TOP2 derivation, latest entry `2023-12-17T08:00Z`.
- PASS — Focused tests: `8 passed`; `check_no_local_accounting("python/experiments/SPDR-011/code")` reports no banned definitions. There is no Python strategy backtest or `BacktestNode` runner yet.
- PASS — Mandatory mechanism, object identity, four control proofs, bands, power, golden traces, hard/informative split, missing-spread disclosure, and amendment-direction ledger are present. No screen-to-money conversion pin is applicable.
- PASS — Spread is `UNAVAILABLE_NOT_CHARGED`, `spread_rt_bps: null`, and `PARTIAL_FEES_FUNDING_ONLY`; prohibited proxies and deployability claims are excluded.
- PASS — Derangement is required for every permutation destroy; fixed exit makes exit-matched-null selection inapplicable; thirds/concentration and shrunk-effect MDE eligibility are predeclared.
- REVISE — The hard future-destroy is described as a control but the mandatory standalone `TRIPWIRE:` declaration does not state a pre-measurement expected collapse criterion. “Collapses” alone is not an executable integrity decision rule.
- BLOCKED — Signed TRAIN data is not materialised for all five symbols. The INFR-017 artifact validates only one day/three symbols and provides no full ingest. This is an honest hard data blocker, not evidence against the design or census.
- NOT ASSESSED — Outcome implementation, deterministic emission, fill prices, cost arithmetic, CONFIRM sealing, derangement generation, sentinel detection, and golden outcome values do not exist and therefore cannot be approved.

### Issues

1. **REVISE — registered-contract deviation.** Design §5.1/§6/A3 (`design.md:144-146,180-182,348-349`) retains located events with null outcomes, while the registered family and governing brief exclude unavailable entry/full-path episodes before outcome access (`cf-volconv-001.md:75-77`; `intraday-way-forward-plan.md:175-179`). **Required change:** `quant-designer` must either restore the registered exclusion or obtain and record operator approval, then align the governing artifacts before implementation.
2. **REVISE — incomplete hard-tripwire declaration.** Design §8/§13 (`design.md:236-246,319-325`) gives a valid deranged future destroy and sentinel, but omits the mandatory standalone tripwire block and a pre-measurement collapse criterion. **Required change:** `quant-designer` must add `TRIPWIRE:` with the metric, derived expected-collapse decision rule, vacuity proof, sentinel acceptance rule, and `derangement=YES`; it must remain an integrity check, not a value gate.
3. **BLOCKED, not a defect — signed data.** Design §3.4 correctly records the missing five-symbol signed TRAIN lane. Restore the existing signed source, bulk-ingest it, and produce the stated hash/row/timestamp/split/fence attestation before any outcome implementation or run.
4. **MISSING, expected at this stage — outcome implementation.** No outcome runner exists, so all outcome, cost, control, emission, and golden-value clauses are unreviewed. After issues 1–3 are resolved and the runner is authored, run fresh-context QA again. QA approval never authorises execution by itself.

## QA run 2 — 2026-07-22T22:35:30Z — mode: subagent — HEAD 495c83ae34e76cda93f35e888e2d4039fafefbdf

Verdict: REVISE

Reviewed git state: dirty. Modified: `docs/experiments-docs/INDEX.md`, checkpoint-016
`design.md`, `docs/knowledge-base/{data-architecture,memory/chapter05-entry-gate}.md`,
`docs/references/{architecture,chapter-05-governance,dataset-reference}.md`,
`docs/signal-registry/{candidate-families/cf-volconv-001,multiplicity-registry,test-read-ledger}.md`,
`python/experiments/INDEX.md`, and `python/tests/test_chapter05_preflight.py`. Untracked:
SPDR-011 artifacts and `python/tests/test_spdr011_census.py`. The ignored
`results/census_event_keys.parquet` was reviewed. No outcome data, historical TEST, or holdout
artifact was opened.

### Design-fidelity trace

| Design clause (§ref) | Code / artifact | Verdict | Notes |
|---|---|---|---|
| TRAIN fence; TEST/holdout zero reads (§3.1, §4, §13) | `design_derivations/census.py:502-519`; `results/census.json:5-15` | MATCHES | Query is fenced to `TRAIN`; result declares TEST/holdout not queried. |
| Prior-only daily state, strict completed break, timestamp rank (§5.1–5.2) | `design_derivations/census.py:131-154,249-320` | MATCHES | State uses prior observations; range is from the confirmed prior day; strict equality produces no event. |
| One row per located event; no future-completeness eligibility (§5.1, §6, A3) | `design_derivations/census.py:333-373,502-585`; family `cf-volconv-001.md:75-79`; governing brief `intraday-way-forward-plan.md:175-181` | MATCHES | Prior QA issue 1 is resolved: all governing texts retain located rows and exclude unavailable rows only from outcome estimands/contrasts. |
| Outcome-isolated census schema (§3.1, §6) | event-key parquet; `design_derivations/census.py:41-80,112-123` | MATCHES | 3,606 unique keys, 24 causal/key columns, zero causal timestamp breaches, and no price/path/return/cost/P&L fields. |
| Counts and count-only power (§3.2–3.3, §9–10) | `results/census.json`; event-key parquet | MATCHES | 1,390 DESIGN + 2,216 CONFIRM; pinned hashes match. MDE is explicitly an assumed-sigma planning calculation using unique dates. |
| Located-event availability output (§6) | no outcome implementation | MISSING — IMPLEMENTATION | Null outcomes/reasons and outcome-estimand exclusion cannot be traced until the runner exists. |
| Signed-flow feature and source readiness (§3.4, §5.3, L5) | `design_derivations/census.py:431-459`; current filesystem; INFR-017 manifest | DEVIATES | Raw source is now readable for all five symbols through the staging symlink, but no `data/catalog_sigbar/train` ingest or full attestation exists. The design and frozen census metadata still describe the symlink/source as unavailable. |
| Four controls and hard future destroy (§8) | design only; no runner | MATCHES DESIGN / MISSING IMPLEMENTATION | All design proof fields exist. Zero-fixed-point generation and control emissions remain unreviewable. |
| Standalone hard tripwire (§8) | `design.md:249-257` | MATCHES DESIGN | Prior QA issue 2 is resolved: named metric, pre-outcome 2,000-derangement 99% envelope, invalidation rule, non-vacuity proof, sentinel acceptance, and `derangement=YES` are explicit. |
| Fees/funding/allowance and missing-spread boundary (§11) | design only; no runner | MATCHES DESIGN / MISSING IMPLEMENTATION | Required disclosure is exact; prohibited spread proxies are excluded. Cost arithmetic cannot yet be traced. |
| Golden traces (§12) | census locator; no outcome runner | PARTIAL | Strict long/short/equality locator semantics match; fill and return values remain unimplemented. |

### Golden-trace diff

| Trace | Design expectation | Implemented logic | Verdict |
|---|---|---|---|
| GT-1 LONG | strict upper break; long; 107→104; −280.374 bps | Census implements strict long locator; no fill/outcome code | PARTIAL — locator matches; outcome missing |
| GT-2 SHORT | strict lower break; short; 88→84; +454.545 bps | Census implements strict short locator; no fill/outcome code | PARTIAL — locator matches; outcome missing |
| GT-3 EQUALITY | equal prior high; no event | Locator uses strict `>` / `<` | MATCHES |
| Three no-price anchors | frozen IDs/timestamps/directions | Present in event-key artifact | MATCHES; prices not inspected |

### Governance & boundary

- PASS — Fresh subagent context; append-only rerun; reviewed HEAD and dirty state recorded.
- PASS — Focused census tests: `8 passed`. Pinned SHA-256 values for census JSON, event keys,
  and census code all match design §3.1.
- PASS — Census artifact is outcome-isolated: 3,606 unique events, no causal timestamp breach,
  and no forbidden outcome field. No TEST, holdout, or outcome data was opened in this review.
- PASS — `check_no_local_accounting("python/experiments/SPDR-011/code")` returns `ok: true`;
  no strategy/backtest runner exists.
- PASS — Prior missing-path-policy inconsistency is corrected across design, family, and governing brief.
- PASS — Prior missing standalone-tripwire finding is corrected in the design. Its implementation
  must still be reviewed after code exists.
- PASS — Mandatory mechanism, object identity, control proofs, bands, power, golden traces,
  hard/informative split, amendment ledger, and missing-spread declaration are present. No
  screen-effect conversion pin is applicable.
- REVISE — Signed-data status is stale. `/Volumes/SSID/Xen/data/bars` is mounted now and each of
  `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `DOGEUSDT`, and `XRPUSDT` has a readable parquet. The actual
  remaining data block is bulk TRAIN ingest plus fence/schema/hash attestation.
- BLOCKED — Outcome execution still lacks the signed TRAIN catalog/attestation and any runner.
  Design/census acceptance cannot be treated as execution approval.

### Issues

1. **REVISE — stale signed-source status.** Design §3.4 (`design.md:89-103`) and frozen census
   metadata (`results/census.json:415-430`) say the staging symlink is dangling/unmounted and the
   source bytes are unreadable. At review time the symlink resolves to
   `/Volumes/SSID/Xen/data/bars`, and all five required raw parquets exist. **Required change:**
   `quant-designer` must describe the current boundary accurately: raw signed source is restored
   and readable; full TRAIN custom-catalog ingest and its attestation remain absent. Regenerate or
   amend the outcome-free status artifact and update its pinned hash without opening outcomes,
   TEST, or holdout.
2. **REVISE — source/catalog readiness conflated.** `_signed_data_status`
   (`design_derivations/census.py:431-459`) sets `full_train_materialised` true when any configured
   raw staging path exists for every symbol, even if `data/catalog_sigbar/train` is absent. A rerun
   now would therefore overstate readiness. **Required change:** `experiment-developer` must report
   raw-source readability and TRAIN-catalog materialisation as separate fields; only the verified
   catalog ingest may clear execution readiness.
3. **BLOCKED, expected — no outcome implementation.** No runner exists, so signed-flow joining,
   null availability reasons, fills, costs, controls, sealed CONFIRM, golden outcomes, and tripwire
   execution remain unreviewed. After the data-status correction, signed TRAIN ingest/attestation,
   and implementation, run fresh-context QA again. QA approval never launches execution.

**Package disposition:** the event census and the two corrected design clauses are acceptable.
The package as a whole remains `REVISE` only because its signed-data availability statement is now
factually stale. Execution remains blocked on bulk signed TRAIN ingest/attestation, implementation,
fresh QA, and separate operator authorisation.

## QA run 3 — 2026-07-22T23:00:10Z — mode: subagent — HEAD 495c83ae34e76cda93f35e888e2d4039fafefbdf

Verdict: REVISE

Reviewed git state: dirty. Modified: `docs/experiments-docs/INDEX.md`, checkpoint-016
`design.md`, `docs/knowledge-base/{data-architecture,memory/chapter05-entry-gate}.md`,
`docs/references/{architecture,chapter-05-governance,dataset-reference}.md`,
`docs/signal-registry/{candidate-families/cf-volconv-001,multiplicity-registry,test-read-ledger}.md`,
`python/experiments/INDEX.md`, and `python/tests/test_chapter05_preflight.py`. Untracked:
SPDR-011 design, implementation, census/attestation artifacts, QA review, and focused tests.
No run emission, real event outcome, CONFIRM artifact, TEST, holdout, or unlock was opened or
created. Checks were synthetic or read-only catalog/attestation checks.

### Design-fidelity trace

| Design clause (§ref) | Code / artifact | Verdict | Notes |
|---|---|---|---|
| Frozen TRAIN census, 3,606 IDs and causal provenance (§3.1, §13.1/8) | `code/run_spdr011.py:77-148`; census artifacts | MATCHES | All four pinned files match; 3,606 unique IDs and `known_ts <= trigger_ts` are asserted before outcomes. |
| Signed TRAIN mapping, fence and attestation (§3.4, §5.3, A4) | `signed_ingest.py:388-504`; signed attestation; catalog | MATCHES PREPARATION / DEVIATES EXECUTION | Independent audit reproduced 3,731,908 rows, 90 files, five complete symbol audits and tree hash `d4b7bb…d2b9`. The run gate pins the attestation file but does not recompute that tree hash. |
| Located population retained; missing marks become null (§5.1, §6, A3) | `code/runner_contract.py:50-122`; `code/layers.py:22-79` | MATCHES | Left joins retain every event; availability flags/reasons are explicit; only complete 4h rows enter outcome estimands. |
| Real-open 1h/2h/4h outcomes and fixed episode (§4, §6) | `code/runner_contract.py:38-122`; `code/spdr011_strategy.py:20-79,108-124` | MATCHES FORM / RECONCILIATION MISSING | Mark arithmetic and schedule timing match, but no invariant ties scheduled event actions or actual fills back to artifact event rows. |
| Signed-flow identity, alignment and prior same-slot percentile (§5.3) | `code/run_spdr011.py:321-392`; `code/runner_contract.py:178-226` | MATCHES | Completed signed slots, causal known timestamp, exact buy/sell partition, direction alignment and frozen upper tercile are implemented. |
| Fees, funding and allowances; spread unavailable (§11, A1) | `code/runner_contract.py:125-175` | MATCHES | Shared `bybit_round_trip_cost_bps`, taker fees, `(entry,exit]` funding stamps, 0/2/5 allowances, and `spread_bps=None`; no spread proxy enters cost. |
| Matched timing and L4 beta/occupancy nulls (§8.1, A4/A5) | `code/run_spdr011.py:228-318,507-545`; `code/controls.py:153-358,488-544` | MATCHES | Signal windows/live dates are excluded; exact cells, nearest-five beta, no reuse, exact occupancy, realised TOP2 exclusion, fixed seeds and null reasons match. |
| Direction and future-path derangements (§8) | `code/controls.py:18-150,361-485` | MATCHES CONSTRUCTION | Mappings are within frozen strata and reject every fixed point; 2,000-seed reports retain all effects and changed-sign fractions. |
| Hard future-destroy tripwire (§8, §13 HARD) | `code/run_spdr011.py:404,492-500,502-506`; `code/controls.py:78-111,387-485` | DEVIATES | The synthetic +50-bps sentinel is enforced, but the real future-destroy distribution is only reported. No frozen rule decides whether a material real edge survived destruction, and artifact assembly proceeds regardless. |
| Date-block inference and informative bands (§9-10) | `code/controls.py:547-621`; `code/layers.py` | MATCHES SUPPORT CODE | Whole-date resampling, five fixed seeds, 1/3/7-day parameter and three statistics exist; all labels remain informative and no auto-value verdict is emitted. |
| Nautilus topology and emission (§13, L-29/L-31) | `code/run_spdr011.py:163-215,395-486`; `code/spdr011_strategy.py` | MATCHES TOPOLOGY | One `BacktestNode` in one process, five strategies/instruments, `dispose_on_completion=False`; INFR-014 S1 permits multi-instrument single-node. No second node is constructed. |
| Logical DESIGN/CONFIRM seal (§13, A4) | `code/bundle.py:25-113`; `code/run_spdr011.py:546-559` | MATCHES | Two immutable members, manifest hashes, default DESIGN-only read, hash-chained operator unlock and exact supplied-rule-hash check. No unlock currently exists. |
| Operator execution authority (§15) | `code/run_spdr011.py:1-8,395-403`; current filesystem | MATCHES | No CLI; non-empty explicit authority is required. QA does not supply authority and does not execute the function. |

### Golden-trace diff

| Trace | Design expectation | Implemented logic | Verdict |
|---|---|---|---|
| GT-1 LONG | 107 at entry, 104 at +4h, −280.374 bps | exact open-to-open formula in `runner_contract.py:70-111`; synthetic test reproduces −280.3738 | MATCHES |
| GT-2 SHORT | 88 at entry, 84 at +4h, +454.545 bps | direction multiplier and exact +4h open; synthetic test reproduces +454.5455 | MATCHES |
| GT-3 EQUALITY | close equal prior high produces no event | strict locator comparators retained in frozen census code and tests | MATCHES |
| Shared exit/new-entry boundary | new target supersedes flat; next-open market action | EXIT sorts before ENTRY and grouped last target wins (`spdr011_strategy.py:68-79`) | MATCHES |

### Governance & boundary

- PASS — Fresh subagent context; append-only run; reviewed HEAD and dirty state recorded.
- PASS — Prior QA issues are resolved: missing-path policy is aligned; standalone tripwire exists;
  raw-source versus verified-catalog readiness is separated; full signed TRAIN catalog and runner exist.
- PASS — `27 passed` across `test_spdr011_{census,signed_ingest,runner}.py`; `git diff --check`
  clean; `check_no_local_accounting(...)` returned `ok: true`.
- PASS — Census JSON `547495…b9db`, keys `d1299a…fdfd`, derivation `9fae17…bdc`, and signed
  attestation `bdfe83…0d29` match §3.1 and runner constants.
- PASS — Read-only signed-catalog audit: tree hash equals attestation (`d4b7bb…d2b9`), 90 files,
  3,731,908 total rows, all five row/time/config/version/split/delta audits complete with zero violations.
- PASS — A1–A5 code consequences are present. Direction count is 1 looser / 1 tighter / 3
  neutral; no one-directional amendment streak exists; no global-null qualifier gate applies.
- PASS — Missing spread is represented as null, never zero. Cost scope is partial fees/funding only;
  raw `SpreadBps` is carried only as a quarantined `SignedBar` feature and never enters costs.
- PASS — No XENA route, historical TEST read, holdout path, CONFIRM read, outcome artifact, unlock,
  value auto-verdict, or deployment/tradability claim was found.
- REVISE — Exact signed-catalog bytes are not re-verified by the execution preflight.
- REVISE — The hard future-destroy has no real-outcome survival decision rule or enforcement.
- REVISE — The validated Nautilus emission and the separately mark-assembled primary artifact are
  not reconciled event by event, so the engine can disagree without blocking the artifact.

### Issues

1. **REVISE — signed-catalog hash pin is not enforced at execution.** Design §3.4/§13 HARD
   pins catalog-tree SHA-256 `d4b7bb…d2b9`, but `assert_preexecution_inputs`
   (`code/run_spdr011.py:134-148`) verifies only the attestation-file hash and that the catalog
   directory exists. Catalog bytes can change after attestation without stopping the run.
   **Required change:** `experiment-developer` must recompute the deterministic catalog-tree hash
   at preflight and require exact equality with the attested hash (plus the frozen expected hash),
   before constructing schedules or opening prices. Add a synthetic mutation/failure test.

2. **REVISE — hard future-destroy governs only the synthetic sentinel.** Design §8/§13 declares
   future-destroy a hard integrity gate. `run_train_emission` enforces sentinel recovery/envelope
   (`code/run_spdr011.py:492-500`), then merely stores the real future-path distribution from
   `conversion_control_batteries` (`:502-506,546-558`). There is no predeclared rule for “real edge
   survives destruction” and no blocking result; `controls.py:457-485` emits only descriptive
   statistics. **Required change:** `quant-designer` must freeze an executable, effect-aware
   real-outcome collapse/non-survival rule that does not falsely reject a raw no-edge result;
   `experiment-developer` must emit and enforce that hard integrity result before any value layer is
   readable. Keep the synthetic sentinel as the separate bite/non-vacuity proof.

3. **REVISE — primary artifact is not reconciled to engine execution.** The per-symbol Nautilus
   runs pass `validate_run` (`code/run_spdr011.py:410-486`), but the verdict-bearing event artifact
   is then independently assembled from census rows plus queried marks
   (`code/run_spdr011.py:488-491`; `runner_contract.py:50-122`). No event ID is attached to orders,
   and no check reconciles expected entry/exit actions, actual fill timestamps/sides, or rejected
   orders to the artifact. A broken engine schedule can therefore coexist with unchanged theoretical
   outcomes, violating §2 object identity and §13 estimand reconciliation. **Required change:**
   `experiment-developer` must add an event-level schedule/fill reconciliation artifact and make any
   mismatch block bundle creation; alternatively, `quant-designer` must explicitly demote this to a
   non-trading diagnostic and remove the capital-commitment/engine-execution claim.

**Execution disposition:** not ready. The signed data itself is verified and the prior QA defects are
fixed, but the three integrity seams above require revision and another fresh-context QA. Even a later
APPROVE would only make the package ready for the operator's separate execution decision; no execution
authority exists now.

## QA run 4 — 2026-07-22T23:18:02Z — mode: subagent — HEAD 495c83ae34e76cda93f35e888e2d4039fafefbdf

Verdict: APPROVE

Reviewed git state: dirty. Modified (all pre-existing, unrelated docs/tests): `docs/experiments-docs/INDEX.md`,
checkpoint-016 `design.md`, `docs/knowledge-base/{data-architecture,memory/chapter05-entry-gate}.md`,
`docs/references/{architecture,chapter-05-governance,dataset-reference}.md`,
`docs/signal-registry/{candidate-families/cf-volconv-001,multiplicity-registry,test-read-ledger}.md`,
`python/experiments/INDEX.md`, `python/tests/test_chapter05_preflight.py`. Untracked: SPDR-011 design,
implementation, census/attestation artifacts, QA review, and focused tests. No `run_train_emission` call,
no real outcome / TEST / holdout / CONFIRM outcome read, and no CONFIRM unlock were performed by this
review. Signed-catalog bytes were hashed (no outcome values read); attestation and census JSON read as
metadata only.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| Frozen census, 3,606 IDs, causal provenance ≤ trigger (§3.1, §13.1/8) | `run_spdr011.py:150-179,136-147` | MATCHES | Four pinned SHAs asserted; 3,606 unique IDs; `state_known_ts`/`range_known_ts <= trigger_ts` enforced before outcomes. |
| Live signed-catalog re-hash immediately before engine read (§3.4, §13.9, A6) | `run_spdr011.py:111-133,441-444,549-552` | MATCHES | `catalog_tree_sha256` reproduces frozen `d4b7bb…d2b9`; `assert_signed_catalog_tree` requires equality with BOTH attested and frozen; enforced pre-engine and again pre-signed-flow read. **Closes Run-3 issue 1.** |
| Located population retained; missing marks → null reason (§5.1, §6, A3) | `runner_contract.py:50-122` | MATCHES | Left joins keep every event; `outcome_unavailable_reason`; only 4h-complete rows enter estimands. |
| Real-open 1h/2h/4h outcomes, fixed 4h episode (§4, §6) | `runner_contract.py:38-122`; `spdr011_strategy.py:120-142` | MATCHES | Open-to-open at `entry_ts`/`entry_ts+h`; direction-signed; entry-open guard. |
| Event→fill reconciliation blocks bundle on mismatch (§2, §13.10, A6) | `runner_contract.py:239-408`; `run_spdr011.py:531-547` | MATCHES | One ENTRY+one EXIT per event, one order/FILLED/one fill, side, instrument, `ts_last==decision_ts`, price==first-minute `RealOpen` within 1e-9; unavailable event cannot masquerade as a complete pair; raises before `write_bundle`. **Closes Run-3 issue 3.** |
| Signed-flow identity, alignment, prior same-slot percentile (§5.3) | `run_spdr011.py:352-423`; `runner_contract.py:178-226` | MATCHES | Completed slots, causal `signed_known_ts <= trigger_ts`, exact volume identity, upper-tercile flag; only Buy/Sell/Volume read from `SignedBar`. |
| Fees/funding/allowance; spread null/unavailable (§11, A1) | `runner_contract.py:140-175` | MATCHES | Shared `bybit_round_trip_cost_bps`, `spread_bps=None`, `(entry,exit]` funding stamps, 0/2/5 allowances; no spread proxy. |
| Synthetic sentinel frozen pre-outcome (§8.1, §13 TRIPWIRE) | `controls.py:78-111`; `run_spdr011.py:435,555-563` | MATCHES | 2,000-seed 99% envelope on census keys + synthetic labels calibrated before engine; raw 50±0.5 and audit-seed inside envelope enforced. |
| Real-edge future-destroy survival rule (§8 §275-284, A6) | `controls.py:607-651`; `run_spdr011.py:571-579` | MATCHES | Applicable only if raw L3 ≥+15 and all five date-block CI lowers >0; then requires raw>p99, empirical p≤0.01, |destroyed median|≤25% |raw|; else NOT_APPLICABLE; INVALID raises before `write_bundle`. Integrity (leak-survival) only — a WASH/null yields NOT_APPLICABLE, never a forced verdict. **Closes Run-3 issue 2.** |
| Direction/future-path derangements (§8, L-28) | `controls.py:21-49,137-150,448-455` | MATCHES | `make_derangement` within `(symbol,band,calendar_third)`; zero fixed points asserted twice; ≥2 per stratum required. |
| Matched timing & L4 beta/occupancy nulls (§8.1, A4/A5) | `run_spdr011.py:259-349,580-618`; `controls.py:153-358` | MATCHES | Signal-window overlap excluded, live date excluded, exact cell + nearest-5 beta, no reuse, realised TOP2 pair excluded, fixed seeds, null reasons. |
| Date-block inference & informative bands (§9-10) | `controls.py:547-604,679-728`; `layers.py` | MATCHES | Whole-date resampling, five seeds, 1/3/7-day blocks, three statistics; no `pass`/`verdict` field anywhere. |
| One BacktestNode / process; native engine (§13, L-31) | `run_spdr011.py:446-479` | MATCHES | One node, one config, five strategies/instruments, `dispose_on_completion=False`; no second node; no Python vectorized backtest. |
| Logical DESIGN/CONFIRM seal; CONFIRM unread (§13, §386-392, A4) | `bundle.py:25-113`; `run_spdr011.py:564-634` | MATCHES | Two immutable members; only DESIGN band feeds every control/CI; confirm.parquet sealed behind hash-chained operator unlock; no unlock present. |
| Estimand-validation gate (§13 HARD) | `run_spdr011.py:496-525` | MATCHES | Shared `validate_run` integrity harness; `blocking_pass` required before artifact assembly. Not a value gate. |
| Operator execution authority (§15) | `run_spdr011.py:426-433` | MATCHES | No CLI / `__main__`; non-empty authority required; QA supplied none and did not execute. |

### Golden-trace diff

| Trace | Design expectation (from §12) | Implemented logic | Verdict |
|---|---|---|---|
| GT-1 LONG | 107→104, −280.374 bps | `runner_contract.py:70-111`; test reproduces −280.3738 | MATCHES |
| GT-2 SHORT | 88→84, +454.545 bps | direction multiplier + exact +4h open; test reproduces +454.5455 | MATCHES |
| GT-3 EQUALITY | equal prior high → no event | strict `>`/`<` comparators in frozen census locator | MATCHES |
| Shared exit/new-entry boundary | flat then next-open re-entry | EXIT sorts before ENTRY at shared `decision_ts` (`spdr011_strategy.py:75-83`) | MATCHES |
| Three no-price anchors | frozen IDs/timestamps/directions | present in event-key artifact; prices not inspected | MATCHES |

### Governance & boundary

- PASS — Fresh subagent context; append-only; HEAD and dirty state recorded.
- PASS — `41 passed` across `test_spdr011_{census,signed_ingest,runner}.py`; `git diff --check` clean;
  `check_no_local_accounting("python/experiments/SPDR-011/code")` → `{ok: true}`; no `__main__`/argv/argparse
  in experiment code.
- PASS — Re-verified frozen hashes: census.json `5474955a…b2b9db`, keys `d1299a08…c7dfd`, census.py
  `9fae1731…802bdc`, signed attestation `bdfe839c…b180d29`, all match §3.1 and runner constants.
- PASS — Read-only signed-catalog audit: live tree hash `d4b7bbed…f7d2b9` == frozen == attestation
  `catalog_tree_sha256`; 90 files; attestation `status=VERIFIED`, symbols correct, fence TRAIN,
  `test_rows_read=0`, `holdout_rows_read=0`. Catalog left unmodified.
- PASS — Three A6 fixes each close their Run-3 gap and each is an allowed HARD class (provenance,
  future-destroy leak-survival, estimand reconciliation). None introduces a value/quality/significance gate:
  the survival rule yields NOT_APPLICABLE on a null and only INVALIDates a claimed edge that fails to
  collapse; layer/band outputs carry no `pass`/`verdict`.
- PASS — Boundaries respected by code path: `run_train_emission` uncalled; no TEST/holdout query
  (`fenced_bar_query`/`assert_within_fence` band=TRAIN only); CONFIRM band sealed, never analysed or
  unlocked; no CONFIRM unlock record exists.
- PASS — Missing spread represented as null, never zero: `spread_bps=None`, `spread_rt_bps: null`,
  `cost_scope=PARTIAL_FEES_FUNDING_ONLY`; no `SpreadBps`/`MeanPriceSkewBps`/flip-proxy in cost code; no
  fully-net/cost-complete/tradable/deployable claim.
- PASS — Amendment ledger (L-23): A1 looser, A2-A4 neutral, A5-A6 tighter; count 1 looser / 2 tighter /
  3 neutral; no one-directional streak ≥3; no global-null qualifier gate applies.
- PASS — Derangement destroy (L-28): every permutation destroy rejects fixed points; matched-timing/L4
  are candidate-sampling controls (live date/realised pair excluded), not permutations.
- PASS — One BacktestNode per process (L-31); native NautilusTrader engine; no XENA route; no screen-to-money
  conversion pin applicable.

### Issues

None. Run-3 issues 1-3 are closed and independently verified; no new defect found.

Observation (non-blocking, execution-time, fails safe): `reconcile_event_fills` calibrates the fill
timestamp to `ts_last == decision_ts` (`runner_contract.py:330`). If live Nautilus fill-ts semantics
differ (the known fill-ts off-by-one trap), reconciliation raises and blocks the bundle rather than
passing bad data — an integrity-safe failure, not a governance risk. Flagged only so the operator/analyst
expects a hard stop if the convention is off, not a silent pass.

**Disposition:** APPROVE for the operator's separate execution gate. QA approval does not authorise
execution; TEST, holdout, CONFIRM unlock, and any deployability claim remain outside this run.

## QA run 5 — 2026-07-23T00:19:40Z — mode: subagent — HEAD 96a0a4f81d386408ecb82b0281358cbc7f59ae29

Verdict: APPROVE

Reviewed git state: committed HEAD `96a0a4f81d386408ecb82b0281358cbc7f59ae29`; dirty-file
list before this append: none. Fresh-context reviewer did not implement A7/A8. Per the review
scope, `data/nautilus_runs/SPDR-011` and all real outcome/value/CONFIRM data were not read.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| One causal four-hour episode; strict completed breakout; non-overlap (§1-2, §5) | `design_derivations/census.py:249-320,332-371`; `spdr011_strategy.py:22-84` | MATCHES | State/range are fixed from confirmed prior data; strict locator and explicit ENTRY/EXIT schedule preserve the frozen episode. |
| Daily state, 60-return warm-up, rv20/prior-252 percentile, drift20/beta60 (§5.1) | `design_derivations/census.py:29-38,249-320` | MATCHES | `MIN_DAILY_RETURNS=60`; current rv is excluded from the percentile history. The proposed warm-up change is absent. |
| Real next-open entry/exit with actual engine fills (A7; §4, §13.10-11) | `run_spdr011.py:229-300,538-625`; `spdr011_strategy.py:121-143`; `runner_contract.py:239-424` | MATCHES | Each scheduled action gets a real-price `TradeTick`: source close `decision+1m`, `ts_event=decision`, `ts_init=decision+1ns`, `NO_AGGRESSOR`; insert latency is 1ns. Reconciliation requires actual fill at `decision+1ns` and source `RealOpen` within relative `1e-9`. |
| No post-run fill rewriting (A7; §13.11) | `run_spdr011.py:620-679,646-650`; `runner_contract.py:275-368` | MATCHES | Engine reports flow unchanged into emission writing. The catalog open is used only to build the pre-engine tick and later verify the emitted fill; no assignment replaces `avg_px` or `ts_last`. |
| DESIGN-only Run 1; CONFIRM unexecuted and unstaged (A8; §6, §13.3-4) | `run_spdr011.py:199-219,538-560,627-641,706-776`; `bundle.py:25-50,81-112` | MATCHES | Census is filtered to DESIGN before marks, schedules, engine data, fills, controls, and bundle. Data end is bounded to the final DESIGN exit-open seam. Bundle accepts exactly `{"DESIGN"}` and writes only `design.parquet`; no tracked CONFIRM raw-fill/artifact exists. |
| Located events retained; unavailable events not scheduled (§5.1, §6, §13.10) | `runner_contract.py:50-122`; `run_spdr011.py:222-226,553-560`; `runner_contract.py:298-420` | MATCHES | Left joins retain every located row and freeze a missing-mark reason. Only `4h_available` rows enter schedules; unscheduled unavailable rows reconcile as `UNAVAILABLE`, while a fill pair on one is rejected. |
| Open-to-open outcomes and golden prices (§6-7, §12) | `runner_contract.py:38-122`; `test_spdr011_runner.py:45-123` | MATCHES | Entry and 1h/2h/4h marks use real first-minute opens; no trigger-bar move is credited. |
| Signed flow causal same-slot prior-60 percentile (§5.3) | `run_spdr011.py:464-535`; `runner_contract.py:178-226` | MATCHES | Current imbalance is appended after its percentile is formed; known timestamp must be no later than trigger; zero-volume remains base but flow-ineligible. |
| Fees, discrete `(entry,exit]` funding, 0/2/5 allowance, no spread (§11) | `runner_contract.py:125-175` | MATCHES | Shared `bybit_round_trip_cost_bps` receives `spread_bps=None`; missing outcomes retain null partial-net values. |
| Frozen matched timing, unconditional breakout, direction/future derangements (§8) | `controls.py:21-150,153-358,387-545`; `run_spdr011.py:371-461,707-760` | MATCHES | Timing/date and realised-pair exclusions are enforced; all permutation destroys use zero-fixed-point derangements; batteries use 2,000 frozen seeds. |
| Hard future-destroy sentinel and supported-edge survival rule (§8.1) | `controls.py:78-111,387-485,607-651`; `run_spdr011.py:548,697-721` | MATCHES | Sentinel is calibrated before engine/outcome access; real-edge rule blocks only an authenticated supported edge that survives destruction. |
| Date dependence, informative bands, ordered layers (§9-10) | `controls.py:547-604,679-728`; `layers.py:22-80` | MATCHES | UTC-date resampling and 1/3/7-day-capable machinery emit measurements; L1-L5 views preserve predeclared arms and contain no value auto-verdict. |
| Frozen hashes and live-tree identity (§3.1, §13.1,9) | `run_spdr011.py:84-95,116-184,575-579,691-696` | MATCHES | All four committed artifact hashes match design and runner constants; live signed-tree hash is required before engine construction and before flow access. |
| UTC-aware mark seam retained; rejected warm-up change absent (A7 context) | `run_spdr011.py:342-358`; `design_derivations/census.py:31-38,262-289` | MATCHES | `SourceCloseTime` is explicitly UTC-aware. Census still requires 60 returns and its derivation/event-key hashes are unchanged. |
| One node/process; operator authority; no CLI (§13, §15) | `run_spdr011.py:538-545,581-625` | MATCHES | One `BacktestNode`, deferred disposal, non-empty operator authority, and no command-line entry point. |

### Golden-trace diff

| Trace | Design expectation | Independent check | Verdict |
|---|---|---|---|
| GT-1 LONG | 107 to 104 = -280.374 bps | Open-to-open formula and runner test reproduce `-280.3738`; synthetic engine gap smoke filled ENTRY at 107, not processed-bar close 100. | MATCHES |
| GT-2 SHORT | 88 to 84 = +454.545 bps | Direction multiplier and exact four-hour open reproduce `+454.5455`. | MATCHES |
| GT-3 EQUALITY | prior-high equality emits no event | Census uses strict `>`/`<`; existing census test covers equality/no-event behavior. | MATCHES |
| A7 engine sequence | order decision at boundary; actual fill at real next open one ns later | Temporary real `BacktestNode` smoke used deliberate gaps: bar closes 100/110, execution ticks 107/104. Engine fills were 107/104 with `ts_last=decision+1ns` for both ENTRY and EXIT. | MATCHES |
| Shared exit/entry boundary | EXIT before ENTRY | Schedule priority sorts EXIT first at equal decision timestamp. | MATCHES |

### Governance & boundary

- PASS — Fresh subagent context; append-only review; committed HEAD and initial clean state recorded.
- PASS — `51 passed` across `test_spdr011_{census,signed_ingest,runner}.py` using the project
  Python 3.13/NautilusTrader 1.230.0 environment.
- PASS — Ruff reports `All checks passed`; `git diff --check` clean before this append;
  `check_no_local_accounting("python/experiments/SPDR-011/code")` returns
  `{"ok": true, "banned_defs_found": []}`.
- PASS — Independent temporary Nautilus gap smoke proves the mixed Bar/TradeTick event order and
  matching 1ns insert latency produce actual fills at the supplied real opens, not bar closes.
- PASS — L-41 supersedes only L-29's universal price-anchor claim. L-29's close-axis timestamp
  warning remains; SPDR-011 now binds price to the separate real-open event and fill timestamp to
  `decision+1ns`.
- PASS — Actual hashes: census JSON `94faab2e...13681`, event keys `d1299a08...c7dfd`, census
  derivation `9fae1731...802bdc`, signed attestation `bdfe839c...180d29`. Census JSON changed only
  its regeneration timestamp; counts/coverage and event keys are unchanged.
- PASS — Run-1 code cannot query/schedule CONFIRM events or write a CONFIRM bundle member. Git tracks
  no SPDR-011 CONFIRM fill/artifact. The forbidden run directory was not inspected.
- PASS — TEST and holdout remain outside every Run-1 query. Missing spread is null/unavailable; no
  prohibited spread proxy or deployability claim enters code.
- PASS — Amendment ledger is directionally correct: A1 1L, A2-A4 3N, A5-A8 4T. The four-amendment
  tighter streak is explicitly flagged for the execution gate; no qualifier gate makes a false-
  qualifier re-derivation applicable.
- PASS — One BacktestNode/process, no Python strategy backtest, no local accounting, no XENA route,
  and no screen-to-money conversion pin apply.

### Issues

None. A7/A8 close the real-open execution and CONFIRM-exposure defects without introducing a
design deviation or value gate.

**Disposition:** APPROVE for the operator's separate DESIGN-only Run-1 execution gate. This review
does not execute the run, authorise CONFIRM, inspect any real result, or permit TEST/holdout access.

## QA run 6 — 2026-07-23T00:34:39Z — mode: subagent — HEAD c6bc99074aec7587378f59eb9839cfe032e18ae5

Verdict: APPROVE

Reviewed git state: committed HEAD `c6bc99074aec7587378f59eb9839cfe032e18ae5`; dirty-file
list before this append: none. Fresh-context reviewer did not implement A9. Per the assigned
boundary, `data/nautilus_runs/SPDR-011`, real outcome/value layers, CONFIRM data, TEST and holdout
were not inspected.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| One causal four-hour episode; strict completed breakout; non-overlap (§1-2, §5) | `design_derivations/census.py:131-154,249-320,333-373`; `spdr011_strategy.py:22-84` | MATCHES | State/range inputs are confirmed before the trigger; equality is not an event; schedule construction rejects overlap. |
| Daily state, 60-return warm-up, rv20/prior-252 percentile, drift20/beta60 (§5.1) | `design_derivations/census.py:29-38,249-320` | MATCHES | Current rv is excluded from its prior-history percentile; beta/drift use the frozen causal windows and lexical rank tie-break. |
| Exact engine-clock decisions independent of boundary bars (A9; §13.12) | `spdr011_strategy.py:114-148` | MATCHES | `on_start` registers one `set_time_alert_ns` callback per exact decision timestamp; no `on_bar` callback advances the schedule. |
| Shared EXIT-before-ENTRY order at contiguous boundaries (§2, §13.10) | `spdr011_strategy.py:43-84,126-148` | MATCHES | One shared schedule assigns EXIT priority 0 and ENTRY priority 1 at equal timestamps; the alert drains that ordered schedule, preserving explicit same-direction round trips. |
| Actual engine fill at catalog `RealOpen`, decision `+1ns` (A7/A9; §4, §13.10-11) | `run_spdr011.py:229-300,537-625`; `runner_contract.py:239-368` | MATCHES | Each scheduled action joins the source mark at `decision+1m`, builds a `NO_AGGRESSOR` tick sequenced at `decision+1ns`, and uses matching 1ns insert latency. Reconciliation requires engine fill time `decision+1ns` and price equal to source `RealOpen` within relative `1e-9`. |
| No post-run fill rewrite (§13.11) | `run_spdr011.py:620-689`; `runner_contract.py:275-368` | MATCHES | Engine-generated fill/order reports are written and then checked. Code never assigns catalog prices or timestamps into the fill report. |
| DESIGN-only Run 1; CONFIRM/TEST/holdout outcome access excluded (A8; §4, §6, §13.3-4) | `run_spdr011.py:199-219,537-560,597-617,626-640,705-775`; `bundle.py:25-50` | MATCHES | Runner filters to DESIGN before any mark query, schedule, engine input, control or bundle; the bounded data end covers only the final DESIGN exit open. Bundle accepts only `DESIGN` and writes only `design.parquet`. |
| Located population and unavailable-event handling (§5.1, §6, §13.10) | `runner_contract.py:50-122,239-424`; `run_spdr011.py:222-226,553-560` | MATCHES | Left joins retain every located event with a frozen missing reason. Only complete 4h rows are scheduled; unavailable rows remain in the artifact, and a complete fill pair on one is rejected. |
| Open-to-open real prices and golden fixtures (§6-7, §12) | `runner_contract.py:38-122`; `test_spdr011_runner.py:45-123` | MATCHES | Entry and 1h/2h/4h marks use first-minute `RealOpen`; trigger-bar movement is not credited. |
| Signed flow, fees/funding, and missing-spread boundary (§5.3, §11) | `run_spdr011.py:463-535,689-695`; `runner_contract.py:125-226` | MATCHES | Flow percentile uses prior 60 completed same-slot values; source-known time is causal. Shared Bybit cost receives `spread_bps=None`; partial nets stay null when 4h outcome is unavailable. |
| Frozen controls, derangements and future-destroy tripwire (§8-9) | `controls.py:21-150,153-358,387-651`; `run_spdr011.py:547-548,696-743` | MATCHES | Permutation destroys are zero-fixed-point, frozen seed ranges are used, sentinel calibrates before outcome access, and only the registered supported-edge survival failure blocks. |
| Ordered informative layers; no value auto-verdict (§7, §10, §13.5-7) | `layers.py:22-80`; `controls.py:679-728`; `run_spdr011.py:705-775` | MATCHES | L1-L5 populations remain visible and ordered; outputs contain measurements, not candidate-drop or value-pass machinery. |
| Frozen census/attestation and live signed-tree identity (§3.1, §13.1-2,9) | `run_spdr011.py:84-184,574-578,689-695` | MATCHES | All four file hashes match the design and runner pins; independent live-tree rehash equals `d4b7bbed...f7d2b9` before any authorised engine run. Attestation is VERIFIED for five symbols with zero TEST/holdout rows read. |
| One BacktestNode/process, operator authority, no CLI (§13, §15) | `run_spdr011.py:537-545,580-625` | MATCHES | Exactly one node is constructed; execution requires a non-empty operator authority and the module exposes no command-line runner. |
| A9 authority and amendment direction (§14-15) | `chapter-05-governance.md:58-65`; checkpoint design `:190-215`; `design.md:409-448` | MATCHES | Operator authorised A9 implementation and a clean DESIGN rerun conditional on this QA. Ledger is 1 looser / 5 tighter / 3 neutral; A5-A9's five-tighter streak is explicitly flagged for the execution gate. False-qualifier re-derivation is inapplicable because no arm qualifies or drops by value. |

### Golden-trace diff

| Trace | Design expectation | Independent check | Verdict |
|---|---|---|---|
| GT-1 LONG | 107 to 104 = -280.374 bps | Open-to-open formula produces `-280.3738` bps; the real BacktestNode missing-bar regression fills 107/104 rather than adjacent bar closes. | MATCHES |
| GT-2 SHORT | 88 to 84 = +454.545 bps | Direction multiplier and exact four-hour opens produce `+454.5455` bps. | MATCHES |
| GT-3 EQUALITY | Close equal to prior high emits no event | Locator uses strict `>` and `<`; equality fails both predicates. | MATCHES |
| A9 missing decision bar | Alert still submits at the exact boundary; fill is real open at `+1ns` | Independently reran committed real `BacktestNode` regression with no bar at the entry boundary: asserted fills 107/104 and `ts_last=entry+1ns/exit+1ns`; test passed. | MATCHES |
| Shared boundary | EXIT precedes ENTRY when one episode ends as the next begins | Builder regression and explicit priority show `ENTRY(old), EXIT(old), ENTRY(new), EXIT(new)` with EXIT before the equal-time new ENTRY. | MATCHES |

### Governance & boundary

- PASS — Fresh subagent context; append-only run; requested committed HEAD and initial clean state recorded.
- PASS — Focused suite: `87 passed` across SPDR-011 census, signed-ingest, runner and Chapter-05
  preflight tests. The separate real-engine missing-bar regression passed (`1 passed`); its only
  output was Nautilus's upstream `Timestamp.utcnow` deprecation warning.
- PASS — Ruff: `All checks passed`; `check_no_local_accounting("python/experiments/SPDR-011/code")`
  returned `{"ok": true, "banned_defs_found": []}`; `git diff --check` was clean before append.
- PASS — Independent SHA-256: census JSON `94faab2e...13681`, event keys `d1299a08...c7dfd`, census
  derivation `9fae1731...802bdc`, signed attestation `bdfe839c...180d29`. Independent live signed
  TRAIN tree hash exactly matched `d4b7bbed...f7d2b9`.
- PASS — No Python strategy backtest, second BacktestNode, local accounting definition, XENA path,
  spread proxy, CONFIRM execution path in Run 1, TEST/holdout query, or deployment claim was found.
- PASS — L-42 is enforced by an exact clock alert and a deliberately missing-boundary real-engine
  regression; L-41 remains enforced by real-open tick sequencing, actual engine-fill reconciliation,
  and the absence of any post-execution fill replacement.
- PASS — A9 is operator-authorised but does not itself launch the run. A5-A9's five consecutive
  tighter amendments must still be disclosed when the operator opens the execution gate.

### Issues

None.

**Disposition:** APPROVE for the operator's separate DESIGN-only Run-1 execution gate. This QA does
not execute the run, authorise any value-layer read or CONFIRM, or permit TEST/holdout access.

## QA run 7 — 2026-07-23T00:50:08Z — mode: subagent — HEAD 53136599001772a3317c6a81dc538c964a04f48b

Verdict: REVISE

Reviewed git state: committed HEAD `53136599001772a3317c6a81dc538c964a04f48b`; dirty-file
list before this append: none. Fresh-context reviewer did not implement A10. Per the assigned
boundary, `data/nautilus_runs/SPDR-011`, real outcome/value layers, CONFIRM data, TEST and holdout
were not inspected.

### Design-fidelity trace

| Design clause (§ref) | Code (file:line) | Verdict | Notes |
|---|---|---|---|
| One causal four-hour episode; strict completed breakout; non-overlap (§1-2, §5) | `design_derivations/census.py:131-154,249-320,333-373`; `spdr011_strategy.py:22-84` | MATCHES | State and range use confirmed prior data; equality is not an event; overlapping episodes are rejected. |
| Fixed daily state, rank, warm-up and causal source times (§5.1-2) | `design_derivations/census.py:29-38,249-320`; `run_spdr011.py:144-187` | MATCHES | Current `rv20` is excluded from prior-252 history; beta/drift windows and lexical tie-break match; source-known times must not exceed the trigger. |
| Frozen symbol serialization: offsets 0/3/6/9/12ns, alert, insert +1ns, own tick +1ns (§13.11-12; L-42/L-44) | `run_spdr011.py:95-99,232-323`; `spdr011_strategy.py:93-125` | MATCHES | `index*3` over frozen BTC/ETH/SOL/DOGE/XRP gives the required offsets; strategy alert is `decision+offset`, latency inserts at `+1ns`, and the own `NO_AGGRESSOR` real-open tick initializes at `+2ns`. |
| Integer-nanosecond reconciliation at `decision+symbol_offset+2ns` (§13.10,13; L-43) | `runner_contract.py:233-280,308-351`; `run_spdr011.py:683-690`; `test_spdr011_runner.py:519-580` | MATCHES | Schedule and `datetime[ns]` fill columns are converted to integer epochs inside Polars. An independent ETH fixture with offset `3ns` reconciled exactly at `decision+5ns`. |
| EXIT before ENTRY at one symbol's shared boundary (§2, §13.10) | `spdr011_strategy.py:76-83,103-113`; `test_spdr011_runner.py:233-294` | DEVIATES | Builder creates EXIT priority, but runtime reload immediately sorts only `decision_ts` with Polars `maintain_order=False`; equal-time order is therefore not guaranteed. The pinned DESIGN census has 926 contiguous boundaries (922 same-direction). |
| Real multi-instrument stale-state regression (§13.11; L-44) | `test_spdr011_runner.py:775-921` | DEVIATES | One node, two instruments, and one present/one missing decision bar are covered, but both streams use prior close `100` and execution opens `107/104`. The required deliberately different per-symbol prior closes and opens are absent. |
| Real first-minute `RealOpen` fills and no post-run fill rewrite (§4, §13.10-11; L-41) | `run_spdr011.py:232-310,581-690`; `runner_contract.py:233-433` | MATCHES | Catalog opens create pre-engine ticks; engine reports flow unchanged into emission and are checked against source marks. No assignment replaces emitted fill price or time. |
| Located population retained; unavailable paths explicit (§5.1, §6, §13.10) | `runner_contract.py:50-122,233-433`; `run_spdr011.py:225-229,564-570` | MATCHES | Left joins retain located rows and freeze reasons; only complete rows are scheduled; an unavailable row cannot carry a complete fill pair. |
| DESIGN-only Run 1; no CONFIRM/TEST/holdout execution (§4, §6, §13.3-4) | `run_spdr011.py:202-222,548-570,608-628,717-787`; `bundle.py:25-50` | MATCHES | Events are filtered to DESIGN before mark reads, schedules, engine data, controls and bundle; bundle accepts only `DESIGN` and writes only `design.parquet`. |
| Signed flow and partial cost boundary (§5.3, §11) | `run_spdr011.py:474-545,701-707`; `runner_contract.py:125-226` | MATCHES | Flow uses prior 60 completed same-slot imbalances and a causal known time. Shared Bybit cost receives `spread_bps=None`; 0/2/5-bps allowances remain reports, not gates. |
| Frozen controls, zero-fixed derangements and future-destroy (§8-9) | `controls.py:21-150,153-358,387-651`; `run_spdr011.py:558,718-755` | MATCHES | Seed ranges, strata, realised-pair exclusion and derangements match. Sentinel calibrates before outcome access; only the registered supported-edge future-destroy rule can invalidate. |
| Ordered informative layers; no value auto-verdict (§7, §9-10, §13.5-7) | `layers.py:22-80`; `controls.py:679-728`; `run_spdr011.py:717-787` | MATCHES | All five populations remain visible; effect/MDE/band reads do not drop candidates or decide progression. |
| Frozen hashes, live signed tree and census membership (§3.1, §13.1-2,9) | `run_spdr011.py:84-187,585-589,701-707` | MATCHES | Four artifact hashes match; 3,606 unique event IDs reproduce; live signed-tree hash matches attested/frozen `d4b7bbed...f7d2b9`; attestation records zero TEST/holdout rows. |
| One BacktestNode/process, explicit authority, no CLI (§13, §15) | `run_spdr011.py:548-555,591-635` | MATCHES | One node is constructed only after non-empty operator authority; import has no run side effect and no execution command is exposed. |
| Amendment ledger and execution disclosure (§14-15; L-23) | `design.md:410-450`; checkpoint design `:190-216` | MATCHES | A1-A10 running count is 1 looser / 6 tighter / 3 neutral. A5-A10's six consecutive tighter amendments are explicitly disclosed; no qualification gate makes false-qualifier re-derivation applicable. |

### Golden-trace diff

| Trace | Design expectation | Independent check | Verdict |
|---|---|---|---|
| GT-1 LONG | 107 to 104 = -280.374 bps | Open-to-open implementation and focused fixture produce `-280.3738` bps. | MATCHES |
| GT-2 SHORT | 88 to 84 = +454.545 bps | Direction multiplier and exact four-hour opens produce `+454.5455` bps. | MATCHES |
| GT-3 EQUALITY | Close equal to prior high emits no event | Locator uses strict `>` and `<`; equality satisfies neither. | MATCHES |
| A10 nanosecond trace | ETH offset 3ns; insert at +4ns; fill at +5ns | Independent real `datetime[ns]` reconciliation passed at `decision+3+2ns`; integer conversion preserved the final nanoseconds. | MATCHES |
| A10 cross-stream trace | Distinct stale states and distinct own opens cannot cross-fill | Standalone real-engine regression passed, but both instruments were fed the same stale close and same execution-open sequence. | DEVIATES |
| Shared episode boundary | EXIT before next ENTRY | Builder fixture orders EXIT first, but runtime's equal-key re-sort does not guarantee preservation. | DEVIATES |

### Governance & boundary

- PASS — Fresh subagent context, append-only review, exact committed HEAD, and initially clean tree.
- PASS — Focused suite: `111 passed` across SPDR-011 census, signed ingest, runner, Chapter-05
  preflight and shared evaluation tests. Standalone real multi-instrument test: `1 passed`; only two
  upstream `Timestamp.utcnow` deprecation warnings.
- PASS — Ruff: `All checks passed`; `git diff --check` clean before append;
  `check_no_local_accounting("python/experiments/SPDR-011/code")` returned
  `{"ok": true, "banned_defs_found": []}`.
- PASS — SHA-256 matched design pins: census JSON `94faab2e...13681`, event keys
  `d1299a08...c7dfd`, derivation `9fae1731...802bdc`, signed attestation
  `bdfe839c...180d29`; signed tree matched `d4b7bbed...f7d2b9`.
- PASS — Missing spread remains null/unavailable with partial-cost disclosure; no spread proxy,
  deployability claim, Python strategy backtest, second node, XENA route or post-run fill rewrite.
- PASS — Family is registered, 0 counted TEST reads are recorded, holdout remains sealed, and
  A5-A10's six-tighter streak is disclosed at the execution gate.
- REVISE — L-44's durable regression is under-discriminating, and shared-boundary execution order
  is not preserved by an explicit runtime tie-break.

### Issues

1. **REVISE — runtime EXIT-before-ENTRY is not guaranteed.** Design §2/§13.10 requires EXIT before
   ENTRY at a contiguous boundary. `spdr011_strategy.py:79-83` creates that priority, but
   `spdr011_strategy.py:105` reloads with `.sort("decision_ts")`; installed Polars defaults to
   `maintain_order=False` for equal keys. This is material for 926 DESIGN boundaries. Required
   change: preserve an explicit action-priority key (or a stable-order equivalent) through runtime
   load and add a runtime/real-engine contiguous same-symbol regression. `FAILING_ARTIFACT: code/`
   `REQUIRED_SKILL: experiment-developer`.
2. **REVISE — L-44 regression does not use distinct per-symbol market states.**
   `test_spdr011_runner.py:807-858` gives XRP and ETH the same prior close and the same `107/104`
   execution opens. Required change: retain one missing and one present decision bar, but give both
   instruments deliberately different prior closes and different entry/exit opens, then assert
   every tagged fill uses its own stream and frozen offset. `FAILING_ARTIFACT: python/tests/`
   `REQUIRED_SKILL: experiment-developer`.

**Disposition:** REVISE before any DESIGN Run-1 execution. No outcome emission is authorised; QA
must be rerun after both ordering regressions are made discriminating and deterministic.
