# EXP-014 — CF-MR-004/HYP-002: faithful full-exit cross-instrument MR strategy (scope + plan)

**Family:** CF-MR-004 (REGISTERED) · **Phase:** 004 · **Type:** full-strategy screen (availability + net, TRAIN)
**Classification:** **PRICE-PRIMARY** (in-engine, native pending orders; L-01/P-09)
**Slots/reads:** 0 candidate slots, **0 counted TEST reads** · **Holdout:** final-30% sealed; emit over
**first-49% TRAIN sub-split** only · Frozen referee — **never tuned** (L-12).
**Origin:** `amendment-001-faithful-full-strategy-redo.md` (downgrades EXP-013 → CONFOUNDED). Supersedes the
EXP-013 vehicle-incomplete build.

## 0. Mandate

Operator directive (`.ignore/idea/newer.md`, do-not-override): implement + test **immediately** — the
faithful full exit set (form-1 + refreshing form-2), re-entry variants, and trend/vol conditioners are
**not gated behind an initial edge confirmation** (they may be the missing core of the family). Full-scope,
no simplification; performant + memory-safe without compromising integrity. From-scratch family code (L-13);
multi-symbol StrategyHost = reusable infra.

## 1. Falsifiable question (one)

*On the 4h anchor domain, does the **faithful full-exit** precalc limit-order cross-instrument MR-fade
strategy (4 series S5/S6/S7/S8; form-1 event-reversion exit **and** refreshing form-2 anchor-mean limit;
horizon last-resort) produce (a) reversion-to-anchor beyond a dislocation-matched matched-random control
(availability) AND (b) a net-positive per-stratum edge under the frozen 4h referee (tradability) — and if
not, **exactly which leg fails, where** (entry fill / form-1 / form-2 / horizon / trend-bucket / vol-regime /
reentry)?*

## 2. Price-primary classification — PRICE-PRIMARY (confirmed)

Native cTrader pending orders (`Mode=NativeOrders`); cTrader's **m1 backtester owns fill resolution**. No
self-adjudicated fills, no vectorized Python edge/outcome module (L-01/P-09). Python analysis-only on
emitted `data/strategy_runs/EXP-014*/` parquet with engine-realized fill prices. Frozen referee
(`referee_pstar.gate_stack_pstar`, domain=4h, q\*=0.75) adjudicates the emitted per-4h-bar realized net series.

## 3. Data scope

| Field | Value |
|---|---|
| Universe | INFR-003 5-year, 16 instruments (VAL-003 minus DE30) |
| Traded | FX majors (7: EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD, NZDUSD) + indices (4: USTEC, US500, US2000, JP225) = **11** |
| Peers/baskets | FX: other 6 majors per class basket / single peer for pairs. Indices: other 3 per class. XAUUSD/BTCUSD standalone (not in baskets). |
| Anchor domain | **4h only** (frozen referee supports 4h; 1D deferred — needs referee extension). No lower-domain (operator mandate). |
| Time range | Full 5-year; first-70% analysis slice; **first-49% TRAIN sub-split** (`int(int(N·0.7)·0.7)` row CloseTime — matches EXP-010/013). |
| Global holdout | Final-30% **never loaded**. `AnalysisEndUtc` = each file's first-49% cutoff (reuse EXP-013 cutoffs — identical dataset/fence). |
| Stratum | `(series, instrument-or-pair, 4h)`; per-stratum binding (L-03); pooled = disclosure-only. |
| Exclusions | No lower-domain; no 1D/1h/15m; no TEST read; no holdout release. S1–S4 (single-instrument) out of scope. |

## 4. Series (unchanged from EXP-013 defs, F-fix on S8)

| Series | Construction | Invertible price | Cells |
|---|---|---|---|
| **S5** | `d = log P^A − (β·basket + α)`; equal-weight log-basket of class-mates; `(β,α)`=OLS trailing W_a=200 4h | `P^A = basket^β·e^(α+d)` | 11 |
| **S6** | `S = log P^A − β·log P^B`; β=1 (log-price diff) | `P^A = P_B·e^S` | 5 pairs |
| **S7** | `S = log P^A − Σ wᵢ·log Pᵢ`; equal wᵢ=1/n | `P^A = (Π Pᵢ^wᵢ)·e^S` | 11 |
| **S8** | `S = (log P^A − Σ wᵢ·log Pᵢ) − Median_W(·)`; equal-weight **basket** (F-fix: was pair), **W=90** (F-fix: was 60) 4h | `P^A = (Π Pᵢ^wᵢ)·e^(S+C_t)` | 11 |

