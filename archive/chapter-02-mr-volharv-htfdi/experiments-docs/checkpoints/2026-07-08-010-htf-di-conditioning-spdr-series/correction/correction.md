# Phase 010 Correction — Independent Audit + Fade Re-Probe (2026-07-08)

**Trigger:** independent read/recompute audit of the SPDR CTRL-01/02/03 series (same date as the
original disposition). Two defects were found and confirmed by re-derivation from raw bars; this
directory holds the correction probe (`probe_fade_correction.py` + CSVs) and this binding record.
All affected artifacts (three `analysis.md`, `synthesis.md`, checkpoint `design.md`, family card,
registries) were **rewritten in place** to the corrected findings, each with a pointer here.

## Defect 1 — under-blocked CIs on overlapping per-bar estimands (SPDR-001 analysis)

The SPDR-001 analyst's full-sample estimand samples every valid LTF bar with an H-bar forward
window: consecutive observations share up to H−1 bars, so the series' autocorrelation persists to
lag ≈ H (measured: 0.84 at lag 5, ≈0 at lag 48 for H=48). All its CIs used a circular block
bootstrap with **block=5** — far below the dependence length — so every CI on that estimand was
too narrow, and every "CI excludes zero" call and CI-count derived from it was inflated.

**Fix:** block ≥ H (hold-matched). Recomputed for all 48 plain-`di` cells (`dirgap_cells.csv`)
and all 84 DI-axis cells per instrument (`sign_counts.csv`).

| Quantity | As originally reported (block=5) | Corrected (block=H) |
|---|---|---|
| USTEC 1h/5min dir_gap H12/24/36/48 | CI-clear all 4 | **CI-clear all 4** (H48 edge CI [+0.083,+0.416]) |
| EURUSD 1d/1h dir_gap H24–96 | CI-clear (H48–96) | **none CI-clear** (H48 edge CI [−0.167,+0.684]) |
| EURUSD 1h/5min fade H36/48 | CI-clear negative | **not CI-clear** (H48 [−0.212,+0.073]) |
| XAUUSD dir_gap (all domains/holds) | never CI-clear even at block=5 | not CI-clear |
| BTCUSD 1h/5min dir_gap | CI-clear all 4 | CI-clear H12–36; H48 marginal [−0.010,+0.258] |
| Sign counts USTEC | 18+/4− | **9+/0−** |
| Sign counts XAUUSD | 6+/17− | **4+/3−** |
| Sign counts EURUSD | 14+/15− | 6+/2− |
| Sign counts BTCUSD | 20+/12− | 9+/3− |
| BTC ATR×DI `atrH_adxHi_di` | +0.12→+0.41 CI-clear | **CI-clear all 4 holds** |
| BTC ATR×DI `atrL_adxHi_di` | −0.22 CI-clear at H48 | **not CI-clear at any hold** (H48 [−0.583,+0.129]) |

Point estimates were all reproduced exactly from raw bars (e.g. USTEC dir_gap +0.0922/+0.2260/
+0.3768/+0.4992; τ = −0.023; dir_gap = 2·Cov identity holds to 3 decimals). Only the uncertainty
statements change.

## Defect 2 — SPDR-003 "DI conditional-mean spread" was a different estimand than labelled

