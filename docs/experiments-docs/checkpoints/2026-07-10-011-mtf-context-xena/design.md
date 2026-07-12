# Checkpoint 011 — MTF Context Filters via XENA (Chapter 03, Phase 1)

**Opened:** 2026-07-10 · **Container for:** XENA-001, XENA-002, XENA-003 (first live XENA
universes) + first-live-universe infrastructure (C# batch runner, permutation-null battery).
**Family group:** `docs/signal-registry/candidate-families/cf-mtfctx-001.md` (REGISTERED).
**Lane:** XENA (default route, INFR-006). Frozen registry v3, sha256 `537d691a…e672a6`.

## Objectives

1. Exercise the full XENA lane end-to-end on real emissions for the first time.
2. Adjudicate the CF-MTFCTX-001 idea (HTF context filters on naive LTF controls) at the
   portfolio level — selection outcomes are the thesis read; no A/B claim.
3. Deliver the two INFR-006 leftovers that were blocked on a real candidate:
   - **C# batch manifest runner** — sweeps one universe manifest (model × params ×
     instrument × domain) through cTrader emissions.
   - **Permutation-null battery** — permutes the real emitted trade streams of the first
     universe (causal alignment-breaking, not P&L permutation — L-14/EXP-012).

## Planned runs (sequential; XENA-001 first, gated)

| Run | Universe | Model | N cands | Status |
|---|---|---|---|---|
| XENA-001 | MTFCTX-C1 | CTRL-01 RANDOM (lambda=2) | 2,736 | QA APPROVE ×2 (design run 3, post-impl run 4, 2026-07-11); model+conf+manifest built, smoke verified; AWAITING operator execution approval |
| XENA-002 | MTFCTX-C2 | CTRL-02 NAIVE MOMENTUM | 2,736 | QA APPROVE ×2 (design run 1, post-impl run 2, 2026-07-11); model+conf+manifest built, smoke verified; execution blocked on XENA-001 retro read + operator approval |
| XENA-003 | MTFCTX-C3 | CTRL-03 NAIVE REVERSION (native limit orders, m1 fills) | 2,736 | QA APPROVE ×2 (design run 1, post-impl run 2 w/ golden trace, 2026-07-11); NativeOrders mode + model + conf + manifest built, smoke verified (76/76 candidate gate); AWAITING operator execution approval |

Order rationale: CTRL-01 (random) doubles as the live-data null exercise for the lane and
the permutation-battery substrate; CTRL-03 last (native-order harness risk isolated).

## Per-run pipeline (xena-lane.md)

```
design (quant-designer: manifest, band pin, unit pin L-21, seed pin, stop k)
  → ledger row in xena-runs.md (registration-before-search)
  → QA pre-exec (fresh context) → [OPERATOR execution approval]
  → batch emission (C# runner) → candidate gate (BLOCKING, SlPrice)
  → LAHC search ×10–15 restarts (search band only)
  → certify_and_rank (registry_path mandatory) → [OPERATOR reviews evidence package]
  → counted final gate (cap 2; gross binding, net informational) → [OPERATOR verdict]
```

## Mandatory design.md blocks (each run)

- **L-21 unit pin:** ATR units, bps conversions, `cost_bps`, `money_per_unit` per
  instrument (indices + XAUUSD + BTCUSD are non-trivial pins — v1 default 1.0 is
  USD-quote-only).
- **Band pin:** exact ns `SegmentLayout.from_span` 50/30/20 boundaries over the common
  analysis span (start 2021-06-02; end = min over instruments of the per-file 70%
  analysis-set cutoff — never end-of-file); per-instrument holdout fences listed;
  pre-registered before any search.
- **Vol-regime pin:** median-TR ATR(14); percentile-rank window exact value in [200, 300]
  HTF bars; hysteresis HIGH >P80/<P65, LOW <P20/>P35, MID otherwise (cf-mtfctx-001
  appendix spec) — pinned before search, never tuned on outcomes.
- **Feature causality:** all HTF features from confirmed HTF bars, ≤ t−1, timestamp-aligned
  (`CloseTime`), never bar indices.
- **Sizing stop:** k × HTF median-TR ATR(14) synthetic `SlPrice`, sizing-only — finite
  per-leg field as sizing denominator; NO live stop orders in this family; k pinned.
- **CTRL-03 profit-exit spec:** any LTF close in profit ≥ 0.5 × current HTF median-TR
  ATR(14) (latest confirmed HTF bar) from entry → close; distance floats, not
  entry-frozen; no adverse target.
- **CTRL-01 seed pin:** per-candidate fixed seeds, regenerable (L-19 D1).
- **From-scratch clause:** no reuse of prior model-specific implementations.

## Success criteria

- Phase succeeds by producing clean adjudications, not passes: each run ends with an
  operator-signed outcome row (eval_count + distinct_subsets mandatory) regardless of
  gate result.
- Infra deliverables: batch runner reusable for any future manifest; permutation-null
  battery report on MTFCTX-C1 emissions.
- Failed gross gates are negative results; no threshold revision (L-23), no re-search on
  gate segments.

## Constraints carried in

P-14 escape-clause conditions (≥10× capture vehicle, L-21 pin) · L-22 gross ≠ deployability ·
gate ledger cap 2/universe, attestation operator-only · holdout untouched · pooled figures
disclosure-only · universe status transitions only at this checkpoint's retrospective,
operator-signed.
