# XENA-HTFCAP-001 — report (CF-HTFCAP-001, Bybit HTF-interaction filter × capture scale)

**Status:** COMPLETE 2026-07-19 · **Operator verdict: EXPLORATORY — real sub-cost gross edge, NOT deployable.**
**Lane:** XENA (default route) · **Family:** CF-HTFCAP-001 · **Pin:** INFR-015 `abbb1842…`
(CLS-FILTER, LOW-only certified) · **Gate slots spent: 1/2 (TEST band opened, exploratory).**
**Global 30% holdout (≥ 2025-01-08): SEALED throughout (never queried).**
**Run mode:** operator-authorized EXPLORATORY (AMENDMENT-4/5) — TRAIN+TEST window, **no reserved
OOS**. This is therefore **not a certification and not a deployability claim**; results are
informative-only and the operator decides what advances.
**Analysis framework:** re-done under INFR-016 report layers (value/quality/significance reads are
`observed/ideal/interpretation` layers, no pass/fail gates). Prior gate-framed analysis archived
at `archive/pre-infr016/`.

## Research question
Under the pinned cost-aware CLS-FILTER binder (stage-1 net search → stage-2 gross leg-studentized
LCB on an embargoed band), does a portfolio drawn from the HTF-interaction-filter × hold-scale
universe on BTC/SOL 4h/15m carry a per-leg edge that survives cost, where the calibrated
false-pass rate is α̂ ≈ 4.5% (LOW cadence)?

**Mechanism.** A confirmed 4h HTF state — DI-direction continuation gated by high relative
volatility (`vol_ratio = ATR(14)[t−1] / median(ATR14, W=100 HTF bars) ≥ thr`), optionally
ADX-strength-gated — is hypothesised to raise the conditional gross bps/trade of otherwise-
unconditioned 15m entries, with capture scaling in hold length. P&L object = the individual
directional **leg** (market-on-open entry at gate-ON confirmed ≤ t−1, fixed hold H ∈ {16,32,64}
15m bars, market-on-open exit). LOW cadence (holds 4–16h).

## Run history — why this run is exploratory
QA run 4 APPROVE, then the majors' TRAIN-only window (~1.4y) fell below the LOW leg-count floor
(100% out-of-domain re-CAL probe). The operator authorized (AMENDMENT-4/5) a **TRAIN+TEST window**
(2022-07-14 → 2025-01-08 = holdout_start; ~2.46y) and demoted the leg-count floor to informative.
Because that consumes the TEST band with **no reserved out-of-sample left**, the run cannot
certify or claim deployability — it is an honest in-sample characterisation. HOLDOUT self-test
PASS; holdout never touched.

## Scope + exclusions
- **Binding instruments:** BTC + SOL (SPDR-006 §10 caveat 2 evidence-scope supersedes the
  ckpt-013 online-10 rule for this universe). **ETH disclosure-only** — 12 `v1.1` ETH cells fail
  the candidate gate's `oracle_smoke` (`NaN→int` on the densest streams; data sound per estimand
  gate) and never entered search or stage-2.
- 72 binding cells; embargoed stage-2 gate band 2024-07-10 → 2025-01-08.
- No limit entries anywhere (`limit_entry_cells=false`, matches pin; L-27 confound not in play).

## Method
NautilusTrader BacktestNode emission (contract v1) per candidate under the pinned catalog fence;
emission REUSED across every analysis layer (engine runs only at emission; each layer reads the
emitted parquet). Pinned two-stage CLS-FILTER binder: LAHC search (12 restarts, 1747 evals) on the
net-search band → `certify_and_rank` on ranking folds → pinned stage-2 studentized leg-bootstrap
gross LCB on the embargoed band. Sign battery + attribution derangement are analyst-owned
(`analysis_code/`). Costs analyst-injected (taker + conservative 5 bps GAP spread + funding).

## Data-validity attestations (HARD — all PASS on the reused emission)
A failure here means *fix the emission*, not *no edge*.

