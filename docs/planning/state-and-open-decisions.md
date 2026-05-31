# State & Open Decisions — Thesis-Qualification Programme

**Type:** Status + decision document (snapshot, not a design)
**Date:** 2026-05-31 (revised — state reconciled, decisions D0–D7 resolved)
**Companions:** [`thesis-qualification-system-problem-statement.md`](thesis-qualification-system-problem-statement.md) (seed) · [`charter.md`](charter.md) (founding design)
**Purpose:** Record where the programme stands — project-wide and for the founding checkpoint — and the decisions taken before any code runs. Nothing here changes the charter; it reports state and records the resolved forks. **All hard blockers (D0–D3) are resolved; the programme is ready to draft deliverable #2.**

---

## Part A — Project-wide state

### A.1 Direction
Xen has been refreshed **in place** (same repo; no separate project; no new project name — an interim "Touchstone" sibling tree was created and deleted). The object of study is now the **referee** that qualifies trading theses — the machinery that decides which candidates earn scarce validation resources — under an honest accounting of both false-positive and false-negative error. It is no longer a search for a specific market edge.

### A.2 What was reset / archived — and what was deliberately kept
- A full snapshot of the prior batch (chart-type validation, signal-quality, ICT, HTF state-descriptor theses; Phases 001–005; EXP-001…EXP-036) was copied to `.ignore/projects/v01.zip` (≈330 MB), walled off by `.gitignore` (`**/.ignore/`). The zip is a **backup snapshot**, not a seal: the live artefacts it duplicates remain in the working tree and are accessible (see A.2a).
- **A.2a — The prior artefacts are retained, not deleted (corrected state).** An earlier step in this session deleted the experiments, checkpoints, code-reviews, and `python/src/ict_timebar.py` from the working tree, and reset the two `INDEX.md` files. **Those deletions were intentionally reverted.** Two independent analysts recommended *reusing the existing Xen artefacts* for the new checkpoint — most consequentially, the gate-stack implementation that closed Phases 003–005 is the baseline referee under test, so destroying it would have destroyed the founding experiment's object. The working tree is therefore **clean at HEAD `947a6bd`**, with `EXP-001…036`, all five checkpoints, `docs/code-reviews/`, both populated `INDEX.md` files, and `ict_timebar.py` all present. The "demolition" framing of earlier drafts is void.

### A.3 What is retained (deliberately)
- **Chart-type architecture** — `linebreak_generator.py`, `renko_generator.py`, `heiken_ashi_generator.py`, plus `bar_aggregator.py` (OHLC resampling) and `time_alignment.py` (timestamp normalization). Jerry's rule: all future theses ride on chart types (primarily traditional time bars), so chart generation is agnostic infrastructure, not thesis baggage.
- **The prior experiment tree** (`python/experiments/EXP-001…036`, checkpoints, code-reviews) — retained as the **source of record for the baseline referee**. The §5.6 closure stack is read directly from `python/experiments/EXP-036/code/run_experiment.py` (see B.4); the closed theses themselves stay closed (charter C1).
- **Data** — 4 instruments under `data/timebars/` (EURUSD, XAUUSD, USTEC, BTCUSD), 2023-01 → 2026-05. The final-30% global holdout remains untouched.
- **Gate inference primitives** — inside `signal_quality.py`: `bootstrap_diff_ci`, `bootstrap_rate_ci`, `compare_signal_sets`, `coverage_adjusted_outcomes`.
- **The research pipeline skills** — agnostic apart from the chart-type architecture, which is kept.

### A.4 Module state this session (resolved)
`signal_quality.py`, `timeframe_replication.py`, `market_bias.py` were briefly `git rm`'d (when the plan was a fresh stack) and then **restored**, because the existing stack became the baseline-under-test. Current `python/src` = chart architecture + `ict_timebar.py` + these three modules. `python/INDEX.md` was reverted to its committed state and **still describes the old "Event-Based Price Aggregation Research" programme** (stale — rewritten under D5 when the checkpoint opens).

### A.5 Founding documents & memory
- `docs/planning/thesis-qualification-system-problem-statement.md` — the seed.
- `docs/planning/charter.md` — founding design, currently at **option 2** (calibrate the existing stack first; 13 constraints; honesty clauses C1–C4, C1 reversed to "answer §5.6").
- Memory (`MEMORY.md`, `qualification_programme.md`, `xen_research_culture.md`) updated to reflect the in-repo refresh, the existing-stack baseline decision, and §5.6 now being answered.

