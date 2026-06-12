# G1 Gate Review — Phase 013 Move-Size Adjudication

**Date:** 2026-06-12
**Gates:** G1a — readiness (mechanical, per cell), design §8.2; G1b —
move-size adjudication (mechanical), design §8.3
**Adjudicated by:** desk review (research-pipeline governance); operator ratification pending
**Inputs:** EXP-047 (`python/experiments/EXP-047/`: report.md, results.md,
results/readiness_map.csv, results/shift_classification.csv,
results/move_size_distributions.csv, results/reconciliation.csv,
results/audit_anchor_coincidence.csv, results/run_metadata.json,
audit.md PASS 0 Critical / 2 Warning, post-experiment governance APPROVE)

---

## Verdict

```text
G1a STATUS: 51/51 READY (full grid admissible)
G1b STATUS: ANCHOR_MOVE_FLAT
PHASE 013: CLOSES — the move-size ceiling is recorded as intrinsic to the
AVWAP family on the tested anchor; programme routes to a NEW CANDIDATE
FAMILY (operator pre-commitment, design §1.5 item 2 / §8.3 / §9)
```

Design §8.3 makes G1b a mechanical composition count: ANCHOR_MOVE_VIABLE
iff ≥5 SHIFTED_VIABLE cells over ≥3 instruments (D0 item 6). The count is
**0/51 SHIFTED_VIABLE** — not a near miss; the relaxed sensitivity
thresholds (≥4/≥2, ≥3/≥2) are also unmet.

## G1a — readiness (mechanical count, from `readiness_map.csv`)

All 51 cells of the 17-instrument × {1h, 2h, 4h} universe are READY: 0
invariant violations, determinism replay drift 0, all look-ahead truncation
probes pass, all cells ≥30 TRAIN `/ANCHOR` events. No cell is excluded;
the full grid enters Track B. (Contrast EXP-043's 50/51 on the old anchor —
the `/ANCHOR` event population is anchor-specific and was gated fresh.)

## G1b — mechanical count (from `shift_classification.csv`)

| P5 leg | Rule | Count |
| --- | --- | --- |
| 1 — MFE shift | Δ median MFE ≥ 1×SE_diff | **0/51** (Δ −2.7…+0.9 bps; 29/51 exactly 0.0; best margin −1.67 bps, EURUSD-1h; no borderline flags) |
| 2 — floor headroom | `/ANCHOR` median MFE ≥ 2×floor (M=2) | 51/51 |
| 3 — MAE offset | MAE shift does not erase the gain | n/a (leg 1 empty) |
| 4 — event floor | ≥30 TRAIN events | 51/51 |
| 5 — determinism | replay drift 0 | 51/51 |
| **SHIFTED_VIABLE** | all legs | **0/51** → composition (≥5/≥3) NOT MET |

## Integrity preconditions (all satisfied — the FLAT readout is valid)

- **Baseline reconciliation:** 125/125 checks PASS; gross(H=8) recompute
  matches EXP-046 persisted values at diff exactly 0.0; EXP-043 count
  identities hold.
- **Determinism:** replay drift 0 on every cell, both anchors.
- **P8 regression gate:** 15/15 green before the first TRAIN read
  (anchor parameterisation covered; baseline bit-for-bit).
- **Budget discipline:** 0 slots, 0 TEST reads, ledger unchanged (EURUSD-4h
  AT CAP 2, USTEC-4h 1, XAUUSD-4h 1, all others 0); holdouts sealed; no
  threshold, grid, or anchor re-parameterisation after data contact.
- **Audit:** PASS — 0 Critical, 2 Warning, both interpretive (recorded in
  the adjudication notes below); neither affects the mechanical count.

## Adjudication notes (caveats carried, none alters the count)

1. **The FLAT readout is mechanically valid but near-structurally forced
   (audit W2).** At the ratified k=1.0 the ATR-prominence rule selects the
   baseline running extreme in ~95–99% of regimes (anchor coincidence
   97.8/98.3/98.5% mean by domain, min 94.6%; 13/51 cells with literally
   identical event populations), while the predeclared `fallback_rate`
   disclosure read only 0.7–1.5% — the dominant collapse path was
   qualification, not fallback (audit W1). The verdict therefore closes the
   **ratified `/ANCHOR` definition only**; it is not evidence that anchor
   placement is irrelevant under a binding prominence threshold. A
   binding-k variant would be a *new* predeclared scope (report
   "Implications"), not a re-opening of this one.
2. **Leg 2 passing 51/51 is the load-bearing descriptive surprise:** median
   lifetime MFE ≈ 24/36/64 bps on 1h/2h/4h against binding floors ≈
   4.9/5.3/7.2 bps (≈5–9× floor, both anchors, censoring ≤3.1%). Move
   availability was never the constraint; **capture geometry** (peak →
   realizable exit, net of cost) is. This is the primary input to the
   new-family design brief (design §10).
3. **Matched-control context cuts against in-family hope:** control median
   MFE ≈ event median MFE on all three domains — the bounce trigger accesses
   no privileged move sizes (descriptive; same-sub-segment circularity
   disclosed).

## Operator decision record

Design §1.5 item 2 (ratified pre-data, 2026-06-12): *"if the `/ANCHOR`
available-move distribution remains capped near the cost floor → … route to
a new candidate family."* The literal "capped near the cost floor" premise
was refuted by leg 2 (the move clears the floor everywhere), but the
operative G1b rule (§8.3, frozen at D0) keys on the SHIFTED_VIABLE
composition, which fails 0/51: the `/ANCHOR` lever produces **no shift**,
so the in-family branch is closed and the pre-committed FLAT routing
applies. Per design §1.5 item 3 and §10, no family selection or new-family
design is performed here; routing only.

## Consequences

| Item | State |
| --- | --- |
| Phase 013 | CLOSES — ANCHOR_MOVE_FLAT; retrospective records the hand-off (design §10) |
| `CF-AVWAP-001/ANCHOR` (as ratified, k=1.0) | CLOSED-MEASURED — inert at these timeframes; re-opening requires a new D0 with a demonstrably binding threshold |
| `CF-AVWAP-001` candidate family | **CLOSED for new in-family phases** — every move-geometry and tuning lever is measured and exhausted: exits (010–011), entry parameters (012), anchor (013); the remaining Stage-C detectors (`/LB` `/MB` `/ATR`) are regime-timing levers, not move-geometry levers (design §10), and stay DEFERRED with no candidate status |
| Phase 014 | New candidate family: own design/D0; fresh EXP-020/027/029-analog readiness/calibration/parity scaffolding; design brief targets **capture geometry**, not move availability |
| EXP-047 anchor-parameterised `xen.avwap` machinery + regression suite | RETAINED (default-preserving, baseline bit-for-bit); available to any future scope |
| TEST budget | Untouched (0 of ≤6 phase reads spent); ledger unchanged; holdouts sealed |
