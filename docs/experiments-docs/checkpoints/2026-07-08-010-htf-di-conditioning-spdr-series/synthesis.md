# SPDR CTRL-01/02/03 Series — Cross-Leg Synthesis (CORRECTED 2026-07-08)

> **CORRECTION NOTICE.** This synthesis was rewritten in place on 2026-07-08 after an independent
> audit + correction probe (`correction/` in this checkpoint). Two defects invalidated parts of
> the original read: (1) SPDR-001's CIs on the overlapping per-bar estimand used block=5 against a
> dependence length ≈ H — all CI-clearance calls and CI-counts were re-derived with hold-matched
> blocks; (2) SPDR-003's "DI conditional-mean spread" was computed on the side-signed reversion
> return, not the labelled raw forward move. Net effect: **the continuation thread (USTEC 1h/5min)
> survives fully; the fade thread (XAUUSD) is NOT SUPPORTED by the corrected evidence.** The
> original operator disposition (§8, two tiered threads) is superseded by the corrected
> disposition below.

**Series:** SPDR-001 (random base) · SPDR-002 (naive-momentum base) · SPDR-003 (naive-reversion,
causal m1 limit-fill). Source idea `.ignore/temp/new-research/mtf.md`. Lane: SPDR (TRAIN-only,
0 reads, 0 holdout touch, no family). All three legs `analysis.md`-binding (each corrected in
place, see their headers), integrity all-pass — the integrity machinery (TRAIN fence, HTF-bar
boundary, t−1 lag, m1-fill causality, seed batteries) was audited directly in code and confirmed.

**Shared falsifiable question.** Does higher-timeframe context (DI direction, ADX strength, ATR
vol regime) carry its **own conditional effect** on the LTF forward-return distribution — and does
it hold **across base-strategy type** (null / momentum / reversion)?

**Status:** all three legs CHARACTERISED; corrected. Each leg's fresh-context analyst ran BLIND of
the others (only causal primitives reused); the correction probe re-measured registered quantities
only (no new estimand freedom).

---

## 1. The corrected finding — one CI-clear axis, one amplifier, no established fade

| Axis | Conditions | Corrected read across legs |
|---|---|---|
| **DI (direction)** | the **mean** | **CI-clear continuation on USTEC 1h/5min only**: random base +0.09→+0.50 ATR dir_gap, CI-clear all holds at block=H; momentum base +0.26→+0.39 CI-clear H24–H48 (independent blind replication, non-overlapping trades). BTC 1h/5min CI-clear H12–36 but LTF-shared (discounted). **No CI-clear negative (fade) cell anywhere** on the corrected grid. |
| **ADX (strength)** | *hypothesised* dispersion | unchanged: single-leg (002) design hypothesis, not an established axis. Weak/flat on the mean everywhere. |
| **ATR (vol)** | dispersion (mostly normaliser mechanic) + **amplifies** DI | direct dispersion read ~1.5× normaliser artifact (established, 3 legs). Interaction **corrected**: high-vol **amplifies** continuation (BTC `atrH_adxHi_di` +0.12→+0.41, CI-clear all holds at block=H); the low-vol negative branch is **not CI-clear at any hold** — "ATR sets the sign" was an over-read. |

Pure symmetric-sign gating (ADX-only, ATR-only, no DI) is weak-to-null on the mean on every leg —
the built-in null sentinels behaved as null on location.

## 2. The reproducible candidate — USTEC 1h/5min HTF-DI continuation (unchanged by correction)

The single stratum that replicates across two independent blind bases and survives every guard,
**including the corrected statistics**:

| Guard | Random base (001) | Momentum base (002) |
|---|---|---|
| DI conditional-mean shift | **+0.09 → +0.50 ATR** (H12→H48) | **+0.26 → +0.39 ATR** (H24→H48; H12 +0.07 n.s.) |
| CI-clear under corrected blocks | yes — all four holds (H48 edge [+0.083,+0.416] at block=H) | yes — H24/36/48 (non-overlapping trades) |
| HTF-specific (vs LTF-momentum twin) | yes — partial +0.253, wins conflicts (CIs block=5-optimistic; direction corroborated by mis-aligned control) | (between-state effect, not base-confounded) |
| Mis-aligned-HTF control | aligned +0.046→+0.248; mis-aligned +0.009→−0.054 (dies/reverses) | — |
| Phase-shift Control B/C | collapses | collapses (DI lift arms 0.21–0.44 or sign-flip) |
| Breadth (84 DI-axis cells, block=H) | **9 CI-clear positive / 0 negative** | — |
| Grows monotonically with hold | yes | yes |

**Ranked continuation candidates (Thread A), corrected:**

