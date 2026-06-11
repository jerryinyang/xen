# Phase 011 — Per-Instrument Foundation & Strategic Reset

**Checkpoint type:** Research phase design.
**Date drafted:** 2026-06-11.
**Status:** ACTIVE — D0 closed, **G0 PASS 2026-06-11** (operator-ratified
`D0-predeclarations.md`; all §8.5 items FROZEN, EXP-018 threshold fixed
first, before any TRAIN read). **Track A0 REMOVED 2026-06-11
(framing error):** the band multiplier is an exit parameter, not an entry
parameter — EXP-042 set aside (MEASUREMENT_COMPLETE — FRAMING_ERROR), entry
reverts to the frozen baseline arm/trigger at the AVWAP line, and the band
lives entirely in Track B exit training (§5.4 Family 2). Tracks A/B data
contact authorized. See the amendment log (§11) for the post-draft
corrections (§7.3 cost transcription error; `/BAND` entry-rule semantics —
**rescinded**; Track A0 removal) and
`docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`.
**Candidate family:** `CF-AVWAP-001` (continued from Phases 004–010).
**Follows:** `2026-06-10-010-exit-exploration-and-line-sr` (CLOSED —
EXIT_FLAT / HYP-001 INCONCLUSIVE; INFR-002 carried OPEN, now closed by
VAL-003 PASS 2026-06-11).
**Source:** `docs/planning/phase-011-redesign-per-instrument-foundation.md`
(post-Phase-010 operator discussion). This design supersedes the original
Phase-011 MTF scoping.

## 1. Provenance

### 1.1 The discovery that rescoped this phase

Phases 001–010 ran under a silent assumption: the AVWAP strategy's
parameters (band multiplier=1.0, MA 20/50, exponent 0.75, FH H\*=12) were
universal constants applied identically to all instruments and domains. In
reality, every one of these was a brainstorming placeholder — never trained,
never swept, never questioned. This produced a misleading convergence:

| Phase | Claim | What was actually being tested |
|-------|-------|-------------------------------|
| 007 | Equal-weight net-negative → "not tradable" | The equal-weight mean of 4 instruments under **one fixed parameter set** |
| 008 | FH H\*=12 saves +40.56 bps on EURUSD TEST | Selected from a pooled 3-instrument mean curve; `h_star_stable = false` (split-half argmax disagreed 24 vs 12) |
| 010 | EXIT_FLAT — 0/10 exits beat R-FH(12) at +37.3 bps | Competing exits evaluated on **events selected by band=1.0**, which may be noise-dominated |

The universal-parameter constraint was never deliberate — it was inertia
from the brainstorming document. Every non-baseline branch (`/ALPHA`,
`/BAND`, `/MA-DOMAIN`, `/BAND-MULTIPLIER`) existed precisely to explore
these dimensions, yet none was ever scoped. The programme converged on "the
base strategy is done, move to MTF" when the base strategy was never given a
fair fight with instrument-appropriate tools.

A second correction follows from the first — and was itself corrected on
2026-06-11 (§11): replacing band=1.0 with an *asserted* band=2.0 would
repeat the exact failure being diagnosed, but the original remedy (a global
entry-level band scan, Track A0) was a framing error — the band multiplier
is an exit parameter and there is no entry-level band to select. The band is
therefore **selected per cell, not asserted**, inside Track B Family 2
(§5.4), by the same n-neighbour stability rule as the FH horizon. Entry
stays the frozen baseline AVWAP-line arm/trigger, unchanged from Phases
004–010.

### 1.2 Binding constraints carried into this phase

- **No holdout read exists for any package, ever** (Phase 009 spent the
  single sanctioned shot: HOLDOUT_INCONCLUSIVE). USTEC/XAUUSD/BTCUSD
  holdouts and all 13 new-instrument holdouts remain sealed (final 30% per
  INFR-002 declaration).
- **EURUSD holdout is contaminated-by-disclosure** — EURUSD results at any
  domain are permanently TEST-capped.
- **EURUSD-4h TEST is at the read cap** (2 counted reads: EXP-037, EXP-038;
  §7.1) — no further stratum-specific read, including Track D. EURUSD-1h/2h
  TEST strata have zero counted reads and remain eligible.
- **Small-n bootstrap reads are anti-conservative without calibration**
  (R1.2, EXP-032): every binding one-shot read in this phase carries the
  matched-structure null calibration and margin.
- **R1.7:** prior-touched strata yield variant-level confirmation, not
  independent out-of-sample evidence; every read of a previously-touched
  stratum carries that disclosure.

### 1.3 Operator decisions recorded 2026-06-11 (pre-design)

1. Phase-011 is rescoped from MTF to **per-instrument foundation**; MTF is
   deferred (§10).
2. Domains: **1h, 2h, 4h**. 5m is retired from all primary strategy
   considerations (carried from Phase 010; net-negative under CONSERVATIVE
   costs on every test — EXP-030/033/039; reserved for MTF execution-layer
   use only).
