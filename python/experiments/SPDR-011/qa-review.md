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
