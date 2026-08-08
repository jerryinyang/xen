# PROPOSAL — CF-EPSOSC-001 — Episode-Clearing Oscillation Harvest

**Status:** `SUPERSEDED` (2026-07-16) — authoritative D0: [`cf-epsosc-001.md`](cf-epsosc-001.md).  
**Working name:** REF-B  
**Chapter context:** post–INFR-010 (NautilusTrader + Bybit USDT-perp primary)  
**Supersedes / re-opens:** spirit of CF-VOLHARV-001 (P-12 structure re-open) — **new family, new harvest object, new stack**. Does **not** re-parameterise the retired banded/hard-cap grid.

**Companion:** SPDR pack → *(removed from live refs — family closed)*  
**Shared open questions:** `docs/signal-registry/candidate-families/proposal-ref-ab-open-questions.md`

---

## 1. Thesis (restated)

Prices can **oscillate / mean-revert** enough that a **harvest structure** can earn money after costs. Prior work found **process-level** evidence of reduced multi-horizon variance on FX and proved that a **banded rebalance + hard inventory cap grid** failed for **mechanical** reasons (cadence collapse, cap-lock, inventory mark-out) — Mode C structure failure, not “oscillation is fake.”

This family re-opens on **Bybit crypto**:

- **new** episode / clearing objects (rolling anchor, within-episode clear, no hard inventory freeze as a **preferred** region — not the only allowed shape)  
- **no locked** entry/exit rules; multi-variant SPDR and XENA  
- **does not assume** FX VR&lt;1 transfers to perps — substrate must re-appear or the family dies cheaply  
- room for **crypto-native** harvest paths (funding-aware, volume-aware) without smuggling FX nulls as law  

---

## 2. Binding process decisions (operator-aligned, 2026-07-16)

| Decision | Choice |
|---|---|
| Route | **SPDR → (minimal promote) → full XENA** |
| EXP lane | **Skipped** |
| Rules | **Not locked** — variants and sub-modalities explored in both stages |
| Universe | Bybit USDT linear perps primary |
| Priors | Soft market priors; **hard** process bans + ban on **identical dead grid object** |
| Qualification | Portfolio contribution under cost (XENA), not per-variant metric perfection |

---

## 3. Prior evidence (legacy — do not transplant as Bybit fact)

| Source | What it established | What it did **not** establish |
|---|---|---|
| CF-VOLHARV / EXP-019/020 | FX VR&lt;1 / oscillation-like behaviour on multiple pairs; process property | That any vehicle was tradable net of cost |
| CF-VOLHARV grid vehicle | Structure failed: rare fills vs theory, cap-locks, inventory MTM erased harvest | That all mean-reversion harvest is impossible |
| Related residual/MR arcs | Reversion can exist while **idiosyncratic / hedged** money is ~0; two-sided cost hurts | Crypto-specific substrate map |

**Soft design hints:** prefer rolling anchors and episode clears; prefer one-sided or force per-side economics if two-sided; include funding in multi-session economics; do not retune the old grid.

---

## 4. Hard bans (process + structure identity)

1. Causal path only; no look-ahead.  
2. Honest money units (bps / named money) at screen and XENA seams.  
3. Cost binds when claiming net edge.  
4. Passive fill ≠ free alpha without decomposition / MM framing.  
5. **Identical dead object:** banded-rebalance **+ hard inventory cap** symmetric grid as the *same* harvest structure (P-12) — **out of family**. New episode objects only.  
6. SPDR is not tradability.  
7. No void chapter-03 XENA registry on Bybit without fresh CAL.

---

## 5. Soft priors (shape, don’t forbid)

- Oscillation may be **weaker or absent** on many perps → SPDR should kill cheaply if so.  
- Two-sided books paid double cost historically → default grid includes **one-sided** variants; two-sided allowed with diagnostics.  
- Real volume (new stack) may help **arming / regime** features — optional axes, not required for the thesis.  
- Funding can dominate multi-session inventory → prefer **within-episode** clears in the default grid.

---

## 6. Exploration plane (no locked rules)

| Axis | Example levels (not final) | Role |
|---|---|---|
| Episode definition | stretch from rolling mid/anchor; vol-expansion arm then fade; range-based episode | Harvest object |
| Anchor | rolling median/mean of price or return; session VWAP-like; crypto session anchors | Reference |
| Entry modality | market on confirmed breach; optional limit variants with fill decomposition if used | Execution |
| Clear / exit | return-to-anchor; fixed episode time; hybrid; **no hard inventory cap** in preferred set | Structure |
| Side policy | long-only stretch fade; short-only; two-sided | Cost arithmetic |
| Stretch threshold | coarse k grid | Hyperparameter |
| Symbols | **10-asset** SPDR universe via instrument selection rules (Q1); XENA may expand later | Universe |

**Controls:** matched random-timing / shuffled-episode entry; optional “dead grid twin” as **negative control** (should not win) if cheap to emit — disclosure only.

---

## 7. Route detail

```text
SPDR pack (TRAIN-only, multi-variant, disposition-only)
    → operator disposition
    → if WORTH_EXPLORING: XENA universe on episode-harvest variants
Full XENA (cost + funding aware; portfolio contribution selects structures/params)
```

**SPDR promote bar:** minimal cluster evidence that *some* non-grid episode object beats null in money or availability space (see SPDR pack).  
**XENA:** pre-search bps floor; reject universes whose entire mass is sub-breakeven before search.

---

## 8. Success / kill (family level)

| Stage | Success | Kill / park |
|---|---|---|
| SPDR | Coherent variant cluster with lift vs matched control | No substrate / no structure lift on liquid set |
| XENA | Portfolio finds cost-surviving contribution from episode objects | Only noise, or only print/cadence artifacts, or re-creates cap-lock pathology |

---

## 9. Infrastructure dependencies

- Nautilus + Bybit OHLCV (real volume available for optional features).  
- T1 costs: fees + spread model + **funding** (episode length interacts with funding).  
- XENA fresh CAL/registry.  
- If gross edge &lt; ~3× RT spread, T1 may be undecidable (programme T1/T2 rule) — park or demand larger capture variants.

---

## 10. Open questions

See `proposal-ref-ab-open-questions.md` (shared + Q-B*).

---

## 11. Operator sign-off block

| Item | Decision | Date |
|---|---|---|
| Approve thesis + route | ☐ | |
| Approve hard bans (incl. no dead grid object) | ☐ | |
| Resolve open questions | ☐ | |
| Assign SPDR-ID / register CF-ID | ☐ | |
