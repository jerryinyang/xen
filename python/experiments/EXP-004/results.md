# Results: Experiment EXP-004 — Real Dogfood Consistency Anchor

## Summary

Across all 48 cells (4 instruments × 3 domains {5m, 1h, 4h} × 2 strategies
{Donchian(20), MA(20,50)} × 2 referees {minimal baseline, gate stack}), both
referees returned **REJECT**, and every cell was classified **consistent**
(`matched_reject`) with the EXP-003 calibrated MDE map: each measured net effect
sits below its domain MDE, so a reject is exactly what the calibration map
predicts. There are **0 inconsistent and 0 inconclusive cells**, so the
experiment's hypothesis (H-dogfood) is **SUPPORTED**. The deeper purpose — the
empirical anchor for the keystone reading (H-keystone) — yields a **null/lower
anchor**: these simple untuned strategies carry no statistically positive edge
even gross of cost, so they locate "where simple intraday edges live" at ≈0,
beneath every per-domain MDE. That is consistent with (does not contradict) the
gate stack's rejections, but it does not positively resolve the structural-
blindness question, because no real positive edge was present to probe detection
near the MDE boundary. The audit verdict is PASS.

## Detailed Findings

### Finding 1 — Every dogfood verdict is consistent with its MDE position (H-dogfood)

- **Observation**: 48/48 cells REJECT; 48/48 `consistency_status = PASS`
  (`reason = matched_reject`). `run_metadata.json` `overall_status = PASS`.
- **Evidence**: `dogfood_consistency.csv`; plots `dogfood_consistency_counts.png`
  (all bars in the consistent category) and `candidate_verdict_matrix.png`
  (uniformly REJECT). For each cell the gate-stack point estimate is below
  `MDE + grid_uncertainty` and the CI lower bound is below `MDE − grid_uncertainty`,
  so the predeclared rule (design §10) expects REJECT — which both referees
  return. The audit independently re-derived all 48 classifications with 0
  mismatches and confirmed the EXP-003 α=0.05 MDE map loaded correctly
  (5m gate 1.0 / 1h gate 4.0 / 4h gate 12.0 bps; minimal 0.5 / 0.5 / 2.0).
- **Interpretation**: Real, simple, untuned price strategies behave exactly as
  the synthetic calibration predicts for edge-free inputs — no synthetic-vs-real
  DGP gap is surfaced. H-dogfood is supported.

### Finding 2 — The strategies carry no positive edge, even gross of cost

- **Observation**: The minimal-baseline referee tests the **gross** edge (no cost
  gate). It also REJECTs all 48, i.e. no candidate's gross effect has a
  block-bootstrap CI excluding zero.
- **Evidence** (`dogfood_effects.csv`, minimal-baseline rows): gross effects span
  ≈ **[−2.20, +1.32] bps/trade**, every CI brackets or sits below zero. Examples:
  XAUUSD/4h/MA +1.317 [−1.445, +4.035]; USTEC/1h/Donchian +0.226 [−0.178, +0.680];
  EURUSD/1h/MA +0.120 [−0.212, +0.448]. The gate-stack (net) effects are the gross
  effect minus cost×(active-bar fraction), driving them negative: e.g.
  BTCUSD/5m/MA gross +0.013 → net −9.987 (BTCUSD round-trip cost 10 bps);
  the most negative is BTCUSD/4h/MA −12.20 [−18.52, −6.46].
- **Interpretation**: The rejections are not merely "edge eaten by cost" — there
  is no statistically detectable edge to begin with. This is the expected
  behaviour of untuned Donchian/MA and confirms the candidates are an honest
  edge-free real-data input.

### Finding 3 — Empirical-anchor reading for H-keystone: a null/lower anchor

- **Observation**: Per design §4 / §10 / D-ceiling, EXP-004's measured effect
  sizes are meant to locate where plausibly-real intraday edges live, against
  which EXP-003's per-domain gate MDE is judged blind or not. The measured edges
  cluster at ≈0 (gross) / negative (net), all below the gate MDE on every domain.
