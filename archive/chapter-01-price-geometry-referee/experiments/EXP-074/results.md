# Results: EXP-074 — TRAIN-Only Substrate-Wide Loser-Tail Characterization (CF-HA-HARAMI-001 / HYP-027)

**Stratum:** TRAIN only `[0, train_cutoff)`. **0 counted TEST reads, holdout untouched.**
**Audit:** CONDITIONAL PASS (`audit.md`) — its two Warnings (W1 feature redundancy, W2 gate
masking) are binding interpretation inputs and are carried below.
**Binding object:** per-domain dual-metric verdict. **Returns:** real-price `N-PARTIAL-V2A` `r_e`
(certified EXP-068 arm). 99 cells, 237,698 events, 67 powered.

---

## Headline (read this first)

**The binding verdict and the pooled verdict both say "no uniform lever," and both are
masking the single most important finding in this experiment.** The H1 exhaustion-magnitude
feature `msofar_atr` (m_sofar/ATR at entry) is a **near-universal, strong separator of the extreme
q05 loss tail** — the exact tail that broke EXP-071's raw mean — but it is **disqualified by the
pre-registered all-framing consistency gate** because its effect is *tail-specific, not
location-monotone*.

> **The feature that explains why the mean dies is precisely the feature the consistency gate
> rejects.**

This is not a contradiction in the data; it is a property of the mechanism (bimodality under
exhaustion) interacting with a gate that was designed to demand distribution-wide monotonicity.
The correct reading is the **stratified, framing-resolved** one below. The pooled `NO_SEPARATOR` is
the trap.

---

## 1. The H1 tail-shape signal (the actual finding)

`msofar_atr` separation of the **extreme tail (TA_q05 = `r_e < q05`)**, across powered cells:

| Domain | Powered cells | TA_q05 share \|eff\|≥0.15 | Median effect (rank-biserial) | Min effect |
|---|---|---|---|---|
| 5m  | 17 | **100%** | 0.705 | 0.677 |
| 15m | 17 | **100%** | 0.781 | 0.680 |
| 30m | 17 | **100%** | 0.787 | 0.633 |
| 1h  | 16 | **100%** | 0.733 | 0.596 |
| 2h / 4h | 0 | — | — | — (underpowered) |

- Rank-biserial **0.68–0.80 ⇒ AUC ≈ 0.84–0.90**. This is a large, not marginal, separation.
- Block-bootstrap 1σ CIs sit far above the material bar in every spot-checked cell (e.g. GBPUSD-5m
  point 0.680, 1σ [0.652, 0.703]; XAUUSD-30m 0.799, 1σ [0.753, 0.840]; BTCUSD-1h 0.724, 1σ [0.666,
  0.773]; EURUSD-15m 0.680, 1σ [0.639, 0.717]). On the q05 framing, `msofar_atr` passes **both** the
  point and the 1σ-CI-material gates in essentially every powered cell.
- **Direction:** positive ⇒ higher exhaustion at entry ⇒ systematically more likely to land in the
  worst 5% of outcomes. High `m_sofar/ATR` means the reversal was taken against a counter-move that
  had already run very far; those entries supply the catastrophic tail.

**On every other framing the effect vanishes or flips:** TA_neg (all losers) ≈ 0, TB_median ≈ 0 to
−0.17, TC (continuous) ≈ −0.07 to −0.22 (i.e. *higher* exhaustion is weakly associated with
*higher* typical return). Concretely (GBPUSD-5m): TA_q05 +0.680, TA_neg −0.012, TB_median −0.056,
TC −0.129.

### Why — the mechanism

Exhaustion is **tail-specific, not a location shift.** Exhausted (stale, mature-move) entries are
**bimodal**: they either work (median-positive — the move keeps going your way after the reversal)
or they go catastrophic (q05 — the counter-move that already ran far keeps running and overruns the
stop structurally). So `msofar_atr` predicts *being in the worst 5%* extremely well, while
predicting *generic loser-vs-winner* not at all. This is exactly the bimodality that made
EXP-071's **raw mean fail while the median and winsorized mean passed** (`mean_recoverable=false`,
entry-structural loss tail). EXP-074 now identifies the **driver** of that tail: entry exhaustion
magnitude.

