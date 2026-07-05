# EXP-016 — CF-MR-005 one-shot TEST persistence read: PERFORMANCE RETAINED; two harness flaws exposed

**Family:** CF-MR-005 · **Type:** counted TEST-stratum confirmation, price-primary (native
cTrader, m1 fills) · **Date:** 2026-07-03 · **Operator-directed** (retire ratification made
contingent on this read).
**Outcome: PERFORMANCE_RETAINED (numerically, all 3 cells; formally UNPOWERED under the frozen
referee — and that formal result is itself the finding: the referee cannot adjudicate a
9-month band). Family stays OPEN; routing = operator discussion.**
**Reads:** 3 counted TEST reads spent (AUDUSD-4h, NZDUSD-4h, US2000-4h → each 1/2), entered in
`test-read-ledger.md` **before** result contact. Holdout (final 30%) untouched. Referee untuned.

Artifacts: [design.md](design.md) (frozen §4 criteria pre-execution) ·
[code/adjudicate.py](code/adjudicate.py) · [results/test_read.json](results/test_read.json) ·
emissions `data/strategy_runs/EXP-016-4h-s8-e3-extend-z15[-shift]/`.

## 1. Setup (all frozen before execution)

Variant prespecified from TRAIN: **e3/extend/z15** (unique config where all three cells
Holm-admitted in EXP-014c). Same C# model byte-identical; only conf fences extended to the 70%
cutoff. TEST band = rows 49%→70% of the 20230103-era dataset (≈ 2024-09 → 2025-05/06, ~1,110
4h bars/cell) — never touched by any CF-MR-004/005 experiment. 6 native runs (3 raw + 3
phase-shift twins; twins predeclared as collapse-fraction disclosure, not a binary gate —
L-15/W3: the own-price thesis *expects* shift survival).

**Validation:** the TRAIN-band legs of these fresh runs reproduce EXP-014c exactly —
AUDUSD 3.98, NZDUSD 4.00, US2000 10.90 net bps/active-bar — same strategy, same fences,
deterministic replay. The TEST read sits on a verified base.

## 2. Result — the edge is bigger out-of-TRAIN

| Cell | TRAIN net | **TEST net** | TEST ci_low | epi | boot_p | Holm(3) | shift collapse (TEST) |
|---|---|---|---|---|---|---|---|
| AUDUSD | 3.98 | **+5.50** | −0.64 | 5 | 0.066 | ✗ | 0.94 |
| NZDUSD | 4.00 | **+4.68** | +0.59 | 7 | 0.0064 | ✓ | 1.06 |
| US2000 | 10.90 | **+11.83** | **+5.33** | 20 | **0.0001** | ✓ | 0.56 |

- Every cell's TEST net **exceeds** its TRAIN net. US2000: ci_low +5.33, 20 episodes,
  boot_p 0.0001, 262 trades in-band.
- Holm over the 3 bootstrap p-values: US2000 + NZDUSD significant; AUDUSD narrowly not
  (p 0.066, 5 episodes).
- Shift attribution unchanged from TRAIN: AUDUSD/NZDUSD ≈ fully own-price (0.94/1.06);
  US2000 again ~half basket-linked (0.56).
- Carryover legs at band start: 0–3/cell (disclosed; negligible).

## 3. Finding A — frozen-referee flaw: L1 readiness veto is band-length-blind

The formal referee verdict on all three cells is UNPOWERED/REJECT. Leg forensics (US2000,
strongest cell): **L3 outcome PASS, L5 materiality PASS (pooled), ci_low +5.33 — the sole
failing leg is `L1_readiness: false`** (effective_n 333 vs a floor calibrated on full ~3.2-year
samples). A ~1,110-bar band **cannot satisfy L1 at any edge size** — the +8 bps bite plant
fails the same leg, i.e. the gate is *provably blind* on this band, so its negative carries no
evidential weight (bite-vacuous by its own standard). This is the known L-12 §2 failure mode
(L1 readiness veto, edge-independent) surfacing in a new place: **TEST-band adjudication**.
Any confirmation read on a ~21%-of-data band needs a band-length-aware readiness rule or a
predeclared episode-native instrument, frozen candidate-blind — the current frozen referee
structurally cannot say yes OR no there. → **KB lesson L-17.**

## 4. Finding B — evaluation-object flaw: EXP-015 characterised the wrong object

EXP-015 concluded NO_MECHANISM_EVIDENCE from single-event dislocation recovery (dislocated
bars don't out-revert matched bars — that measurement stands; independently re-verified under
the control-free symmetric read). EXP-016 shows the P&L object nonetheless **reproduces
out-of-TRAIN with a stronger mean**. Both facts hold simultaneously because they describe
different objects: EXP-015's estimand was **per-event** recovery; the field P&L is a
**multi-leg episode object** (EXP-015 Part A itself: ~68% of net accrues with ≥2 legs open;
per-leg P&L fattens with add depth). A single-entry estimand is structurally deaf to a
structure-borne P&L — the mechanism question for this family is *unanswered*, not answered in
the negative. EXP-015's "retire" recommendation is **withdrawn as over-reaching its
instrument**; its factual reads (event scarcity at depth, per-event non-reversion, tail
census) all stand. → **KB lesson L-16** (a characterisation estimand must match the
P&L-bearing object, or its null is object-mismatch, not absence — the L-13 vehicle-fit lesson
extended from *evaluation* vehicles to *characterisation* estimands).

## 5. Honest caveats

- One 9-month window, one regime; the M4 tail population (deep-episode dependence, 40–85%
  bin-4 non-recovery) is untested by a band this short — persistence here does not price the
  tail.
- AUDUSD individually not significant; the "all three retained" statement is point-estimate,
  Holm-backed only for US2000/NZDUSD.
- US2000 remains half basket-linked under shift (0.56) — its attribution is still mixed.
- No formal referee admit exists (Finding A); "retained" rests on frozen-seed bootstrap
  p-values + ci_low, predeclared in design §4 before result contact.
- Second TEST read per stratum (cap 2) is now the last; it must be reserved for a final
  confirmation under a repaired instrument.

## 6. Dispositions

- **CF-MR-005: OPEN** (retire ratification withdrawn by operator fork: performance retained ⇒
  harness at fault). EXP-015's verdict re-labelled: NO_MECHANISM_EVIDENCE **for the per-event
  object**; family mechanism question open (multi-leg object uncharacterised).
- Registry: HYP-001 row annotated; EXP-016 recorded; 3 counted reads in the ledger (pre-result).
- KB: **L-16** (characterisation-object match) + **L-17** (referee band-length blindness) filed.
- Routing (pending operator discussion): candidate next scopes = (a) episode-native mechanism
  probe of the multi-leg object; (b) short-band-capable confirmation instrument, predeclared +
  frozen candidate-blind, before any second (final) TEST read.

## GATE: APPROVE (orchestrator inline post-exec, 2026-07-03)

Operator-directed spend; variant/cells prespecified from TRAIN; criteria frozen pre-execution;
ledger entries preceded result contact ✓. TRAIN reproduction exact (3/3) — execution verified ✓.
Leg-level forensics performed (L1 isolated as sole blocker; bite shown vacuous on-band) ✓.
Shift twins run, collapse fractions disclosed (no binary read) ✓. Holdout sealed; referee
untuned (its inadequacy documented, not patched in-run) ✓. Findings A/B filed as KB lessons;
family status + registry updated ✓. **One-shot honored: no re-runs after result contact.**
