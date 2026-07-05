# EXP-016 — CF-MR-005 one-shot TEST persistence read (operator-directed)

**Type:** counted TEST-stratum confirmation, **price-primary** (native cTrader orders, m1
fills). **Operator decision (2026-07-03):** ratification of CF-MR-005 retire is made contingent
on an out-of-TRAIN persistence read of the three passing field cells. **3 counted TEST reads
spent** (one per stratum: AUDUSD-4h, NZDUSD-4h, US2000-4h) — entered in
`docs/signal-registry/test-read-ledger.md` **before** any result is read. Holdout (final 30%)
untouched. Frozen referee untuned (L-12).

## 1. Question (one-shot, frozen before execution)

Does the engine-realized net edge of the selected TRAIN-passing variant — **e3 / extend / z\*1.5**
(frozen bracket TP@anchor + outward SL + ⌈3·HL⌉ time-stop; extend ladder {1.5, 2.0, 2.5}) — on
S8_RVINDEX at 4h **persist in the TEST band** (rows 49%→70% of the 20230103-era dataset;
never touched by any CF-MR-004/005 experiment) for US2000, AUDUSD, NZDUSD?

## 2. Variant selection (prespecified from TRAIN, no new search)

(e3, extend, z15) is the unique config where all three cells Holm-admitted on TRAIN
(EXP-014c: US2000 10.90/ci 3.17; NZDUSD 4.00/1.53; AUDUSD 3.98/1.06). One variant, three
prespecified cells, no in-run selection.

## 3. Execution

- **Same C# strategy, byte-identical model path** (`Xen.cs` CrossInstrumentSpreadMr,
  `--CisExitSet=bracket --CisReentry=extend --CisZStar=1.5`, same basket mates) — no code
  changes; only the conf's `ANALYSIS_END`/`BACKTEST_END` extend to the **70% fence**:
  AUDUSD 2025-05-29T14:08Z · NZDUSD 2025-05-29T05:14Z · US2000 2025-06-02T07:30Z
  (= `int(N*0.7)` row CloseTime of the 20230103-era files; 49% fences reproduce EXP-013
  verbatim — verified).
- Runs: 3 cells raw + 3 phase-shift twins (`BasketPhaseShiftHours=60`) = 6 native runs.
- Emissions: `data/strategy_runs/EXP-016-4h-s8-e3-extend-z15[-shift]/`.

## 4. Adjudication (frozen)

- **TEST-band series:** per-bar engine-realized NET (audited `assemble_realized_bps`, frozen
  cost map, MTM L-09, cost once/entry L-02) restricted to bars with
  `train_fence < SourceCloseTime ≤ test_fence`. Legs entered before the band contribute MTM
  without entry cost (carryover count disclosed).
- **Binding:** frozen 4h referee (`gate_stack_pstar`, q\*=0.75, seed 20260703) on the TEST-band
  series per cell; **Holm over the 3 cells**; bite (+8 bps plant) per cell.
- **Verdicts per cell:** RETAINED = referee net admit (Holm) & bite-valid. NOT_RETAINED =
  powered + bite-valid + no admit. UNPOWERED = episodes < 8 or bite-blind (no verdict; band is
  ~21% of data — power risk disclosed upfront).
- **Family routing (operator pre-commitment):** all three NOT_RETAINED → **retire CF-MR-005
  immediately**. Any RETAINED → the TRAIN evaluation harness (not the strategy) becomes the
  suspect — route to a harness forensics scope before any further family action. Mixed/
  UNPOWERED → operator.
- **Phase-shift twins = disclosure, not a binding gate** (predeclared): under the own-price
  thesis the basket shift is *expected* to be survived, so a binary REJECT_LEAK read is the
  wrong instrument here (EXP-014c W3 / L-15); **collapse fractions disclosed per cell**.
- TRAIN-band figures from the same runs are reproduction checks only (must ≈ EXP-014c; any
  material mismatch is a Critical).

## 5. Discipline

3 counted TEST reads (cap 2/stratum lifetime: these are read #1 for each of the three 4h
strata on the active INFR-003 ledger). Final-30% holdout sealed — the 70% fence is asserted
per cell (`HoldoutFence.AssertCanEmit` + analysis assert). No parameter changes, no new
search, no exit edits (P-02). One-shot: no re-runs after seeing TEST results.

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-03) — operator-directed spend;
variant + cells prespecified from TRAIN; criteria frozen above before execution; ledger
entry precedes result contact; holdout untouched; referee untuned.
