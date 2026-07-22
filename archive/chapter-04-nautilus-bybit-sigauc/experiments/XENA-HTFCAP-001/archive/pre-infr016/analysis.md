# XENA-HTFCAP-001 — Informative results (EXPLORATORY, AMENDMENT-4/5)

**Run mode:** operator-authorized EXPLORATORY (TRAIN+TEST, no reserved OOS). **NOT a
certification, NOT a deployability claim.** Pin INFR-015 `abbb1842…` CLS-FILTER LOW-only
(verified). HOLDOUT (≥ 2025-01-08) sealed throughout. Recommended (non-final) verdict:
**NOT SUPPORTED (exploratory)** — operator decides follow-up.

## Headline
The pinned CLS-FILTER binder certifies **nothing real** on the BTC/SOL 4h/15m
HTF-interaction × capture-scale universe over the exploratory window. The certified top-1
**fails both** the embargoed stage-2 gross lower bound (strongly negative) **and** the HARD
leak tripwire. The search concentrates on the sparsest high-threshold corner (16h holds,
vol≥1.5, ADX≥25/30) — the design's predeclared-UNPOWERED stratum (§10) — with high in-search
score that collapses out-of-search-band.

## Integrity gates (all HARD checks)
| Gate | Result |
|---|---|
| Emission fence (strict, < holdout_start) | PASS 72/72 binding after boundary-mark trim (see §Provenance) |
| Estimand reconciliation (gate v2) | PASS 108/108; max abs 8.2e-12 bps; coverage BTC+ETH+SOL |
| Cadence coverage (LOW-only pin) | PASS — 108 emitted, 0 HIGH-shaped |
| Pin hash `abbb1842…` CLS-FILTER | PASS |
| §8 derangement leak tripwire (BTC top-1) | **FAIL — collapse 0.136 < 0.5 → REJECT-class** |

## Stage-2 (embargoed gate band, top-1 only — pin one_subset)
Top-1 = `BTCUSDT__DI_ADX_VOL_HI__v1.5__adx30__H64` (single cell).
- gross: point **−13.2 bps**, LCB **−123.2**, se **71.8**, n_legs **18** → `pass_positive=False`
- net:   point **−31.3 bps**, LCB **−140.5** → `pass_positive=False`
- 18 legs on the ~6-month gate band drives se 71.8 → the estimate is un-resolvable, and the
  point is negative regardless. `in_domain_16=True` (barely; floor is INFORMATIVE only, A5).

## Stage-1 search / ranking (evidence of overfit)
- 12 restarts, budget 200, 1747 evals, 10 distinct terminals. In-search F_hat 26.6–70.7
  (median 61.5).
- **Every finalist lives in H64 × vol≥1.5 × high-ADX** (the sparse corner). Ranking-fold
  `worst_F` is **negative for all 10 ranked** subsets (e.g. #1 median_F 33.4 / worst_F −35.3);
  fold Jaccard median 0.0 → unstable selection, no shared structure across folds.
- Classic pattern: high search F_hat → negative/near-zero on the embargoed band.

## Controls on finalists (informative attribution)
| Cell | n_legs (full) | raw med gross | sign-battery pct | ≥P95? | derangement collapse | HARD |
|---|---|---|---|---|---|---|
| BTC v1.5/adx30/H64 (top-1) | 119 | 1.03 bps | 0.64 | no | **0.136** | **FAIL (leak)** |
| BTC v1.5/adx25/H64 (#2) | 126 | 10.7 bps | 0.76 | no | 0.773 | pass |
| SOL v1.5/adxna/H64 | 192 | 24.9 bps | 0.80 | no | 0.824 | pass |

Reads: the **top-1's** ~1 bps edge **survives** destroying the HTF gate timing (collapse
0.14) → it is base drift, not HTF-attributable → leak/REJECT. The **higher-raw** cells' edges
**do** mostly collapse under derangement (0.77–0.82 → gate-attributable, not a leak) **but**
none reaches ≥P95 of the 25-seed Rademacher sign battery → direction content too weak to
distinguish from sign noise. So: the object with the largest raw edge is not what the
selection machinery certified; the certified object is the leak-class one.

## Per-candidate trade counts (§6 / AMENDMENT-5 informative)
Full TRAIN+TEST emission — every binding cell clears the informative 16-leg floor:
| Group | cells | legs min / p50 / max | below-floor |
|---|---|---|---|
| Binding (BTC+SOL) | 72 | 119 / 463 / 1857 | 0 |
| Disclosure (ETH) | 36 | 115 / 430 / 1578 | 0 |
| Binding H16 | 24 | 425 / 979 / 1857 | — |
| Binding H32 | 24 | 221 / 505 / 951 | — |
| Binding H64 | 24 | 119 / 267 / 497 | — |
Note the seam: cells are leg-rich over the full 2.46y emission, but the **embargoed gate band
alone** thins the certified H64 top-1 to **18 legs** → the negative stage-2 read is also thin.

## Costs / economics (informative)
- Pre-search gross floor (108-cell emission medians): binding median gross **2.77 bps/trade**
  vs measured breakeven ~13–15 bps; 13/72 binding cells ≥ breakeven, 59 sub-breakeven; entire
  mass NOT sub-breakeven → XENA-003 park not triggered, search proceeded.
- Net stage-2 LCB strongly negative (−140) — costs + funding bind hard at these hold lengths.

## ETH disclosure caveat (off the binding path)
12 ETH `v1.1` (loosest vol, highest cadence) cells fail the candidate gate's `oracle_smoke`
with a `NaN→int` numerical edge in the oracle's smoke eval. Estimand gate passed those same
cells (data is sound); ETH is disclosure-only and never entered the search. Reported, not
blocking. Worth a one-line fix in the oracle smoke path if ETH disclosure is ever centred.

## Provenance / boundary fix (holdout-adjacent, operator-approved option A)
The `--extend-test` emission ran one MTM mark too far — a single bar-mark per cell timestamped
exactly at holdout_start (2025-01-08). The strict candidate-gate fence (< AnalysisEndUtc)
rejected it; the estimand fence (inclusive) had passed it. Operator-approved trim removed that
one boundary mark from both emission layers (`xena/positions.parquet` + `bar_marks.parquet`),
touching **0 trades** and **0 data past the boundary** (receipt:
`results/boundary_trim_receipt.json`). Both gates re-run green; last emitted bar now
2025-01-07 23:59, strictly pre-holdout. Root cause fixed in `run_batch.py::_bands_for_window`
(TEST read now caps at holdout_start − 1 grain, mirroring the TRAIN/TEST boundary convention).

## Bottom line
No supported signal. The certified object is REJECT-class (embargoed gross LCB −123 + leak
tripwire 0.14); the search overfits the predeclared-UNPOWERED sparse corner; the strongest raw
cells fail the sign-battery bar. Informative only — no reserved OOS, no deployability. This is
experiment-level evidence; family CF-HTFCAP-001 status changes only at a checkpoint.
