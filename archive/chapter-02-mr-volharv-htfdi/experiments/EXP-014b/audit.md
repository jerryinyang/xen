# Audit Report: EXP-014b — CF-MR-004 / HYP-003 (amendment-003 streamlined S8 symmetry rerun)

Forensic/investigative audit of the amendment-003 run (supersedes the amendment-002 audit that
previously occupied this file). Method: independent re-derivation from the **raw emitted parquet**
(not the result JSONs), line-level code verification (C# + Python), per-stratum verdict forensics,
causal-provenance trace, and mechanism explanations for every axis of the design — what robustly
works, what doesn't, and **why**.

**Scope note (stale artifacts).** `data/strategy_runs/EXP-014b-s{5,6,7,8}-*` and the
`EXP-014b-s*-{noneR,allowR,extendR,...}-{fix,trail}.conf` files are the superseded amendment-002
run (Jul 2 15:34). The amendment-003 emission set is `EXP-014b-{1h,4h}-s8-<arm>-<ztag>[-shift]`
(27 dirs, Jul 2 20:55–23:59). `EXP-014b-4h-s8-none` (no z-tag) is a smoke run; `lib.run_root`
builds exact `-z{15,20}` names, so neither the smoke dir nor the stale dirs can leak into the
analysis (verified by name construction, `lib.py:79-83`). Recommend archiving the stale dirs/confs.

## Summary

- **Family outcome audited: `REJECT_LEAK` — direction STANDS.** The two binding reads both fail
  their leak gate somewhere: (a) most 1h availability raw-passes **survive** the peer-feed
  phase-shift (own-price auto-reversion, not a cross-instrument edge); (b) two extend-arm net
  admits **survive** the phase-shift (4h/extend/z15 US2000, 1h/extend/z20 JP225 — shift re-derived:
  admit=True both). No stratum is TRADABLE. Availability is genuinely (collapse-verified) present
  only at **4h EURUSD and 4h JP225**, where tradability is unpowered or fails.
- **Numbers reproduce exactly.** p_inward re-derived independently from raw positions.parquet for
  3 cells (live + shift): byte-identical to `mr_characterisation.json` (§Forensics). Referee rows
  re-derived for the 4 admitting extend cells: identical.
- **2 Critical (analysis-only fix + re-adjudication; no engine rerun):**
  C1 per-stratum status mislabels (unpowered→NOT_TRADABLE; family-wide tripwire contaminating
  per-cell labels), C2 both-leg net uses an equal-weight leg mean instead of the pinned
  spread weighting (A + mean-of-mates) — ~1.7× distortion, sign-flips possible near zero.
  **Neither changes the family REJECT_LEAK outcome** (driven by availability leaks + the two
  surviving extend admits, none of which C1/C2 touch), but per-stratum labels are binding (L-03)
  and feed the registry, so both block Stage 5 until fixed and re-adjudicated.
- **Core exploratory findings (the "why") in §Mechanisms:** S8 basket construction *dilutes*
  rather than adds reversion at 1h; the moving-mean exit converts availability into a
  small-win/large-loss skew (f2 harvest vs f1 anchor-drift losses); extend's net edge is mostly
  own-price MR harvesting (≈halves but persists under decorrelation); both-leg is
  median-profitable but mean-killed by a loss tail + N+1 cost stack.

---

## 1. Scope compliance

| Design item | Verified |
|---|---|
| S8 only, 11 cells, domains {1h,4h}, z* {2.0,1.5}, arms {none,allow,extend,bllim,blmkt} | ✓ 26 confs + 6 shift confs; 220 live cells adjudicated in verdict.json |
| PRIMARY = single-leg none z20; rest disclosure | ✓ `lib.PRIMARY_ARM/PRIMARY_ZTAG`; plots/Holm booked per family |
| Emissions Mode=3 NativeOrders, m1 fills | ✓ run_metadata `execution=native_ctrader_pending_orders_m1` |
| No horizon, no fix/trail; form-2 = moving-mean TP; form-1 = close-confirmed crossing | ✓ Xen.cs:806-815, 1088-1124; metadata `exit_set=form1_event_reversion+form2_moving_mean_limit` |
| Ladder {z*, z*+0.5, z*+1.0} | ✓ metadata `ladder_z_stars=1.5;2;2.5` (z15) / `2;2.5;3` (z20) |
| Fence = EXP-013 first-49% cutoffs, both domains, timestamp-based | ✓ conf `ANALYSIS_END` == EXP-013 cutoffs; `assert_run_within_holdout` on every load (lib.py:113) |
| Frozen referee untuned; per-domain min_state 4h=8 / 1h=20 | ✓ `DOMAIN_SPECS` frozen (1h: min_effective_n=60, min_state=20); no knob passed |
| Trend tercile + vol tercile conditioners emitted per bar | ✓ metadata; slices computed in mr_characterisation |
| No holdout contact | ✓ all loads fence-checked; no code path reads past `analysis_end_utc` |

No undocumented analyses. One deliberate post-design economy, correctly justified in design §3:
availability's shift twin emitted only for `none-z20` (Z is band-independent → both z-triggers read
from one emission); tradability shift twins emitted for `none` and `extend` (the only arms that
produced admits). `allow`/both-leg produced no admits, so their absent shift runs never gate.

