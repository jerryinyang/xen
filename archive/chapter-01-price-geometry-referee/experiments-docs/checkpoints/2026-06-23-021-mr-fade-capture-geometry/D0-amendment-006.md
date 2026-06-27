# Phase 021 D0 — Amendment 006 (EXP-093 carried TEST set = the full EXP-092 SEQUENCE_PASS set, all 11 cells)

**Date:** 2026-06-24. **Status:** **FROZEN — RATIFIED 2026-06-24 (operator-authorized).** **Nature:** a
**TEST-plan scope decision** for the one-shot EXP-093 confirmation. The frozen `D0-predeclarations.md` §8.3 /
D7 ratified the EXP-093 carried set as the **"smallest defensible set — best 1–2 cells per surviving exit"**,
with the exact cells deferred to "a D0 decision (operator-ratified) from the EXP-092 hash-pinned candidate set."
This amendment **fixes that deferred decision**: the operator ratifies carrying the **entire EXP-092
`SEQUENCE_PASS` candidate set — all 11 cells** (sha256 `f6427e83…`) — to the counted TEST read, **superseding**
the "1–2 cells per surviving exit/domain" sizing language. **Slot / read impact:** **0 new candidate slots**
(the first was consumed at G-020); **11 counted TEST reads** at EXP-093 (one per carried (instrument, domain)
stratum, each 0→1 of the 2-lifetime cap). Holdout untouched.

**Checkpoint:** `2026-06-23-021-mr-fade-capture-geometry` · **Amends:** `D0-predeclarations.md` §D6/4c
(Holm family re-sized to 11), §D7 (carried set + counted-read count), §8.3 (smallest-defensible sizing
superseded); `design.md` §4 (EXP-093 row), §8.3. **Everything else unchanged** (frozen entry, EXIT-RCT geometry,
adverse side, 1m fill engine, MR-tempo cap, `D0-amendment-003` cost table, the frozen referee suite, the
per-cell margins, and the TRAIN-only / holdout discipline).

---

## 1. Decision (recorded, not implied)

The operator directs EXP-093 to confirm on the **full EXP-092 `SEQUENCE_PASS` set, all 11 cells**, rather than
the smallest-defensible robust core (8) that the EXP-092 report recommended. The carried set is therefore the
complete hash-pinned candidate set `f6427e83…`:

| # | Stratum | Domain | TRAIN net_ci_low | margin (EXP-090/094 MDE) | clears margin (TRAIN) | mean & median + (TRAIN) |
|---|---|---|---|---|---|---|
| 1 | EURUSD-4h | 4h | 0.13509 | 0.025 | ✓ | ✓ |
| 2 | USDCHF-4h | 4h | 0.12224 | 0.025 | ✓ | ✓ |
| 3 | AUDJPY-4h | 4h | 0.11910 | 0.025 | ✓ | ✓ |
| 4 | XAUUSD-4h | 4h | 0.11492 | 0.025 | ✓ | ✓ |
| 5 | USTEC-1h | 1h | 0.10802 | 0.0125 | ✓ | ✓ |
| 6 | US2000-1h | 1h | 0.10393 | 0.0125 | ✓ | ✓ |
| 7 | GBPJPY-4h | 4h | 0.08645 | 0.025 | ✓ | ✓ |
| 8 | EURJPY-4h | 4h | 0.04986 | 0.025 | ✓ | ✓ |
| 9 | EURUSD-1h | 1h | 0.04697 | 0.0125 | ✓ | ✗ (median −0.010) |
| 10 | NZDUSD-1h | 1h | 0.03907 | 0.0125 | ✓ | ✗ (median −0.005) |
| 11 | **GBPUSD-1h** | 1h | **0.00441** | 0.0125 | **✗** | ✗ (median −0.052) |

The cells are EXIT-RCT (the only surviving exit; EXIT-ERT + the 4 conventional arms died at the EXP-091/094
screen and stay in the file drawer). EURUSD-1h and EURUSD-4h are **distinct strata** (each spends its own read).

## 2. Disclosure carried into interpretation (binding)

The smallest-defensible §8.3 sizing is superseded, **not** the per-cell honesty it encodes. The G-021
adjudication and EXP-093 `results.md` must carry, per stratum (LESSON-001):

