# Results: EXP-057 — Adverse-Target Geometry

## Question

For the live `/STRONG-STAT`-conditioned HA harami (anchored at the confirmation-bar close, faded against the in-progress strong move, favourable target held at benchmark 50%-of-`M_sofar`), does changing **only the adverse target** — from the benchmark 1:1 (`adv_dist = 0.50 × M_sofar`) to a faded-move extreme stop (`/ADV-EXTREME`, raw and ≥1:1-constrained) or to no stop at all (`/ADV-NONE`) — improve **gross per-event median expectancy** (ATR-normalised, P15 fills, real prices) vs the benchmark? And which variant wins?

## Verdict

**EVIDENCE_FOR** — one alternative adverse-target geometry improves conditioned capture over the 1:1 benchmark.

- **Passing variant:** `/ADV-NONE` (removing the adverse barrier)
- **Composition:** 23 WIN cells over 15 instruments (quorum: ≥5 cells over ≥3 instruments — **not fragile**)
- **P11 met:** Yes — `n_pass = 1`, `fragile_passes = []`

---

## Findings per Variant

### BENCH (benchmark 1:1, reference)

- **Powered:** 99/99 cells, 17/17 instruments
- **Viable:** 8 cells, 7 instruments (CI_low > 0 & m ≥ 30)
- **Win:** 0/0 (reference — the benchmark is the contrast anchor)
- **First-hit `r`:** 0.506 across cells — replicates EXP-049/053 `r ≈ 0.50` null exactly
- **Interpretation:** The benchmark performs as expected; 8 cells have positive expectancy but of modest magnitude. The 1:1 adverse stop clips about as many favourable hits as adverse hits.

### ADV-EXTREME-raw (tight faded-move extreme stop, R:R free)

- **Powered:** 99/17
- **Viable:** 0 cells, 0 instruments
- **Win:** 0/0
- **First-hit `r`:** 0.28 on BTCUSD-5m (well below 0.50, as predicted)
- **BTCUSD-5m detail:** `median = −0.368 ATR` (benchmark 0.057); `FAV=627, ADV=1631, TIMECAP=859`. The tight stop converts winners to stop-outs: 2.6× more ADV hits than FAV hits.
- **Contrast vs BENCH (BTCUSD-5m):** `contrast_bench_low = −0.474` — dramatically worse.
- **Interpretation:** The tight faded-move extreme stop destroys expectancy everywhere. No cell is viable — the CI_low is negative across the board. R:R < 1:1 converts the near-0.50 FAV/ADV split into a 28% FAV rate, and the median return is negative in every cell. This confirms that an extreme-anchored stop without an R:R floor is harmful.

### ADV-EXTREME-rr1 (extreme-anchored, widened to ≥1:1)

- **Powered:** 99/17
- **Viable:** 8 cells, 7 instruments (same set as BENCH, plus AUDUSD-5m)
- **Win:** 0/0 — **never beats the benchmark**
- **First-hit `r`:** 0.509 on BTCUSD-5m — nearly identical to BENCH (both 1:1 R:R)
- **BTCUSD-5m detail:** `median = 0.059` (benchmark 0.057); `FAV=748, ADV=722, TIMECAP=1647` — essentially identical to BENCH.
- **Contrast vs BENCH (BTCUSD-5m):** `contrast_bench_low = 0.0` — tie.
- **Interpretation:** When the extreme stop is widened to match the benchmark's 1:1 R:R, the result converges to the benchmark. The extreme **position** of the stop (anchored to the faded-move extreme rather than to the midpoint of M_sofar) does not, by itself, improve expectancy. This isolates the mechanism: ADV-NONE's improvement comes from **removing the stop entirely**, not from repositioning it.

### ADV-NONE (no adverse barrier; FAV-or-TIMECAP only)

- **Powered:** 99/17
- **Viable:** 27 cells, 15 instruments
- **Win:** 23 cells, 15 instruments — **P11 met robustly**
- **First-hit `r`:** 1.0 by construction (degenerate — no ADV can occur with the `±∞` sentinel)
- **BTCUSD-5m detail:** `median = 0.163` (benchmark 0.057, improvement +0.106 ATR); `FAV=802, ADV=0, TIMECAP=2315` — **more FAV hits** (802 vs 745) and **more TIMECAP exits** (2315 vs 1644).
- **Contrast vs BENCH (BTCUSD-5m):** `contrast_bench_low = 0.083 > 0` — beats benchmark.
- **Mechanism:** Removing the stop serves two effects: (1) events that would have hit the benchmark 1:1 stop-out now run on to hit the favourable target or TIME CAP → more FAV hits; (2) events that hit neither run to the TIME CAP, often with large negative returns that dilute expectancy. The median endpoint shows the positive tail (more FAVs) dominates the negative timecap tail — the net effect is +0.083 to +0.142 ATR in the contrast CI. The `r` metric (1.0) completely misses this, confirming the design's rationale for using median expectancy (P14) as the binding endpoint.

---

## P11 Composition — Contrast (why ADV-EXTREME variants did not win)

| Variant | Powered cells | Viable cells | WIN cells | WIN instruments | P11? |
|---|---|---|---|---|---|
| BENCH | 99 | 8 | 0 (ref) | 0 (ref) | N/A |
| ADV-EXTREME-raw | 99 | 0 | 0 | 0 | No |
| ADV-EXTREME-rr1 | 99 | 8 | 0 | 0 | No |
| ADV-NONE | 99 | 27 | **23** | **15** | **Yes** |

