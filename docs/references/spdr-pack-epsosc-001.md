# SPDR Pack — EPSOSC (REF-B / proposal CF-EPSOSC-001)

**Status:** `D0-FROZEN` 2026-07-16 — open questions resolved; **SPDR-ID not yet assigned**.  
**Lane:** SPDR (TRAIN-only, disposition-only). Integrity boundary: `docs/references/spdr-lane.md`.  
**Family D0:** `docs/signal-registry/candidate-families/cf-epsosc-001.md`  
**Promote target if promising:** full **XENA** universe (not EXP).

---

## 1. Purpose

Cheap multi-variant screen: on Bybit, is there **any non-grid episode-harvest structure** with availability/money lift vs matched controls sufficient to justify a full XENA universe?

**Not:** tradability claim; not a retune of the retired VOLHARV grid.

---

## 2. Decisions preserved

| Item | Choice |
|---|---|
| Next stage if promote | **XENA** (skip EXP) |
| Rules | **Unlocked** — thin multi-object / multi-hyper grid |
| Promote bar | **Minimal** cluster justification |
| FX VR&lt;1 | Soft hope only; **must re-appear or family dies at SPDR** |

---

## 3. Screen question (single sentence)

On TRAIN Bybit majors, do one or more **coherent clusters** of episode-harvest variants (rolling anchor / stretch / clear policy × side policy) show **lift over matched random-timing or shuffled-episode controls** in **bps per episode** (or bps per trade), under causal rules — **excluding** the banned hard-cap banded grid object?

---

## 4. Thin variant grid (default — operator may edit before run)

| Axis | Default span (proposal) | Notes |
|---|---|---|
| Symbols | **10-asset** universe via **instrument selection rules** (Q1 decided) | Same selection rules as HTFCAP unless operator splits packs |
| Episode objects (2–3 max at SPDR) | (A) stretch-from-rolling-anchor fade; (B) vol-expansion arm → fade extreme; (C) optional simple mean-revert to rolling mid | Prefer within-episode clear |
| Anchor | rolling median window coarse set | No cointegration stack at SPDR |
| Entry | market on confirmed event (default) | Limit cells only if fill decomp planned |
| Clear | return-to-anchor; time-stop; hybrid | **No hard inventory cap** in pack |
| Side | one-sided variants required; two-sided optional | Report per-side if two-sided |
| Threshold k | 2–4 coarse levels | |

**Hard exclusions:** banded rebalance + hard inventory cap symmetric grid (dead object).  

**Optional negative control:** one “grid-like” twin (if cheap) expected **not** to promote — disclosure.

---

## 5. Estimands and integrity

| Item | Requirement |
|---|---|
| Slice | TRAIN only under active fence policy |
| Causality | Confirmed bars; no look-ahead |
| Primary unit | **bps per episode** (native object); bps/trade disclosed |
| Controls | Matched random timing and/or episode-time shuffle; ≥25 seeds if random |
| Dependence | Episode-level or block ≥ dependence horizon |
| Multiplicity | Promote on cluster, not single cell |
| Funding | **Disclose** episode length × funding sensitivity even at SPDR (Bybit-critical) |

---

## 6. Minimal promote rule (predeclare before run)

**WORTH_EXPLORING** if **all** of:

1. **Cluster rule:** ≥ *K* cells sharing an episode-object family show positive lift vs matched control on bps/episode.  
2. **Neighbourhood:** not a lone max cell.  
3. **Structure identity:** promoting cluster is **not** the banned grid object.  
4. **Substrate honesty:** if a simple VR / oscillation diagnostic on the same symbols is flat everywhere, require **stronger** cluster evidence or prefer INCONCLUSIVE/NOT_WORTH (freeze exact coupling in design.md).

**NOT_WORTH:** no cluster; only grid-twin “works”; pure noise.  
**INCONCLUSIVE:** underpowered / infrastructure incomplete.

**K = 3** (frozen).

---

## 7. Diagnostics (always report, not gates)

- One-sided vs two-sided economics  
- Episode duration distribution vs funding  
- Cadence (episodes per year) vs implied capacity  
- Whether “lift” is adverse-selection / fill artifact (if any limits)

---

## 8. Artifacts

```text
python/experiments/SPDR-###/
  design.md / screen.md / analysis.md / results/
```

On **WORTH_EXPLORING** → XENA universe design for CF-EPSOSC (separate artifact).

---

## 9. Explicit non-goals

- Proving FX VR&lt;1 on Bybit as a standalone paper  
- Optimizing grid spacing  
- Deploy CI  
