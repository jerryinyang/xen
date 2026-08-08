---
name: frozen-suite-floors
description: Frozen per-domain MDE floors for the three referee components; never retune after seeing a candidate
metadata: { type: reference, chapter: 01 }
---
> **SUPERSEDED-FOR-LIVE-USE (INFR-022, 2026-08-08).** The frozen per-domain MDE floors are historical chapter-01/02 apparatus (L-63): not live value-path gates. Keep as calibration history; never re-derive or re-apply. Live instruction:
> zero-cost model (`NO_COST_CHARGED`) + sample-size context + direct baseline comparison +
> PSR (`docs/references/neutrality-standard.md`; lessons L-62..L-65; plan
> `docs/superpowers/plans/2026-08-08-infr-022-zero-cost-neutrality-psr-pipeline-update.md`).


Frozen detection floors (bps), 5m / 1h / 4h:
- Strict 5-check gate stack (EXP-003/005): 1 / 4 / 12
- Ratified-loose referee (EXP-011/012): 0.5 / 2 / 8
- Revised portfolio-fitness unit (EXP-018): 12 / 16 / 32

L5 materiality is the binding, α-invariant leg. Per-instrument MDEs can be lower than pooled
(EXP-008). Do not retune thresholds/losses/costs/denominators/pass-logic after seeing a
candidate outcome. Detail: [[../evaluation-framework]].