## 2. Causal-provenance & leak pass

**Provenance trace (verdict-bearing columns).**
- *Signal/entry*: orders armed in `RearmBracket` (Xen.cs:908-) from `_lastBracket` computed after
  `Observe(logClose_i, feedLog_i)` on the **completed** bar i (Xen.cs:780-786); fills occur during
  bar i+1 via native m1. Decision inputs ≤ bar-i close = ≤ t-1 relative to the fill bar. The
  forming bar's OHLC is never read (`latest = _h4.Count - 2`, Xen.cs:757).
- *Exits*: form-1 compares bar-i close to bar-i anchor, closes at next open (Xen.cs:1088-1101);
  form-2 TP modified at bar-i boundary, favorable-asserted, live from bar i+1 (Xen.cs:1105-1124).
  Both-leg form-1 identical seam (Xen.BothLeg.cs:130-163). Both-leg limit sub-axis: mate limits
  placed only **after** the A fill, at the mate's ≤t-1 close (`MateCloseAt` exact OpenTime match,
  Xen.BothLeg.cs:516-523); atomic partial unwind next bar. No forward index anywhere.
- *Availability inputs*: `_event_arrays` lags Anchor/Dev/Z/Hl by one emitted row
  (mr_characterisation.py:202-205) → decision values are bar i−1's, race runs over bars i..i+H−1
  real Low/High. Event anchor is **frozen at entry** for the race (no moving-anchor contamination
  of the two-barrier read). ✓
- *Outcome/cost*: `assemble_realized_bps` open-to-open with engine fills substituted on
  entry/exit bars (lib.py:155-176); RT cost once per entry from the frozen per-domain map. Both-leg
  cost per leg via `cost_for(LegSymbol, domain)`, raises on unknown symbol.
- *Fill sanity (validate_provenance — run by this audit; the pipeline scripts never call it, see
  I2)*: breach rates entry/exit ≤0.6% (max 23/3719 = 0.6% USTEC 1h extend), far under the 5%
  systematic threshold; mate-gap fraction ≤0.2%. Both-leg positions rows carry NaN fills by design
  (fills live in cis_trades) — leg-level in-bar-range validation is not covered by the helper (I3).

**Leak tripwires (shipped and binding).** Peer-feed phase-shift = `BasketPhaseShiftHours=60`
(60 domain bars back on the basket feed only, `CrossInstrumentBasketFeed` idx − shift,
Xen.cs:1300). Emitted for none-z20 (both domains), extend-z15/z20 (both domains). Result: the
tripwire **fired** — it did NOT collapse everything, and the analysis correctly booked survivors as
REJECT_LEAK rather than passing them (run_experiment.py:229-233, 268-273). The L-01 discipline is
also correctly encoded: raw-pass-without-emitted-control → `AVAILABILITY_UNVERIFIED`/
`TRADABILITY_UNVERIFIED`, never CONFIRMED (run_experiment.py:225-237, 274-281). ✓

