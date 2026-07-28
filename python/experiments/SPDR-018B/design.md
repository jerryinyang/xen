# SPDR-018B — Design: the checkpoint-017 residue on the cTrader universe

- **Family / hypothesis:** `CF-VOLDIR-001` / `HYP-D5` (same hypothesis, second universe)
- **Checkpoint:** `2026-07-25-018-trade-opportunity-capture-geometry`
- **Lane:** SPDR · TRAIN-only · vectorised Python · 0 counted TEST reads · no family action · no XENA
- **Status:** DESIGN — operator-approved 2026-07-25
- **Binding substrate:** `python/experiments/SPDR-018/design.md`. **This document narrows nothing
  and re-states nothing.** Every mechanism, object, estimand, band rule, control and target
  precision is inherited from SPDR-018 verbatim; only the universe changes.

```
SPREAD-COST-DISCLOSURE
  spread_cost_status: UNAVAILABLE_NOT_CHARGED
  spread_rt_bps: null
  cost_scope: PARTIAL_FEES_FUNDING_ONLY  (BORROWED MODEL — see §3)
  implication: reported cost understates total cost; reported net performance is overstated
  prohibited_claims: fully-net, cost-complete, tradable, deployable
```

---

## §1 Why this experiment exists

SPDR-018 ran all four arms on the Bybit crypto universe but replicated **only arm B, at one exit
geometry, gross only** on cTrader. The operator's intent was that **everything be tested on both
universes**. That narrowing was an implementation defect in SPDR-018, not a design decision, and
it left the run's single surviving live thread — `C2` shock-conditioned MOMO — with **zero
external replication**.

SPDR-018 is **COMPLETE and FROZEN**. It is not modified. SPDR-018B is a separate speed-run that
puts the same four arms on the cTrader universe.

> **Falsifiable question.** Do the SPDR-018 results — the break-even geometry, the `W/L` mirror,
> the powered/`NOT_RESOLVABLE` split, and specifically the `C2` shock-MOMO survivor — reproduce on
> an independent asset class with its own fence?

**This is a true speed run** (operator directive). Code, design, objects and protocol are reused
directly from 017/018. No fresh design derivation, no new controls, no re-registration.

---

## §2 Scope

