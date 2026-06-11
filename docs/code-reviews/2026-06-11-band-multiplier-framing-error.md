# Band-Multiplier Framing Error: Exit Parameter Applied as Entry Filter in EXP-042

**Date:** 2026-06-11.
**Status:** IMMEDIATE — active discovery affecting Phase 011 Track A0.
**Affects:** EXP-042 (Track A0 band-selection scan, already executed).
**Discovered:** Post-execution review of EXP-042 results.

---

## 1. The Error

The arm-at-adverse-band entry rule implemented in EXP-042 treats the band multiplier as an **entry filter** — requiring price to breach `AVWAP ± b×MADspread` before the bounce signal can arm. This is a conceptual error. The band multiplier was always an **exit parameter** across Phases 004–010, controlling where favorable/adverse exit targets sit, never interacting with entry.

**Consequence:** EXP-042 tested a filtered subset of events (deep-pullback bounces only) and selected band=1.0 solely because it was the only band with enough events to rank — not because it's the right exit parameter. The DEGENERATE_FLOOR verdict was an artifact of measuring the wrong thing.

---

## 2. Evidence from Prior Experiments

### 2.1 Candidate family registry (`avwap.md`)

The first-branch definition lists the band under AVWAP and bands (line 86-88):

> *"Band spread: median absolute deviation of typical price from the anchored AVWAP path since the active anchor."*
> *"First-branch band multiplier: 1.0."*

This is a **descriptive stat** — it measures how far price typically disperses from AVWAP. It does not enter the bounce definition.

The bounce definition (`avwap.md`:93-104) makes no mention of bands:

> *"bullish regime: arm when a completed close is below AVWAP; trigger when a later completed close crosses back above AVWAP."*

The band appears only in the **exit** section (`avwap.md`:146-150):

> *"long/bullish bounce favorable target: the upper MAD band value frozen at the trigger bar; long/bullish bounce adverse target: the lower MAD band value frozen at the trigger bar."*

The registered non-baseline branch `/BAND` (`avwap.md`:219) is described as:

> *"band-multiplier sensitivity over predeclared values, with no post-result selection"*

It is listed alongside `/ALPHA` (volume exponent) and `/MA-DOMAIN` — all **exit/structural parameters**, not entry parameters.

### 2.2 EXP-022 (original lifetime study)

Scope.md line 26-35:

```
Parameters:
  - AVWAP branch: MA(20,50) regime detector, typical price, TickVolume ** 0.75,
    MAD band multiplier 1.0, and EXP-020 bounce definition unchanged;
  - event favorable/adverse targets: EXP-020
    favorable_target_at_trigger and adverse_target_at_trigger, frozen at
    trigger time;
```

The band multiplier is a fixed parameter; the bounce definition is "EXP-020 bounce definition unchanged" — arm at AVWAP side, no band involvement.

### 2.3 EXP-028 (faithful re-screen)

Scope.md line 20-22 lists the band under the strategy definition:

```
| Band spread | Median absolute deviation from anchored typical-price path |
| Band multiplier | 1.0 |
```

And line 22:

```
| Bounce definition | EXP-020: arm on close below AVWAP (bullish)/above AVWAP (bearish); trigger on close crossing back |
```

These are separate rows. The band never touches the bounce definition.

### 2.4 EXP-030/033/037/039

All later experiments inherit these definitions unchanged. The band multiplier 1.0 appears as a frozen parameter; nowhere does it enter entry logic.

---

## 3. How the Error Entered

The Phase-011 planning document (`docs/planning/phase-011-redesign-per-instrument-foundation.md`) proposed a band-scan Track A0 without precisely specifying *where* the band attaches. The design document (`docs/experiments-docs/checkpoints/2026-06-11-011-per-instrument-foundation/design.md §5.2`) inherited this ambiguity — it described measuring "mean gross forward return at H=8" after a bounce event, which is compatible with either interpretation.

The error was **operationalized in EXP-042's scope** (`python/experiments/EXP-042/scope.md`:31-39):

> *"in the frozen baseline the band plays no role in entry ... so a naive multiplier sweep would leave the event population unchanged — the scan would be vacuous. Phase 011 therefore uses the **arm-at-adverse-band** rule."*

The diagnosis was correct (the band does not affect entry in the baseline) but the prescription was wrong. The correct conclusion: the band belongs in **exit training (Track B)**, not entry. No entry-level sweep is needed because the band is not an entry parameter.

The pre-execution review caught the DEGENERATE_FLOOR edge case (F03) but did not re-examine whether the band should be filtering entry at all.

---

## 4. Impact

| Artifact | Impact |
|----------|--------|
| EXP-042 results | Measure filtered events, not the full bounce population. Rank table and selected band=1.0 reflect data availability, not exit parameter quality. The output is not usable for its intended purpose. |
| Track A0 concept | An entry-level band scan is conceptually invalid. The band multiplier does not and should not affect entry. |
| Phase 011 design §5.2 | Must be deleted or rewritten. The band selection step has no object. |
| Phase 011 design §5.4 (Track B) | The MAD-band-multiplier sweep in Track B is unaffected — this is where the band always belonged. It remains the correct path for selecting exit-target levels per instrument per domain. |

---

## 5. Resolution

1. **EXP-042 results are set aside.** No decision is based on them. The band=1.0 "selection" is discarded.
2. **Track A0 is removed** from Phase 011. There is no entry-level band to select. The entry remains the frozen AVWAP arm/trigger at the line itself.
3. **The band multiplier moves entirely to Track B** (exit training) — per-instrument×domain n-neighbour stability selection, as originally designed for the MAD-band-target exit family. This is unaffected by the error.
4. **The Phase 011 design is amended** to reflect the removal of Track A0 and the correction. EXP-042 is recorded as a diagnostic that measured filtered events; its code and results are retained but flagged.
5. **The Phase-011 planning document's "band=2.0" discussion is moot** — the band was never going to be an entry parameter anyway. The "second guess" critique of the planning document (which led to Track A0) was predicated on a misunderstanding of what the band does.

---

## 6. What This Uncovered About Process

1. **Design ↔ scope handoff ambiguity.** The design document said "band sweep" but never specified where the band attaches. The scope made an operational choice that contradicted all prior experiments. A missing traceability step.

2. **Review missed the framing question.** The pre-execution review focused on edge cases (DEGENERATE_FLOOR) and correctness of implementation, not on whether the measurement matched the parameter's historical role.

3. **The registry's `/BAND` branch is defined as an exit/structural parameter**, not an entry parameter. If the scope had been checked against the registry definition, the mismatch would have been visible.

---

## 7. File-Drawer Entry

EXP-042 is recorded as **MEASUREMENT_COMPLETE — FRAMING_ERROR** in the multiplicity registry. Its code, results, and run_metadata are retained as a negative-process record but carry zero weight in Phase 011 outcomes. It consumed no candidate slot (diagnostic) and no TEST reads.
