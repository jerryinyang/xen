# XENA Lane — Portfolio-Construction Workflow + Referee Framework (INFR-006)

**The DEFAULT route for incoming ideas** (operator decision Q3, 2026-07-10): operator
presents an idea → it enters a XENA universe. EXP/SPDR lanes remain available but are
**operator-invoked only** (exploration/characterisation). XENA replaces per-candidate
referee adjudication as the tradability route (the L-12 fix pathway).

Design record: `python/experiments/INFR-006/design.md` (plan, locked decisions, review-fix
log, battery results). Spec source: `.ignore/temp/new-referee/xena-model.md`.

## Principle

**No per-candidate evaluation.** Every (model × parameters × instrument × domain) is a
valid candidate — no qualification gates at candidate level. Candidates run once in
cTrader; the portfolio framework selects the subset. The optimizer is a candidate
*generator*, never a *certifier*: certification is machinery the search cannot influence.

## Pipeline

```
1 Universe assembly ... manifest + engine emissions → data/strategy_runs/XENA-<univ>/
2 Candidate gate ...... xen.xena.ingest.gate_universe → xena_candidate_gate.json (BLOCKING)
3 Search .............. xen.xena.search.run_restart ×10–15 (LAHC, TRAIN search band only)
4 Certification ....... xen.xena.certify.certify_and_rank (plateau screen + fold ranking)
    [OPERATOR — reviews evidence package; approves gate spend]
5 Final gate .......... xen.xena.final_gate.run_final_gate (TEST band, counted, cap 2)
    [OPERATOR — final verdict on the artifact]
```

## Price-primary carve-out (binding)

- **cTrader (per candidate, once):** all signal logic; standard fills-based emission under
  the `AnalysisEndUtc` fence — `positions.parquet` (bar grid + `RealOpen` marks) +
  `cis_trades.parquet` per-leg ledger with **finite `SlPrice` on every leg** (stop distance
  `|EntryFill − SlPrice|` is the sizing denominator; no engine stop ⇒ gate REJECT).
  Candidate never sizes, never sees account state.
- **Python oracle (`xen.xena.oracle`, per subset):** chronological composition ONLY —
  FM(t), `R_i = r·FM·w_i` sizing, global `R_max` admission (rejected signals logged as
  first-class events — the sole interaction channel), cost charging (spread + commission,
  L-22 binding), segment-end censoring, reconciliation invariant (raises). Deterministic:
  (bitmask, segment, seed) → bit-identical. It may never alter an entry/exit decision.
- A candidate whose logic depends on account state cannot use this carve-out.

## Frozen registry (treat like the frozen referee)

`python/experiments/INFR-006/results/xena_frozen_registry.json` — verify with
`xen.xena.calibration.verify_frozen_registry`. **Active pin: v3 (2026-07-10), sha256
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

**Enforced in code (review F01):** for live universes, `certify_and_rank` and
`run_final_gate` MUST receive `registry_path`; they hash-verify the pin and refuse
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
  process. cTrader emissions are gross as always (engine costless).
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
- Per-candidate `cost_bps` + `money_per_unit` pins stay verdict-bearing for the
  deployability read (L-21): wrong pin = wrong informational block = wrong deployment
  decision.

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
elements); C# batch manifest runner pending first live universe.
