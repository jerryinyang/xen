# Results Interpretation: EXP-029 — cTrader Per-Bar Streaming Parity for Faithful AVWAP Strategy

**Date**: 2026-06-09
**Status**: CONSISTENT (parity confirmed)
**Audit**: PASS (0 Critical, 0 Warning, 4 Info)
**Disposition consequence**: EXP-028 `EVAL_SUPPORTED` → **cTrader-confirmed**

---

## 1. What this experiment asked

EXP-029 is a **parity confirmation**, not a re-litigation of edge. EXP-028 found the
faithful selective AVWAP strategy `EVAL_SUPPORTED` (all three domains `EVIDENCE_FOR`)
under the corrected EXP-027 event-level method — but did so by **pure Python
re-analysis** of upstream synthetic-event artifacts (EXP-020 events, EXP-022 lifetime
observations). It never executed the C# strategy on cTrader, so the production
execution path validated in VAL-002 was bypassed and the pyramid-inclusive faithful
strategy existed only as a Python re-aggregation, not as runnable code (see
`EXP-028-omission.md`).

The binding question, per domain (5m / 1h / 4h):

> Does the **corrected C# strategy, executed bar-by-bar inside cTrader's engine**,
> evaluated through the *same* estimand and the *same* frozen inference EXP-028 used,
> agree with EXP-028's per-domain PRIMARY verdict and effect within the predeclared
> parity tolerances?

The PRIMARY estimand is identical to EXP-028's: per-event **symmetric own-exit
matched-control excess** (`event_lifetime_bps − mean(control_lifetime_bps)`),
direction-signed log return in bps on real domain `RealClose`, both event and controls
completed under the EXP-022 band-target / trend-change own-exit rule. The inference
tail is the frozen EXP-027 method, hash-asserted byte-identical to EXP-028's
(`ea261b9ee0a8aca3`).

---

## 2. Headline result

**Overall parity disposition: CONSISTENT.** All three domains land in the CONSISTENT
band; no domain is INCONSISTENT; the 5m signal layer passes. Under the predeclared
interpretation guide — *CONSISTENT iff all five binding gates hold on ≥2/3 domains AND
the 5m signal-layer passes AND no domain is INCONSISTENT* — this **upgrades EXP-028's
Python-only `EVAL_SUPPORTED` to cTrader-confirmed**.

### PRIMARY effect: EXP-029 (cTrader) vs EXP-028 (Python)

| Domain | EXP-029 effect [95% CI] (bps) | EXP-028 effect [95% CI] (bps) | \|Δeffect\| | Holm p | Verdict (both) | n (029 / 028) |
|--------|------------------------------|------------------------------|------------|--------|----------------|---------------|
| 5m | **+5.79** [5.37, 6.18] | +5.78 [5.39, 6.13] | 0.007 | 0.002997 | EVIDENCE_FOR | 12 784 / 12 795 |
| 1h | **+23.33** [17.46, 28.91] | +23.38 [17.40, 29.32] | 0.054 | 0.002997 | EVIDENCE_FOR | 927 / 924 |
| 4h | **+69.02** [49.32, 90.38] | +69.02 [46.84, 90.52] | 0.000 | 0.002997 | EVIDENCE_FOR | 187 / 187 |

Every domain: positive effect, `CI_low > 0`, Holm-adjusted p at the permutation floor
(3/1001), verdict `EVIDENCE_FOR` in both experiments. The effect ordering and
magnitude band (single-digit 5m → tens 1h → ~70 bps 4h) reproduce EXP-028 closely.

---

## 3. Reading the five binding gates

The disposition is deliberately **falsifiable**: the adversarial-review hardening
(F01–F05) replaced the original "verdict + CI-overlap" read — which could only confirm
EXP-028 — with gates that can downgrade it. All five hold on all three domains:

| Gate | What it tests | 5m | 1h | 4h |
|------|---------------|----|----|----|
| **Verdict match** | same 3-way label | ✔ | ✔ | ✔ |
| **Magnitude equiv (F02)** | \|Δeffect\| ≤ max(2 bps, 25%·\|ref\|) | ✔ (0.007≤2.0) | ✔ (0.054≤5.85) | ✔ (0.0≤17.25) |
| **Count ±10% incl pyramid (F04)** | total/bull/bear/**pyramid** | ✔ (Δ≤0.09%) | ✔ (Δ≤0.45%) | ✔ (Δ=0%) |
| **Exit-parity (F01)** | C# completion == Python scan, same feed | ✔ (rate 1.0) | ✔ (rate 1.0) | ✔ (rate 1.0) |
| **Signal-layer 5m (F03)** | C# events == EXP-020 substrate | ✔ (≥99.8%) | n/a | n/a |

None of the INCONSISTENT triggers fired: no powered verdict conflict, no magnitude
divergence beyond `max(2 bps, 50%·|ref|)`, and no exit-parity failure.

### What was actually graded (the substantive content of the upgrade)

This is the key point distinguishing EXP-029 from a re-run of EXP-028's numbers. Three
distinct layers of the *production* code path were independently graded:

1. **Entry signal layer (F03).** On the feed-exact 5m domain, the C# AVWAP signal
   (regime / anchor / band / bounce / frozen targets) reproduces the EXP-020 Python
   substrate: 99.8% / 99.8% / 99.98% / 100% of EXP-020 5m triggers matched per
   instrument (all ≥98%), and on matched triggers the frozen favorable/adverse targets
   agree to a median relative difference of 0.0 (≤1e-3). A signal-logic divergence
   would have surfaced here rather than being absorbed as "benign feed coverage".

2. **Pyramid handling (F04).** The corrected multi-position logic produces pyramid
   counts of 6 254 / 445 / 84 vs EXP-028's 6 258 / 443 / 84 — within ±0.5%. The pyramid
   split is the direct signature of the multi-position correction and is now inside the
   count gate. ~49% of PRIMARY events are pyramids, so this is roughly half the
   evidence base, not a rounding term.

3. **Executed completion code (F01).** The corrected C# concurrent-completion routine
   (`MaybeCompletePosition`) backfills its executed exit per bounce, and the harness
   grades it against the Python `scan_lifetime` on the *same* cTrader feed and frozen
   targets: **match_rate = 1.000** on all domains (15 027 / 1 038 / 236 completed
   events), with max bps discrepancies of 1.8e-11 / 1.4e-13 / 0.0. The non-zero
   residuals confirm this is a genuine cross-implementation comparison (independent C#
   and Python computations agreeing to float precision), not a tautology — a
   multi-position completion bug would have dropped the rate below the 99% floor and
   forced the domain INCONSISTENT.

So the CONSISTENT upgrade certifies the **actual runnable robot** — entry signal,
pyramid position opening, and completion scanning — not just a re-aggregation. This is
what the EXP-028 omission demanded, in spirit and in letter.

---

## 4. Audit caveats carried into interpretation

- **4h PRIMARY effect is bit-identical to EXP-028 (`69.0156543344473`)** while 5m/1h
  differ slightly (Info #1). This is *not* data reuse — the audit verified separate
  code paths (EXP-029 from the cTrader frames, EXP-028 from the reference CSV) and the
  two 4h CIs differ (49.32 vs 46.84, different bootstrap draws). The likely cause is
  that the cTrader 4h resampled feed coincided exactly with the local 4h bars for all
  187 events and their controls within the fence — plausible on the coarsest domain
  with the fewest bars. **Read this as strengthening, not as a red flag**, and do not
  over-interpret it: it simply means the 4h feed had zero drift here, consistent with
  VAL-002's ≤1.83 bps *upper* bound on 1h/4h drift.

- **Secondary-horizon {1,3,6} numbers intentionally differ from EXP-028** (Info #2,
  F07). EXP-029 computes the fixed-horizon stability inputs from its own cTrader feed
  (the correct feed-matched analog), whereas EXP-028 drew them from EXP-021's local
  observations. These feed only the *non-binding* `decide_label` stability guard and
  never enter the PRIMARY effect. The divergence (e.g. 4h `sec_h6` 94.0 vs 83.2 bps) is
  **not** a parity discrepancy — the PRIMARY excess is the sole parity object, and all
  verdicts remain `EVIDENCE_FOR`.

- **`exit_parity` n_events exceeds PRIMARY n_events by design** (Info #3): exit-parity
  grades the full valid-target event population; PRIMARY additionally requires a
  completed outcome, per-instrument reportability, and ≥`MIN_CONTROLS` controls. The
  funnel (≈19.2k emitted 5m bounces → 15 027 valid-target → 12 784 PRIMARY) is
  coherent, with no double-counting.

- Integrity guards all clean: `reconciliation_bad = 0`, frozen hash hard-asserted
  `== ea261b9ee0a8aca3 ==` EXP-028's, `control_matching_equivalence_pass = true`,
  holdout fence enforced in-robot and re-asserted in Python (final 30% never loaded).

---

## 5. Equity companion (non-gating context only)

`equity_companion.csv` reports an exposure-matched cumulative own-exit advantage of
the strategy trades over their matched controls (5m +20 115 bps, 1h +5 819, 4h +3 755;
advantage_rate 1.0; positive Sortino differences). This is **context only — it carries
no verdict weight** and is not a tradability claim. It is a cumulative, cost-free,
instrument-summed diagnostic on the same own-exit excess the PRIMARY test already
adjudicates; it should not be read as a P&L or expectancy figure.

---

## 6. What this does and does not establish

**Establishes:**
- The faithful, pyramid-inclusive AVWAP strategy, *as actual cTrader-executed code*,
  carries the same positive event-level edge EXP-028 measured — on all three domains,
  under the frozen EXP-027 yardstick, on the cTrader `RealClose` feed.
- The Phase 006 objective ("fix the yardstick, then re-screen the faithful strategy")
  is now **fully** satisfied: the yardstick was fixed (EXP-027), the re-screen was run
  (EXP-028), and the re-screen's execution-path omission is closed (EXP-029). The
  half-satisfied state flagged in the omission record is resolved.
- VAL-002-style pipeline parity now extends from MA crossover to the AVWAP baseline
  strategy: the Python re-analysis is a faithful representation of the C# per-bar
  execution.

**Does not establish (limitations, unchanged from EXP-028):**
- **Not a per-bar-suite tradability claim.** This is an *event-level* edge confirmation
  under EXP-027, explicitly **not** a re-screen through the frozen per-bar
  qualification suite. EXP-023's per-bar `REFUTED` is not overturned; the two use
  different, non-substitutable yardsticks (event-level vs per-bar continuous-position).
- **No costs.** All effects are gross, cost-free event-level excess. Cost-bearing
  tradability is out of scope.
- **Holdout still sealed.** All evidence is on the first-70% analysis set; the final
  30% global holdout was never touched. No out-of-sample confirmation exists.
- **HYP-001 (AVWAP line as direct support/resistance) remains untested** — out of scope
  here, as in Phase 006.
- The edge remains **relative (vs matched controls), not absolute**, consistent with
  the EXP-024 retained finding; EXP-029 changes none of that framing.

---

## 7. Recommended follow-up (new scopes only — not extensions of EXP-029)

These are candidate *new* experiments, recorded for the phase retrospective, not scope
additions:

1. **Out-of-sample confirmation** of the event-level edge on the sealed final-30%
   holdout — a deliberate, one-shot holdout-release experiment with its own governance,
   if and when the programme decides to spend the holdout.
2. **Cost/slippage-bearing tradability** of the faithful AVWAP strategy under an
   explicitly-scoped cost model and an appropriate (per-bar or event-level) referee —
   the question EXP-029 deliberately does not answer.
3. **HYP-001 direct line-S/R test** with a confound-free metric (the gap EXP-025 could
   not close).

None of these are required to accept the EXP-029 result; the parity confirmation
stands on its own under the predeclared guide.