### A.6 Git state
Working tree is **clean at HEAD `947a6bd`** — the intentional reversion (A.2a) restored every retained artefact, so there are no pending deletions. The only net-new items from the refresh are untracked because they live in gitignored paths: the `.ignore/projects/v01.zip` snapshot and the three `docs/planning/*.md` programme documents. Tracking the latter is the substance of decision D6.

---

## Part B — Founding-checkpoint state (the calibration phase)

### B.1 Charter essentials (full detail in `charter.md`)
- **Founding thesis.** **H1:** a qualification system's operating characteristics (FPR, a power *surface*, per-leg pass rates) can be measured with enough fidelity that "reject" carries trustworthy meaning. **H0:** they cannot — power is too sensitive to the synthetic effect-generator (the calibrator-needs-calibrating problem).
- **Founding experiment (EXP-037).** Two-part calibration of the **existing Xen stack as baseline referee**: Part A null calibration (dependence-preserving bootstrap of real series → FPR + per-leg leak/over-reject, *trustworthy*); Part B power bracketing (planted synthetic edges varied by **mechanism and parameters** → the *sensitivity of apparent MDE to the synthetic family* is the H0/H1 verdict; report a power *surface*, never a scalar).
- **Decision the experiment yields.** A **§5.6 ruling** (is the existing stack appropriately strict, too insensitive, or mismatched to the kind of edge worth finding?) and a founding-thesis ruling (is the calibration itself trustworthy or generator-dependent?).
- **13 binding constraints** and **4 honesty clauses** (notably: admissibility vs evidentiary separation; second-order holdout / frozen battery; economic materiality + proxy-cost regimes; decision ladder; do-not-loosen-gates-before-calibration; answer §5.6 but measure the referee only, never rescue a closed thesis).

