# Phase 019 D0 — Predeclarations (Family-Selection Availability Screen)

**Status:** **RATIFIED — G0 PASS (2026-06-22).** D1–D6 ratified by the operator as drafted and now
**FROZEN**; the **D2 admission-gate bite-check is GREEN** (`bite-check/bite_check.py` →
`bite-check/bite_check_report.json`, SEED 20260622; report sha256 `208dfb3f…`; byte-identical second pass).
No amendment without a dated `D0-amendment-*` file in this directory. Result-producing code (EXP-086 →) is
now **authorized**.

**Bite-check result (run 2026-06-22 — `OVERALL: GREEN`):** the binding D2b admission gate (per-cell
CI_low>0 test → axis statistic `S = #cells-beat-random` → permuted-axis null → `S* = Q(1−FWER)` + cross-axis
Holm) is confirmed **neither vacuous nor impossible, self-calibrating, and band-invariant** on synthetic
fixtures at the realized cell count `C=46`:
- **Not vacuous** — a pure-noise axis is admitted at **0.0248** (FWER 0.05; Wilson-hi 0.0295 ≤ 0.075); the
  empirical permutation null mean **2.267** matches `C·Φ(−1.645)=2.299` and its `S*`(Q95)=**5** equals the
  Binomial(46,0.05) ceiling; the empirical noise axis was **rejected** (S=3, perm-p 0.39).
- **Not impossible** — a genuinely non-random axis (a modest **+0.20 ATR** availability lift on **8 ≥5**
  well-powered cells) is admitted with **power 1.0** (empirical planted axis S=11, perm-p 0.001 → admitted).
- **Routing invariant across the sensitivity band** FWER ∈ {0.025, 0.05, 0.10} (`S*`=6/5/4; noise rate
  0.006/0.025/0.077 ≤ FWER; planted power 1.0 throughout).
- **Self-calibrating** — under an inflated per-cell FP (0.061, the EXP-077 percentile-bootstrap effect) the
  axis-level admission rate stays **0.0214 ≤ FWER** because `S*` is computed from the *same* test
  (the permuted-axis null absorbs per-cell inflation).
- **EXP-081 sign-band sanity** — the descriptive sign-count noise band is Binomial(46,0.5) 90% interval
  **[17, 29]**, which brackets EXP-081's observed **17/46–28/46**: *availability ≈ random was the coin-flip
  noise distribution*, and the binding CI_low>0/permutation gate separates a real lift from it. **Holm
  step-down** verified correct.

**Prior status (for the record):** DRAFT — CANDIDATE VALUES POPULATED (2026-06-22); G0 PENDING. D1–D6 carried
concrete candidate values; the D2 admission gate and the Screen-M tail threshold required the bite/fixture
check above before ratification.
**Checkpoint:** `2026-06-22-019-family-selection-availability-screen`
**Governing design:** `design.md` (this directory).
**Scope of this D0:** family-agnostic availability screening to *select* the next entry-side family.
**No candidate screening, 0 candidate slots, 0 counted TEST reads, holdout never touched.**
**Discipline (binding throughout Phase 019):** TRAIN sub-split only on the VAL-005 5-year data; all
return/range metrics on real prices; deterministic (fixed seeds, byte-identical second pass); no
parameter tuned against any TEST or holdout data; per-stratum reporting (LESSON-001).

---

## D1 — Matched-random control, substrates & information axes (frozen) — CANDIDATE VALUES

**Dataset:** VAL-005-admitted 5-year 1-minute bars, 16 instruments (DE30 dropped), holdout-fenced
`build_domain_bars`; domains **{15m, 1h, 4h}** (CF-CAPGEO scope; reuse EXP-080 readiness). **TRAIN
sub-split `[0, int(analysis_rows·0.7))` only**; analysis-TEST + final-30% holdout never sliced. All
metrics in **ATR(14) units** on real OHLC. Master seed `20260622`; per-draw seed = deterministic hash
of `(axis_id, instrument, domain, replicate)`.

**Matched-random control (frozen, reused):** the EXP-080/081 `SUB-RANDOM` construction —
random-timing entries on the same regime/direction within the same cell, matched count — is the null
for the **per-cell** Δ-over-random read. This is the descriptive baseline (D2a), distinct from the
binding permuted-axis admission null (D2b).

**Information axes (one screen each; the conditioning is pre-registered, never selected post-hoc):**