**Price-primary check.** All edges engine-generated (native cTrader pending/market orders, m1
fills); Python only ingests emissions. ✓  **Shared modules**: referee_pstar/adaptive consumed
frozen; no xen module regenerates outcomes. ✓

## 3. Verdict forensics (per-stratum re-derivation + masking + mechanism + gate shape)

### 3.1 Independent re-derivation (raw parquet, from-scratch two-barrier implementation)

| Cell | Reported | Re-derived | Shift reported | Shift re-derived |
|---|---|---|---|---|
| 1h EURUSD z2.0 | p=0.508, dec=701, cens=1192 | p=0.508, dec=701, cens=1192 | 0.688 | 0.688 (dec 539) |
| 4h JP225 z2.0 | p=0.696, dec=260, cens=153 | p=0.696, dec=260, cens=153 | 0.541 | 0.541 (dec 111) |
| 1h USDCAD z2.0 | p=0.722, dec=237, cens=1761 | p=0.722, dec=237, cens=1761 | 0.580 | 0.580 (dec 647) |

Referee re-runs for all four Holm-admitting extend cells reproduce net/ci/admit exactly, and the
shift adjudications confirm the REJECT logic:

| Admitting cell | Live net (ci_low) | Shift net (ci_low) | Shift admit | Booked |
|---|---|---|---|---|
| 1h/extend/z15 USTEC | 6.47 (1.73) | 2.74 (0.66) | **False** | collapsed → AVAILABILITY_NULL |
| 4h/extend/z15 US2000 | 14.33 (3.76) | 7.12 (0.22) | **True** | REJECT_LEAK ✓ |
| 4h/extend/z15 GBPUSD | 3.80 (1.27) | 2.67 (0.81) | **False** | REJECT_LEAK ✗ (family-wide splash — C1b) |
| 1h/extend/z20 JP225 | 3.85 (1.11) | 1.67 (0.16) | **True** | REJECT_LEAK ✓ |

### 3.2 Masking check (pooled vs per-stratum)

No pooled headline is booked; the family outcome is an OR over per-stratum leak states, which is
the correct direction for a leak gate (one confirmed leak anywhere → the construction is suspect).
Within-family heterogeneity is real and disclosed below (FX vs index at 1h; EURUSD/JP225 vs rest at
4h). The one masking defect found is the **family-wide tripwire splash** (C1b): `tripwire_ok` is
computed once per (domain,arm,z*) family (`len(survivors)==0`, run_experiment.py:360) and applied
to every admitting cell, so GBPUSD/NZDUSD 4h extend z15 — whose own shift nets collapse — inherit
US2000's REJECT_LEAK. Per-stratum discipline (L-03) requires the per-cell shift verdict.

### 3.3 Mechanism statements (what drove each verdict)

**Availability (the binding question: "reverts beyond a coin flip?").**
- **1h: raw passes are leaks.** Every 1h cell whose raw two-barrier passed (EURUSD z15, GBPUSD z15,
  USDCAD, AUDUSD, NZDUSD, USTEC z15 …) **survives** basket decorrelation — and for EURUSD the
  shift p_inward is *higher* than live (0.508 → 0.688; USDCAD 0.722 → 0.580 stays >0.5). Mechanism:
  at 1h the traded FX price itself mean-reverts after its own extreme moves (bid/ask bounce +
  genuine short-horizon MR; VR(4)≈0.27-0.29, HL 1-2 bars for EURUSD/GBPUSD/CHF/CAD/AUD). The S8
  spread z-score with a *live* basket partially absorbs common-class moves, so live events are a
  *mix* of own-price extremes and basket moves — **the basket dilutes the own-price reversion
  rather than adding cross-instrument signal**. Decorrelate the basket and the event selector
  becomes a nearly pure own-price-extreme detector, which reverts harder. S8's construction adds
  nothing at 1h; what reverts is the leg, not the spread.