3. Asset set: **17 instruments** — the 4 old plus 13 new admitted via
   VAL-003 PASS (2026-06-11). First analytical use of the new universe.
4. Entry signal MA(20,50) and exponent 0.75: **frozen as-is** — a deliberate
   freeze, not an examined optimum; `/ENTRY`, `/ALPHA`, `/MA-DOMAIN` remain
   registered but deferred.
5. Band multiplier: **no entry-level selection.** Track A0 was removed by the
   2026-06-11 framing-error amendment; entry remains the frozen baseline
   AVWAP-line arm/trigger. The band multiplier is selected only inside Track
   B Family 2 as an exit-target parameter.
6. Inference inverted: portfolio membership decided on TRAIN; **one
   portfolio-level one-shot TEST read (EXP-018 vs Donchian(20)) is the
   primary endpoint**; per-cell TEST reads limited to a top-5 secondary
   family. Total phase TEST budget ≤6 reads.
7. TEST strata governed by a **TEST-read ledger** with a 2-counted-read
   lifetime cap per stratum (§7.1), backfilled from verified records.

## 2. Objective

Determine whether the AVWAP strategy — with the frozen baseline AVWAP-line
entry and per-instrument-trained exits across 1h/2h/4h domains — is tradable
as a portfolio, and on any standalone subset, of the 17-instrument universe.

Per-instrument×domain training covers 51 cells (17 × 3). Each cell trains
two exit families on TRAIN, selects between them by stability-plane score,
and either joins the candidate portfolio or is declared non-tunable. The
binding multi-instrument claim is a single EXP-018 portfolio-fitness read;
standalone single-instrument claims are available only to the top-5 cells.

## 3. Track and gate structure

> **Amended 2026-06-11:** Track A0 (entry-level band-selection scan) is
> **removed** (FRAMING_ERROR — §11). Track A runs on the frozen **baseline**
> entry events (arm/trigger at the AVWAP line); the band multiplier appears
> only inside Track B Family 2 as an exit parameter.

```
Tier 0 (desk, no runs)
  D0  Registry amendment (multiplicity-registry.md): Phase 011 batch;
      ledger materialized (test-read-ledger.md, verified backfill §7.1);
      cost model declared for all 13 new instruments; all predeclarations
      (§8.5) fixed.
        │
        ▼  GATE G0 (§8.1): predeclaration completeness — no TRAIN read
        │  before every §8.5 item is frozen, EXP-018 threshold first.
        ▼
Track A — Readiness & calibration [0 slots, diag]
      EXP-020-analog substrate readiness (baseline entry events, 2h
      construction, determinism, event rates) on 51 cells; EXP-027-analog
      method calibration for the per-cell event populations; EXP-029-analog
      C#/Python parity re-verification (2h domain).
        │
        ▼  GATE G1 (§8.2): readiness pass per cell — failing cells are
        │  excluded from Track B with the failure recorded.
        ▼
Track B — Exit training [0 slots, TRAIN-only]
      Per cell: FH grid {2,3,4,6,8,11,16,23} + MAD-band-multiplier grid
      (geometric, predeclared) → n-neighbour stability plane (k=1, interior
      points only) → tunability rule → per-cell exit selection by stability
      score → portfolio membership (tunable AND stability ≥ floor).
        │
        ▼  GATE G2 (§8.3): membership set non-empty and composition
        │  threshold met → Track C authorized. Else phase closes
        │  FOUNDATION_NON-TUNABLE.
        ▼
Track C — Portfolio gate [1 one-shot TEST read; PRIMARY ENDPOINT]
      EXP-018 revised portfolio-fitness unit: candidate portfolio C (each
      cell at its TRAIN-selected exit) vs reference book R = Donchian(20).
      Ledgered as a disclosure against every member stratum (§7.1).
        │
        ▼  GATE G3 (§8.4)
        ▼
Track D — Top-k confirmations [≤5 one-shot TEST reads; SECONDARY]
      Top-5 portfolio-member cells by TRAIN stability score (at-cap strata
      ineligible — currently EURUSD-4h). One-shot read per cell, Holm-5,
      R1.2 margins. Standalone-deployment claims only.
```

- The sequencing is **binding**: each step's predeclarations are fixed
  before the next step's data contact. Tracks C and D both run only after
  Track B closes; Track D may run regardless of the Track C verdict (it is
  a separate, predeclared family), but both consume ledger entries.
- **TRAIN/TEST discipline:** Tracks A/B read TRAIN only (boundary = the
  R1.3 1-minute-row timestamp convention, `train_end_ts`; TEST = last 30% of
  the first-70% analysis slice; final 30% global holdout sealed). Tracks C/D
  evaluate frozen selections **once** on TEST.

## 4. Scope discipline

**In scope:** D0 (registry amendment, ledger, cost model, predeclarations);
~~Track A0 band-selection scan~~ (removed 2026-06-11, §11); Track A
readiness/calibration/parity analogs; Track B exit training on 51 cells;
Track C EXP-018 portfolio read; Track D top-5 confirmations. EXP-IDs for
each item are assigned at Stage-1 scoping per registry convention.

