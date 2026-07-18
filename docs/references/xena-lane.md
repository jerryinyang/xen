# XENA Lane v2 — Portfolio-Construction Workflow (INFR-006 → INFR-009 → INFR-012 rebind)

**Version:** v2 (INFR-012, 2026-07-15) — Nautilus emissions + Bybit universe
**The DEFAULT route for incoming ideas** (operator decision Q3, 2026-07-10; route RESTORED
2026-07-14 under INFR-009 P5): operator presents an idea → it enters a XENA universe.
EXP/SPDR lanes remain **operator-invoked only**.

## VOID on new stack (binding, INFR-010 R4)

All frozen registry pins from chapter 03 (INFR-006/009) are **VOID for new Bybit/crypto data**.
No XENA universe may run on the new stack until a fresh calibration cycle (CAL discipline:
n_null sizing, design/confirm bank split, predeclared n) completes and a new hash-pinned
registry is operator-signed. Chapter-03 registry artifacts remain for archived reproducibility
only.

## Archived binder (chapter 03 only — VOID on Bybit/crypto)

The following INFR-009 P5 mechanics are **archived reference** for chapter-03 reproducibility.
They MUST NOT bind any crypto/Bybit universe until a fresh CAL cycle produces a new pin.

**Archived binder (INFR-009 exit (c), P5 pin):** two-stage sample-split — stage-1 costless intensive
`g_gross` search → fix top-1 → stage-2 leg-studentized LCB on a distant/embargoed band.
- **Gross structure:** `lcb_g_leg_studentized(g_gross) > 0` (costless).
- **Deployability:** `lcb_g_leg_studentized(g_net) > 0` after **flat injected RT = 1.0 bps**
  (not stream `cost_bps` on engine-costless emissions).
- **Registry:** `python/experiments/INFR-009/results/pc_frozen_registry.json` (schema v2,
  sha256 `db87dc1a…`; parent P4 `44e1aa3c…`). α̂=5.0% boundary accepted (Wilson upper 9.0% disclosed).
- **INFR-006 v3** absolute extensive-F binders (X / F_floor / gate 0.0558) remain **superseded** —
  artifacts retained; do not re-enable on the binding path.

Design record (redesign): `python/experiments/INFR-009/design.md`. Historical INFR-006 plan:
`python/experiments/INFR-006/design.md`. Spec source: `.ignore/temp/new-referee/xena-model.md`.

## INFR-016 — value chain is report layers, not gates (2026-07-18, operator-ratified)

Every value / quality / significance / selection read is a **report layer**
(`xen.xena.report_layer.LayerReport`): per candidate, `observed / ideal / interpretation`, **no
`pass` field**, nothing machine-dropped. The operator authorises which candidates advance. Two
disjoint layers (design §4):

- **VALIDITY attestations (HARD)** — holdout fence, causal ≤t-1, estimand reconciliation,
  non-STUB fence, no-local-accounting, structural computability, oracle determinism, and
  **future-destroy leak survival** (edge survives destroying FUTURE info ⇒ acausal L-01 leak).
  A failure = *emission invalid → fix the data*, never *no edge*.
