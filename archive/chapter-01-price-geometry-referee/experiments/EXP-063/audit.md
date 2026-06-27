# Audit — EXP-063 (dual-object re-run)

**Scope:** validate `code/run_experiment.py` and the regenerated `results/` for the dual-object
adverse-geometry + mean-investigation re-run under D0 Amendment 001.
**Verdict: PASS** (0 Critical, 0 Major).

## Integrity gates (from `run_metadata.json` / `reconciliation.csv`)

| Gate | Result |
|------|--------|
| `is_defect` | **False** |
| Determinism (first-usable-cell replay, every object × variant × {signal,null} + contrasts) | **PASS** — `non_deterministic: []` |
| Causality (`_causality_ok` MA end ≤ entry, entry ≤ t_i, faded-span start ≤ entry, **ZigZag** end ≤ entry) | **PASS** — `causality_violations: []` |
| Structural invariants (per object: V-RAW ≤ V-RR1; V-NONE 0 ADV; weights sum 1.0; matched-count) | **PASS** — `invariant_violations: []` |
| Reconciliation vs EXP-061 (P12, both objects) | **PASS** — 99/99 checked, all `consistent=true`, `exp061_mismatch: []` |
| EXP-062 L2→L3 tail cross-check available | **True** (disclosed, not a hard gate) |

**Reconciliation spot-check (exact):** native `V-BENCH` reproduces EXP-061 `M0` — BTCUSD-5m m=10667,
median 0.055249410758157674 (identical to anchor); hybrid `V-BENCH` reproduces EXP-061 `H0` — BTCUSD-5m
m=3044, median −0.053125795483862495 (identical). Both per-object anchors matched on every checked cell;
the dual-object median paths are the audited EXP-061 populations.

## Code correctness

- **Holdout fence:** F01 prefix loader; full file never sorted/collected; domain bars fenced; forward scans
  clipped → `DATA_CENSORED`. TEST + holdout untouched.
- **Dual-object separation:** `_resolve_objects` loops `OBJECTS=(nat,hyb)`; native conditions on the
  MA-segment mask, hybrid on the new `_zz_context` ZigZag mask (`generate_zigzag` + `move_arrays` +
  `live_strong_stat`, mirroring EXP-061 H0). Both score on the **shared** MA geometry (`rd`/`M_sofar`/fav/
  cap/`ma_start_idx`); only the conditioning mask differs. Per-object nulls matched to each object's count,
  excluding that object's own entries, disjoint RNG (native existing/≥210000; hybrid H0/RH0 + ≥310000).
  Per-object `var_rm`/recovery/paired; per-object composition; **no pooling**. Verified.
- **`/ADV-EXTREME` causality (P7 Q5):** faded extreme over `[ma_start_idx+1 … entry_idx]` from the MA
  in-progress `start_epoch`; the new hybrid causality leg asserts ZigZag references end ≤ entry.
- **Real-price discipline:** detection on HA candles; all metrics on real OHLC; MA on real close.
- **Determinism / RNG:** native V-BENCH reuses M0/RM0 purposes, hybrid V-BENCH reuses H0/RH0 purposes
  (reproduce their anchors); all other (object, variant) + nulls use fresh disjoint blocks. Byte-identical
  across `--workers`.
- **Zero-baseline:** `< 30` → NOT_VIABLE-by-power; tail-share finite (0.0 on no negative mass); recovery
  contrast NaN when an arm unpowered (disclosed); V-NONE degenerate `r` caveat documented.

## Numerical findings (validated, not interpreted here)

- **Native = EVIDENCE_FOR:** bounded V-BENCH generalises 8/99 (P11+P6 True), V-RR1 9/99 (True); both beat
  their own RM. **mean_viable composes** for the bounded variants (raw-mean CI_low > 0 in a composing set);
  but **recovery_positive = 0/99** for every bounded variant.
- **The mean structure (the decisive §4 read):** native V-NONE raw-mean median −0.058 ATR but **10%-trimmed
  +0.422 ATR** with worst-5% tail-share 0.356 — the negativity is a thin catastrophic *left* tail (the
  EXP-060B uncapped downside). Bounded V-BENCH raw-mean median +0.0065, trimmed −0.018: the stop truncates
  the left tail (raw mean no longer dragged negative) but the centre is ≈ 0; the recovery *contrast*
  `mean(bounded) − mean(/ADV-NONE)` is null (0/99) because /ADV-NONE's raw mean is only marginally below.
- **Hybrid = EVIDENCE_AGAINST:** V-RR1 median-viable in 90/99 cells but **beats_rm in 0** → generalises 1/99
  (P11 False); V-BENCH generalises 1/99. The hybrid median viability is **not** signal-attributable
  (random-in-regime matches it), consistent with EXP-061's hybrid finding.

```text
AUDIT VERDICT: PASS
```