- **Evidence**: gate MDE vs best gross dogfood effect by domain — 5m: MDE 1.0 vs
  max gross ≈ 0.04; 1h: MDE 4.0 vs max gross ≈ 0.50; 4h: MDE 12.0 vs max gross
  ≈ 1.32. Plot `dogfood_effects_vs_mde.png` shows every effect marker below its
  red MDE marker. The 4h gate MDE (12 bps) sits an order of magnitude above where
  these effects fall.
- **Interpretation**: This is a **null anchor**. It demonstrates that these simple
  untuned strategies have no edge above the MDE (true negatives → the gate's
  rejections are correct, not false negatives), and it bounds simple-strategy
  edge magnitudes at ≈0/sub-materiality. It does **not** demonstrate that the gate
  MDE sits below genuinely-real-but-weak edges, because no such positive edge was
  present in this dogfood set to test detection just beneath the MDE. The keystone
  structural-blindness question is therefore **not falsified and not positively
  resolved** by this anchor — it is consistent and bounded, not closed.

## Hypothesis Verdict

**SUPPORTED** (for the experiment's own hypothesis, H-dogfood).

Every finite-MDE cell satisfies the predeclared Evidence-FOR criterion (a reject
with point estimate below MDE), with 0 cells meeting Evidence-AGAINST (a pass
below MDE or a reject well above MDE) and 0 inconclusive cells. Real Donchian and
MA-crossover verdicts agree with where their measured effect sizes fall on the
calibrated per-domain MDE map.

For the cross-experiment H-keystone reading this experiment feeds: the anchor is
a **null/lower anchor** — simple untuned intraday edges live at ≈0, beneath all
per-domain MDEs. Consistent with the gate stack's behaviour; insufficient on its
own to declare the gate stack non-blind to weak real edges.

## Limitations

- **Null anchor.** With no positive real edge in the set, the experiment cannot
  probe the gate's detection in the near-MDE region — the zone where structural
  blindness would actually bite. It bounds edges from above (≈0), not the gate's
  sensitivity to a real-but-weak edge.
- **Narrow candidate universe.** Two strategy families at one fixed lookback each
  (by design — untuned). They do not represent the full space of plausibly-real
  intraday edges; absence of edge here does not generalise to all simple signals.
- **Effective-N / block length.** `block_length = 1` for all 48 cells (lag-1 ACF
  of per-bar strategy returns < 1/e), so the stationary bootstrap reduced to
  i.i.d. resampling and effective N equals the raw test-bar count (4h smallest at
  ~900–1335, widest CIs; 5m largest at ~50–65k).
- **Pooled/flat cost & single operating point.** Flat per-instrument/domain
  round-trip costs (EURUSD 1 / XAUUSD 3 / USTEC 4 / BTCUSD 10 bps), log-return
  bps, and α=0.05 only. The MDE map is itself a four-instrument domain aggregate
  from EXP-003.
- **Grey-band branch unexercised.** The classifier's conservative INCONCLUSIVE
  branch (large point estimate, wide CI) was never triggered (0/48); the
  consistency reading rests entirely on the clean reject-below-MDE case.

## Alternative Explanations

- The uniform REJECT could reflect genuinely edge-free candidates **or**
  candidates mis-specified for these instruments/domains. Either way the
  consistency verdict (verdict matches MDE position) holds, since both readings
  place the effect below the MDE.
- The systematic gate-stack negativity is mechanical (cost applied to active
  bars), not evidence of a negative edge per se; the gross (minimal-baseline)
  effects are the cleaner read on edge presence, and they too are non-positive.

## Recommended Next Steps

1. **New EXP** — *Near-MDE detection anchor*: evaluate a candidate engineered to
   carry a small, real, predeclared edge straddling each domain's gate MDE (e.g.
   a weak real-feature signal, or a real strategy with a controlled planted-edge
   overlay validated as in EXP-001), to convert this null anchor into a near-MDE
   anchor and directly test the gate stack's structural blindness at the boundary.
2. **New EXP** — *Broadened dogfood distribution*: a wider real-candidate set
   (additional lookbacks and strategy families, still untuned) to characterise the
   empirical effect-size distribution of simple intraday signals, giving the
   keystone a population-level anchor rather than two point candidates.
3. **New EXP** — *Per-instrument MDE*: re-derive MDE per instrument (not pooled)
   so the dogfood comparison uses instrument-specific detection floors, since
   per-instrument costs and dispersion differ by up to 10×.
