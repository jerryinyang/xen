# Experiment: EXP-032 — One-Shot Holdout Confirmation of Package B (EURUSD-4h, FH H\*=12, all_legs)

**Registry ID:** `CF-AVWAP-001/HOLDOUT-B` (programme holdout shot, 1-of-1).
**Phase:** 009 (`docs/experiments-docs/checkpoints/2026-06-10-009-avwap-holdout-release/design.md`).
**Authorization:** Phase 008 G2 SATISFIED → CLINICAL_TRADABLE; operator selected
Package B 2026-06-10 (`G2-gate-review.md`, operator-decision section).
**Depends on:** EXP-037 (frozen H\*=12/all_legs, `frozen_selection.json`
content-hash `2bbbf65ba0a3d9d50ad0c988e3845bdae93edc863756c810ff4f53f3770b0fea`),
EXP-030 (frozen CONSERVATIVE costs), EXP-034/D0 (financing layer), EXP-027
(frozen inference tail, pinned hash `e50873d12a9f68d9`), EXP-020/022 (event
generator + population), EXP-028/029 (faithful-strategy lineage).

## Hypothesis

On the **global holdout stratum** (final 30% of the full dataset, never
previously read), the Package-B candidate — EURUSD-4h AVWAP bounce events with
fixed-horizon exit at H\*=12 domain bars, all_legs pyramid policy, frozen
CONSERVATIVE costs (RT 3.0 bps) plus financing (0.6 bps/day, adverse-side,
fractional calendar days) — has positive net per-event expectancy:
`ci_low_1s > m_cell` and one-sided bootstrap p ≤ 0.05.

## One-shot discipline (LOCKED — Phase 009 design §3)

- The holdout outcome inference runs **exactly once**; the shot is spent on any
  outcome (CONFIRMED / REFUTED / INCONCLUSIVE).
- After Stage-1 scope freeze, **no parameter may change** — there is no amendment
  path for this experiment.
- Two-phase execution: **H1** (entry attributes, reconciliation, calibration
  margin → `frozen_holdout_manifest.json`, content-hashed) strictly precedes
  **H2** (outcome computation + inference → `holdout_verdict.csv`). No outcome
  quantity may be computed in H1.
- **Recovery semantics (EXP-037 R1.6-identical):** a rerun after H1 must
  reproduce the manifest hash exactly (hard stop on mismatch); any run finding an
  existing `holdout_verdict.csv` must refuse to recompute inference.

## Holdout access protocol (LOCKED — Phase 009 design §5)

- **Unsealed:** EURUSD 1-minute rows past the analysis cutoff, lazily and
  column-projected, solely for (a) streaming event-generation continuity, (b)
  the EXP-031-identical 4h rebuild, (c) the scoped outcome computation.
- **Stays sealed:** BTCUSD/USTEC/XAUUSD holdout rows (never loaded); any EURUSD
  holdout use beyond this scope (no 5m/1h aggregation, no per-bar suite, no
  conditioning, no exploratory plotting of holdout paths).
- The standard "DO NOT USE the final 30%" rule is **superseded for EURUSD only,
  within this scope only**, by the Phase 009 design — this is the sanctioned
  release the rule reserves for. Implementation must still assert that no other
  instrument's holdout rows are touched.

## Scope Boundaries

- **Instrument/domain:** EURUSD 4h only.
- **Data views:** full EURUSD 1-minute series (analysis + holdout);
  EXP-031-identical 4h domain rebuild over the full series; EXP-020/022 AVWAP
  event generator (frozen parameters, unchanged) run as a sequential stateful
  stream over the full series.
- **Stratum membership (predeclared, causal):** boundary = CloseTime of the last
  analysis 1-minute row (`analysis_rows = int(total_rows × 0.7)`). An event is
  HOLDOUT iff its entry-confirmation (trigger) close time > boundary; ties →
  analysis. Membership keys on the entry bar; the FH window may run toward
  series end.
