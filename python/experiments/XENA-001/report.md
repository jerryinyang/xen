# Experiment Report: XENA-001 — MTFCTX-C1: HTF context filters on a RANDOM entry control (CTRL-01)

## Status: COMPLETED — **OPERATOR VERDICT: MACHINERY-ALARM**

**Date:** 2026-07-13 (operator verdict) · adjudication completed 2026-07-12
**Lane:** XENA (portfolio referee, default route) · **Family group:** CF-MTFCTX-001
**Instruments (12):** USTEC US500 US2000 JP225 AUS200 US30 EU50(STOXX50) GER40(DE40) HK50 UK100 XAUUSD BTCUSD
**Universe:** 2,736 candidates (19 filter variants × 4 holds × 3 domains × 12 instruments)
**Frozen registry:** v3, sha256 `537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6` (hash-verified at certification)
**Gate ledger: 0/2 slots spent. No counted TEST read. TEST band never opened.**

---

## 1. Question

Does the XENA adjudication machinery manufacture certified portfolios out of noise when run on
**real prices, real code paths, and a real 2,736-candidate universe** whose entries carry
**zero information**?

CTRL-01 strips the entry of all content: entries are pseudo-random (splitmix64, lambda=2, 36
pinned streams), exits are fixed multiples of the HTF span. Any structure XENA finds can only
come from the HTF filter masks or from the machinery itself. Pre-registered (design §1, §8):
**certification or gate pass here is a MACHINERY-ALARM, never an edge.**

## 2. Method summary

| Stage | Configuration | Result |
|---|---|---|
| Emission | cTrader StrategyHost, market orders at bar open, fence `AnalysisEndUtc = 2024-12-11T08:19:00Z` | 2,736/2,736 cells |
| Candidate gate | `xen.xena.ingest.gate_universe` (finite `SlPrice` per leg) | 2,736/2,736 PASS |
| Estimand gate (blocking) | `xen.estimand_validation` | **2,736/2,736 PASS**, `blocking_pass: true` |
| Search | LAHC ×12 restarts, TRAIN search band only (2021-06-02 → 2023-03-08), budget **21,835** (smoke curve read v2 over rids 100/101/102 → 5,723 / 21,835 / 13,974, max taken), `charge_costs=false` (A-1) | 12 distinct terminals |
| Certification | `certify_and_rank(registry_path=…)`: plateau X ≥ 0.70 ∧ F̂ ≥ F_floor 0.4302; 4 purged folds (14-day purge; boundaries 2023-06-12 / 09-16 / 12-22) | **4 of 12 certified** |
| Permutation battery v2 | price-coherent re-marking rotation, K=10 perms × 2 restarts @ budget 21,835 | live median F̂ **below** permuted median |
| Final gate | **NOT RUN** | ledger 0/2 |

**Evaluation counts (§10.4 — mandatory; they travel with every number below):**

| Stage | `evaluation_count` | `distinct_subsets` |
|---|---|---|
| Search (12 restarts) | **255,142** | **255,142** (no cache collisions) |
| Certification top-up | 2,190 | 2,190 |
| Permutation battery | 10 perms × 2 restarts @ 21,835 budget | null draws |

**Platform:** c8g.12xlarge (Graviton4, aarch64) — sole adjudication platform for this
universe's lifetime (INFR-007 1-ULP libm caveat). Rust `xena_fold` kernel (INFR-007/008).

---

## 3. Operator verdict (recorded verbatim, 2026-07-13)

