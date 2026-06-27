# Results: Experiment EXP-087

**Screen X — cross-sectional relative-strength / directional-favourable availability (Phase 019 family-selection).**
Axis X · `CF-XSECT-001/HYP-001` · TRAIN-only, gross · 0 candidate slots · 0 counted TEST reads · holdout untouched.

> **Reading frame (binding).** This is a family-agnostic *availability* screen, **not** an edge,
> tradability, or candidate verdict. EXP-087 emits the realized D2b gate statistics; the **binding
> admit / exonerate adjudication is G-019**, under the frozen D5 rule with the cross-axis Holm
> step-down over the {M, X, (F)} slate. Every disposition below is captioned **NON-BINDING**.

## Summary

Conditioning entries on **cross-sectional relative strength** (top/bottom-decile trailing-20-bar return,
both as a raw rank `COND-XSRANK` and as divergence-from-basket `COND-XSDIV`, traded in the decile-sign
direction) produces **no improvement** in directional-favourable availability over a direction-matched
random-timing control, across all 46 member cells. The axis statistic `S_X = 1` cells-beat-random sits
**at the permuted-axis null ceiling** (`S* = 1`, axis perm-p `= 0.323`, ranking z `= 1.26`); both
primitives independently fail (`S = 1` each; perm-p 0.113 / 0.236). The routing is invariant across
`N_PERM ∈ {1000, 5000}` and across the FWER band {0.025, 0.05, 0.10}. Provisional disposition:
**`NOT_ADMITTED (NON-BINDING)`**. The experiment verdict is **`SCREEN_DELIVERED`** — every statistic was
produced deterministically with reconciliation, causal construction, and the holdout fence all intact
(audit PASS, 0 Critical). Cross-sectional relative strength was the programme's a-priori mechanism
favourite (the one information axis never varied); on this screen it **earns no admission**.

## Detailed Findings

### 1. The axis does not beat random — and the result is homogeneous across strata

- **Observation:** `S_X = 1` of a possible 46 powered cells; `S* = 1` (Q95 of the joint max-statistic
  null); axis perm-p `= 0.323`. Only **2 of 92** cell-reads beat random.
- **Per-stratum (domain × primitive), disclosure — LESSON-001:**

  | Domain | primitive | cells | beats | mean Δ̂ (ATR) | cells Δ̂ > 0 |
  |--------|-----------|-------|-------|---------------|--------------|
  | 15m | COND-XSRANK | 16 | 0 | −0.279 | 2/16 |
  | 15m | COND-XSDIV  | 16 | 0 | −0.244 | 2/16 |
  | 1h  | COND-XSRANK | 16 | 0 | −0.152 | 5/16 |
  | 1h  | COND-XSDIV  | 16 | 0 | −0.140 | 5/16 |
  | 4h  | COND-XSRANK | 14 | 1 | −0.024 | 6/14 |
  | 4h  | COND-XSDIV  | 14 | 1 | +0.084 | 8/14 |

- **Interpretation:** the pooled headline is **not masking heterogeneity** (audit verdict forensics
  confirm). The picture is uniformly negative: cross-sectional conditioning gives no favourable-excursion
  advantage at any domain, and at the fast domains (15m, 1h) it *degrades* it — the conditioned median
  favourable MFE is materially **below** the direction-matched random median. There is no hidden stratum
  that separates; if anything `S_X = 1` is generous to the axis.

### 2. The two "beats" are small-cell multiplicity artefacts, correctly absorbed by the gate

- **Observation:** the only two cells that clear the per-cell one-sided lower bound are the two smallest
  4h cells: GBPUSD-4h COND-XSRANK (Δ̂ = 1.19 ATR, ci_low = 0.0235, `n_cond = 353`) and NZDUSD-4h
  COND-XSDIV (Δ̂ = 0.54 ATR, ci_low = 0.0234, `n_cond = 450`). Both lower bounds sit *barely* above zero.
- **Evidence:** `axis_admission.json`, `cell_availability.csv`; plot `01_delta_favourable.png` (boxed
  cells), `04_beats_vs_band.png`.
- **Interpretation:** these are exactly the few-events-per-cell regime where ranking-over-16-instruments
  manufactures lucky cells — the multiplicity caution the scope flagged as load-bearing for this axis. The
  joint permuted-axis null reproduces the same `S* = 1` ceiling, so the gate does **not** credit them
  (`S_X = 1 ≤ S* = 1`). This is the D2b control working as designed: a lucky single cell does not admit the
  axis.

### 3. Mechanism — why cross-sectional extremes carry no favourable continuation

- **Observation / interpretation:** a decile event fires only **after** the trailing 20-bar relative move
  has already occurred, so the conditioned entry buys late into relative strength / sells late into
  relative weakness. Over the subsequent adaptive-cap window the relative-strength extreme does not extend
  favourably more than a direction-matched random clock — and at intraday speed it does slightly worse.
  This is consistent with **short-horizon mean-reversion / exhaustion of intraday cross-sectional
  momentum**: the information is spent by the time the rank crystallises. This is a genuine *absence* of
  directional-favourable continuation, not a single binding leg or cell the gate vetoed.
- **Evidence:** plot `03_mfe_examples.png` (conditioned vs random favourable-MFE distributions, densest
  cells); the per-domain mean Δ̂ progression (−0.26 → −0.15 → ≈0 from 15m to 4h) in Finding 1.

### 4. Gate is shape-appropriate and unsaturated