- **Parameters (ALL FROZEN, inherited — no selection happens in this experiment):**
  - Exit: FH at H\* = 12 domain bars; pyramid policy all_legs (EXP-037 freeze).
  - RT cost, CONSERVATIVE: EURUSD 3.0 bps (EXP-030).
  - Financing: 0.6 bps per calendar day, adverse-side, charged
    `0.6 × elapsed_calendar_days(trigger, FH-exit)` with fractional days
    (D0/EXP-034).
  - Inference: frozen EXP-027 regime-cluster bootstrap, 1000 resamples,
    one-sided p, pinned tail hash `e50873d12a9f68d9`.
  - Truncation: events whose FH window passes series end exit at the last
    available bar (EXP-033-identical); truncated share disclosed.
- **Outcome per event:** real-OHLC return, entry-confirmation close → close
  H\*=12 4h bars later, minus RT, minus financing. Real prices only.
- **Per-cell estimand:** event-weighted mean `net_e` over holdout-stratum events
  (pyramids per all_legs). Baseline exactly 0 bps net; no
  percentage-of-baseline metric (zero-baseline rule).
- **Exclusions:** all other instruments/domains; BTC exit as a binding quantity
  (companion only, below); conditioning strata; any H ≠ 12; any cost/financing
  variant; any re-selection or sensitivity sweep on holdout data; the per-bar
  frozen suite (event-level method only).

## Pre-outcome null calibration and binding margin (LOCKED — Phase 009 design §6)

Computed in H1, persisted in the manifest **before** any outcome contact:
cluster sizes and direction labels from the holdout stratum's entry attributes
under all_legs; null returns from the zero-mean Gaussian cluster model
(r = a_c + e_i), between/within variance components by method of moments from
the **full-analysis** EURUSD-4h FH(H\*=12)/all_legs nets (already-disclosed
data; both TRAIN and TEST strata); R = 2000 null replicates scored by the frozen
1000-resample bootstrap. Binding margin `m_cell = max(0, Q95 of null
ci_low_1s)`; measured uncorrected null FPR disclosed. No post-result iteration.

## Integrity guards (must pass before any holdout outcome is computed)

1. **Analysis-stratum reconciliation:** events with trigger ≤ boundary reproduce
   the EXP-037 EURUSD population partition exactly (39 events; 27 TRAIN / 12
   TEST per `frozen_selection.json`; identical triggers/directions/regime ids).
   Any mismatch is a hard stop — the generator lineage is broken.
2. **Frozen-selection hash pin:** EXP-037 `frozen_selection.json` content hash
   verified before H\*/policy are used.
3. **Frozen-tail hash pin:** inference tail `e50873d12a9f68d9` verified.
4. **Analysis-set FH reproduction anchor:** FH(H\*=12)/all_legs nets recomputed
   on the EXP-037 TEST stratum must reproduce `test_verdicts.csv` EURUSD
   (net +40.5589 bps) to ≤ 0.01 bps before holdout outcomes are computed.
5. **Freeze-before-outcome assertion:** H2 refuses to run unless
   `frozen_holdout_manifest.json` exists and hash-verifies.
6. **No-second-read guard:** H2 refuses to run if `holdout_verdict.csv` exists.
7. **Seal assertion:** runtime check that no non-EURUSD file rows past each
   instrument's analysis cutoff are read (loader-level guard + run-metadata
   disclosure of every file and row range touched).
8. **Same-seed determinism replay** of the inference step (within H2, on the
   already-computed outcome vector — not a second read).

## Estimand and verdict (LOCKED, mechanical)