`facets.py` computed the DI spread on the **side-signed** reversion return
(`side·(exit−fill)/ATR`), not on the raw forward move `m`. The label
`E[m|+DI] − E[m|−DI]` (and the cross-leg comparison to SPDR-001's `dir_gap = 2·Cov(htf_dir, m)`)
therefore did not describe what was computed. The side-signed quantity is a *reversion-strategy ×
DI interaction* ("the reversion arm performs worse under +DI"), not a conditioning shift of the
forward move, and it does not license "trade against HTF direction".

**Fix:** both estimands recomputed on the same fills (`xau_fill_probe.csv`), XAUUSD 1d/1h H24:

| Estimand | Spread | 95% CI | Half-split (first / second) |
|---|---|---|---|
| Side-signed (as computed originally) | −0.857 | [−1.55, −0.15] | −0.687 n.s. / −1.049 clear |
| **Raw forward move (as labelled)** | **−0.083** | **[−0.68, +0.53]** | −0.246 n.s. / −0.063 n.s. |

The raw-move conditioning spread — the registered fade estimand — is indistinguishable from zero,
full-sample and in both halves. The side-signed interaction is marginal and half-unstable.

## Defect 3 (minor) — SPDR-002 USTEC H12 row

Reported DI sign-conditioning +0.26 [+0.10,+0.43] at H12 does not reproduce; re-derivation
(`spdr002_ustec.csv`) gives **+0.066 [−0.020,+0.148]** (n.s.). H24 +0.258, H36 +0.276, H48 +0.387
all reproduce CI-clear (non-overlapping greedy trades; block choice immaterial there).

## Corrected series conclusions

1. **Thread A rank-1 (USTEC 1h/5min continuation) stands, strengthened by audit.** Reproduced
   exactly from raw bars; CI-clear at every hold under hold-matched blocks on the random base;
   independently CI-clear at H24/H36/H48 on the momentum base (non-overlapping trades); breadth
   9+/0− across the 84 DI-axis cells; mis-aligned-HTF edge dies/reverses; phase-shift collapses it.
2. **EURUSD 1d/1h is demoted from Thread A anchor to point-magnitude-only.** dir_gap +0.27→+0.47
   remains as a point estimate, but no hold is CI-clear under hold-matched blocks — a power
   statement (B-5), not evidence-for. It survives only as a candidate stratum to power up in the
   graduation experiment, not as screen evidence.
3. **Thread B (XAU fade) is NOT SUPPORTED by the corrected evidence.** All three original pillars
   fail: the 17/23 negative-cell breadth collapses to 4+/3− (block artifact); the −0.86 powered
   cell was the wrong estimand (raw-move −0.083 n.s., halves n.s.); EURUSD-intraday and BTC-daily
   fade cells are not CI-clear. No reliable negative dir_gap exists anywhere in the corrected grid.
   The symmetric-estimand *logic* (a real negative would be an equal-information fade signal) is
   untouched — the corrected data simply contain no real negative to read.
4. **ATR×DI is an amplification interaction, not a sign-setter.** High-vol continuation CI-clear at
   all 4 holds (BTC +0.12→+0.41); the low-vol "reversal branch" is not CI-clear at any hold. The
   design constraint becomes "condition on vol regime — high-vol amplifies; low-vol effect
   unproven", not "ATR sets the sign".
5. **Unchanged findings:** the dispersion-normaliser mechanic (~1.5× ATR[t−1] inflation, three-leg
   coherent); 4h/1h structurally small; the tail-eaten base structure (separate log line); base
   null/failure characterisation; all integrity gates (TRAIN fence, HTF-bar boundary, t−1 lag,
   m1-fill causality, seed batteries) — audited directly in code and confirmed sound.

## Standing methodological rule (fed back into the SPDR lane spec)

Any CI on a per-bar estimand with overlapping forward windows must use a dependence-matched block
(**block ≥ hold H**) or a non-overlapping (greedy) trade series. `xen.evaluation` defaults do not
substitute for this choice. Added to `docs/references/spdr-lane.md` integrity boundary.

## Audit trail

- Probe code: `probe_fade_correction.py` (reuses the screens' own causal primitives; TRAIN-only;
  no holdout/TEST touch; no new estimand freedom — it re-measures registered quantities only).
- Outputs: `dirgap_cells.csv`, `sign_counts.csv`, `xau_fill_probe.csv`, `atrdi_cells.csv`,
  `spdr002_ustec.csv`.
- Rewritten artifacts (clean, in place, each pointing here): `SPDR-001/analysis.md` (§B1, §1, §4,
  §5, §9, Thread-1 caveat), `SPDR-002/analysis.md` (§3.1), `SPDR-003/analysis.md` (§4.1, §5.2, §6,
  §7), `synthesis.md` (§1–§5, §7, §8, §8b), checkpoint `design.md`, `cf-htfdi-001.md`,
  `multiplicity-registry.md` Phase 010 batch, `signal-registry/README.md`.
