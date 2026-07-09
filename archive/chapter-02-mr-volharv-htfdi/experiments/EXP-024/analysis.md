# EXP-024 — Analysis (CF-CSRR-001 / HYP-002b — US-bloc session-anchor availability primary)

> **Stage 5 deliverable (INFR-001 pipeline).** Data-analyst evidence for+against per stratum +
> a **recommended, NON-FINAL** verdict. The **operator renders the final experiment verdict.**
> No estimand-validation gate applies (availability screen, no P&L/accounting object — design §9);
> integrity gates (holdout, causal ≤t-1/open-to-open, tripwire, no-local-accounting) were
> QA-verified in `qa-review.md` run 1 (design) + run 2 (code, R1 resolved).

**Construction (frozen, pre-registered):** R_US bloc {USTEC, US500, US2000, US30} · anchor S
(session-open) · A=median · B=raw · C=all>k (primary, powered) · D=hedged (idio=g_i−G) ·
h_i=clamp(round(2·HL_i),[1,12]). Binding bar (design §6): hardened block-boot CI (10k×5-seed,
block≥h_i, block_sensitivity ½/1/2×, trimmed_mean) at the ≥1 bp band. **TRAIN only (first 49%);
0 reads, 0 slots; holdout sealed.**

**§0 honesty (controlled thesis-shopping):** EXP-022 selected USTEC post-hoc as the best of
10×6 on TRAIN; re-testing on the SAME TRAIN is in-sample. This experiment is legitimate only as
a *controlled* follow-up — frozen construction, 4-member Holm family, binding bar = the hardened
CI USTEC previously FAILED. **A TRAIN pass would NOT be out-of-sample confirmation.** The result
here can only decide whether USTEC is worth an EXP-023 tradability read; it cannot confirm.

Emission: `results/{cell_reads,substrate,robustness,holm,golden_trace,summary}.*`
(union 3174 4h bars; 2200 all>k events; 1562 single-worst events; run 2026-07-06, PYTHONHASHSEED=0).

---

## 1. Substrate — is the consensus residual mean-reverting? (disclosure)

| Member | n | VR(2) | VR(6) | autocorr(1) | HL (4h-bars) | h |
|---|---|---|---|---|---|---|
| USTEC | 3164 | 0.974 | 0.549 | 0.685 | 1.83 | 4 |
| US500 | 3042 | 0.890 | 0.462 | 0.636 | 1.53 | 3 |
| US2000 | 3158 | 0.920 | 0.511 | 0.676 | 1.77 | 4 |
| US30  | 3164 | 0.949 | 0.542 | 0.685 | 1.83 | 4 |

**Read:** All 4 members show VR(2)<1 and VR(6)<1 with positive lag-1 autocorrelation decaying
over ~1.5–1.8 4h-bars → the session-anchored consensus residual **is mean-reverting** on the US
bloc (substrate PASS, as in EXP-022). This supports the *premise* (residual reverts) but says
nothing about whether fading the dislocation earns idiosyncratic forward return — that is the
binding cell below. HL values give h≈3–4, consistent with intraday reversion scale.

---

## 2. Binding cell — all>k / hedged (the design §6 bar; per member)

All values bps of idiosyncratic forward return; hardened block-boot CI, block=h_i, 10k×5-seed.
`block_sens` = ci_low at [½h, h, 2h]; `tmean` = 20%-trimmed mean CI. `ri`/`rt` = random-index /
random-timing twins (25-seed battery); collapse = twin/raw (L-15). tripwire = temporal
block-permute mean (block=12≥h; MUST collapse to ≈0).

