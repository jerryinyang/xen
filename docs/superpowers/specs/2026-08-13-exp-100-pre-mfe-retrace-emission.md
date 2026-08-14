# EXP-100 pre-MFE retracement emission

**Authorised:** 2026-08-13 by the operator

## Purpose

Add one forward raid-emission column that lets a later experiment test whether a
confirmed favourable sweep revisits its completed TPO value area or selected value-gap
box before reaching its terminal maximum favourable excursion (MFE). This is measurement
support only; it does not answer or add that downstream hypothesis to EXP-100.

## Column contract

`pre_mfe_retrace` is one nullable Arrow struct on `raids.parquet`:

```text
struct<price: float64, status: string>
```

- Clock: strictly after `confirmation_ts_ns` and through the 1-minute bar that establishes
  the terminal post-confirmation MFE; the completed endpoint-reference bar does not add a
  synthetic observation.
- HIGH-side sweep (favourable move down): `price` is the greatest real 1-minute high seen
  before the terminal-MFE bar.
- LOW-side sweep (favourable move up): `price` is the least real 1-minute low seen before
  the terminal-MFE bar.
- Confirmation close is the starting price. The confirmation reference bar's earlier
  intrabar high/low is not treated as post-confirmation path.
- When the terminal-MFE 1-minute bar also extends the retracement extreme, OHLC cannot
  establish which occurred first. Emit that bar's possible retracement price with
  `status=AMBIGUOUS_SAME_BAR`.
- Otherwise emit `status=DEFINED`.
- If no post-confirmation source bar establishes a favourable extreme beyond confirmation
  price, emit the confirmation price with `status=NO_POST_CONFIRMATION_MFE`.
- Raids without primary favourable-sweep confirmation emit null.

The downstream experiment joins `raids.parquet` to `tpo_profiles.parquet` by `raid_id` and
compares the side-aware retracement price with `VAL`/`VAH` or the selected `gap_mask` bounds.
Ambiguous rows are reported separately and never silently counted as touch or no-touch.

## Online algorithm

Per confirmed primary raid, retain only four scalar state values: confirmation price,
running post-confirmation MFE, running adverse extreme, and the current emitted struct.
On a new MFE bar, snapshot the adverse extreme from prior bars. If that same bar extends
the adverse extreme too, use its adverse extreme and mark the snapshot ambiguous. Then
include the bar in running state for any later MFE. A later MFE therefore resolves an older
same-bar ambiguity because the whole older bar is known to precede it.

## Verification

- HIGH- and LOW-side symmetric unit traces.
- Same-minute MFE/retracement extension emits `AMBIGUOUS_SAME_BAR`.
- A later MFE converts the earlier bar into an unambiguous prior observation.
- Non-primary/unconfirmed raids emit null.
- Parquet schema retains the single struct column.
- Existing EXP-100 tests, full repository tests, lint, matrix integrity gates, and fresh
  EXP-100 analysis all pass before completion is claimed.