**Out of scope (this phase):** the MTF model (deferred, §10); `/ENTRY`,
`/ALPHA`, `/MA-DOMAIN` sweeps (entry signal frozen); any 5m analysis;
any entry-level band rule or tuning (the band is an exit parameter — §11
amendment; entry is the frozen baseline arm/trigger); re-testing
the Phase 010 exit families E1–E5 on the new event population (a possible
future scope); any holdout read (none exists or is implied); any
cross-instrument pooling for per-cell verdicts; post-result cost-model
iteration; grid extension after curves are seen.

## 5. Item specifications

### 5.1 D0 — Registry amendment + governance materialization (Tier 0)

- Amend `multiplicity-registry.md`: Phase 011 batch; Track A0 removal and
  EXP-042 file-drawer disposition recorded; the declared families
  (51-cell training family, top-5 TEST family, portfolio read) recorded; all
  data-dependent design inputs (§1) listed per the Phase 008 §7.4 convention.
- Materialize `docs/signal-registry/test-read-ledger.md` from the verified
  backfill (§7.1).
- Declare the cost model for all 13 new instruments (§7.3) — financing
  rates from broker swap schedules (forex), RT costs estimated from spread
  data + commission schedules. Frozen before any TRAIN read.
- Fix every §8.5 predeclaration. G0 (§8.1) verifies completeness.

### 5.2 Track A0 — REMOVED 2026-06-11 (framing error)

The entry-level band-selection scan originally specified here was removed by
the 2026-06-11 amendment (§11): the band multiplier is an exit parameter
(Phases 004–010; registry `/BAND` is exit/structural), so there is no
entry-level band to select. The arm-at-adverse-band rule that operationalized
it is rescinded; Phase 011 entries use the frozen baseline arm/trigger at the
AVWAP line. The band multiplier is selected per cell in Track B Family 2
(§5.4). EXP-042, executed under the removed specification, is set aside
(MEASUREMENT_COMPLETE — FRAMING_ERROR); its record preserves the original
section text. Power expectations revert to the §7.4 baseline event rates,
measured by Track A. Review:
`docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`.

### 5.3 Track A — Readiness & calibration (0 slots, diag)

- **EXP-020-analog:** substrate readiness for the frozen baseline event
  definition on all 51 cells — event rates, determinism, and 2h-domain
  artifacts. 2h bars are constructed from the 1-minute source with the
  `min_coverage` parameter; determinism and construction verified before
  the exit-training loop.
- **EXP-027-analog:** event-level inference method calibration for the new
  event population (per-instrument calibration; the EXP-027 inference
  machinery itself is unchanged and re-used).
- **EXP-029-analog:** C#/Python parity re-verification for the 2h domain
  and the new-universe instruments (the established parity covers neither;
  the event definition itself is the unchanged frozen baseline).

### 5.4 Track B — Exit training (0 slots, TRAIN-only, 51 cells)

Two exit families, trained independently per instrument×domain cell:

**Family 1 — FH (fixed-horizon) exit** (structure as EXP-033/037, trained
per-instrument):
- Grid: H ∈ {2, 3, 4, 6, 8, 11, 16, 23} domain bars — geometric (≈√2 ratio)
  so a ±1-step neighbourhood spans a comparable proportional range
  everywhere (per domain: 1h grid = 2–23h, 2h = 4–46h, 4h = 8–92h).
- Selection: n-neighbour stability plane (§6), not the one-SE rule.

**Family 2 — MAD-band-target exit** (the original band-target/trend-change
completion framework from HYP-003/HYP-004-R, with robust parameters):
- Band multiplier: not a universal constant; selected per cell from a
  geometric grid over the MAD-bands framework (range and ratio predeclared
  at scope freeze, §8.5; same edge rules as the FH grid).
- Trend-change leg: kept as-is (MA(20,50) regime flip) — a structural
  constant.
- Selection: n-neighbour stability plane (§6).
- Context: this is the "original strategy exit" from the brainstorming
  document — it was never given per-instrument parameters; the baseline in
  EXP-022/028/030 used multiplier 1.0 universally. Sweeping it properly is
  the point.

**Per-cell exit selection (TRAIN-only):**
1. Train both families on TRAIN.
2. Compare by stability-plane score.
3. The better-scoring family becomes the cell's exit. No TEST contact.
4. If neither family is tunable (§6 tunability rule), the cell is
   non-tunable and excluded from the portfolio, recorded as such.

**Portfolio membership rule:** a cell enters the candidate portfolio iff its
leading family is tunable **and** its stability score clears the predeclared
floor (§8.5). Validation within TRAIN is split-half stability (part of the
tunability rule); no TEST contact for membership.

### 5.5 Track C — Portfolio-fitness gate (1 one-shot TEST read; PRIMARY)

