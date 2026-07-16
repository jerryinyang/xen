# CF-EPSOSC-001 — Episode-Clearing Oscillation Harvest

**Status:** `REGISTERED` (2026-07-16, checkpoint-013 D2, operator-signed; D0 COMPLETE same date) — live ledger row appended (`multiplicity-registry.md` Chapter 04); **SPDR-005** assigned; 0 slots, 0 reads. XENA gate blocked until INFR-014 fresh CAL pin.  
**Working name:** REF-B  
**Family ID:** CF-EPSOSC-001  
**Chapter:** 04 (NautilusTrader + Bybit USDT-perp primary, INFR-010+)  
**Route:** **SPDR → full XENA** if `WORTH_EXPLORING` (**EXP lane not used**)  
**Companions:**  
- SPDR pack: `docs/references/spdr-pack-epsosc-001.md`  
- Open-Q log: `docs/signal-registry/candidate-families/proposal-ref-ab-open-questions.md`  
- Sibling family: CF-HTFCAP-001  

**Re-open lineage (not a re-run):** CF-VOLHARV-001 / P-12 — substrate real on FX, **banded + hard-cap grid structure failed**. This family requires a **new harvest object** (rolling anchor / within-episode clear / no hard inventory freeze as preferred region). **New D0, new stack.** FX VR&lt;1 does **not** transplant as a Bybit fact.

---

## 1. Thesis

Prices may **oscillate / mean-revert** enough for a **harvest structure** to earn after costs. Legacy work showed process-level oscillation on FX and proved one vehicle class dead (grid cadence collapse, cap-lock, inventory MTM wipe). On **Bybit USDT linear perps** we re-open with:

- multi-variant **episode** definitions (unlocked rules)  
- ban on the **identical dead grid object**  
- SPDR justification → XENA portfolio+cost qualification  
- room for crypto-native paths (funding-aware clears, optional volume arms)  

---

## 2. Mechanism class (for CAL / checkpoint scoping)

| Attribute | Value |
|---|---|
| Class | **Episode-native path / oscillation harvest** (structure search) |
| Information source | Price OHLCV (optional real volume for arming) |
| Adjudication shape | Multi-candidate portfolio (XENA); episode-level economics |
| Cost sensitivity | Two-sided cost; funding vs episode length; small capture risk (Mode B) |
| CAL implication | Episode/leg estimands; inventory/path diagnostics; funding in cost; pre-search bps floor; avoid costless cadence-max |

---

## 3. Binding decisions (frozen 2026-07-16)

| Item | Decision |
|---|---|
| Pipeline | SPDR → XENA if promising; **no EXP** |
| Rules | **Not locked** |
| SPDR universe | **n = 10**, instrument **selection rules** |
| Promote cluster K | **K = 3** |
| vs HTFCAP | **Parallel**, separate packs/universes |
| SPDR vs INFR | SPDR on available Bybit data + fence; XENA after emission+cost+**CAL shaped to this D0** |
| Funding | Disclose at SPDR; bind in XENA |
| Episode objects (SPDR) | **Two:** (1) stretch-from-rolling-anchor fade; (2) vol-expansion arm → fade |
| Sides | **One-sided required**; two-sided optional ≤25% of SPDR cells |
| VR diagnostic | **Parallel facet** in SPDR; not sole hard-gate for promote |
| Dead object | Banded rebalance + **hard inventory cap** symmetric grid **out of family** |

---

## 4. Hard bans

1. Non-causal construction.  
2. Unit lies / local accounting for verdicts.  
3. Costless net-edge theater.  
4. Passive fill as free alpha without decomposition/MM framing.  
5. **Identical P-12 grid object** (banded rebalance + hard cap symmetric grid).  
6. SPDR as deployability.  
7. Void registry on Bybit without fresh CAL.  
8. Promote on single lottery cell (K≥3).

---

## 5. Soft priors

- Oscillation may be weak on many perps → SPDR can kill cheaply.  
- Prefer within-episode clears (funding).  
- Prefer one-sided economics; allow two-sided with per-side diagnostics.  
- Real volume optional for arming features.  
- Do not hard-kill a non-VR object solely because a VR table is flat (diagnostic only).

