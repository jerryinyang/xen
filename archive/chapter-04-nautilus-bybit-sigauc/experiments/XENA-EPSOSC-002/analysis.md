# XENA-EPSOSC-002 — analysis (data-analyst, non-final)

**Hypothesis (design §1).** With the search band aligned to the VOLARM mass and the grid
restricted to endogenous-clear (RET_ANCHOR), does a **cross-symbol** portfolio (K≥3, pooled
n_legs ≥ 16) certify under the pinned CLS-EPISODE binder (stage-2 gross LCB > 0), AND does its
edge survive the derangement tripwire **after** the directional-drift pedestal is subtracted?

**Recommended verdict: NOT SUPPORTED (refuted on both legs).** The certified cross-symbol
subset fails the pin's stage-2 gross LCB gate (−68 bps) and fails the derangement tripwire
(raw collapse 0.09, drift-adjusted 0.14). Residual positive gross is **AKRO-concentrated
unconditional drift — the exact 001 failure mode**, not a signal-conditioned reversion.

---

## Phase 0 — Integrity gate (blocking)

| Check | Result | Evidence |
|---|---|---|
| Estimand gate v2 | **PASS** | `results/estimand_validation.json` `blocking_pass:true`; 152/152 cells pass; 19 symbols × 8; 13 physicality flags (informative) |
| Provenance ≤ t−1 | **PASS** | strategy arms on confirmed LTF ≤ t−1; entry at next-bar RealOpen; membership at daily 00:00 rebalance ≤ open (`code/epsosc_strategy.py:163-172,229-251`, byte-identical reuse of 001, QA-approved) |
| Leak tripwire non-vacuous | **PASS (non-vacuous)** | derangement moves the mean (design §8); drift-twin pair added (§7). See below — the certified subset's edge does NOT survive → REJECT-class, not a surviving leak |
| Holdout sealed | **PASS** | window [2022-07-01, 2023-12-18]; `train_end` < holdout_start 2025-01-08; no holdout path |
| Price-primary | **PASS** | Nautilus BacktestNode emission under catalog fence (`fence_attestation.json`), non-STUB |
| Shared-code boundary | **PASS** | `check_no_local_accounting("…/002/code")` → `{ok:true}` |

Integrity clean. Everything below is evidence for the operator, not a gate.

## Phase 1 — Question list (answered)

1. Does the certified subset clear the pinned stage-2 gross LCB? → **No, −68 bps.**
2. Is the pooled gross positive at all, or an artifact of one symbol? → **Positive pooled naive
   mean but AKRO-concentrated; 2 of 4 symbols dead/negative.**
3. Does the edge collapse under derangement (signal-conditioned)? → **No — 0.09 raw collapse.**
4. Is the edge just unconditional drift? → **Largely yes — drift-adjusted collapse 0.14; live <
   drift-twin P95.**
5. Did AMENDMENT-1 (K≥3) do its job vs 001's concentration defect? → **Yes — it excluded the two
   higher-ranked 2-symbol finalists; but the admissible 4-symbol object still fails.**
6. Was the search powered / non-degenerate? → **Yes — eval_count 1898, 12 distinct restart
   terminals, 62 gate-band legs ≥ F*16.**

## Phase 2 — Interrogation (canonical, xen-only)

Verdict-bearing gross = canonical adjudication-shim episode gross (`RealizedBps`), reconciliation
validated by the estimand gate. Analyst code: `analysis_code/{canonical_reads,tripwire_drift_twin}.py`.

### Search / certify evidence package (interrogated, not certified)
- eval_count **1898**, distinct_restart_terminals **12/12** (no restart degeneracy).
- Raw ranked top-1 = **2-symbol** (1000BONK×2 + AKRO), medianF 58.5 → **excluded by AMENDMENT-1**.
  Rank-1 = 2-symbol (AKRO+LEVER) medianF −23 → excluded. **AMENDMENT-1 removed exactly the
  concentrated bets it was designed to (design §4.3).**
- **Certified (rank-2, 4 distinct symbols):** `10000LADYS_L, AKRO_S, LEVER_L, STMX_S`.

### Certified subset — stage-2 gate band (canonical)
| Read | Value |
|---|---|
| Pin stage-2 **gross LCB** (studentized, `episode_overlap_rule_v1`) | **−68.2 → FAIL (>0 required)** |
| Pin stage-2 net LCB | −102.1 |
| n_legs | 62 (≥ F*16, in-domain) |
| Naive pooled mean (block-bootstrap, block 64, 5-seed) | 94.5 bps, CI95 **[68.3, 116.4]** (excludes 0) |

**The two CIs disagree, and the disagreement is the finding.** The naive equal-weight block
bootstrap ignores episode-overlap correlation and cross-symbol concentration; the pin's
overlap-aware studentized LCB (the certification-relevant interval) is **negative**. Per-symbol
shows why:

### Per-symbol gate-band gross (canonical, block-bootstrap CI95)
| Symbol | n | mean bps | CI95 | read |
|---|---|---|---|---|
| AKROUSDT (S) | 10 | **450.1** | [372.8, 534.2] | dominates the pool — 001's pedestal symbol again |
| 10000LADYS (L) | 16 | 171.1 | [34.1, 308.1] | positive |
| LEVERUSDT (L) | 13 | 0.6 | [−83.2, 81.5] | null |
| STMXUSDT (S) | 23 | −60.2 | [−130.0, 10.6] | negative |

The "cross-symbol" pooled positive is **AKRO drift + one positive name, diluted by two dead
names**. Half the subset (LEVER, STMX; 36 of 62 legs) carries no edge.

### Tripwire + drift-twin (200 derangement + 200×2 twin seeds; `derangement_tripwire.json`)
Certified subset:
| Quantity | Value | Rule | Result |
|---|---|---|---|
| live mean gross | 95.0 bps | — | — |
| deranged median (arm-time permute) | 86.3 | — | — |
| **raw collapse** | **0.091** | ≥ 0.5 | **FAIL** |
| matched-drift twin median (random entry times) | 31.2 | — | — |
| **drift-adjusted collapse** | **0.135** | ≥ 0.5 | **FAIL** |
| coin-flip twin median (E[gross]=0 null) | 8.5 | ≈ 0 | ok (null behaves) |
| bite: live > P95 of both twins | 95 < drift-P95 **131.5** | — | **no** |
| L-29 anchor | clean | — | ok |
| **HARD pass (raw AND drift-adj ≥ 0.5)** | — | — | **REJECT-class** |

**Mechanism read.** Deranging *among the actual arm timestamps* barely moves the mean (86 vs
95), but sampling *uniformly random* entry times drops it to 31. So the "edge" lives in **when
the arms cluster (volatile windows)**, not in the arm→reversion *alignment*. That is a
volatility-clustered drift artifact, not a within-episode signal-conditioned reversion. The
drift-adjusted signal (63.7 bps above the random-time twin) also fails to collapse under
derangement and does not clear the drift-twin's own P95 → no signal survives subtraction.

## Phase 3 — Evidence assembly

### Evidence FOR the hypothesis
- Pooled naive mean +94.5 bps, block-bootstrap CI95 excludes zero; 62 legs ≥ F*16 (powered).
- Two of four symbols individually positive (AKRO 450, 10000LADYS 171).
- Coin-flip null twin centers ~0 (8.5 bps) → the machinery is non-vacuous; a real signal *could*
  have shown.
- AMENDMENT-1 worked: search was well-formed (1898 evals, 12 distinct terminals), and the
  concentrated 2-symbol finalists were correctly demoted to disclosure.

### Evidence AGAINST the hypothesis (decisive)
- **Pin stage-2 gross LCB −68 → does not certify** (the pre-registered e2e pass event).
- **Derangement collapse 0.091 and drift-adjusted 0.135**, both far below the 0.5 HARD floor →
  the edge is not signal-conditioned; it is arm-time clustering / unconditional drift.
- **AKRO concentration reproduced from 001**: AKRO (10 legs, 450 bps) carries the pooled mean;
  STMX −60 and LEVER ~0 contribute nothing. The redesign's cross-symbol requirement did not
  break the drift pedestal — it diluted it.
- Live 95 < matched-drift twin P95 131.5 → the live read is *below* what random-timed entries in
  the same symbols/side/durations produce 5% of the time. No bite.

### Anomalies / open questions
- STMX is net negative (−60) yet was selected into the top subset — the search maximises the
  pooled/portfolio functional, tolerating a negative constituent when AKRO carries the pool.
  Consistent with a concentration artifact, not a portfolio edge.
- Naive-vs-overlap-aware CI gap (positive vs negative LCB) is a reusable caution: equal-weight
  block bootstrap is over-optimistic on concentrated, overlapping cross-symbol subsets.

### Recommended verdict — NOT SUPPORTED (experiment hypothesis only)
Three drivers: (1) pinned stage-2 gross LCB negative (−68); (2) derangement raw + drift-adjusted
collapse both < 0.15 (edge not signal-conditioned); (3) per-symbol AKRO concentration reproduces
001's pedestal — residual gross is unconditional drift, not within-episode reversion.

**What would change it:** a certified subset with (a) positive overlap-aware stage-2 gross LCB,
(b) derangement collapse ≥ 0.5, and (c) live above both twins' P95 — none of which any admissible
subset here shows. No further probe on this emission is likely to reverse the reading; the signal
is absent, not merely underpowered (62 legs, MDE ~38 bps « the 95 bps read, yet it fails).

**Final verdict is the operator's.** Suggested probes if you want to push: (i) inspect the
disclosure 2-symbol finalists' collapse (all < 0.5 too — `derangement_tripwire.json`); (ii)
confirm AKRO's 450 bps is the same 2023 downtrend drift flagged in 001 (per-episode sign/dir).
