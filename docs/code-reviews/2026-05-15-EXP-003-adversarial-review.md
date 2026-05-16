# EXP-003 Adversarial Review

**Timestamp:** 2026-05-15
**Review skill:** `bmad-review-adversarial-general`
**Pipeline context:** `research-pipeline`
**Experiment:** EXP-003 - Noise Filtering & Statistical Robustness

## Scope Reviewed

This is a pre-execution review. The EXP-003 directory contains `scope.md`, `analysis-plan.md`, `code/run_experiment.py`, and `governance/pre-execution-review.md`. No `results/`, `audit.md`, `results.md`, `report.md`, or post-execution governance artifacts exist yet, so result integrity and numerical correctness cannot be reviewed.

References consulted:

- `docs/references/dataset-reference.md`
- `python/experiments/INDEX.md`
- `docs/experiments-docs/INDEX.md`
- `docs/experiments-docs/checkpoints/2026-05-14-001-chart-type-validation/design.md`
- `.opencode/skills/research-pipeline/_pipeline-config.md`
- `.opencode/skills/research-pipeline/references/governance-constraints.md`
- `python/experiments/EXP-003/scope.md`
- `python/experiments/EXP-003/analysis-plan.md`
- `python/experiments/EXP-003/code/run_experiment.py`
- `python/experiments/EXP-003/governance/pre-execution-review.md`
- `python/src/linebreak_generator.py`
- `python/src/renko_generator.py`
- `python/src/heiken_ashi_generator.py`
- `python/src/time_alignment.py`

## Review Lens

Content type: empirical experiment plan plus Python implementation.
Active lenses: **statistical methodology > algorithm correctness > replication risk**.

Justification: EXP-003 is an empirical study injecting synthetic noise into financial time-series data and measuring statistical stability of chart-type transformations. The primary risk is methodological (whether the metrics and comparisons actually test what the hypothesis claims) and algorithmic (whether the perturbation and metric code produce valid, reproducible results). Replication risk is secondary since the experiment is deterministic by design.

## Content Type Assessment

This spans two types:
- **Empirical study** — the core experiment measures statistical properties of generated data.
- **Algorithm** — the perturbation logic and stability metrics are algorithmic constructs that must be correct for the results to be meaningful.

The primary lens (statistical methodology) applies because the success/failure criteria depend on whether the metrics validly measure "robustness." The secondary lens (algorithm correctness) applies because bugs in perturbation or metric computation produce silently wrong results.

## Findings