| Rank | Stratum | Magnitude | Status after correction |
|---|---|---|---|
| 1 | **USTEC 1h/5min** | +0.09→+0.50 ATR | **intact** — the sole fully-supported stratum; dense (n>170k), replicated, breadth 9+/0− |
| — | EURUSD 1d/1h | +0.27→+0.47 ATR (point) | **demoted** — no hold CI-clear at block=H (H48 edge [−0.167,+0.684]); a power statement (B-5), carried only as a candidate stratum to power up in the graduation experiment, not screen evidence |
| — | BTCUSD 1h/5min | +0.09→+0.27 | CI-clear H12–36 at block=H but mostly shared with LTF autocorrelation (LTF-own +0.20 > HTF +0.13, loses conflicts) — remains discounted |

## 3. The fade branch — NOT SUPPORTED by the corrected evidence

The symmetric-estimand logic stands: on a null base `dir_gap = 2·Cov(htf_dir, m)`, and a genuine
CI-clear −0.41 would carry exactly as much conditioning information as a +0.41, traded in reverse.
**The corrected data contain no such negative.** Every pillar of the original fade thread fails:

| Original pillar | Corrected result |
|---|---|
| XAUUSD sign-count fingerprint 6+/**17−** of 84 (001) | **4+/3−** at block=H — the fingerprint was an under-blocking artifact |
| XAU 1d/1h H24 **−0.86** [−1.54,−0.17] n541 (003), "powered fade cell" | wrong estimand (side-signed strategy × DI interaction). Raw-move conditioning: **−0.083 [−0.68,+0.53] n.s.**, both half-splits n.s. The interaction itself is half-unstable (first half n.s.) |
| EURUSD 1h/5min −0.05→−0.13 "CI-clear H36/48" (001) | not CI-clear at block=H (H48 [−0.212,+0.073]) |
| BTCUSD 1d/1h −0.18→−0.41 "CI-clear H48" (001) | not CI-clear at block=H ([−0.736,+0.330]) |
| BTC low-vol branch −0.22 "sign flip" (001 §4) | not CI-clear at any hold ([−0.583,+0.129] at H48) — no established reversal branch |
| XAUUSD conflict subset −0.109 [−0.202,−0.018] (001 Thread 1) | block=5-optimistic CI on the overlapping estimand; unverified at block=H; at best marginal |

All fade-signed magnitudes remain in the record as **point estimates with CIs including zero** —
power statements, not evidence-against and not evidence-for (B-5). If a future, adequately powered
measurement produces a real CI-clear negative dir_gap, the fade reading revives with full force;
nothing here forecloses it.

## 4. Why the surviving thread is not a lucky cell

1. **Same-stratum replication across two independent blind bases** at matching holds (random +
   momentum), the strongest evidence type the series can produce — and the momentum-base
   replication uses non-overlapping trades, immune to the block defect.
2. **Breadth under corrected statistics:** USTEC is 9 CI-clear positive / 0 negative across its 84
   DI-axis cells — the only instrument with a surviving one-sided fingerprint (BTC 9+/3−,
   EURUSD 6+/2−, XAU 4+/3−).
3. **Two orthogonal causal controls:** the phase-shift (roll the HTF stream) collapses the effect,
   and the mis-aligned-HTF subset (trades disagreeing with HTF direction) kills or reverses it
   (+0.248 aligned vs −0.054 mis-aligned at H48).
4. **A mechanism-consistent amplifier:** the high-vol ATR regime amplifies the same-signed effect
   (BTC +0.41 hi-vol, CI-clear all holds) rather than producing scattered sign-flips.

## 5. Standing caveats (carry into any graduation)

1. **Dispersion conditioning is largely a normaliser artifact — reproduced on all 3 legs.**
   ATR[t−1] inflates apparent vol-conditioning ~1.5× (003: 2.11× vs 1.16 raw-bps / 1.13 fixed-ATR).
   Genuine residual ~1.1–1.4× in normaliser-invariant space. Any downstream claim must use
   raw-bps / fixed-window ATR.
2. **Sign effect is magnitude-weighted, not a per-trade coin-bias.** |hit−0.5| ≤ 0.03–0.05
   everywhere; the dir_gap comes from HTF direction aligning the position with the larger forward
   moves over the hold. A vehicle that caps winners (fixed TP) clips exactly the trades carrying
   the edge — graduation must run uncapped / horizon exits, or measure TP erosion explicitly.
3. **Domain power gradient.** 1h/5min dense (n to 214k). 1d/1h carries big point magnitudes but no
   CI-clear cell under corrected blocks — UNPOWERED is a power statement (B-5), never folded into
   a negative.
4. **4h/1h is structurally small across all legs** (|shift| ≤0.13 ATR, CIs include 0) — confirmed
   structural, not a coverage artifact.
5. **No tradability claim.** Costs unmodeled; multiplicity 960 cells × 3 legs; a CI-clear screen
   magnitude is a routing signal, not an edge.
6. **Bases are near-null / failing objects** (verified): legs 1–2 measure HTF cleanly on a null;
   leg-3's base has genuine adverse-tail structure.
7. **(New — from the correction.)** Overlapping per-bar estimands need dependence-matched blocks
   (block ≥ H) or non-overlapping trade series; block=5 on such series understates uncertainty
   ~2–3× and manufactured the original fade thread. Rule added to the SPDR lane spec.

## 6. A SECOND, ORTHOGONAL lever — the tail-eaten base structure (unchanged)

Both informative bases show the same signature: the base strategy is right on average / on the
median and killed by a thin adverse tail — not by a wrong centre.

- **Momentum (002 §2.4 mode b):** `mean_excl_worst5` positive in 46/48 strata even where the full
  mean is ~0 or negative; the worst 5% of trades carry 20–36% of all loss mass; the worst-decile
  mean exceeds the full mean in magnitude in every stratum.
- **Reversion (003 §3.5 mode b):** cleanest on BTCUSD 4h/1h all holds — median +0.10→+0.12 ATR,
  mean −0.03→−0.13, skew −0.55→−1.18 (usually right, occasionally crushed).

The lever is a risk / tail overlay — orthogonal to the HTF-direction question. Logged as a
separate observation, not folded into this series' verdict. (These are per-trade distributional
facts on non-overlapping trades; the correction does not touch them.)

## 7. Graduation-design constraints (corrected)

1. **Condition on vol regime as an AMPLIFIER hypothesis** — high-vol amplifies the continuation
   effect (established); the low-vol branch showed no CI-clear effect in either direction. Do not
   carry "ATR sets the sign" — carry "measure the vol-regime interaction; high-vol expected
   stronger".
2. **Uncapped / horizon exit** — the edge is magnitude-weighted; capping winners clips it. If a TP
   is used, measure the erosion explicitly.
3. **Pre-registered family-wise max-stat per instrument over its holds** — the honest multiplicity
   answer to the 960×3-cell screen grid.
4. **Raw-bps / fixed-window ATR for any dispersion claim** — never ATR[t−1].
5. **Sign fixed a priori from TRAIN for the registered stratum only:** USTEC 1h/5min =
   continuation. No other instrument sign is established; no fade prior anywhere.
6. **Dependence-matched uncertainty everywhere** (block ≥ H on overlapping estimands, or
   non-overlapping trade series) — the correction's standing rule.

## 8. Operator disposition — CORRECTED (2026-07-08, supersedes the original §8)

**WORTH_EXPLORING — graduate HTF-DI continuation as a SINGLE thread (USTEC 1h/5min), under the §7
corrected design constraints, routing to full cTrader-primary experiment; the fade thread is
recorded NOT SUPPORTED on the corrected evidence; log the tail-eaten base structure as a separate
exploration line.**

- **Thread A (sole registered thread):** HTF-DI continuation — **USTEC 1h/5min** (replicated
  across two blind bases, dense, HTF-specific, 9+/0− corrected breadth, survives hold-matched
  blocks, mis-aligned control, phase-shift control). **EURUSD 1d/1h demoted** to a
  power-up candidate stratum inside the graduation design (point +0.27→+0.47, no CI-clear hold);
  BTC 1h/5min remains discounted as repackaged LTF autocorrelation.
- **Thread B (fade) — WITHDRAWN / NOT SUPPORTED (corrected):** no CI-clear fade-signed cell exists
  on the corrected grid; the XAU "powered cell" was a mislabelled strategy × DI interaction,
  half-unstable, raw-move n.s. Revival condition: a pre-registered, adequately powered CI-clear
  negative dir_gap on the correct estimand. The originally gated year-split probe was executed as
  part of the correction and failed (both estimands n.s. or half-unstable).
- **Separate log line (NOT in this verdict):** tail-managed naive base exploration (§6).
- **Recorded NOT SUPPORTED:** the universal HTF thesis; ATR as a *direct* dispersion signal
  (~1.5× artifact); ATR as a sign-setter (only high-vol amplification is established); the 4h/1h
  domain; BTC 1h/5min as an HTF-specific thread; **the XAUUSD fade thread (corrected evidence)**.

## Appendix — per-leg headline pointers (corrected)

- **SPDR-001** (random, cleanest isolation): `analysis.md` (corrected) §Facet B B1 → synth §2/§3;
  §1 corrected sign counts + mis-aligned-HTF edge → synth §2/§4; §4 corrected ATR×DI
  (amplification) → synth §1/§7.1; §B2 magnitude-weighted → synth §5.2; Thread 1 direction (CIs
  block=5-optimistic) → synth §2.
- **SPDR-002** (momentum): `analysis.md` (corrected §3.1: H12 n.s.; H24–48 CI-clear) → synth §2;
  §2.4 tail-eaten base → synth §6; open-thread 2 max-stat → synth §7.3.
- **SPDR-003** (reversion, m1 fill): `analysis.md` (corrected §4.1: side-signed interaction vs
  raw-move n.s.) → synth §3; §4.3 normaliser guard → synth §5.1; §3.5 BTC 4h/1h tail-eaten →
  synth §6.
- **Correction probe:** `correction/` (audit record, probe code, 5 CSVs).