- **HOLDOUT_CONFIRMED** iff `ci_low_1s > m_cell` AND one-sided bootstrap
  p ≤ 0.05. (Family size 1 — the phase's only binding read; no Holm.)
- **HOLDOUT_REFUTED** iff two-sided 95% CI upper bound < 0.
- **HOLDOUT_INCONCLUSIVE** otherwise.
- **Descriptive labels** (non-binding) from the two-sided 95% CI:
  EVIDENCE_FOR / EVIDENCE_AGAINST / INCONCLUSIVE_SPANS_ZERO.
- **Non-binding companions (predeclared, same pass, never promotable):**
  (a) BTC-exit net on the same holdout events (Package-A estimand, descriptive
  mirror of EXP-037's `btc_net_bps`); (b) gross/cost/financing decomposition of
  the binding cell. Neither can ground, upgrade, or substitute for the binding
  verdict, nor nominate any future holdout read.

## Predeclared power statement (mandatory)

Analysis set (70%) holds 39 EURUSD-4h events → holdout (30%) expected ≈ 15–18,
subject to regime composition (disclosed in H1 before outcomes). At EXP-037 TEST
scale (n=12 → margin 8.42 bps), a true effect near the TEST point (+40 bps)
likely confirms; a true effect at the EXP-038 baseline scale (+24 bps) with
adverse dispersion can land INCONCLUSIVE. **INCONCLUSIVE is an expected, honest
outcome and still spends the shot** — accepted in advance by the operator's
Package-B selection.

## Success / Failure Criteria

- **Evidence FOR:** HOLDOUT_CONFIRMED → first net-positive, holdout-confirmed
  AVWAP candidate; next required step (outside this scope) is cTrader per-bar
  parity of the FH exit on analysis-set data (EXP-029 covered only the BTC exit).
- **Evidence AGAINST:** HOLDOUT_REFUTED → Package B fails out-of-sample; holdout
  spent; Tier-C routing per Phase 008 design §9.
- **Inconclusive:** HOLDOUT_INCONCLUSIVE → holdout spent without confirmation;
  TEST-stratum evidence stands but is never upgradable.

## Complexity Budget

- Statistical test families: 1 (frozen regime-cluster bootstrap CI + one-sided
  p on one cell; the H1 null calibration is verification machinery of the same
  frozen family on synthetic data only).
- Visualisations: 3 (holdout per-event net distribution with binding bound vs
  margin; binding net vs BTC-exit companion on the same events; analysis-vs-
  holdout per-event net comparison at H\*=12).
- New code modules: 1 (orchestration only, reusing EXP-037's FH construction,
  cost/financing overlay, and calibration machinery; no new `xen` module).

## Data Requirements

Full EURUSD 1-minute series. Event provenance regenerated by the frozen
EXP-020/022 generator over the full series (analysis-stratum reconciliation is
guard 1). FH exit prices from the full-series 4h rebuild at `entry_idx + 12`.

### Loading pattern (EXP-032-specific — sanctioned EURUSD holdout read)

```python
import polars as pl
from pathlib import Path

DATA_DIR = Path("data")
path = sorted(DATA_DIR.glob("timebars/timebars_EURUSD_*.parquet"))[-1]

scan = pl.scan_parquet(path).sort("CloseTime")
total_rows = int(scan.select(pl.len()).collect().item())
analysis_rows = int(total_rows * 0.7)
boundary_ts = (
    scan.slice(analysis_rows - 1, 1).select("CloseTime").collect().item()
)
bars = scan.collect()  # FULL series — sanctioned by Phase 009 design §5,
                       # EURUSD only; no other instrument file may be loaded
                       # past its analysis cutoff.
# HOLDOUT stratum: events with trigger CloseTime > boundary_ts (ties → analysis)
```

## Suggested Direction

Thin deterministic overlay on EXP-037's code: run the frozen generator over the
full series, reconcile the analysis stratum (guard 1), write the H1 manifest
(stratum manifest + margin + inherited constants, content-hashed), then run H2
once — FH(12)/all_legs nets on holdout events, frozen bootstrap, mechanical
verdict. The freeze-before-outcome assertion and the no-second-read guard are
the load-bearing controls; the reconciliation guard is what proves the holdout
events come from the same generative lineage as everything G2 certified.
