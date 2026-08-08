---
name: infr022-powering-strip
description: INFR-022 powering strip: sample-size context + direct baseline comparison only; MDE/floors retired
metadata: { type: lesson, chapter: 6 }
---
Operator directive INFR-022 (2026-08-08), lesson L-63: MDE, detection floors (`2.8/sqrt(n)`,
`MDE_Z x SE`), power curves, `min_powered_seeds`/`n_legs_floor` vetoes, and machine power labels
are retired from live designs/code/artifacts. Retained: sample-size context (never a hide rule)
and DIRECT comparison against a pre-specified baseline. The leak tripwire's integrity bite is
`INTEGRITY_Z x bootstrap_SE` (N6b) — never called MDE.
