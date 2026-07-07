# Experiment Report: EXP-024 — CF-CSRR-001 HYP-002b US-bloc session-anchor availability primary

## Status: COMPLETED — NOT SUPPORTED (availability; operator verdict 2026-07-06)

**Date**: 2026-07-06
**Instruments**: 4-member US equity bloc — USTEC, US500, US2000, US30 (σ_i=+1; single common
US-equity factor; near-24h US CFDs).
**Data Views / Feature Categories**: 4h TRAIN (first 49%, panel 2021-06-02 → 2023-11-21, 3,174
union bars; median 4/4 present per bar). Real OHLC; open-to-open. Execution-agnostic (no fills /
no P&L / no `xen.adjudication` estimand gate — availability screen).

---

## Question

On the 4-member US equity bloc at 4h TRAIN, with the session-open-anchored **hedged** residual and
an `all>k` (powered) selection frozen in advance: does fading a member's consensus residual earn a
positive consensus-hedged forward return that clears the **hardened block-bootstrap CI at the ≥1 bp
band**, both temporal halves, and both twins — for USTEC (power question) AND for ≥1 sibling
(mechanism-vs-artifact question)? Controlled follow-up to the EXP-022 USTEC disclosed lead.

## Hypothesis

**HYP-002b.** FROZEN single construction (R_US bloc, session-open anchor S, A=median, B=raw,
C=all>k, D=hedged, h=2·HL); multiplicity family = the 4 members (Holm). Binding bar = the hardened
block-bootstrap CI USTEC FAILED in EXP-022 (ci_low −0.58, effect ≈ MDE 5.28) — NOT the
permutation-only read that lit it up. Resolves (a) does power push ci_low>0 or dilute to MDE, and
(b) real bloc mechanism vs USTEC-only artifact.

## Method Summary

Python characterisation on canonical `xen.bar_aggregator` (1m→4h, min_coverage 0.90) +
`xen.evaluation` (hardened block-boot CI, L-20). Estimand ρ_i(t,h) = −sign(s_i)·idio_i,
idio = g_i − G (consensus-hedged forward, open-to-open, entry Open(t+1)/exit Open(t+1+h), h=2·HL).
Binding CI: circular block ≥ h_i, 10k×5-seed battery, block_sensitivity ½/1/2×, trimmed_mean
(R1 fix — hardened battery applied to the binding cell unconditionally, NOT gated to N×P as
EXP-022 screen.py:422 did). Significance: permuted-axis within-bar identity null (1000 perms) +
Holm over the 4 members (UNPOWERED excluded from denominator). Controls: random-index twin,
random-timing battery (25 seeds, L-19), temporal block-permute tripwire (block=12≥h). Robustness
(disclosed): single-worst hedged continuity (the exact EXP-022 lead form, lighter 2k CI), both-
temporal-halves, horizon 1/2/3·HL. See [design.md](design.md), [qa-review.md](qa-review.md).

## Key Findings

### Finding 1: Substrate — the US-bloc consensus residual mean-reverts (unanimous)

VR(2)<1 on all 4 members (0.89–0.97), VR(6) 0.46–0.55, AR(1) half-life ~1.5–1.8 4h-bars. The
session-anchored residual is a genuine mean-reverting level (substrate PASS, as in EXP-022).

### Finding 2: Binding cell (all>k/hedged) — no member clears the hardened CI

| Member | n | mean ρ (bps) | hardened CI | MDE | p_perm | Holm |
|---|---|---|---|---|---|---|
| USTEC | 800 | +1.08 | [−3.75, +5.88] | 4.83 | 0.171 | 0.684 |
| US500 | 39 | +4.34 | [−0.02, +9.49] | 4.35 | 0.323 | 0.969 |
| US2000 | 857 | +0.65 | [−4.43, +5.75] | 5.08 | 0.329 | 0.969 |
| US30 | 504 | +0.10 | [−4.95, +5.20] | 5.05 | 0.601 | 0.969 |