| Member | n | h | mean ρ | CI [lo,hi] | tmean | tmean_ci_lo | MDE | blk_sens[½h,h,2h] | p_perm | Holm | ri_twin | rt_twin (pct) | tripwire |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| USTEC | 800 | 4 | +1.08 | [−3.75, +5.88] | +1.35 | −2.50 | 4.83 | [−3.10,−3.75,−4.22] | 0.171 | 0.684 | −0.78 | −0.47 (0.84) | +0.08 |
| US500 | 39 | 3 | +4.34 | [−0.02, +9.49] | +3.22 | −0.81 | 4.35 | [+0.51,−0.02,−0.30] | 0.323 | 0.969 | +0.93 | +0.21 (0.96) | +0.31 |
| US2000 | 857 | 4 | +0.65 | [−4.43, +5.75] | +1.17 | −3.02 | 5.08 | [−3.87,−4.43,−4.26] | 0.329 | 0.969 | −0.45 | +1.46 (0.32) | −0.02 |
| US30 | 504 | 4 | +0.10 | [−4.95, +5.20] | −1.19 | −4.29 | 5.05 | [−4.47,−4.95,−4.92] | 0.601 | 0.969 | +0.87 | +1.06 (0.32) | +0.25 |

**§7 SUPPORTED band requires ALL of:** mean ρ ≥ +1 bp **AND** hardened ci_low > 0 (5-seed,
block-stable) **AND** both-halves sign-stable **AND** beats BOTH twins (Δ>0) **AND** p_perm
Holm-significant **AND** tripwire collapses. **No member meets this.**

### USTEC (the power question)
- **For:** mean ρ = +1.08 bp (clears the ≥1 bp floor); sign-stable across both temporal halves
  (first +0.13, second +2.02) and across all three horizons (h=2:+0.80, h=4:+1.08, h=5:+1.69,
  all +, rising); tripwire collapses (tripwire mean +0.08 bps ≈ 0, collapse 0.075); beats the
  random-timing twin (rt +0.47 below signal, percentile 0.84).
- **Against:** hardened ci_low = −3.75 (< 0 — CI does NOT exclude zero); trimmed-mean ci_low =
  −2.50 (< 0); block_sensitivity all negative across ½h/h/2h (block-fragile the other way —
  no block length clears zero); p_perm = 0.171, Holm = 0.684 (not significant); **MDE 4.83 >
  effect 1.08 → UNPOWERED by the MDE>effect criterion** — the effect sits *at* the detection
  floor, not above it; random-index twin (−0.78) is *below* the signal (Δ>0 on this twin) but
  the random-timing twin is the closer call.
- **Band:** effect-at-MDE. Not SUPPORTED (ci_low<0, not Holm-sig, MDE>effect). Predeclared as
  the key trade-off (§8): all>k admits moderate dislocations → per-event effect falls below
  single-worst's +4.7 bps even as n rises. **Confirmed: effect diluted to the MDE.**

### US500 (predeclared UNPOWERED)
- n = 39 < 100 → **UNPOWERED by the n<100 criterion (B-5, never a negative).**
- For what it is worth: mean +4.34, ci [−0.02, +9.49] (ci_low *just* below zero — 0.016 bps);
  block_sensitivity even flips positive at ½h (+0.51). Both-halves flip (first +9.50, second
  −0.57) — unstable. Not a read.

### US2000
- **For:** mean +0.65 (positive but < 1 bp floor); sign-stable halves (first +1.06, second
  +0.24) and horizons (+0.57, +0.65, +1.34, all +, rising); tripwire collapses (−0.02 ≈ 0).
- **Against:** ci_low = −4.43 (< 0); p_perm 0.329, Holm 0.969; **MDE 5.08 >> effect 0.65 →
  UNPOWERED by MDE**; the random-timing twin (+1.46) *beats* the signal (rt_percentile 0.32,
  collapse 2.25 — the twin is larger) — the signal does not separate from random timing.
- **Band:** UNPOWERED (MDE>effect); not SUPPORTED.

### US30
- **Against (strong):** mean +0.10 (≈ 0, < 1 bp); ci [−4.95, +5.20]; both-halves FLIP (first
  +3.18, second −2.98) → not sign-stable; BOTH twins crush the signal (ri +0.87, rt +1.06;
  collapse 8.9 / 10.9 — the signal is far *below* random); MDE 5.05 >> effect.
