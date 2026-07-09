# SPDR-003 — Screen summary (HTF context on CTRL-03 naive-reversion LTF limit entries)

> **CORRECTION 2026-07-08 (post-audit).** Statistics in this summary that rely on the screen's
> original CI machinery are superseded where they conflict with the corrected `analysis.md` and the
> Phase-010 checkpoint `correction/` (hold-matched blocks; SPDR-003 estimand relabel). This file is
> subordinate to `analysis.md`; read that first.

**Lane:** SPDR speed-run leg 3/3 (FINAL, TRAIN-only). Design: `design.md`.
**No disposition** — after this leg the operator takes the combined CTRL-01/02/03 series verdict.
This file is a **neutral factual record of the stage-3 screen only**; the binding read is the
fresh-context stage-5 analyst pass (`analysis.md`, pending), reported base-conditional + granular
per-stratum + quantify-not-qualify. Analysed independently of the other legs.

## What ran

- Signal: naive reversion trailing limit — buy at min(Low[t-3..t-1]), sell at max(High[t-3..t-1]);
  trailing (re-placed each bar), so each LTF bar is a fill opportunity at its own 3-bar extreme.
- **Causal m1 fill sim (the new/heavy piece):** the touch is resolved on the LTF bar's own
  1-minute base bars — buy fills at the first m1 with Low ≤ limit; fill price = limit if the m1
  Opened above it, else the m1 Open (gap-through, conservative). H measured **from the fill bar**;
  HTF context anchored at the **fill** bar's open (B-4). Causal machinery otherwise reused from the
  SPDR-001 primitives (HTF-bar-boundary, Wilder ADX/±DI, ATR regime).
- Grid: 4-core × {1d/1h, 4h/1h, 1h/5min} × holds {1–4}×ratio × 20 variants = **960 cells**. TRAIN
  block (first 49%). `none` = unfiltered reversion baseline; DI = HTF-direction confirmation; gating
  = HTF regime subset. Every variant is a real test.
- Controls emitted per HTF cell: (A) lift vs unfiltered baseline + `baseline_admit_frac`;
  (B) matched-random-timing limit twin using the same fill outcomes (`rand_twin_*`, 25 seeds);
  (C) HTF phase-shift on DI arms (`phaseshift_*`).
- **Integrity: all-pass 12/12** (`results/integrity.json`) — TRAIN fence, HTF-bar-boundary, causal
  signal + m1 fill, seed battery, golden trace.

## Facts (coarse — full CI/power/facets are stage-5)

- **Fill-rate 0.54–0.63** of bars across instruments/domains (a 3-bar-extreme touch is frequent).
- Emission schema (`results/cells.parquet`): per cell — n, mean, std, hitrate, ci, mde, trimmed,
  baseline_admit_frac, lift, lift_ci, rand_twin_mean/ci, phaseshift_mean/ci_low.
- Stage-3 CI is deliberately coarse (n_boot 2000 × 2 seeds; lift CI = conservative independent-arm
  combination). No counts or interpretation reported here — the stage-5 analyst re-derives per
  stratum under the base-conditional frame (Facet A base-failure + Facet B HTF-conditional-effect).

## Stage-5 analysis

> Pending — fresh-context data-analyst quantification (`analysis.md`), blind of other legs,
> base-conditional + granular per-stratum + quantify-not-qualify.

## Operator disposition

> Deferred to the combined CTRL-01/02/03 series verdict (after this leg).