No member meets the §7 SUPPORTED band (mean ≥ +1 bp AND hardened ci_low>0 AND both-halves
sign-stable AND beats both twins AND p_perm Holm-significant AND tripwire collapses). Every powered
member has hardened ci_low < 0 and MDE > effect → **UNPOWERED-by-MDE**. The §8 pre-declared trade-off
is **confirmed**: all>k admits moderate dislocations → the per-event effect diluted from single-
worst's +4.26 bps to +1.08 bps (USTEC), landing *at* the MDE, not above it. Power bought n but
spent effect. US500 predeclared UNPOWERED (n=39 < 100, B-5).

### Finding 3: Single-worst continuity — reproduces EXP-022, still fails the binding bar

| Member | n | mean ρ (bps) | hardened CI | p_perm | tripwire |
|---|---|---|---|---|---|
| USTEC | 573 | +4.26 | [−1.15, +9.61] | **0.009** | +0.019 (collapse 0.004) |
| US2000 | 693 | +1.35 | [−4.29, +7.01] | 0.205 | −0.17 |
| US30 | 290 | −2.13 | [−8.56, +4.81] | 0.831 | +0.33 |
| US500 | 6 | −2.97 | [−4.21, −1.74] | 0.541 | −0.22 |

**The decisive continuity check.** EXP-022's USTEC lead was permutation-significant (p=0.002) but
hardened-CI-failing (ci_low −0.58). EXP-024 **reproduces it exactly**: p_perm 0.009 (the residual
IS cross-sectionally linked to its own forward idio beyond a random pairing) **but hardened ci_low
−1.15** (still does not exclude zero). The lead does NOT clear the binding bar even at the
selection that maximises it. No sibling reproduces the pattern.

## What EXP-024 explained about the EXP-022 USTEC lead

EXP-022 left an open question: was the USTEC lead's hardened-CI-failure **underpowering** (n=582
too few → could clear with more events) or **effect-at-MDE** (genuinely at the detection floor)?
EXP-024 resolved it in favour of **effect-at-MDE**:

1. **Powering via all>k (n=800 vs 582) did NOT rescue the CI** — the effect *diluted* from +4.71 →
   +1.08 bps and ci_low went more negative (−3.75). The edge was concentrated in the most-extreme
   dislocations; admitting less-extreme events shrank the per-event effect toward zero. The
   "underpowered" hopeful reading is **refuted**.
2. **Re-testing the exact single-worst form reproduced the lead** (+4.26, p_perm 0.009) **with the
   same CI-failure** (ci_low −1.15) — not a one-time fluke.

**Explanation:** the USTEC lead is a **real, reproducible cross-sectional i→i linkage** (the
permutation-significance is genuine, not noise) whose **magnitude sits at the detection floor**
and does not clear the honest block-bootstrap CI at either selection. It is USTEC-specific (no
sibling reproduces) — a single-instrument idiosyncrasy, not a bloc mechanism. This is the design
§7 predeclared operator read #3: "USTEC still fails the hardened ci_low even powered →
effect-at-MDE confirmed → retire evidence."

## Verdict (operator, final — 2026-07-06)

**NOT SUPPORTED at the binding (all>k/hedged) construction.** The substrate reverts, but fading the
dislocation does not earn an idiosyncratic forward return that clears the hardened CI on any
member; the powered members are UNPOWERED-by-MDE (the all>k effect dilutes to the detection floor).
The single-worst continuity reproduces EXP-022's USTEC pattern — permutation-significant but
hardened-CI-fails — so the lead does NOT clear the binding bar even at the selection that
maximises it, and no sibling reproduces it. **The EXP-022 USTEC lead is retired at 0 cost**
(0 counted TEST reads, 0 slots spent). Graduation to an EXP-023 tradability read is **not
warranted** on this evidence. Family disposition → **checkpoint-009 retrospective** (operator-
signed); no family status transition in this experiment.