> **XENA-001 (RANDOM control) — verdict: MACHINERY-ALARM**
>
> Per its own pre-registered design.md §8 band: *"certification rate far above battery null
> rate."* The random-entry control certified **4/12 finalists (33%)** against a WS-6 battery
> null certification rate of **0.75%**. Root cause identified and proven: the frozen registry's
> `F_floor` (0.4302) was calibrated on 24-candidate / 400-budget null universes whose F̂ ≈ 0.19
> median; live universes run 2,736 candidates / 21,835–34,000 budget and produce F̂ 3.57–24.64,
> so **F_floor is cleared by 12/12 finalists in every universe including the random control**.
> In the WS-6 null, F_floor was the only screen doing work — the plateau screen (X ≥ 0.70) alone
> passes **50.8% of pure-noise finalists**. Certification therefore degraded to a coin flip at
> live scale.
>
> Important nuance to record: **substantively XENA-001's evidence is noise-consistent** (fold
> medians +0.100 / +0.043 / −0.098 / −0.286; worst fold −0.69; pbo_like 0.25). The alarm is in
> the **adjudication layer**, not the emission layer — engine, fills, estimand gate (2,736 cells
> PASS), provenance, and holdout fence all held. XENA-001 did exactly the job it was designed to
> do: it is the lane's live-data null, and it caught a real machinery defect.
>
> Also record the battery calibration constant it yields: live median F̂ 4.27 vs permuted median
> 5.94 → **live-vs-permuted bias on a no-structure universe = −1.67 log-wealth** (live at the 0th
> percentile of the permuted distribution).

