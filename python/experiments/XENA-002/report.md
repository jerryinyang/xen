# Experiment Report: XENA-002 — MTFCTX-C2: HTF context filters on a NAIVE MOMENTUM control (CTRL-02)

## Status: COMPLETED — **OPERATOR VERDICT: NO DETECTABLE STRUCTURE**

**Date:** 2026-07-13 (operator verdict) · adjudication completed 2026-07-12
**Lane:** XENA (portfolio referee, default route) · **Family group:** CF-MTFCTX-001
**Instruments (12):** USTEC US500 US2000 JP225 AUS200 US30 EU50(STOXX50) GER40(DE40) HK50 UK100 XAUUSD BTCUSD
**Universe:** 2,736 candidates (19 filter variants × 4 holds × 3 domains × 12 instruments)
**Frozen registry:** v3, sha256 `537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6` (hash-verified at certification)
**Gate ledger: 0/2 slots spent. No counted TEST read. TEST band never opened.**

---

## 1. Question / hypothesis

**Mechanism (design §1):** a close breaking the prior 3-bar high/low range marks initiative flow
whose direction is hypothesised to persist over 0.5–4× the HTF span; **HTF context** (ADX
strength, ±DI direction, vol regime) is hypothesised to condition the quality of those LTF
breakout entries. Adjudication is portfolio-level (no A/B claim): does the machinery certify
anything, and are filtered variants (V01–V18) systematically selected over the unfiltered
baseline (V00)?

XENA-002 is the family's **first informed control** universe. XENA-001 (random entries, same
instruments, same bands, same machinery) is its **live-data null anchor**.

## 2. Method summary

| Stage | Configuration | Result |
|---|---|---|
| Emission | cTrader StrategyHost, market orders at bar open (deterministic model, no RNG), fence `AnalysisEndUtc = 2024-12-11T08:19:00Z` | 2,736/2,736 cells |
| Candidate gate | `gate_universe` (finite `SlPrice` per leg) | PASS |
| Estimand gate (blocking) | `xen.estimand_validation` | **2,773/2,773 cells PASS**, `blocking_pass: true`, manifest 12/12 instruments |
| Search | LAHC ×12 restarts, TRAIN search band only (2021-06-02 → 2023-03-08), budget **34,000** (smoke curve read v2 over rids 100/101/102 → 7,154 / 27,294 / 34,000, max taken = smoke cap), `charge_costs=false` (A-1) | 12 distinct terminals |
| Certification | `certify_and_rank(registry_path=…)`: plateau X ≥ 0.70 ∧ F̂ ≥ F_floor 0.4302; 4 purged folds (14-day purge; boundaries 2023-06-12 / 09-16 / 12-22) | **7 of 12 certified** |
| Permutation battery v2 | price-coherent re-marking rotation, K=10 perms × 2 restarts @ budget 34,000 | live median F̂ **below** permuted median |
| Final gate | **NOT RUN** | ledger 0/2 |

**Evaluation counts (§10.4 — mandatory; they travel with every number below):**

| Stage | `evaluation_count` | `distinct_subsets` |
|---|---|---|
| Search (12 restarts) | **397,475** | **397,475** (no cache collisions) |
| Certification top-up | 1,851 | 1,851 |
| Permutation battery | 10 perms × 2 restarts @ 34,000 budget | null draws |

**Platform:** c8g.12xlarge (Graviton4, aarch64) — sole adjudication platform for this universe's
lifetime (INFR-007 1-ULP libm caveat). Rust `xena_fold` kernel.

---

## 3. Operator verdict (recorded verbatim, 2026-07-13)

