# EXP-015 Report — CF-MR-005/HYP-001: mechanism characterisation of the 4h ladder scale-in own-price MR harvest

**Family:** CF-MR-005 · **Phase:** 005 · **Type:** mechanism characterisation, TRAIN,
**analysis-only**. **Status: COMPLETED 2026-07-03.**
**Outcome (frozen §5 criteria): NO_MECHANISM_EVIDENCE — 0/11 cells MECHANISM_SUPPORTED; 10
powered cells NO_SEPARATION (one significantly anti-reverting), 1 UNPOWERED; depth premise
structurally untestable at bins 3–4 (event scarcity). Family disposition → operator routing
(retire-leaning; see §6).**
Artifacts: [design.md](design.md) · [code/](code/) · [results/](results/) · [plots/](plots/) ·
[audit.md](audit.md) (PASS, 0 open Critical; C1/C2 fixed + full re-run before this report).

## 1. Question

Does own price at 4h, conditioned on a basket-free dislocation of depth z below/above its
rolling-median anchor, revert toward the frozen (≤t−1) anchor beyond a matched control — per
instrument, monotonically in depth — and is the EXP-014b/c extend-arm engine P&L attributable
to that depth-graded reversion rather than drift, short-vol exposure, or tail episodes?

## 2. Method (as designed, no deviations)

- **Part B (measurement):** 5y-era 1m timebars → strict 4h bars, fenced at the EXP-013
  first-49% cutoffs verbatim (asserted per cell; holdout sealed). Trigger `z_{t−1} =
  (logP − Median₉₀)/σ₂₀₀`, all ≤ t−1; events de-clustered (one per episode × depth bin;
  episode ends |z|<1.0); recovery `R_h = dir·(logOpen_{t+h} − logOpen_t)/|S_{t−1}|`,
  open-to-open from the action-bar open. **Paired ΔR_h** = median over events of
  (event R_h − median of 20 matched controls; vol-tercile × |ret|-decile, frozen seed);
  moving-block bootstrap CI (block 12, 10k). Tripwire: block-permuted-returns null
  (L-07; 200 replicates, full pipeline, collapse fractions disclosed).
- **Part A (anatomy, read-only):** EXP-014b/c 4h extend emissions (e0–e3 × z15/z20 × 11
  cells; 87/88 present) — per-LadderLevel P&L, shift-twin collapse fractions per level
  (L-15), ≥2-leg overlap census, episode-level tail, {1,2,3}× cost stress. Provenance +
  fence re-asserted on every load.

## 3. Results — Part B (binding characterisation)

### 3.1 M1 — no dislocation-conditional recovery separates from control

Per-cell binding read at h=24 (`results/part_b_mechanism.json`, `plots/delta_r_profiles.png`):

| Cell | bin-1 n | bin-1 ΔR₂₄ [95% CI] | deeper bins ≥30 ev | label |
|---|---|---|---|---|
| EURUSD | 49 | +0.079 [−0.227, +0.306] | 0/3 | NO_SEPARATION |
| GBPUSD | 42 | −0.064 [−0.263, +0.160] | 0/3 | NO_SEPARATION |
| USDJPY | 41 | +0.095 [−0.192, +0.421] | 0/3 | NO_SEPARATION |
| USDCHF | 50 | +0.126 [−0.037, +0.406] | 0/3 | NO_SEPARATION |
| USDCAD | 45 | −0.086 [−0.257, +0.073] | 0/3 | NO_SEPARATION |
| AUDUSD | 57 | −0.005 [−0.295, +0.236] | 0/3 | NO_SEPARATION |
| NZDUSD | 50 | −0.044 [−0.269, +0.355] | 0/3 | NO_SEPARATION |
| USTEC | 62 | −0.026 [−0.246, +0.172] | 0/3 | NO_SEPARATION |
| US500 | 32 | −0.013 [−0.514, +0.296] | 0/3 | NO_SEPARATION |
| **US2000** | 43 | **−0.295 [−0.443, −0.007]** | 0/3 | NO_SEPARATION (negative) |
| JP225 | 14 | −0.156 [−0.643, +0.362] | 0/3 | UNPOWERED |

