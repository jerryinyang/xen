# Results: Experiment EXP-035

## Summary

**CHARACTERISATION_DELIVERED — zero qualified dimensions across all 9 domain×dimension cells.**

No predeclared conditioning dimension (C1 %completion-to-target, C2 session, C3 trailing-vol regime) passes the G1 conjunction on any domain. The binding failure is consistent: every dimension's materiality leg fails because the candidate-bin TRAIN net expectancy is ≤ 0 under frozen costs + financing (even the best bin is net-negative on absolute terms), or the SNR is below the 1.0 floor, or both.

The conditioning lever is therefore empty on this entry substrate. Per design §9, this outcome routes the phase toward FLAT/Tier-C — selectivity/efficiency levers on the existing entry substrate do not produce a clinical subset with positive absolute net.

## Detailed Findings

### Finding 1: All 9 Cells Fail Materiality (§8.1i)

- **Observation**: No domain×dimension cell satisfies both prongs of the materiality criterion (SNR ≥ 1 AND candidate-bin net > 0). The closest is 5m/c1_completion (SNR = 1.42) but its candidate (high %completion) mean net = −7.07 bps — still negative.
- **Evidence**: `results/g1_qualification.csv`: `material_i = false` on every row. `results/characterisation.csv` for per-cell detail.
- **Interpretation**: Conditioning can separate bins by relative performance (some bins are less negative than others), but no bin achieves positive absolute net expectancy. On 5m, even the best %completion tercile (−7.07 bps) remains well below zero. The pattern is consistent across all three dimensions: the edge is relative, not absolute — consistent with Phase 007's core finding.

### Finding 2: Structure and Stability Pass on Some Cells

- **Observation**: 5m/c1 passes the structure leg (weak monotonic ordering: low < mid < high mean net) and stability leg (same candidate bin in both TRAIN halves, Δ > 0 in both). 5m/c2 passes stability. 4h all cells fail stability (halves disagree).
- **Evidence**: `results/characterisation.csv`: `structured_ii` and `stable_iii` per cell. `results/g1_qualification.csv` for final flags. Plot: `plots/split_half_stability.png`.
- **Interpretation**: The %completion dimension shows real and stable relative separation on 5m (higher completion-to-target → less negative outcomes), but the separation is within a net-negative regime. The session dimension on 1h/5m also shows some stability. The vol regime dimension is noisy, especially on 4h where both stability and structure fail.

### Finding 3: Multiplicity Passes But Is Moot

- **Observation**: Holm adjustment does not block any cell (no cell had a qualifying permutation p at α_G1 = 0.10 that would have survived adjustment). 5m/c1 has perm_p = 0.010 and holm_p = 0.030 < 0.10, but materiality already failed.
- **Evidence**: `results/g1_qualification.csv`: `multiplicity_iv` column.
- **Interpretation**: The multiplicity gate (iv) is not the binding constraint — materiality (i) is. Even the 5m/c1 cell with a strong permutation p does not qualify because the best bin's absolute net is negative.

### Finding 4: 4h Underpowered as Expected

- **Observation**: 4h cells have very wide CIs (SNR 0.15–0.58) and unstable split-half results. 4h TRAIN events = 125 (excluding containment), split across 4 instruments and 3 bins/tercile → ~10 events per instrument×tercile cell.
- **Evidence**: `results/population_accounting.csv`: 4h n_events_train = 125. `results/characterisation.csv`: 4h CI half-widths 42–64 bps. `results/g1_qualification.csv`: all 4h cells fail all criteria.
- **Interpretation**: 4h is predeclared as likely floor-fragile (~40 events per tercile). The wide CIs confirm this — no conditioning conclusion is possible on 4h from this experiment. This is expected and not new information.

## Verdict

**CHARACTERISATION_DELIVERED — zero G1-qualified dimensions.**

Per design §9, this outcome maps to the `FLAT` path: no selectivity lever produces a clinical (net-positive) subset on this entry substrate under frozen costs + financing. The conditioning lever is exhausted.

## Limitations

- TRAIN-only characterisation. The relative separation observed on 5m/c1 may not replicate on TEST.
- 4h is underpowered for conditioning characterisation (n=125 TRAIN events). 4h may have qualifying dimensions that cannot be resolved with the current sample — but this cannot be determined here.
- The 5m/c1 gradient (higher %completion → less negative) is hypothesis-generating, not a rule. The hard no-selection rule prevents promoting it without a fresh TEST read.
- Permutation p values are acknowledged as anti-conservative under clustering, but materiality (the binding leg) uses the cluster-aware bootstrap CI.

## Alternative Explanations

- The consistent failure of materiality (even the best bin is net-negative) could be a cost-model or financing artifact: if costs or financing are overestimated, a dimension's best bin might be net-positive under more favorable assumptions. However, per the scope, no cost-model iteration is permitted.
- Conditional rules combine dimensions (e.g., high completion AND low volatility) might unlock a positive subset even when no single dimension does, but interaction analysis is explicitly out of scope (plan: "no interaction/conjunction analysis").

## Recommended Next Steps

- Per design §9, the FLAT path opens: B1 (/COND) does not open (no qualified conditioning dimension). The phase outcome leans entirely on B2 (/EXIT-FH) from EXP-033's 4h B2 eligibility, and Tier C (Stage-C branches or HYP-001).
- Document this result for the G1 gate review: the selectivity lever is empty, capture efficiency (B2) is the only remaining Tier-B path.