- **Tripwire note:** tripwire mean = +0.25 bps ≈ 0 (collapses as required — no leak); the
  *collapse fraction* (2.62) is numerically unstable because the observed effect is itself ≈0,
  so the ratio divides a near-zero denominator. The integrity check is the tripwire *mean* ≈ 0,
  which holds; the ratio is not informative here.
- **Band:** WASH / UNPOWERED; not SUPPORTED. The strongest AGAINST read in the bloc.

---

## 3. Single-worst continuity (the exact EXP-022 lead form; disclosed, lighter 2k CI)

| Member | n | mean ρ | CI [lo,hi] | p_perm | tripwire |
|---|---|---|---|---|---|
| USTEC | 573 | +4.26 | [−1.15, +9.61] | **0.009** | +0.019 (collapse 0.004) |
| US500 | 6 | −2.97 | [−4.21, −1.74] | 0.541 | −0.22 |
| US2000 | 693 | +1.35 | [−4.29, +7.01] | 0.205 | −0.17 |
| US30 | 290 | −2.13 | [−8.56, +4.81] | 0.831 | +0.33 |

**This is the decisive continuity check.** EXP-022's USTEC lead was: permutation-significant
(p small) but **hardened block-boot ci_low < 0** (it FAILED the binding bar there: ci_low −0.58,
effect ≈ MDE 5.28). EXP-024 **reproduces that pattern exactly on USTEC**: p_perm = 0.009
(the permutation null lights up — the residual *is* predictively paired to its own forward
idio beyond a random pairing) **but the hardened CI still does not exclude zero** (ci_low −1.15).
Tripwire collapses cleanly (0.004). So under the more extreme (single-worst) selection the
effect is larger (+4.26 bps) and the permutation is significant, yet the honest block-bootstrap
CI — the binding bar the design froze — **still fails**. The lead does NOT clear the binding bar
even at the selection that maximises it. No sibling reproduces the pattern (US2000 p_perm 0.205,
US30 0.831, US500 n=6 UNPOWERED).

---

## 4. Robustness (disclosed; sign-stability only — no second primary)

**Both temporal halves (binding all>k):**
- USTEC: +0.13 / +2.02 → **sign-stable** (+/+).
- US2000: +1.06 / +0.24 → **sign-stable** (+/+).
- US500: +9.50 / −0.57 → flips (UNPOWERED, n=19/20).
- US30: +3.18 / −2.98 → **flips** (not stable).

**Horizon 1/2/3·HL (binding all>k, sign):**
- USTEC: +0.80, +1.08, +1.69 → **stable +, rising** with horizon.
- US2000: +0.57, +0.65, +1.34 → **stable +, rising**.
- US500: +2.32, +4.34, +4.03 → stable + (UNPOWERED).
- US30: −0.59, +0.10, +1.58 → **flips at h=1** (unstable short horizon).

**Read:** USTEC and US2000 are directionally robust (sign holds across halves and horizons,
rising with horizon — consistent with reversion arriving over a few bars). US30 is not robust
(flips both ways). US500 is too thin to read.

---

## 5. Golden trace (QA-diffed; first 3 all>k events post-warmup)

First event 2021-07-06 16:00 UTC, all 4 present. USTEC s=+0.0091 > k=0.0038 → fade=−1,
h=4, g_i=+0.0093, G=+0.0053, idio=+0.0040, ρ=−39.6 bps (the fade was wrong — residual
*continued* on this one event). US2000 at the same bar s=−0.0093 → fade=+1, idio=−0.0021,
ρ=−20.5 bps (also wrong). Second USTEC event 20:00: ρ=+1.34 bps (reverts). Single events are
noisy; the trace confirms the construction is causal (inputs ≤ t, forward from Open(t+1),
session anchor, |s|>k fired) and the rho bit-for-bit matches the emission — QA's integrity check,
not a verdict input.

---

## 6. Evidence synthesis + RECOMMENDED verdict (NON-FINAL — operator decides)

### What supports the hypothesis (FOR)
- **Substrate:** the residual mean-reverts on all 4 US-bloc members (VR<1, HL ~1.8) — the
  premise holds.
