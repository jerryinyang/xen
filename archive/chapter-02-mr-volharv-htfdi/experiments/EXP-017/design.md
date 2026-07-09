# EXP-017 — CF-MR-005/HYP-002: episode-native mechanism probe of the ladder harvest

**Family:** CF-MR-005 (OPEN — TEST persistence retained, EXP-016) · **Type:** mechanism
characterisation, TRAIN-only · **Classification: ANALYSIS-ONLY** — episode reconstruction
strictly from existing engine emissions; no new runs; no Python strategy backtest (the one
price-path comparator below is a labelled non-tradable diagnostic measurement, not a strategy).
**Slots/reads:** 0 slots, 0 counted TEST reads. **Holdout:** final-30% sealed.
**Fences:** TRAIN bands only — EXP-014b/c emissions as-is (they end at the 49% fence);
EXP-016 emissions restricted to `SourceCloseTime ≤` the EXP-013 49% fence (their TEST band is
already-read TEST data — **excluded entirely**; no disclosure use).

**The P&L-bearing object (L-16, stated explicitly).** One **episode** = the maximal interval in
one (cell, exit, arm, z\*) run during which ≥1 ladder leg is open: first entry fill → last exit
(flat). Episode net = sum of engine-realized per-bar NET bps over the interval (audited
`assemble_realized_bps`; MTM L-09, cost per entry L-02). Every binding read in this experiment
is a function of episodes. Fence rule: episodes still open at the 49% fence are censored —
excluded from episode stats, counted and disclosed.

**L-17 compliance.** The frozen referee is **not used anywhere** in this design — no gating on
any subset. All inference is episode-level bootstrap / permutation with predeclared floors.

## 1. Falsifiable question

*Is the ladder's episode-level P&L (a) attributable to the scale-in structure itself — i.e.
does the multi-leg episode outperform a passive same-direction, same-window exposure — and (b)
predictable from information available at episode START (≤ t−1), in ≥2 powered strata; or is it
(c) indistinguishable from passive directional exposure whose profitability is only knowable
path-dependently?* (a)+(b) = a statable mechanism → HYP-003 (short-band instrument + final
confirmation) becomes motivated. (c) in the powered strata = exposure verdict → retire case,
this time at the correct object.

## 2. Scope

| Field | Value |
|---|---|
| Primary strata | US2000, AUDUSD, NZDUSD × (e3, extend, z15) — the EXP-016-retained cells (prespecified) |
| Replication strata (disclosure) | Same 3 cells × {e0, e2}/extend/z15 + the remaining 8 cells × e3/extend/z15 (TRAIN band) — same reads, non-binding |
| Sources | `data/strategy_runs/EXP-014{b,c}-4h-s8-*extend-z15*` (read-only) + `EXP-016-4h-s8-e3-extend-z15` TRAIN-band rows only |
| Episode features — START-known (≤ t−1 at first-entry arm bar) | entry \|z\|, σ, vol-regime tercile (`EntryVolRegime`), trend dir/Z, bracket HL, cost_bps |
| Episode features — PATH (not start-known; descriptive only) | max ladder level reached, leg count, duration (bars), aggregate-position MAE, per-level P&L contribution |
| Exclusions | TEST/holdout rows; new emissions; exit modifications (P-02); frozen-referee reads (L-17); pooled cross-stratum verdicts (L-03) |

## 3. Methods (episode-level; simplest sufficient)