---

## 6. D0 exploration plane

### 6.1 SPDR (thin grid — pack normative)

| Axis | Frozen default |
|---|---|
| Symbols | 10, rule-selected |
| Objects | Stretch-fade; vol-expansion-arm fade |
| Anchor | Rolling median (coarse window grid) |
| Entry | Market on confirmed event (default) |
| Clear | Return-to-anchor; time-stop; hybrid — **no hard inventory cap** |
| Side | One-sided required; two-sided ≤25% cells |
| k thresholds | 2–4 coarse levels |

**Promote:** K≥3 cluster on **bps/episode** (or declared equivalent) vs matched random-timing / shuffled-episode control; neighbourhood rule; not banned grid (full text in SPDR pack).

### 6.2 XENA (wide grid — later universe design.md)

After promote: expand objects/hypers/instruments/sides; all cells enter; funding+fees+spread in cost; portfolio contribution under post-CAL binder; pre-search bps floor; path/inventory diagnostics mandatory in analysis plan.

---

## 7. Hypotheses

| ID | Question | Stage |
|---|---|---|
| HYP-S1 | Does any non-grid episode-object cluster show bps/episode lift vs matched controls on Bybit-10? | SPDR |
| HYP-S2 (disclosure) | Do simple VR/oscillation diagnostics on the same symbols support a process story? | SPDR facet |
| HYP-X1 | Does XENA select episode-harvest candidates with cost-aware structure beyond battery null? | XENA |
| HYP-X2 (disclosure) | Do selected structures avoid cap-lock / inventory-censor pathology of P-12? | XENA analysis |

---

## 8. Kill / park criteria

| Stage | Kill / park |
|---|---|
| SPDR | NOT_WORTH — no cluster; only banned-grid-like behaviour |
| SPDR | INCONCLUSIVE — power/data |
| XENA | Noise; print/cadence only; re-created cap-lock; pre-search mass sub-breakeven |
| Substrate | Optional: if diagnostics and structure clusters both empty on liquid set — park family |

---

## 9. Infrastructure dependencies

| Dependency | Blocks |
|---|---|
| Bybit OHLCV + integrity | SPDR |
| TRAIN fence | SPDR/XENA |
| 10-asset selection rules (codified selector optional later) | Named membership for runs |
| Nautilus emissions | XENA |
| Fees + spread + **funding** model | XENA net |
| **CAL + registry for episode-harvest / path class** | XENA gate — **after this D0** |
| Optional volume features | not blocking |

---

## 10. Distinctness (pitfalls)

| Pitfall | Why not a re-run |
|---|---|
| P-12 / CF-VOLHARV | New object class; hard ban on dead grid; new stack |
| P-10 passive MR | Default market-on-event; limits only with decomp |
| P-13 hedged residual | Not CSRR basket residual; episode harvest on single names (basket not required) |
| CF-HTFCAP | Different mechanism class (harvest vs HTF conditioning) |

---

## 11. Evidence ledger

| Date | Item |
|---|---|
| 2026-07-16 | D0 complete; operator freeze (Q1=10 rule-selected; remaining Q = recommendations) |
| 2026-07-16 | REGISTERED at checkpoint-013 (D2, operator-signed); SPDR-005 assigned; registry row appended (`multiplicity-registry.md` Chapter 04) |
| 2026-07-16 | D3/D5 operator decisions: anti-survivorship binding project-wide (SPDR most-liquid-10 acceptable as justification-only); universe selection is ONLINE (trailing 24h volume, ≤ t−1, rule + rebalance frequency frozen — no fixed list) |

---

## 12. Operator sign-off

| Item | Status |
|---|---|
| D0 content freeze | **Complete** (2026-07-16) |
| Checkpoint-013 agenda | **Done** (ckpt-013 design, 2026-07-16) |
| SPDR-### / ledger registration | **SPDR-005 / REGISTERED** (D2 operator-signed, 2026-07-16) |
