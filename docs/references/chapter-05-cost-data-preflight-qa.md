# Chapter 05 Cost/Data Preflight — Fresh-Context QA

> **HISTORICAL (chapter-05) — not binding on the live programme after INFR-022 (2026-08-08).**
> This QA record backs the superseded chapter-05 cost policy; the live programme is
> zero-cost (`NO_COST_CHARGED`). Body retained verbatim for reproducibility.

## QA run 1 — 2026-07-22T20:11:51Z — mode: subagent — HEAD `839b4438da6a6ec524d4fd0e8805fba0af58bcd1`

**Reviewed dirty files:**

- `docs/experiments-docs/INDEX.md`
- `docs/references/architecture.md`
- `docs/references/dataset-reference.md`
- `docs/references/chapter-05-cost-data-preflight.md` (untracked)
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/__init__.py`
- `python/src/xen/sigbar/access.py` (untracked)
- `python/src/xen/sigbar/data_types.py`
- `python/tests/test_chapter05_preflight.py` (untracked)
- `python/tests/test_evaluation.py`

**Verdict: REVISE**

The cost arithmetic, discrete funding counter, invalid-spread rejection, INFR-017 hash/pin
verification, adapter output, tests, and live research block pass. Approval is blocked by one
storage-contract mutation and contradictory live cost/routing references.

### Design-fidelity trace

| Design clause | Implementation / evidence | Verdict | Notes |
|---|---|---|---|
| Governance §2.1 / brief §7.1 — stress once; components reconcile | `python/src/xen/evaluation.py:534-559`; `python/tests/test_evaluation.py:89-108` | MATCHES | Independent discrete-stamp arithmetic: stress 0.5/1/2 gives totals 6.122/12.244/24.488 bps for BTC, exactly equal to returned fee + spread + funding. |
| Governance §2.2 / brief §7.2 — reject negative/non-finite spread | `python/src/xen/evaluation.py:485-499`; `python/tests/test_evaluation.py:111-114` | MATCHES | `-1`, NaN, +Inf and -Inf raise `ValueError`; negative input is not floored. Stress is also checked finite/non-negative. |
| Governance §2.3 / brief §7.3 — discrete funding stamps for fixed four hours | `python/src/xen/evaluation.py:459-482,543-553`; `python/tests/test_evaluation.py:117-160` | MATCHES | Counter implements `(entry, exit]`. Exact-entry stamp is excluded; exact-exit stamp is included; midnight rollover works. Discrete use is explicit through `funding_stamps=` and disclosed as `DISCRETE_STAMPS`. |
| Governance §2.4 / brief §7.4 — taker/taker, stress 0.5/1/2, invalid spread, reconciliation tests | `python/tests/test_evaluation.py:89-160`; `python/tests/test_chapter05_preflight.py:24-70` | MATCHES | Required regression cases exist and pass. |
| Governance §2.5 / brief §7.5 — correct dataset and architecture truth | `docs/references/dataset-reference.md:81-91,204-230`; `docs/references/architecture.md:20-30,122-139` | PARTIAL | The edited references correctly define the field and costs. Other live references still contradict them (Issue 2). |
| Governance §2.6 / brief §7.6-7 — quarantine carrier; preserve bytes; accurate name/status | `python/src/xen/sigbar/access.py:10-35`; `python/tests/test_chapter05_preflight.py:50-70` | DEVIATES | Adapter preserves input values and emits `MeanPriceSkewBps` / `UNUSABLE_AS_SPREAD`, but the retained storage contract itself changes `SPREAD_UNUSABLE` while retaining the same pipeline version (Issue 1). No data/fence artifact appears in the dirty list; field order/types are unchanged. |
| Governance §2.7 / brief §7.8 — verify five pins against INFR-017 at process start | `python/src/xen/evaluation.py:400-456`; `python/tests/test_chapter05_preflight.py:15-47`; `docs/references/chapter-05-cost-data-preflight.md:22-38` | MATCHES | Independently recomputed self-hash is `e3b9fd9b...e6225`; summary has exactly five symbols. Derived `round(max(flip_median_bps, one_tick_bps), 3)` values are 0.244/0.305/0.727/1.477/1.965. Tampering fails. Future Chapter-05 processes are explicitly required to call the loader before event/cost work. |
| Governance §2.8 — fresh QA and focused tests | This run; commands below | MATCHES when Issues 1-2 close | QA is structurally independent and read-only except this append-only artifact. |

### Golden arithmetic and boundary trace

| Case | Design expectation | Observed implementation | Verdict |
|---|---:|---:|---|
| Taker/taker fee | `2 × 5.5 = 11.0` bps | 11.0 bps at stress 1 | MATCHES |
| BTC, one funding stamp, stress 1 | `11 + 0.244 + 1 = 12.244` | 12.244; components sum exactly | MATCHES |
| Same, stress 0.5 | `0.5 × 12.244 = 6.122` | 6.122 | MATCHES |
| Same, stress 2 | `2 × 12.244 = 24.488` | 24.488 | MATCHES |
| `07:59:59.999999999 → 08:00` | one stamp | 1 | MATCHES |
| `08:00 → 08:00` | entry stamp excluded | 0 | MATCHES |
| `08:00 → 16:00` | exit stamp included | 1 | MATCHES |
| `22:00 → 02:00` across midnight | one stamp | 1 | MATCHES |
| exit before entry | reject | `ValueError` at `evaluation.py:480-481` | MATCHES |

### Governance, compatibility, and boundary checks

| Check | Evidence | Verdict |
|---|---|---|
| INFR-017 self-hash and five derived pins | Independent JSON canonicalisation reproduced the recorded/frozen hash; all five raw pairs independently re-derived | PASS |
| Bad-input handling in scoped requirements | Invalid spread and stress rejected; reversed timestamps rejected; non-integer/negative funding-stamp counts rejected | PASS |
| Stored-byte preservation | No catalog, staging, manifest, or pin artifact is dirty; adapter leaves input frame unchanged | PARTIAL — storage status constant mutation remains |
| Misleading-name quarantine | Adapter removes `SpreadBps`/`spread_feature` from its output and emits accurate name/status; exactly one carrier required | PASS at adapter seam |
| Public access | `xen.sigbar` exports `quarantine_mean_price_skew`, `MEAN_PRICE_SKEW_COLUMN`, and `UNUSABLE_AS_SPREAD` at `__init__.py:42-57` | PASS |
| Backward compatibility | Default-stress cost values remain unchanged; legacy continuous funding remains when no stamp count is supplied; retained full tests pass | PARTIAL — `SPREAD_UNUSABLE` wire value changes without a version change |
| Documentation truth | Edited dataset/architecture/preflight docs are accurate internally | PARTIAL — stale live references remain |
| Live experiments gate | `docs/experiments-docs/INDEX.md:5-10,14-23` remains `BLOCKED ON COST/DATA PREFLIGHT`; no family/checkpoint exists | PASS |
| Research/outcome contact | Dirty diff contains no outcome loader, experiment runner, event census, family registration, TEST read, or holdout read; no registry/checkpoint/experiment path is dirty | PASS |
| Diff hygiene | `git diff --check` clean | PASS |

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **28 passed**.
- Retained: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **199 passed, 4 skipped, 1 pre-existing NumPy warning**.
- Hash/pin and arithmetic/boundary values above were also recomputed independently of pytest assertions.

### Issues requiring revision

1. **Warning — the byte-compatible signed-bar contract was changed without a version change.**
   - Design: governance §2.6; brief §7.7 requires preserved stored bytes/fence pins and analytical-only renaming.
   - Evidence: `python/src/xen/sigbar/data_types.py:35-42` says any semantic change requires a pipeline-version bump, keeps `sigbar-0.1.0`, but changes the storage constant from the frozen `UNUSABLE` wire value to `UNUSABLE_AS_SPREAD`. `data_types.py:60-62` remains the persisted `spread_feature`/`spread_status` contract. The frozen archive copy still records `SPREAD_UNUSABLE = "UNUSABLE"`.
   - Risk: newly encoded `sigbar-0.1.0` records can carry a different status value from existing records while claiming the same pinned contract; this weakens byte/schema compatibility and conflates storage status with the new analytical status.
   - Required fix (`experiment-developer`): retain `SPREAD_UNUSABLE = "UNUSABLE"` in the storage contract. Keep `UNUSABLE_AS_SPREAD` only in `xen.sigbar.access` output. Add a regression assertion that the frozen storage value/version remain unchanged while the adapter emits the new analytical status.

2. **Warning — live cost/routing references still bypass or contradict the new boundary.**
   - Design boundary: `docs/references/architecture.md:24-30` and `docs/references/dataset-reference.md:95-99,204-230` say audited pins replace the bad field and unresolved T1 evidence cannot open a T2 branch.
   - Evidence: `docs/references/xena-lane.md:148-149,167-168` still permits T2 confirmation and directs costs to a per-symbol pseudo-quote series. `docs/knowledge-base/evaluation-framework.md:199-200,208-213` still says the negative-input/pin correction is outstanding and names the pseudo-quote model as active. The shared route still returns `AWAITING_MBP` with a T2-confirmation note at `python/src/xen/evaluation.py:567-578`; `python/tests/test_estimand_validation_v2.py:139` freezes that stale route label.
   - Risk: a live consumer can follow current project documentation or the mandatory shared route and re-enter the invalid spread/T2-rescue path despite the corrected Chapter-05 references.
   - Required fix (`experiment-developer` for the shared route/tests; `experiment-documenter` for docs): reconcile live references with the audited-pin/no-T2 boundary. Preserve archived reproducibility explicitly. If `spread_scale_route` must retain legacy/XENA behavior, add an explicit Chapter-05 policy/wrapper whose unresolved route is permanently parked, and test it; do not silently break retained callers.

### Revision disposition

`FAILING_ARTIFACTS`: `python/src/xen/sigbar/data_types.py`, `docs/references/xena-lane.md`,
`docs/knowledge-base/evaluation-framework.md`, and the Chapter-05 routing seam in
`python/src/xen/evaluation.py` (or a dedicated wrapper).

After both issues are fixed, rerun focused + retained tests and append a fresh-context QA run.
Execution, registration, event census, TEST, and holdout access remain blocked.

## QA run 2 — 2026-07-22T20:17:19Z — mode: subagent — HEAD `839b4438da6a6ec524d4fd0e8805fba0af58bcd1`

**Reviewed dirty files:**

- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (untracked; append-only review)
- `docs/references/chapter-05-cost-data-preflight.md` (untracked)
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/__init__.py`
- `python/src/xen/sigbar/access.py` (untracked)
- `python/src/xen/sigbar/data_types.py`
- `python/tests/test_chapter05_preflight.py` (untracked)
- `python/tests/test_evaluation.py`