---

## 2. The gate failure (emphasized)

The cell-level **candidate-separator** definition (pre-registered, D0-amendment-006) requires the
effect to be **directionally consistent across all four framings** (TA_q05, TA_neg, TB_median, TC),
then point ≥ 0.15, then 1σ CI material-side. This all-framing consistency rule is the program's
**anti-p-hacking guard** — and it is correct *for location effects*.

But it is **structurally blind to tail-shape effects.** A feature that separates only the extreme
tail (and is neutral or sign-flipped on the central mass) can *never* satisfy a same-sign-across-all-
framings rule, no matter how strong, robust, and broadly replicated its tail separation is.
Consequence:

- `msofar_atr` → **0 candidate cells in every domain**, `share = 0.00`, `is_uniform_lever = false`
  everywhere — driven entirely by the consistency gate, **not** by weak effects or wide CIs.
- This cascades into the binding per-domain verdict: no feature reaches uniform-lever status, so no
  domain returns SEPARATOR_FOUND.

> The gate, designed to reject signals that appear under only one of several framings (p-hacking),
> here rejects the **one framing (q05) that diagnoses the mean failure** — because that framing
> *is* the question of interest, not a fishing expedition. The pre-registration of H1 + the q05
> framing is what distinguishes this from p-hacking: we are not searching framings for significance;
> the mean-failure mechanism *lives* in the tail framing a priori.

### Governance: the verdict stands as written

We do **not** retro-edit EXP-074's binding gate. The all-framing consistency rule was
pre-registered; relaxing it *after* observing that it is what blocks H1 would be goalpost-moving on
a sealed criterion. **EXP-074's binding verdict stands** — it correctly answered the question it
was registered to ask: *"is there a distribution-wide, location-monotone uniform lever?"* → **No.**

The resolution is **framing + routing, not re-adjudication.** We relabel the binding result as
*"no location-monotone uniform lever; H1 is a tail-shape lever the consistency gate is blind to by
design,"* and we route the gate question into **EXP-075's pre-registration**: a **tail-framing-only
(q05) screen** for the pre-registered H1 lead, designing an exhaustion **cap**, with confirmation
deferred to the sealed holdout.

---

## 3. Binding per-domain verdict (as registered — stands)

| Domain | Verdict | Per-cell sep_rate | Uniform levers | Read |
|---|---|---|---|---|
| 5m  | NO_SEPARATOR | 0.35 | none | noisier; per-cell tail rarely separable under the full gate |
| 15m | SEPARABLE_NO_UNIFORM_LEVER | 0.88 | none | separable core |
| 30m | SEPARABLE_NO_UNIFORM_LEVER | 0.71 | none | separable core |
| 1h  | SEPARABLE_NO_UNIFORM_LEVER | 0.94 | none | separable core |
| 2h  | INCONCLUSIVE_POWER | — | — | 0 powered cells (< 5) |
| 4h  | INCONCLUSIVE_POWER | — | — | 0 powered cells (< 5) |

**Pooled (disclosed-only, non-binding):** NO_SEPARATOR, 67/99 powered. This is the trap line:
pooling 5m noise + underpowered 2h/4h against the 15m–1h core, *and* applying the location-monotone
gate, erases the tail-shape signal entirely. Do not route on it.

**Stratified lens (correct):** the **15m/30m/1h core** is where the tail is separable at the cell
level (sep_rate 0.71–0.94); 5m is noisier under the full gate (0.35) but **still shows 100% q05 H1
breadth**; 2h/4h are simply underpowered (every cell < 30 q05 events). The binding "no uniform
lever" is true *for location-monotone levers* and false *for the q05 tail-shape lever*.

---

## 4. Secondary findings

