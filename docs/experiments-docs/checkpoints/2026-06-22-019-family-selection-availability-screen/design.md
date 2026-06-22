# Phase 019 — Family-Selection Availability Screen (family-agnostic)

**Status:** **OPEN — G0 PASS (2026-06-22).** D0 ratified and frozen (`D0-predeclarations.md`); the **D2
admission-gate bite-check is GREEN** (`bite-check/`, report sha256 `208dfb3f…`, byte-identical second pass) —
the gate is confirmed not-vacuous (pure-noise axis admitted 0.0248 ≤ FWER 0.05), not-impossible (planted
+0.20-ATR/8-cell axis admitted power 1.0), band-invariant {0.025,0.05,0.10}, and self-calibrating under
inflated per-cell FP. **Pipeline opens at EXP-086 (Screen M).** **This is NOT a candidate family** — it is a
family-agnostic
*selection* phase (analogous to Phase 017 being a methodology phase, not a CF), whose deliverable is
*a decision about which entry-side family to open next, and in what order* — backed by cheap
Δ-over-random availability numbers, not a tradable strategy.
**Date:** 2026-06-22 (design).
**Opened by:** operator selection of the next programme direction (2026-06-22), after CF-CAPGEO-001
RETIRED at G-018 (Phase 018 retrospective) and the two independent post-018 reviews reconciled in
[`../../reflections/2026-06-22-reconciliation-and-family-selection-phase.md`](../../reflections/2026-06-22-reconciliation-and-family-selection-phase.md).
**Discipline (binding throughout Phase 019):** TRAIN-only availability screens on the VAL-005 5-year
data; **0 candidate slots, 0 counted TEST reads, holdout never touched**; all return/range metrics on
**real prices**; deterministic (fixed seeds, byte-identical second pass); no parameter tuned against any
TEST or holdout data; **per-stratum reporting, never pooled-as-verdict** (LESSON-001).

---

## 1. Why Phase 019 exists (measure availability *first*, family-agnostically)

Three candidate families have now been taken to closure with the global holdout still sealed:
CF-AVWAP-001 (ANCHOR_MOVE_FLAT), CF-HA-HARAMI-001 (CLOSE_FAMILY), CF-CAPGEO-001 (NOT_CONFIRM). The
two independent post-018 reviews ([cold autopsy](../../reflections/2026-06-22-cold-autopsy-three-families-next-family.md);
[next-family recommendation](../../reflections/2026-06-22-next-family-recommendation.md)) converge on
one diagnosis, re-derived from primary evidence:

> **Single-instrument, event-driven, price-geometry entries carry no signal-conditional favourable
> price excursion beyond a matched random control — *availability ≈ random*.** Established twice with
> matched-control designs: **EXP-047** (AVWAP event MFE ≈ control MFE on every domain — "the bounce
> trigger does not access privileged move sizes") and **EXP-081** (harami `MFE_med` Δ-over-random
> −0.140, real>random **17/46** cells; AVWAP +0.061, **28/46** — coin-flip). The whole downstream stack
> (exit/capture geometry, costs, conditioning, anchors, sizing) is exhausted *and* exonerated on these
> entries — EXP-084 is **exit-invariant** (0/11 exit arms had a positive OOS CI_low).

The programme's historical mistake was to **measure availability last** — build an entire family around
a pattern's logic, then discover only at the end (EXP-047 in Phase 013; EXP-081 in Phase 018) that the
entry never accessed a privileged move. Phase 019 institutionalises the fix: **availability is the
selection gate, measured first, family-agnostically, before a single slot is committed.** A few seconds
of TRAIN-only gross compute with a matched-random null repeatedly relocated the binding constraint in
prior phases (retrospective §2.6); here it *chooses the next family* for that same near-zero cost.

This phase changes no verdict about any market signal and reads no TEST stratum. It decides only which
entry-side information axis (if any) earns the next candidate slot — and in what order.

## 2. The reconciled frame: the availability 2×2

Every family so far lived in **one** cell of a 2×2 over `{information source} × {target}`, and that cell
is dead:

```
                    DIRECTIONAL target              MAGNITUDE / range target
single-series   │  TESTED → dead (EXP-047/081/084) │  UNTESTED — low prior; typical range flat
                │                                   │   (EXP-081 MAE_q90 9/46), tail-only hint
cross-sectional │  UNTESTED (lead bet, mechanism)   │  UNTESTED
```

Three cells are untested, and **all three are cheaply screenable with the same EXP-081-clone
availability read** (0 slots, 0 OOS reads, TRAIN-only). The disciplined move is *screen, then commit* —
let the Δ-over-random numbers select the family rather than picking blind.