**Verdict: APPROVE**

Both run-1 blockers are closed. All eight preflight requirements match the design; focused and
retained tests pass; the live gate remains blocked pending the operator's separate status update.
This approval does not authorise registration or execution.

### Revision closure

| Prior issue | Revised evidence | Verdict |
|---|---|---|
| Frozen signed-bar wire value changed under `sigbar-0.1.0` | `python/src/xen/sigbar/data_types.py:35-43` retains `SIGBAR_PIPELINE_VERSION = "sigbar-0.1.0"` and `SPREAD_UNUSABLE = "UNUSABLE"`; `python/src/xen/sigbar/access.py:10-35` separately emits analytical `UNUSABLE_AS_SPREAD`; regression at `python/tests/test_chapter05_preflight.py:76-78` freezes both storage values | CLOSED |
| Active pseudo-spread/T2 guidance contradicted the Chapter-05 boundary | `python/src/xen/evaluation.py:567-592` adds explicit availability routing; `secondary_available=False` yields `PARKED_T1_UNRESOLVED`. `docs/references/xena-lane.md:148-151,169-171`, `docs/knowledge-base/evaluation-framework.md:193-215`, and `docs/signal-registry/candidate-families/cf-sigauc-001.md:91-98` now use audited pins/discrete funding and quarantine the stored field. Chapter-05 regression at `python/tests/test_chapter05_preflight.py:81-116` covers route and active guidance | CLOSED |

