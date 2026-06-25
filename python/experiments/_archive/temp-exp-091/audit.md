# Audit Report: Experiment EXP-091

**Phase 021 (CF-MR-001 batch 2) · RSI-2 fade exit / capture-geometry screen · HYP-002.**
Auditor: research-pipeline consolidated Stage-5 audit · Date 2026-06-24. Numeric re-derivation run
independently on `results/*.csv` (not read off `run_metadata.json`).

## Summary

- **Verdict**: PASS (implementation trustworthy; mechanical screen verdict reproduces exactly; mechanism explained)
- **Critical Issues**: 0
- **Warnings**: 3 (all interpretive context for Stage 6 — each shown **not** to move the mechanical screen verdict)
- **Info Notes**: 3

The frozen D6 screen verdict reproduces: **RCT PASSES** (net-clears 5 cells / 5 instruments ≥ the 5/3 quorum);
the other five arms net-clear in **0** cells. `experiment_verdict = SCREEN_DELIVERED`. This is correct and
re-derivable from the raw per-cell net lower bounds. The audit's substantive content is the **verdict forensics**:
the pass is genuine but domain-conditional, boundary-fragile, and mean/tail-carried — context that is binding on
interpretation and the EXP-092 hand-off, and which the auditor confirms does not change the mechanical count.

## Code Review

| File | Check | Verdict | Notes |
|------|-------|---------|-------|
| `code/run_experiment.py` | Correctness | PASS | Net-clear `net_ci_low>0` reproduces written `net_clear` on all 120 (cell×arm) rows (0 mismatches). |
| `code/run_experiment.py` | Cost identity | PASS | `net_mean == gross_mean − cost_txn_mean` to 2.2e-16 on every row; `cost_fin_mean == 0` everywhere (F=0, D0-amendment-003). |
| `code/run_experiment.py` | Edge cases | PASS | `keep` mask drops non-finite / `atr≤0` / `hd<0`; `n_resolved<2 ⇒ _empty_arm_result` (denominators shown, never a net-clear, no `0/0`). Min `n_resolved`=3835; resolution 0.9943–0.9996 — no thin-cell power risk. |
| `code/run_experiment.py` | Type safety / docstrings | PASS | Typed public fns; `ArmResult` frozen dataclass; docstrings present. |
| `code/run_experiment.py` | NaN handling | PASS | `tie_break_frac=NaN` appears **only** on PARTIAL-TRAIL (20/20) — correct: the bar-level resolver has no 1m tie-break notion (disclosed). All engine arms finite. |
| `code/run_experiment.py` | Holdout exclusion | PASS | TRAIN sub-split inherited verbatim via `E90.load_train_1m` (`int(int(total·0.7)·0.7)`); `build_cell_context`/`resolve_arm` reused unchanged from validated EXP-090; 1m walk clips at TRAIN edge in the reused engine. No analysis-TEST or final-30% path. |
| `code/run_experiment.py` | Real-price discipline | PASS | Gross = signed `(fill_price − ctx.close[idx])/atr` on real touched fill levels + real ATR; cost in ATR units. No HA/Renko synthetic price. (`net_return_atr` is mis-named — it computes the *gross* signed return — inherited from EXP-090; cosmetic, see Info-2.) |
| `code/run_experiment.py` | Timestamp alignment | PASS | Domain↔1m mapping by timestamp inside the reused engine; no bar-index alignment introduced here. |
| `code/run_experiment.py` | Verdict representation (per-stratum) | PASS | Binding figure written per (cell×arm) (`net_clear`); experiment verdict is the predeclared D6 **count** over per-stratum clears, not a collapsed `.all()`. Per-stratum doctrine (LESSON-001) honoured. |
| `code/run_experiment.py` | Safe optimization / progress | PASS | Bootstrap via frozen `xen.ass`; causal 1m walk kept sequential in reused engine; `tqdm` over 20-cell loop; helpers return data. |
| `code/run_experiment.py` | Import side effects / plot reuse | PASS | Dirs made in `run()`; `matplotlib Agg`; plots built from collected `ArmResult`s, no reloads. |

## Numerical Validation

### Spot Checks (independent re-derivation)

- **Cost overlay (EURUSD-1h RCT):** gross_mean 0.29754 − cost_txn 0.23686 = 0.06068 = net_mean (0.06067). ✓ F=0 confirmed on all rows.
- **Net-clear boolean:** recomputed `net_ci_low>0` for all 120 rows → identical to `net_clear` column (0 mismatches). ✓
- **RCT quorum:** independently counted net-clearing RCT cells = {EURUSD-1h, GBPUSD-1h, NZDUSD-1h, US2000-1h, USTEC-1h} = 5 cells / 5 distinct instruments → passes (≥5/≥3). ✓
- **Native A/B:** `delta_RCT_minus_RSIREVERT > 0` in 20/20 cells (range +0.2231…+0.2927, median +0.2609). ✓ matches `n_RCT_gt_RSIREVERT=20`, Wilcoxon p≈1.9e-6.

### Range / sanity

