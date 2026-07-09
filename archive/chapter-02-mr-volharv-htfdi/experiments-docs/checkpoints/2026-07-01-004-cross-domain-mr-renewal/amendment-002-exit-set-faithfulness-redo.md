# Amendment 002 — CF-MR-004 exit-set faithfulness redo (EXP-014b)

**Date:** 2026-07-02 · **Author:** research-pipeline orchestrator (operator-directed) · **Supersedes:**
EXP-014's binding verdict (downgraded → CONFOUNDED-exploratory, record retained, never deleted).

## Why

EXP-014 shipped NOT_TRADABLE on the "faithful" full-exit strategy. Operator review (2026-07-02) found
**two further silent deviations from the proposal** (`.ignore/idea/`), both introduced by amendment-001's
exit design, both verdict-material — the same L-14 class of defect that downgraded EXP-013:

1. **Unspecified horizon time-stop.** `newer.md:8-10` names exactly two exits — form-2 favorable limit +
   form-1 event-reversion — then states **"no other exit methods enforced on the positions."** Amendment-001
   added a `min(48,3·HL)` horizon last-resort. Forensics (EXP-014 `cis_trades`): horizon = **30-50% of all
   trades and the ONLY losing leg** (−43…−100 bps/trade); the 48-bar cap mechanically **starved form-1** and
   guaranteed non-reversion for slow series (S6 half-life ≈ 1029 bars ≫ 48). The horizon manufactured the
   losing leg and the "capture-vs-dispersion wash" verdict.

2. **Moving/refreshing form-2 target.** Amendment-001 refreshed the form-2 TP to the moving anchor mean each
   bar. The intended design is **per-signal, entry-referential**: entry price = f(spread, current price);
   **exit price = f(spread, entry price)**, locked at signal time. A target recomputed off the drifting anchor
   (not the entry price) was never intended — it fills on partial/drifting recovery, not the signal's own
   reversion (EXP-014 S8: 59% form-2-fill ≈ 58% *fraction-recovered*, not the 22% full-reach; reversion ≈
   random control). This is why independent per-signal pricing warranted the re-entry axis in the first place.

## What changes (EXP-014b = direct copy of EXP-014, two deltas)

| # | Delta | Detail |
|---|-------|--------|
| D1 | **Remove horizon** | Exit set = form-1 event-reversion + form-2 favorable-limit **only**. A non-reverting position rides until form-1/form-2 fires or the fence stops it. |
| D2 | **`/TRAIL` axis** | New exit axis. **OFF (default, faithful):** form-2 TP fixed at open to the entry-referential level `EntryFill·exp(dir·band)`, band = Z*·σ locked at the arm bar; never moved. **ON (disclosure):** trailing moving-anchor-mean refresh (the EXP-014 behaviour). |
| D3 | **Open-at-end handling** | Still-open legs at the fence emitted as **censored** `open_at_end` rows (RealizedBps NaN) — **excluded** from the realized-P&L referee, disclosed as a survival count. (Operator: censor + disclose.) |
| D4 | **Richer emission** | `cis_trades` gains `FixedExitPrice`, `MaeBps`, `MfeBps` (per-hold excursion), `Censored`. All other emission unchanged. |
| D5 | **Full-cross arm matrix** | reentry {none,allow,extend} × recalc {R,S} × trail {fix,trail} = **12 arms/series × 4 = 48 confs, ~456 cells**. Binding PRIMARY = **none-R-fix** (the faithful fixed-exit design). |

Everything else is identical to EXP-014: series S5/S6/S7/S8 defs, WZ/Z*/Wa, min-mate valid-basket rule,
breach policy, conditioners (trend/vol), 6-stage MR screen booked pre-verdict, dislocation-matched
availability control, leak tripwires (peer-feed phase-shift + label-perm, on-demand for admitting cells),
frozen 4h referee **untuned** (L-12), first-49% TRAIN fence (EXP-013 cutoffs), final-30% sealed, 0 counted
reads. From-scratch family code extended in place (L-13).

## Fixed-exit definition (operator-confirmed)

`exit = EntryFill · exp(dir · band)`, `band = Z*_level · σ_arm`. SHORT (dir=−1): `EntryFill·exp(−band)`
(lower). LONG (dir=+1): `EntryFill·exp(+band)` (higher). The dislocation (Z*σ) is **frozen at signal time**;
the exit tracks the price actually filled, not the drifting anchor. Coincides with `exp(anchorLog_entry)`
only when the fill == the limit exactly; diverges (correctly) on gap fills.

## Status of the EXP-014 verdict

**Downgraded to CONFOUNDED-exploratory** (like EXP-013): the horizon + moving-target deviations invalidate
the NOT_TRADABLE closure gate. EXP-014 remains a valid **exploration** — it established that form-2 capture
is positive pre-horizon (ci_low>0 all series, biased) and that availability does not separate at 4h under
the moving target. EXP-014b is the faithful test that can actually adjudicate the family. Record retained.

## Lessons touched

- **L-14** (silent dropped/substituted core exit → confounded verdict) — re-affirmed and **widened**: the
  pre-exec exit-set diff must catch **added** unspecified exits (horizon) and **altered** exit *semantics*
  (fixed vs moving), not just missing ones. The EXP-014 gate diffed *names* (form-1/form-2 present ✓) but not
  *semantics* (moving vs fixed) or *additions* (horizon). See `lessons-and-amendments.md`.