**Total binding cells: S5 11 + S6 5 + S7 11 + S8 11 = 38** (S8 now basket-based per `new-anchor-series-suggestions.md` headline variation; the pair−median-60 variant is dropped, resolving finding F).

**Min-mate-count — valid-basket-bar predeclaration (amendment §7 basket-feed fix; CF-MR-003 F-1 risk).**
A basket bar (S5/S7/S8) is **valid only if the full predeclared class-mate set has an exact-`CloseTime`
4h bar** (min-mate-count = full membership: FX = the other 6 majors; indices = the other 3). Any missing
mate → basket bar **invalid** → **arm no new order** that bar (existing positions run their own §5 exits
unchanged). This keeps β/anchor composition **fixed** — no silent mate-drop shifting the anchor. Per-bar
mate-count + gap flags are still emitted (§11) so the audit can bound the invalid-bar rate and confirm no
drift. S6 (single pair, β=1) needs both legs present by the same rule.

## 5. Execution model — faithful full exit (frozen)

Per 4h bar, from ≤ t-1 anchor/σ (`WZ=200`, `Z*=2.0`), when flat: arm resting bracket
sell-limit `exp(a+Z*σ)` / buy-limit `exp(a−Z*σ)`; exit target `exp(a)`. Band **is** the trigger (no z
pre-gate; z provenance-only, L-12). On fill: sibling cancelled (primary reentry=none); position opens.

**Exit set (all three; open-to-open; no other exit methods — proposal constraint):**
1. **Form-2 (favorable limit, REFRESHING).** Each bar while holding, recompute `exp(a_t)` (moving anchor
   mean) and modify the resting TP to it. **Assert favorable placement before every placement** (long:
   TP>mark; short: TP<mark) — skip+log if violated (fixes finding F guard).
2. **Form-1 (event reversion, market at next bar open).** Each completed bar, if the position's spread has
   reverted through mean (short: `spread ≤ mean`; long: `spread ≥ mean`), close at the next bar **open**.
   This is the moving-anchor exit the static TP cannot represent (fixes findings A/B/C).
3. **Horizon (last-resort time stop).** `H_i = min(48, 3·HL_i)` 4h bars → market close at bar open.

**Breach policy:** predeclared test vs the **≤ t-1 confirmed close** (proposal wording) — skip a side
already through that close; **additionally** record the live-bid/ask skip as a disclosure. Quantify both.
**Refresh (primary):** re-arm each 4h bar while flat.

## 6. Axes — tested immediately (operator NEW); binding-primary + disclosure variants

**Binding PRIMARY config (the one Holm-adjudicated):** faithful full-exit · reentry=**none** ·
**both-directions** (no trend filter) · refresh=**R** · target=mean. This is the faithful proposal strategy.

**Disclosure variants (analyzed in the SAME emission from the start — not gated behind primary edge; if a
variant materially changes the verdict it becomes the primary of a follow-up EXP with its own multiplicity):**

| Axis | Variants | Derivation |
|---|---|---|
| **Recalc → fill** | R (refresh/bar) vs S (place-once, leave until fill/horizon) | **2 runs** (lifecycle-changing). Quantify fill rate, near-miss, refresh-moved-away-from-excursion. |
| **Trend conditioner** | fade only adverse-to-4h-trend: strong-up→long-only, strong-down→short-only, weak→both, weak→neither | **python slice** of the both-directions run (drop with-trend side). Trend measure §7. |
| **Vol regime** | low / mid / high spread-σ tercile | **python slice** (emit vol state per bar). |
| **Reentry** | none / allow / extend (z\* ∈ {2.0,2.5,3.0} ladder) | **superset run** (extend+allow ladder w/ per-fill provenance) → derive none/allow/extend by truncation; separate run only where truncation unsound. |

Rationale for primary+disclosure split: operator mandate = test all immediately (satisfied — one emission
covers all via slices + 2 lifecycle runs). Multiplicity discipline = one predeclared binding primary avoids
comparison inflation (L-03/L-08); the conditioners are reported per-leg, booked only via a follow-up.

## 7. Conditioner + MR-screen definitions (predeclared, informative-not-gating L-12)