| Metric | Expected | Actual | Pass? |
|--------|----------|--------|-------|
| `resolved_frac` | (0,1], high | [0.9943, 0.9996] | YES |
| `net_clear` vs `net_ci_low>0` | identical | 0 mismatches / 120 | YES |
| `cost_fin_mean` | 0 (F=0) | 0 all rows | YES |
| gross_ci_low>0 (RCT, ERT) | broad (availability real) | 20/20 both natives | YES |
| Determinism | byte-identical replay | pass (2 cells, USTEC-15m + EURUSD-1h) | YES |

## Assumption Validation

| Method | Assumption | Holds? | Evidence |
|--------|-----------|--------|----------|
| Moving-block bootstrap `ci_low_1s` | within-cell block exchangeability; powered n | YES | n_resolved ≥ 3835/cell — far above the EXP-090 MDE regime; block length `round(n**⅓)` inherited. |
| Cost as additive ATR-unit location shift | net = gross − cost per event | YES | identity exact to machine eps; cost is per-event txn in ATR units. |
| Wilcoxon paired Δ (descriptive) | paired-by-cell, non-parametric | YES (non-binding) | 20 matched cells; reported as attribution only, does not gate. |

## Results Plausibility

All outputs in-domain. Both native arms have **gross** edge on 20/20 cells (availability is real and broad);
the reactive/conventional arms have gross edge on only 7–8/20. The net collapse to ≤5 clears is driven entirely
by the cost overlay — consistent with the honest prior (*availability ≠ capturable edge*) and with the
~3-bar / ~0.28-ATR gross geometry.

## Verdict Forensics (run autonomously)

### Per-stratum re-derivation & masking check

| Stratum | Per-stratum result (RCT) | Agrees with "RCT passes" headline? | Notes |
|---------|--------------------------|-------------------------------------|-------|
| Domain 15m (10 cells) | **0/10** net-clear | NO (headline is carried wholly by the other domain) | every 15m cell net-NEGATIVE; cost (~0.6 ATR) > gross (~0.28 ATR). |
| Domain 1h (10 cells) | **5/10** net-clear | YES | the entire pass lives here. |
| 1h clearing cells | EURUSD, GBPUSD, NZDUSD, US2000, USTEC | YES | the 5 lowest-cost-in-ATR 1h cells. |
| GBPUSD-1h | net_ci_low **+0.00426** | YES but boundary | one cell essentially touching zero — drop it and RCT = 4 cells → FAIL. |

- **Pooled/aggregate headline:** "RCT passes the screen (5/5)." **Is it masking heterogeneity? PARTIALLY —
  and it must be disclosed, but it does not change the mechanical verdict.** The quorum is the *predeclared D6
  count over per-stratum net-clears* (not an illegitimate pooled boolean), so RCT genuinely passes. But the pass
  is **(a) domain-conditional** — 0/10 on 15m, 5/10 on 1h; **(b) boundary-fragile** — hangs on GBPUSD-1h at
  +0.0043; **(c) mean/tail-carried** — see Mechanism. None of these flips the 5/3 count, so none is
  verdict-material in the blocking sense; all three are **binding interpretive context** for Stage 6 and the
  EXP-092 candidate selection.

### Mechanism

The verdict is a **pure ATR-normalized cost-geometry** result, not a signal-strength result.

- **Gross is ≈ domain-invariant.** RCT hits its reversion-completion target on **~99%** of events
  (`terminal_fav` 0.989–0.997) for a gross mean of **~0.27–0.30 ATR everywhere**, 15m and 1h alike.
- **Cost is NOT domain-invariant.** The conservative round-trip is a fixed bps figure converted to price and
  divided by the entry **ATR(14)**. A 15m bar's ATR is far smaller than a 1h bar's, so the *same* bps round-trip
  consumes **~0.6 ATR on 15m vs ~0.24–0.30 ATR on 1h**. Net = gross − cost is therefore deeply negative on 15m
  (cost ≈ 2× gross) and hovers around zero on 1h, turning positive only on the **cheapest** instruments
  (EURUSD/GBPUSD/NZDUSD = 3–4 bps; USTEC = 5 bps; US2000 = 6 bps but larger ATR).
- **The pass is mean/right-tail-carried on 3 of the 5 clearing cells.** EURUSD-1h, GBPUSD-1h and NZDUSD-1h have
  **net_mean > 0 with net_median < 0** (e.g. EURUSD-1h mean +0.0607 / median −0.0103; GBPUSD-1h +0.0183 /
  −0.0518). The binding figure is the **mean** lower bound (per plan, matching EXP-090) — legitimately positive —
  but the *typical* trade in those cells loses after cost; the positive expectancy is carried by the favourable
  right tail. USTEC-1h and US2000-1h are the only cells whose **median is also positive** (+0.040, +0.028) — the
  two robustly-clearing cells. This is the EXP-089 mean-fragile / median-watch signature, predeclared in the
  analysis plan, persisting into the net exit.

### Gate-shape check