The shared function's default `secondary_available=True` retains historical `AWAITING_MBP`
behaviour for archived replay compatibility. Active Chapter-05 instructions explicitly require
`secondary_available=False`: `.agents/skills/quant-designer/references/design-requirements.md:128-158`,
`.agents/skills/qa-compliance/SKILL.md:71-76`, and `docs/references/xena-lane.md:148-151`.

### Design-fidelity trace

| Design clause | Code / evidence | Verdict | Notes |
|---|---|---|---|
| Governance §2.1 / brief §7.1 — stress once; components reconcile | `python/src/xen/evaluation.py:534-559`; `python/tests/test_evaluation.py:89-108` | MATCHES | Independent recomputation for one BTC stamp: stress 0.5/1/2 gives 6.122/12.244/24.488 bps, exactly equal to returned components. |
| Governance §2.2 / brief §7.2 — reject negative/non-finite spread | `python/src/xen/evaluation.py:485-499`; `python/tests/test_evaluation.py:111-114` | MATCHES | Negative, NaN and infinite spread values fail; no flooring. |
| Governance §2.3 / brief §7.3 — discrete funding stamps | `python/src/xen/evaluation.py:459-482,543-553`; `python/tests/test_evaluation.py:117-160` | MATCHES | `(entry, exit]` semantics independently reproduce: `08:00→12:00 = 0`, `04:00→08:00 = 1`; rollover and reversed-time handling covered. |
| Governance §2.4 / brief §7.4 — regression battery | `python/tests/test_evaluation.py:89-160`; `python/tests/test_chapter05_preflight.py:27-116` | MATCHES | Taker/taker, stress 0.5/1/2, invalid spread, reconciliation, hash tamper, wire compatibility, quarantine, route and guidance covered. |
| Governance §2.5 / brief §7.5 — dataset/architecture truth | `docs/references/dataset-reference.md:81-99,204-230`; `docs/references/architecture.md:20-30,122-157`; corrected active references above | MATCHES | Stored field is accurately described as mean-price skew with no tick floor; audited pins and discrete funding are active. |
| Governance §2.6 / brief §7.6-7 — quarantine carrier; preserve storage | `python/src/xen/sigbar/access.py:10-35`; `python/src/xen/sigbar/data_types.py:35-63`; `python/tests/test_chapter05_preflight.py:53-78` | MATCHES | Storage schema/version/wire status retained; adapter preserves values, removes misleading input name, and emits `MeanPriceSkewBps` plus `UNUSABLE_AS_SPREAD`. No data/fence artifact is dirty. |
| Governance §2.7 / brief §7.8 — INFR-017 self-hash + five pins at process start | `python/src/xen/evaluation.py:400-456`; `python/tests/test_chapter05_preflight.py:17-50`; `docs/references/chapter-05-cost-data-preflight.md:22-38` | MATCHES | Independent self-hash is `e3b9fd9b...e6225`; exactly five derived pins reproduce: BTC 0.244, ETH 0.305, SOL 0.727, DOGE 1.477, XRP 1.965. Tamper rejection passes. |
| Governance §2.8 — fresh-context QA | This append-only run | MATCHES | Independent reviewer did not implement the patch or revisions. |

### Boundary and governance checks

| Check | Evidence | Verdict |
|---|---|---|
| Chapter-05 resolution route | `spread_scale_route(1.0, 0.5, secondary_available=False)` independently returns threshold 1.5, `t1_undecidable=True`, `PARKED_T1_UNRESOLVED`, and no T2 note | PASS |
| Active guidance | Repository search outside `archive/` finds Chapter-05 `secondary_available=False` / audited pins / discrete funding. Remaining `AWAITING_MBP` code/test is explicitly retained historical behaviour, not active Chapter-05 routing | PASS |
| Public access seam | `xen.sigbar` exports the quarantine adapter and analytical name/status; adapter accepts each retained storage carrier and rejects ambiguous/missing carriers | PASS |
| Backward compatibility | Storage wire/version frozen; legacy cost callers retain continuous funding when `funding_stamps` is absent; historical route is preserved by default; full retained suite passes | PASS |
| Live experiments gate | `docs/experiments-docs/INDEX.md:5-23` remains `PRE-EXPERIMENT — BLOCKED ON COST/DATA PREFLIGHT`; no `CF-VOLCONV-001` family/checkpoint exists | PASS |
| No research/outcome contact | Implementation/tests load only the frozen INFR-017 pin and synthetic frames/timestamps. No event, outcome, analysis-TEST, holdout, experiment runner, or new-family path is added. The existing closed-family card changes one cost-guidance row only; status/evidence are untouched | PASS |
| Diff hygiene | Full dirty diff inspected; `git diff --check` clean | PASS |

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **37 passed**.
- Retained: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **208 passed, 4 skipped, 1 pre-existing NumPy warning**.
- Independent direct checks reproduced the frozen hash, all five pins, storage/adapter status split,
  both route policies, stress arithmetic, and exact funding boundaries.

### Disposition

No required fixes. The cost/data patch is ready for the operator to record the preflight exit.
Family registration and Run 1 remain separate operator decisions; TEST and holdout remain sealed.

### QA run 2 addendum — 2026-07-22T20:18:13Z — verdict correction

**Corrected verdict: REVISE**

The code, arithmetic, routing, compatibility, tests, and no-contact checks above remain passing.
The approval is withdrawn because a final source-language audit found an unresolved documentation-
truth issue in active guidance.