- **VALUE reads (REPORT LAYERS)** — cost floor & breakeven, cadence coverage, **leg-power**
  (`power_layer`, retires `n_legs_floor` veto), search score, fold stability, **stage-2 bounds
  for ALL subsets AND per-cell** (`stage2_bounds_layer`, retires `one_subset` top-1),
  **within-sample attribution** collapse (`controls.attribution_derangement` — reported
  fraction, retires `hard_fail_leak` collapse<0.5), **sign battery** (`controls.sign_battery`,
  ≥2000 seeds → effect size + one-sided p + CI, retires the 25-seed `at_or_above_p95` boolean),
  cost/funding sensitivity, spread-scale routing, **net deployability**
  (`final_gate.final_report_layer`, retires the final gate's `passed`).

Interpretation bands `SUPPORTED / WASH / CONTRADICTED / UNPOWERED / SUGGESTIVE / STRONG` are
**labels on a layer, never gates**. The counted-read ledger + holdout-safety stay as read-budget
/ validity controls. Grounding failures (HTFCAP): a 25-seed P95 boolean auto-"failed" SOL 24.9
bps (p≈0.22, ~P78 at 2000 seeds — SUGGESTIVE, not refuted); `one_subset` hid it and certified a
~1 bps leak-class cell. `python/experiments/INFR-016/design.md`.

## Principle

**No per-candidate evaluation.** Every (model × parameters × instrument × domain) is a
valid candidate — no qualification gates at candidate level. Candidates run once in
**Nautilus**; the portfolio framework selects the subset. The optimizer is a candidate
*generator*, never a *certifier*: certification is machinery the search cannot influence.
**INFR-016:** even the post-search chain never *certifies* — it **reports layers**; the
operator authorises progression.

## Pipeline

```
1 Universe assembly ... manifest + Nautilus emissions → data/nautilus_runs/XENA-<univ>/
2 Candidate gate ...... xen.xena.ingest.gate_universe → xena_candidate_gate.json (BLOCKING)
3 Search .............. xen.xena.search.run_restart ×10–15 (LAHC, TRAIN search band only)
4 Certification ....... xen.xena.certify.certify_and_rank (plateau screen + fold ranking)
    [OPERATOR — reviews evidence package; approves gate spend]
5 Final gate .......... xen.xena.final_gate.run_final_gate (TEST band, counted, cap 2)
    [OPERATOR — final verdict on the artifact]
```

## Price-primary carve-out (binding)

- **Nautilus (per candidate, once):** all signal logic; emission contract v1 under catalog
  fence — `bar_marks.parquet` (bar grid + `RealOpen` marks) + `positions_ledger.parquet`
  per-leg ledger (shim → `cis_trades`) with **finite `SlPrice` on every leg** (stop distance
  `|EntryFill − SlPrice|` is the sizing denominator; missing/non-finite `SlPrice` ⇒ gate
  REJECT). **Clarified (operator, 2026-07-10, CF-MTFCTX-001 reconciliation):** the gate
  requirement is the finite per-leg `SlPrice` FIELD; a live engine stop order is not
  required — a synthetic sizing-only stop price satisfies the contract. Candidate never
  sizes, never sees account state.
- **Python oracle (`xen.xena.oracle`, per subset):** chronological composition ONLY —
  FM(t), `R_i = r·FM·w_i` sizing, global `R_max` admission (rejected signals logged as
  first-class events — the sole interaction channel), cost charging (Bybit fees + T1 spread +
  funding via `xen.evaluation`, L-22 binding), segment-end censoring, reconciliation
  invariant (raises). Deterministic:
  (bitmask, segment, seed) → bit-identical. It may never alter an entry/exit decision.
  **INFR-007 (NEUTRAL, 2026-07-12):** the sequential event fold is dispatched to the
  `xena_fold` Rust kernel (`OracleConfig.backend`, ~15×/eval) — proven bit-identical to
  the Python loop by the pinned parity corpus (`python/tests/test_xena_fold_parity.py`)
  and the XENA-001 rid-0 replay credential; sorting, mark schedules, bootstrap RNG, and
  all search/certify/gate layers stay in Python unchanged.
- A candidate whose logic depends on account state cannot use this carve-out.

## Frozen registry (chapter 03 archive — VOID on new stack)

`python/experiments/INFR-006/results/xena_frozen_registry.json` — verify with
`xen.xena.calibration.verify_frozen_registry` **on archived FX/indices universes only**.
**Archived pin: v3 (2026-07-10), sha256
`537d691aaf59c19220ac65b922d780e970167e8b71972ea8d864402b36e672a6`** — operator-signed
(v2 X/F_floor sign-off + A-4 dual-gate directive). Superseded: v1 costed-selection
(`results/v1-costed-selection/`), v2 net-binding-gate (`results/v2-net-binding-gate/`).

| Quantity | Frozen value |
|---|---|
| Search params | `SearchParams()` registry defaults (L=150, c=5, kick 2–4 swap-paired, probs .25/.25/.45/.05, B=150, block 64, P25, q=0.6, clear-win 2.0 SD, init size 5) |
| Gate mechanics | decay windows 4, gate boot seed 424243, gate B = max(B, 200) — fixed in code, listed for §11 registry completeness |
| Plateau X | 0.70 (min single-drop F̂ ratio) |
| F_floor | 0.4302 (minimum robust objective, gross scale; conjunction with X) |
| Gate pass threshold | 0.0558 on the GROSS gate bootstrap P25 (rule: max(0, GROSS null-P95); A-4) |
| Segment layout shape | 50/30/20 search/ranking/gate (`SegmentLayout.from_span`) |
| Base objective F | log-wealth; DD limits are gate feasibility checks, never inside F |

**Calibration credentials (WS-6 v3, 550 realistic-null universes — shared regime-GBM
path, correlated coin-flip nulls, vol-clustered entries — real code paths incl. the A-4
dual gate):** null certification 2/300, **end-to-end false passes 0/300 → FPR ≤ 1% at
95%** (rule of three; the gross gate threshold killed both certifiers — layered defense
observed). End-to-end power: 18 bps gross 16% · 30 bps 70% · 40 bps 94% · 60 bps 100%
(at 60 trades/candidate + regime-GBM noise; restate per live trade density). All
end-to-end passers were also net-P25-positive (deployability preview 1.0). §11
insensitivity verified. Raw + summary: `python/experiments/INFR-006/results/`.

**Enforced in code (review F01, archived universes only):** for chapter-03 live universes,
`certify_and_rank` and `run_final_gate` MUST receive `registry_path`; they hash-verify the pin and refuse
thresholds/params that differ (`threshold_override_attestation` is the operator-only
escape hatch, recorded verbatim like `new_data_attestation`). Only calibration runs —
where thresholds are being derived, not consumed — pass None. Artifacts and the gate
ledger carry `registry_sha256`.

**Tuning any frozen value after seeing a live universe's outcome is a governance
violation.** A change = new predeclared calibration (new battery, new hash-pin), with a
LOOSER/TIGHTER-tagged amendment (L-23).

## Cost policy (amendments A-1 + A-4, operator 2026-07-10)

- **Selection stages (search + certification) run cost-free** (`OracleConfig
  .charge_costs=False`): commissions/spread are excluded from the portfolio-selection
  process. Nautilus T1 emissions are gross as always (engine costless-honest).
- **T1 spread-scale routing (INFR-010 §4):** candidates with gross edge within ~3× RT spread
  are undecidable on T1 — park `AWAITING_MBP` or require T2 confirm (BTC/ETH/SOL).
- **Rationale (operator, 2026-07-10, review F02):** the dual gate separates the
  characterisation of model performance / signal quality (gross) from failure-by-cost
  scenarios (net). A portfolio that dies only under costs is a cost problem, not a
  selection-machinery problem; one blended binding number would hide which failed. Net
  stays strictly informational but important; the final verdict is always the operator's.
- **The final gate runs the §A.4 protocol TWICE (A-4):**
  - **GROSS run — BINDING.** `passed` = gross bootstrap P25 ≥ threshold AND gross-path
    DD feasible. Validates the pure optimizer + walk-forward selection machinery on the
    same scale the selection ran on. Gate threshold is derived from GROSS null gate P25s.
  - **NET run — INFORMATIONAL.** Full costs charged + its own DD read; recorded in the
    artifact as `net_informational`.
- **L-22 retained clause (binding):** a gross gate pass is a **selection-machinery
  verdict, never a tradability/deployability claim**. Any deployability claim MUST cite
  the `net_informational` block (net P25, net DD) — and deployability remains
  operator-gated as always.
- **DD feasibility**: FTMO-style limits (daily 5% vs day-start equity, total 10% vs
  initial) — binding on the gross path; disclosed on the net path.
- Per-candidate cost pins use `bybit_round_trip_cost_bps` + per-symbol pseudo-quote spread
  series; `money_per_unit` pins stay verdict-bearing for deployability (L-21).

## Temporal mapping (Q1, tightened)

TRAIN is **partitioned**: search band ∪ disjoint contiguous purged selection folds
(ranking band). Folds never overlap the search band. Final gate = TEST, continuous
walk-forward, fresh account state. Band boundaries are pre-registered per universe.
Global 30% holdout untouched, as always. CPCV/stitched paths excluded (account-state
path dependency).

## Gate ledger (Q2 — LOOSER amendment vs spec §A.5, tagged)

- Portfolio-level ledger `xena_gate_ledger.json` at the universe root; **cap 2 final
  gates per universe**; a slot is spent on pass OR fail.
- The second slot = a **materially different certified subset** or **new TEST data** —
  never a free retry. `run_final_gate` refuses a subset identical to a FAILED row unless
  `new_data_attestation` is supplied. **The attestation is an OPERATOR-ONLY field**: an
  agent must never fabricate or supply it; it is the operator's signed reason, recorded
  verbatim in the ledger.
- A failed gate = negative result; no post-hoc threshold revision; no re-search on the
  gate segment.
- **Similarity to prior failed subsets is reported, never gating** (operator decision
  2026-07-10, review F03): the artifact carries `max_jaccard_vs_prior_failed`; only exact
  identity is refused. Candidate-removal responsibility belongs to the whole portfolio
  referee system — per-candidate qualifying rules are against XENA principles.

## Registry semantics

- The registered object is a **XENA run**: universe manifest + frozen registry hash +
  pre-registered band boundaries. Multiplicity ledger logs `evaluation_count` (total
  oracle calls) AND `distinct_subsets` per run — both travel with every reported number
  (§10.4). No result without its evaluation counts.
- Universe status changes (certify/retire) happen at operator-signed checkpoints, mirroring
  the experiment≠family separation.

## Analyst reads (certification evidence package)

`certify_and_rank` output is **evidence, not a verdict**: plateau reports (min drop ratio,
keystone attributions — a keystone is routed to individual scrutiny, not just discarded),
restart F-dispersion + Hamming proximity (wild dispersion = noise-dominated landscape:
distrust the winner), fold ranking (median/worst + PBO-like stat), collapse fractions,
resim-divergence rows (spec §14 ledger-resampling detector: search-band bootstrap claim vs
full re-sim fold scores per certified finalist; watch `frac_folds_below_search_p25` → 1).
Gate artifact adds: bootstrap P25/median/P75 (never one number), decay windows +
rank-corr, search-stage gap (labelled: search-P25 claim vs gate median — deliberately not
like-for-like), seed spread. Operator judges value on this package.

## v1 limitations (logged, revisable per spec §12)

FM(t) = marked equity (no leverage-margin model); `money_per_unit` default 1.0 is
USD-quote-only (non-USD-quote symbols must pin the factor); deep validation subsumed by
fold ranking while the oracle is deterministic (multi-seed leg activates with stochastic
elements); Nautilus batch manifest runner pending first live crypto universe (post-CAL).
