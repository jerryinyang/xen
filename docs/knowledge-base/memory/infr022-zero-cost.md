---
name: infr022-zero-cost
description: INFR-022 zero-cost model: no spread/commission/swap in any calculation; caveat on every report
metadata: { type: lesson, chapter: 6 }
---
Operator directive INFR-022 (2026-08-08), lesson L-62: the programme runs the zero-cost model
(`NO_COST_CHARGED`) — no spread, commission, or swap enters any calculation in any experiment
type unless an explicit operator cost directive (recorded in design.md + `operator_cost_directive.json`)
requests costs. `cost_bps == 0` is a compliant pin; the retired stack lives in
`xen/evaluation_cost_legacy.py` (ARCHIVED banner). Every money-bearing artifact carries the
ZERO-COST-DISCLOSURE caveat verbatim. "Zero" is a model, never a measured zero.