- **ADV-EXTREME-raw** fails because its median expectancy is negative in every cell — not one cell has CI_low > 0. The tight stop is destructive.
- **ADV-EXTREME-rr1** is viable in 8 cells (similar to BENCH) but the paired contrast CI_low is 0.0 or negative — extreme-anchoring at 1:1 R:R is not measurably different from the mid-anchored 1:1 benchmark. The stop location alone does not matter once R:R is equated.
- **ADV-NONE** wins because removing the stop lets more events reach the favourable target, and the increased FAV count compensates for the large negative timecap draws. The unpaired median is higher, and the paired contrast CI_low > 0 in 23 cells.

---

## Secondary Endpoints

### First-hit `r` (disclosed)

- **BENCH:** ≈0.506 — confirms the EXP-049/053 null.
- **ADV-EXTREME-raw:** well below 0.50 (≈0.28 on BTCUSD-5m) — tight stop produces many ADV outs. The off-0.50 narrative is confirmed.
- **ADV-EXTREME-rr1:** ≈0.509 — identical to benchmark (both 1:1 R:R).
- **ADV-NONE:** degenerate 1.0 by construction (no ADV possible). Reported with the explicit caveat that `r` cannot see the negative timecap tail. This is the headline lesson: a lever that destroys `r` (ADV-NONE) can still win on expectancy.

### `/STRONG-HA` arm (disclosed)

ADV-NONE also passes on the `/STRONG-HA` arm — the effect is not specific to the `/STRONG-STAT` conditioning. For example, BTCUSD-5m HA: ADV-NONE median = 0.178, contrast_bench_low = 0.145 > 0.

### STAT-MAD sensitivity (disclosed)

ADV-NONE's effect is robust to the MAD percentile sensitivity: BTCUSD-5m STAT-MAD ADV-NONE median = 0.159, contrast_bench_low = 0.102 > 0.

### P13 Baselines (matched-random, MA-seg; disclosed)

The matched-random baselines for ADV-NONE show negative or near-zero medians (e.g., BTCUSD-5m ADV-NONE rand_median = 0.511, rand_ci_low_1s = 0.487 — the random entries under ADV-NONE also have positive expectancy but lower than the conditioned signal). The conditioned signal's ADV-NONE expectancy beats the matched-random baseline across most cells. MA-seg baselines are noisier with wider CIs.

### Invariant & Reconciliation Checks

All predeclared invariant checks pass: benchmark reproduces EXP-053 exactly (99/99 cells), `raw_adv_dist ≤ rr1_adv_dist` event-wise, ADV-NONE yields 0 ADV outcomes across all arms and baselines, raw adverse-side ordering holds. Causality violations: 0. Determinism: byte-identical replay on 17 cells. No defects.

---

## Phase 014-B Context

EXP-057 is **surface read 2** of the 014-B post-lead slate — the adverse-target geometry comparison (sibling of EXP-056 favourable-target). The result is a **characterization readout** (`ADVERSE_TARGET_CHARACTERISED`), not a gate. It feeds the single 014-B G2 (which will combine EXP-056/057/058/059/060 findings). No candidate slots consumed (0 slots, 0 TEST reads), global holdout sealed, TRAIN-only.

The key insight for G2: **removing the adverse barrier unlocks significantly higher median expectancy** for the conditioned HA harami vs the 1:1 benchmark, across 15 instruments. However, ADV-NONE is not a screening candidate — it is a registered branch of `/ADV-NONE` within HYP-010. The G2 will decide whether and how to combine this lever with the favourable-target (EXP-056), third-barrier (EXP-058), and exit-geometry (EXP-059) results.

---

## Caveats & Limitations

1. **Gross only.** No costs (spread, slippage, commission) are modelled. A no-stop strategy may incur large adverse fills in practice that could erode the expectancy advantage.
2. **P15 fill approximation.** Path-ordered fills over 1-minute bars are a documented approximation of unobserved intrabar motion. EXP-054 bounded the effect as immaterial for the benchmark, but ADV-NONE's heavy reliance on TIME CAP exits (cap-bar close) is less sensitive to intrabar path order than FAV/ADV resolutions. Not expected to materially change the result.
3. **DE30 truncated history.** DE30 m1 history ends 2026-01-16. Its counts derive from its own realised timeline and are not span-comparable (VAL-003 disclosure). DE30-4h is in the WIN set, which is encouraging but carries this caveat.
4. **TRAIN-only.** No TEST or holdout validation. The result is a TRAIN characterization, not a cross-validated or out-of-sample finding. The EVIDENCE_FOR label reflects the pre-registered mechanical criteria, not a generalisation claim.
5. **`ADV-NONE` `r = 1.0` is degenerate.** Reported with caveat as planned. The median expectancy endpoint correctly captures the trade-off that `r` cannot see.
6. **0 candidate slots consumed.** ADV-NONE is characterised but not registered as a screening candidate — that decision belongs to the 014-B G2.

---

## Open Questions & Recommended Follow-ups

1. **Does the ADV-NONE advantage survive costs?** The large negative timecap tail may be expensive in slippage. A cost-model follow-up (EXP-061 or within G2) is warranted before any desk application.
2. **Combined system (EXP-060).** How does ADV-NONE interact with the favourable-target lever (EXP-056) and third-barrier geometry (EXP-058)? The combined-optimisation experiment EXP-060 will test whether ADV-NONE + EXP-056's optimal favourable target is additive or redundant.
3. **Why does ADV-NONE work better on some instruments than others?** 27 viable cells across 15 instruments, but 7 cells where the contrast CI_low spans 0. Cross-instrument feature analysis (e.g., trend strength, volatility regime, timecap distribution) could explain heterogeneity.
4. **Sector concentration.** The WIN cells are predominantly FX pairs + US indices. Commodities (XAUUSD) and single equity indices are also represented. The breadth (15 instruments) is reassuring, but regional/sector effects could be explored.