## Governance (post-exec)

- Integrity gates PASS — QA run 1 (design, APPROVE w/ R1 carry-forward) + QA run 2 (code, APPROVE,
  R1 RESOLVED). Holdout sealed (load capped first 49%, panel ends 2023-11-21, final-30% never
  loaded); causal ≤t-1 provenance (u/m/s/k/HL from confirmed close ≤ t, forward from Open(t+1));
  tripwire collapses (USTEC 0.08 bps ≈ 0; US2000 −0.02; the US30 collapse-*fraction* is numerically
  unstable because its observed effect ≈ 0, but the tripwire *mean* +0.25 bps ≈ 0 — no leak);
  no local accounting (no P&L object; canonical `xen.evaluation` only).
- 0 counted TEST reads, 0 slots (TRAIN-only availability screen). Estimand-validation gate N/A
  (no P&L/accounting object — design §9).
- §0 honesty: TRAIN-only, in-sample-honest. A pass here would NOT have been out-of-sample
  confirmation; the failure of the binding bar on TRAIN is a clean honest signal that the lead is
  effect-at-MDE, not a tradable edge.

## Limitations

- **all>k dilutes.** The pre-declared trade-off (§8) materialised: powering via all>k admitted
  moderate dislocations and the per-event effect fell to the MDE. Single-worst concentrates the
  edge but reproduces the same CI-failure.
- **Single regime.** ~2.5-year TRAIN, one macro regime; no TEST/holdout read (by design — 0
  reads/0 slots).
- **US500 structurally thin** under both selections (n=39 all>k, n=6 single-worst) — predeclared
  UNPOWERED, never a negative (B-5).
- **Permutation vs hardened-CI disagreement persists.** USTEC's single-worst p_perm 0.009 is
  genuine, but under programme discipline (L-20) the reporting standard is "CI excludes zero" —
  here it does not, at either selection.

## Implications for Future Research

- The EXP-022 USTEC lead is **resolved as effect-at-MDE** and retired; it does not graduate to an
  EXP-023 tradability read.
- No US-bloc construction separates at the primary on either basket (EXP-021 Currencies + EXP-022
  Indices + EXP-024 US-bloc controlled follow-up all NOT SUPPORTED at the binding bar). The
  cross-sectional consensus-residual reversion thesis has now failed availability on both baskets
  and on the controlled USTEC re-test.
- Family disposition (retire the family / iterate a component / pursue the AUDUSD-USDCAD lead from
  EXP-021) is an **operator-signed checkpoint-009 retrospective** decision — not an experiment-
  level action.

## Artifacts

| Artifact | Path |
|----------|------|
| Design (frozen construction, §0–§11) | [design.md](design.md) |
| QA review (run 1 design APPROVE + run 2 code APPROVE, R1 resolved) | [qa-review.md](qa-review.md) |
| Analysis (evidence for+against, recommended non-final verdict) | [analysis.md](analysis.md) |
| Analysis code (screen.py, R1 fix) | [analysis_code/](analysis_code/) |
| Report (this file) | [report.md](report.md) |
| Results outputs (cell_reads, substrate, robustness, holm, golden_trace, summary) | [results/](results/) |

**Registry updates (experiment-level, append/disposition only — no family status transition):**
- `docs/signal-registry/candidate-families/cf-csrr-001.md` — HYP-002b evidence row appended;
  HYP-002b status → COMPLETED (NOT SUPPORTED, availability). Family **status field UNCHANGED**
  (REGISTERED/G0-pending; transitions only at the checkpoint retrospective).
- `docs/signal-registry/multiplicity-registry.md` — HYP-002b disposition updated (0 slots, 0
  counted TEST reads; screen-tier, no admission).
- `test-read-ledger.md` — no change (0 counted reads; TRAIN-only availability screen).