- **Trend (traded instrument, 4h):** `trend_z = (EMA_20 − EMA_50)/σ_close(WZ)`; direction = sign; strength
  bands (disclosed) `{0.5, 1.0, 1.5}`, "strong" = `|trend_z| ≥ 1.0`. Mild-parametric, streaming, cheap.
- **Vol regime:** tercile of current spread-σ within trailing 500 4h-bar σ history → {low,mid,high}.
- **MR screen (full 6-stage, per series/stratum, ≤ t-1, TRAIN):** robust detrend · lag-1 autocorr ·
  VR(q=4) · ADF · KPSS · AR(1) **and** OU half-life. All **reported, none gating**. HL feeds `H_i` only.
- **Independence + single-emission ordering (amendment §5).** The 6-stage screen **and** the native
  reversion-completion read (§9 E3: reach-anchor / fraction-recovered / time-to-anchor ÷ HL under the
  §10 dislocation-matched null) are the "how mean-reverting is each series" characterisation, answered on
  the series' own terms. They are **booked before net-verdict outcome contact** (so characterisation is
  not back-rationalised from the tradability result), yet derive from the **same single cTrader
  emission** as the tradability run (the per-bar/hold/exit state of §11) — **no separate script run, no
  vectorized Python edge module** (L-01). "Alongside" = one emission, analysis-only Python, MR read first.

## 8. Cost model (analyst-derived; binding-leg L-02)

| Component | Binding (conservative) | Disclosure |
|---|---|---|
| RT cost | Frozen per-instrument 4h `cost_bps` (referee cost map) on **every** completed round-trip → `realized_bps` (net). | `{0.5,1,2}×` + limit-favourable (commission-only on limit legs, half-spread only on market legs). |
| Form-2 exit | Limit (favourable fill) — commission only in the favourable-disclosure. | — |
| Form-1 / horizon exit | Market — full half-spread + commission (inside RT `cost_bps`). | — |
| Unfilled entry | No trade, no cost (selection; diagnostic = fill rate). | — |
| MTM | **Intra-position mark-to-market** per 4h bar (L-09) — required for the per-bar referee + comparability. | — |

## 9. Endpoints, adjudication, multiplicity, power

| Component | Spec |
|---|---|
| **Tradability (binding)** | Per-4h-bar realized net series (engine exact-fill, intra-position MTM, cost §8) → frozen referee (`referee_pstar.gate_stack_pstar`, 4h, q\*=0.75). Per-stratum verdict (L-03). PRIMARY config only. |
| **Per-trade disclosure lens** | Non-binding per-trade evaluation alongside the frozen per-bar verdict (audit §4 vehicle-fit flag; does NOT replace or retune the frozen referee). |
| **Availability (alongside)** | (E1) entry fill rate; (E2) gross P&L/filled RT; (E3) **reversion-completion** (native estimand: reach-anchor / fraction-recovered / time-to-anchor ÷ HL) — separates form-1 reversion from static price-hit (fixes finding C). Dislocation-matched matched-random control (§10). |
| **Exit-leg split** | Fraction + P&L by exit reason {form1, form2, horizon}; by trend bucket; by vol regime; by reentry variant; R-vs-S. |
| **Multiplicity** | 4 series axes → cross-axis Holm max-stat (PRIMARY). Per-stratum binding; conditioner/reentry = disclosure. |
| **Power / MDE** | Per-cell MDE = smallest Δ the block-bootstrap resolves at n_episodes; `MDE>Δ*` or `n_episodes<N_min` → UNPOWERED (never FAIL). N_min = **frozen 4h referee `min_state_count`=8** (frozen value governs, not the design-preferred 20 — L-12). |
| **TEST tally** | **0 counted reads** (TRAIN-only; ledger unchanged). |

## 10. Availability control + leak tripwires

- **Dislocation-matched matched-random control:** among 4h bars at the same `|z|` bin, sample screen-free
  random bars, count-matched; each gets a random entry+exit at the same distance (preserves round-trip
  geometry, varies only whether the screen placed at the extreme/mean). Δ = cond − ctrl; **moving-block
  bootstrap** on conditioned events, iid on control; per-cell ci_low (`n_boot ≥ 10 000`); **block-permute
  per-event outcomes, never rotate the path** (L-07). Disclosure nulls: random-timing, random-within-|z|-bin.