| # | Question | Method | Why sufficient / null validity |
|---|---|---|---|
| **M1 — anatomy (descriptive)** | Where does episode P&L live? | Per stratum: episode net by max-level-reached {L0-only, L1, L2}, by leg count, by duration tercile; per-level contribution within episodes. No inference — path features are mechanically coupled to P&L (deeper adds ⇔ adverse path); labelled descriptive. | The map the mechanism statement must explain; avoids inferring from coupled variables. |
| **M2 — structure increment (binding)** | Does the ladder beat passive exposure? | Per episode: **passive comparator** = 1-unit position, episode's initial direction, opened at the first-entry fill, marked open-to-open to the episode's last exit bar, charged 1× cost (a price-path measurement from the same emission's Real* columns — non-tradable diagnostic, no order logic). Increment `Δ_e = net_ladder − net_passive` per episode; stratum read = median & mean Δ with moving-block bootstrap CI over episodes (episodes ordered by start time; block 5 episodes; 10k; frozen seed). | Isolates what the scale-in structure adds over plain being-long/short the same window — the exposure-vs-structure question in one paired statistic. Paired ⇒ market drift cancels within episode. |
| **M3 — start-predictability (binding)** | Is episode net predictable at entry? | Per stratum × start-known feature: Spearman ρ(feature, episode net) with a **feature-label permutation null** (5,000 perms, frozen seed): permute the feature vector across episodes, re-compute ρ → null band; report observed ρ, null 95% band, and **collapse fraction** (L-15). Multiplicity: Holm across the 6 features within a stratum. | Label permutation is the exact null for association (not signal-derived, L-08; not a mean-stat destroy, so the EXP-012 mean-invariance trap does not apply — ρ is permutation-sensitive by construction). |
| **M4 — episode tail census (descriptive)** | What tail does the structure carry? | Per stratum: aggregate-position MAE distribution (bps of initial notional-equivalent), underwater duration, episode net q{01,05}, top-k winners removed (k=1,3,5), share of net from max-level=L2 episodes, per-year split. | Refines the EXP-015 Part-A tail read at the correct object; feeds any HYP-003 tail budget. |

**Zero-baseline / power floors:** stratum powered when ≥**30 completed episodes**; below →
UNPOWERED (reported, never FAIL). Censored episodes counted per stratum. All denominators
(episodes, legs, bars) stated per table. Seeds: bootstrap 20260703, permutation 20260705.

## 4. Leak tripwire (binding)

**Start-feature label permutation (M3's null) is the primary destroy** — association must
collapse under it, and observed-vs-null magnitudes are reported as collapse fractions (L-15).
Additionally, M2's increment is re-computed under **episode-start-offset placebo**: shift each
episode's passive-comparator window forward by 5 episodes' start times within the same stratum
(window length preserved) — the paired increment must not survive with the wrong windows
(placebo Δ distribution disclosed alongside the real one). No time-reversal/path-rotation
(L-07); no permutation of realized P&L against a mean statistic (mean-invariant, EXP-012).

## 5. Interpretation criteria (frozen before results)

| Outcome | Condition (per stratum; family read = counts over the 3 primary strata) |
|---|---|
| **MECHANISM_STATED** | M2 Δ median & mean CI > 0 (ladder beats passive) **and** ≥1 start-known feature's ρ outside the permutation band after Holm, in ≥2/3 powered primary strata, with the same feature sign in both. |
| **STRUCTURE_ONLY** | M2 Δ CI > 0 in ≥2/3 but no start-known predictability anywhere → the ladder adds value over passive mechanically (e.g. add-at-depth rebalancing premium) but entry timing carries no information; mechanism = structure, capacity ruled by M4 tail. Routes to operator (HYP-003 design decides if this is tradable-in-principle). |
| **EXPOSURE_VERDICT** | M2 Δ CI covers 0 (or <0) in ≥2/3 powered primary strata → the ladder is passive directional exposure in disguise; combined with EXP-015's per-event null this is the family-terminal retire case, at the correct object this time. |
| **UNPOWERED / MIXED** | <2 powered primary strata, or criteria split across strata → operator routing; no verdict. |
| Replication strata | Disclosure only; consistency/contradiction noted, never binding. |

## 6. Complexity budget

Tests: M2 bootstrap + M3 perm-null (Holm/6) + placebo = 3. Plots ≤5: episode net by max-level;
Δ_ladder−passive distribution per primary stratum; ρ vs null bands (feature grid); tail census;
per-year episode net. Code: `code/lib.py` (episode reconstruction + comparator + stats; reuse
EXP-014c lib loaders/provenance) + `code/run_experiment.py`. No new `python/src/xen` module.

## 7. Implementation safety

- Episode reconstruction from `cis_trades` + positions, ordered by `SourceCloseTime`/`EntryTime`
  — never bar index; sequential stateful loop (bounded, tqdm) is correct here, do not vectorize
  the episode splitter.
- EXP-016 sources: hard-filter `SourceCloseTime ≤ 49% fence` **before** any computation; assert
  no TEST-band row enters any table (audit will check).
- Passive comparator uses the same emission's `RealOpen` marks, open-to-open, 1× frozen cost;
  same bars as the episode — no external data, no order simulation, labelled non-tradable.
- Provenance (`validate_provenance`) + `assert_run_within_holdout` on every load.
- Censored-at-fence episodes excluded + counted; NaN RealizedBps legs disclosed.
- No perf shortcut may alter episode membership, pairing, denominators, or temporal order.

## 8. Registry

Add `CF-MR-005/HYP-002` row (EXP-017, 0 slots, 0 counted reads) at gate approval. Outcomes
route per §5; nothing here authorizes a TEST read (final reads reserved behind the L-17
short-band instrument, HYP-003 material).

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-03)

Single question ✓ (structure-vs-exposure + start-predictability of the episode object; M1/M4
descriptive facets). **L-16 ✓** — P&L-bearing object stated and every binding read is
episode-level. **L-17 ✓** — no frozen-referee use anywhere; inference = bootstrap/permutation
with predeclared floors. **L-15 ✓** — collapse fractions on M3 + placebo disclosure on M2.
Nulls valid: label permutation (association-sensitive, not mean-invariant — EXP-012 honored),
placebo windows; no L-07/L-08 violations. TEST hygiene ✓ — EXP-016 TEST band excluded outright.
Analysis-only ✓ (comparator is a labelled price-path diagnostic, not a backtest; P-09/L-01
honored). P-02 ✓ (no exit scope). Per-stratum ✓ (3 prespecified primary strata; replication
disclosure-only). Budget ✓ (3 tests, ≤5 plots, 1 lib + 1 script). Criteria frozen ✓ incl. the
STRUCTURE_ONLY middle outcome. Registry row pending entry ✓. **READY for Stage 2 (Implement).**

## AMENDMENT A1 (2026-07-03, operator-approved) — M2 comparator replaced; invalid M2 outputs hard-deleted and re-run

**Trigger.** The §4 placebo tripwire fired on the original M2: real Δ (ladder − 1-unit passive)
survived start-offset placebo windows nearly unchanged (AUDUSD 220 vs 188, NZDUSD 217 vs 202,
US2000 396 vs 376 bps) — the increment was mechanical **size confound** (episodes average
12–15 legs vs a 1-unit comparator), not window-specific information. Per the frozen §4 rule the
original M2 read is INVALID and the run's STRUCTURE_ONLY print was never booked.

**A1-M2 (replacement, binding).** Per episode: **size-and-time-matched passive** — for each
ladder leg, one unit entered at the `RealOpen` of the leg's entry bar (market, same bar as the
fill), held to the episode's end mark (next open after last bar), charged 1× cost per unit
(same cost count as the ladder). `Δ_e = net_ladder − net_matched_passive`. Identical exposure
bars and unit count; Δ isolates the ladder's execution structure (limit-fill entry prices +
bracket exits) at matched size. Stratum read: median & mean Δ, moving-block bootstrap over
episodes (block 5, 10k, seed 20260703), per stratum.

**A1 destroy (replacing the window placebo, which A1 closes by construction).** Bar-matched
pairing cancels window effects exactly, so the valid null is **within-episode add-bar
randomization**: recompute the matched passive with each add assigned to a uniformly random
bar in the episode span (same unit count; 200 draws, seed 20260706) → null band of Δ. If
observed Δ sits inside the random-timing band, the adds' actual bars carry no information and
Δ reduces to fill-discount + exit mechanics (disclosed as such, collapse fraction per L-15).

**§5 criteria unchanged** with "M2" read as A1-M2. Old `results/` deleted before re-run
(amend-in-place, L-10 discipline). M1/M3/M4 unchanged (M3's label-permutation null was valid
and its null result stands).