| Attestation | Result |
|---|---|
| Estimand reconciliation (gate v2) | **PASS** 108/108; max abs 8.2e-12 bps; coverage BTC+ETH+SOL |
| Emission fence (strict, < holdout_start) | PASS 72/72 binding after boundary-mark trim |
| Boundary-mark trim (holdout-adjacent) | receipt `boundary_trim_receipt.json`; last bar 2025-01-07 23:59; 0 trades / 0 data past boundary |
| Cadence coverage (LOW-only pin) | PASS — 108 emitted, 0 HIGH-shaped |
| Pin hash `abbb1842…` CLS-FILTER | PASS |
| Causal ≤ t−1 / non-STUB fence | PASS (design §14, gate v2) |
| Holdout sealed | PASS — self-test clean; no holdout path |

The design §8 gate-schedule derangement is a **within-sample attribution** control (entries stay
causal ≤ t−1); under INFR-016 §4c it is a report layer, not a hard leak gate. No `future_destroy`
control applies (this is timing/alignment attribution, not a leak surface).

## Key quantitative evidence (report layers)

**What the retired gates had hidden.** The archived read reported one certified object (binder
top-1) and called the family NOT SUPPORTED / leak-class. Retiring three value gates changes two
of those conclusions:

1. **Top-1 hiding (`one_subset`) → all 72 cells reported.** The binder's `g_net` top-1 landed on
   the **worst** cell (`v1.5/adx30/H64`, embargoed gross LCB −123). Reporting every cell surfaces
   **5 cells with a positive embargoed gross LCB**, the strongest of which also clear the sign
   null and are gate-attributable.
2. **Leak boolean (`hard_fail_leak`) → reported fraction.** The "top-1 leak, collapse 0.14" was a
   near-zero-denominator artifact — that cell's raw edge is ~1 bps (sign p 0.44 = pure noise), so
   `1 − deranged/raw` is undefined-noisy. Nothing to attribute → not a leak, just no edge.
3. **Sign boolean (`at_or_above_p95`) → 2000-seed p + CI.** 20/72 cells sit at one-sided sign
   p ≤ 0.15; the strongest at p 0.017–0.043. The 25-seed P95 bar had mislabelled these "fail".

**Layer 4 — stage-2 bounds, embargoed band. Cells with positive GROSS LCB (5 of 72):**

| Cell | gross point | gross LCB | net point | **net LCB** | n_legs |
|---|---|---|---|---|---|
| BTC DI_ADX·VOL v1.25/adx25/H64 | 99.6 | **+17.5** | 81.8 | **−4.6** | 34 |
| BTC DI_ADX·VOL v1.1/adx25/H64 | 58.0 | **+9.5** | 39.9 | −7.0 | 65 |
| BTC DI_ADX·VOL v1.25/adx25/H32 | 42.8 | **+7.8** | 26.0 | −17.8 | 64 |
| BTC DI_ADX·VOL v1.1/adx20/H64 | 51.4 | **+3.7** | 33.6 | −12.3 | 78 |
| BTC DI·VOL v1.1/adxna/H64 | 42.9 | **+1.5** | 24.9 | −15.7 | 89 |

**The binding read — net-of-cost:** ZERO cells and ZERO subsets have net LCB > 0. Best net point
+81.8 (v1.25/adx25/H64), but its net LCB is −4.6 — closest to zero, still below. The binder's
certified top-1 `v1.5/adx30/H64` is the *worst* corner (gross point −13.2, LCB −123.2, net LCB
−140.5), not representative.

**Layer 5a — sign battery (2000-seed Rademacher, one-sided p):**