#### Required issue

1. **Warning — active guidance overstates the five INFR-017 values as executable or measured spreads.**
   - Source truth: `archive/chapter-04-nautilus-bybit-sigauc/experiments/INFR-017/results/column_pins.json:63-71` pins the flip-pair estimator as `VALIDATED_ON_SAMPLE_ONLY`, a **conservative upper bound, not the quoted spread**, because adjacent flips include real price movement; it was validated on only 20 symbol-days. `INFR-017/report.md:61-75` says this bias and scope must be labelled wherever used.
   - Correct Chapter-05 meaning: the five values are binding **conservative cost-floor proxies** for this fixed five-symbol programme. They are not historical BBO, quoted spread, per-episode realised spread, or execution measurements. `docs/references/architecture.md:128-129` already describes them as sample-validated proxies; the governing brief §6.2 carries the same caveat.
   - Overstatements: `docs/knowledge-base/evaluation-framework.md:199-213` says “audited executable-spread pins”; `docs/references/xena-lane.md:169-171` says the same; `docs/knowledge-base/families-explored.md:99` calls them executable; `docs/signal-registry/candidate-families/cf-sigauc-001.md:98,142` still says “measured spread”. `docs/knowledge-base/pitfalls-ledger.md:38` directs readers to audited quote/execution pins even though these INFR-017 values are neither.
   - Required fix (`experiment-documenter`): replace those claims with **audited conservative upper-bound cost-floor proxy**, state the 20-symbol-day validation scope, and explicitly exclude quoted/BBO, realised, and measured-execution interpretations. Keep “binding” only to mean the predeclared Chapter-05 accounting input. Align `dataset-reference.md` cost-read wording and `chapter-05-cost-data-preflight.md` pin table with that caveat so the usage site cannot be read as an execution measurement.
   - Regression: extend the active-guidance test to reject unqualified `executable-spread` / `measured spread` wording and require the conservative-upper-bound/sample-only caveat at the live cost guidance sites.

`FAILING_ARTIFACTS`: active cost guidance listed above. No implementation change is required.
After correction, rerun the focused documentation test and append a new fresh-context verdict.

## QA run 3 — 2026-07-22T20:20:43Z — mode: subagent — HEAD `839b4438da6a6ec524d4fd0e8805fba0af58bcd1`

**Reviewed dirty files:**

- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/chapter05-entry-gate.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (untracked; append-only review)
- `docs/references/chapter-05-cost-data-preflight.md` (untracked)
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/__init__.py`
- `python/src/xen/sigbar/access.py` (untracked)
- `python/src/xen/sigbar/data_types.py`
- `python/tests/test_chapter05_preflight.py` (untracked)
- `python/tests/test_evaluation.py`

**Verdict: REVISE**

The implementation, routing, storage compatibility, arithmetic, pin hash, no-contact boundary,
and all tests pass. Most terminology sites are corrected, including the two late-discovered lesson
files, but the requested disclosure is not yet present at every active instruction site.

### Terminology trace

| Active site | Required meaning | Evidence | Verdict |
|---|---|---|---|
| Main architecture | conservative upper-bound cost-floor proxy; not quoted/executable; 20 symbol-days | `docs/references/architecture.md:128-130` | PASS |
| Dataset usage example | same caveat beside current loader/cost use | `docs/references/dataset-reference.md:204-225` | PASS |
| Preflight pin table | binding means accounting input only; proxy caveat + scope | `docs/references/chapter-05-cost-data-preflight.md:22-40` | PASS |
| Quant-design instruction | proxy caveat + scope beside Chapter-05 use | `.agents/skills/quant-designer/references/design-requirements.md:154-158` | PASS |
| XENA/current routing reference | proxy caveat + scope beside loader use | `docs/references/xena-lane.md:169-171` | PASS |
| Closed-family replay guidance | conservative proxy, not quote, 20 symbol-days | `docs/signal-registry/candidate-families/cf-sigauc-001.md:96-98,142` | PASS |
| Durable KB summary/pitfall/lesson/memory | upper-bound proxy, not quote, 20 symbol-days | `docs/knowledge-base/families-explored.md:99`; `pitfalls-ledger.md:38`; `lessons-and-amendments.md:879-882`; `memory/spreadbps-unusable.md:6-10` | PASS |
| Evaluation framework current cost model | says audited conservative proxy and not a quote, but omits validation on only 20 symbol-days and does not expressly exclude executable/measured interpretation | `docs/knowledge-base/evaluation-framework.md:196-203,208-215` | **MISSING** |
| Active QA instruction | still calls the input “one audited non-negative spread pin” with no conservative-upper-bound, not-quoted/executable/measured, or 20-symbol-day qualification | `.agents/skills/qa-compliance/SKILL.md:71-76` | **MISSING** |
| Loader public docstring | identifies conservative cost-floor proxies, but omits upper-bound/not-quote and sample-only scope at the public seam | `python/src/xen/evaluation.py:418-419` | **PARTIAL** |

Historical statements that the bad stored `SpreadBps` was formerly called “measured spread,” or
headings saying it is “not executable spread,” are accurate retrospective warnings and are not
current-use overstatements.

### Required fix

1. Add the complete qualification — **conservative upper-bound cost-floor proxy; not quoted,
   executable, realised, or measured spread; validated on only 20 symbol-days** — to the evaluation
   framework's current model, the active QA instruction, and the loader's public docstring. Extend
   `test_live_cost_pin_guidance_discloses_proxy_scope` to cover those three sites so the disclosure
   cannot regress. The numerical pins and implementation must not change.

### Checks retained

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **48 passed**.
- Retained: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **219 passed, 4 skipped, 1 pre-existing NumPy warning**.
- `git diff --check` clean.
- Live gate remains `PREFLIGHT FINAL QA PENDING`; no family/checkpoint/outcome/TEST/holdout contact.

`FAILING_ARTIFACTS`: `docs/knowledge-base/evaluation-framework.md`,
`.agents/skills/qa-compliance/SKILL.md`, `python/src/xen/evaluation.py` docstring, and the focused
guidance-regression parameter list. No cost logic change is required.

## QA run 4 — 2026-07-22T20:22:21Z — mode: subagent — HEAD `839b4438da6a6ec524d4fd0e8805fba0af58bcd1`

**Reviewed dirty files:**

- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/chapter05-entry-gate.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (untracked; append-only review)
- `docs/references/chapter-05-cost-data-preflight.md` (untracked)
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/__init__.py`
- `python/src/xen/sigbar/access.py` (untracked)
- `python/src/xen/sigbar/data_types.py`
- `python/tests/test_chapter05_preflight.py` (untracked)
- `python/tests/test_evaluation.py`

