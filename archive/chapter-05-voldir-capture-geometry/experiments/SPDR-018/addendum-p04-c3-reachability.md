# SPDR-018 — Addendum P4: is C3's required `n` reachable inside the Bybit catalog?

- **Date:** 2026-07-26
- **Thread:** **P4** from `analysis.md` §14 and `report.md` §9
- **Class:** analysis addendum over the **emitted** `results/not_resolvable.json`. **No re-run, no new
  emission, no catalog read, no new estimand, no new hypothesis.** SPDR-018's closed values are
  untouched.
- **Script:** `analysis_code/p04_c3_reachability.py` · **Artifact:** `results/p04_c3_reachability.csv` (1,946 rows)
- **Status:** **ANSWERED.** This converts an open lead into a recorded result.

---

## 1. Why this was worth asking

C3 (ordered `last_k` volatility flip) is **1,946 of SPDR-018's 3,559 `NOT_RESOLVABLE` cells — 55% of
the entire unresolved population**, and it is the specific object checkpoint-018's premise names as
*"conditional direction is unpowered, not refuted"*. `not_resolvable.json` records
`n_required_for_target` per cell, but nobody had asked **whether that `n` is obtainable at all**.

The distinction matters for the retrospective:

- If the required `n` is reachable, C3 is a live lead awaiting more data, and closing over it would
  violate B-5.
- If it is **not** reachable, then *"unpowered"* is the terminal state of the registered object, and
  **that is itself the answer** — recordable without ever reading it as a negative.

---

## 2. Method

Pure arithmetic. Each unresolved cell carries realised `n`, realised block MDE, and its parent's
target. The relation is verified rather than assumed:

```
n_required_for_target == n * (block_mde / target_mde)^2      max relative error 3.6e-2 (rounding)
```

Two ceilings are compared against:

1. **Absolute catalog ceiling** — one event per bar per symbol over the fenced TRAIN span:
   `901 days x 24 H1 bars x 25 symbols = 540,600` pooled bar-observations. Nothing event-nested can
   exceed this no matter how the conditioner is defined.
2. **Rate-preserving ceiling** — the cell's *own* realised event rate applied to every bar in the
   catalog. This is the honest one, because the event rate is a property of the registered
   conditioner, not a free parameter.

---

## 3. Result

**All 1,946 C3 unresolved cells are `pooled_sigma_normalised`** (1,932 H1, 14 H4). Every design §5
lever — pooling across all 25 symbols, σ̂-normalisation, the full TRAIN span — is **already applied**.
There is no remaining legitimate lever.

| Quantity | Median | q25 | q75 | q95 |
|---|---|---|---|---|
| realised `n` (events) | **140** | — | — | — |
| realised `n_dates` | 104 | — | — | — |
| realised block MDE | **90.2 bps** (target **10.0**) | — | — | — |
| MDE shortfall multiple | **9.02×** | — | — | — |
| **required `n`** | **10,450** | 5,248 | 19,002 | 42,256 |
| **required `n` ÷ realised `n`** | **81.3×** | 22.1× | 302.5× | 1,480× |
| realised event rate | **0.0003 of all bars** (3 in 10,000) | — | — | — |

### 3.1 It is not arithmetically impossible — it is impossible at the conditioner's own event rate

**This is the key distinction, and it is what makes the answer defensible.**

- Against the **absolute** ceiling, the required `n` is comfortably obtainable: **0 of 1,904 cells
  exceed it** (median required ÷ ceiling = **0.02×**). So the requirement is not absurd in principle.
- Against the **rate-preserving** ceiling, it is unobtainable. At a realised event rate of 3 in 10,000
  bars, the catalog can supply at most the `n` already realised — the levers are exhausted by
  construction.

Translating the shortfall into calendar span at the realised event rate (TRAIN = **2.47 years** of
25-symbol history):

| Required span of 25-symbol history | Share of C3 unresolved cells |
|---|---|
| more than **20 years** | **88.3%** |
| more than **100 years** | **64.5%** |
| median requirement | **200.6 years** |
| q25 / q75 / q95 | 54.6 y / 746.3 y / 3,651 y |
| **most favourable single cell** | **3.1 years** |

---

## 4. Answer

> ### C3 is **terminally `NOT_RESOLVABLE` in its registered event-nested form.**
>
> Not refuted. Not negative. **Unpowerable** — 88.3% of its unresolved cells would need more than 20
> years of 25-symbol crypto history and the median needs **201 years**, at an event rate the
> registered conditioner itself fixes. Crypto perpetuals do not have that history and will not for
> decades.

**Three consequences, stated precisely:**

1. **The only way to power C3 is to change its event definition** — loosen `last_k`, widen the state
   grammar, or drop the ordering requirement. Each of those is a **different object**, and therefore a
   **new registration**, not a powering attempt. SPDR-018 was explicitly forbidden from doing this
   (design: *original statement, no estimand substitution*), and correctly did not.
2. **The retrospective may now close over C3 without violating B-5** — provided it is booked as
   *terminally unpowerable in the registered form*, never as *refuted*, and provided the recorded
   reason is this arithmetic rather than the absence of a positive finding. **The distinction is not
   cosmetic:** "we measured it and it isn't there" is false; "the registered object cannot be measured
   on any obtainable crypto history" is true.
3. **The most favourable ~5% of C3 cells need only ~3–5 years** and are within reach of a modest
   catalog extension. If C3 is ever revisited, that thin stratum — not the median cell — is the only
   defensible target, and it must be predeclared rather than selected after the fact.

**What this does not say.** It says nothing about whether the C3 *mechanism* exists. The powered C3
cells that did reach target sit at gross **+0.34 bps** — the only positive item-level gross median in
arm C, and far below any cost floor. That remains a measured magnitude, not an edge, and this addendum
does not change it.

---

## 5. Governance

| Item | Value |
|---|---|
| Counted TEST reads | **0** — no data was read beyond an already-emitted JSON |
| Holdout contact | **none** |
| Cells or estimands modified | **none** — SPDR-018 remains closed and frozen |
| Family status change | **none** |
| New hypothesis or registration | **none** |

**No tradability, deployability, cost-complete, family-status, graduation or XENA claim is made or
implied by this document.**