### B.2 Founding deliverables — status
| # | Deliverable | Status |
|---|---|---|
| 1 | Charter (approved) | Drafted (option 2); **awaiting your sign-off** |
| 2 | Predeclared spec of the existing stack, in two layers (admissibility vs evidentiary) + proxy-cost regimes + harness DoF (+ stopping rule) + frozen battery & second-order holdout + compute budget | **Unblocked (D0–D3 resolved); ready to draft** |
| 3 | EXP-037 calibration (Part A null, Part B power) | Not started (needs #2) |
| 4 | §5.6 ruling + founding-thesis ruling | Not started |
| 5 | *Deferred/conditional:* successor-stack design, only post-ruling | Not started (by design) |

### B.3 Readiness check (re-run 2026-05-31, post-reconciliation)
| Check | Result |
|---|---|
| Real data for null calibration | ✅ 4 instruments, 2023–2026 |
| `python/src` imports in venv | ✅ `signal_quality` primitives present |
| Gate inference primitives present | ✅ bootstrap CIs, `compare_signal_sets`, `coverage_adjusted_outcomes` |
| A single canonical "existing stack" callable | ⚠️ **Materialized by transcription** from `EXP-036/code/run_experiment.py` — see B.4 |
| The §5.6 closure stack present and readable | ✅ **Yes** — `python/experiments/EXP-036/code/run_experiment.py` (retained, not sealed) |

### B.4 The former blocker, resolved: "the existing stack" is read from the retained EXP-036 implementation
The earlier draft treated the §5.6 stack as missing from the tree and reachable only by breaching a sealed archive. **That is no longer true.** With the prior artefacts retained (A.2a), the closure stack is read directly from the accessible experiment code — no guessing, no reconstruction-from-memory.

- **Canonical instance: `python/experiments/EXP-036/code/run_experiment.py`** (the last and most-evolved Phase-005 application of the stack). Its predeclared constants are stable across the Phase-005 closure experiments (verified identical in EXP-034/035/036): row floors 100/50, episode floors 30/15, instrument floor k=2.
- **The transcribed §5.6 stack (evidentiary layer):**
  1. **Representation floors** (per state, per segment): rows ≥ 100 (train) / ≥ 50 (test); **episodes** ≥ 30 (train) / ≥ 15 (test). Inference unit = independent state **episode**, never row (naive row-level CI is diagnostic only). Adjudicability: the neutral contrast requires both extreme buckets *and* the middle bucket to clear floors; the control contrast requires both extremes.
  2. **Neutral-baseline gate** (`Delta_neutral`): direction-adjusted excess of the extreme state's executable next-bar log return over the *measured* middle-bucket mean `mu_mid`, via a two-sample episode bootstrap that propagates the baseline's sampling error.
  3. **Matched-control gate** (`Delta_control`): paired head-to-head against a deliberately naive prior-bar-momentum-sign control, `mean((d − c)·r)` on the descriptor's own traded bars.
  4. **Replication / sign preservation:** the test-segment bootstrap CI lower bound > 0 **and** the train-segment point estimate > 0 (same-signed, test CI excluding zero positively).
  5. **Replication breadth k:** the both-contrast pass must hold on **≥ 2 distinct instruments** at a timeframe (`QUALIFYING_INSTRUMENT_FLOOR = 2`); the independence unit is the **instrument** (horizons/parameters of one instrument do not count).
  6. **Bootstrap:** 10,000 episode-level resamples, fixed seed, deterministic per-cell seed offsets, cell-budget cap 2M.
  7. **Secondary horizon:** a single predeclared 4-bar hold, under asymmetric semantics — it can reopen a question at a longer horizon but is **barred from producing the primary pass**.
  8. **Decision ladder (already present):** `FOR` / `STATE_DIFFERENTIATION_ONLY` / `HORIZON_DEPENDENT` / `INCONCLUSIVE` / `AGAINST` — the stack already outputs a graded verdict, not a binary one (satisfies constraint 12 in embryo).
- **Admissibility layer (held fixed during calibration):** real OHLC only / no synthetic price in the measured returns / holdout-excluded analysis set / 0.70 train fraction within that set / strict canonical aggregation / episode inference / full predeclaration.
- **What the stack does *not* contain, and must be added in deliverable #2** (these are calibration-harness or charter constructs, never part of the closed-thesis stack): the **economic-materiality threshold + proxy-cost regimes** (constraint 11 — EXP-036 has only an `EntryGapMin` executability diagnostic, no spread/slippage model); the **harness DoF + explicit stopping rule** (constraint 7); the **frozen calibration battery + second-order holdout** (constraint 10); the **compute budget** (constraint 6).

So we *can* honestly "calibrate *the* existing stack": it is the EXP-036 evidentiary stack above, transcribed verbatim and frozen, with the four harness/economic constructs added around it (not into it).

---

## Part C — Decisions (resolved)

D0–D3 were the hard blockers; all are resolved. D4–D7 follow Jerry's instruction to proceed with the recommended options.

### D0 — State reconciliation (was undocumented) — **RESOLVED**
**Question:** were the working-tree deletions of the prior artefacts intentional or an accidental revert?
**Resolution:** **Intentional retention.** Two independent analysts recommended reusing the existing Xen artefacts for the new checkpoint; Jerry reverted the deletions deliberately. The working tree at HEAD `947a6bd` is the intended state. Part A is corrected accordingly (A.2a). Nothing further to "un-delete."

### D1 — Which stack is the baseline referee? — **RESOLVED**
**Decision: (a) the §5.6 closure stack** — representation floors + neutral-baseline + matched-control superiority + ≥2-instrument train/test sign preservation + bootstrap CI excluding zero. It is the gate that closed Phases 003–005 and the one §5.6 actually asks about. The Phase-2 signal-quality gate (`signal_quality.py:proceed_criteria`, thresholds `{Precision60: 0.05, RunContinuation30: 0.03}`, ≥3 instruments) answers a different question and is **not** the calibration target.

### D2 — How is that stack materialized? — **RESOLVED (tension dissolved)**
**Decision: transcribe it verbatim from the retained `EXP-036/code/run_experiment.py`** (canonical Phase-005 instance; constants verified stable across EXP-034/035/036), then **freeze** the transcription in the deliverable-#2 spec.
- The earlier recommendation ("predeclare fresh from memory to keep a sealed archive sealed") is **superseded**: the artefacts are retained and accessible, so there is no sealed archive to breach and no need to guess. We read the real implementation.
- The fidelity tension I raised in the prior draft (faithful-reconstruction vs. sealed-archive) is therefore **void** — the §5.6 answer now reads *"the exact stack that closed Phases 003–005 is/isn't passable,"* the strongest available claim.
- **Honest caveat retained:** the stack drifted in shape across earlier phases (EXP-020/030 did not expose the same named constants). The spec fixes **EXP-036 as the canonical reference version** and notes earlier-phase divergences explicitly, so "the existing stack" denotes one frozen artifact, not a moving target.

### D3 — Concrete predeclared thresholds for the §5.6 stack — **RESOLVED (read, not invented)**
The evidentiary thresholds are now **read facts** transcribed from EXP-036, not choices to be argued: representation floors (rows ≥100/50, episodes ≥30/15, per state per segment); replication breadth **k = 2** instruments (independence unit = instrument); bootstrap CI rule (test CI lower > 0 **and** train point > 0; 10,000 episode-level resamples); neutral-baseline = measured `mu_mid` two-sample episode bootstrap; matched-control = naive prior-bar-momentum-sign predictor. These are frozen as-is (constraint 13: measured first, never tuned to make theses pass).
**The only genuinely new values to *draft*** (absent from the stack): the **economic-materiality threshold** and **proxy-cost regimes** (low / central / stress), since the data lacks true spread/slippage (constraint 11). I draft these for review in deliverable #2.

### D4 — Phase / experiment numbering — **RESOLVED**
**Decision: (b) continue the sequence — Phase 006 / EXP-037+.** Honors the pipeline's never-reuse rule and avoids collisions with the retained `EXP-001…036` (which now physically remain on disk, so a "fresh EXP-001" would also collide in the filesystem, not just in history). The reset index tables simply begin their visible rows at the new IDs.

### D5 — `python/INDEX.md` forward rewrite — **RESOLVED (scheduled)**
It still declares the old "Event-Based Price Aggregation Research / Phase 001 — Chart-Type Validation" programme. **Rewrite it to the qualification programme** (existing stack retained as baseline-under-test) **when the founding checkpoint is opened**, bundled with the D4 numbering, to avoid churn before sign-off.

### D6 — Commit strategy — **RESOLVED**
Because the artefacts were retained (D0), there is **no deletion reset to commit** — the tree is clean. The remaining action is to make the load-bearing programme documents version-controlled:
- **Narrow `.gitignore`** so `docs/planning/charter.md`, `…/thesis-qualification-system-problem-statement.md`, and `…/state-and-open-decisions.md` are **tracked** (they are now founding documents, not scratch). The `.ignore/` archive stays ignored.
- Commit as one explicit "refresh: adopt thesis-qualification programme" commit (the gitignore narrowing + the three docs).

### D7 — Calibration compute budget (constraint 6) — **RESOLVED (target set in #2)**
Set an explicit wall-clock / replication budget in the deliverable-#2 spec, anchored to EXP-036's actual harness cost (10,000 episode resamples, 2M-cell cap per cell) scaled by Part A null replications × Part B (effect-mechanisms × parameters × regimes) × stack legs × instruments. The budget is stated up front so a calibration regime more expensive than the research it referees is flagged as a design failure, not absorbed.

### Design items promoted to first-class within deliverable #2
These are **design problems, not threshold picks**, and EXP-037 cannot run without them. They are no longer buried as sub-bullets:
- **Harness-DoF stopping rule (constraint 7).** The synthetic effect-generator has its own researcher DoF; deliverable #2 pre-registers the generator and states an **explicit stopping rule for the regress** up front.
- **Second-order holdout + frozen battery (constraint 10).** Deliverable #2 defines how calibration cases are partitioned into a versioned tuning battery vs. an untouched second-order holdout, so "trust attaches only to the second-order holdout" is enforceable rather than aspirational.
- **Compute budget (constraint 6).** As D7.

---

## Part D — Sequenced path (decisions resolved)

1. ~~Resolve D0–D3 (hard blockers) and D4 (numbering).~~ **Done** (this document).
2. **Draft deliverable #2:** the EXP-036 §5.6 stack transcribed and frozen in two layers (admissibility vs evidentiary), with the read thresholds plus the four new constructs — economic-materiality/proxy-cost regimes, harness DoF + stopping rule, frozen battery + second-order holdout, and compute budget.
3. Open the founding **checkpoint `design.md`** (Phase 006 / EXP-037) and rewrite `python/INDEX.md` (D5).
4. **Commit the refresh** (D6): narrow `.gitignore`, track the three planning docs.
5. Governance pre-execution review of the spec.
6. Implement and run **EXP-037** (Part A null, Part B power).
7. Audit → interpret → the **§5.6 / founding-thesis ruling** (deliverable #4).
8. Only then: decide on a successor-stack design (deliverable #5), never before.

**Immediate next action:** produce **deliverable #2** — the predeclared, frozen specification of the existing stack (transcribed from EXP-036) with the four harness/economic constructs drafted for review. No decision blocks this.