- **USTEC directional robustness:** sign is stable across both temporal halves and all three
  horizons, rising with horizon; tripwire collapses (no leak); the permutation null is beaten
  at the single-worst selection (p_perm 0.009) — there *is* a cross-sectional i→i linkage.
- **US2000 directional robustness:** sign stable halves+horizons; tripwire collapses.

### What contradicts / dilutes (AGAINST)
- **No member clears the binding bar.** Every powered member has hardened ci_low < 0 and is
  not Holm-significant. The predeclared §8 trade-off is **confirmed**: all>k admits moderate
  dislocations → the per-event effect diluted from single-worst's +4.26 bps to +1.08 bps
  (USTEC), landing *at* the MDE (4.83) rather than above it. Power bought n but spent effect.
- **USTEC fails the hardened CI even at single-worst** (ci_low −1.15) — the same bar it failed
  in EXP-022. The permutation-significant read that lit the lead is *not* the binding read; the
  honest block-bootstrap CI does not exclude zero. Per design §0, this is the bar that matters.
- **US2000 does not separate from random timing** (rt twin +1.46 > signal +0.65; percentile
  0.32) — the signal is not distinguishable from firing at random times.
- **US30 is ≈ random** (mean +0.10; both halves flip; both twins beat the signal by ~10×).
- **US500 is UNPOWERED** (n=39 < 100) as predeclared.
- **No sibling supports:** even on the lenient permutation read, only USTEC lights up; the
  mechanism is not a bloc-level regularity, at most a single-instrument idiosyncrasy.

### Recommended verdict (per member + overall) — NON-FINAL

| Member | Recommended band | Basis |
|---|---|---|
| USTEC | **WASH (effect-at-MDE)** | mean ≥ 1 bp, sign-robust, tripwire clean, perm-significant at single-worst — but hardened ci_low < 0 at BOTH selections, not Holm-sig, MDE > effect. Not SUPPORTED; not a refutation (sign holds, no leak). |
| US500 | **UNPOWERED** | n=39 < 100 (B-5, never a negative); predeclared. |
| US2000 | **UNPOWERED** | MDE 5.08 >> effect 0.65; rt-twin beats signal; ci_low < 0. |
| US30 | **WASH / UNPOWERED** | mean ≈ 0; halves flip; both twins crush signal; MDE >> effect. |

**Overall recommended (non-final) verdict: NOT SUPPORTED at the binding (all>k/hedged)
construction.** The substrate reverts, but fading the dislocation does not earn an idiosyncratic
forward return that clears the hardened CI on any member; the powered members are UNPOWERED-by-MDE
(the all>k effect dilutes to the detection floor). The single-worst continuity reproduces
EXP-022's USTEC pattern — permutation-significant but hardened-CI-fails — so the lead does NOT
clear the binding bar even at the selection that maximises it, and no sibling reproduces it.

This maps to design §7's operator read: **"USTEC still fails the hardened ci_low even powered →
effect-at-MDE confirmed → retire evidence."** On this evidence, **graduation to an EXP-023
tradability read is not warranted.**

### Operator's decision space (informative; not exhaustive)
- Accept NOT SUPPORTED → the USTEC lead is retired at 0 cost (0 reads/0 slots spent); family
  disposition → checkpoint-009 retrospective.
- Judge the USTEC direction-robust + perm-significant single-worst read as worth a tradability
  read anyway (operator discretion — the binding bar is the design's honest call, but the
  operator judges value, and may weight the stable sign + perm result differently).
- Order a follow-up probe (e.g. a different k/threshold regime) — but note §0: a re-parameterised
  re-test on TRAIN is controlled-thesis-shopping and must be registered as a new branch before
  screening; no scope expansion after QA APPROVE on EXP-024.

**Reminder (§0):** this is TRAIN-only, in-sample-honest. Even a pass here would not be
out-of-sample confirmation. The failure of the binding bar on TRAIN is, however, a clean
honest signal that the lead is effect-at-MDE, not a tradable edge.