- **4h: two genuine survivors, rest null.** 4h EURUSD z2.0 (p=0.589, ci_low 0.520 → shift ci_low
  0.486 collapses) and 4h JP225 z2.0 (p=0.696, ci_low 0.638 → shift 0.541, ci_low 0.450 collapses)
  are the only collapse-verified availability cells. JP225 is the strongest and most coherent cell
  in the experiment (also broad across vol terciles: vol_low 0.719, vol_mid 0.718, vol_high 0.660,
  trend_neutral 0.746). Everything else at 4h is AVAILABILITY_NULL on powered samples.
- **z* axis:** z15 triples decided events (e.g. EURUSD 1h 701→2264) but weakens per-event strength
  (JP225 4h 0.696→0.577) — outliers less extreme revert less. It changes no verdict direction; the
  leak/NULL split is the same. The magnitude axis is not where the edge hides.
- **Sparsity axis (4h→1h):** 1h delivers 3-5× decided events as designed, but the extra power
  only resolves the leak faster. Sparsity was never the binding problem; specificity is.
- **Censoring caveat (W4):** decided-event fractions are low where HL is short — 4h USDCAD 21/427
  decided (95% censored), USDCHF 49/481. H = min(48, ⌈3·HL⌉) with HL≈2-3 domain bars gives races
  only ~6-9 bars to decide a barrier at distance D. The p_inward for those cells describes a small,
  fast-moving subpopulation; their AVAILABILITY_NULL/leak labels rest on thin decided counts even
  when n_events is large. Predeclared (decided≥30 floor), but interpretation must carry this.
- **Time-reversal disclosure is structurally broken (W3):** rev p_inward ≈0.97-1.00 for FX, not
  ≈0.5. Mechanically forced: the reversed window starts at the event bar and walks back through the
  dislocation's own build-up — price *came from* near the anchor, so the reversed race hits the
  inward barrier almost surely. It cannot serve as a ≈0.5 sanity check (US500's 0.41-0.49 reflects
  session gaps, not health). Disclosure-only, no verdict weight; drop or redesign in any follow-up.

**Tradability (the binding question: "net-positive per-stratum under the frozen referee?").**
- **PRIMARY (none, z20): 0 admits anywhere — and the P&L anatomy explains why.** The moving-mean
  exit-set is a small-win/large-loss machine: f2 (intrabar TP at the moving anchor) books many
  small wins (1h: 8-24 bps mean), while f1 (close-confirmed crossing) fires mainly when the
  *anchor migrated to the price* rather than the price to the anchor — those exits average −6 to
  −79 bps at 1h and up to −216 bps at 4h (NZDUSD), with per-trade MAE −100 to −220 bps. form-2 at
  the mean and form-1 are the *same target*; f2 is just its intrabar version, so f1 residual fires
  are precisely the adverse-drift outcomes. Net ≈ 0 gross minus cost → uniform fail. This is the
  concretization of "availability ≠ tradability": even where the two-barrier read is real
  (JP225 4h), D-sized reversion minus giveback minus 4 bps RT ≈ nothing.
- **extend (disclosure): the only net admits — and they are own-price harvesting, not S8.** The
  ladder (z*, z*+0.5, z*+1.0, refresh-R) plus the moving-mean TP turns the strategy into a
  short-horizon MR scalper: thousands of f2 exits (USTEC 1h z15: 4,427 f2 vs 285 f1), episodes
  inflated past min_state, tight CIs. Under the phase-shift the net roughly **halves everywhere
  but stays positive** (6.47→2.74, 14.33→7.12, 3.80→2.67, 3.85→1.67): about half the harvested
  edge needs the live basket (the S8 anchor placing limits at better levels), half is the leg's own
  reversion. Two cells' shift nets still clear the referee → REJECT_LEAK booked. The Holm-admit
  binarization of "halves but persists" is noisy — the honest exploratory read is *one continuous
  phenomenon* (own-price MR harvest, partially basket-assisted) rather than 2 leaky + 2 clean cells.
- **allow (disclosure): 0 admits.** Re-arms the base band only (no deeper ladder); fewer, larger
  positions; the f1 loss tail dominates as in `none`. The ladder depth, not re-entry per se, is
  what manufactures the extend profile.