**The selection is a cascade; the high-stakes decision is the in/out admission gate, not the
winner-pick.** The metric only sets exploration *order*; the multiplicity risk lives at the threshold
that admits an axis to the explore-list at all. Run several axes × many cells and a **pure-noise** axis
can clear a single-axis-calibrated band *somewhere* (cross-sectional ranking over 16 instruments
manufactures the most cells → worst offender). So the admission gate is calibrated against a
**multiplicity-adjusted / permuted-axis null at the realized cell count** (D2 / §5.3 discipline), not the
single-axis null band. A selection phase whose method is "screen many, keep the best" must inherit the
programme's own file-drawer/multiplicity discipline into the screening method itself, or it re-imports
the exact selection bias 16 phases were spent avoiding.

## 3. The single question

> For each untested information axis (single-series **magnitude**, **cross-sectional** relative strength,
> and optionally **order-flow**), does a TRAIN-only conditioned entry produce signal-conditional
> availability that beats a **matched random control** by more than a **multiplicity-adjusted permuted-axis
> null** would, at the realized per-cell count — and if so, which axes are admitted to the explore-list,
> ranked best-first by the frozen Δ-over-random metric?

The output is a **ranked admit/exonerate inventory** of information axes, not a tradability or edge claim.
Every admitted axis is *eventually* opened as a candidate family at its own future G0/D0; ranking
sequences the scarce TEST-read budget (the first family opened gets the freshest reads and could end the
search if it confirms).

## 4. Binding inheritances (carried from the reconciliation + retrospectives)

1. **Availability-first selection** (§1). Availability is the gate, measured before any slot.
2. **Calibrated / data-derived thresholds, not magic numbers** (retrospective §5.3). The binding admission
   gate is a permuted-axis null calibrated by a **bite/fixture check** before G0 — confirmed neither
   vacuous (admits regardless) nor impossible (rejects a true non-random axis).
3. **Match the metric to the mechanism's shape** (retrospective §2.3). Screen M's magnitude read is **split**
   into typical-range and tail/bimodality — never pooled into one `|move|` number, because EXP-081 already
   shows the pooled number is null and the only hint is tail-concentrated.
4. **A magnitude "pass" is a long-vol finding, not a tradable edge** (reconciliation §3 harvest model). Any
   magnitude admission routes to a properly-scoped volatility-expansion family under a **two-sided cost**
   (straddle/breakout), never a directional claim — the gross→net trap that ate AVWAP must not recur.
5. **Per-stratum / per-cell adjudication; pooled is a disclosure** (LESSON-001).
6. **Determinism** (retrospective §2.8): fixed seeds; a second full pass is byte-identical.
7. **Real-price discipline:** all returns/ranges on real prices; HA/Renko brick prices never enter a
   return/range metric.
8. **Holdout sealed; 0 counted TEST reads.** TRAIN sub-split only; the analysis-TEST stratum and the
   final-30% holdout are never sliced or materialized (the EXP-080/081 readiness/characterization
   convention — availability disclosure, no strategy estimand, no stratum-specific binding inference).

## 5. Experiment slate

EXP-IDs pre-assigned (next free ID = EXP-086; EXP-079 was reserved-inactive in Phase 017 and is not
reused). Each screen is an **EXP-081 clone** — same matched-random control, same per-cell paired
Δ-over-random table, same TRAIN-only disclosure status — with the **information axis** and the
**availability endpoint** swapped. Screens are independent; none gates another.

### EXP-086 — Screen M: single-series magnitude / non-directional availability

**Question:** Conditioned on existing single-series compression primitives (HA-harami inside-bar; a clean
NR/inside-bar primitive), does forward availability beat a matched within-instrument random control on
**two separately-reported reads** — (i) **typical-range** (`max(MFE,MAE)` / `MFE+MAE`, ATR-normalised)
and (ii) **tail/bimodality** (`tailmass`, `q05`, dip-test; plus a direct re-examination of EXP-074's
`msofar_atr` adverse-tail separation *as predictable magnitude*) — and does the predictable range clear a
**two-sided cost** (the magnitude-budget check)?
**Why first:** cheapest way to *close the single-series quadrant* of the 2×2 — not a pre-commitment.
The prior is **low** (EXP-081 `MAE_q90` Δ-over-random −0.719, real>random only 9/46 → typical range is
not elevated; the only positive hint is the rare tail, `tailmass` 0.0526 vs 0.0437).
**Artifacts:** `python/experiments/EXP-086/`; TRAIN-only; 0 slots; 0 TEST reads.
**Pass criteria (admission, D0/D5):** *either* read (typical-range **or** tail) exceeds the
multiplicity-adjusted permuted-axis admission gate (D2) at the realized cell count. **A tail-only pass is a
long-vol admission** (routes to CF-VOLEXP-001 under the §4.4 harvest model), not a directional edge. **Kill**
(exonerate the single-series-magnitude cell) iff *both* reads fall in the null band.