| Item | Freeze |
|---|---|
| Universe | `EURUSD`, `XAUUSD`, `USTEC` — the full cTrader catalog (INFR-021) |
| Catalog | `data/catalog_ctrader/`, fence `python/experiments/INFR-021/artifacts/fence-manifest.json`, sha256 `4cdc7b01dd47200710d0d961639d55d52e1129ca89096e841eafd816b6061de0` |
| Arms | **All four**, inherited from SPDR-018 §2: A (SPDR-012 residue) · B (SPDR-013) · C (SPDR-014) · D (SPDR-015) |
| Clocks / horizons | inherited per arm, unchanged |
| Objects / estimands | inherited **verbatim**; nothing re-specified |
| Uniform layer | SPDR-018's `metrics.py`, `cells.py`, `uniform_controls.py` reused unchanged |
| TRAIN fence | `analysis_start 2021-06-02T00:01Z` → `train_end 2023-11-22T00:00Z` (cTrader's own) |
| cTrader holdout | `2024-12-13T00:00Z` onward — **never queried**, asserted in code |
| Bybit holdout | `2025-01-08` — not touched; this experiment reads no Bybit bars except for the §5 guard |
| Multiplicity | disclosed, not rationed (inherited operator directive) |

### 2.1 Band split — computed on cTrader's OWN span

The two universes have different fences, so a shared DESIGN/CONFIRM split is impossible
(SoT §5.4). The split is therefore taken at **the same proportion of its own TRAIN span** that
Bybit uses:

```
Bybit  DESIGN fraction of TRAIN = 609d / 901d = 0.676172
cTrader TRAIN span              = 2021-06-02T00:01Z -> 2023-11-22T00:00Z  (902 days)
cTrader DESIGN                  = [2021-06-02T00:01Z, 2023-02-02T00:00Z)
cTrader CONFIRM                 = [2023-02-02T00:00Z, 2023-11-22T00:00Z)
```

Both bands are scored explicitly, as in SPDR-018.

---

## §3 Cost — a BORROWED model (operator directive)

**Operator call, 2026-07-25:** reuse the crypto universe's cost model for simplicity.

```
COST-MODEL-PROVENANCE:
  source:   SPDR-014 screen_code/costs.py -> xen.evaluation
            (Bybit taker fees 11.0 bps round trip + discrete funding stamps + 2.0 bps allowance)
  applied to: EURUSD, XAUUSD, USTEC
  status:   BORROWED — this is NOT a cTrader cost model and NOT a cTrader cost measurement.
            Perp funding does not exist on these instruments; the fee schedule is a different
            broker's. It is used so that net figures are COMPARABLE ACROSS THE TWO UNIVERSES on
            one common yardstick, which is the only claim it supports.
  prohibited: any statement that a cTrader net figure is that instrument's real cost, or that any
            cTrader cell is tradable, deployable or cost-complete.
  gross:    reported alongside net on every cell, always. Gross is the primary comparison.
```

### 3.1 Volatility scaling of the borrowed cost (operator directive, 2026-07-25)

A flat bps charge is **not comparable across universes whose volatility scale differs**. Measured
pooled σ̂ is **73.00 bps on crypto** and **13.03 bps on cTrader** — a 5.6× difference. Charging the
same 13.5 bps on both would make any cross-universe net comparison an artifact of the cost model
rather than of the data: the identical charge is 5.6× heavier in σ-units on the lower-vol book.

The borrowed cost is therefore **scaled by the measured σ̂ ratio**:

```
ratio = sigma_ctrader / sigma_crypto = 13.034 / 73.001 = 0.17855   (COMPUTED AT RUN)
  fee 11.0 bps      -> 1.964
  funding 1.0/stamp -> 0.179
  allowance 2.0     -> 0.357
  floor 13.5 bps    -> 2.410
```

Neither σ̂ is asserted: crypto's is read from SPDR-018's **emitted** `unit_pin.json`, cTrader's is
measured in this run. **Both net legs are emitted on every cell** — `c_net_bps` (vol-scaled,
headline) and `c_net_unscaled_bps` (unscaled borrowed, companion) — and **gross remains primary**.

```
COST-STATUS: DOUBLY SYNTHETIC — BORROWED and RESCALED.
  It is not any instrument's real cost. It supports exactly one claim: cross-universe
  comparability in volatility units. It is not a tradability input.
```

The per-symbol spread pin remains a blocking prerequisite for any real money read on this
universe, exactly as it is on crypto.

---

## §4 What is rebuilt, and from what

No parent screen ever ran on cTrader, so **no parent panel exists to re-score.** Every object is
BUILT from the parents' own modules against cTrader bars — the same approach SPDR-018's arm B
already used:

| Arm | Parent modules driven |
|---|---|
| A | `SPDR-012` `features` · `hmm` · `models` · `pipeline` |
| B | `SPDR-013` `indicators` · `arms` · `capture` — **all 5 exit modes** (018's cTrader read did `signalflip` only) |
| C | `SPDR-014` `prepare` · `engine` · `indicators` · `costs` |
| D | `SPDR-015` `features` · `hmm` · `transitions` · `zz_ordinal` |

Retargeting is done by **rebinding the catalog and band constants on the parents' loaded
modules** — never by editing parent source. Parent code is the substrate and stays untouched.

---

## §5 Parity — maintained in interpretation (operator directive)

SPDR-018's HARD parent-parity check cannot exist here: there are no published cTrader cells to
reproduce. Two substitutes, both weaker and both declared as such:

1. **CROSS-UNIVERSE OBJECT IDENTITY [HARD].** The retargeted code path is run on a *Bybit* symbol
   and must reproduce SPDR-018's emitted cells for that symbol exactly. This proves the retarget
   changed the DATA and not the OBJECT — which is the specific failure parent parity guards
   against.
2. **Own-span interpretation parity.** cTrader cells are read against cTrader's own TRAIN span and
   its own band split, never against Bybit dates or Bybit cell values.

**Binding consequence:** cTrader results are **replication and credibility**, never power for the
crypto estimate. They are reported separately and are **never pooled into `n`**
(AMENDMENT-C1 / AMENDMENT-S1, unchanged).

---

## §6 Inherited unchanged from SPDR-018

Stated so the reuse is explicit and auditable — none of these is re-derived here:

- §4.1 the `(p, W, L, W/L, p_be, p_be_net, edge)` layer, and the identity assertion
  `|p·W − (1−p)·L − mean| < 0.01 bps`
- §4.3 the unit pin (H1 Parkinson EWMA λ=0.94, 60-bar warm-up, causal ≤ t−1), **recomputed on
  cTrader symbols at run**, never carried over from crypto
- §5 the power levers, and `NOT_RESOLVABLE` as a first-class quantified result
- §6.2 day-block bootstrap, blocks {1,3,7} days, 5 seeds, min/max envelope; block MDE drives every
  band label; the iid form is a labelled companion only (M-1)
- §6.3 M-2 exact-span disclosure · M-3 magnitude-matched comparator · M-4 effective coverage ·
  M-5 collapse fraction disclosure-only
- §7 the three uniform controls and three tripwires, derangements with zero fixed points, ≥2000
  seeds
- §8 interpretation bands as labels, never gates; no `pass` field anywhere; B-5 symmetric
- §9 target precision inherited per arm from each parent's own rule
- §13 the full refusal list

---

## §7 Power expectation (predeclared)

**3 instruments against 25.** Pooling across symbols — SPDR-018's primary power lever — is far
weaker here. Cells that were powered on crypto may well be `NOT_RESOLVABLE` on cTrader purely on
`n`, and that is a statement about this universe's size, **never evidence against the crypto
result** (B-5). Every short cell is reported with realised `n`, block MDE, target, multiple short
and required `n`.

The reverse also holds: a cTrader cell that fails to replicate a crypto finding is only
informative **if it is powered**. An unpowered non-replication says nothing.

---

## §8 What this design refuses

Everything SPDR-018 §13 refuses, plus:

- Pooling cTrader into the crypto estimate, or citing it as power rather than credibility.
- Presenting any borrowed-cost net figure as a cTrader cost measurement.
- Reading an unpowered cTrader cell as a failure to replicate.
- Modifying SPDR-018 in any way. It is complete and frozen.

---

## §9 Amendment ledger

```
No amendments. Registered 2026-07-25 under operator approval.
running count: 0 looser / 0 tighter / 0 neutral
```

Operator directives incorporated at registration: all four arms on the cTrader universe;
crypto cost model borrowed for simplicity; fence and band split computed on cTrader's own span;
parity maintained in interpretation; true speed run — 017/018 code and protocol reused directly.
