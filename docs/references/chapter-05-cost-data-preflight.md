# Chapter 05 Cost/Data Preflight

**State:** `COMPLETE / FRESH QA APPROVED`

**Scope:** bounded infrastructure correction required by
[`chapter-05-governance.md`](chapter-05-governance.md) §2. No family, event census, outcome,
historical TEST, or holdout data was created, loaded, or read.

## Clause-to-evidence map

| Governance requirement | Implementation | Focused evidence |
|---|---|---|
| Stress once; components reconcile | `xen.evaluation.bybit_round_trip_cost_bps` stresses fee, spread and funding once, then sums the returned components | `test_bybit_cost_components_reconcile_with_stress_applied_once` at 0.5/1/2 |
| Reject invalid spread | `xen.evaluation.t1_round_trip_spread_bps` rejects negative and non-finite input | `test_t1_round_trip_spread_rejects_invalid_input` |
| Discrete four-hour funding | `count_bybit_funding_stamps` counts 00:00/08:00/16:00 UTC timestamps in `(entry, exit]`; `funding_stamps=` selects discrete cost | four boundary cases plus charged/uncharged cost cases |
| Regression coverage | `python/tests/test_evaluation.py`; `python/tests/test_chapter05_preflight.py` | focused suite |
| Correct references | `dataset-reference.md`; `architecture.md` | stored field defined as mean-price skew, no tick floor, never a cost input |
| Quarantine actual carrier | `xen.sigbar.access.quarantine_mean_price_skew` handles staging `SpreadBps` and signed-catalog `spread_feature` | both storage names tested |
| Preserve bytes; expose accurate name/status | adapter returns `MeanPriceSkewBps` and `MeanPriceSkewStatus=UNUSABLE_AS_SPREAD`; input frame remains unchanged | value/name/status test |
| Verify five cost pins | `load_chapter05_cost_pins` recomputes INFR-017 self-hash, checks frozen hash/status, derives `max(flip median, one tick)`, and matches the five rounded binding pins | genuine artifact passes; tampered artifact fails |

## Frozen process-start contract

Every Chapter-05 Run 1 or Run 2 process must call `load_chapter05_cost_pins()` before reading
events or constructing costs. Failure, hash mismatch, status drift, missing symbol, or pin mismatch
aborts the process. The returned binding round-trip spread pins are:

| Symbol | bps |
|---|---:|
| BTCUSDT | 0.244 |
| ETHUSDT | 0.305 |
| SOLUSDT | 0.727 |
| DOGEUSDT | 1.477 |
| XRPUSDT | 1.965 |

Source: archived INFR-017 `column_pins.json`, self-pin
`e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225`.
The binding value is `round(max(flip_median_bps, one_tick_bps), 3)`. It is a conservative upper bound
for the cost floor, not a quoted or executable spread: adjacent aggressor-side flips include
real price movement, and INFR-017 validated this reconstruction on only 20 symbol-days.

## Economic identity

For the fixed four-hour episode:

```text
pre_allowance_cost = stress × (11.0 bps fee + pinned spread + discrete funding)
economic_net = gross - pre_allowance_cost - execution allowance
```

Returned fee, spread and funding components already include `stress` and sum to `total_bps`.
The execution allowance remains separate. `3 × spread` is a resolution diagnostic through
`spread_scale_route`; it is never added to trading cost.

## Compatibility boundary

- Archived staging and signed-catalog bytes are unchanged.
- `SignedBar.spread_feature` remains only as the byte-compatible legacy storage field.
- Analytical consumers must use `quarantine_mean_price_skew`; direct costing from either legacy
  storage name is prohibited.
- Legacy callers may still use continuous funding accrual when `funding_stamps` is absent.
  Chapter 05 must provide the counted value and assert `funding_method == DISCRETE_STAMPS`.

## Verification record

- Focused: `51 passed`.
- Full retained suite: `222 passed, 4 skipped`; one pre-existing NumPy warning in the synthetic
  XENA search test.
- Fresh-context compliance review: **APPROVE**, run 5 in
  [`chapter-05-cost-data-preflight-qa.md`](chapter-05-cost-data-preflight-qa.md).