- **both-leg (disclosure): faithfully captures the spread and still loses.** Per-group anatomy
  (form-1 groups, gross): 4h blmkt JP225 A-leg +30.7, mates −46.7 (equal-mean −27.3; correctly
  spread-weighted −16.0); median group +54 vs mean −16 → a heavy left tail of long-held losers
  (median hold ≈50 bars) destroys a profitable median. Mechanism: the joint form-1 exit is
  close-confirmed with no intrabar limit (no form-2 analogue), so every group gives back overshoot;
  and when the spread reverts *via the basket*, the mate legs are short exactly the move that
  closes the spread. Add N+1 RT costs (L-02) and the arm is structurally cost-heavy at these hold
  lengths. bllim additionally aborts 89/229 groups partial (cancel-on-partial cost drag, −1.2 bps
  mean per aborted leg — correctly included as a faithful cost of the mechanism). 1h both-leg z20
  powered 1-5/11 cells only.
- **Conditioner slices (informative):** the strongest availability pockets are **with-trend
  extensions at 4h FX** (NZDUSD 4h z2.0 with_trend p=0.910 ci 0.846 n=78; AUDUSD 0.687; GBPUSD
  0.651; US2000 0.652 z15) and **vol_low** (EURUSD 4h 0.742, NZDUSD 0.738) — over-extensions in
  the trend direction snap back, quiet regimes revert; counter-trend slices are mostly unpowered
  (strong-trend + opposite-side events are rare; the per-cell tercile fix works but the joint
  condition starves). 1h USDCAD is strong across almost all slices — consistent with its leak
  profile (own-price MR), not with a cross-instrument story.

### 3.4 Gate-shape check

- The two-barrier proportion + iid bootstrap matches the availability effect's shape (per-event
  binary, race symmetric by construction; null=0.5 sound under driftless-symmetric first passage;
  ambiguous dropped ~0, censored disclosed). No shape blindness found. One structural note: with a
  frozen entry anchor, drift *away* during the race is symmetric, so conditioning bias is avoided —
  the control replacement (vs the degenerate amendment-002 control) is genuinely valid.
- The frozen mean-based referee is the right shape for the extend arm's many-small-wins profile
  (it admitted it), and its `l1` effective-n floor correctly disqualifies sparse arms. But for the
  **both-leg** arm, mean-based adjudication over a median-positive/tail-negative distribution reads
  NOT_TRADABLE at the mean — true for deployment (means pay), but interpreters should know the
  median group is profitable: the failure is tail control, not absence of capture. Recorded for
  the interpreter; no gate retro-edit.