- **Leak tripwires (binding — must collapse on any admitting cell):**
  1. **Peer-feed phase-shift shuffle** (future-destroy) — shift peer feeds a random phase, recompute
     spread, re-emit, re-adjudicate; cross-instrument edge must collapse; survival ⇒ REJECT.
  2. **Label permutation** — permute extreme labels among candidate bars; marginal edge must collapse.
  - Both were **vacuous** on EXP-013's null (gate-debt) — **re-run on any EXP-014 admitting cell** before booking.
  - **Tripwire bite-check (predeclared; non-vacuity gate — L-08, EXP-012 F-2 precedent).** A collapse is
    informative **only** if the tripwire could have detected an edge. Before booking any admitting cell's
    collapse: inject a **planted synthetic reversion edge** into that cell's emitted per-event outcomes and
    confirm **each** tripwire (peer-feed phase-shift, label-perm) **destroys the plant** (post-shuffle
    ci_low ≤ 0). A tripwire that cannot bite the plant is **vacuous** → its collapse is non-informative →
    the cell **cannot clear the leak gate** (gate-debt persists; not a pass). This forecloses the EXP-013/
    EXP-012 mean-invariant vacuity (a stat the permutation cannot move can never "collapse").

## 11. Emission spec (rich — quantify every leg; §6 of amendment)

Extend `SignalRecords`/`StrategyRunParquetWriter` (reusable base; default sentinels keep other models
unchanged). Per bar: **flat** — armed sell/buy levels, σ, moving anchor px, spread, z, β, **basket mate
count + gap flags**, trend dir/strength, vol regime, breach-skip flags (≤t-1-close & live-bid/ask),
would-fill/near-miss vs OHLC. **entry** — side, filled band, entry fill px+time, ladder level, z/spread/
anchor/σ, trend+vol. **hold (per bar)** — mark, moving anchor px, spread/z, form-1 flag, refreshed form-2
level, **unrealized MTM bps**. **exit** — reason ∈ {form1_reversion, form2_favorable_limit,
horizon_time_stop}, exit fill px+time, moving anchor+spread, bars held, realized per-trade bps.
**per series** — full 6-stage MR-screen vector. All ≤ t-1; `CloseTime`/`SourceCloseTime` only; forming-bar
OHLC never read.

## 12. Interpretation criteria (predeclared, frozen before outcome contact)

| Outcome | Condition |
|---|---|
| **Tradable-on-TRAIN** | ≥1 series axis clears cross-axis Holm **AND** ≥50% of that axis's powered cells referee-ADMIT (net ci_low>0) **AND** availability Δ>0 (ci_low>0) on ≥50% powered cells **AND** both leak tripwires collapse on admitting cells. → operator-gated counted TEST read (new D0). |
| **Not-tradable (now credible)** | Faithful full-exit + conditioners: availability real, net fails the majority. **Only this reinforces the terminal-branch prior** (EXP-013 could not — vehicle-incomplete). |
| **Inconclusive / UNPOWERED** | <3 powered cells/axis, or n_episodes<N_min, or direction mixed → UNPOWERED (never FAIL). |
| **REJECT** | Edge survives either future-destroy tripwire → leak → hard stop. |

Effect floors (economic-reasoning, band disclosed — L-08): E1 anchor-hit `Δ*=+0.03` (band {0.02,0.03,0.05});
E2 gross-P&L `Δ*=+0.03`; E3 supportive. Referee MDE = frozen 4h floor (candidate-blind). **Per-leg reporting
mandatory** — a null must name exactly which leg failed where, not a pooled wash.

## 13. Complexity budget

| Item | Planned | Budget |
|---|---|---|
| Statistical tests | availability Δ + referee adjudication + 2 leak tripwires = 4 | 4 ✓ |
| Visualisations | exit-leg split, per-axis net verdict, availability Δ, MR-screen char, trend/vol slice heatmap | 3-5 ✓ |
| Code modules | C# planner+robot+feed+records extend (from scratch/extend) + Python ingest/analysis (from scratch, logic-reuse only) | price-primary C# + Python ✓ |

## 14. Implementation safety constraints (for experiment-developer)

- **Causality:** all decision inputs ≤ t-1; forming 4h bar OHLC never read; engine enforces by construction (L-01).
- **Temporal:** 4h bars by `CloseTime`; limits fill on m1; positions emit per-4h-bar with real OHLC. Never bar indices.
- **From-scratch:** family logic (spread, z, entry/exit mapping, form-1/form-2/horizon, conditioners, ladder,
  order mgmt) new/extended. Multi-symbol StrategyHost + ingestion = reusable. Adversarial contamination
  review per amendment §7 — apply the required fixes before reuse.
