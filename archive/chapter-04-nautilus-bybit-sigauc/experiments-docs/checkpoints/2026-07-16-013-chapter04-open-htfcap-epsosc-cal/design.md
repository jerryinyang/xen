# Checkpoint 013 — Chapter 04 Open: HTFCAP + EPSOSC + Fresh XENA CAL (design)

**Opened:** 2026-07-16 · **Status:** DESIGN SIGNED — operator decisions D1–D5 recorded
2026-07-16 (see decision table); §2 registration rows appended per D2. Nothing executes;
no status transitions (those remain retrospective acts).
**Container for:** SPDR-004 (CF-HTFCAP-001 screen), SPDR-005 (CF-EPSOSC-001 screen),
INFR-014 (fresh XENA CAL — Bybit registry), and — conditional on SPDR promotes —
XENA-HTFCAP-001 / XENA-EPSOSC-001 universes.
**Family group:** `docs/signal-registry/candidate-families/cf-htfcap-001.md` (REF-A) +
`cf-epsosc-001.md` (REF-B); frozen decisions `proposal-ref-ab-open-questions.md`;
index `proposal-ref-ab-INDEX.md`. Pre-D0 `proposal-cf-*.md` are SUPERSEDED.
**Lane:** SPDR → XENA (default route; EXP lane not used — D0-frozen).

## Preconditions (verified on disk 2026-07-16)

| Item | State |
|---|---|
| INFR-010 | Phases 0/A/B/C/D/E ALL COMPLETE 2026-07-16 |
| Phase D | VAL-008 operator verdict SUPPORTED / PASS (`python/experiments/VAL-008/report.md`) |
| Phase E | INFR-013 verify PASS — `xen.orderflow` contracts + skeleton only; no bulk collection, detectors stubbed (`docs/references/orderflow-feature-store.md`) |
| Engine | nautilus_trader==1.230.0 pinned (`python/pyproject.toml`) |
| Data | catalog `data/catalog/` — 894 ADMITTED instruments, 672M bars; fence PINNED sha `35d3375e…` via `xen.nautilus.catalog_fence` |
| Governance | INFR-012 rebind verified 10/10 (estimand gate v2, STUB-fails) |
| XENA registry | chapter-03 frozen registry **VOID on Bybit** (INFR-010 R4) — INFR-014 required before any counted XENA path |
| Family D0s | both COMPLETE 2026-07-16, not yet REGISTERED; 0 slots, 0 reads |
| Holdout | sealed; both sanctioned reads spent (legacy datasets); no TEST contact this checkpoint until XENA gates post-CAL |

## Objectives

1. Ratify VAL-008 §5 stack lessons into the KB (operator-signed) — §1 below.
2. Register CF-HTFCAP-001 and CF-EPSOSC-001 as formal REGISTERED families (ledger rows +
   card status), consistent with the D0 cards — §2.
3. Scope and run INFR-014: fresh Bybit CAL producing a new hash-pinned XENA registry shaped
   to the two mechanism classes; absorb the multi-instrument single-engine smoke — §3.
4. Execute the family experiment sequence: SPDR-004/005 screens first, XENA universes only
   after promote + CAL pin — §4.
5. Codify the instrument selection rules (Q1: n=10) as a written, reproducible rule set —
   §5.

---

## §1 Ratify VAL-008 §5 stack lessons (operator-signed KB act)

Proposed as KB lessons **L-28…L-31** in `docs/knowledge-base/lessons-and-amendments.md`
(next free IDs after L-27; L-18 remains reserved). Text sourced from
`python/experiments/VAL-008/report.md` §5; each entry carries mechanism + enforcement hook.

| ID | Lesson | Enforcement hook |
|---|---|---|
| L-28 | Destroy permutations must be **derangements** — plain permutation leaks signal through fixed points (measured 11.1% alignment → collapse only 0.87) | quant-designer control spec + qa-compliance clause; builds on L-14/L-19 |
| L-29 | Nautilus **fill-ts = decision-bar close** (= wall-clock open of fill bar); naive `searchsorted` on bar closes mis-indexes by one. Anchor check: `EntryFillPrice == next-bar RealOpen ± 1 tick` | estimand-gate / analyst alignment check; emission contract note |
| L-30 | `BacktestRunConfig(dispose_on_completion=False)` required for node-path report capture (default silently empties reports) | `xen.nautilus.backtest_util` + runner template; optional patch of `run_ma_cross_node` (VAL-008 follow-up) |
| L-31 | **One BacktestNode per process** (Rust logging init panics on a second node) — runners are subprocess-per-cell | runner template + qa-compliance clause |

VAL-008 §5.5 (multi-instrument single-engine untested) is NOT a lesson — it is an open
engineering item absorbed by INFR-014 (§3, smoke S1).

Retrospective act: operator signs the four lessons; documenter writes them into the KB and
patches the affected skill clause lists. No lesson text is final until signed.

## §2 REGISTERED ledger rows — CF-HTFCAP-001 + CF-EPSOSC-001

