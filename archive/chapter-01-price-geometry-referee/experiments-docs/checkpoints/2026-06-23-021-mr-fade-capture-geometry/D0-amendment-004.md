# Phase 021 D0 — Amendment 004 (open the 4h domain, gated behind a falsification re-screen)

**Date:** 2026-06-24. **Status:** **FROZEN — RATIFIED 2026-06-24 (operator-authorized).** **Nature:** a **domain-scope
expansion** of the admitted lever (bare RSI-2 fade CORE + the EXIT-RCT capture geometry) to the **4h domain**,
which D0 §0/§D1/§D9 explicitly excluded (dead-by-absence at EXP-089, 1/14) and registered as a deferred branch.
The expansion is **opened but not admitted**: 4h enters the Phase-021 candidate pipeline only after a new
**TRAIN-only governed experiment (EXP-094)** clears a binding **falsification re-screen** that reconciles the
EXP-089 dead-by-absence finding. **Slot / read impact:** **0 new candidate slots** (domain expansion of the
G-020-admitted lever, operator decision 2026-06-24); **0 counted TEST reads** through EXP-094 (TRAIN-only).
Holdout untouched.

**Checkpoint:** `2026-06-23-021-mr-fade-capture-geometry` · **Amends:** `D0-predeclarations.md` §0 (4h
out-of-scope), §D1 (domains `{15m,1h}` only), §D9 (instrument/domain expansion deferred); `design.md` §0/§8.4.
**Cost model unchanged** — the `D0-amendment-003` Phase-021 table already prices all 13 member instruments,
including the 4h cells (it is domain-invariant in bps).

---

## 1. Trigger (recorded, not implied)

The operator ran a **side experiment on a hunch** — `python/experiments/temp-exp-091/` (`TEMP-091`), an
**unaudited, temporary, non-governed** copy of EXP-091 modified to run the frozen exit slate on **4h only**, all
13 cost-table instruments, TRAIN-only, EXP-090 substrate reused verbatim (4h patched in as 240-minute bars).

**TEMP-091 result (file-drawer disclosure — non-binding, unaudited):** EXIT-RCT **net-clears 12/12 instruments
on 4h** (JP225-4h failed to build → 12 cells screened), every clearing cell **mean *and* median positive**
(net_median +0.08…+0.16) — materially more robust than the binding EXP-091 1h pass (5 cells, 3 of them
median-negative / tail-carried). The other five arms net-clear 0 cells; the **reactive RSI-revert-on-close
analog of the same entry is net-negative on all 12 cells**. Determinism replay passed; holdout untouched.
Mechanism is the same ATR-normalized cost geometry as EXP-091, taken one domain further: 4h ATR is larger
still, so the fixed-bps round-trip costs an even smaller ATR fraction (~0.07–0.20 ATR vs ~0.24–0.30 on 1h).

Per programme norm, a hunch run on a deferred lever is **recorded in the file drawer regardless of outcome**
(remembering only positive probes of deferred branches is the exact researcher-degrees-of-freedom risk the
signal registry controls). TEMP-091 is therefore entered as a disclosure in the Phase-021 multiplicity batch;
its artifacts are **archived** (moved to `python/experiments/_archive/temp-exp-091/`, retained in git history,
removed from the active experiment tree — operator preference 2026-06-24), not hard-deleted. Its result is
non-binding and is superseded by the governed EXP-094 rerun (programme deviation-handling norm —
`deviation_handling_amend_in_place`, adapted to archive-not-delete).

## 2. The tension this must confront (why "just add 4h" is inadmissible)

There is a **hard contradiction** between the hunch and the screen that gated this entire phase:

- **EXP-089 (the family-selection availability screen) found 4h dead-by-absence — 1/14 cells.** The fade
  **entry** has no favourable-excursion edge above a *direction-matched random clock* on 4h. That is precisely
  why §0/§D1 excluded 4h.
