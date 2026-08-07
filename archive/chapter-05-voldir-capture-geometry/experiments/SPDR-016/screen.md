# SPDR-016 — Screen (START-GATE SKIP)

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D3` (O3 Group 3)
- **Lane:** SPDR TRAIN-only · 0 TEST reads · no XENA · no family status change
- **Status:** **SKIP — start gate failed (no named residual to refine)**
- **Pin:** `results/014_residual_pin.json` (copy of SPDR-014)

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY
  implication: n/a — no money path emitted
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

## Start gate (HARD)

| Check | Value | Pass? |
|---|---|---|
| Pin loaded | yes | yes |
| `016_start_allowed` | true (`OPERATOR_OVERRIDE`) | yes (shell open) |
| `residual_status` | **NONE** (0 powered cells) | **no** — nothing named to refine |
| `policy_for_016` | **NONE** (DEFERRED) | **no** — not in {{P-MR, P-MOMO}} |
| Primary cells present | 150 | yes |
| Invent residual? | **refused** | n/a |

**Decision:** SKIP. No train / predict / ablation / money / OOS model artifacts.

**Why:** Operator override opened the 016 *shell* on SUGGESTIVE leads, but left residual object and
policy deferred. O3 Group 3 and design §B.4 require a **named** residual + `P-MR`/`P-MOMO` before
any refine. Inventing either would be an integrity failure for a “success” narrative.

## What was not done

- No `screen_code/` model implementation run
- No A0/A1/A2 ablation
- No Δ vs 014 baseline tables
- No analysis claim that 016 beats 014

## Artifacts

| Path | Role |
|---|---|
| `results/014_residual_pin.json` | input pin copy |
| `results/start_gate.json` | formal gate evaluation |
| `results/SKIP.json` | skip record |
| `screen.md` | this file |

## Operator gate (required before any re-open)

Choose one:

1. **Freeze residual + policy** on the pin (named object), then re-invoke implement+run  
2. **Amend 016 design** to define an explicit SUGGESTIVE-only refine object, then re-invoke  
3. **Terminal** Group 3 extraction path (accept SKIP; no 016 refine)

**Recommendation:** **3** unless you explicitly want to treat SUGGESTIVE leads as the residual
object — that must be a signed freeze, not an engine guess.

No XENA. No family status change. Partial-cost caveat remains programme-wide if money is ever scored.
