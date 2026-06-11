# EXP-042 — Results Interpretation (Stage 6)

> **SET ASIDE 2026-06-11 — FRAMING_ERROR.** This interpretation carries zero
> weight: the arm-at-adverse-band entry rule applied the band multiplier as
> an entry filter, but the band was always an exit parameter (Phases
> 004–010). Final disposition `MEASUREMENT_COMPLETE — FRAMING_ERROR`; Track
> A0 removed from Phase 011; the pending adjudication is moot. See
> `report.md` and
> `docs/code-reviews/2026-06-11-band-multiplier-framing-error.md`.

**Date:** 2026-06-11
**Verdict:** `BAND_SELECTED_DEGENERATE_FLOOR_PENDING_ADJUDICATION` (set
aside — see banner)
**Audit:** PASS (no Critical/Warning; see `audit.md`)

## What the scan measured

5 bands × 17 instruments × 3 domains (255 cells) on TRAIN only, under the
operator-ratified arm-at-adverse-band entry rule. Selection by the frozen
rank rule (within-cell rank of mean gross H=8 forward return; n ≥ 30 floor;
median rank across 51 cells; wider-band tie-break).

## Outcome

- **Selected band: 1.0** — median rank 2.0 vs 5.0 for every wider band.
  Unique minimum; the tie-break was not needed.
- **DEGENERATE_FLOOR fired:** floor-imputed cell fractions are 0.41 (b=1.0),
  0.65 (1.5), 0.88 (2.0), 0.98 (2.5), 1.00 (3.0). Every band ≥ 1.5 exceeds
  the 50% threshold, so per the amended scope the **band freeze is withheld**
  pending operator adjudication.

## Honest reading of the selection

The wider bands did not lose on measured return — they lost on **event
starvation**. Their median rank of 5.0 is dominated by worst-rank imputation,
not by inferior per-event gross: where wider-band cells do have events, their
per-event gross is often *higher* (e.g., AUDJPY-1h H=8: −2.8 bps at b=1.0 →
+16.7 at 2.0 → +19.6 at 2.5, on 19 and 14 events respectively), exactly the
deeper-pullback/stronger-reaction pattern the design conjectured. The scan
answers "which band has usable event rates with non-degraded gross"
(b=1.0), not "which band has the best per-event economics" — at current
data volumes those are different questions, and the frozen rule
deliberately privileges the first. This is the F02 proxy-alignment
disclosure materializing, and it is the honest basis for adjudication.

## Power statement (band 1.0, supersedes all band-era power analyses)

| Domain | Median TRAIN events/cell (min–max) | Cells ≥ 30 events (of 17) | Median projected TEST events |
|---|---|---|---|
| 1h | 69 (58–101) | **17/17** | ~30 |
| 2h | 37 (25–56) | **13/17** | ~16 |
| 4h | 19 (10–27) | **0/17** | ~8 |

Median gross H=8 per event: 1h −1.5 bps, 2h +0.9 bps, 4h +5.7 bps
(descriptive, gross, selection-internal — not edge claims).

## Implications for the phase (evidence, then assessment)

**Evidence:** the new entry rule thins events ~3–5× vs the historical
baseline. At band 1.0, 4h has 10–27 TRAIN events per cell — below the floor
everywhere — and ~8 projected TEST events.

**Assessment (for the adjudication and Track B planning):**

1. **4h per-cell exit training is unpowered at any band.** With ≤27 TRAIN
   events, an 8-point FH grid plus split-half tunability checks will almost
   certainly return non-tunable; 4h cells are unlikely to contribute
   portfolio members. This is the design's §7.4 power wall, now quantified
   for the new event population.
2. **1h is the only fully-powered domain; 2h is usable for 13/17 cells** —
   consistent with the design's expectation that 2h is the middle ground,
   though thinner than its band=1.0-era projection (~180 events).
3. The DEGENERATE_FLOOR adjudication is between: **(a)** accept band 1.0
   with the disclosure and proceed to Track A/B on this power base, or
   **(b)** close the phase early (FOUNDATION_NON-TUNABLE path). Option (a)
   is defensible — band 1.0 is the only band with a usable event supply, and
   the selection rule behaved exactly as predeclared. What option (a) cannot
   claim is that 1.0 was shown *better per event* than wider bands; that
   comparison is unpowered and stays open.

## Caveats (from audit and scope)

- All means are gross, no costs, no exits — selection-internal only.
- Extreme cell means (−282 to +207 bps) sit in floored small-n cells.
- DE30 truncated history (boundaries from its own timeline; disclosed).
- The entry-rule discontinuity stands: these populations (including b=1.0)
  are not comparable to Phase 004–010 results (design §7.5 + amendment log).

## Follow-up (new scopes only)

- If adjudication accepts band 1.0: proceed per design to Track A
  (EXP-020/027/029-analogs) on the band-1.0 population; consider excluding
  4h from Track B training (or accepting its predictable non-tunable
  outcomes as recorded evidence).
- A dedicated, separately-scoped wider-band study only becomes meaningful
  with materially more history per instrument; not this phase.
