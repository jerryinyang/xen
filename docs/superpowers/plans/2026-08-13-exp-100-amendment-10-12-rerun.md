# EXP-100 AMENDMENT-10/11/12 rerun

Operator 2026-08-13. Full TRAIN matrix after three amendments.

## Amendments

10. Previous 1D/1W = America/New_York 17:00 trading day / Mon–Fri week.
    15m/1H/4H StreamingOHLC unchanged. No synthetic minutes.
11. Rolling windows 7 / 14 / 22 / 252. Matrix 264 cells.
12. Tight if `gap_span < 0.50 * VA_width`. Gap selection stays the emptiest
    30% of VA TPO.

Ledger after: **1 looser / 3 tighter / 7 neutral**.

## Launch

```text
cd python
PYTHONPATH=src .venv/bin/python experiments/EXP-100/code/run_matrix.py \
  --mode full --workers 6 --timeout-seconds 21600
```

TRAIN only. Fence INFR-021. Zero-cost. No TEST/holdout.
