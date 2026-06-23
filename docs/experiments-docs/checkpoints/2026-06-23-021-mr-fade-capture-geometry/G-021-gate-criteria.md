# G-021 Gate Criteria — RSI-2 Fade Capture-Geometry & Tradability (PENDING — pre-adjudication)

**Date:** 2026-06-23 (gate *definition*; **not yet adjudicated**).
**Gate:** G-021 (Phase 021 terminal gate — **tradable / not-tradable / inconclusive** verdict on the
**bare RSI-2 fade (CORE)** admitted at G-020, by a net-of-cost capture-geometry screen + a one-shot TEST read).
**Status:** **PENDING.** This fixes the mechanical rubric the future G-021 adjudication applies, frozen before
EXP-090 runs (freeze the rule, not the story). The adjudication (`G-021-gate-review.md`, mirroring G-017/G-019/
G-020) is written **after** the EXP-090→093 arc, reading the realized numbers against this rubric.
**Adjudication basis:** the predeclared **D6 decision rules** over the **frozen referee suite** (D4); cost from
the **EXP-085 conservative model** (D3). The `ASS` qualifier is **non-binding** (G-017).

---

## 1. What G-021 decides (and what it does not)

G-021 emits a **tradable / not-tradable / inconclusive** verdict on the admitted lever — *does the bare RSI-2
fade's gross ~0.75-ATR / ~3-bar favourable availability convert to a positive expectancy that survives
conservative cost, clears the frozen referee, and holds on a counted TEST read?* It decides:

- whether **any exit** in the D2 slate produces a net-of-cost edge that clears the frozen suite on TRAIN
  (EXP-091/092), and whether the carried candidate(s) **confirm on the one-shot TEST** (EXP-093); and
- whether the **native intrabar pair (RCT/ERT) beats the reactive conventional contrast** — a descriptive
  attribution within the verdict, not a separate gate.

It does **not**: consume an additional candidate slot (the first was consumed at G-020); read the **final-30%
global holdout** (a holdout release is a separate, later gate); re-open the inert vol-regime partition, the dead
TREND/FILTER variants, or any registered-but-deferred branch (each needs its own D0-amendment + slot decision).

## 2. The mechanical rules (from D0 §D6 — reproduced for adjudication)

```
EXP-091 (TRAIN screen):  exit×cell net-clears iff net ci_low_1s (Z=1.645, moving-block bootstrap) > 0
                         exit PASSES iff net-clears in >= 5 cells over >= 3 instruments
                         empty screen  ->  G-021 NOT_TRADABLE at 0 TEST reads

EXP-092 (TRAIN sequence): per-cell SEQUENCE_PASS at alpha=0.05 one-sided (net ci_low_1s>0, power-confirmed
                          by EXP-090 MDE)  ->  hash-pinned candidate set (sha256) + phase Holm rule

EXP-093 (one-shot TEST):  carried cell CONFIRMS iff Holm-adj p <= 0.05 AND ci_low_1s > margin
                          (margin = the cell's EXP-090-calibrated MDE); else INCONCLUSIVE_SPANS_ZERO / FAIL

G-021:  TRADABLE      iff >= 1 carried cell CONFIRMS on TEST under the frozen referee + phase Holm + margin
        NOT_TRADABLE  iff the EXP-091 screen is empty, OR every carried cell FAILS the TEST margin/Holm
        INCONCLUSIVE  iff the binding TEST read(s) are power-limited / span zero (à la EXP-032) — neither
                      confirmed nor refuted
```

The verdict is mechanical and predeclared; the explanation is not.

## 3. Adjudication checklist (what the G-021 review must affirmatively confirm)

Each item read **per stratum / per cell** (LESSON-001); no collapsed cross-cell boolean is binding.

1. **Substrate readiness (EXP-090).** Member set = the 15m/1h cells passing the D8 bracket (≥15 events, finite
   per-cell MDE under the frozen referee); `COVERAGE_EXCLUDED` cells recorded; realized counts quoted (supersede
   design figures).