Every powered CI straddles 0 except **US2000, which is significantly NEGATIVE** — dislocated
US2000 bars recover *less* than matched controls. Notable because US2000 was the strongest
EXP-014c field cell (+10.9 bps/bar, depth-graded per-leg P&L). Shorter/longer horizons
(6/12/48) show the same picture.

### 3.2 M2 — no depth gradient

Bin-slope of median ΔR₂₄: CIs straddle 0 in **11/11** cells (e.g. GBPUSD +0.143
[−0.048, +0.383]; US500 +0.216 [−0.019, +0.629]) — no cell shows the monotone-in-depth
reversion the ladder premise requires. **Bins 2–4 never reach the 30-event floor in any cell**
(max n=28): the depth gradient was structurally untestable in this window — an event-mass
fact, not noise (see §5 mechanism).

### 3.3 Tripwire (binding, L-07)

Observed ΔR₂₄ sits inside the block-permuted 95% null band in **41/44** (cell,bin) reads. The
3 exceedances (GBPUSD bin3, USDJPY bin3, AUDUSD bin4) are all UNPOWERED bins (n = 13/22/6),
2/3 with CIs straddling 0 — no admissible edge existed to survive; no REJECT-class finding.
Collapse fractions disclosed per (cell,bin) (`plots/collapse_fractions.png`).

### 3.4 M3b — drift split degenerate (design-inherited)

The trailing-90-bar drift window coincides with the anchor window, so a deep dislocation
mechanically implies opposite-sign drift: with-drift n = 0–4 per cell vs 36–111 against-drift.
The split cannot discriminate exposure-vs-reversion as designed (audit W2). It binds nothing
here (no cell reached the supported path). Against-drift ΔR₂₄ medians: −0.30…+0.29, all
straddling 0.

## 4. Results — Part A (engine-realized anatomy, disclosure)

- **M2 companion:** per-level P&L reproduces the EXP-014c field shape (e.g. EURUSD e0/z15
  L0 n=328, +7.7 bps/leg; deeper levels fatter but thin-n) — the *field* phenomenon is real
  in the emissions; it just does not correspond to any own-price dislocation-conditional
  recovery (Part B).
- **M3a (shift collapse, per level, L-15):** L0 collapse fractions are wildly heterogeneous —
  median 0.33, range −125…+10 across 22 (cell,z\*) reads (small-denominator cells explode the
  ratio; all values disclosed, no binary reads). No uniform "collapses to zero" and no uniform
  "survives" — the shift control is not interpretable as a clean attribution instrument on
  this mixed object, consistent with operator D3's deferral of shift semantics.
- **M3c (scale-in dependency):** 34–83% (median ≈ 68%) of net P&L accrues while ≥2 ladder legs
  are open — the field P&L is dominantly a multi-leg (scale-in-dependent) object.
- **M4 (left tail):** episode-level P&L has heavy left tails (e.g. EURUSD e0/z15 q05 ≈ −2,356
  bps/episode vs +6,040 total over 60 episodes). Deepest-decile-depth episodes carry an
  unstable share of total P&L across cells (−1.6…+3.3 — several cells' entire net P&L and
  more). Part-B bin-4 (|z|≥3) events **fail to recover 50% within 48 bars in ~40–85% of
  cases, in most years, in most cells** — the ladder's failure population recurs annually.
- **M5 (cost context):** extend-arm net per active bar shrinks modestly at 2–3× cost (e.g.
  EURUSD 2.93 → 2.70 → 2.47 bps) — cost is not the binding issue for this family; mechanism is.

## 5. Interpretation (quant-analyst)

**The engine-observed "ladder harvest" is not own-price dislocation-conditional mean
reversion.** Two independent findings force this:

1. **Event-mass mismatch.** The basket-free own-price trigger yields only ~30–60 de-clustered
   episodes/cell in 3.2y (deep bins: single digits), vs ~750 extend-arm engine legs in the
   same cells/window. The engine ladder's entry cadence was overwhelmingly supplied by the
   **S8 basket construction** (spread volatility), not by own-price dislocation frequency.
   The family's premise — that the field P&L lives at own-price dislocation depth — has no
   native event mass to stand on.
