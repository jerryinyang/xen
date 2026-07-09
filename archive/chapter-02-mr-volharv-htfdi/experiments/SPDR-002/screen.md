# SPDR-002 — Screen summary (HTF context on CTRL-02 naive-momentum LTF entries)

> **CORRECTION 2026-07-08 (post-audit).** Statistics in this summary that rely on the screen's
> original CI machinery are superseded where they conflict with the corrected `analysis.md` and the
> Phase-010 checkpoint `correction/` (hold-matched blocks; SPDR-003 estimand relabel). This file is
> subordinate to `analysis.md`; read that first.

**Lane:** SPDR speed-run leg 2/3 (TRAIN-only availability quantification). Design: `design.md`.
**No disposition** — deferred to the post-SPDR-003 series verdict. This file is a **neutral
factual record of the stage-3 screen only**; the binding quantitative read is the fresh-context
stage-5 analyst pass (`analysis.md`, pending). Analysed independently of other legs.

## What ran

- Signal: naive momentum breakout of the prior 3 LTF bars (causal, confirmed on closed bar t-1,
  acted at Open(t)), open-to-open ATR-normalised forward return over hold H. Full causal machinery
  reused from the SPDR-001 primitives (HTF-bar-boundary anti-lookahead, Wilder ADX/±DI, ATR regime).
- Grid: 4-core × {1d/1h, 4h/1h, 1h/5min} × holds {1–4}×ratio × 20 filter variants = **960 cells**.
  TRAIN block (first 49%). `none` = unfiltered-momentum baseline; DI = HTF-direction confirmation;
  gating = HTF regime subset. Every variant is a real test (informative signal).
- Controls emitted per HTF cell: (A) lift vs unfiltered baseline + `baseline_admit_frac`;
  (B) matched-random-timing seed battery (`rand_twin_*`, 25 seeds); (C) HTF phase-shift on DI arms
  (`phaseshift_*`).
- **Integrity: all-pass 12/12** (`results/integrity.json`) — TRAIN fence, HTF-bar-boundary, causal
  breakout, seed battery, golden trace.

## Facts (coarse — full CI/power is stage-5)

- Breakout rate 0.25–0.32 of bars across instruments/domains.
- Stage-3 CI is deliberately coarse (n_boot 2000 × 2 seeds; lift CI = conservative independent-arm
  combination). Under it, of 912 HTF cells: **46 lift-CI excludes zero positive, 2 negative** —
  *not* a finding, just a pre-analysis count; the stage-5 analyst re-derives with the proper
  seed battery, block sensitivity, dose-response, heterogeneity, and power.
- Emission schema (`results/cells.parquet`): per cell — n, mean, std, hitrate, ci, mde, trimmed,
  baseline_admit_frac, lift, lift_ci, rand_twin_mean/ci, phaseshift_mean/ci_low.

## Stage-5 analysis

> Pending — fresh-context data-analyst quantification (`analysis.md`), blind of other legs.
> Quantify the magnitude and shape of what HTF context does to the momentum outcome distribution.

## Operator disposition

> Deferred to the post-SPDR-003 series verdict.