- **W1 — `favdist_atr` ≡ 0.5·`msofar_atr` exactly** (V2A geometry: the favorable partial barrier
  sits at half the move-so-far; verified ratio 0.5, zero variance, all events). Because rank
  statistics are scale-invariant, `favdist_atr` reproduces `msofar_atr`'s effects/CIs byte-for-byte
  in every cell. **It is not independent corroboration of H1 — it *is* H1.** The effective causal
  feature surface is **13, not 14**. EXP-075 should drop `favdist_atr` as a redundant lever.

- **H2 (harami-polarity agreement) is not supported.** `polarity_agree_ha0` and `polarity_agree_ha1`
  on TA_q05 across all 67 powered cells: median effect ≈ −0.003 / −0.004, **0% of cells clear 0.15**,
  full range [−0.07, +0.08]. Polarity disagreement between the harami's HA direction and the
  MA-segment reversal direction does **not** concentrate the loss tail. H2 is refuted as a separator.

- **Other features:** no causal feature produces a uniform lever under the registered gate; the
  per-domain breadth heatmap (`02_domain_breadth.png`) shows only isolated single-cell hits
  (e.g. `ss_excess_ratio` JP225-5m, `ss_excess_diff` USTEC-5m) — cell-local noise, not substrate
  structure. The strong, broad, replicated signal is `msofar_atr` on the q05 framing alone.

---

## 5. Disposition & routing (CAND-001 / EXP-075)

**Do not close the path.** The q05-tail H1 evidence is strong, broad, and mechanism-grounded — it
identifies the driver of the EXP-071 mean failure. It **motivates EXP-075**, it does not refute the
candidate.

Recommended EXP-075 scope (new experiment, its own D0 — not an extension of EXP-074):

1. **Design an exhaustion CAP**, i.e. an *upper* bound on `m_sofar/ATR` at entry. The current
   substrate gates only a *lower* bound (`m_sofar ≥ p75` via `/STRONG-STAT`); it has no maturity
   cap. The q05-tail evidence says the catastrophic tail lives at *extreme* exhaustion → cap it.
2. **Pre-register the tail framing.** Screen the H1 lead on the **q05 (extreme-tail) framing**, with
   a tail-specific consistency rule for the pre-registered lead — i.e. collapse the all-framing gate
   *in EXP-075's design*, transparently and a priori, not retroactively here.
3. **Band:** the **15m–1h core** (separable at the cell level) is the primary band; **5m is a
   credible inclusion on the tail framing** (100% q05 breadth there too, though noisier under the
   full gate). 2h/4h are underpowered — exclude until power exists.
4. **Drop `favdist_atr`** (≡ 0.5·`msofar_atr`); **do not pursue H2** (polarity) as a separator.
5. **Confirm on the sealed holdout.** EXP-074 spent 0 TEST reads and never touched the holdout; any
   cap must be TRAIN-designed and holdout-confirmed in EXP-075 before it can change the family
   decision. Real-price returns throughout.

---

## 6. Caveats (from audit + methodology)

- TRAIN-only diagnostic; no causal/predictive claim is confirmed here — confirmation is deferred to
  EXP-075's holdout test. The q05 quantile is in-sample per cell.
- Block-bootstrap assumes approximate within-TRAIN stationarity at the block scale (descriptive CI).
- The bimodality interpretation is mechanism-grounded and consistent with EXP-071, but the
  "exhausted entries either work or go catastrophic" framing is an inference from the framing-split
  effects, not a directly fitted mixture — EXP-075 can test the cap's effect on the tail directly.
- Doc nit (audit I2): the TRAIN-cutoff wording is now harmonized to `int(...)` in `scope.md` and
  `analysis-plan.md`, matching the frozen EXP-068/071 convention used by the code (fence-conservative).
  No effect on results.
- Housekeeping (audit I1) — DONE: the orphan `plots/02_separator_share.png` (stale pre-rerun
  pooled-version artifact) was removed; the current plot is `02_domain_breadth.png`.