The candidate portfolio C (each member cell at its TRAIN-selected exit) is
evaluated through the **revised portfolio-fitness unit (EXP-018)**, the
third component of the frozen qualification suite (Phase 003b):

> Does the candidate portfolio C (trained per-instrument) add incremental
> edge beyond a reference book R, where R defaults to Donchian(20)?

- One one-shot TEST read, no multiplicity penalty — the single binding test
  for any multi-instrument claim.
- Go/no-go threshold predeclared before any TRAIN read (§8.3) — under
  realistic per-cell power this test decides the phase, so its threshold is
  the first predeclaration to fix, not the last.
- Ledgered as a **disclosure** against every member stratum (§7.1); at-cap
  strata (EURUSD-4h) may contribute with disclosure.
- Why this is the right primary gate: it does not require every cell to be
  positive (weak cells are absorbed); Donchian(20) is a simple, defensible
  benchmark; it tests incremental edge — the deployment-relevant question —
  not standalone significance; it was validated in Phase 003b (flipped
  REFUTED→SUPPORTED with the L2 removal). It replaces both the old
  equal-weight pooled mean (which let BTCUSD veto every domain) and the
  per-cell-verdicts-first structure (which spends ~51 TEST reads on tests
  Holm-across-51 nulls out except for very large effects).

### 5.6 Track D — Top-k per-cell confirmations (≤5 one-shot TEST reads; SECONDARY)

Per-cell significance buys exactly one thing: a standalone
single-instrument deployment claim. It is purchased only where affordable:

- **Family:** top **k = 5** portfolio-member cells by TRAIN stability score
  (ties broken by event count, descending). k fixed in this design.
  **At-cap strata are ineligible** (currently EURUSD-4h); an at-cap cell in
  the top-5 is skipped and the next-ranked eligible cell takes the slot.
- **Estimand:** net per-event expectancy (absolute, frozen CONSERVATIVE
  costs + predeclared per-instrument financing).
- **Test:** one-shot TEST read per cell, subject to the ledger cap.
- **Multiplicity:** Holm across the k=5 family.
- **Verdict:** net CI_low > 0 at one-sided α = 0.05, plus R1.2 margin
  calibration for small-n cells.
- **Hard no-promotion:** per-cell TEST verdicts are final. No
  cross-instrument pooling at this level. Cells outside the top-5 receive no
  individual TEST read this phase; their evidence is their contribution to
  the portfolio test.

**Phase TEST budget: 1 (Track C) + ≤5 (Track D) = ≤6 reads**, each entered
in the ledger — versus ≤102 (or ≤51 after slot-sharing) under the
superseded per-cell-first structure.

## 6. Robust parameter selection: n-neighbour stability plane

The key methodological upgrade. The Phase 008 H\* selection (one-SE rule)
and the Phase 010 exit screen (max-min worst-half) share a weakness: they
select a single point from a noisy curve, fragile under multiple local
maxima or flat plateaus. The FH(H) TRAIN net curve typically has a rising
phase (short H: noise), a plateau or knee (edge stabilizes), and a decaying
phase (financing erodes edge, trend truncation). The argmax is always noisy;
the one-SE rule still selects a single boundary point — and on a flat
plateau different split-half samples produce different boundaries
(`h_star_stable = false`, the Phase 008 symptom).

**Method.** For each candidate θ in the grid:
1. Score θ by net expectancy on TRAIN.
2. Neighbourhood `N(θ, k)` = k grid steps each side. **k = 1 for both
   families** (3-point neighbourhood), fixed here, never tuned
   per-instrument.
3. Stability score `S(θ)` = mean score over `N(θ, k)`.
4. `θ* = argmax S(θ)` over **interior grid points only** — the centre of
   the best stable region.

**Grid geometry and edge rules (predeclared):**
- Grids are geometric (log-spaced) so ±1 step is proportionally uniform; a
  linear grid would make "stability" mean different things at each end.
- Endpoint grid values are **ineligible** as θ\* (truncated neighbourhoods
  bias their stability scores).
- If the stability argmax lands on an endpoint, the cell is **non-tunable**
  for that family — the optimum lies outside the grid, and extending the
  grid after seeing the curve would be tuning. Grids must be chosen wide
  enough at scope freeze that this is rare.

**Tunability rule (operational flat-plane definition).** A cell is tunable
for a family iff **both**:
1. *Separation:* `max S(θ) − median S(θ) > 1 × SE`, where SE is the
   bootstrap standard error of the cell's TRAIN net mean (interior θ only).
   The multiplier (1×) is fixed here, before any curves are seen.
2. *Split-half agreement:* the θ\* selected on each chronological half of
   TRAIN lies within ±1 grid step of the full-TRAIN θ\*.

Fail either → non-tunable: no selection, family excluded for that cell,
outcome recorded.

**Comparison with the one-SE rule:**

