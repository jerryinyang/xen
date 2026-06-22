# Phase 019 D0-Amendment-001 — Screen M Compression-Primitive Freeze

**Date:** 2026-06-22.
**Status:** **RATIFIED (operator, EXP-086 scoping session).** Concretizes the two D1 "frozen at D0"
placeholders for **Screen M (EXP-086)** that the ratified D0 (`D0-predeclarations.md`) carried as an
unresolved menu. **No other D0 decision changes**; D2–D6, the GREEN bite-check, the gate constants, the
member set, seeds, and the TRAIN-only / 0-slot / 0-read discipline are unchanged.

## Why this amendment exists

D0 §D1 froze Screen M's conditioning as *"HA-harami inside-bar **and** a clean NR/inside-bar primitive
(NR4/NR7 **or** inside-bar, frozen at D0)"* and the existing-detector phrasing for the harami arm. The
parenthetical left the **specific** compression primitives unpinned (a three-way NR/inside-bar menu, and an
unstated harami-detector identity). Both materially change the event population and the matched-random
control, so they must be pinned **before** result-producing code, on the record, to avoid a post-hoc
goalpost. The operator ruled on both at EXP-086 scoping.

## The two freezes (binding for EXP-086 and the eventual CF-VOLEXP-001 family)

1. **HA-harami arm = RAW, direction-agnostic `xen.ha_harami.detect_ha_harami`.** The latest HA body strictly
   inside the prior HA body — a single-series **compression state**, with **no** MA(20,50) segmentation and
   **no** `/STRONG-STAT` conditioning. This is the correct fit for a **non-directional magnitude** axis; the
   MA(20,50)-conditioned `xen.capgeo_substrates.harami_native_entries` (the Phase-018 *directional* substrate)
   is explicitly **not** used here — that is the dead 2×2 cell. Conditioning runs on HA (synthetic) candles
   for **detection only**; every return/range/availability metric is on real prices (D6).

2. **NR/inside-bar arm = NR7 (narrowest true range in the trailing 7 bars), real OHLC.** Bar *i* fires iff
   `TrueRange(i) == min(TrueRange(i−6 … i))`. Lookback **7 frozen**; parameter-free otherwise. Chosen over
   NR4 and the plain real-bar inside-bar as the canonical low-volatility **compression precursor to range
   expansion** — directly mechanism-aligned with the CF-VOLEXP-001 magnitude/expansion thesis Screen M
   targets. NR7 is causal (uses only bars `≤ i`), deterministic, and read on real domain OHLC.

## Accounting (unchanged)

- These are the two conditioning primitives **within** the already-registered Screen-M axis
  (`M — CF-VOLEXP-001/HYP-001`, multiplicity-registry Phase 019 batch). They are **not** new countable axes
  — the axis is the countable selection unit; both the raw-harami and NR7 reads sit inside it. **No new
  multiplicity-registry entry** is created by this amendment.
- **0 candidate slots, 0 counted TEST reads, holdout never touched** — unchanged. TRAIN sub-split only.
- The D2b permuted-axis admission gate, its GREEN bite-check (report sha256 `208dfb3f…`), the realized cell
  count `C=46`, the FWER band, and the cross-axis Holm structure are **unchanged** — the gate is
  primitive-agnostic by construction (it permutes the conditioning labels of whatever primitive is supplied).

*Governing design: `design.md` §5 (EXP-086) · `D0-predeclarations.md` §D1/§D3.M · candidate family
`../../../signal-registry/candidate-families/family-selection-phase-019.md` (CF-VOLEXP-001).*