- **Performance:** streaming O(1)/O(n) per bar; rolling windows; incremental OLS/median; bounded memory
  (fixed trailing buffers); append-only parquet. **No** perf shortcut may compromise causality, denominators,
  metric defs, or streaming validity.
- **Holdout fence:** `AnalysisEndUtc` = each file's first-49% cutoff; `HoldoutFence.AssertCanEmit` throws at/after fence. Final-30% never processed.

## GATE: APPROVE (orchestrator inline pre-exec, 2026-07-02 — SUPERSEDES prior APPROVE)

**Revision (2026-07-02, post-review).** Prior APPROVE missed three predeclarations; closed before this
stamp (gate was open → not scope-expansion): **(G1)** valid-basket-bar **min-mate-count** predeclared
(§4 — full-membership rule, no silent β/anchor drift; amendment §7); **(G2)** leak-tripwire
**non-vacuity bite-check** predeclared (§10 — planted-positive must collapse or the tripwire is vacuous
and cannot clear the gate; L-08 / EXP-012 F-2); **(G3)** MR/reversion characterisation **booked before
net-verdict contact, from the same single emission**, no separate run / no vectorized edge module (§7;
amendment §5). All three frozen before outcome contact. Registry `cf-mr-004.md` S8 def synced to
basket−median-90 (G4).

**Design-level exit-set diff (L-14).** Proposal (`original-phase002-thoughts.md`) mandates two named
exits: form-1 (event-driven back-to-anchor) and form-2 (precalc favorable limit). Design §5 ships:
1. form-2 **refreshing** (recompute `exp(a_t)` each bar while holding — fixes EXP-013 frozen-TP
   finding B); 2. form-1 event-reversion (close at next bar open when spread reverts through mean —
   fixes absent-form-1 finding A); 3. horizon last-resort `min(48, 3·HL_i)` (additive safety,
   amendment §3 item 3). **Both proposal-named exits present.** No substitution. ✓

**Leak tripwires (L-01).** Two future-destroying controls shipped (§10): 1. peer-feed phase-shift
shuffle; 2. label permutation. Both must collapse on any admitting cell; survival ⇒ REJECT. Each gated by
a predeclared planted-positive bite-check (§10) — a tripwire that cannot destroy the plant is vacuous and
cannot clear the leak gate (forecloses the EXP-013/EXP-012 mean-invariant vacuity). ✓

**Registry precondition.** CF-MR-004 REGISTERED (`cf-mr-004.md`). 0 counted TEST reads (TRAIN-only,
ledger unchanged). 0 slots. Holdout sealed. Frozen referee untuned. ✓

**All 6 EXP-013 findings addressed:** A (form-1 absent) → present §5.2. B (frozen TP) → refreshing
§5.1. C (mechanism confounded) → native reversion estimands §9 E3. D (incomplete MR) → 6-stage §7.
E (no reentry) → none/allow/extend §6. F (S8 wrong + guard missing) → basket+median-90 §4 +
favorable-placement guard §5.1. ✓

**Price-primary.** cTrader in-engine, `Mode=NativeOrders`, m1 fills own resolution. No vectorized
Python edge module (L-01/P-09). Python analysis-only on emitted `data/strategy_runs/EXP-014*/`. ✓

**Hard constraints.** Open-to-open, ≤ t-1, `CloseTime` alignment, forming-bar OHLC never read,
final-30% never loaded (`HoldoutFence.AssertCanEmit`), per-stratum binding (38 cells, 4 axes →
cross-axis Holm), cost realism binding §8, from-scratch family code (L-13), frozen referee never
tuned (L-12), no pitfalls-ledger dead end re-run, no scope expansion. ✓

**Complexity budget.** 4 tests / 3-5 plots / C#+Python → within envelope. ✓

**Design density.** ~210 lines (budget ~300). Tables/bullets. No caveman compression needed. ✓

**Status:** READY for Stage 2 (Implement). Credentialed cTrader-CLI run is operator-gated (Stage 3).

**Implementation review items (developer, Stage 2).** Verify in code: favorable-placement guard
asserted before every form-2 (re)placement; ≤t-1-close breach test shipped + live-bid/ask disclosure;
rich emission all legs separable (exit reason, trend bucket, vol regime, reentry variant, R-vs-S);
contamination fixes per amendment §7 applied; `AnalysisEndUtc` = EXP-013 cutoffs reused.