| Property | One-SE rule | n-neighbour stability |
|----------|------------|----------------------|
| Noise sensitivity | High — boundary point selection | Low — region averaging |
| Split-half consistency | Fragile (`h_star_stable = false`) | High — plateau centres; agreement enforced, not hoped for |
| Flat plateau handling | Picks smallest boundary | Picks plateau centre |
| No-signal detection | Always selects something | Can fail to select (operational rule) |
| Computational cost | Grid sweep + bootstrap SEs | Grid sweep + neighbourhood means + one bootstrap SE |

**Application:**

| Exit family | θ | Grid | Neighbourhood |
|-------------|---|------|---------------|
| FH H\* | Horizon H | {2, 3, 4, 6, 8, 11, 16, 23} (geometric) | k=1 (±1 step) |
| MAD-band multiplier | Multiplier m | Geometric grid, predeclared at scope freeze | k=1 (±1 step) |

The stability plane is computed on TRAIN only.

## 7. Methodological guardrails

### 7.1 TEST-read ledger (new governance)

TEST strata are finite; a "new event population" (band change, new exit)
does not reset them. `docs/signal-registry/test-read-ledger.md` records one
row per instrument×domain TEST stratum in two categories:

- **Counted reads:** any read where the stratum's events enter a binding
  **stratum-specific** inference. Count toward the cap.
- **Disclosures:** exposures without stratum-level selection or
  stratum-specific inference — pre-split full-slice experiments
  (EXP-022/028/030/034 et al.) and mechanism-science reads with no strategy
  estimand (EXP-040). Recorded and disclosed downstream; not counted.

**Hard cap: two lifetime counted reads per stratum.** A second read is
disclosed as weakened-evidence. A stratum at cap is treated like the EURUSD
holdout — capped, permanently; no further stratum-specific claims.

**Portfolio-aggregate rule:** the Track C read makes no per-stratum claim;
it is ledgered against every member stratum as a disclosure, not a counted
read. At-cap strata may contribute to the portfolio test (with disclosure)
but are ineligible for Track D.

**Backfill (verified against experiment records, 2026-06-11):**

| TEST stratum | Counted reads | Disclosures |
|--------------|---------------|-------------|
| EURUSD-4h | **2 — EXP-037 (FH exit), EXP-038 (BTC-exit baseline). AT CAP.** | EXP-034 et al. (full-slice, pre-split); EXP-040 (mechanism) |
| USTEC-4h | 1 — EXP-037 | EXP-034 et al.; EXP-040 |
| XAUUSD-4h | 1 — EXP-037 | EXP-034 et al.; EXP-040 |
| All other strata (incl. all 1h/2h, BTCUSD-4h, all 13 new instruments) | 0 | 1h: full-slice exposure in pre-split experiments and EXP-040; 2h and new instruments: none |

EXP-039 was TRAIN-only (the provisional EXP-041 slot was never used) — no
ledger entry. Every Phase-011 scope states, per stratum it intends to read,
the prior counted-read tally.

### 7.2 Data, splits, and disclosures

- **Holdout:** per INFR-002 declaration (Phase 010 design §5/C1), the final
  30% of each instrument is global holdout, sealed. The first 70% splits
  70/30 TRAIN/TEST by the 1-minute-row timestamp convention.
- **Asset universe (17):** old — BTCUSD (TRAIN+TEST+holdout; RT 16 bps, may
  be non-tradable per-instrument), EURUSD (TRAIN+TEST only; holdout
  contaminated since EXP-032), USTEC, XAUUSD (holdouts sealed). New (all
  VAL-003 PASS 2026-06-11): GBPUSD 1,273,657 rows; USDJPY 1,274,170; USDCHF
  1,270,134; USDCAD 1,269,870; AUDUSD 1,270,486; NZDUSD 1,271,158; EURJPY
  1,279,097; GBPJPY 1,278,719; AUDJPY 1,277,971; US500 1,187,767; US2000
  1,208,112; DE30 1,025,743 (truncated); JP225 1,157,882.
- **DE30 disclosure:** coverage truncated ~5 months short (history ends
  2026-01-16); boundaries derive from its own timeline. Decision pending
  (§8.5): use as-is with truncated-history disclosure in every result
  artifact, or re-collect under an alternative broker symbol before first
  analytical use.
- **EURUSD disclosure:** permanently TEST-capped (no holdout read exists); a
  EURUSD-only deployment claim requires TEST evidence only; contributes to
  EXP-018 with the TEST-capped disclosure in all artifacts if the portfolio
  passes; EURUSD-4h additionally at the TEST read cap (§7.1).

### 7.3 Cost model (frozen)

Frozen at EXP-030 CONSERVATIVE values, extended to the new universe; frozen
before any TRAIN read, no post-result iteration:

| Instrument | Financing (bps/day) | RT (bps) | Source |
|------------|-------------------|----------|--------|
| BTCUSD | 10.0 | 16.0 | Phase 008 financing (adverse-side) |
| EURUSD | 0.6 | 1.2 | Phase 008 financing |
| USTEC | 1.2 | TBD at D0 | Phase 008 financing |
| XAUUSD | 1.2 | TBD at D0 | Phase 008 financing |
| 13 new instruments | TBD at D0 | TBD at D0 | Broker swap rates (forex); spread + commission estimates (indices). Predeclared per instrument before any TRAIN read. |