- **Bite-check non-vacuity (W2):** the per-cell F2 fix is correctly implemented (planted +8 bps
  per active bar / per settlement episode, gated only on admitting cells). But the plant is
  detected in under half the strata (123/220 planted_fail, 3 unpowered-for-plant) — mostly the
  sparse ones (both-leg families, 1h z20 USDJPY, 4h z20). In those strata the referee could not
  see even an 8 bps true edge, so their "net fails" component is *absence of evidence*. No admit
  was gated by a failing bite (the 4 admits' bite passed), so no verdict moved — but per-stratum
  labels should disclose bite-fail (folded into C1's fix).

## 4. Findings

### C1 (Critical, verdict-material at stratum level; analysis-only fix + re-adjudication)
`cell_status` (run_experiment.py:262-288) mislabels strata in three ways:
1. **Unpowered → NOT_TRADABLE.** The `avail_confirmed and not holm_admit_net → NOT_TRADABLE`
   branch precedes the power check, so 14 of the 15 NOT_TRADABLE cells (all 4h EURUSD/JP225
   variants except 4h/extend/z15 JP225) have `powered=False` (referee `l1` effective-n < 60 or
   epi < min_state) yet are booked as a credible negative. Design §10: UNPOWERED never FAIL.
2. **Family-wide tripwire splash.** `tripwire_ok` computed per family, not per cell
   (run_experiment.py:359-360): GBPUSD + NZDUSD 4h/extend/z15 booked REJECT_LEAK although their
   own shift nets collapse (re-derived: shift admit=False both). Their honest labels are
   NOT_TRADABLE-class/collapsed, and the family's leak evidence rests on US2000 alone.
3. **Bite-fail not disclosed** on negative reads (W2 above).
Fix `cell_status` (+ per-cell `phase_shift_survivors`), re-run `run_experiment.py` only.
**Family outcome will remain REJECT_LEAK** (availability leaks at 1h and the US2000/JP225 net
survivors are untouched), but the registry rows must carry correct per-stratum labels.

### C2 (Critical, verdict-material for both-leg strata; analysis-only fix + re-adjudication)
`_both_leg_group_nets` (lib.py:179-200) takes the **equal-weight mean over N+1 legs**; the pinned
semantics (design §5, Xen.BothLeg.cs:33-36 contract, and the emitted per-bar `MtmBps` which does
it correctly at Xen.BothLeg.cs:373-396) is **A + (1/n)·Σ mates** — matching the actual notional
sizing (each mate carries A-notional/n, Xen.BothLeg.cs:499-513). Verified distortion: JP225 4h
blmkt gross −27.32 (equal-mean) vs −15.99 (spread-weighted) per group — a ~1.7× compression toward
the mate average that can flip signs near zero (e.g. EURUSD 4h blmkt group mean −0.89). Cost must
be re-weighted identically (cost_A + (1/n)·Σ cost_mate, matching per-leg notionals). All both-leg
strata re-adjudicate; realized-vs-MTM consistency restored.

### W1 (Warning — shown non-verdict-moving)
Extend/allow per-bar realized series is a **one-unit netting approximation**: `Position ∈ {−1,0,1}`
while the ladder holds up to 3 legs, and RT cost is charged once per entry *bar* though multiple
ladder legs can fill (USTEC 1h z15: 4,729 leg entries vs 3,719 charged entry bars → ~21% of leg
costs uncharged; 41 multi-fill timestamps). Materiality: correcting cost pro-rata trims USTEC's
net 6.47 → ≈6.1 (ci_low 1.73, referee p≈0) and GBPUSD 4h 3.80 → ≈3.7 — no admit flips, and the
REJECT_LEAK direction is cost-independent (shift survival is relative). Disclosure arms only.
Flag if any extend variant is ever promoted to primary.

### W2 (Warning) — bite-check plant undetectable in 123/220 strata (§3.4). No admit was gated by a
failing bite; disclosure folded into C1.

### W3 (Warning) — time-reversal disclosure control structurally ≈1.0, uninformative (§3.3).
Disclosure-only; never gates. Remove/redesign in follow-ups.

### W4 (Warning) — extreme censoring in short-HL cells (4h USDCAD 95%, USDCHF 90%) makes those
availability reads describe a fast-deciding minority. Predeclared floor respected; carry the caveat
into report.md.

### I1 (Info) — stale amendment-002 run dirs + confs and the `EXP-014b-4h-s8-none` smoke dir are
present but provably unreachable by the loaders; archive for hygiene.
### I2 (Info) — `lib.validate_provenance` exists but is never invoked by the pipeline scripts;
this audit ran it (all clean). Wire it into `run_experiment.main` so future runs self-check.
### I3 (Info) — both-leg leg fills (cis_trades) are not covered by the in-bar-range validator
(positions rows carry NaN fills by design). Extend the helper if both-leg is pursued.
### I4 (Info) — `no_data_verdict`/NO_DATA path (L-03 placeholder) present and unexercised (0
NO_DATA cells; all 220 emissions complete, 0 harness failures).

## 5. What robustly works / what doesn't (exploratory synthesis for the interpreter)

**Works (survived hostile checks):**
1. The symmetry two-barrier control itself — self-contained, reproduces exactly, ambiguity ~0,
   and it successfully *separated* generic reversion from construction-specific reversion when
   paired with the phase-shift (the thing the amendment-002 control could not do).
2. 4h JP225 (and weakly 4h EURUSD) cross-instrument availability — the only collapse-verified
   reversion, broad across vol regimes for JP225.
3. With-trend + vol_low 4h FX availability pockets (NZDUSD 0.91) — strongest conditioned signal
   in the data, currently unexploited by any arm.
4. The L-01 discipline in code: absent control ⇒ UNVERIFIED (never CONFIRMED), survivors ⇒ REJECT.

**Doesn't work (with mechanism):**
1. S8 at 1h — the basket *dilutes* own-price MR; every raw availability pass is a specificity leak.
2. The moving-mean exit-set as a P&L engine — f2 small wins vs f1 anchor-drift large losses nets
   to ≈0 gross before cost, everywhere, both domains.
3. extend as evidence of S8 tradability — it is a short-horizon own-price MR harvester whose edge
   only ~halves under basket decorrelation.
4. Both-leg under joint close-confirmed exit — median-profitable spread capture destroyed by an
   unhedged loss tail (~50-bar holds) plus N+1 costs; entry mode (limit vs market) is second-order
   next to the missing tail control (no intrabar exit, no stop).
5. Counter-trend conditioning as a rescue — structurally starved of events at both z*.

## 6. Blocking decision

**BLOCKED for Stage 5 until C1+C2 are fixed and `run_experiment.py` re-adjudicated**
(analysis-only; mr_characterisation.json is unaffected; no engine rerun — the emissions are
sound). Expected post-fix family outcome: REJECT_LEAK unchanged; both-leg strata re-labeled with
correct spread-weighted nets; ~16 stratum labels corrected. After re-adjudication, report.md may
proceed with the §5 synthesis and the registry booking of: availability leak (1h, REJECT-class for
the S8-at-1h thesis), 4h EURUSD/JP225 availability-confirmed-not-tradable(-unpowered), extend
own-price-harvest leak, both-leg tail-failure characterisation.

## Post-fix addendum (2026-07-03 — C1+C2 applied, re-adjudicated)

- **C1 fixed** (`run_experiment.py`): `phase_shift_results` now returns a per-cell shift verdict
  (True=survived/leak, False=collapsed, None=control missing); `cell_status` books
  NOT_TRADABLE only when the referee is powered **and** the bite plant was detected
  (`trad_credible`), else UNPOWERED_TRADABILITY/UNPOWERED.
- **C2 fixed** (`lib._both_leg_group_nets`): group net = `A_net + mean(mate_nets)` (pinned spread
  weighting, matches sizing + emitted MtmBps); `instrument` threaded through
  `both_leg_realized_{bps,series}` and callers.
- **Re-adjudicated (analysis-only): family outcome `REJECT_LEAK` UNCHANGED, 0 TRADABLE.** Status
  census: AVAILABILITY_NULL 152, REJECT_LEAK 53, UNPOWERED_TRADABILITY 14, NOT_TRADABLE 1
  (4h/extend/z15 JP225 — the only powered+non-vacuous negative). Label corrections realised:
  GBPUSD 4h/extend/z15 → AVAILABILITY_NULL (its own shift net collapses); NZDUSD 4h/extend/z15
  keeps REJECT_LEAK on its **own** shift admit (verified per-cell, no longer US2000 splash).
  Both-leg nets re-weighted (e.g. JP225 4h blmkt −31.3 → −24.0; several sign changes); still 0
  both-leg admits. mr_characterisation.json untouched (availability unaffected by C1/C2).
- **Operator direction:** Stage 5 documentation deferred; amendment-004 (lean single-leg bracket
  redesign) is being designed for a rerun first — report.md will cover both.

## Reproduction notes

- Independent re-derivations: scratchpad `rederive.py` / `dive2.py` (session scratchpad), run with
  `python/.venv/bin/python`; p_inward from-scratch implementation matches
  `results/mr_characterisation.json` exactly (3 cells × live+shift).
- Referee re-runs: `lib.load_cell(...)` + `run_experiment.adjudicate` on live and `-shift` dirs.
- Both-leg weighting evidence: per-group equal-mean vs A+mean(mates) on
  `EXP-014b-4h-s8-blmkt-z20/...jp225...` cis_trades (34 form-1 groups).
- Cost-undercount evidence: `EXP-014b-1h-s8-extend-z15/...ustec...`: 4,729 cis rows vs 3,719
  non-NaN `EntryFillPrice` bars.