2. **Screen integrity (EXP-091).** Net expectancy computed under the **EXP-085 conservative cost** (D3) — gross
   reported as descriptive sanity only; the ≥5-cell/≥3-instrument quorum applied per exit; the **native-vs-
   contrast** comparison reported (does the RCT/ERT pair net-clear more cells than the reactive arms, esp. RCT
   vs RSI-revert-on-close — the clean intrabar-vs-on-close A/B?). An empty screen routes NOT_TRADABLE here.
3. **Candidate set (EXP-092).** The `SEQUENCE_PASS` set is **hash-pinned (sha256)** with the phase Holm rule
   fixed **before** the TEST read; the carried set is the smallest defensible (≤1–2 cells/surviving exit).
4. **Fill-model honesty.** The intrabar 1m fills used **timestamp alignment** (never bar index), causal
   order-of-touch with the conservative adverse-first tie-break (tie-break incidence disclosed), and real
   touched fill prices (not synthetic, not 1m closes). RCT's "model-derived target price" caveat (D2.1) carried.
5. **TEST discipline (EXP-093).** Each carried (instrument, domain) cell spent **exactly 1 counted TEST read**
   on the **analysis-TEST stratum**, recorded in `test-read-ledger.md` in the **same change**; the
   **2-lifetime-per-stratum cap honored** (each carried stratum 0→1); the **final-30% global holdout never
   loaded**; the margin condition (`ci_low_1s` > EXP-090 MDE) applied alongside Holm.
6. **Referee fidelity.** The binding gate was the **frozen suite** (D4), not retro-edited; **`ASS` reported as
   non-binding** only. No new referee tuned.
7. **Integrity.** Determinism byte-identical (incl. the 1m walk + bootstrap stream); real-price metrics only;
   no entry/exit parameter tuned against TEST/holdout; deviation (if any) handled by dated amendment +
   hard-delete + full rerun, not a silent follow-up.
8. **No goalpost-moving.** Frozen D2 exit definitions / D3 cost / D6 thresholds not retro-edited after seeing any
   cell's outcome.

## 4. Programme routing (mechanical consequence)

| Adjudicated state | Consequence |
| --- | --- |
| **TRADABLE** | The bare RSI-2 fade is the programme's **first net-positive price entry**. Next: a sanctioned **global-holdout release** decision (separate gate) and/or deployment-readiness; the deferred levers (vol-regime, contrarian, 25/75, cross-cuts) become candidate expansions, each under its own slot/D0. |
| **NOT_TRADABLE** | The fade's availability does not convert to a net edge on this dataset. The lever closes; with the regime inert and the variants dead, **CF-MR-001 is effectively exhausted**. The programme returns to the **G-019 non-price-data frontier** (operator decision). Counted reads spent are permanent; the file drawer retains every cell. |
| **INCONCLUSIVE** | Disclosed; the candidate is neither confirmed nor refuted; any further read is a separate decision under the remaining per-stratum cap (1/2 left on each carried stratum). |

## 5. Integrity expectations at adjudication (carried)

- **Holdout sealed** throughout Phase 021; the final-30% global holdout never loaded (incl. its 1m bars).
- **TEST discipline:** counted reads only at EXP-093, on the analysis-TEST stratum, ≤1/carried-stratum, cap
  2/stratum honored, recorded in `test-read-ledger.md` in the same change; EXP-090–092 spend 0.
- **Determinism / real-price:** byte-identical second passes; real touched fill prices; ATR-unit metrics.
- **No goalpost-moving:** frozen D2/D3/D6 not retro-edited; per-stratum doctrine (LESSON-001) enforced — any
  collapsed convenience flag is NON-BINDING.
- **File drawer:** every exit-family and cell outcome (clears / dies / inconclusive) is **retained** in the
  registry and the Phase 021 multiplicity batch, never deleted or reused; a refuted exit is not silently
  reopened by re-parameterization.

---

*Companion documents: [`design.md`](design.md) · [`D0-predeclarations.md`](D0-predeclarations.md) §D6 ·
family spec [`../../../signal-registry/candidate-families/cf-mr-001.md`](../../../signal-registry/candidate-families/cf-mr-001.md).
The adjudicated outcome is written to `G-021-gate-review.md` (this directory) after the EXP-090→093 arc.*
