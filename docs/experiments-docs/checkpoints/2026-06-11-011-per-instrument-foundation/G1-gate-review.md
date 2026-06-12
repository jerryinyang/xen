# G1 Gate Review — Phase 011 Track A Readiness (Adjudication 1 of 2)

**Date:** 2026-06-11
**Gate:** G1 — readiness (per cell, lenient), design §8.2
**Adjudicated by:** desk review (research-pipeline governance), operator-ratified 2026-06-11
**Inputs:** EXP-043 (`python/experiments/EXP-043/`: report.md, results/readiness_map.csv, results/power_statement.csv, audit.md PASS 0C/0W/4 Info, post-experiment governance APPROVE)

---

## Verdict

```text
G1 STATUS: PARTIAL — readiness leg SATISFIED; calibration leg OUTSTANDING
TRACK B AUTHORIZATION: NOT YET GRANTED
```

Design §8.2 defines G1 as a two-condition per-cell gate: a cell proceeds to
Track B iff **(i)** EXP-020-analog readiness passes (event determinism,
construction integrity, no domain artifacts) **and (ii)** the EXP-027-analog
calibration covers its event population. This review adjudicates condition (i)
only. Condition (ii) has no input artifact yet; it is assigned to **EXP-044**
(registered 2026-06-11 as the EXP-027-analog calibration, Track A, 0 slots).

## Leg (i) — EXP-020-analog readiness: SATISFIED (50/51 cells)

EXP-043 (READINESS_DELIVERED, audit PASS) delivers the full 51-cell map:

- **50 cells READY.** Zero invariant violations (7-family battery, all events,
  all cells), zero determinism failures (in-run second regeneration
  frame-identical everywhere; audit reproduced two cells in a third pass),
  all construction predicates pass. `substrate_alert: false` — the
  predeclared substrate-level halt condition was never approached.
- **1 cell NOT_READY: JP225-2h**, on the frozen >25% 2h dropped-window
  fraction gate (0.2566 at `min_coverage=0.90`). A session-structure coverage
  outcome, not a generator defect (its 96 events are otherwise clean).
  Per §8.2 the cell is **excluded from Track B with this record**; it consumes
  nothing. 16 instruments remain at 2h; the Track B grid is **50 cells**.
- **Power basis:** realized TRAIN event counts (1h 151–273, 2h 86–143,
  4h 32–86; min 32 at JP225-4h, all ≥ the 30-event floor) supersede the
  design §7.4 planning figures and the set-aside EXP-042 power statement.
  Disclosures carried into Track B: 11/17 4h cells hold only 32–55 events;
  index 2h dropped fractions sit in the flagged 10–25% band (US2000 0.103,
  DE30 0.163, US500 0.196); DE30 derives from a ~5-month-shorter history.

## Leg (ii) — EXP-027-analog calibration: OUTSTANDING → EXP-044

No cell may enter Track B until the event-level inference method calibration
covers its event population (per-instrument calibration; the EXP-027 inference
machinery itself is unchanged and re-used — design §5.3). **EXP-044** is the
registered vehicle. When EXP-044 completes with calibration coverage for the
50 READY cells, G1 closes by a second adjudication appended to this file;
cells whose populations the calibration cannot cover are excluded with record,
exactly as JP225-2h was under leg (i).

## EXP-029-analog parity — Track A item, not a G1 condition

The C#/Python parity re-verification for the 2h domain and the new universe
remains a registered Track A item, but design §8.2 does not bind it into G1.
Disposition: required before any **binding TEST read** on a 2h or new-universe
cell (consistent with the registry's standing gate note for new execution
domains); it does not block TRAIN-only Track B training. This disposition is
recorded here so the index statement "remaining Track A items before G1" is
superseded by this gate review for the parity item.

## Operator decision record (2026-06-11)

The operator proposed closing G1 as PASS on EXP-043 alone; desk review flagged
the §8.2 conflict (calibration leg unmet; EXP-043's own report records G1
incomplete). Operator selected the design-compliant path: **G1 PARTIAL now,
EXP-044 = EXP-027-analog calibration next, Track B opens on G1 close.** No
design amendment was made; §8.2 stands as frozen.

## Consequences

| Item | State |
| --- | --- |
| Track B (`CF-AVWAP-001/PI-EXIT`, 50-cell exit training) | Remains REGISTERED — pending G1 close (EXP-044) |
| JP225-2h | Excluded from Track B, recorded, nothing consumed |
| Next experiment | EXP-044 — EXP-027-analog per-instrument inference calibration (Track A, 0 slots, TRAIN/synthetic only) |
| EXP-029-analog parity | Pre-TEST-read requirement for 2h/new-universe strata; not a Track B blocker |
| TEST budget | Untouched (0 of ≤6 reads spent) |

