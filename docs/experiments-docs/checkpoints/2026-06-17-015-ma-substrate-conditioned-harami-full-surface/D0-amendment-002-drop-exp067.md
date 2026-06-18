# D0 Amendment 002 — Drop EXP-067 (hybrid combined champion); close the Phase 015 slate

**Status:** RATIFIED (operator direction, 2026-06-18). Dated amendment to the Phase 015 `design.md`
(§5/§7) and `D0-predeclarations.md` (P9) under the rule "any change after ratification is a new
registered branch or a dated amendment" (`D0-predeclarations.md` head). HYP-020/EXP-067 is **dropped,
not deleted** — it is retained in `multiplicity-registry.md` (never deleted or reused), exactly as
HYP-022/EXP-069 was dropped under Amendment 001. **No countable item is added or removed; 0 candidate
slots, 0 TEST reads unchanged; holdouts sealed.**

---

## 1. Decision (operator, 2026-06-18)

**Drop EXP-067 (the hybrid combined champion, HYP-020).** The Phase 015 dual-object surface is
declared complete after EXP-068. The hybrid object is adjudicated at the single terminal **G-015** on
the **disclosed surface reads** (EXP-061–066), not on a dedicated combined-champion measurement.

## 2. Rationale

1. **The hybrid object is EVIDENCE_AGAINST across the entire individual surface.** L1 (EXP-061) —
   EVIDENCE_AGAINST (`H0`: 1 cell); S1 (EXP-064) — EVIDENCE_AGAINST (0/7 variants); S2 (EXP-065) —
   INCONCLUSIVE (power-limited, max 4 powered cells); S3 (EXP-066) — EVIDENCE_AGAINST (0 arms
   compose). L2 (EXP-062) — only 4/99 signal-attributable (generic MA-segment property).
2. **A combined champion can only assemble per-layer winners.** The hybrid object has **no** per-layer
   geometry that composes at P11 — there is nothing positive to combine. EXP-067 would assemble the
   benchmark/PARTIAL-V2A geometry on the hybrid object, which already failed at S3 (EXP-066 hybrid:
   0 arms compose).
3. **The levers are additive-not-synergistic for this family** (established at EXP-060): a combined
   read is extremely unlikely to surface synergy absent in every individual layer.
4. **EXP-067 does not gate G-015.** G-015 PROCEED requires ≥1 combined definition on **either** object
   (per `design.md` §7); the native object (EXP-068) already satisfies the full conjunction as a
   PROCEED_TO_SCREEN-candidate, independently judged and never pooled with hybrid. Skipping EXP-067
   cannot change whether G-015 can PROCEED.
5. **Resource conservation.** Running a near-certain CHARACTERISED_NOT_VIABLE / EVIDENCE_AGAINST read
   that gates nothing is not a good use of compute.

## 3. What this changes (and what it does not)

- **Changes:** the hybrid object's G-015 input is the **disclosed surface synthesis**
  (EVIDENCE_AGAINST dominant; INCONCLUSIVE at S2), recorded as a documented **inference**, rather than
  a dedicated EXP-067 combined-champion measurement. The Phase 015 slate is **complete** after EXP-068.
- **Does not change:** the native PROCEED_TO_SCREEN-candidate (EXP-068) stands unaffected; G-015
  remains the single terminal gate, judged per object individually; the two objects are never pooled;
  the no-early-*closure* discipline is intact (this drops a confirmatory read on an already-negative
  object — it does **not** close the family early, and it does not skip any read on the *native* object
  that carries the live signal). 0 candidate slots, 0 TEST reads; `test-read-ledger.md` unchanged.

## 4. Honest caveat (recorded for the G-015 gate)

The genuine hybrid **combined-champion** efficacy is, strictly, **unmeasured** — its G-015 disposition
rests on the strong, but inferential, extrapolation from the individual surface reads (every hybrid
layer EVIDENCE_AGAINST or INCONCLUSIVE, no positive lever to combine, additive-not-synergistic levers).
The gate adjudicates the hybrid object as **CHARACTERISED_NOT_VIABLE on the disclosed surface** on that
basis. If the gate (operator) judges the inference insufficient, EXP-067 can be reinstated as its own
scope before adjudication.

## 5. Slate after this amendment

| ID | Object | Role | Status |
| --- | --- | --- | --- |
| EXP-061–066 | hybrid **and** native | L1–S3 dual-object surface | COMPLETE |
| EXP-068 | **native** combined champion (hybrid disclosed) | S4/native integrative readout | **COMPLETE — PROCEED_TO_SCREEN-candidate (G-015 input)** |
| ~~EXP-067~~ | ~~hybrid combined champion~~ | ~~S4/hybrid~~ | **DROPPED (Amendment 002)** — hybrid adjudicated at G-015 on the disclosed surface reads; retained in the ledger, never deleted or reused |
| ~~EXP-069~~ | — | — | DROPPED (Amendment 001) |

**Phase 015 experiment slate is COMPLETE.** Next step: the single terminal **G-015** gate
(operator-adjudicated), spanning both objects judged individually — native PROCEED-candidate vs the
disclosed hybrid EVIDENCE_AGAINST.

## 6. Registry / governance impact

- `multiplicity-registry.md` — `CF-HA-HARAMI-001/HYP-020` (EXP-067) PLANNED → **DROPPED (Amendment
  002)**; retained, never deleted/reused. No countable item changed.
- `candidate-families/harami.md` — EXP-067 drop + hybrid-on-disclosed-surface note recorded.
- `design.md` §5/§7 and `D0-predeclarations.md` P9 — in-file pointers to this amendment (this file is
  the governing record).
- Master `docs/experiments-docs/INDEX.md` live status + `Family Indexes` table — slate complete; G-015
  the next step.
- **0 candidate slots, 0 TEST reads unchanged; holdouts sealed; `test-read-ledger.md` unchanged.**