**D2 APPROVED 2026-07-16 — rows appended as specified below.** (Registration-before-
screening is a hard constraint — rows must exist before SPDR-004/005 run; this is an
**append/registration act**, not a status *transition*, and is therefore permitted
mid-checkpoint.)

1. `docs/signal-registry/multiplicity-registry.md` — new Chapter 04 sections, one per
   family, recording: family ID, D0 card + SPDR pack paths, route SPDR→XENA (no EXP),
   universe = 10 rule-selected Bybit USDT-perps (§5), promote rule = cluster K≥3 on the
   pack's primary bps estimand vs matched controls (pack text normative), TRAIN-only,
   funding disclose@SPDR / bind@XENA, 0 slots / 0 counted reads at registration, hard bans
   as per card §4 (incl. P-12 dead-grid object out-of-family for EPSOSC; no chapter-03
   registry pins on Bybit).
2. Card status header: `D0 COMPLETE` → `REGISTERED (2026-07-16, checkpoint-013)`; evidence
   ledger row added; SPDR-ID recorded (§4).
3. Test-read ledger: no entries (no TEST contact at registration).

Consistency check performed: rows must not add, drop, or reinterpret any frozen decision in
`proposal-ref-ab-open-questions.md` (Q1–Q5, Q-A1/A2, Q-B1/B2/B3).

## §3 INFR-014 — fresh XENA CAL (Bybit registry)

**Goal.** Produce a new hash-pinned frozen registry for the XENA counted path on the Bybit
Nautilus stack, replacing the VOID chapter-03 pin (INFR-010 R4). Own design.md at
`python/experiments/INFR-014/` (full CAL design is that document; this section fixes scope
+ constraints only).

**Shape to the two registered mechanism classes** (D0 cards §2):

| Class | Family | CAL implication |
|---|---|---|
| Conditioning / filters + hold-scale capture | CF-HTFCAP-001 | binder must express **selectivity under net cost** (L-26 — costless cadence-max cannot adjudicate a filter thesis); pre-search gross-bps floor vs Bybit breakeven (XENA-003 lesson); funding in cost stack |
| Episode-harvest / path structure | CF-EPSOSC-001 | episode/leg-level estimands; inventory + path diagnostics; funding-vs-episode-length in cost; avoid cadence artifacts |

**Binding constraints carried in (not re-decided here):**
- CAL discipline per `docs/references/xena-lane.md` v2: predeclared battery, design/confirm
  bank split, new hash-pin; changing any pinned element post-pin = new predeclared CAL.
- Binder starting form: INFR-009 two-stage CONFIRM DUAL_CERTIFY (archived pin) is the
  **prior**, re-calibrated — not reused — on Bybit; α̂ resolved by scaling **n_null**
  (SE ≈ 0.218/√n_null), gate on point α̂, predeclared n, no optional stopping.
- Permutation-null battery: destroys are **derangements** (L-28); alignment-break, not P&L
  shuffle (L-14); confound check for limit-entry universes (L-27) if any limit-entry cells
  exist in either family's XENA grid.
- Costs analyst-injected (engine costless): Bybit fees + spread model + **funding**;
  per-symbol spread pinning status disclosed.
- CAL runs on TRAIN band of the fenced catalog only; instruments drawn via §5 rules
  (anti-survivorship handling per rules; delisted membership as the rules dictate).

**Absorbed engineering item — smoke S1:** multi-instrument single-engine Nautilus run
(untested per VAL-008 §5.5). Pass = one BacktestNode process running N≥3 instruments in one
engine with bitwise-consistent emissions vs per-instrument runs, honoring L-30/L-31.
Outcome decides whether XENA batch cells are single-engine-multi-instrument or
subprocess-per-cell; recorded in INFR-014 results.

**Exit criteria.** New registry JSON hash-pinned + verify wrapper green; predeclared α̂
within tolerance for both class-shaped binder configs; smoke S1 verdict recorded. Until
then: SPDR may run (Q4), XENA counted path is blocked.

## §4 Planned experiment sequence

| Seq | ID | What | Gate to start | Depends on |
|---|---|---|---|---|
| 1 | **SPDR-004** | CF-HTFCAP-001 TRAIN-only vectorised screen per `docs/references/spdr-pack-htfcap-001.md` | registration rows (§2 — DONE) + selection rule + rebalance frequency declared in design.md (§5) + operator execution approval | catalog fence (done) |
| 2 | **SPDR-005** | CF-EPSOSC-001 screen per `spdr-pack-epsosc-001.md` | same | same; may run parallel to SPDR-004 (Q3: separate packs) |
| 3 | **INFR-014** | fresh CAL + registry pin + smoke S1 (§3) | own design.md + QA + operator approval | catalog; runs parallel to SPDRs (D4 APPROVED) |
| 4 | **XENA-HTFCAP-001** | full XENA universe (wide grid; manifest = later design.md) | SPDR-004 = WORTH_EXPLORING **and** INFR-014 pin exists | 1, 3 |
| 5 | **XENA-EPSOSC-001** | full XENA universe | SPDR-005 = WORTH_EXPLORING **and** INFR-014 pin | 2, 3 |

