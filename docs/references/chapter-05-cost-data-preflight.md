# Chapter 05 Cost/Data Preflight

> **HISTORICAL (chapter-05) — not binding on the live programme after INFR-022 (2026-08-08).**
> INFR-022 retired the cost model programme-wide (zero-cost, `NO_COST_CHARGED`): the
> no-spread amendment, `PARTIAL_FEES_FUNDING_ONLY` scope, and fee/funding injection below are
> superseded-for-live-use. Do not use this document as cost policy. Body retained verbatim
> for reproducibility.

**State:** `COMPLETE / NO-SPREAD AMENDMENT QA APPROVED`

**Scope:** bounded infrastructure correction required by
[`chapter-05-governance.md`](chapter-05-governance.md) §2. No family, event census, outcome,
historical TEST, or holdout data was created, loaded, or read.

## Clause-to-evidence map

| Governance requirement | Implementation | Focused evidence |
|---|---|---|
| Stress once; available components reconcile | `xen.evaluation.bybit_round_trip_cost_bps` stresses fee and funding once, then sums them; spread is `None`, not zero | `test_bybit_cost_components_reconcile_with_stress_applied_once` at 0.5/1/2 |
| Reject invalid spread | `xen.evaluation.t1_round_trip_spread_bps` rejects negative and non-finite input | `test_t1_round_trip_spread_rejects_invalid_input` |
| Discrete four-hour funding | `count_bybit_funding_stamps` counts 00:00/08:00/16:00 UTC timestamps in `(entry, exit]`; `funding_stamps=` selects discrete cost | four boundary cases plus charged/uncharged cost cases |
| Regression coverage | `python/tests/test_evaluation.py`; `python/tests/test_chapter05_preflight.py` | focused suite |
| Correct references | `dataset-reference.md`; `architecture.md` | stored field defined as mean-price skew, no tick floor, never a cost input |
| Quarantine actual carrier | `xen.sigbar.access.quarantine_mean_price_skew` handles staging `SpreadBps` and signed-catalog `spread_feature` | both storage names tested |
| Preserve bytes; expose accurate name/status | adapter returns `MeanPriceSkewBps` and `MeanPriceSkewStatus=UNUSABLE_AS_SPREAD`; input frame remains unchanged | value/name/status test |
| Verify quarantine decision | `verify_chapter05_spread_quarantine` recomputes the INFR-017 self-hash and verifies the stored field remains pinned `UNUSABLE` | genuine artifact passes; tampered artifact fails; no cost pins are exposed |

## Frozen process-start contract

Every Chapter-05 Run 1 or Run 2 process must call `verify_chapter05_spread_quarantine()` before
reading the legacy field. It verifies INFR-017 self-pin
`e3b9fd9b9b5851b8a9a11f9ce34cd1e0fa8e10ea1fe1b210bd0090da379e6225` and the `UNUSABLE`
decision only. It exposes no spread or cost pins.

## Economic identity

For the fixed four-hour episode:

```text
reported_cost = stress × (11.0 bps fee + discrete funding)
reported_net = gross - reported_cost - execution allowance
```

**Spread cost unavailable and not charged.** `spread_rt_bps` is `None`, never `0`; the returned
scope is `PARTIAL_FEES_FUNDING_ONLY`. The reported cost understates total cost and reported net
performance is overstated. Every strategy report must carry that caveat and may not claim fully
net, cost-complete, tradable, or deployable performance from this accounting.

## Compatibility boundary

- Archived staging and signed-catalog bytes are unchanged.
- `SignedBar.spread_feature` remains only as the byte-compatible legacy storage field.
- Analytical consumers must use `quarantine_mean_price_skew`; direct costing from either legacy
  storage name is prohibited.
- Legacy callers may still use continuous funding accrual when `funding_stamps` is absent.
  Chapter 05 must provide the counted value and assert `funding_method == DISCRETE_STAMPS`.

## Verification record

- Focused: `53 passed`.
- Full retained suite: `224 passed, 4 skipped`; one pre-existing NumPy warning in the synthetic
  XENA search test.
- Fresh-context compliance review of the no-spread amendment: **APPROVE**, run 10 in
  [`chapter-05-cost-data-preflight-qa.md`](chapter-05-cost-data-preflight-qa.md).