**Verdict: APPROVE**

The three run-3 seams are corrected and regression-protected. All eight preflight clauses, prior
revision closures, proxy terminology, routing, compatibility, and test gates now pass. Approval
clears only the infrastructure preflight; family registration and Run 1 remain separate operator
decisions.

### Run-3 closure

| Prior seam | Evidence | Verdict |
|---|---|---|
| Evaluation framework | `docs/knowledge-base/evaluation-framework.md:196-204` states conservative upper bound, not quoted/executable or measured spread, validated on only 20 symbol-days; current cost stack remains audited proxy + discrete funding at `:209-215` | CLOSED |
| Active QA instruction | `.agents/skills/qa-compliance/SKILL.md:73-77` requires one cost-floor proxy and carries the complete upper-bound/non-spread/20-symbol-day qualification | CLOSED |
| Public loader seam | `python/src/xen/evaluation.py:418-423` states conservative upper bound, sample-only 20 symbol-days, neither executable nor measured spreads | CLOSED |
| Regression scope | `python/tests/test_chapter05_preflight.py:126-141` now covers preflight, architecture, dataset, evaluation framework, quant-design instruction, QA instruction, and public loader | CLOSED |

### Final verification

| Check | Evidence | Verdict |
|---|---|---|
| Every active current-use pin site | Global active-tree scan plus focused regression: main references, KB guidance, XENA/replay guidance, designer/QA skills, and loader describe conservative upper-bound cost-floor proxies; no unqualified current-use executable/measured-spread claim remains | PASS |
| Validation scope | Current-use instructions disclose validation on only 20 symbol-days; the pins are not historical BBO, quoted, realised, executable, or measured spreads | PASS |
| Stored-field quarantine | `SpreadBps` remains `UNUSABLE`; stored wire/version independently reproduce `sigbar-0.1.0 / UNUSABLE`; adapter exposes `UNUSABLE_AS_SPREAD` | PASS |
| INFR-017 integrity | Independent loader call reproduces self-hash `e3b9fd9b...e6225` and BTC/ETH/SOL/DOGE/XRP pins 0.244/0.305/0.727/1.477/1.965 | PASS |
| Chapter-05 route | Independent call with `secondary_available=False` returns `PARKED_T1_UNRESOLVED`, threshold 1.5 for gross 1.0 / proxy 0.5, and no T2 note | PASS |
| Cost/funding arithmetic | Prior independent stress and `(entry, exit]` boundary traces remain covered by the passing focused suite | PASS |
| Live gate / no contact | `docs/experiments-docs/INDEX.md:5-22` remains final-QA-pending with no family/checkpoint/run; no outcome, event census, analysis-TEST, or holdout contact was added | PASS |
| Diff hygiene | `git diff --check` clean | PASS |

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **51 passed**.
- Retained: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **222 passed, 4 skipped, 1 pre-existing NumPy warning**.

### Disposition

No required fixes. The operator may record the Chapter-05 cost/data preflight exit. This does not
register `CF-VOLCONV-001`, authorise Run 1, or unseal historical TEST or the global holdout.

## QA run 5 — 2026-07-22T20:25:38Z — mode: subagent — HEAD `839b4438da6a6ec524d4fd0e8805fba0af58bcd1`

**Reviewed dirty files:**