> **XENA-002 (naive momentum) — verdict: NO DETECTABLE STRUCTURE**
>
> Live median F̂ 4.79 vs permuted median 6.20 (live at 0th percentile; battery delta −1.41).
> Netted against XENA-001's −1.67 no-structure bias, XENA-002 sits **+0.26 above the random
> control — well inside restart dispersion of 2.90.** Statistically it is the random control.
> 7/12 certified, but that count is uninformative given the F_floor defect above. pbo_like 0.50
> (worse than the random control's 0.25). All seven certified finalists do have positive fold
> medians (+0.063 to +0.246), which XENA-001 cannot claim — record that as the one genuine
> difference, and record that it does not survive the battery comparison. **Negative evidence for
> the CF-MTFCTX-001 arc.**

No data-analyst stage was run on XENA-002 (evidence base = `results/evidence_package.json`,
`certification.json`, `permutation_battery.json`; the cross-universe economic scan is in
XENA-003's `analysis.md` §3.4). There is therefore no analyst recommendation that differs.

---

## 4. Key evidence

### 4.1 The decisive read — battery comparison against the live-data null

| Universe | live median F̂ | permuted median F̂ | **delta** | live pctile in permuted null |
|---|---|---|---|---|
| **XENA-001** (RANDOM control, no-structure) | 4.267 | 5.937 | **−1.67** | 0.00 |
| **XENA-002** (naive momentum) | **4.786** | **6.197** | **−1.41** | **0.00** |

**XENA-002 − XENA-001 = +0.26 log-wealth**, against a **restart F̂ dispersion of 2.90** within
XENA-002 itself (min 4.158 · max 7.054). The informed universe is statistically indistinguishable
from the information-free one. Both sit at the **0th percentile** of their own permuted nulls
(audit C2: the battery is biased *low-for-live* on bar-close universes — decrowding under
per-candidate rotation; observed, not characterized).

### 4.2 Certification — 7/12, and why the count is uninformative

All twelve finalists clear `F_floor` by **9.7×–16.4×** (F_floor 0.4302; live F̂ 4.16–7.05).
Certification is decided **solely** by the plateau screen (certified ⇔ `min_drop_ratio` ≥ 0.70) —
a screen that passes **50.8% of pure-noise finalists** in the WS-6 battery. 7/12 (58%) is exactly
what a ~50% noise-passer predicts.

| Rank (search F̂) | F̂ | × F_floor | min_drop_ratio (X=0.70) | size | **certified** | fold F (4 purged) | median F | worst F |
|---|---|---|---|---|---|---|---|---|
| 1 | 7.054 | 16.4 | 0.748 | 48 | **YES** | 0.052 / 0.270 / 0.036 / 0.141 | +0.097 | +0.036 |
| 2 | 5.270 | 12.3 | 0.717 | 45 | **YES** | −0.018 / 0.356 / 0.144 / −0.249 | +0.063 | −0.249 |
| 3 | 4.922 | 11.4 | 0.636 | 52 | no | — | — | — |
| 4 | 4.859 | 11.3 | 0.665 | 52 | no | — | — | — |
| 5 | 4.819 | 11.2 | 0.791 | 39 | **YES** | 0.082 / 0.075 / 0.053 / 0.301 | +0.079 | +0.053 |
| 6 | 4.816 | 11.2 | 0.646 | 68 | no | — | — | — |
| 7 | 4.756 | 11.1 | 0.685 | 64 | no | — | — | — |
| 8 | 4.625 | 10.8 | 0.510 | 55 | no | — | — | — |
| 9 | 4.497 | 10.5 | 0.743 | 34 | **YES** | −0.246 / 0.326 / 0.465 / 0.166 | **+0.246** | −0.246 |
| 10 | 4.364 | 10.1 | 0.774 | 46 | **YES** | 0.122 / 0.097 / 0.008 / 0.269 | +0.110 | +0.008 |
| 11 | 4.314 | 10.0 | 0.703 | 50 | **YES** | −0.095 / 0.031 / 0.276 / 0.153 | +0.092 | −0.095 |
| 12 | 4.158 | 9.7 | 0.702 | 60 | **YES** | −0.099 / 0.553 / 0.247 / −0.064 | +0.091 | −0.099 |

- **`pbo_like = 0.50`** — worse than the random control's 0.25.
- Keystone attributions flagged on 5 of 12 finalists.
- **The one genuine difference vs XENA-001:** all seven certified finalists have **positive fold
  medians (+0.063 … +0.246)**; XENA-001's certified set contains two negative medians (−0.098,
  −0.286). Recorded as a real difference — **and it does not survive the battery comparison
  (§4.1)**.

### 4.3 Dispersion + landscape

| Read | Value |
|---|---|
| Restart F̂ (12) | min 4.158 · median **4.786** · max 7.054 · **spread 2.897** |
| Terminal proximity | Hamming 69 / 96 / 126 (min/median/max); 12 distinct terminals; sizes 34–68 |
| Permuted F̂ (K=10 × 2) | median 6.197 · P95 8.778 · max 9.942 |
| `resim frac_folds_below_search_p25` | 1.0 for every finalist — **structurally vacuous** (folds ≈ 3 months vs a 21-month search band; log-wealth scales with window length; audit A3) |

### 4.4 Filter structure (pre-registered FILTER-STRUCTURE band — disclosure only)

Composition of the 322 member slots across the 12 finalist subsets (computed from
`certification.json` `ranked[*].subset`):

| Axis | Finalist share | Universe share | Ratio |
|---|---|---|---|
| V00 (no HTF filter) | 6.2% | 5.3% (1/19) | **1.18×** |
| 1H5M domain (fastest) | 47.2% | 33.3% | 1.42× |
| H4X (longest hold) | 33.2% | 25.0% | 1.33× |

The HTF filter variants are **not** systematically selected over the unfiltered baseline — V00 is
if anything mildly over-represented. No support for the conditioning thesis from this universe.
Per design §8 this is a disclosure, never a standalone SUPPORTED claim.

### 4.5 Integrity gates — all held

| Gate | Result |
|---|---|
| Candidate gate (finite `SlPrice` per leg) | PASS |
| Estimand validation (blocking) | **2,773/2,773 cells PASS** (`blocking_pass: true`) |
| Holdout fence | PASS — `AnalysisEndUtc = 2024-12-11T08:19:00Z`; global 30% holdout never loaded; TEST gate band (≥ 2024-03-28) never read |
| Registry hash | matches v3 pin `537d691a…e672a6` |
| Oracle determinism / L-18 reconciliation | PASS (scale-aware tolerance amendment; numeric outputs unchanged) |
| Rust-kernel parity (INFR-007) | PASS on platform; cross-platform pin digest 499/500 (`rand-146`, 1-ULP libm) — operator-review flagged |
| Permutation-battery alarm (live ≫ permuted) | not triggered (live *below* permuted) |

---

## 5. Conclusion

**NO DETECTABLE STRUCTURE (operator).** Naive momentum entries plus HTF context filters, composed
at portfolio level on 12 instruments over a 21-month search band, produce a universe that is
**statistically the random control**: the live-vs-permuted delta (−1.41) sits +0.26 above
XENA-001's no-structure bias (−1.67), well inside XENA-002's own restart dispersion (2.90). The
7/12 certification count carries no information — it is a product of the `F_floor` scale defect
(XENA-001 §4.1), which leaves a ~50%-noise-passing plateau screen as the sole criterion.

The single genuine difference from the random control — all seven certified finalists have
positive fold medians (+0.063 to +0.246), which XENA-001 cannot claim — does not survive the
battery comparison.

**Negative evidence for the CF-MTFCTX-001 arc** (family status is not moved here; that is the
checkpoint-011 retrospective's call).

## 6. Cross-cutting disclosures (common to XENA-001/002/003)

1. **Framework audit.** `.ignore/temp/new-referee/post-xena-infr-audit.md` (2026-07-13) — five
   root causes: (A) extensive-vs-intensive F statistic (`F_floor` inoperative — PROVEN; gate
   threshold same lineage — INFERRED; `resim_divergence` vacuous — PROVEN); (B) costless
   cadence-maximizing objective, structurally hostile to a conditioning thesis (B2: *a
   conditioning thesis cannot win under a costless cadence-maximizing objective, regardless of
   whether it is true* — directly load-bearing for how §4.4 is read); (C) permutation battery
   confounded on non-grid-priced entries, oppositely biased on bar-close universes like this one;
   (D) plateau screen rewards ubiquity, not robustness; (E) governance/process sequencing. It
   warrants a dedicated INFR redesign. Referenced, not restated.
2. **Governance near-miss (recorded).** Design §4 spread pins were never set —
   `universe_manifest.json` carries `cost_bps = 0.0` for **ten of twelve** instruments. A gate
   spend would have produced a **binding GROSS pass with a vacuous NET block** — the exact L-22
   failure shape. **Nothing in the pipeline blocked this.**
3. **Proposed new lesson (PROPOSAL — operator ratifies at checkpoint-011; not self-ratified).**
   Suggested **L-25**:
   > *An absolute threshold on an **extensive** statistic — one that scales with band length,
   > trade count, or candidate-pool size — is valid only at the scale at which it was calibrated.
   > A frozen, hash-pinned registry is coherent only for **scale-free** statistics. Any frozen
   > constant must therefore be either (a) defined on a standardized/intensive statistic
   > (per-trade, per-unit-time, or z-scored against a per-universe null), or (b) re-derived per
   > universe from that universe's own null — and no registry may be pinned before at least one
   > live null universe has been run at production scale.*

## 7. Limitations

- The negative read rests on a **battery whose bias on bar-close universes is observed, not
  characterized** (both live universes sit at the 0th percentile of their permuted nulls). The
  netting (−1.41 vs −1.67) is the best available comparison, not a calibrated test.
- **The objective cannot adjudicate the registered thesis** (audit B2): every HTF filter thins
  cadence, and a costless log-wealth objective pays for cadence. A null filter-structure read here
  is therefore weaker evidence against HTF conditioning than it looks.
- No data-analyst interrogation of XENA-002's emissions was run. Its cross-universe economics
  (gross +0.085 bps/leg; 52.6% of candidates gross-profitable standalone) come from
  [../XENA-003/analysis.md](../XENA-003/analysis.md) §3.4.
- Certification counts here are **not** evidence of edge, in either direction.

## 8. Implications / recommended next work

1. **No gate spend on this universe** — the count that would justify it is defect-driven, and the
   gate threshold shares the F_floor lineage (audit A2).
2. **INFR (proposed):** referee redesign before any further XENA universe is adjudicated —
   scale-free objective or per-universe null; cadence-neutral or cost-aware selection objective if
   a conditioning thesis is ever to be testable in this lane.
3. A conditioning thesis, if pursued, needs an **objective that does not pay for cadence** — an
   EXP-lane per-stratum conditional read may be the honest vehicle, not portfolio selection.

## 9. Registry disposition

**Evidence rows only — no status transitions.** (Experiment ≠ family: CF-MTFCTX-001 status moves
only at the operator-signed checkpoint-011 retrospective.)

| Ledger | Update |
|---|---|
| `docs/signal-registry/xena-runs.md` | XENA-002 row closed: eval count 397,475 / distinct subsets 397,475, certified 7/12, **0/2 gate slots**, outcome NO DETECTABLE STRUCTURE (operator 2026-07-13) |
| `docs/signal-registry/candidate-families/cf-mtfctx-001.md` | evidence row appended (negative evidence for the arc + filter-structure disclosure); **status field untouched** |
| `docs/signal-registry/test-read-ledger.md` | **unchanged — no counted TEST read, no holdout contact** |
| `docs/signal-registry/multiplicity-registry.md` | not applicable — XENA runs are accounted in `xena-runs.md` (`docs/references/xena-lane.md` §Registry semantics) |

## 10. Artifacts

| Artifact | Path |
|---|---|
| Design (scope + plan + amendments) | [design.md](design.md) |
| QA (pre-exec, append-only) | [qa-review.md](qa-review.md) |
| Code (search / certify drivers) | [code/](code/) |
| Certification | [results/certification.json](results/certification.json) |
| Evidence package | [results/evidence_package.json](results/evidence_package.json) |
| Permutation battery v2 | [results/permutation_battery.json](results/permutation_battery.json) |
| Estimand gate (blocking) | [results/estimand_validation.json](results/estimand_validation.json) |
| Search restarts ×12 + budget | [results/](results/) (`search_restart_00..11.json`, `search_budget.json`) |
| Bundle digest manifest | [results/bundle_sha256_manifest.json](results/bundle_sha256_manifest.json) |
| Superseded run-1 / x86 lineage | [results/superseded-run1-2026-07-12/](results/superseded-run1-2026-07-12/) · [results/archive-ec2-c7i/](results/archive-ec2-c7i/) |
| Live-data null anchor (random control) | [../XENA-001/report.md](../XENA-001/report.md) |
| Framework audit (cross-cutting) | `.ignore/temp/new-referee/post-xena-infr-audit.md` |
