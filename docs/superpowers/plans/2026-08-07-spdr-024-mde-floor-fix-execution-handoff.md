# SPDR-024 MDE / Detection-Floor Fix — Execution Handoff

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` for the
> main sequence. Use the Xen `research-pipeline` only at lifecycle boundaries that this
> handoff explicitly names. Use the Xen `data-analyst` in a **fresh context** for the final
> `analysis.md` only after the apparatus success criteria pass. Steps use checkbox
> (`- [ ]`) syntax so `/goal` can resume at the first unchecked item.

**Goal:** Correct the SPDR-024 detection-floor / MDE apparatus end-to-end (design → code →
tests → smoke → **one comprehensive Claude review gate** → purge of contaminated emission →
full four-cell re-run → re-analysis), so that power is honest context, not a silent second
test statistic, and so the experiment can be read without re-importing the five proven floor
defects.

**Architecture:** SPDR-024 remains one experiment with four cells
(`ctrader|crypto` × `H1|H4`), TRAIN-only, SIZE + selection channels on the fixed breakout
substrate. The fix is **apparatus**, not a new research grid: arms, components, devices,
domains, universes, PRIMARY estimand definition, and cost disclosure stay as already
designed. What changes is how floors, preflight power, and channel scales are *defined,
emitted, and talked about*.

**Tech stack:** Python 3.13, Polars, NumPy, pytest, Ruff, NautilusTrader, TRAIN catalog fence,
`xen.adaptive_management` (`spdr024*.py`, runner, integrity), experiment wrappers under
`python/experiments/SPDR-024/`.

**Execution authority:** Operator decision 2026-08-07 in  
`docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/mde-floor-defect-spdr024.md`
**§13** (with independent validation in **§12**). That authorises: design amendment for
remedies R1–R5, implementation, destructive purge of SPDR-024 generated artefacts, full
four-cell engine re-screen, full re-analysis, and replacement `analysis.md` / `screen.md`.  
It does **not** authorise: TEST/holdout contact, XENA, family-status change, arm ranking,
tradability, a hypothesis verdict, or a prose “rewalk” of the old emission in place of a
re-emission.

**Primary defect record (read before any edit):**

```text
docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/
  mde-floor-defect-spdr024.md