| Axis | EXP | Conditioning primitive (candidate) | Availability endpoint (→ D3) |
| --- | --- | --- | --- |
| **M — single-series magnitude** | EXP-086 | HA-harami inside-bar **and** a clean NR/inside-bar primitive (NR4/NR7 or inside-bar, frozen at D0) | **split:** typical-range **and** tail/bimodality (D3.M) |
| **X — cross-sectional** | EXP-087 | basket-relative momentum / divergence **rank** across the 16-instrument universe (lookback, rank vs divergence, rebalance cadence frozen at D0) | favourable excursion `MFE_med` vs random (D3.X) |
| **F — order-flow** (reserved-conditional) | EXP-088 | tick-volume / volume-at-price imbalance extremes | availability vs random (D3.F) |

**Member cells:** the EXP-080-READY 46 instrument×domain cells (US500-4h, JP225-4h `COVERAGE_EXCLUDED`)
× the axis's conditioning. For Screen X the cross-sectional rank is computed across all instruments at
each timestamp, then read per (instrument, domain) cell, so the cell count matches the single-series
screens for a like-for-like admission-gate calibration.

## D2 — Two thresholds, bite-calibrated (no magic numbers — retrospective §5.3) — CANDIDATE VALUES

**D2a — Descriptive per-cell null band (reporting only, NON-BINDING).** A cell "beats random" when its
paired Δ-over-random one-sided lower bound > 0. The established random-looking baseline is
**≈17/46–28/46** cells-beat-random (EXP-081 Finding 3). Reported per axis for transparency; it does
**not** decide admission.

**D2b — Binding multiplicity-adjusted admission gate (THE decision; bite-checked before G0).** An axis
is `ADMITTED` only if its realized cells-beat-random count (and/or its aggregate Δ) exceeds what a
**permuted-axis / shuffled-conditioning null** produces across the **same number of cells**, at a frozen
family-wise error rate. Construction (candidate):

- Build the null by **shuffling the conditioning labels** (permuting which timestamps are "signal" vs
  not, preserving per-cell event counts and the regime/direction match) and recomputing the full per-cell
  Δ-over-random table — i.e., a pure-noise axis run through the identical pipeline.
- `N_PERM = 1000` permutations (candidate; confirm MC stability at the bite scale, lift to production
  scale before the binding read). Per permutation record the axis-level statistic
  `S = (#cells-beat-random)` and, as a continuous companion, the trimmed-mean per-cell Δ.
- **Admission gate `S* = Q95(S_perm)`** (candidate FWER 0.05 at the axis level; the permuted null already
  absorbs the across-cells multiplicity *within* an axis). **Across axes** (M, X, optional F), apply a
  Holm step-down over the three axis-level permutation p-values so the *selection* is FWER-controlled at
  0.05 — admitting "the best of three noise axes somewhere" is exactly the failure this prevents.
- **`ADMITTED` iff** the realized `S_axis > S*` **and** Holm-adjusted axis p ≤ 0.05.
- **`INCONCLUSIVE` iff** the permuted null cannot separate (the `S*` ceiling sits at or above the
  maximum attainable `S` at the realized cell count → no power).

**Bite/fixture check (REQUIRED before G0 ratification):** run the gate on (i) a **pure-noise synthetic
axis** (random conditioning) — confirm admission rate ≤ FWER (not vacuous); and (ii) a **planted
non-random synthetic axis** (a known availability lift on ≥5 cells) — confirm it is admitted with high
power (not impossible). Re-anchor `N_PERM` / `Q95` / the Holm structure if either bite fails; record the
bite output. Routing must be shown **invariant across a pre-registered sensitivity band** (e.g. FWER
∈ {0.025, 0.05, 0.10}; `S*` from Q90/Q95/Q975).

**Rationale (binding):** the single-axis EXP-081 band would let a pure-noise axis with many cells clear it
*somewhere*; cross-sectional ranking over 16 instruments manufactures the most cells and is the worst
offender. The permuted-axis null at the realized cell count is the `m_cell`/EXP-077-style calibrated
threshold the programme already trusts, applied to *selection* rather than to a single verdict.

## D3 — Availability endpoints (frozen) — CANDIDATE VALUES

**D3.M — Screen M magnitude (SPLIT — never pooled; retrospective §2.3, reconciliation §3).** Report
**two separate** per-cell Δ-over-random reads; a pooled `|move|` number is **prohibited** (EXP-081 shows
it is null):

1. **Typical-range read:** forward realized range / symmetric excursion `max(MFE, MAE)` (and `MFE+MAE`
   as a companion), ATR-normalised, vs matched random over the per-event adaptive cap (EXP-081 geometry).
2. **Tail/bimodality read:** `tailmass` (fraction below `median − K_tail·MAD`, `K_tail=3.0` frozen),
   `q05`, Hartigan dip-p; **plus** a direct re-examination of EXP-074's `msofar_atr` adverse-tail
   separation expressed as *predictable magnitude* (rank-biserial of conditioning vs the q05 tail),
   carried as the one place the prior is non-trivial.