No data-analyst stage was run on XENA-001 (evidence base = `results/evidence_package.json`,
`certification.json`, `permutation_battery.json`; the cross-universe economic scan lives in
XENA-003's `analysis.md` §3.4). There is therefore no analyst recommendation that differs.

---

## 4. Key evidence

### 4.1 Certification — 4/12, and the screen that decided it

All twelve finalists clear `F_floor` by **8.3×–13.1×**. The floor discriminates nothing at live
scale; the **plateau screen alone** decides certification (certified ⇔ `min_drop_ratio` ≥ 0.70).

| Rank (search F̂) | F̂ | × F_floor (0.4302) | min_drop_ratio (X=0.70) | size | **certified** |
|---|---|---|---|---|---|
| 1 | 5.648 | 13.1 | 0.755 | 57 | **YES** |
| 2 | 5.432 | 12.6 | 0.636 | 55 | no |
| 3 | 5.263 | 12.2 | 0.661 | 55 | no |
| 4 | 5.004 | 11.6 | 0.692 | 41 | no |
| 5 | 4.637 | 10.8 | 0.744 | 68 | **YES** |
| 6 | 4.507 | 10.5 | 0.561 | 48 | no |
| 7 | 4.028 | 9.4 | 0.751 | 45 | **YES** |
| 8 | 4.027 | 9.4 | 0.731 | 39 | **YES** |
| 9 | 3.772 | 8.8 | 0.556 | 67 | no |
| 10 | 3.720 | 8.6 | 0.504 | 104 | no |
| 11 | 3.696 | 8.6 | 0.627 | 83 | no |
| 12 | 3.566 | 8.3 | 0.483 | 64 | no |

Keystone attributions flagged on 8 of 12 finalists (`keystones` in `certification.json`).

**Certification rate 33% (4/12) vs WS-6 null finalist-level certification 0.75%** (19 / 2,550
null finalists; recomputed from `python/experiments/INFR-006/results/ws6_battery_raw.jsonl`).
In that null battery the plateau screen alone passed **50.8%** of finalists while `F_floor`
cleared only **0.78%** — the floor was carrying the entire screen, and it is inoperative here
(null F̂ median 0.193, max 0.533; live F̂ 3.57–5.65).

### 4.2 The evidence is substantively noise-consistent (the nuance)

| Certified finalist | fold F (4 purged folds) | **median F** | worst F |
|---|---|---|---|
| size 57 | −0.491 / 0.072 / 0.227 / 0.128 | **+0.100** | −0.491 |
| size 45 | 0.084 / 0.002 / −0.232 / 0.123 | **+0.043** | −0.232 |
| size 68 | 0.017 / −0.229 / 0.128 / −0.214 | **−0.098** | −0.229 |
| size 39 | −0.689 / 0.100 / −0.302 / −0.271 | **−0.286** | **−0.689** |

`pbo_like = 0.25`. Two of the four certified subsets have **negative** fold medians. Nothing
here resembles an edge; what fails is the screen that let them through.

### 4.3 Restart dispersion + permutation battery

| Read | Value |
|---|---|
| Restart F̂ (12) | min 3.566 · median **4.267** · max 5.648 · spread **2.082** |
| Terminal proximity | Hamming 74 / 113.5 / 175 (min/median/max); 12 distinct terminals; sizes 39–104 |
| Permuted F̂ (battery v2, K=10 × 2 restarts) | median **5.937** · max 8.579 · P95 8.062 |
| **Live median percentile within permuted null** | **0.00** (live max: 0.45) |
| **Live − permuted (no-structure calibration constant)** | **−1.67 log-wealth** |

The live universe scores **below** its own permuted twin. Recorded as the lane's no-structure
bias constant (used to net XENA-002's −1.41). Mechanism hypothesis (audit C2 — OBSERVED, not
proven): rotation is applied per candidate independently, decorrelating entry times *across*
candidates and decrowding the portfolio under shared capital / `R_max` admission; real streams
crowd on the same volatility events.

### 4.4 Filter structure (pre-registered FILTER-STRUCTURE band — disclosure only)

Composition of the 209 member slots across the 12 finalist subsets (computed from
`certification.json` `ranked[*].subset`):

| Axis | Finalist share | Universe share | Ratio |
|---|---|---|---|
| V00 (no HTF filter) | 2.4% | 5.3% (1/19) | **0.45×** |
| 1H5M domain | 45.0% | 33.3% | 1.35× |
| H05X (shortest hold) | 25.8% | 25.0% | 1.03× |

On the random control there is no informative preference for filtered variants over baseline.
This is the noise composition against which XENA-002's and XENA-003's filter reads are judged.
**Never a SUPPORTED claim in this run** (design §8).

### 4.5 Integrity gates — all held (the emission layer is clean)

| Gate | Result |
|---|---|
| Candidate gate (finite `SlPrice` per leg) | 2,736/2,736 PASS |
| Estimand validation (blocking) | **2,736/2,736 PASS** (`blocking_pass: true`) |
| Holdout fence | PASS — `AnalysisEndUtc = 2024-12-11T08:19:00Z`; global 30% holdout never loaded; TEST gate band (≥ 2024-03-28) never read |
| Registry hash | matches v3 pin `537d691a…e672a6` |
| Oracle determinism / L-18 reconciliation | PASS (scale-aware tolerance amendment 2026-07-12; numeric outputs unchanged, parity re-proved) |
| Rust-kernel parity (INFR-007) | **PASS on platform** (box Rust == box Python bitwise on all 500 corpus cases); cross-platform pin digest 499/500 (`rand-146`, 1-ULP libm, macOS pin lineage) — **OPERATOR REVIEW FLAGGED**; pins not regenerated |
| Permutation-battery alarm (large live ≫ permuted gap) | not triggered (live *below* permuted) |

---

## 5. Conclusion

**MACHINERY-ALARM (operator, per pre-registered design §8).** The random-entry control certified
4/12 finalists — 33% against a 0.75% battery null rate. The cause is proven and lies in the
**adjudication layer**: `F_floor` is an absolute threshold on an **extensive** statistic
(log-wealth), calibrated at 24 candidates / 400 budget; at live scale (2,736 candidates / 21,835
budget) every finalist clears it by an order of magnitude, leaving the plateau screen — which
passes ~50% of pure noise — as the sole certification criterion.

The emission layer is exonerated: engine, fills, estimand gate, provenance, oracle reconciliation
and the holdout fence all held. XENA-001 performed exactly its designed function as the lane's
live-data null and caught a real defect **before** any gate slot was spent.

## 6. Cross-cutting disclosures (common to XENA-001/002/003)

1. **Framework audit.** A framework-level audit of the adjudication layer is written to
   `.ignore/temp/new-referee/post-xena-infr-audit.md` (2026-07-13): five root causes —
   (A) F is extensive but treated as intensive (`F_floor` inoperative — PROVEN; gate threshold
   shares the lineage — INFERRED; `resim_divergence` structurally vacuous — PROVEN);
   (B) costless gross log-wealth = cadence maximization, structurally hostile to a conditioning
   thesis; (C) the permutation battery is confounded on non-grid-priced entries and oppositely
   biased on bar-close universes; (D) the plateau screen rewards ubiquity, not robustness;
   (E) governance/process sequencing (registry frozen before any live universe; lane made
   default on a synthetic-only credential; L-22 has no enforcing protocol). It warrants a
   dedicated INFR redesign. Referenced, not restated.
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

- Certification is **evidence, not a verdict**; the defect invalidates the *screen*, not the
  emissions. Per-candidate reads are not verdicts in the XENA lane.
- The permutation battery's own biases (audit C2) are **observed, not characterized** — the
  −1.67 constant is a single-universe estimate (K=10 × 2 restarts), not a calibrated null.
- No data-analyst interrogation was run on this universe. Economic reads for XENA-001 (gross
  −0.065 bps/leg; 47.4% of candidates gross-profitable standalone) come from the cross-universe
  anchor scan in [../XENA-003/analysis.md](../XENA-003/analysis.md) §3.4.
- One pinned parity case (`rand-146`) shows a 1-ULP cross-platform libm divergence — flagged for
  operator review (INFR-007); not load-bearing for any number above.

## 8. Implications / recommended next work

1. **No XENA universe should reach a counted gate until the scale defect is resolved** (audit
   item 1): a gross gate pass is arithmetically near-guaranteed at live F̂ scale.
2. **INFR (proposed):** referee redesign — scale-free objective or per-universe null; Jaccard +
   universe-marginal-profitability diagnostics in the evidence package; an entry-price-basis-
   preserving permutation battery; a code-enforced cost-pin precondition.
3. XENA-001's certification evidence stands as the lane's **live-data null anchor** for any
   future universe on these bands/instruments.

## 9. Registry disposition

**Evidence rows only — no status transitions.** (Experiment ≠ family: CF-MTFCTX-001 status moves
only at the operator-signed checkpoint-011 retrospective.)

| Ledger | Update |
|---|---|
| `docs/signal-registry/xena-runs.md` | XENA-001 row closed: eval count 255,142 / distinct subsets 255,142, certified 4/12, **0/2 gate slots**, outcome MACHINERY-ALARM (operator 2026-07-13) |
| `docs/signal-registry/candidate-families/cf-mtfctx-001.md` | evidence row appended (control-universe result + filter-structure disclosure); **status field untouched** |
| `docs/signal-registry/test-read-ledger.md` | **unchanged — no counted TEST read, no holdout contact** |
| `docs/signal-registry/multiplicity-registry.md` | not applicable — XENA runs are accounted in `xena-runs.md`, the portfolio-lane analogue (`docs/references/xena-lane.md` §Registry semantics) |

## 10. Artifacts

| Artifact | Path |
|---|---|
| Design (scope + plan + amendments) | [design.md](design.md) |
| QA (pre-exec, append-only) | [qa-review.md](qa-review.md) |
| Code (search / certify drivers) | [code/](code/) |
| Certification | [results/certification.json](results/certification.json) |
| Evidence package (parity, budget, search, dispersion) | [results/evidence_package.json](results/evidence_package.json) |
| Permutation battery v2 | [results/permutation_battery.json](results/permutation_battery.json) |
| Estimand gate (blocking) | [results/estimand_validation.json](results/estimand_validation.json) |
| Search restarts ×12 | [results/](results/) (`search_restart_00..11.json`) |
| Search budget (smoke curve read) | [results/search_budget.json](results/search_budget.json) |
| Bundle digest manifest | [results/bundle_sha256_manifest.json](results/bundle_sha256_manifest.json) |
| Superseded run-1 / x86 lineage | [results/superseded-run1-2026-07-12/](results/superseded-run1-2026-07-12/) · [results/archive-ec2-c7i/](results/archive-ec2-c7i/) |
| Framework audit (cross-cutting) | `.ignore/temp/new-referee/post-xena-infr-audit.md` |