- Yet TEMP-091's RCT net-clears 4h **everywhere**.

These cannot both read as "the fade signal works on 4h" without an explanation. The pattern in the TEMP-091
4h data points to the worrying reading: **only the proactive small resting-limit (RCT) is positive**, while the
**reactive version of the identical signal (RSI-revert-on-close), ATR-barrier, fixed-bar, and ERT are all
net-negative**. That is consistent with RCT harvesting **generic short-horizon oscillation** — a ~0.28-ATR
target that price reverts to ~99% of the time *regardless of the entry signal* — which nets positive on 4h only
because ATR-normalized cost is so small there. If so, the 4h "edge" is **exit geometry / volatility harvesting,
not the RSI-2 fade**, and 4h must stay closed (EXP-089 dead-by-absence reaffirmed, now mechanistically
explained).

TEMP-091's `native_vs_contrast` (RCT vs RSI-revert) is an **exit-mechanism** A/B on the real entry; it does
**not** discriminate signal from oscillation. The missing falsification is **RCT on a matched-random /
shuffled entry** on 4h: if a random entry with the same RCT exit also net-clears, the edge is not the fade.

## 3. Resolution — open 4h, admit only behind a binding falsification re-screen (EXP-094)

**3.1 Scope change (binding on ratification).** The **4h domain is opened** as a domain expansion of the
G-020-admitted lever (bare RSI-2 fade CORE + EXIT-RCT). The frozen entry (`RSI(2)` 2/10/90), the EXIT-RCT
target construction (D2.1), the adverse side (D2.3, 2.0×ATR + MR-tempo cap), the 1m intrabar fill engine
(D2.5), and the `D0-amendment-003` conservative cost table are **carried unchanged** to 4h. **No constant is
re-tuned.** 4h domain bars = 240-minute, built by the same holdout-fenced `build_domain_bars`.

**3.2 Slot decision (operator-ratified 2026-06-24): NO new candidate slot.** 4h is the same admitted lever +
exit on a new domain, not a new bet; the first CF-MR-001 slot (G-020) covers it. (Recorded explicitly per the
§D9 requirement that any domain expansion state its slot treatment.)

**3.3 4h is OPENED, not ADMITTED.** No 4h cell is eligible for EXP-092 candidate selection or EXP-093 TEST
until **EXP-094** clears the §4 binding rule on TRAIN. A failing or empty EXP-094 leaves 4h **closed and
retained** (dead-by-absence reaffirmed); the phase proceeds on its 1h result unchanged.

## 4. EXP-094 — 4h readiness + falsification re-screen (TRAIN-only; 0 reads / 0 slots)

A single governed experiment, run through the full pipeline (scope → … → governance). It carries three binding
legs, all TRAIN sub-split only, real OHLC, determinism byte-identical, holdout sealed:

**(a) 4h member-cell readiness (EXP-090 analog).** 4h was never put through EXP-090's readiness/MDE
calibration. EXP-094 re-confirms, per 4h cell: RSI-MR event coverage ≥ 15 (EXP-080 floor), exit substrate
deterministic, and a **finite per-cell event-level MDE on EXIT-RCT** under the frozen referee. A cell with no
finite MDE is `COVERAGE_EXCLUDED` with record (**JP225-4h is flagged a priori** — it failed to build in
TEMP-091). The 4h member set defines what (b)/(c) screen.

**(b) Net exit screen (frozen D6/4a, unchanged).** EXIT-RCT (and the full frozen slate, for the file drawer)
on the 4h member cells, net of the `D0-amendment-003` conservative cost: a cell net-clears iff net `ci_low_1s`
> 0; the arm passes iff it net-clears in **≥5 cells over ≥3 instruments**.