- **Binding gate:** mean per-event expectancy one-sided lower bound (a **location** gate). **Effect shape:** a
  location effect on the mean — so the gate is the **correct instrument** for the scoped endpoint; there is no
  "gate blind to the shape" mismatch. The *median* is a different (more conservative) location read; it is
  co-reported and disagrees on 3/5 clearing cells. The gate is not retro-edited. The interpreter must carry the
  mean-vs-median split forward (it distinguishes "robust net edge" — USTEC-1h, US2000-1h — from "mean/tail-only
  net edge" — EURUSD/GBPUSD/NZDUSD-1h), but this is a **read of degree, not a verdict-flip**.

## Scope Compliance

- Analysis plan followed: **YES** — 7 steps + 4 plots implemented; no bonus analyses.
- Complexity budget: tests 2/≤2 (net `ci_low_1s` binding; Wilcoxon descriptive), plots 4/≤4, modules 0/target 0–1
  (one screen-orchestration script reusing the EXP-090/capgeo stack; no new `xen` module, no frozen-generator edits).
- Holdout exclusion verified: **YES** (TRAIN sub-split; analysis-TEST + final-30% never sliced; `holdout_untouched=true`).
- Registry: 0 candidate slots, 0 counted TEST reads — consistent with scope and the Phase-021 batch.

## Issues

### Critical

None. No finding can move sample membership, a denominator, a metric value, temporal/causal validity, the
mechanical screen verdict, or the binding stratum.

### Warning

1. **The pass is domain-conditional (1h-only) and the interpreter must not generalize it to 15m.**
   - Evidence: RCT 0/10 on 15m, 5/10 on 1h; every 15m net is negative.
   - Materiality: does **not** change the 5/3 quorum count (the clearing cells are all 1h by construction of the
     count). It is binding context for EXP-092 (the carried candidate set should be 1h-cell-scoped) and for the
     G-021 narrative. **Cannot move a verdict-bearing number** → non-blocking, but must appear in `results.md`.

2. **The pass is boundary-fragile: it hangs on GBPUSD-1h at net_ci_low = +0.0043.**
   - Evidence: 4 of the 5 clearing cells are ≥ +0.039; GBPUSD-1h is +0.0043 (essentially zero). Remove it and
     RCT = 4 cells → fails the 5-cell quorum.
   - Materiality: the **realized** count is 5 and reproduces deterministically, so the mechanical verdict is firm
     *as computed*; the fragility is a robustness disclosure (it informs how much weight EXP-092/093 place on the
     pass), not a code defect or a number that the audit can/should move. Non-blocking; must appear in `results.md`.

3. **On 3 of the 5 clearing cells the net edge is mean/right-tail-carried (net_median < 0).**
   - Evidence: EURUSD-1h, GBPUSD-1h, NZDUSD-1h have net_mean>0 but net_median<0; only USTEC-1h and US2000-1h have
     net_median>0.
   - Materiality: the **binding** endpoint is the mean lower bound (scoped, EXP-090-matched), which is positive —
     so the verdict stands. The median disagreement is the predeclared EXP-089 watch; it must be disclosed so the
     EXP-092 candidate set is read shape-aware. **Cannot move the binding (mean) figure** → non-blocking.

### Info

1. **Result is cost-table-sensitive by construction (disclosed companion behaves as predeclared).** Under the
   faster round-trip variant (`RT/2`, predeclared D3 companion) RCT net-clears **14** cells vs 5 binding. This is
   the intended sensitivity disclosure, not a defect; it confirms the screen is cost-dominated, not signal-absent.
   The binding cost is the operator-ratified Phase-021-local conservative table (`D0-amendment-003`, hash
   `fa7c887…`); shared `xen.capgeo_cost.COST_CONSTANTS` untouched (Phase-018 integrity verified in code).

2. **`net_return_atr` is a misnomer** — it computes the *gross* signed ATR return (used for `gross`), inherited
   from EXP-090. Cosmetic; no numeric effect.

3. **Determinism replay is a reduced check** — 2 cells, comparing `net_ci_low/gross_ci_low/net_clear/n_resolved`
   rather than full-frame on all 20 (scope language was "frame-identical every cell"). Mitigants: content-addressed
   `seed_for` seeds, deterministic `default_rng`, both a 15m and a 1h high-count cell checked, and all 5 headline
   CSVs SHA-256-pinned in `run_metadata.json` for external re-verification. Affects reproducibility assurance, not
   any verdict-bearing number → non-blocking.

## Materiality & Re-Audit Requirements

- **No blocking finding.** Every Warning/Info is accompanied above by the explicit reasoning that it cannot move
  sample membership, a denominator, the binding (mean) metric, causality, or the mechanical screen verdict. The
  three Warnings are **mandatory interpretive content** that Stage 6 must carry (domain-conditional, fragile,
  mean/tail-carried), and Stage 7/Stage 8 must confirm they were carried.
- **No re-run required.** The numbers reproduce exactly; the cost-table provenance is ratified and hashed; the
  holdout is sealed. Proceed to Stage 6.

**Audit verdict: PASS.**