- SPDR IDs continue the zero-padded never-reused series (chapter-02 spent SPDR-001..003).
- SPDR lane rules bind (`docs/references/spdr-lane.md`): TRAIN fence code-asserted, causal
  t−1 lag, matched-control + seed battery, per-stratum reads, Stage-5 fresh-context
  summary, L-21 unit pin + money floor at the screen→graduation seam, disposition once
  after both packs' legs per family. WORTH_EXPLORING is not a tradability claim.
- Each item gets its own design.md → QA (fresh context) → operator execution approval;
  nothing in this checkpoint design pre-approves execution.
- Kill/park criteria are the D0 cards' §8 tables; NOT_WORTH or INCONCLUSIVE at SPDR
  stops the family's XENA leg without touching INFR-014.

## §5 Instrument selection rules — Q1 codification (amended per D3/D5, 2026-07-16)

Q1 froze **n = 10 assets via instrument selection rules** (membership rule-defined, not an
ad-hoc list). `xen.nautilus.universe_selection` is **uncodified** (verified: no module in
`python/src/xen/`). **D5: there is NO fixed pre-run ticker list — selection is ONLINE.**
The frozen declarations are the **rule + rebalance/reset frequency**, not a list.

1. **Online selection rule (default, operator-signed D5):** at each rebalancing/asset-reset
   point, select the 10 instruments with the **highest trailing 24h volume**, re-evaluated
   at the configured rebalance/asset-reset frequency. Rule and frequency are declared as a
   binding block in each SPDR/XENA design.md before any cell runs; deterministic and
   reproducible from catalog data alone (ADMITTED, spec-complete instruments; tie-break
   lexicographic).
2. **Causality:** selection at time t uses volume data **≤ t−1 only** (same causal fence as
   every feature; code-asserted).
3. **Anti-survivorship (D3):** binding **project-wide**. At **XENA** the point-in-time
   universe **includes delisted symbols** (a symbol listed and liquid at time t is
   selectable at time t regardless of later delisting) — characterisation happens at XENA,
   where anti-survivorship binds fully. At **SPDR**, selecting the 10 currently-most-liquid
   is acceptable because SPDR's purpose is justification (WORTH_EXPLORING disposition), not
   characterisation — rationale operator-recorded 2026-07-16.
4. Codified selector (`xen.nautilus.universe_selection`) may follow as parked apparatus —
   engineering, not blocking (per D0 cards §9).
5. Both families follow the same selection rule (D5: shared-vs-per-family is moot — same
   rule → same selections).

## Success criteria (checkpoint level)

- L-28..L-31 signed into KB + skill clauses patched.
- Both families REGISTERED with consistent rows; 0 unexplained deltas vs D0 cards.
- SPDR-004/005 each end in an operator-signed disposition (WORTH / NOT_WORTH /
  INCONCLUSIVE) — negatives are clean outcomes.
- INFR-014 ends with a hash-pinned registry + smoke S1 verdict, or a recorded park.
- Any XENA universes end in operator-signed outcome rows (eval_count + distinct_subsets),
  regardless of gate result.
- Family status changes (if any) happen only at this checkpoint's retrospective,
  operator-signed.

## Constraints carried in

Holdout sealed (both shots spent) · chapter-03 registry VOID on Bybit until INFR-014 pin ·
pitfalls P-10/P-12/P-14/P-15 escape clauses bind (D0 cards §10) · registration before
screening · per-stratum reads, pooled disclosure-only · no scope expansion after QA APPROVE ·
no auto-verdicts · SPDR never touches TEST, spends no reads, registers nothing by itself ·
estimand gate v2 passing required before any verdict/TEST read on Nautilus emissions.

## Operator decisions — SIGNED 2026-07-16

| # | Question | Operator decision (2026-07-16) |
|---|---|---|
| D1 | Approve §1 lesson texts L-28..L-31 as written? | **APPROVED as written** — wording signed; KB ratification proceeds per §1's process |
| D2 | Approve §2 registration rows for both families now (before SPDRs)? | **APPROVED** — REGISTERED rows appended per §2 framing (append/registration acts only; no status transitions, no frozen-Q changes) |
| D3 | Do the Q1 selection rules include delisted instruments in the SPDR 10? | **Anti-survivorship is BINDING PROJECT-WIDE.** For SPDR specifically, selecting the 10 currently-most-liquid is acceptable because SPDR's purpose is justification (WORTH_EXPLORING disposition), not characterisation — characterisation happens at XENA, where anti-survivorship binds fully |
| D4 | INFR-014 in parallel with SPDR-004/005, or after their dispositions? | **APPROVED — parallel** |
| D5 | One shared 10-asset list for both families, or per-family lists? | **DISSOLVED — wrong assumption.** No fixed pre-run ticker list exists: selection is ONLINE (§5). Both families follow the same rule, so shared-vs-per-family is moot (same rule → same selections) |