---

## G1 Adjudication 2 of 2 — Calibration leg (ii): EXP-044 (2026-06-11)

**Inputs:** EXP-044 (`python/experiments/EXP-044/`: report.md,
results/coverage_map.csv, results/fpr_per_cell.csv,
results/tpr_mde_per_cell.csv, audit.md PASS 0C/1 latent W/4 Info,
post-experiment governance APPROVE Revision 1 incl. adversarial-review
disposition).

### Verdict

```text
G1 STATUS: CLOSED — both legs adjudicated
TRACK B AUTHORIZATION: GRANTED on the 37-cell COVERED grid
```

EXP-044 (CALIBRATION_DELIVERED) delivers the per-cell coverage map at every
READY cell's realized TRAIN event count, with 100% draw completion, all
Wilson precision gates met, and a frame-identical two-cell determinism
replay. Leg (ii) is **satisfied for the 37 COVERED cells**; the **13
NOT_COVERED cells are excluded from Track B with record**, consuming
nothing — the same treatment as JP225-2h under leg (i).

### Leg (ii) detail

- **COVERED: 37 cells** (1h 14, 2h 12, 4h 11). Per-cell event-level MDEs
  recorded: median 16 bps (1h), 32 bps (2h), 64 bps (4h); four cells sit at
  the 128 bps grid endpoint. These MDEs are the binding power context for
  Track B exit training and Track D affordability.
- **NOT_COVERED: 13 cells** — 12 on FPR point excess at α₀ = 0.05 under the
  predeclared both-nulls rule (11 **marginal**: point estimates 0.052–0.062
  with Wilson 95% intervals including α₀ — borderline failures, not clear
  excesses; 1 **material**: USDCAD-2h, N1 = 0.070, interval entirely above
  α₀) and 1 on no finite MDE (BTCUSD-4h, TPR 0.64 at 128 bps).
  Excluded cells: AUDUSD-1h/4h, BTCUSD-1h/4h, USTEC-1h/2h, GBPJPY-2h,
  USDCAD-2h, XAUUSD-2h, EURJPY-4h, EURUSD-4h, NZDUSD-4h, USDJPY-4h.
- **Substrate validity:** the METHOD_NOT_TRANSFERABLE triggers did not fire
  (2-instrument Wilson disagreement < 3; no domain-wide excess), so the
  per-cell application of the frozen EXP-027 machinery is admitted as the
  Phase 011 binding inference.

### Adjudication notes (binding interpretation for Tracks B/D and G3)

1. **Systematic N1 > N2 FPR offset.** N1 exceeds N2 in 35/50 cells
   (sign-test p ≈ 0.001; medians 0.041 vs 0.030); 11/12 FPR exclusions fail
   on N1 only. The pooled-scale two-null agreement (EXP-027) did not
   replicate per cell. The predeclared both-nulls rule makes the stricter
   N1 binding by construction — no null-selection decision exists, and
   re-basing coverage on N2 would be post-hoc metric reselection. The 13
   exclusions stand.
2. **Marginal exclusions and the precision-only lever.** The 11 marginal
   cells are individually compatible with sampling noise; the predeclared
   operator option remains a precision-only re-run (more draws, no object
   change, incorporating the audit's latent-warning fix) if the 37-cell
   grid proves limiting. Until then the conservative map governs.
3. **Horizon-transfer caveat.** Coverage is calibrated at H_cal = 8 bars.
   If Track D selects cells whose trained exits sit far from H ≈ 8, the
   predeclared targeted second-horizon FPR check is required on those cells
   before any binding TEST read (new scope).
4. **Secondary α = 0.01 columns are uncalibrated-for-use**
   (anti-conservative, mean FPR 0.0225); only the α₀ = 0.05 operating point
   is consumable, pre-Holm, by G3.

### Consequences

| Item | State |
| --- | --- |
| Track B (`CF-AVWAP-001/PI-EXIT`) | **OPEN** on the 37-cell COVERED grid (TRAIN-only exit training) |
| 13 NOT_COVERED cells + JP225-2h | Excluded from Track B with record; nothing consumed |
| Per-cell MDE table (`tpr_mde_per_cell.csv` / `coverage_map.csv`) | Binding power context for Track B/D; supersedes the EXP-027 pooled-domain map |
| EXP-029-analog parity | Unchanged: pre-TEST-read requirement for 2h/new-universe strata |
| Predeclared follow-ups | Second-horizon FPR check (conditional on Track D exits); precision-only re-run (operator option); N1>N2 dependence diagnostic (optional new scope) |
| TEST budget | Untouched (0 of ≤6 reads spent) |
