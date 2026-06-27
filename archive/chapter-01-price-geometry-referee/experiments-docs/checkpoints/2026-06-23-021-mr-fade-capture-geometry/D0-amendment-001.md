# Phase 021 D0 — Amendment 001 (pre-execution clarifications)

**Date:** 2026-06-23 (operator-authorized). **Status:** APPLIED to `D0-predeclarations.md` (D2.4, D7).
**Nature:** **Clarifications, not parameter changes.** No ratified value in the D0 parameter table is altered;
no result-producing code (EXP-090) has run, so **no hard-delete / rerun is required** (programme deviation norm
applies to post-run confounds; these are pre-execution specifications filling two under-specified points).

**Checkpoint:** `2026-06-23-021-mr-fade-capture-geometry` · **Amends:** `D0-predeclarations.md` §D2.4, §D7.

---

## Clarification 1 — ATR triple-barrier time barrier (D2.4)

**Gap.** D2.4 specified the ATR triple-barrier conventional contrast arm's favourable (`1.0×ATR`) and adverse
(`2.0×ATR`) legs but was **silent on its third (time) barrier**. D2.3 requires the **adverse side (stop + hold
horizon) held identical across all arms** so that a win is attributable to the favourable target, not the stop
or the hold window.

**Resolution.** The ATR triple-barrier's **time barrier is the same EXP-089 MR-tempo cap (param #3)** used by
every other arm (native and contrast). With this fixed, the ATR triple-barrier differs from the native arms
**only** in its favourable leg (a fixed `1.0×ATR` target vs RCT's reversion-completion price / ERT's
equilibrium return) — preserving favourable-capture isolation (EXP-057 discipline).

## Clarification 2 — EXP-093 counted-read attaches to the stratum, not the (exit × cell) pair (D7)

**Gap.** D7 says EXP-093 carries "best 1–2 cells per surviving exit" and "each carried (instrument, domain)
cell spends 1 counted TEST read." With **multiple surviving exits**, two exits could select the **same**
(instrument, domain) cell — leaving it ambiguous whether that stratum is read once or twice, and whether a
single EXP-093 could push one stratum toward its 2/2 lifetime cap.

**Resolution.** **One stratum = one counted read per EXP-093, regardless of how many surviving exits select it.**
The counted read is the stratum's events entering the binding gate, which happens **once** for that
(instrument, domain) stratum no matter how many exits are evaluated on it. So if two surviving exits both carry
the same cell, that stratum goes **0→1**, not 0→2. The 2-lifetime-per-stratum cap is therefore honored with
one read preserved for any future confirmation, and no single EXP-093 can exhaust a stratum's cap.

---

*Both clarifications are reflected inline in `D0-predeclarations.md` (§D2.4, §D7) with a back-pointer to this
file. The G-021 adjudication checklist (`G-021-gate-criteria.md` §3.5) reads the counted-read accounting against
this clarified rule.*