```

**Experiment pointer:** `python/experiments/SPDR-024/implementation-notes.md` §8.

---

## `/goal` execution contract

Use **this** document as the single execution ledger. The goal is complete only when Tasks
1–9 are checked and the final operator interpretation handoff is on disk. Do not stop between
tasks merely to ask permission when the next action is already covered here. Stop only at a
listed **stop condition**, an unsigned-amendment gate, a **failed Claude review gate
(Task 5)**, or a hard integrity failure.

Suggested goal objective:

```text
Execute docs/superpowers/plans/2026-08-07-spdr-024-mde-floor-fix-execution-handoff.md
from the first unchecked item through Tasks 1-9. Update the handoff after every completed
task, obey its gates and stop conditions, and finish only at the operator interpretation
handoff. Do not rewalk the pre-fix SPDR-024 emission. Do not purge or full-run until
Task 5 (Claude review) passes or the operator explicitly waives findings.
```

The executing agent must:

- begin by reading **this file**, `AGENTS.md` / `Agents.md`, the defect doc §0–§13, SPDR-024
  `design.md` (esp. §3, §8–§11, §15 ledger), and `implementation-notes.md` §6–§8;
- inspect the worktree before editing and preserve unrelated user changes (git status at
  conversation start may already show SPDR-024 and adaptive-management edits);
- update **this file** immediately after each completed task with observed tests, durations,
  paths, hashes, preflight labels, and any safe deviation;
- use TDD for every behavioral correction: focused failing test → observed failure → minimum
  fix → focused pass → regression pass;
- land **one coherent amendment (AMENDMENT-7)** covering R1–R5 — not a chain of mini-patches
  that restarts the amendment treadmill (see § *Amendment discipline*);
- run **exactly one** comprehensive Claude CLI review at Task 5 (after acceptance/smokes,
  **before** purge and full four-cell run); do not skip it; do not substitute a Grok-only
  review for this gate;
- purge only the explicit paths in Task 6; never glob the repo root;
- re-emit analysis only from the **post-purge** engine outputs;
- leave all value, power and significance reads **informative**; no result may gate another
  result; no power label may describe a row;
- make no commit, push, external publication or family-status change unless separately
  authorised.

The executing agent may make a small implementation adjustment without returning to the
operator only when **all** of these are true: it is required to satisfy a pass criterion
below; it does not change arms / populations / dates / estimand identity / cost scope; it has
a focused regression test; and it is recorded in this handoff. Any research-scope change
requires a further dated amendment and **stops**.

---

## Authoritative current state

### Complete and retained (do not re-litigate)

- [x] SPDR-024 design exists; SIZE-only device scope; eight components; four cells; TRAIN-only.
- [x] PRIMARY estimand is capital-normalised episode return (E6); per-notional bps diagnostic
  and barred from sizing claims.
- [x] Emission requirements E1–E6 (regime labels, counterfactual declines, capital-normalised
  outcome, etc.) are in the design; implementation largely present.
- [x] Gate-permutation control, regime-matched selection control, future-shift tripwire, three
  variance treatments V-A/V-B/V-C.
- [x] AMENDMENT-6 **withdrew result labels** from the analyser; population columns are
  first-class.
- [x] Defect document §12 independently **reproduced** the five floor defects against live
  artefacts and code (2026-08-07).
- [x] Operator decision §13 requires clean fix + purge + full re-emission (not a rewalk).

### Pre-fix emission (invalid for MDE-based interpretation)

The tree under `python/experiments/SPDR-024/results/` and the current `analysis.md` /
`screen.md` are the **pre-fix cycle**. Estimates, CIs, exposure/selectivity, and controls
remain *descriptively* interesting, but:

- `mde_sigma` / `mde_bps` / `contrast_over_mde` and preflight magnitude labels are **not**
  usable as resolve/unresolve;
- any narrative that “only crypto H1 can see anything” as a pure substrate power finding is
  **withdrawn** pending re-emission;
- Task 6 **deletes** this cycle only after Task 4 acceptance **and** Task 5 Claude review.

### Confirmed defects requiring amendment and re-emission

Source of truth: defect doc §2–§6; verdicts: §12.2 (all **PROVEN**).

| # | Defect (short) | What breaks in a reader’s hands |
|---|---|---|
| **D1** | For pure SIZE, σ̂ effect scale is ≈ baseline per-trade Sharpe × √gate (soft ceiling). Floor often sits **above** that scale. | “Below MDE” is often *impossible to clear*, not a measured null. |
| **D2** | Yardstick 0.022–0.150 is Step-3’s own **unresolved** point-estimate range. | Circular power bar; FULLY_RESOLVING/WASH logic was unreachable (labels now withdrawn; constants still poison informal reads). |
| **D3.1** | `MDE_Z=2.8` used as pass mark on realised \|est\|. | Silent bar stricter than the row’s own ~95% CI (11/17 CI≠0 demoted on governing PRIMARY POOLED). |
| **D3.2** | Floor = `2.8/√blocks`; ignores bootstrap SE on the same row. | Two uncertainty scales per row; parametric SE often optimistic ~20%. |
| **D4** | Scale σ̂ = sd(paired Δ); selection σ̂ = sd(outcome level); one numeric ladder. | Selection held 2.2–4.0× stricter in raw units; “0/96” is not a shared standard with scale. |
| **D5** | Preflight counts **orders**, gates on top of range (0.150); post-run uses fills + different story. | Cells “carry magnitude” then go blind; cTrader H4 exemplar 0.126 → 0.164. |

### Soft edges (do not reverse the defects; do not over-claim the fix)

- D1 is a **soft** ceiling: observed max can exceed simple `√gate × Sharpe` by ~1.5–2.8×
  (selectivity, continuous size > 1, per-symbol normalise-then-pool). Still: order of magnitude
  and floor-above-ceiling in 3/4 cells stand.
- Fixing the apparatus does **not** prove vol sizing works (D1 is symmetric).
- Engine lifecycle / fill identity are **not** the subject of this handoff unless a new HARD
  failure appears on re-run (then stop; do not mix scopes).

### Current repository cautions

- Worktree may already contain uncommitted SPDR-024 / adaptive-management changes from the
  pre-fix cycle and label withdrawal. Inspect before edit; do not discard unrelated work.
- `preflight.py` still imports symbols (`STEP3_OBSERVED_EFFECT_SIGMA`, `MIN_TRADES_FOR_POWER`)
  that the cleaned analyser no longer exports — **broken import contract** after AMENDMENT-6.
- Several design amendments (4–6) remain **UNSIGNED** in the ledger. This handoff’s AMENDMENT-7
  must either (a) fold their still-binding technical findings into one operator-ratifiable
  package, or (b) explicitly list which prior unsigned findings remain in force without
  reopening withdrawn band taxonomies.
- `analysis_code/da_*.py` may still contain legacy `WASH` / band helpers used only by
  exploratory scripts — must not re-enter the emission path.

---

## Amendment discipline (read twice — we are on amendment 6–7)

SPDR-024 has already accumulated a dense ledger (AMENDMENT-0…6), including post-review
corrections that **introduced** then **withdrew** resolution labels. That is the treadmill this
handoff exists to stop.

### Binding rules for AMENDMENT-7

1. **One amendment, five remedies.** R1–R5 land as a single dated ledger entry and a single
   coherent §10 (and related) rewrite. Do **not** ship R2 alone, re-analyse, then discover R4.
2. **No new result labels.** AMENDMENT-6 stands. Do not invent `CLEARS_FLOOR`,
   `DIRECTION_RESOLVED_*`, `FULLY_RESOLVING`, or any synonym that classifies a row by power.
3. **Direction accounting (L-23).** Record LOOSER / TIGHTER / NEUTRAL honestly. Expected shape:
   TIGHTER on honesty of power and preflight; NEUTRAL on strategy admission and arm grid. A
   one-directional streak of 3 triggers an **operator flag** before execution (design ledger
   rule).
4. **No silent code patch under stale design text.** If the code computes floors from bootstrap
   SE, the design must say so *before* production re-run.
5. **Unsigned backlog hygiene.** In Task 1, state explicitly for AMENDMENT-4, -5, -6:
   - what is **retained** (e.g. unit-capital PRIMARY reading; admission-at-fill; no result labels;
     population columns);
   - what is **superseded** (any remaining use of 0.022/0.150 as gate or resolve ladder;
     `2.8/√n` as row floor; band taxonomy from A5).
6. **Stop condition:** if the implementer finds a sixth independent power defect mid-flight,
   **stop and amend once** — do not accumulate another three unsigned patches.

### Forbidden “fixes” (these recreate the same class of bug)

| Forbidden | Why |
|---|---|
| Keep `mde = 2.8/√blocks` but only “document that it’s approximate” | D3.2 remains |
| Compare estimate to MDE for “resolved” language in `analysis.md` | D3.1 re-enters by prose |
| Reintroduce Step-3 0.022–0.150 as preflight or FULLY_RESOLVING bar | D2 |
| Share one σ̂ ladder across scale and selection without declaring denominators | D4 |
| Preflight on orders with a footnote that fills are lower | D5 (already did this) |
| Lower `MDE_Z` to 1.96 to “match the CI” without unifying SE | Cosmetic; still dual SE if blocks≠bootstrap |
| Analysis-only reprocess of **old** engine runs after changing preflight admission rules, then claim full re-emission | Contaminates provenance |
| Partial purge (keep `results/runs/`, only delete analysis) when §13 requires full purge | Violates operator decision |
| Prose rewalk / CI-only narrative as disposition of D1–D5 | Explicitly rejected §13.1 |
| New arms, new devices, cost charging, TEST band “while we’re here” | Scope creep; separate decision |

---

## Binding constraints

### Research / fence

- **TRAIN only.** Never load TEST or the global holdout.
- Decisions use information available by `t-1`; Nautilus event-driven execution retained.
- Four cells, never pooled across universe or domain.
- Eight components; SIZE only (continuous where defined + `STATE_HALVE_HIGH`); no REVERSE;
  no hold/stop/target/trail devices as arms.
- PRIMARY: capital-normalised episode return; paired adaptive−fixed on common-closed for scale;
  selection on origin lens vs declined counterfactuals (E2); admission at **stop fill**.
- No spread charged: keep disclosure block and prohibited claims.
- No `SUPPORTED` / `REFUTED` / winner / deployability / universal-effect labels.
- Power is **context only** (`adaptive-management-design.md` §1 / §9).
- All strata stay visible; no top-N pruning; no dropping rows for low n or high MDE.

### Apparatus (this fix)

- **R1** — Mechanism-derived SIZE ceiling per cell from baseline-only quantities; retire
  0.022/0.150 as gate/yardstick (historical context only).
- **R2** — Row floor from **same SE family as the CI** (bootstrap / clustered interval SE), not
  free-standing `2.8/√blocks`.
- **R3** — `MDE_Z=2.8` is for **planning next sample size**, not for classifying realised
  estimates. Emit estimate, CI, counts, effective counts; optional est/SE as context; **no**
  clears-floor label.
- **R4** — Scale and selection: declared separate scales **or** both in raw bps with one stated
  dispersion. Never one silent dual-σ̂ ladder.
- **R5** — Preflight counts **fills** (or fill-rate-adjusted orders labelled provisional) and
  uses the **same endpoint** as post-run descriptive/power context (R1). Optimistic upper bound
  must not return “carries magnitude.”

### What must not change without a new operator decision

- Arm lattice, component set, universes, domains, TRAIN fence, cost scope.
- Gate-permutation and future-shift as integrity/informative controls (may need wording so
  tripwire does not re-import MDE-as-pass-mark incorrectly — see Task 2 stop note).
- Determinism / HARD check inventory discipline (P-23): count and names asserted.

---

## Performance and reliability standard

Preserve SPDR-024 / adaptive-management lessons already paid for (L-54 / P-26 and SPDR-021–023
handoff standards):

- Prefer sequential cells; default engine `--jobs` only as already validated for this host.
- Do not run integrity or analysis beside a live engine cell on a memory-tight host.
- Atomic publication; hash-valid resume only; never treat partial units as complete.
- No “faster” change that alters fences, seeds, bootstrap draws, arm sets, or numeric schemas
  without parity proof.

A new optimisation during this plan is allowed only if:

1. it does not alter fences, dates, origins, arms, scheduling, engine event order, bootstrap
   draws, metrics, or row identity of non-floor fields;
2. focused tests cover the floor contract and label ban;
3. wall time / memory deltas are recorded here;
4. the simpler safe route is preferred when the gain is not material.

**Explicitly prohibited:** fewer bootstrap draws, altered seeds, dropped symbols/dates, arm
pruning, charging spread “to see,” or skipping future-shift / determinism phases.

---

## Final pass matrix

| Gate | Required evidence | Pass criterion |
| --- | --- | --- |
| Defect lock | defect doc §12 | All five defects graded; no economic verdict |
| Design AMENDMENT-7 | `design.md` §10/§11/§15 | R1–R5 text exact; no result labels; L-23 recorded; prior A4–A6 hygiene stated |
| Floor contract tests | pytest | Floor uses CI-consistent SE; `2.8/√n` not row floor; no label columns |
| Channel scale | design + tests + emitted columns | Scale vs selection denominators declared; no silent shared ladder |
| Preflight | new `preflight/*.json` after purge | Fill-based (or labelled provisional); endpoint = R1; no 0.022/0.150 gate |
| Acceptance + smoke | Task 4 | Focused suite green; design↔code R1–R5 map; resource margin; smoke pass |
| **Claude review gate** | Task 5 report on disk | Comprehensive adversarial review; blocking findings fixed or operator-waived; **no purge/full-run until clear** |
| Purge | path list + search | No live pre-fix `mde_sigma` / analysis.md from old cycle |
| Production cell | selfcheck + estimand | `blocking_pass=true`; HARD inventory complete by name |
| Analysis emission | parquet + summary | Floors coherent with CIs; no power labels; populations named |
| Documents | `analysis.md` / `screen.md` | Fresh-context analyst; no \|est\|≥MDE resolve rule; gross disclosure |
| Closeout | this handoff Tasks 1–9 | All boxes checked; operator interpretation gate only |

---

## Task 1: Design amendment (AMENDMENT-7) — R1–R5 in one shot

**Files:**

- Modify: `python/experiments/SPDR-024/design.md` (§10 power, §11 reporting, §15 ledger; cross-links §3 if needed for selectivity/exposure reminder)
- Modify: `python/experiments/SPDR-024/implementation-notes.md` (pointer + what A7 supersedes)
- Modify if needed: defect doc only to add “execution handoff path” one-liner (optional)
- Create/update this handoff’s completion evidence

**Produces:** a single operator-ratifiable amendment. **Stop after this task if the operator has
not yet said AMENDMENT-7 may execute** (unsigned design must not silently drive production
purge). If the operator’s §13 decision is treated as pre-authorisation of the *content* of R1–R5,
still land the text and mark “authorised by §13 / 2026-08-07” explicitly in the ledger.

- [ ] **Step 1: Freeze the problem statement into the design ledger**

In AMENDMENT-7 basis, cite defect doc path and §12 verdicts (D1–D5 **PROVEN**). State that the
pre-fix emission is invalid for MDE-based resolution claims and that rewalk is refused.

Pass: no economic verdict; no arm change.

- [ ] **Step 2: Rewrite power (§10) for R1, R2, R3, R5**

Required declarations (use exact formulae in design; implementer may not invent siblings):

```text
SIZE_MECHANISM_CEILING (per cell, baseline-only):
  sharpe_per_trade := |gross_mean_bps| / gross_sigma_bps
  ceiling_sigma(p) := sqrt(p) * sharpe_per_trade
  # p = design gate rate for planning; report realised gate rates beside estimates
  # soft ceiling: selectivity / continuous size may exceed; still the planning scale

ROW_FLOOR (if mde_* columns remain):
  SE := SE of the same estimator as the CI on that row
       (e.g. bootstrap SE, or (ci_high - ci_low) / (2 * z_0.975) only if documented
        as an interval-implied SE and used consistently)
  mde := MDE_Z * SE
  FORBIDDEN: mde := MDE_Z / sqrt(effective_blocks) as the row floor

MDE_Z := 2.8
  USE: sample-size planning for future designs / preflight descriptive capacity
  DO NOT USE: pass mark on realised |estimate|

PREFLIGHT M2:
  n_basis := FILLS (preferred) or orders * measured_fill_rate with
             count_basis labelled PROVISIONAL_FILL_RATE_ADJUSTED
  endpoint := mechanism ceiling / descriptive rule from R1 (same as post-run context)
  FORBIDDEN: gate on STEP3 0.022 or 0.150
  FORBIDDEN: CARRIES_MAGNITUDE on pure order counts while noting optimism
```

Pass: a reader can implement floors without opening the defect doc.

- [ ] **Step 3: Rewrite reporting (§11) for R3 + R4 + AMENDMENT-6 preservation**

```text
EVERY ROW:
  estimate, CI (all three treatments; governing = most conservative by fewest blocks /
  highest coherent floor under R2), population counts, effective counts
  optional: mde from R2, est/SE, exposure/selectivity terms, control fields

NEVER:
  band, resolution_class, WASH, UNPOWERED, NOT_RESOLVABLE_*, DIRECTION_RESOLVED_*,
  SUPPORTED, CONTRADICTED, or prose that means the same

CHANNELS:
  SCALE: state that sigma-hat is sd of the paired difference (or raw capital-normalised
         delta with stated sigma)
  SELECTION: state that contrasts are in bps (or their own declared sigma); do not claim
             the same numeric 0.022–0.150 ladder
  If both reported in sigma-hat, each row names its denominator object in a column
```

- [ ] **Step 4: Hygiene for AMENDMENT-4/5/6**

Write a short “still in force / superseded” table in the ledger:

| Prior | In force | Superseded |
|---|---|---|
| A4 unit-capital PRIMARY | yes (if still implemented) | — |
| A5 admission-at-fill; selection floor vs block treatment alignment intent | yes (fill identity; coherent SE) | resolution ladder / band names |
| A6 no result labels; seven populations | yes | any residual Step-3 range as resolve bar |

- [ ] **Step 5: L-23 and unsigned status**

Compute running looser/tighter/neutral counts. Flag if streak of 3. Mark AMENDMENT-7
**SIGNED by operator decision §13** or leave UNSIGNED with explicit stop before Task 6 (purge).

**Task 1 complete when:** design text alone is implementable; checklist of R1–R5 maps 1:1 to
Task 2–3 tests; no new labels; grid unchanged.

---

## Task 2: Implement floor contract, channel scale honesty, label ban (analyser)

**Files:**

- Modify: `python/src/xen/adaptive_management/spdr024_analysis.py`
- Modify: `python/tests/test_spdr024.py` (and/or new focused test module)
- Modify only if required for column contracts: `python/experiments/SPDR-024/analysis_code/analyse.py`
- Audit: `python/experiments/SPDR-024/analysis_code/da_*.py` — must not be on the emission path
  with band labels; fix or quarantine

**Interface:** every emitted scale/selection row either has no `mde_*` or has `mde_*` derived
under R2; never `MDE_Z/sqrt(blocks)` as floor; never label columns; selection and scale document
denominator.

- [ ] **Step 1: Failing tests for D3.2 / R2**

Assert for a synthetic series with known bootstrap width:

```python
# Pseudocode — adapt to project fixtures
assert mde_sigma == pytest.approx(MDE_Z * bootstrap_se, rel=1e-6)
assert mde_sigma != pytest.approx(MDE_Z / sqrt(n_blocks), rel=1e-3)  # when SE ≠ 1/√n
```

Also assert CI bounds and floor use the same treatment’s draws / SE.

Pass of this step: tests **fail** on current `:392`-style implementation.

- [ ] **Step 2: Failing tests for label ban (A6 lock)**

Emission frames must not contain columns matching:

```text
band, governing_band, component_specific_band, resolution_class,
step3_*, floor_over_*, *_band
```

(Exact denylist as already used in tests if present; extend if needed.)

- [ ] **Step 3: Failing tests for R4**

Either:

- selection estimates expose `sigma_denominator = "outcome_level_bps"` and scale exposes
  `sigma_denominator = "paired_delta"` (or equivalent), **or**
- selection is reported only in bps with `mde_bps` and no pretence of shared σ̂ ladder with scale.

- [ ] **Step 4: Minimum implementation**

- Replace row floor construction with R2.
- Remove or repurpose `STEP3_OBSERVED_EFFECT_SIGMA_MIN/MAX` so nothing in code **gates** on them
  (analysis_summary may still mention historical Step-3 range as **non-gating context** only if
  design allows — prefer dropping from summary to reduce misuse).
- Keep exposure/selectivity decomposition and gate-permutation.
- **Tripwire care:** future-shift HARD criterion must not reintroduce “collapse into MDE” as a
  stricter pass than design §9 REJECT (surviving edge = shifted outperforms causal beyond noise).
  If current code uses `mde_sigma` for bite notes, redefine bite using the **same SE family as CI**
  or design-stated noise rule; record the choice here. Do not fail a cell for non-collapse into
  an incoherent floor (see implementation-notes §6.3 lesson).

- [ ] **Step 5: Verify**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest tests/test_spdr024.py -q
# plus any new test file
.venv/bin/ruff check src/xen/adaptive_management/spdr024_analysis.py tests/test_spdr024.py
```

Pass: zero failures; denylist holds; floor≠`2.8/√n` when bootstrap SE differs.

---

## Task 3: Preflight R1 + R5

**Files:**

- Modify: `python/experiments/SPDR-024/screen_code/preflight.py`
- Modify: shared constants only via `spdr024_analysis.py` exports that actually exist
- Tests: extend `tests/test_spdr024.py` or preflight-focused tests with fixtures

- [ ] **Step 1: Failing tests**

- Import of preflight module succeeds (currently at risk after A6 symbol removal).
- Preflight `n` basis is fills or explicitly provisional fill-rate-adjusted; never silent orders.
- Power / descriptive label uses R1 ceiling comparison, not `mde > 0.150`.
- A synthetic cell with floor > mechanism ceiling is marked DESCRIPTIVE / cannot resolve SIZE
  magnitude (exact string frozen in design).

- [ ] **Step 2: Implement**

- Fix imports.
- Compute baseline mean/σ and mechanism ceiling from TRAIN baseline characterisation path the
  preflight already can see (or document a baseline-only micro-pass if required — **no full arm
  lattice** for this).
- Align endpoint with post-run context fields written into preflight JSON.

- [ ] **Step 3: Verify**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest tests/test_spdr024.py -q  # or targeted preflight tests
.venv/bin/ruff check experiments/SPDR-024/screen_code/preflight.py
```

---

## Task 4: Acceptance checks and smoke (before Claude gate and purge)

**Do not delete results, and do not start the full four-cell run, until Tasks 4 and 5 both pass.**

- [ ] **Step 1: Full focused suite**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest tests/test_spdr024.py tests/test_adaptive_management_*.py -q
.venv/bin/ruff check src/xen/adaptive_management experiments/SPDR-024
git diff --check
```

Record exact pass counts.

- [ ] **Step 2: Golden / self-check contract**

Run whatever SPDR-024 golden traces and unit-level selfcheck pieces can run **without** the old
results tree if possible; otherwise schedule full selfcheck post-re-run in Task 7. At minimum:
tests that encode HARD inventory count expectations still pass.

- [ ] **Step 3: Design↔code checklist**

One row per R1–R5 with: design clause, code symbol, test name. All checked.

- [ ] **Step 4: Bounded smoke (not a production cell)**

Run the lightest real or synthetic smoke that exercises the **new floor contract and preflight
path** without a full four-cell lattice. Prefer:

- existing SPDR-024 golden traces / unit engine fixtures if they cover capital-normalised SIZE
  deltas and analysis helpers; and/or
- a **single-symbol or synthetic** analysis-path smoke that emits one scale row + one selection
  row and asserts R2 floor coherence + no label columns.

Record command, duration, and pass/fail here. This is not a substitute for Task 7.

- [ ] **Step 5: Resource preflight (pre-deletion)**

Record free disk, predicted SPDR-024 four-cell output size (use prior cycle sizes as prior:
crypto cells dominate), and host memory policy. Require predicted + 25% free or stop for
operator.

**Stop condition:** any R1–R5 without a test; any label column found; design still describing
`2.8/√n` as the row floor; smoke failed.

**Task 4 complete when:** suite + checklist + smoke + resource margin are green. **Next is
Task 5 (Claude), not purge.**

---

## Task 5: Comprehensive Claude review gate (mandatory — before purge / full run)

**Purpose:** One adversarial, comprehensive review of the **apparatus fix** after automated
checks and smokes, **before** destructive purge and the expensive four-cell re-screen. Catches
amendment treadmill regressions (new labels, dual SE, order-count preflight, silent Step-3
yardstick) that unit tests can miss in prose/design coupling.

**Authority:** Operator-requested gate, 2026-08-07. Operator confirms Claude CLI is configured
on this host. **Do not skip. Do not replace with a Grok-only review.** A second Claude pass is
allowed **only** to re-review after fixing blocking findings from this gate — not as a routine
double-spend.

**When:** Immediately after Task 4. **Before** Task 6 purge and Task 7 full run.

**Mode:** Non-interactive Claude Code via `claude -p` / `--print`. Prefer **read-only** tool
allowlist (Read, Grep, Glob — no Edit/Write to production sources during the review itself).
The orchestrating agent applies any fixes after the report.

**Output path (create parent dirs):**

```text
docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.md
```

Also paste a short verdict + blocking-finding count into this handoff’s completion log.

- [ ] **Step 1: Assemble the review brief (orchestrator)**

Write a short ephemeral brief (or pass inline) that **requires** Claude to read and use:

```text
PRIMARY DEFECT RECORD:
  docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/
    mde-floor-defect-spdr024.md
  — especially §2–§6 (defects), §10 (R1–R5), §12 (validation), §13 (operator decision)

THIS HANDOFF:
  docs/superpowers/plans/2026-08-07-spdr-024-mde-floor-fix-execution-handoff.md
  — Amendment discipline, forbidden fixes, Tasks 1–4 completion evidence

DESIGN + NOTES:
  python/experiments/SPDR-024/design.md          (§10, §11, §15 AMENDMENT-7)
  python/experiments/SPDR-024/implementation-notes.md

IMPLEMENTATION (post-Task-2/3):
  python/src/xen/adaptive_management/spdr024_analysis.py
  python/experiments/SPDR-024/screen_code/preflight.py
  python/tests/test_spdr024.py
  (and any new test files from Tasks 2–3)
```

- [ ] **Step 2: Run one comprehensive Claude review**

From repo root (adjust flags only if the host’s Claude config requires it; do not weaken the
review scope):

```bash
mkdir -p docs/superpowers/plans/reviews

claude -p "$(cat <<'PROMPT'
You are performing a single comprehensive pre-production review of the SPDR-024 MDE / detection-floor fix, immediately before artefact purge and a full four-cell TRAIN re-run.

Read and ground every finding in:
1) docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/mde-floor-defect-spdr024.md (§2–§6 defects D1–D5, §10 remedies R1–R5, §12 validation, §13 operator decision)
2) docs/superpowers/plans/2026-08-07-spdr-024-mde-floor-fix-execution-handoff.md (amendment discipline + forbidden fixes)
3) python/experiments/SPDR-024/design.md (AMENDMENT-7 / §10 / §11 / §15)
4) python/experiments/SPDR-024/implementation-notes.md
5) python/src/xen/adaptive_management/spdr024_analysis.py
6) python/experiments/SPDR-024/screen_code/preflight.py
7) python/tests/test_spdr024.py and related new tests

Mission: determine whether the implemented apparatus fix actually closes D1–D5 / R1–R5 without reintroducing the amendment treadmill (result labels, 2.8/√n row floors, Step-3 0.022–0.150 gates, order-count preflight magnitude passes, silent dual-σ̂ ladders, |est|≥MDE resolve language).

Review dimensions (cover all):
A. Design↔code fidelity for R1–R5 (missing clause, contradictory formula, unsigned/stale text)
B. Floor construction: same SE family as CI? any remaining MDE_Z/sqrt(blocks) as row floor?
C. Label ban: any band/resolution/WASH/UNPOWERED/clears-floor classification in emission or likely analysis prose hooks?
D. Preflight: fills (or explicit provisional fill-rate); same endpoint as post-run; no 0.150/0.022 gate
E. Channel honesty (scale vs selection denominators)
F. Tripwire / integrity interaction: does future-shift HARD criterion abuse incoherent MDE?
G. Tests: are defects locked by failing-first tests, or only documented?
H. Scope creep: arms/grid/cost/TEST/estimand identity changed?
I. Amendment discipline: one coherent A7 or patch chain? L-23 risks?
J. Residual risk for full re-run: what could still poison analysis.md after re-emission?

Output format (markdown file body):
# SPDR-024 MDE floor fix — Claude pre-run review
## Verdict
ONE of: READY_FOR_PURGE_AND_FULL_RUN | FIX_THEN_RE_REVIEW | BLOCKED_NEEDS_OPERATOR
## Executive summary
≤12 short lines, plain language, no hypothesis verdict on vol sizing
## Blocking findings
For each: id, severity BLOCKING, path/symbol, defect (D#/R#) if any, problem, required fix
## Non-blocking findings
Same shape, severity NON_BLOCKING or NIT
## Defect coverage matrix
Row per D1–D5 and R1–R5: ADDRESSED / PARTIAL / MISSING with one-line evidence
## Explicit non-findings
What you checked that looked clean
## Recommendation
Whether to proceed to purge + four-cell run

Rules:
- No experiment hypothesis verdict; no arm ranking; no tradability
- Do not edit production files in this session; report only
- Prefer evidence (file:line / symbol) over vibe
- If information is missing, say what is missing — do not invent pass
PROMPT
)" \
  --allowedTools "Read,Grep,Glob" \
  > docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.md
```

If the CLI requires different permission flags on this host, use the operator’s configured
equivalent **without** granting Edit/Write to `python/src` or experiment design during the
review process. Capture exit code and wall time in this handoff.

- [ ] **Step 3: Triage findings (orchestrator)**

| Verdict / finding class | Action |
|---|---|
| `READY_FOR_PURGE_AND_FULL_RUN` and zero BLOCKING | Proceed to Task 6 |
| BLOCKING findings | Fix with TDD (Tasks 2–4 as needed); re-run **only** the focused tests for the fix; optional **one** Claude re-review (same prompt + “delta since last review”); then continue |
| `BLOCKED_NEEDS_OPERATOR` or design-scope change | **Stop**; do not purge |
| NON_BLOCKING only | Record in handoff; may proceed unless operator previously required zero nits |

Do **not** start Task 6 while any BLOCKING item is open.

- [ ] **Step 4: Record gate evidence in this handoff**

Write: review file path, Claude exit code, wall seconds, verdict, blocking count, fix summary
(if any), and final gate status `CLEARED` / `STOPPED`.

**Task 5 complete when:** review artefact exists on disk, blocking findings are cleared or
operator-waived in writing in this handoff, gate status is `CLEARED`.

---

## Task 6: Hard-remove pre-fix artefacts

Destructive; authorised by defect doc §13. **Requires Task 5 gate `CLEARED`.** Resolve and print
every target **before** deletion. Never use a bare `rm -rf` on a path not listed. Never delete
`design.md`, `implementation-notes.md`, `screen_code/`, `analysis_code/`, the defect document, or
the Claude review under `docs/superpowers/plans/reviews/`.

**Delete only:**

```text
python/experiments/SPDR-024/results/
python/experiments/SPDR-024/analysis.md
python/experiments/SPDR-024/screen.md
python/experiments/SPDR-024/plots/          # if present and generated
```

If `results/` is a symlink, **stop** and report; do not follow into foreign trees.

- [ ] **Step 1: Inventory**

```bash
# from repo root — record sizes and that paths exist / are directories
ls -la python/experiments/SPDR-024/
du -sh python/experiments/SPDR-024/results python/experiments/SPDR-024/plots 2>/dev/null
```

Write the listing into this handoff.

- [ ] **Step 2: Delete and verify absence**

Delete only the listed targets. Verify each is gone. Record space recovered.

- [ ] **Step 3: Decontamination search**

```bash
# Live experiment folder should not still present old analysis claims as current artefacts
rg -n "mde_sigma|CARRIES_MAGNITUDE_QUESTION|NOT_RESOLVABLE_AT_THIS_FLOOR" \
  python/experiments/SPDR-024 --glob '!**/.git/**'
```

Pass: matches only in `design.md` / `implementation-notes.md` / code comments / tests as
*historical or forbidden*, not in live `results/` or current `analysis.md`. Defect doc and this
handoff may still discuss the defects.

- [ ] **Step 4: Re-measure free disk**

Record post-deletion free space before Task 7.

---

## Task 7: Full four-cell engine re-screen

**Order (cheap cells first):**

```text
ctrader_H1 -> ctrader_H4 -> crypto_H1 -> crypto_H4
```

Use `python/experiments/SPDR-024/screen_code/run_cell.py` (or the documented equivalent) so
hold → cap rule → full → shift → replay → selfcheck → analysis wiring stays in design order.
Prefer not to prune shift/replay (`--prune` off) so tripwire/determinism remain re-checkable.

- [ ] **Step 1: Preflight all four cells under new gate**

Write `results/preflight/<cell>.json`. Record per cell: n basis, fill counts, mechanism ceiling,
most conservative floor, descriptive label. **No cell may show order-only magnitude-carrying pass.**

If preflight marks a cell DESCRIPTIVE for SIZE magnitude: still follow design on whether the cell
**runs** (breadth vs blind breadth). Design must already say; if DESCRIPTIVE means “run but do not
claim magnitude,” run it; if DESCRIPTIVE means “do not spend engine budget,” skip only if design
explicitly allows and record here. Default under §13: **run all four** unless design forbids.

- [ ] **Step 2: Execute cells sequentially**

For each cell, record: wall time, peak RSS if available, output size, jobs, blocking selfcheck,
estimand validation, future-shift summary (survivors, bite notes without incoherent floor abuse).

Pass per cell: HARD inventory complete; `blocking_pass=true`; determinism policy satisfied.

- [ ] **Step 3: Fail closed**

A failing cell is fixed under this amendment’s scope or stopped for operator. It is never
“interpreted” as an economic observation. Do not launch the next cell’s analysis on a failed
selfcheck.

---

## Task 8: Full re-analysis and document replacement

- [ ] **Step 1: Emit analysis artefacts for all four cells**

Via `run_cell` tail or `analysis_code/analyse.py` as designed. Confirm:

- `mde_*` obey R2 if present;
- no label columns;
- scale/selection denominator fields or raw-bps honesty (R4);
- populations null-correct.

- [ ] **Step 2: Independent analysis document (fresh context)**

Invoke Xen `data-analyst` (or equivalent fresh-context discipline) to write
`python/experiments/SPDR-024/analysis.md`:

- TRAIN only; gross disclosure; no verdict;
- estimate + CI + counts + effective counts; power as context;
- **forbidden:** resolve/unresolve by \|est\|≥MDE; WASH/UNPOWERED language; tradability;
- use exposure/selectivity and gate-permutation for component claims;
- selection discussed in its declared units, not a fake shared σ̂ ladder.

- [ ] **Step 3: Replace `screen.md`**

Screen summary from new selfcheck/preflight/performance only.

- [ ] **Step 4: Dual-pass or hash note**

If the project standard requires two analysis passes with matching hashes, do so and record
manifest path. If not required for SPDR-024, state that explicitly and still keep deterministic
seeds.

- [ ] **Step 5: implementation-notes**

Record: pre-fix emission superseded; cite defect doc §12–§13 and this handoff; note AMENDMENT-7
in force; link Claude review path from Task 5.

---

## Task 9: Closeout and operator interpretation handoff

- [ ] **Step 1: Apparatus success criteria (defect doc §13.5)**

Check all six bullets; paste evidence paths into this handoff.

- [ ] **Step 2: Boundary search**

```bash
rg -n "SUPPORTED|REFUTED|WASH|UNPOWERED|NOT_RESOLVABLE|deployable|CARRIES_MAGNITUDE" \
  python/experiments/SPDR-024/analysis.md python/experiments/SPDR-024/screen.md \
  python/experiments/SPDR-024/results/analysis || true
```

Pass: no forbidden result labels in live analysis artefacts; preflight labels only as design-frozen
descriptive vocabulary if still used.

- [ ] **Step 3: Final regression**

```bash
cd python
PYTHONPATH=. .venv/bin/pytest tests/test_spdr024.py -q
```

- [ ] **Step 4: Operator handoff blurb (write at end of this file)**

Include: what changed in the apparatus; what did not change in the grid; where new results live;
path to Claude pre-run review; explicit reminder that hypothesis interpretation is the operator’s;
no family action taken.

---

## Stop conditions (mandatory)

Stop and return to the operator if any of:

1. AMENDMENT-7 would change arms, devices, cost scope, or TRAIN fence.
2. A sixth independent power/estimand defect appears that cannot fit R1–R5 without a new remedy.
3. L-23 one-directional streak of 3 without operator flag clearance.
4. Purge path resolves outside the Task 6 list or is a symlink to a shared volume.
5. Engine HARD failure that is **not** explained by floor apparatus (lifecycle, fence, determinism).
6. Host cannot meet disk/memory margin for four cells.
7. Pressure to “just rewalk” or “analysis-only on old runs” as substitute for Task 6–8.
8. Request to open TEST/holdout or issue a family/XENA verdict.
9. Task 5 Claude review missing, failed to run, or still has open **BLOCKING** findings (no purge,
   no full four-cell run).
10. Pressure to skip Task 5 “because tests passed” — tests are necessary, not sufficient for this
    gate.

---

## Relationship to prior SPDR-021/023 handoff standards (reuse)

Borrow without re-deriving:

- checkbox tasks + completion evidence in-file;
- TDD before production;
- explicit delete lists;
- no economic verdict in engineering docs;
- power context only;
- sequential cells; fail closed on integrity;
- fresh-context final analysis.

Do **not** import SPDR-021 device grids, six-cell matrix, or SIZE horizon amendments — different
experiment.

---

## Completion log

| Task | Status | Date | Evidence summary |
| --- | --- | --- | --- |
| 1 Design AMENDMENT-7 | pending | | |
| 2 Analyser R2/R3/R4 | pending | | |
| 3 Preflight R1/R5 | pending | | |
| 4 Acceptance + smoke | pending | | |
| 5 Claude review gate | pending | | path → `docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.md` |
| 6 Purge | pending | | |
| 7 Engine re-screen | pending | | |
| 8 Re-analysis + docs | pending | | |
| 9 Closeout | pending | | |

---

## Appendix A — Remedy → task map

| Remedy | Design Task 1 | Code | Test emphasis |
| --- | --- | --- | --- |
| R1 mechanism ceiling | §10 rewrite | preflight + optional analysis context fields | ceiling vs floor descriptive label |
| R2 floor = Z × SE_CI | §10 rewrite | `spdr024_analysis` interval helpers | mde tracks bootstrap SE |
| R3 no pass-mark / no labels | §11 + A6 | emission schema | denylist columns; analysis prose rules |
| R4 channel scales | §11 | selection vs scale columns | denominator named or bps-only selection |
| R5 preflight fills + same endpoint | §10 M2 | `preflight.py` | no order-only CARRIES; no 0.150 gate |

---

## Appendix B — Key paths

```text
Defect + operator decision:
  docs/experiments-docs/checkpoints/2026-07-25-018-trade-opportunity-capture-geometry/
    mde-floor-defect-spdr024.md

This handoff:
  docs/superpowers/plans/2026-08-07-spdr-024-mde-floor-fix-execution-handoff.md

Claude pre-run review (Task 5 output):
  docs/superpowers/plans/reviews/2026-08-07-spdr-024-mde-floor-claude-review.md

Experiment:
  python/experiments/SPDR-024/design.md
  python/experiments/SPDR-024/implementation-notes.md
  python/experiments/SPDR-024/screen_code/{run_cell,run_screen,preflight,selfcheck}.py
  python/experiments/SPDR-024/analysis_code/analyse.py

Core library:
  python/src/xen/adaptive_management/spdr024_analysis.py
  python/tests/test_spdr024.py
```

---

## Appendix C — Operator one-pager (constraints to not forget)

1. **Don’t rewalk** — fix apparatus, purge, re-emit.
2. **One amendment** for R1–R5 — no patch chain.
3. **No power labels** — ever.
4. **Floor shares SE with CI** — or don’t emit floor.
5. **2.8 is planning**, not a test.
6. **Preflight = fills + same endpoint** as the report’s power story.
7. **Scale ≠ selection σ̂** unless declared.
8. **SIZE σ̂ effects are small by construction** — don’t revive 0.15 as the bar.
9. **Estimates/CIs/controls stay**; only the resolution story was broken.
10. **No verdict / no TEST / no XENA** in this plan.
11. **Claude review once** after checks/smokes, **before** purge and full four-cell run — do not skip.

**End of handoff (execution not started).**