**(c) Falsification leg — the new binding gate reconciling EXP-089.** For EXIT-RCT, a **matched-random /
shuffled-entry** baseline: the *same* RCT target + adverse side + 1m fill + cost, but with entries drawn at
**matched per-cell count and matched long/short direction mix at random eligible TRAIN bars** — the EXP-089
direction-matched `SUB-RANDOM` construction reused, holding the exit geometry identical so the contrast
isolates the **entry signal**. Fixed seeds. Per cell, the **paired net advantage** Δ = (real-entry RCT net) −
(random-entry RCT net) is bootstrapped (moving-block, one-sided lower bound, Z=1.645). The real entry **beats
random** in a cell iff Δ's lower bound > 0.

**Binding admission rule for the 4h domain:**

| EXP-094 outcome (TRAIN-only) | 4h disposition |
| --- | --- |
| (b) RCT passes the quorum **AND** (c) real-entry beats random in a **≥5-cell / ≥3-instrument** quorum | **4h ADMITTED** (domain expansion, no new slot). The real-vs-random-beating 4h RCT cells become eligible for the EXP-092 sequence + EXP-093 TEST, smallest-defensible per §8.3. EXP-089's 4h dead-by-absence is overturned as a metric-specific false negative (the ~3-bar MFE_med statistic missed the RCT-capturable geometry). |
| (b) RCT passes the quorum **BUT** (c) random entry matches/beats real (the real-vs-random quorum fails) | **4h stays CLOSED**, retained. The 4h net-clear is **exit-geometry / oscillation harvesting, not the fade** — EXP-089 dead-by-absence reaffirmed and now mechanistically explained. No 4h cell carries to TEST. *(This outcome also flags a mechanism question for the 1h pass — see the §4 positive control.)* |
| (b) RCT net-clears < quorum on 4h | **4h not carried** (empty 4h screen); retained. |

**Positive control (disclosed companion, non-binding but required for power assurance).** Run the same
real-vs-random RCT contrast on the **EXP-091 1h clearing cells**, where EXP-089 *did* find availability
(1h 11/16). Real entry is expected to beat random there; if it does **not**, the test (c) lacks the power to
detect a true signal and EXP-094's 4h read is INCONCLUSIVE rather than a refutation — disclosed, not gated.

**Counted-read / holdout discipline (unchanged).** EXP-094 is TRAIN sub-split only → **0 counted TEST reads**;
`test-read-ledger.md` unchanged (all 4h strata stay 0/2 open). Any 4h cell later carried to EXP-093 spends ≤1
counted read on its 4h stratum (cap 2/stratum), recorded in the same change. The final-30% global holdout is
never sliced.

## 5. What this amendment does NOT change

- The frozen entry, EXIT-RCT geometry, adverse side, 1m fill engine, MR-tempo cap, referee suite, the
  `D0-amendment-003` cost table, and the EXP-091/092/093 1h pipeline and its verdicts — **all unchanged**.
- The other deferred levers (15m capture, vol-regime, contrarian, 25/75, regime×variant cross-cuts, parameter
  tuning) **remain deferred**, each behind its own future `D0-amendment-*`. This amendment opens **4h only**.
- No new selection statistic that gates a candidate is introduced beyond the §4(c) real-vs-random paired Δ —
  which is a **falsification null**, not a new admission statistic layered on the referee; per the bite-check
  convention it should be **bite-checked GREEN** at EXP-094 D0 before EXP-094 runs (a paired difference-of-net
  bootstrap on shuffled-entry controls — the EXP-089 SUB-RANDOM machinery in a paired form).

---

*FROZEN — RATIFIED 2026-06-24 (operator-authorized). The §3.1/§D1 domain change and the §D9 expansion note are
reflected inline in `D0-predeclarations.md` with a back-pointer here; TEMP-091 is recorded in the Phase-021
multiplicity batch and its artifacts archived to `python/experiments/_archive/temp-exp-091/`; EXP-094 is
registered (0 slots / 0 reads) and enters the pipeline at Stage 1 (scope). The G-021 adjudication reads 4h only
if EXP-094 admits it.*
