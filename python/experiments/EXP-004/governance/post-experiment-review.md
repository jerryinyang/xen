VERDICT: APPROVE

Reviewed artifacts:
- `python/experiments/EXP-004/audit.md`
- `python/experiments/EXP-004/results.md`
- `python/experiments/EXP-004/report.md`
- `python/experiments/INDEX.md` (EXP-004 row added)
- `docs/experiments-docs/INDEX.md` (EXP-004 comprehensive section added)

## Governance assessment

### Audit (audit.md)
- Thorough: correctness, edge cases, type safety, NaN handling, holdout
  exclusion, look-ahead safety, and real-price discipline all checked, with
  exact file/line references.
- Independent numerical validation present: re-derived all 48 consistency
  classifications (0 mismatches), re-built the EXP-003 α=0.05 MDE map (0
  mismatches), and verified the gross−net = cost×active-fraction relationship.
- Severity classification appropriate: 0 Critical, 0 Warning, 4 Info; the Info
  notes (vectorizable Donchian loop, block_length=1, generators in the shared
  module, unexercised conservative grey-band branch) are advisory and do not
  affect trust. Verdict PASS.

### Holdout & look-ahead
- First-70% analysis slice only; `analysis_metadata.csv` shows `analysis_end`
  precedes each source file's end date, confirming the final 30% holdout was
  never loaded.
- Train/test cut is the shared 1-minute `CloseTime` boundary (`domain_split_index`),
  not a per-timeframe row fraction — no cross-domain future leakage.
- Donchian uses prior-window highs/lows; MA uses closes at bar `t`; both evaluated
  on `t→t+1` real returns. No future data used.

### Real-price & alignment discipline
- Returns computed from real resampled domain `Close`; no chart-type views, no
  HA/Renko synthetic prices. Alignment is timestamp-based throughout.

### Scope & complexity
- Single hypothesis (dogfood consistency vs MDE map); boundaries, exclusions, and
  predeclared success/failure/inconclusive criteria all honoured.
- Budget respected: 2/2 statistical tests (two referees), 3/3 visualisations,
  0/0 new modules (dogfood generators added to the existing shared module).
- No scope creep: fixed, untuned parameters (Donchian 20, MA 20/50, α=0.05); no
  referee redesign based on dogfood results.

### Interpretation (results.md) & report (report.md)
- Honest and non-overreaching: H-dogfood SUPPORTED (48/48 consistent) is justified
  by the predeclared criteria; the keystone contribution is correctly framed as a
  **null/lower anchor** that bounds (does not close) the structural-blindness
  question, since no positive real edge was present to probe near-MDE detection.
- Uncertainty, limitations, and alternative explanations included.
- Follow-ups are framed as new experiments (proposed EXP-005/006/007), not scope
  extensions.
- Report is self-contained, embeds the two key plots with captions, links all
  artifacts by relative path, and both indexes are updated.

## Phase alignment

EXP-004 is the planned final experiment of checkpoint
2026-06-01-001-thesis-qualification-calibration (design §10). It is aligned with
the dogfood-anchor objective. The phase is now ready for its retrospective, which
is a separate pipeline action outside this experiment's post-execution scope.

No Critical or Warning issues. APPROVE.