### EXP-087 — Screen X: cross-sectional relative-strength availability

**Question:** Conditioned on **basket-relative momentum / divergence rank** across the synchronized
16-instrument universe (constructible from the existing VAL-005 5-year dataset, **zero new collection**),
does signal-conditional favourable excursion of an entry beat a matched within-instrument random control
(the EXP-081 favourable-availability read, re-pointed at the cross-sectional conditioning)?
**Why the a-priori favourite (mechanism, not evidence):** the dead cell is specifically *single-series*
price geometry; cross-sectional relative strength sources its edge from the *relationship* between
instruments — a demonstrably non-random anomaly across asset classes elsewhere — which is exactly the axis
the programme has never varied. It must nonetheless **earn** first place on the screen like any other axis.
**Multiplicity caution:** ranking over 16 instruments manufactures the most cells → the binding admission
gate (D2 permuted-axis null) matters most here.
**Artifacts:** `python/experiments/EXP-087/`; TRAIN-only; 0 slots; 0 TEST reads.
**Pass criteria (admission, D0/D5):** favourable-availability Δ-over-random exceeds the
multiplicity-adjusted admission gate at the realized cell count. **Kill** (exonerate cross-sectional price
information) iff it reproduces the ≈-random pattern.

### EXP-088 — Screen F: order-flow / liquidity-imbalance availability (optional runner-up)

**Question:** Conditioned on tick-volume / volume-at-price imbalance extremes, does availability beat a
matched random control?
**Status:** **reserved-conditional** — run only if the operator wants a third comparison after M and X
(it brings genuinely orthogonal *flow* information but carries a lower prior: EXP-046 found tick-volume
construction inert once, and tick volume is broker-dependent).
**Artifacts:** `python/experiments/EXP-088/`; TRAIN-only; 0 slots; 0 TEST reads.
**Pass criteria (admission, D0/D5):** as Screens M/X — exceeds the multiplicity-adjusted admission gate.

## 6. D0 decisions required before G0

Ratify in `D0-predeclarations.md` before any result-producing code:

- **D1 — Matched-random control & substrates** (frozen): the within-instrument / within-substrate
  matched-random null (reuse the EXP-080/081 `SUB-RANDOM` construction and readiness scaffolding), the
  compression primitives for Screen M, the cross-sectional ranking construction for Screen X (universe,
  lookback, rank/divergence definition, rebalance cadence), and the flow primitive for Screen F. Member
  cells, domains ({15m,1h,4h}, the CF-CAPGEO scope), seeds.
- **D2 — Two thresholds, bite-calibrated** (no magic numbers — retrospective §5.3): **(a)** the descriptive
  per-cell null band (≈17/46–28/46 cells-beat-random, EXP-081 baseline; reporting only); **(b)** the
  **binding multiplicity-adjusted admission gate** — a permuted-axis / shuffled-conditioning null at the
  realized cell count and a frozen FWER, **bite-checked** (neither vacuous nor impossible) before G0, with
  the routing shown invariant across a pre-registered sensitivity band.
- **D3 — Availability endpoints** (frozen): Screen M's **split** typical-range and tail/bimodality reads
  (kept separate, never pooled) + the magnitude-budget two-sided-cost check; Screen X's favourable-availability
  read; Screen F's read. All ATR-normalised, real prices.
- **D4 — TRAIN-only disclosure accounting:** confirm each screen reads the TRAIN sub-split only
  (`[0, int(analysis_rows·0.7))`), makes no stratum-specific selection/inference, and is therefore a
  **disclosure, not a counted read** (EXP-080/081 precedent); `test-read-ledger.md` unchanged; holdout never
  sliced.
- **D5 — G-019 mechanical verdict rule** (§7): the exact admit/exonerate rule per axis and the ranking metric.
- **D6 — Determinism & real-price discipline:** fixed seeds, byte-identical second pass; all returns/ranges
  on real prices.

## 7. G-019 gate outcome criteria

G-019 is adjudicated after the run slate (EXP-086, EXP-087, and EXP-088 if opened). The verdict is a
**ranked inventory**, not a single PASS/FAIL.