- **Observation:** Screen X's endpoint is a **location** read (median favourable MFE, directional by
  construction — D3.X; no tail/bimodal/magnitude-budget split). The binding gate measures a location
  effect. Max attainable `S = 46` (all cells powered); `S* = 1 ≪ 46`, so the no-power `INCONCLUSIVE`
  branch does not trigger and the statistic retains full 0–46 dynamic range.
- **Interpretation:** there is no effect of a shape this gate could be blind to. `S_X = 1` lands at the
  Q95 null ceiling because the signal is genuinely absent — a true **"no effect"**, correctly distinguished
  from "an effect the gate cannot see." Plot `02_permuted_axis_null.png` shows the realized `S_X` buried in
  the null mass.

## Hypothesis Verdict

**Experiment verdict: `SCREEN_DELIVERED`.** For both primitives across all 46 member cells, the per-cell
`MFE_med` Δ-over-random table, per-cell beats-random tests, the two sub-screen `S`/`S*`/perm-p, the axis
`S_X`/`S*`/`p_X`, the FWER band, the MC-stability table, and the descriptive D2a band were all produced
deterministically; determinism (metrics + permutation stream), matched-random count + direction-mix
reconciliation, and causal forward-fill all hold; the holdout was never touched
(`counted_test_reads = 0`).

**Provisional single-axis disposition (NON-BINDING): `NOT_ADMITTED`.** `S_X = 1 ≤ S* = 1` and
axis perm-p `= 0.323 > 0.05`, on every FWER level in the band and at both `N_PERM` scales.

**`NOT_ADMITTED` is distinct from `EXONERATED` — state precisely for G-019.** The scope's provisional
`EXONERATED` requires every sub-screen's `S` to fall **inside** the D2a coin-flip null band [17, 28]
(price-derived information behaving like a fair coin). Here `S = 1` for both primitives falls **far below**
the band — the axis is provisionally **dead-by-absence** (it underperforms even the coin-flip baseline),
not exonerated-by-coin-flip. **What G-019 reads from EXP-087:** the axis permutation p-values
(`COND-XSRANK` 0.113, `COND-XSDIV` 0.236; axis max-stat 0.323) and the ranking z (1.26) enter the
cross-axis Holm step-down over {M, X, (F)}; the Holm adjustment can only *raise* these p-values, so no
post-adjustment admission is reachable from `S_X = 1`. The descriptive **below-band** placement is the
terminal-branch input the G-019 rubric uses to characterise the cross-sectional × directional cell of the
availability 2×2.

## Limitations

- **TRAIN-only, gross, availability-only.** No exit, barrier, target, stop, portfolio, or market-neutral
  construction — those are deferred to a family's own post-admission G0/D0. This screen measures *gross
  directional-favourable availability*, not net tradability. A `NOT_ADMITTED` here closes the cheap
  availability question, not a fully-built strategy.
- **Frozen conditioning, by design.** Lookback 20, both-tail deciles, `MIN_XS_INSTR = 8`, forward-filled
  union grid, and the matched-random/permutation construction are frozen (D0-amendment-002). The screen
  tests *these* cross-sectional primitives; it does not sweep lookbacks or alternative basket definitions
  (a sweep would be a separate scoped experiment, not an extension).
- **Provisional, not binding.** The binding admit/exonerate is G-019. EXP-087 contributes statistics only.
- **Audit Info notes (non-material):** the provisional-disposition *string* inherits a stale `S_M` label
  from the frozen EXP-086 gate module (binding JSON fields are correctly labelled `S_X`); `causal_fill_ok`
  is a statically-true constant justified by the searchsorted construction. Neither moves any
  verdict-bearing number.

## Alternative Explanations

- **Could the absence be a power problem?** No — all 46 cells are powered (smallest `n_cond = 274`), the
  gate is unsaturated (`S* = 1 ≪ 46` attainable), and the no-power `INCONCLUSIVE` branch did not trigger.
  The screen had ample power to detect a real cross-sectional availability edge; it found none.
- **Could the wrong direction convention be hiding an edge?** The conditioned and random sets share the
  identical per-cell LONG/SHORT mix (exact `long_frac == ctrl_long_frac` on all 92 cells), so Δ isolates
  *conditioning/timing*, not direction. A direction artefact cannot explain the null.
- **Could a longer lookback or a different basket carry continuation?** Possible but out of scope; the
  mechanism (late entry after the move) suggests timing, not the specific basket definition, is the binding
  problem — see Next Steps.

## Recommended Next Steps

1. **G-019 adjudication (already scheduled, binding).** Feed EXP-087's axis perm-p and ranking z into the
   cross-axis Holm step-down over {M, X, (F)}. No new experiment required.
2. **(New scope, only if the slate warrants it) Cross-sectional *reversion* availability.** The mechanism
   here (extremes don't *continue*) is the dual of a reversion read: a separate scoped experiment could test
   whether *fading* the cross-sectional decile (entering against the relative move) shows favourable
   availability. This is a different hypothesis and a different family — it must open its own G0/D0 and is
   **not** an extension of EXP-087.
3. **Programme note (for the retrospective, not an experiment):** with Screen M (EXP-086) and Screen X
   (EXP-087) both failing to admit, the family-selection slate's evidence points toward price-derived
   information — single-series geometry *and* cross-sectional relational — being exhausted on this dataset;
   G-019 formalises this against the frozen D5 rule.