- **GBPUSD-1h is carried despite being below its own EXP-093 margin on TRAIN** (`net_ci_low` 0.0044 < 0.0125,
  median −0.052; `clears_margin=false`). It is a **near-certain FAIL** by construction of the margin condition,
  and EXP-092 + the frozen D0 explicitly flagged it "should NOT be carried." The operator carries it for
  completeness of the TEST evidence base; its counted read (GBPUSD-1h 0→1) is **spent and permanent**
  regardless of outcome. A FAIL here is the expected result, not new information against the lever.
- **EURUSD-1h and NZDUSD-1h are mean-carried / median-negative on TRAIN** (clear margin on the binding mean
  gate, fail the co-reported median). The binding gate is the **mean** (D5); the median is the disclosed shape
  read. These two are weaker than the robust core (8) but margin-clearing.
- **The robust core (8)** — six 4h members + USTEC-1h + US2000-1h — are mean-AND-median-positive and
  margin-clearing on TRAIN; they remain the strongest evidence and the de-facto "smallest defensible" subset
  inside the carried 11. The G-021 TRADABLE verdict needs ≥1 carried cell to CONFIRM; the per-stratum table
  makes clear which cells carry the verdict.

## 3. Holm family re-sizing (amends §D6/4c)

The **phase Holm rule is sized to the carried-set cardinality = 11** (one-sided, α=0.05, Holm–Bonferroni over
the 11 carried cells' TEST p-values). The EXP-092 pinned `holm_rule` note ("sized to the EXP-093-carried
subset cardinality … selected at EXP-093 D0") is hereby resolved to **11**. The per-cell margin condition is
unchanged: PASS iff **Holm-adj p ≤ 0.05 AND `ci_low_1s` > margin** (margin = the cell's EXP-090/094 MDE: 1h
0.0125 / 4h 0.025 ATR). Carrying more cells **widens** the Holm family and is therefore the **conservative**
direction for false-positive control (it cannot make a true CONFIRM easier).

## 4. Counted-read / holdout accounting (amends §D7)

- **EXP-093 spends 11 counted TEST reads** — one per carried (instrument, domain) stratum, each **0→1** of the
  2-lifetime cap. All 11 carried strata are currently **0/2 open**; after EXP-093 each is **1/2** (one read
  preserved for any future confirmation). Recorded in `test-read-ledger.md` **in the same change** that records
  the EXP-093 result.
- The read is on the **analysis-TEST stratum** (last 30% of the first-70% analysis set, 1-minute-row timestamp
  boundary). The **final-30% global holdout is never loaded** (incl. its 1m bars) — a global-holdout release is
  a separate, later gate.
- **One stratum = one counted read** (§D7, `D0-amendment-001`): only EXIT-RCT survived, so each stratum is
  carried by exactly one (exit × cell) pair; no double-counting arises.
- **0 new candidate slots.**

## 5. What this amendment does NOT change

- The frozen entry (`RSI(2)` 2/10/90), EXIT-RCT target construction (D2.1), adverse side (2.0×ATR + MR-tempo
  cap, D2.3), the 1m intrabar fill engine (D2.5), the `D0-amendment-003` Phase-021 cost table (hash
  `fa7c887…`, F=0), the frozen referee suite (D4), the per-cell margins (D8/EXP-090/094 MDE), and the
  TRAIN-only-until-TEST / real-price / determinism discipline — **all unchanged**.
- The decision rule **mechanics** (D6/4c) are unchanged; only the **Holm family size** (→ 11) and the **carried
  set** (→ all 11) are fixed here.
- No new selection statistic is introduced ⇒ **no bite-check required** (the binding gate remains the existing
  frozen referee suite; EXP-093 reuses the EXP-090/092 substrate verbatim).
- The other deferred levers (15m capture, vol-regime, contrarian, 25/75, regime×variant cross-cuts, parameter
  tuning) **remain deferred**, each behind its own future `D0-amendment-*`.

---

*FROZEN — RATIFIED 2026-06-24 (operator-authorized). The §8.3 / §D6/4c / §D7 changes are reflected with a
back-pointer to this amendment; the 11 counted reads are entered in `test-read-ledger.md` in the same change
that records the EXP-093 result; the G-021 adjudication reads the 11 carried strata per the per-cell rule with
the §2 disclosures binding on interpretation.*