- `.claude/skills/qa-compliance/SKILL.md`
- `.claude/skills/quant-designer/references/design-requirements.md`
- `.claude/skills/research-pipeline/_pipeline-config.md`
- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/chapter05-entry-gate.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (untracked; append-only review)
- `docs/references/chapter-05-cost-data-preflight.md` (untracked)
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/__init__.py`
- `python/src/xen/sigbar/access.py` (untracked)
- `python/src/xen/sigbar/data_types.py`
- `python/tests/test_chapter05_preflight.py` (untracked)
- `python/tests/test_evaluation.py`

**Verdict: APPROVE**

The repository-hygiene correction is sound. Canonical tracked skill sources contain the approved
Chapter-05 governance, their generated mirrors are byte-identical, and regression tests read the
canonical paths that will exist in a clean checkout. Run-4's compliance verdict is unchanged.

### Canonical-source and mirror trace

| Check | Evidence | Verdict |
|---|---|---|
| Canonical ownership | `scripts/sync_skills.sh:2-27` declares `.claude/skills` canonical and mirrors generated; `git ls-files` confirms all three reviewed `.claude` files and the sync script are tracked | PASS |
| Mirrors ignored | `.gitignore:69` ignores `.agents/skills/`; equivalent generated mirror roots are sync targets, not review sources | PASS |
| QA skill parity | SHA-256 `bfe155b35514db939878a4c7eece0d6cd30f71451f204b5dfa3d579c848c6435`; canonical equals all eight mirrors | PASS |
| Quant-design parity | SHA-256 `edeeade92d41b6edfb95c8e7639e6f576a004a7f795ea69fd18b1d924625b40f`; canonical equals all eight mirrors | PASS |
| Pipeline-config parity | SHA-256 `4924570c2c5bdca696445bae3605cc4b28a6fc3b7b3c8901f6e82d7a2ec48005`; canonical equals all eight mirrors | PASS |
| Mirror set | `.agents`, `.cline`, `.codex`, `.cursor`, `.grok`, `.kilocode`, `.opencode`, `.windsurf` each pass `cmp` for all three files | PASS |
| Clean-checkout regression paths | `python/tests/test_chapter05_preflight.py:93-141` references tracked `.claude/skills/...` sources for obsolete-route and proxy-scope checks; no `.agents` test dependency remains | PASS |
| Canonical content | QA, quant-design, and pipeline sources carry the approved conservative-proxy, 20-symbol-day, no-T2, sealed-TEST/holdout boundaries | PASS |
| Current diff | New tracked skill changes match the already-approved mirrored content; no unrelated semantic change found | PASS |
| Diff hygiene | `git diff --check` clean | PASS |

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **51 passed**.
- Retained: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **222 passed, 4 skipped, 1 pre-existing NumPy warning**.

### Disposition

No required fixes. The canonical-source correction is clean-checkout safe, and the Chapter-05
cost/data preflight remains approved. Registration and execution remain separate operator gates.

## QA run 6 — 2026-07-22T20:55:29Z — mode: subagent — HEAD `16212e8bdc23e669cc61d2d5177d94a321a9befb`

**Reviewed dirty files (before this append):**

- `.claude/skills/qa-compliance/SKILL.md`
- `.claude/skills/quant-designer/references/design-requirements.md`
- `.claude/skills/research-pipeline/_pipeline-config.md`
- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight.md`
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/access.py`
- `python/tests/test_chapter05_preflight.py`
- `python/tests/test_evaluation.py`

**Verdict: REVISE**

The no-spread accounting implementation is correct and all tests pass, but one live Chapter-05
entry-gate memory still says the superseded proxy-era preflight is approved and registration is the
next action. The repository therefore gives contradictory instructions about whether research may
advance.

### Amendment-fidelity trace

| Requirement | Evidence | Verdict |
|---|---|---|
| Quarantine raw stored field | `python/src/xen/evaluation.py:412-438` verifies the frozen self-hash and `UNUSABLE` decision only; `python/src/xen/sigbar/access.py:16-36` exposes `MeanPriceSkewBps / UNUSABLE_AS_SPREAD`. Independent call reproduced self-hash `e3b9fd9b...e6225`; adapter retained values `[-0.25, 0.5]` under the quarantined name. | PASS |
| Remove the five flip-pair proxies from Chapter-05 accounting | `CHAPTER05_SPREAD_PINS_BPS` and `load_chapter05_cost_pins` are absent; the verifier returns only source/hash/status (`evaluation.py:434-438`). Tracked active-tree scan found no loader, five numerical pins, or flip-median cost use outside regression/history text. | PASS |
| Omitted-spread cost contract | `evaluation.py:494-564`: omitted spread returns `spread_rt_bps=None`, `UNAVAILABLE_NOT_CHARGED`, `PARTIAL_FEES_FUNDING_ONLY`; total is fee + funding; caveat states cost is understated and reported net performance overstated. Independent stress trace at 0.5/1/2 returned totals 5.75/11.5/23.0 bps with exact component reconciliation. | PASS |
| Historical explicit-spread compatibility | `evaluation.py:511-513,527-530` expressly limits explicit spread and continuous accrual to historical callers. Independent `spread_bps=0.244` trace retained stressed spread 0.122/0.244/0.488 and totals 5.872/11.744/23.488 bps at stress 0.5/1/2. It is labelled `EXPLICIT_INPUT_CHARGED / FULL_DECLARED_COMPONENTS`, not presented as Chapter-05 cost-complete evidence. | PASS |
| Governing ignored brief | `.ignore/what-next/alts/intraday-way-forward-plan.md:30-38,228-289,642-645` prohibits raw spread and replacements, specifies null/unavailable rather than zero, mandates the caveat, and seals historical TEST/holdout. | PASS |
| Tracked skills and primary gate docs | Canonical QA/design/pipeline instructions (`.claude/...`) and `chapter-05-{governance,cost-data-preflight}.md` require fees + discrete funding only, no proxy, the exact partial-cost fields, and no tradability claim. `docs/experiments-docs/INDEX.md:5-16` correctly leaves fresh QA pending. | PASS |
| Durable entry-gate memory | `docs/knowledge-base/memory/chapter05-entry-gate.md:3-5` still says fresh QA passed and the next gate is family registration, contradicting the current gate and governance. | **DEVIATES** |
| Research boundary | Diff changes no experiment artifact, outcome/result/data artifact, TEST-read ledger, multiplicity registry, holdout fence/artifact, checkpoint, or `CF-VOLCONV-001` family registration. The existing closed-family card edit changes cost guidance only. | PASS |

### Issue

1. **Warning — stale live gate.** Update `docs/knowledge-base/memory/chapter05-entry-gate.md:3-5`
   to say the no-spread amendment awaits fresh QA and that registration remains blocked. Add this
   memory file to the focused live-gate consistency regression so a passed preflight cannot remain
   cached while `docs/experiments-docs/INDEX.md` says QA is pending. Required owner: documentation /
   infrastructure patch; no accounting-code change is needed.

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **51 passed**.
- Full retained suite: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **222 passed, 4 skipped, 1 pre-existing NumPy warning**.
- `git diff --check 16212e8` → clean.

### Disposition

Keep the Chapter-05 gate blocked. Correct the stale memory and regression-protect it, then rerun
fresh-context QA. No family registration, outcome contact, historical TEST read, or holdout read is
authorised.

## QA run 7 — 2026-07-22T20:57:07Z — mode: subagent — HEAD `16212e8bdc23e669cc61d2d5177d94a321a9befb`

**Reviewed dirty files:**

- `.claude/skills/qa-compliance/SKILL.md`
- `.claude/skills/quant-designer/references/design-requirements.md`
- `.claude/skills/research-pipeline/_pipeline-config.md`
- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/chapter05-entry-gate.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (append-only QA output)
- `docs/references/chapter-05-cost-data-preflight.md`
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/access.py`
- `python/tests/test_chapter05_preflight.py`
- `python/tests/test_evaluation.py`