3. **Magnitude-budget check (BINDING for any magnitude admission):** the predictable range must clear a
   **two-sided** cost (CONSERVATIVE round-trip × 2 sides + financing, EXP-030/085 cost convention), since
   the harvest is a straddle/breakout, not a directional bet. A tail-only admission is recorded as a
   **long-vol** finding (routes to CF-VOLEXP-001 under the harvest model), never a directional edge.

**D3.X — Screen X cross-sectional.** The EXP-081 favourable-availability read (`MFE_med` Δ-over-random,
per-cell paired) re-pointed at the cross-sectional-rank conditioning. Directional-favourable endpoint
(the cross-sectional anomaly is directional by construction).

**D3.F — Screen F order-flow.** Availability (favourable `MFE_med` and the split magnitude reads as for
M) at imbalance extremes vs matched random.

## D4 — TRAIN-only disclosure accounting (binding — preserves 0 counted TEST reads)

Each screen reads the **TRAIN sub-split only** (`[0, int(analysis_rows·0.7))`); the next-21% analysis-TEST
stratum and the final-30% holdout are **never sliced or materialized** (forward path resolution clips at
the TRAIN edge). The screens make **no stratum-specific selection or inference** — they compute family-agnostic
availability disclosures over the full TRAIN region of each cell (the EXP-080/081 readiness/characterization
convention). Therefore, per the readiness/TRAIN-only convention (EXP-074/075/080/081 precedent), **each
screen is a disclosure, not a counted read**: all 48 strata remain **0 counted reads / open**;
`test-read-ledger.md` is **unchanged** by Phase 019. Holdout sealed throughout. The permuted-axis null
(D2b) shuffles conditioning labels *within* the same TRAIN region — it reads no additional data.

## D5 — G-019 mechanical verdict rule

```
For each information axis A in {M, X, (F)}:

  ADMITTED(A)      iff  realized S_A > S*  (permuted-axis Q95 ceiling at the realized cell count, D2b)
                   AND  Holm-adjusted axis-level permutation p(A) <= 0.05      (cross-axis FWER 0.05)
                   [Screen M: typical-range OR tail read may satisfy this; a TAIL-ONLY pass is a
                    LONG-VOL admission -> CF-VOLEXP-001 under the two-sided harvest model, not directional]

  EXONERATED(A)    iff  S_A is within the D2a null band on EVERY read
                   [Screen M: on BOTH the typical-range AND the tail read]   -> cell of the 2x2 is dead

  INCONCLUSIVE(A)  iff  the permuted null cannot separate at the realized cell count (no power)

Programme routing:
  ADMITTED set non-empty -> open the top-ranked admitted axis next (own G0/D0), ranked best-first by the
                            frozen Delta-over-random metric; queue the rest; EVERY admitted axis is
                            eventually opened (ranking orders, never prunes).
  ADMITTED empty AND all EXONERATED -> price-derived information exhausted on this dataset; frontier is
                            NON-PRICE DATA ACQUISITION (operator decision); reached at 0 reads / 0 slots.
  any INCONCLUSIVE -> disclosed; neither admitted nor exonerated; re-scope is a separate future decision.
```

The verdict is mechanical and predeclared; the explanation it produces is not (freeze the rule, not the
story — retrospective §2.1). The ranking metric is frozen at D0 (candidate: the axis-level permutation
z-score `(S_A − mean(S_perm)) / sd(S_perm)`, tie-broken by trimmed-mean per-cell Δ).

## D6 — Determinism & real-price discipline

- All RNG seeds fixed and recorded; a second full pass of every screen is byte-identical (including the
  permutation null at a fixed permutation seed-stream).
- All return/range metrics computed on **real prices** (`RealOpen/High/Low/Close`); no HA-price or Renko
  brick-price returns anywhere (HA candles used for harami detection only).
- No tuning against any TEST or holdout data; all axis-conditioning definitions and thresholds frozen at
  G0 (the D2 sensitivity band is a pre-registered robustness sweep, not a selection).

## Slot & TEST accounting

- **0 candidate slots** consumed (family selection, not candidate screening; the candidate families under
  consideration are registered DRAFT/PENDING-SELECTION in
  `candidate-families/family-selection-phase-019.md` and consume a slot only when promoted at a future G0).
- **0 counted TEST reads.** TRAIN sub-split only; the analysis-TEST stratum and final-30% holdout are never
  sliced. `test-read-ledger.md` is unchanged by Phase 019 (all 48 strata stay 0/2 open).
- Holdout sealed throughout.