| Cell | raw med gross | one-sided p |
|---|---|---|
| BTC DI_ADX·VOL v1.25/adx25/H32 | 10.8 | **0.017** |
| BTC DI_ADX·VOL v1.25/adx25/H64 | 22.2 | **0.043** |
| BTC DI_ADX·VOL v1.1/adx25/H64 | 9.7 | 0.179 |
| SOL DI·VOL v1.5/adxna/H64 | 24.9 | 0.224 |
| BTC DI_ADX·VOL v1.5/adx25/H64 (#2) | 10.7 | 0.232 |
| BTC DI_ADX·VOL v1.5/adx30/H64 (top-1) | 1.0 | 0.441 |

The two BTC `adx25` H32/H64 cells sit at p 0.017–0.043 — real directional content. Labels are
**structural only** (UNPOWERED / CONTRADICTED / —); the number is the read, not a cutpoint word
(INFR-016 follow-up 2026-07-19: a hardcoded-p label re-imports the L-32 threshold trap in
miniature). 23/72 cells are CONTRADICTED (wrong-sign raw); the remaining 49 are positive-sign.

**Layer 5b — attribution derangement (collapse fraction, L-28 zero-fixed-point, 25-seed):** for
cells with a real raw edge, collapse is high (edge IS the gate construction, not base drift):
BTC v1.25/adx25/H64 0.96 [0.54–1.49]; v1.25/adx25/H32 0.92 [0.43–1.31]; v1.1/adx25/H64 0.87
[0.20–1.47]. The top-1's collapse 0.90 has band ±16 (raw ≈ 1 bps → meaningless), which is where
the old "leak 0.14" number came from.

**Evidence for / against (summary).**
- **For (gross, in-sample):** a real, gate-attributable, sign-null-clearing GROSS edge exists on
  BTC mid-threshold `DI_ADX×VOL_HI adx25` H32/H64 holds — embargoed gross LCB +8 to +18, sign
  p 0.02–0.05, derangement collapse ~0.9. This is a genuine finding the old top-1 framing hid.
- **Against (deployability):** net-of-cost, no cell and no subset resolves above zero. The
  gross→net gap is ~18 bps/round-trip (taker + GAP + funding), and funding is the dominant slice
  at 8–16h holds. Ranking-fold `worst_F` is negative for all 10 finalists, fold Jaccard median 0.0
  → unstable selection (overfit signature). SOL v1.5/adxna/H64 looked suggestive on the full
  window (24.9 bps, p 0.224) but is strongly negative on the embargoed band (gross point −154) —
  its edge does not transfer.

## Analyst recommendation vs operator verdict
- **Analyst recommended (non-final):** exploratory, in-sample, NOT deployable — a real directional
  BTC edge too small to beat cost at these holds; not "dead", not "deployable".
- **Operator verdict (final, verbatim intent):** **EXPLORATORY — accept the characterisation.**
  The HTF-interaction filter carries a real directional edge on BTC that does not survive cost at
  8–16h holds. No certification, no deployability, no family status change here (that is the
  checkpoint-013 retrospective).

## Follow-up recommendations (each a NEW design, not this run)
- **Lower-cost capture:** maker entries or shorter-cost venues, where the ~18 bps cost wall shrinks
  and a +10–18 bps gross edge could clear.
- **Denser-cadence variants:** a smaller edge that compounds over more legs; requires re-CAL on a
  HIGH-cadence pin (current pin is LOW-only certified).
- Both are new registered designs; neither reuses this exploratory TEST spend.

## Artifacts
- Design: [`design.md`](design.md) · QA: [`qa-review.md`](qa-review.md) · Analysis:
  [`analysis.md`](analysis.md) (archived gate-framed read: `archive/pre-infr016/`)
- Results: [`results/layer_reports.json`](results/layer_reports.json),
  [`results/layer_tables.md`](results/layer_tables.md),
  [`results/estimand_validation.json`](results/estimand_validation.json),
  [`results/boundary_trim_receipt.json`](results/boundary_trim_receipt.json)
- Code: [`code/`](code/) · Analysis code: [`analysis_code/`](analysis_code/)
- **Raw emission removed post-analysis (2026-07-19, disk cleanup, 4.6G):**
  `data/nautilus_runs/XENA-HTFCAP-001/` deleted after the analysis completed — matches the
  EPSOSC precedent. The full record (estimand + per-cell fence/provenance, layer reports/tables)
  is preserved in `results/`; the emission is deterministically regenerable from the pinned
  catalog + `code/` if ever needed.

## Signal-registry disposition (evidence rows only)
- `multiplicity-registry.md` (Chapter 04, CF-HTFCAP-001): append this experiment's outcome —
  EXPLORATORY, real sub-cost gross BTC edge, not deployable.
- `test-read-ledger.md`: 1 TEST-band read recorded (exploratory, no certification), holdout sealed.
- `candidate-families/cf-htfcap-001.md`: append evidence row; **status field untouched**.
- `xena-runs.md`: XENA-HTFCAP-001 row already carries the outcome (1/2 slots, exploratory).
- **Family status transition (open/RETIRED) is deferred to the checkpoint-013 retrospective,
  operator-signed — not performed here.**
