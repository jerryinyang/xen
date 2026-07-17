# SPDR Pack — HTFCAP (REF-A / proposal CF-HTFCAP-001)

**Status:** `D0-FROZEN` 2026-07-16 — open questions resolved; **SPDR-004 assigned**; design
COMPLETE (`python/experiments/SPDR-004/design.md`) — screen execution separate go.  
**Lane:** SPDR (TRAIN-only, disposition-only). Integrity boundary: `docs/references/spdr-lane.md`.  
**Family D0:** `docs/signal-registry/candidate-families/cf-htfcap-001.md` (REGISTERED).  
**Promote target if promising:** full **XENA** universe (not EXP).

---

## 1. Purpose

Cheap multi-variant screen: is there **enough conditional structure** under HTF context × capture-scale variants on **Bybit** to justify a full cost-aware XENA universe?

**Not:** tradability, deployability, or locked strategy rules.

---

## 2. Decisions preserved

| Item | Choice |
|---|---|
| Next stage if promote | **XENA** (skip EXP) |
| Rules | **Unlocked** — pack explores a **thin** variant grid |
| Promote bar | **Minimal** (family justification only) |
| Old evidence | Soft prior only; re-measure on crypto |

---

## 3. Screen question (single sentence)

On TRAIN Bybit majors, do one or more **coherent clusters** of (HTF state × LTF base × hold × domain) show **signal-conditional lift** over matched baselines in **money-relevant units (bps)**, under causal `t−1` rules?

---

## 4. Thin variant grid (default — operator may edit before run)

Keep SPDR **smaller than XENA**. Exact levels frozen in the first `SPDR-###/design.md`.

| Axis | Default span (proposal) | Notes |
|---|---|---|
| Symbols | **10-asset** universe via **instrument selection rules** (Q1 decided) | Rules define membership; not a frozen ad-hoc ticker list only |
| Domains (HTF/LTF) | At least two of: 1h/5m, 4h/15m, 1d/1h | Include ≥1 longer-grain pair |
| HTF state | ±DI continuation; ADX-on/off; simple vol regime (optional) | Confirmed HTF bar only |
| LTF base | Unfiltered baseline + 1–2 naive entries (e.g. momentum breakout; optional random-sign control) | Bases are **rulers**, not strategies to rescue |
| Hold | 0.5×, 1×, 2×, 4× HTF span (LTF bars) | Captures short + longer; not a claim that 4× wins |
| Polarity | with-HTF vs unfiltered (against-HTF optional disclosure) | |

**Hard grid exclusions:** no passive-limit MR entry as a primary SPDR cell without fill decomposition (print confound).

---

## 5. Estimands and integrity

| Item | Requirement |
|---|---|
| Slice | TRAIN only (new global calendar fence when active; else legacy TRAIN definition until fence lands) |
| Causality | Decision ≤ t−1 confirmed; open-to-open (or pack-declared equivalent) |
| Primary unit | **bps** (L-21); any ATR figure is disclosure with **named** normaliser |
| Lift | Treatment over matched baseline; random controls ≥25 seeds (L-19) |
| Dependence | Block ≥ hold H (or non-overlapping trades) for overlapping windows |
| Multiplicity | Disclose cell count; promote on **cluster**, not single max cell |
| Accounting | No local P&L primitives for verdict; evaluation toolbox / declared screen metrics |

---

## 6. Minimal promote rule (predeclare before run)

**WORTH_EXPLORING** if **all** of:

1. **Cluster rule:** ≥ *K* cells in a connected region of the grid (same domain family and HTF modality, varying hold and/or symbol) show positive lift vs baseline on the primary bps facet, with dependence-honest uncertainty not obviously null.  
2. **Not a single lottery ticket:** the best cell is not the only positive in its neighbourhood (simple neighbour or sign-agreement rule — freeze in design.md).  
3. **Money-relevant:** report median gross bps/trade (or bps/episode) for the cluster; **no** requirement to clear full deploy cost at SPDR, but cluster should not be **visibly pure noise**.

**NOT_WORTH:** no cluster; lift concentrated in one cell under huge multiplicity.  
**INCONCLUSIVE:** underpowered / data gap / fence not ready.

**K = 3** (frozen).

---

## 7. Diagnostics (always report, not gates)

- Hold ladder: does lift grow with hold in **bps** (not only ATR)?  
- Drift / beta: long-only vs sign-symmetric reads where relevant.  
- Filter vs baseline: lift over unfiltered, not “absolute return of a broken base.”  
- Cell count and implied multiplicity.

---

## 8. Artifacts

```text
python/experiments/SPDR-###/   # when ID assigned
  design.md      # frozen grid + promote rule
  screen.md      # neutral quantification
  analysis.md    # fresh-context analyst (mandatory per spdr-lane)
  results/ plots/
```

Disposition operator-signed after analysis.md.  
On **WORTH_EXPLORING** → open XENA universe design for CF-HTFCAP (separate artifact).

---

## 9. Explicit non-goals

- Selecting the “best” hyperparameter for live trading  
- Net-of-full-cost CI deploy claims  
- Replaying EXP-025 design on USTEC  