| Per-axis outcome | Criteria | Consequence |
| --- | --- | --- |
| **`ADMITTED`** | The axis's availability read exceeds the D2 multiplicity-adjusted admission gate at the realized cell count (per-stratum, not pooled). | The axis earns a candidate family; it is **queued for opening at its own future G0/D0**, ordered best-first by the frozen Δ-over-random metric. A **tail-only** Screen-M admission is queued as a *volatility-expansion* family under the §4.4 two-sided-cost harvest model (long-vol, not directional). |
| **`EXONERATED`** | The axis falls in the null band on every read (and, for Screen M, on *both* the typical-range and tail reads). | That cell of the 2×2 is **dead**; recorded in the file drawer, not reopened without a genuinely new lever at a fresh D0. |
| **`INCONCLUSIVE`** | Power-limited at the realized cell count (the permuted-axis null cannot separate signal from noise). | Disclosed; the axis is neither admitted nor exonerated; a re-scope at finer resolution is a future decision, not an admission. |

**Programme routing (mechanical):**

```
ADMITTED set non-empty  -> open the top-ranked admitted family next (own G0/D0); queue the rest best-first;
                           every admitted axis is eventually opened (ranking orders, does not prune).
ADMITTED set empty AND all axes EXONERATED
                        -> price-derived information (single-series AND relational) is exhausted on this
                           dataset; the frontier is NON-PRICE DATA ACQUISITION (order book, cross-asset,
                           fundamentals) — a data decision, not a modelling one, escalated to the operator.
                           Reached having spent 0 reads and 0 slots (the terminal branch, stated now).
any axis INCONCLUSIVE    -> disclosed; not admitted; re-scope is a separate future decision.
```

The verdict is mechanical and predeclared; the explanation it produces is not (freeze the rule, not the
story — retrospective §2.1).

## 8. Guardrails (carried)

- 0 candidate slots, 0 counted TEST reads; holdout never loaded (TRAIN sub-split only).
- Both thresholds bite/fixture-calibrated or a disclosed routing-invariant band — no magic-number gate
  constants; the binding admission gate is multiplicity-adjusted (permuted-axis null), not single-axis.
- Determinism: fixed seeds; second full pass byte-identical.
- Real-price returns/ranges only; no HA/Renko brick-price returns.
- No tuning against any TEST or holdout data; all screen parameters frozen at D0 (the magnitude/cross-sectional
  conditioning definitions are pre-registered, not selected post-hoc).
- **Per-stratum verdict representation (BINDING — LESSON-001):** every screen emits its admit/exonerate read
  per cell; no single collapsed cross-cell PASS/FAIL is binding (collapsed flags captioned non-binding).
- **The magnitude harvest-model guard (BINDING):** a Screen-M tail admission is a long-vol finding only; it
  may never be carried forward as a directional edge, and its eventual family must clear a two-sided cost.

## 9. Immediate next steps

1. **Operator G0 ratification — DONE (2026-06-22):** D1–D6 ruled on and frozen; the D2 admission-gate
   bite-check ran **GREEN** (`bite-check/`, report sha256 `208dfb3f…`, byte-identical second pass);
   `D0-predeclarations.md` frozen. Result-producing code is authorized.
2. **Scope EXP-086 (Screen M)** (Stage 1) after G0 PASS — the first concrete experiment, an EXP-081 clone
   with the endpoint swapped from favourable `MFE_med` to the **split** typical-range + tail reads plus the
   magnitude-budget check. Then EXP-087 (Screen X); EXP-088 (Screen F) only if the operator wants the third
   comparison.
3. **G-019 adjudication** after the slate — emit the ranked admit/exonerate inventory; route per §7.
4. **On the top-ranked `ADMITTED` axis:** open the corresponding entry-side candidate family at its own
   G0/D0 (its own CF-XXX spec promoted from `candidate-families/family-selection-phase-019.md`, its own
   readiness/characterization slate). Capture geometry and risk-sizing return as levers only *after* a
   first-order availability edge exists.

---

*Companion documents: candidate-families under consideration
[`../../../signal-registry/candidate-families/family-selection-phase-019.md`](../../../signal-registry/candidate-families/family-selection-phase-019.md);
gate definition [`G-019-gate-criteria.md`](G-019-gate-criteria.md);
predeclarations [`D0-predeclarations.md`](D0-predeclarations.md);
the reconciliation [`../../reflections/2026-06-22-reconciliation-and-family-selection-phase.md`](../../reflections/2026-06-22-reconciliation-and-family-selection-phase.md)
and its two source reviews; multiplicity registry Phase 019 batch
[`../../../signal-registry/multiplicity-registry.md`](../../../signal-registry/multiplicity-registry.md);
master index [`../../INDEX.md`](../../INDEX.md).*