### 7.4 Honest power statement

Per-instrument training means each instrument's 4h bucket has only ~90
TRAIN events at the baseline entry rates (Track A measures the realized
per-cell rates); TEST is sparser still (~27–40 events per 4h cell). Per-cell significance after multiplicity
correction across dozens of cells is close to unreachable except for very
large effects. Therefore:

- The primary endpoint is the single portfolio-level test (§5.5) — one
  test, no multiplicity penalty, maximum power, the deployment question.
- 2h (~180 TRAIN events at band=1.0 rates) provides ~2× the power of 4h for
  exit training; 1h (~350–400) has the most events for training sweeps,
  with the trained exit verified on the sparser TEST stratum. 2h is
  introduced precisely as the middle ground: half the overnight financing
  burden of 1h, ~2× the events of 4h — if any domain can show
  per-instrument tradability across multiple symbols, 2h is the candidate.
- Per-cell verdicts exist only in the Holm-5 secondary family (§5.6).
- **The realistic positive outcome of this phase is a portfolio-fitness
  pass with few or zero individually-significant cells. That outcome is a
  success, not a partial failure.**

### 7.5 Prior-work dispositions

Prior-work dispositions (records retained; none creates a re-read license —
§7.1 governs):

| Prior result | Reason | Disposition |
|-------------|--------|-------------|
| EXP-028 (HYP-004-R supported) | Baseline entry, original fixed exits | Retained as baseline event-level support; not directly comparable to per-instrument-trained exits or the 17-instrument universe |
| EXP-030 (INCONCLUSIVE on costs) | Baseline entry, equal-weight pooled, fixed exits | Cost-veto analysis may differ after per-instrument exit training |
| EXP-037 (FH H\*=12 passes TEST) | Pooled-curve H\* on existing 4h strata | Its three TEST reads (EURUSD/USTEC/XAUUSD 4h) counted in the ledger |
| EXP-039 (EXIT_FLAT) | Existing-universe TRAIN-only exit families E1–E5 | E1–E5 re-test on the new universe or new scope is possible later, not this phase. TRAIN-only — no ledger entry |

Retained: EXP-018 (now the primary endpoint); EXP-020 (state machine
unchanged; 2h needs its own readiness check); EXP-027 (inference machinery
re-used with per-instrument calibration); EXP-029 (parity established;
re-verify for 2h + the baseline event population); VAL-001/002/003 (data integrity; new
universe admitted); the frozen three-component qualification suite (strict
gate stack, ratified-loose referee, revised portfolio-fitness unit); the
30% global holdout convention.

## 8. Gate specifications

### 8.1 G0 — predeclaration completeness (before any TRAIN read)

D0 closes only when: the ledger is materialized with the §7.1 backfill; the
cost model covers all 17 instruments; the EXP-018 go/no-go threshold is
fixed; the MAD-band grid is fixed; the stability floor is fixed; and the
remaining §8.5 items are ratified. The former A0 reference horizons and
event-count floor are retained only as the moot EXP-042 record. No Track A/B
data contact before G0 passes.

### 8.2 G1 — readiness (per cell, lenient)

A cell proceeds to Track B iff EXP-020-analog readiness passes (event
determinism, construction integrity, no domain artifacts) and the
EXP-027-analog calibration covers its event population. Failing cells are
excluded with the failure recorded; they do not consume anything.

### 8.3 G2 — portfolio authorization (strict, predeclared)

Track C is authorized iff the candidate-portfolio membership set meets the
predeclared composition threshold (§8.5 item 5 — e.g., minimum member-cell
count and instrument diversity; the exact rule is the first predeclaration
fixed at D0). If membership is empty or below threshold, the phase closes
**FOUNDATION_NON-TUNABLE** with no TEST read spent.

The Track C verdict itself: EXP-018 incremental-edge rule at its
predeclared threshold → **PORTFOLIO_PASS** / **PORTFOLIO_FAIL**.

### 8.4 G3 — Track D adjudication

Per-cell: Holm-adjusted net CI_low > 0 (one-sided α = 0.05) **and** ci_low
clears the R1.2 null-calibration margin for the cell's TEST structure.
Verdicts are final (hard no-promotion). Output: zero or more
**CELL_CONFIRMED** standalone packages.

### 8.5 D0 predeclarations (fixed at D0; A0 item now moot)

1. **EXP-018 go/no-go threshold** — first to fix; the primary endpoint.
2. Cost model values for the 13 new instruments (+ USTEC/XAUUSD RT).
3. A0 scan parameters: **moot after Track A0 removal**; retained in
   `D0-predeclarations.md` and §5.2 only as the EXP-042 historical record.