```json
[
  {
    "id": "F01",
    "severity": "Major",
    "title": "Heiken Ashi variance stability metric is degenerate with time bars",
    "evidence": "CHART_CONFIG sets HeikenAshi close_col to 'RealClose' (run_experiment.py:58). extract_real_returns uses chart_df['RealClose'] directly when close_col is set (run_experiment.py:405-407). HeikenAshi RealClose is the original time-bar Close copied into the HA DataFrame (heiken_ashi_generator.py:59). Since HA candles are 1:1 with time bars, np.diff(RealClose) for HA is identical to np.diff(Close) for time bars.",
    "impact": "The VarianceDrift metric for Heiken Ashi will be numerically identical to VarianceDrift for time bars, making the comparison trivially equal. This does not test HA's noise filtering — it tests the same underlying price series twice. The hypothesis clause 'Heiken Ashi reduces variance' cannot be evaluated without measuring HA-price variance distortion separately from real-price variance stability. The scope's success criteria call for comparing variance stability across chart types, but the HA vs Time comparison is vacuous.",
    "fix": "Add an explicit HA-price variance distortion metric that measures drift in HAClose returns vs RealClose returns, distinct from the shared real-price variance. Alternatively, document in scope/results.md that HA variance stability is tautological and exclude HA from the VarianceDrift ranking, relying on DirectionDrift and ComplexityDrift (which use HA-native directions) for HA evaluation."
  },
  {
    "id": "F02",
    "severity": "Major",
    "title": "OHLC integrity repair is incomplete — Open can fall outside [Low, High]",
    "evidence": "perturb_time_bars modifies Close and repairs High/Low: new_highs = np.maximum(highs, new_closes); new_lows = np.minimum(lows, new_closes) (run_experiment.py:150-151). Open is never modified. The dataset reference requires High >= max(Open, Close) and Low <= min(Open, Close) (dataset-reference.md:50-51). The repair only enforces High >= Close and Low <= Close, leaving Open potentially outside [Low, High].",
    "impact": "Perturbed bars can violate OHLC integrity if Open > new High or Open < new Low, producing synthetic data that could never exist in real markets. Downstream chart-type generators receiving these invalid bars may produce undefined behavior. The scope's inconclusive criterion checks whether perturbation produces invalid OHLC bars for >5% of rows, but the current repair doesn't guarantee validity and the >5% check isn't implemented in code.",
    "fix": "Extend the repair to also ensure High >= max(Open, Close) and Low <= min(Open, Close): new_highs = np.maximum(highs, np.maximum(new_closes, opens)); new_lows = np.minimum(lows, np.minimum(new_closes, opens)). Add a validation pass that counts and reports any remaining violations. Implement the scope's >5% invalid-bar threshold check."
  },
  {
    "id": "F03",
    "severity": "Major",
    "title": "Lempel-Ziv implementation is non-standard and overcounts complexity",
    "evidence": "lempel_ziv_complexity (run_experiment.py:242-276) iterates length from 1 upward and increments complexity when the first shortest substring not in the prefix is found. Standard LZ76 factorization finds the LONGEST match in the parsed prefix and then extends by one character. The implemented shortest-new-substring algorithm will generally produce a higher count than LZ76 because it splits at shorter boundaries.",
    "impact": "Absolute LZ complexity values will not match published LZ76 benchmarks, making cross-study comparison impossible. The relative drift (|perturbed_lz - baseline_lz| / baseline_lz) is still approximately valid for within-experiment comparison, but the complexity values themselves are inflated. Additionally, if baseline and perturbed sequences have very different lengths (e.g., Renko producing different numbers of bricks under perturbation), length-dependent scaling of LZ complexity conflates length effects with noise sensitivity.",
    "fix": "Replace with the standard LZ76 factorization algorithm, or use a length-normalized variant (e.g., dividing by log2(n)). At minimum, document the deviation from LZ76 in the analysis plan and results so readers don't interpret the values as standard LZ complexity."
  },
  {
    "id": "F04",
    "severity": "Minor",
    "title": "Perturbation seed deviates from scope specification",
    "evidence": "Scope states 'seed derived from instrument and timestamp' (scope.md:36). Implementation uses base_seed = abs(hash(f'{instrument}_EXP003_noise')) % (2**31) (run_experiment.py:129), which is an instrument-level seed without per-bar timestamp incorporation.",
    "impact": "Low practical impact — the perturbation is still deterministic and reproducible per instrument. However, the scope specification implied per-bar seeding tied to timestamps, which would ensure perturbations are identifiable and reproducible at the bar level. The current approach ties the seed to the instrument name only, so reordering bars would change which bars get perturbed.",
    "fix": "Update scope.md to document the actual seeding mechanism (instrument-level hash seed with vectorized bar selection) for consistency, or implement per-bar hashing if bar-level reproducibility is desired."
  },
  {
    "id": "F05",
    "severity": "Minor",
    "title": "Direction-sign perturbation not implemented despite scope mentioning it",
    "evidence": "Scope says 'Perturb close values or direction signs' (scope.md:36, emphasis on 'or'). The implementation only perturbs Close values with magnitude perturbation (run_experiment.py:144-147). No direction-sign flip perturbation is implemented.",
    "impact": "The experiment only tests one noise model (price-level perturbation). Direction-sign perturbation would test a qualitatively different stress: whether chart types are robust to bars that close in the opposite direction of their true movement. Since 'or' in the scope permits either, this is within scope, but the experiment is less comprehensive than the scope description suggests.",
    "fix": "Either implement a second perturbation type that flips direction (Close = Open rather than a random offset), or amend the scope to clarify that only price-level perturbation is tested, and note this as a scope narrowing in analysis-plan.md or results.md."
  },
  {
    "id": "F06",
    "severity": "Minor",
    "title": "LZ complexity comparison across sequences of different lengths",
    "evidence": "compute_complexity_stability (run_experiment.py:332-354) computes LZ complexity on baseline_directions and perturbed_directions independently, then takes relative drift. For event-based chart types (Line Break, Renko), perturbation can change the number of generated bars, producing sequences of different lengths. LZ complexity scales with log(n) for random sequences, so different lengths produce different baseline levels.",
    "impact": "If Renko or Line Break produces 8000 bars baseline and 6000 bars perturbed, the complexity drift includes a length-effect component unrelated to noise sensitivity. This biases complexity drift upward for chart types that change bar count under perturbation, which is likely the event-based types the hypothesis claims are more robust.",
    "fix": "Normalize LZ complexity by sequence length (divide by log2(n) or use the LZ76 normalized variant), or truncate both sequences to the minimum length before comparison. Adding the normalized variant preserves the relative comparison while removing length confounds."
  },
  {
    "id": "F07",
    "severity": "Minor",
    "title": "Inconclusive-criterion bar validity threshold not implemented",
    "evidence": "The scope defines inconclusive as 'perturbation produces invalid OHLC bars after repair for more than 5% of rows' (scope.md:26). The code computes repaired_rows but does not validate that repaired bars satisfy full OHLC integrity (see F02), nor does it compare the proportion against the 5% threshold to classify the result as inconclusive.",
    "impact": "The experiment cannot automatically flag inconclusive results per its own scope criterion. This must be checked manually from the perturbation_audit.csv output.",
    "fix": "After the perturbation quality summary, add a check that computes the proportion of invalid/repaired bars and flags the result as inconclusive if it exceeds 5%."
  },
  {
    "id": "F08",
    "severity": "Minor",
    "title": "Variance metric naming is ambiguous — not a Variance Ratio test",
    "evidence": "The scope refers to 'variance ratio stability' (scope.md:7) and the analysis plan refers to 'variance ratio stability' (analysis-plan.md:21). The code computes relative drift in return variance: |perturbed_var - baseline_var| / baseline_var (run_experiment.py:325-328). This is not the Variance Ratio (VR) test for random walks used in financial econometrics.",
    "impact": "Readers familiar with the VR test will be confused by 'variance ratio' terminology. The metric measures variance stability under perturbation, not the VR test statistic. This is a naming issue, not a correctness issue — the computation itself is appropriate for the experiment's purpose.",
    "fix": "Rename the metric from 'VarianceDrift' to 'ReturnVarianceDrift' or 'VarianceStabilityDrift' in the code and outputs, and update scope/analysis-plan to say 'return variance stability' instead of 'variance ratio stability' to avoid confusion with the VR test."
  }
]
```

## Summary

Three Major findings dominate. **F01** identifies that Heiken Ashi's variance stability metric is degenerate — it compares RealClose returns against themselves, producing identical drift to time bars and making the HA variance comparison vacuous. This undermines one of the three metrics for the primary hypothesis evaluation. **F02** identifies that OHLC repair after perturbation leaves Open potentially outside [Low, High], producing impossible synthetic bars that could corrupt downstream chart-type generators. **F03** identifies that the Lempel-Ziv complexity algorithm deviates from the standard LZ76 definition, overcounting factors and conflating length effects when baseline and perturbed sequences differ in length. The five Minor findings (F04–F08) concern seed documentation, missing perturbation types, length normalization, the unimplemented 5% invalid-bar threshold, and ambiguous metric naming. The pre-execution governance review passed all constraints but did not catch F01, F02, or F03, which are substantive methodological issues that should be resolved before relying on the experimental results.