**Verdict: REVISE**

The stale memory text is corrected, and the implementation/test suites remain clean. The requested
regression protection is incomplete: the new parameter only subjects the memory to missing-spread
disclosure checks, not to the live-gate state that failed in run 6.

### Run-6 closure trace

| Run-6 requirement | Evidence | Verdict |
|---|---|---|
| Memory says amendment QA pending | `docs/knowledge-base/memory/chapter05-entry-gate.md:3` says it awaits fresh-context QA. | CLOSED |
| Registration remains blocked; no outcome exists | `chapter05-entry-gate.md:3-4` states both facts; `:5-7` makes registration conditional on later QA approval and preserves the SPDR→EXP/no-XENA/no-historical-TEST route. | CLOSED |
| Missing-spread disclosure | `chapter05-entry-gate.md:4-5` says unavailable/not charged, cost understated, and reported net performance overstated. | CLOSED |
| Memory included in focused regression | `python/tests/test_chapter05_preflight.py:120-138` includes the memory, but asserts only `spread cost unavailable`, `not charged`, `understates`, and absence of `load_chapter05_cost_pins`. It never asserts QA pending, registration blocked, no outcome, or absence of the superseded “preflight passed” state. | **PARTIAL** |
| Accounting and research boundaries | Run-6 accounting/quarantine/compatibility evidence is unchanged; no experiment, outcome/result/data, TEST-read ledger, holdout, checkpoint, or proposed-family registration artifact was added. | PASS |

### Issue

1. **Warning — gate-state regression remains unprotected.** Add a focused assertion for
   `docs/knowledge-base/memory/chapter05-entry-gate.md` that requires the amendment to await fresh
   QA, requires registration to remain blocked and no outcome to exist, and rejects the superseded
   “preflight passed” state (or directly checks consistency with `docs/experiments-docs/INDEX.md`).
   Merely adding the memory to the caveat parameter list cannot detect the run-6 failure mode.

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **52 passed**.
- Full retained suite: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **223 passed, 4 skipped, 1 pre-existing NumPy warning**.
- `git diff --check 16212e8` → clean.

### Disposition

Keep the Chapter-05 gate blocked until the live-gate state itself is regression-protected. No
accounting-code or memory-text change is otherwise required.

## QA run 8 — 2026-07-22T20:58:33Z — mode: subagent — HEAD `16212e8bdc23e669cc61d2d5177d94a321a9befb`

**Reviewed dirty files:**

- `.claude/skills/qa-compliance/SKILL.md`
- `.claude/skills/quant-designer/references/design-requirements.md`
- `.claude/skills/research-pipeline/_pipeline-config.md`
- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/chapter05-entry-gate.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (append-only QA output)
- `docs/references/chapter-05-cost-data-preflight.md`
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/access.py`
- `python/tests/test_chapter05_preflight.py`
- `python/tests/test_evaluation.py`

**Verdict: APPROVE**

The run-7 blocker is closed. The durable entry-gate memory now matches the live gate, and a focused
test directly protects every state phrase whose stale value caused run 6. The no-spread accounting,
quarantine, compatibility, and research-boundary findings from run 6 remain passing.

### Run-7 closure trace

| Requirement | Evidence | Verdict |
|---|---|---|
| Explicit pending state | `docs/knowledge-base/memory/chapter05-entry-gate.md:3` records `COST_AMENDMENT_QA_PENDING`; `:5` says fresh-context QA is still awaited. | CLOSED |
| Registration/outcome gate | `chapter05-entry-gate.md:5-6` states contiguous `family registration remains blocked` and `no outcome exists`; `:7-9` makes registration conditional on later approval and preserves the fixed route. | CLOSED |
| Missing-spread disclosure | `chapter05-entry-gate.md:6-7` states spread unavailable/not charged, cost understated, and reported net performance overstated. | CLOSED |
| Gate-state regression | `python/tests/test_chapter05_preflight.py:141-149` requires the pending status, blocked registration, and no-outcome text, and rejects `preflight passed`. This directly detects the run-6 failure shape rather than relying on the separate caveat test. | CLOSED |
| Full amendment | Prior independent traces remain unchanged: stored spread is quarantined, the five proxy pins/loader do not enter Chapter-05 costs, omitted spread returns the required partial-accounting fields and caveat, historical explicit-spread behavior is retained and labelled historical, and the ignored brief/tracked governance agree. | PASS |
| Research boundary | No experiment, outcome/result/data, historical TEST-read ledger, holdout, checkpoint, or `CF-VOLCONV-001` registration artifact is changed. | PASS |

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **53 passed**.
- Full retained suite: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **224 passed, 4 skipped, 1 pre-existing NumPy warning**.
- `git diff --check 16212e8` → clean.

### Disposition

The operator may record the no-spread cost/data preflight as QA-approved. This approval clears only
the infrastructure amendment; family registration, Run 1, outcome contact, historical TEST, and the
global holdout remain separately blocked or sealed until their explicit gates.

## QA run 9 — 2026-07-22T21:00:04Z — mode: subagent — HEAD `16212e8bdc23e669cc61d2d5177d94a321a9befb`

**Reviewed dirty files:**

- `.claude/skills/qa-compliance/SKILL.md`
- `.claude/skills/quant-designer/references/design-requirements.md`
- `.claude/skills/research-pipeline/_pipeline-config.md`
- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/chapter05-entry-gate.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (append-only QA output)
- `docs/references/chapter-05-cost-data-preflight.md`
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/access.py`
- `python/tests/test_chapter05_preflight.py`
- `python/tests/test_evaluation.py`

**Verdict: REVISE**

