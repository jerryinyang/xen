---
name: gate-implies-label-and-live-controls
description: Gating by a state without labelling realised state makes questions unaskable; a control that equals the real estimate is a failed control.
metadata: { type: lesson, chapter: 5 }
---
Two emission defects found together at the SPDR-021/022/023 confirmation extraction, both of
which made questions **unaskable rather than underpowered**:

1. **Gate implies label.** All six cells gated arms by volatility state and none recorded the
   **realised** regime on the origin or trade. Gating writes state into control flow and then
   discards it; no analysis recovers a column that was never written, and reconstructing it post
   hoc uses a different clock than the gate did, silently adding look-ahead. Fix: emit the
   decision-time state as a labelled column (`E1`), inherited by every fill. Caught at QA.

2. **Controls must differ.** `TIME_DERANGEMENT` returned the **identical number to the real
   estimate on 100% of rows in all six cells**, across multiple experiments, reported as held
   throughout. A control that equals the real estimate does not fail — it *agrees* — so the
   harness reports green precisely because the control is vacuous. Fix: every control carries a
   HARD **non-degeneracy assertion** (must differ on a stated minimum share of rows). Removed,
   not repaired.

Companion to the check-*count* rule (L-52): that asserts a check **ran**; this asserts it has
**content**. See [[matched-random-timing]].