4. Stability-score floor for portfolio membership (as a fraction of the
   cell's TRAIN mean or another predeclared reference) — without a floor,
   noise-dominated cells dilute the portfolio test.
5. G2 composition threshold (minimum membership for Track C).
6. MAD-band-multiplier grid (range and ratio; same edge rules as FH).
7. 2h `min_coverage` parameter and construction spec.
8. DE30: as-is with disclosure vs re-collection (§7.2).

## 9. Phase outcome criteria

| Outcome | Condition | Consequence |
|---------|-----------|-------------|
| **FOUNDATION_NON-TUNABLE** | G2 fails (membership below threshold) | No TEST read spent; the AVWAP baseline entry substrate with per-instrument exits is not tunable; `/ENTRY` exploration or substrate change becomes the path |
| **PORTFOLIO_PASS** | Track C passes its predeclared threshold | Multi-instrument claim established (incremental edge over Donchian(20)); the portfolio package is frozen (hash-pinned) as the carry-forward candidate; MTF (Phase 012+) becomes admissible on the tradable cells |
| **PORTFOLIO_FAIL** | Track C fails | TEST evidence final; per-cell CELL_CONFIRMED packages (if any) stand alone; programme routes to `/ENTRY` or substrate-level revision |
| **CELL_CONFIRMED (×n)** | Track D Holm passes | Standalone single-instrument deployment claims, independent of the portfolio verdict |

A PORTFOLIO_PASS with zero CELL_CONFIRMED cells is a success (§7.4).

## 10. Non-goals

- **MTF (deferred):** the multi-timeframe model (signal 4h / execution
  5m–30m) remains a valid subsequent direction, deferred until the
  per-instrument foundation is complete, the tradable instruments×domains
  and exits are known, and the execution-layer design is grounded in actual
  results, not speculation.
- No holdout read of any kind; no implication of one.
- No entry-parameter sweeps (MA 20/50 and exponent 0.75 stay frozen;
  `/ENTRY`, `/ALPHA`, `/MA-DOMAIN` deferred; Track A0 removed).
- No 5m analysis; no per-instrument entry-band tuning; no cost-model
  iteration; no grid extension after curves are seen; no cross-instrument
  pooling for per-cell claims; no E1–E5 re-test this phase.

## 11. Amendment log

### 2026-06-11 — initial draft (no data contact)

Drafted from `docs/planning/phase-011-redesign-per-instrument-foundation.md`
after operator review. Incorporates the verified TEST-read ledger backfill
(EXP-037: EURUSD/USTEC/XAUUSD 4h; EXP-038: EURUSD-4h; EXP-039 TRAIN-only,
no entry; EXP-040 disclosure-only), the counted-read/disclosure ledger
taxonomy, the portfolio-aggregate disclosure rule, and the EURUSD-4h
at-cap Track-D ineligibility. Then-open predeclarations listed in §8.5; none
resolved by data.

### 2026-06-11 — D0 closed, G0 PASS (no data contact)

D0 executed and operator-ratified: multiplicity registry amended (Phase 011
batch), `docs/signal-registry/test-read-ledger.md` materialized with the
§7.1 verified backfill, 17-instrument cost model declared, and all §8.5
predeclarations frozen in `D0-predeclarations.md` (P1 EXP-018 threshold
fixed first: ci_low_1s > R1.2 margin AND boot_p < 0.05, one-sided α=0.05,
no extra materiality floor; P3 A0 horizons {4,8,16}, floor 30 TRAIN events;
P4 stability floor S(θ\*) ≥ +1×SE; P5 G2 composition ≥5 cells over ≥3
instruments; P6 MAD grid {0.5,0.7,1.0,1.4,2.0,2.8,4.0,5.7}; P7 2h
`min_coverage=0.90`; P8 DE30 as-is with disclosure). **Correction recorded:**
§7.3's EURUSD RT "1.2 bps" was a transcription error — the frozen EXP-030
CONSERVATIVE value 3.0 bps RT is authoritative (USTEC 5.0, XAUUSD 6.0,
BTCUSD 16.0). G0 PASS; Tracks A0/A/B data contact authorized.

### 2026-06-11 — `/BAND` entry-rule semantics fixed (no data contact)

Stage-3 implementation review of EXP-042 found that in the frozen substrate
the band multiplier plays **no role in entry** (arm = close on the opposite
side of the AVWAP; trigger = AVWAP recross; the multiplier only sets the
event-row band/target levels) — a naive multiplier sweep would leave the
event population identical at every band, making Track A0 vacuous. Operator
ratified (pre-TRAIN-read): Phase 011 events use the **arm-at-adverse-band**
rule — bull arms when a completed close < `AVWAP − b×MADspread` (bear
mirrored); trigger unchanged. Consequence disclosed: b=1.0 does **not**
reproduce the historical Phase 004–010 population (which corresponds to
b=0 in this parameterization; "band=1.0 events" in §1.1/§5.2/§7.5 referred
to exit targets); §7.5 non-comparability applies to the entire A0 grid
including 1.0, and the §5.2 "near-subset" conjecture is corrected — every
arm-at-band population is a subset of the *baseline* population in trigger
terms only where the deeper pullback occurred. Implemented as
backward-compatible parameters on `xen.avwap.generate_avwap_events`
(defaults reproduce the frozen baseline bit-for-bit).

### 2026-06-11 — pre-execution review fixes F01–F05 (no data contact)

Adversarial review of the approved EXP-042 package, all fixes applied before
any TRAIN read: **F01 (Critical)** — `load_train_slice` no longer sorts the
full file (a full-file sort would pull TEST/holdout rows through the scan
engine); it now collects the first TRAIN file-order rows (count from Parquet
metadata) and re-asserts sortedness on the collected slice, relying on the
VAL-001 rev. 3 / VAL-003 validated chronological source order. **F03
(Major)** — DEGENERATE_FLOOR no longer silently freezes the band: the
selection is reported but the freeze is withheld pending operator
adjudication (accept-with-disclosure vs early FOUNDATION_NON-TUNABLE; no
re-ranking/grid extension permitted). **F04 (Major)** — the `xen.avwap`
parameterization now carries a committed regression suite
(`python/tests/test_avwap_band_param.py`): baseline fixture anchor (69
events, multiplier-invariant in baseline mode), determinism, band-count
monotonicity, bull/bear adverse-band arm unit cases (20/20 project tests
pass). **F05 (Minor)** — design/registry status headers updated to the
ratified G0 state. **F02 (Major, fix rejected)** — the gross/H=8/no-cost
selection statistic is a frozen G0 predeclaration; replacing it post-G0
would itself violate governance. The proxy-alignment risk is recorded as a
standing disclosure in the EXP-042 scope and carries into Tracks B/C.

### 2026-06-11 — A0 selection statistic made scale-free (no data contact)

Operator review caught a unit/scale flaw in the A0 selection rule: a raw
cross-cell median of gross-per-event would be dominated by high-volatility
instruments even with returns in bps. Replaced with within-cell band
ranking → best median rank across cells (worst rank imputed where a band
fails the event-count floor; wider-band tie-break). The statistic is now
fixed in §5.2; only the reference horizons and event-count floor remain
open in §8.5.

### 2026-06-11 — Track A0 removed; EXP-042 set aside (FRAMING_ERROR)

Post-execution review of EXP-042
(`docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`) found the
arm-at-adverse-band entry rule (the 2026-06-11 `/BAND` entry-rule-semantics
amendment above) was a framing error: across Phases 004–010 the band
multiplier was always an **exit parameter** — it sets the favorable/adverse
target levels frozen at trigger and never enters the bounce definition —
and the registry `/BAND` branch is defined as exit/structural. The earlier
amendment's diagnosis was correct (the band plays no entry role in the
frozen baseline, so a naive entry-level sweep is vacuous) but its
prescription was wrong: the correct conclusion is that **no entry-level band
selection exists**, not that entry should be redefined to create one.
Consequences, operator-ratified:

1. **EXP-042 is set aside** — disposition `MEASUREMENT_COMPLETE —
   FRAMING_ERROR`. It measured a filtered deep-pullback subpopulation;
   band=1.0 won on event availability, not exit quality; the
   DEGENERATE_FLOOR adjudication is moot and the freeze was never granted.
   No decision is based on its results. Code/results retained as a
   negative-process record (0 slots, 0 TEST reads).
2. **Track A0 is removed** (§5.2 replaced by a removal stub; the original
   specification text is preserved in the EXP-042 record and the
   comprehensive index; §3 track structure reads A → B → C/D). The §1.1
   "selected, not asserted" band correction is itself corrected — the
   band=2.0 working-candidate discussion is moot.
3. **The arm-at-adverse-band entry rule is rescinded.** Phase 011 events use
   the frozen baseline arm/trigger at the AVWAP line, identical to Phases
   004–010. The `xen.avwap` parameterization and its regression suite are
   retained (defaults reproduce the baseline bit-for-bit); the non-default
   arm rule is unused.
4. **The band multiplier lives entirely in Track B Family 2 (§5.4)** — the
   per-cell MAD-band-target exit sweep over the P6 grid — which is unchanged
   and was always the correct home. `/BAND` slot accounting follows Track B
   registration; no slot was consumed by A0.
5. **Power expectations revert to the §7.4 baseline event rates** (the
   EXP-042 power statement described the filtered population and does not
   transfer). Track A readiness (EXP-020-analog) measures the actual
   baseline rates on all 51 cells.
6. **Prior-result comparability is restored:** with the baseline entry
   unchanged, §7.5's "not directly comparable — band change" rationale no
   longer applies to the entry population; non-comparability now stems only
   from per-instrument exit training and the new universe.

Process lessons recorded in the review §6 (design↔scope traceability; review
must check a parameter's historical role, not only implementation
correctness; registry branch definitions are the authority).