2. **No conditional recovery where powered.** At the powered read (bin 1), dislocated bars
   recover no more than vol/return-matched control bars in 9/10 cells and significantly
   *less* in US2000. No depth gradient anywhere.

What the field P&L looks like instead (Part A): a **scale-in-dependent** (≥2-leg, ~68% of
P&L), **heavy-left-tail** object whose deepest episodes carry unstable, sometimes >100% shares
of total P&L, with an annually recurring non-recovery failure population — i.e.
exposure/tail-harvest flavored, not a per-event conditional reversion. A formal
EXPOSURE_ARTIFACT label is **not** mechanically triggered (M3b degenerate by design; M3a
collapse heterogeneous), so under the frozen §5 table the family-level read is the
**UNPOWERED/INCONCLUSIVE row — with the explicit reason being event scarcity at depth plus
powered nulls at bin 1**, not measurement noise.

**Honest tension, stated:** design §1 predeclared "if dislocation-conditional reversion does
not separate from control in any powered cell, the family has no mechanism and retires."
That condition **is met** on the powered strata. Design §5 simultaneously routes
straddling-CI outcomes to operator routing. Retirement is a per-family critical decision →
routed to the operator with a **retire recommendation**: no mechanism evidence, no viable
native event mass for a HYP-002 tradability vehicle, and the residual unexplained P&L belongs
to the (retired) CF-MR-004 construction, not to an own-price family.

**Limits (audit §5):** median fraction-recovered is a location read — a hit-rate- or
tail-shaped effect could evade it; the M3b drift split needs a drift window decoupled from
the anchor window in any successor design. Neither limit rescues the depth-gradient premise,
which failed on event mass, not on estimator shape.

## 6. Conclusion & follow-up

- **CF-MR-005/HYP-001: NO_MECHANISM_EVIDENCE** (0 supported / 10 powered-null / 1 unpowered;
  §5 family gate not met; HYP-002 tradability phase **not** admissible).
- **Recommendation to operator: RETIRE CF-MR-005** (per design §1 predeclaration). Alternative
  routing (a redesigned mechanism probe with an independent drift control and an event
  definition matched to the engine's actual entry cadence) would be a new hypothesis under
  this family — registered before any run — but nothing in this result motivates it.
- No new experiments proposed from this result. The EXP-014c extend-arm field remains fully
  documented as engine-realized disclosure; its P&L anatomy (scale-in-dependent, tail-heavy)
  is now characterised and on record.

## Registry disposition

`CF-MR-005/HYP-001` (multiplicity-registry) → **COMPLETE — NO_MECHANISM_EVIDENCE** (0 slots,
0 counted TEST reads; TRAIN-only; retained per never-delete rule). Candidate family
`cf-mr-005.md` status → **CHARACTERISED-NULL, RETIRE RECOMMENDED (operator-gated)**. No
TEST-read ledger entry (no TEST-stratum read).

## GATE: APPROVE (orchestrator inline post-exec, 2026-07-03)

Audit PASS, 0 open Critical — both verdict-material findings (C1 slope-CI bootstrap
multiplicity, C2 M4b census censoring) were fixed and the **full experiment re-executed**
before interpretation; labels unchanged across the re-run ✓. Verdict forensics present
(per-stratum re-derivation, masking check — outputs are natively per-stratum, family figures
are counts only; mechanism stated: event scarcity + powered bin-1 nulls; gate-shape limits
recorded) ✓. Causal-provenance & leak pass present (provenance trace table; L-07 tripwire run
with collapse fractions disclosed, no surviving admissible edge; no shared-module changes;
analysis-only classification verified — no vectorized strategy backtest) ✓. Holdout: EXP-013
fence verbatim, asserted per cell; final-30% sealed ✓. Denominators/zero-baselines: event
counts in every table, UNPOWERED never FAIL ✓. Registry disposition recorded; HYP-001 row
updated; no counted reads to enter ✓. Interpretation criteria applied as frozen; §1-vs-§5
tension surfaced honestly and routed to the operator (family retire = operator-gated critical
decision, correctly not self-executed) ✓. **Stage 5 complete; phase close pending operator
routing on family disposition.**
