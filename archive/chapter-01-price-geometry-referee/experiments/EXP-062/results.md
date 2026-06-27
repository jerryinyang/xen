# Results: Experiment EXP-062 — MA-Substrate Lifetime Availability (dual-object)

**Deliverable: MA_AVAILABILITY_CHARACTERISED (dual-object).** Phase verdict **AVAILABILITY_GOOD**
(stronger object = native), but with a **binding signal-attribution caveat** that is the read's real
finding. Emitted for the single terminal G-015; no closure here.

## Headline (per object, never pooled)

| Object | MOVE_AVAILABLE (P11+P6) | median MFE / MAE | SIGNAL_ATTRIBUTABLE (beats RM-on-MA) | Verdict |
|--------|------------------------|------------------|--------------------------------------|---------|
| **Native** `A_MA_nat` | **91/99 cells, 17 instr, 77 non-4h — composes** | ≈ 3.84 / 2.92 ATR | **4/99 — does NOT compose** (contrast median CI_low ≈ −0.88) | AVAILABILITY_GOOD |
| **Hybrid** `A_MA_hyb` | **94/99 cells, 80 non-4h — composes** | ≈ 3.77 / 2.83 ATR | **2/99 — does NOT compose** (contrast median CI_low ≈ −0.98) | AVAILABILITY_GOOD |

## Interpretation

**1. A large favourable lifetime move is available on the MA substrate — on both objects.** Median
lifetime MFE ≈ 3.8 ATR (well above the 1.0-ATR reference) and > median MAE in 91/94 cells, composing P11
with the non-4h rule. The EXP-055 ZigZag AVAILABILITY_GOOD reading reproduces in magnitude on MA, for
both the native and the genuinely-new hybrid object. The MA reversal segment is long, so the room is
abundant.

**2. That room is NOT harami-attributable — it is an ambient property of the (long) MA segments.** The
binding P5 leg fails decisively: the conditioned harami beats its own matched-random-on-MA null in only
**4/99** (native) / **2/99** (hybrid) cells, and the *typical* contrast lower bound is **negative**
(≈ −0.88 / −0.98 ATR) — i.e. a random in-regime entry on the same MA segment captures **as much or more**
lifetime favourable room than the conditioned harami. The available move is a function of MA-segment
length, not of the harami signal. This is the decisive qualification the scope asked for ("is the room
signal-driven or a generic MA-segment-length property?"): **generic.**

**3. Reconciling with EXP-060B/061.** EXP-060B/061 found a signal-attributable *capture* (benchmark-
geometry median) edge on the native object (85/99 at the champion; 8/99 at benchmark). EXP-062 shows the
raw *availability* (lifetime MFE) is **not** where that signal lives — availability is ambient. So the
native edge that EXP-061 found is a **capture-geometry** property (the harami times the 50%-of-segment
target / stop interaction), not "the harami sees more room." Availability does not distinguish native from
hybrid (both ~3.8 ATR, both non-attributable); capture does (EXP-061: native generalises, hybrid doesn't).

**4. The adverse tail (the L2→L3 hand-off).** Median MAE ≈ 2.9 ATR; worst-5% tail-share ≈ 0.23; raw-mean
MAE ≈ 4.60 vs 10%-trimmed ≈ 3.52 (native). The adverse side is **moderately top-heavy** — there is a
truncatable catastrophic tail (the `/ADV-NONE` downside EXP-060B flagged), but the bulk MAE is large
(trimmed mean ≈ 3.5 ATR), so a stop truncates the tail without making the central adverse excursion
small. EXP-063 confirms the consequence: bounding repairs the catastrophic mean but does not lift the
centre.

## Reading against the pre-registered guide

- `MOVE_AVAILABLE` composes P11+P6 for both objects → **AVAILABILITY_GOOD** by the letter of the rule.
- The `SIGNAL_ATTRIBUTABLE` tally is **sparse and non-composing** for both → the AVAILABILITY_GOOD must be
  read as *ambient availability*, **not** a harami-specific availability edge. This is recorded as the
  material caveat carried to G-015, exactly as the interpretation guide prescribes ("If `MOVE_AVAILABLE`
  is broad but `SIGNAL_ATTRIBUTABLE` is sparse, the room is largely a generic MA-segment-length
  property").
- No power limitation (99/99 powered, both objects). No correctness failure (reconciliation 99/99 exact,
  determinism + causality clean).

## Limitations

1. **TRAIN-only** (first 49%); TEST + final-30% holdout sealed for G-015.
2. **Gross, availability ceiling.** MFE/MAE are excursion ceilings, not captured returns; availability
   composing says nothing about tradability.
3. **Attribution is the binding leg, and it fails** — the AVAILABILITY_GOOD label, taken alone, would
   overstate the result; the per-object attribution tally is the honest read.
4. `/STRONG-HA` and MAD arms are disclosed-secondary; not the binding read.