The main index, governance, and preflight record the approved exit correctly, and all tests pass.
One contradictory pre-approval sentence remains in the durable memory, so the post-approval state is
not yet internally exact.

### Gate-exit consistency trace

| Check | Evidence | Verdict |
|---|---|---|
| Live index | `docs/experiments-docs/INDEX.md:5-16` says preflight passed / amendment QA approved, family registration awaits separate authorisation, Run 1 remains unauthorised, and no research stage is active. | PASS |
| Governance | `docs/references/chapter-05-governance.md:3-11,27,55-60` records the passed amendment, no family/experiment/outcome, and the separate registration and Run-1 gates. | PASS |
| Preflight record | `docs/references/chapter-05-cost-data-preflight.md:3,52-58` records COMPLETE / QA APPROVED, 53 focused and 224 retained tests, and run-8 approval. | PASS |
| Durable memory state | `docs/knowledge-base/memory/chapter05-entry-gate.md:3,5-6` correctly records `PREFLIGHT_PASSED_AWAITING_FAMILY_REGISTRATION`, separate registration authorisation, and no outcome. | PASS |
| Durable memory next-step sentence | `chapter05-entry-gate.md:7-8` still says **“If QA approves, the next gate is”** even though `:3,5` says QA already passed. | **DEVIATES** |
| Regression fidelity | `python/tests/test_chapter05_preflight.py:141-149` enforces passed status, separate registration authorisation, no outcome, and absence of the pending-status token, but does not reject the stale `If QA approves` conditional. | **PARTIAL** |
| Research boundary | No family registration, Run 1, outcome/result/data artifact, historical TEST read, holdout read, or checkpoint was added. | PASS |

### Issue

1. **Warning — stale pre-approval conditional.** Replace `If QA approves, the next gate is` at
   `docs/knowledge-base/memory/chapter05-entry-gate.md:7` with an unconditional post-approval
   statement such as `The next gate is`. Extend the focused memory test to reject `If QA approves`
   so the exact post-approval state is protected.

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **53 passed**.
- Full retained suite: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **224 passed, 4 skipped, 1 pre-existing NumPy warning**.
- `git diff --check 16212e8` → clean.

### Disposition

The amendment itself remains technically approved, but the recorded gate exit needs the one-line
memory/test correction above before the final consistency review can APPROVE. Family registration
and all research/data gates remain untouched.

## QA run 10 — 2026-07-22T21:01:15Z — mode: subagent — HEAD `16212e8bdc23e669cc61d2d5177d94a321a9befb`

**Reviewed dirty files:**

- `.claude/skills/qa-compliance/SKILL.md`
- `.claude/skills/quant-designer/references/design-requirements.md`
- `.claude/skills/research-pipeline/_pipeline-config.md`
- `docs/experiments-docs/INDEX.md`
- `docs/knowledge-base/evaluation-framework.md`
- `docs/knowledge-base/families-explored.md`
- `docs/knowledge-base/lessons-and-amendments.md`
- `docs/knowledge-base/memory/chapter05-entry-gate.md`
- `docs/knowledge-base/memory/spreadbps-unusable.md`
- `docs/knowledge-base/pitfalls-ledger.md`
- `docs/references/architecture.md`
- `docs/references/chapter-05-cost-data-preflight-qa.md` (append-only QA output)
- `docs/references/chapter-05-cost-data-preflight.md`
- `docs/references/chapter-05-governance.md`
- `docs/references/dataset-reference.md`
- `docs/references/xena-lane.md`
- `docs/signal-registry/candidate-families/cf-sigauc-001.md`
- `python/src/xen/evaluation.py`
- `python/src/xen/sigbar/access.py`
- `python/tests/test_chapter05_preflight.py`
- `python/tests/test_evaluation.py`

**Verdict: APPROVE**

The final gate-exit record is internally consistent and regression-protected. The no-spread
amendment remains approved, while family registration and every research/data gate remain separate.

### Run-9 closure and final consistency

| Check | Evidence | Verdict |
|---|---|---|
| Stale conditional removed | `docs/knowledge-base/memory/chapter05-entry-gate.md:7-8` now states unconditionally, `The next gate is separate operator authorisation to register CF-VOLCONV-001`. | CLOSED |
| Exact post-approval state | `chapter05-entry-gate.md:3,5-9` records passed preflight, separate family-registration authorisation, no outcome, missing-spread caveat, SPDR→EXP route, no XENA/secondary rescue/historical TEST. | PASS |
| Regression protection | `python/tests/test_chapter05_preflight.py:141-150` requires passed status, separate authorisation, no outcome, rejects the pending token, and rejects `If QA approves`. | CLOSED |
| Cross-document consistency | Live index, governance, preflight, and memory all say amendment/preflight passed; family registration remains a separate operator gate; Run 1 remains unauthorised; no outcome exists. Active-doc scan found no pending-QA or stale conditional text outside append-only QA history. | PASS |
| No-spread amendment | Run-6/8 evidence remains unchanged: quarantine, no proxy pins/loader in Chapter-05 accounting, required partial-cost return fields/caveat, historical explicit-spread compatibility, ignored brief/tracked guidance alignment. | PASS |
| Research boundary | No family registration, Run 1, checkpoint, outcome/result/data, historical TEST read, or holdout read was added. | PASS |

### Test record

- Focused: `cd python && .venv/bin/pytest -q tests/test_evaluation.py tests/test_chapter05_preflight.py` → **53 passed**.
- Full retained suite: `cd python && PYTHONPATH=. .venv/bin/pytest -q` → **224 passed, 4 skipped, 1 pre-existing NumPy warning**.
- `git diff --check 16212e8` → clean.

### Disposition

The Chapter-05 no-spread cost/data preflight and its recorded exit are approved. The next permissible
step is a separate operator decision on family registration; this QA does not register the family,
authorise Run 1, or open outcomes, historical TEST, or the global holdout.
