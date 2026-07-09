# EXP-012 — CF-MR-003 CONC-1 Track 2: form-2 limit-at-anchor fade, exec-15m

**Status:** COMPLETE — **NOT-TRADABLE (POWERED)**. **Class:** price-primary, cTrader in-engine (L-01).
**Phase:** 003 CONC-1, Track 2 (the exec-15m arms EXP-010 deferred behind E7). **Budget:** 0 counted TEST
reads (TRAIN disclosure), 0 new candidate slots, holdout sealed. **Date:** 2026-07-01.

## Question

On the EXP-009-admitted exec-15m cells, does the form-2 limit-at-anchor fade (entry = live limit at the
≤t-1 `|z|≥2` band edge; exit = precalc favourable limit at the higher-domain anchor mean `a[t-1]` fixed
at entry; no re-entry) earn a **net-positive** per-15m-bar realized edge — binding-leg cost charged —
that clears the **frozen 15m referee** (`gate_stack_pstar`, domain="15m"), **per stratum**? Or is it
cost-dominated / referee-REJECT / underpowered?

## Method

- **24 cells, one Holm family, two sub-families:** T2a = 14 S3_DETREND single-symbol (rolling-OLS
  log-price trendline residual anchor, W=200 exec-15m); T2b = 10 S5_SPREAD multi-symbol rolling-β
  class-mate basket anchor. All anchor/selector/limit logic in the C# engine (`CrossDomainMrLimitModel.cs`,
  `--CdmSeries`); S3 OLS verified bit-parity vs `cross_domain_mr.rolling_ols_fit` (max |Δ| 1.8e-15).
- Per-symbol TRAIN fence (`AnalysisEndUtc` = first-49% cutoff); holdout never emitted.
- Python ingest-only: assemble per-bar realized NET bps (open-to-open, intra-position MTM L-09, one
  round-trip cost/entry L-02) → `gate_stack_pstar(domain="15m")`, Holm-24. Cost = frozen per-instrument
  15m round-trip (= 1h value, E7-frozen).
- Gate-debt discharge: **F-1** vehicle fidelity (in-engine z vs reference z; tol z_corr≥0.90 ∧
  Jaccard≥0.70); **F-2** planted-positive power check; **live future-destroy** = phase-shifted-basket
  shuffle run.

## Results

**All 24 cells POWERED** (episodes 70–390 ≥ 15m floor 25; L1=True). **0/24 admit, 0/24 Holm-admit.**

| Arm | Cells | Powered | Admit (Holm, F-1-fit) | Net bps/active (range) | F-1 z_corr / Jaccard |
|---|---|---|---|---|---|
| T2a (S3, single-symbol) | 14 | 14 | **0** | −0.77 … +0.04 (med ≈ −0.06) | 1.00 / 0.97–0.98 |
| T2b (S5, basket) | 10 | 10 | **0** | −0.54 … +0.00 (med ≈ −0.05) | 1.00 / 0.98–0.99 |

- Best cells still net-negative at CI: GBPUSD +0.04 / US2000 +0.02 bps (both CI_low < 0). Worst:
  BTCUSD −0.77, USTEC(T2b) −0.54, USTEC(T2a) −0.41. **Every CI_lower ≤ 0** — no cell clears the referee
  even pre-Holm.
- **F-1 vehicle fidelity: PASS all 24** (z_corr 1.00, Jaccard 0.97–0.99) — clears the tightened
  tolerance with margin and **discharges EXP-010's F-1 debt** (its T1 vehicle was 0.67 / 0.30). The S3
  single-symbol path (no basket carry-forward) is faithful.
- **Power is real:** F-2 planted-positive (+8 bps/active) detected **24/24** ⇒ the vehicle can see a real
  edge at this N. The null is genuine, not a failure to test.
- **Valid future-destroy CLEAN:** live phase-shifted-basket shuffle → 0 survivors, `tripwire_pass=True`.

**Mechanism.** The edge is null-to-negative at the 15m horizon exactly as the LOW prior anticipated:
shorter-horizon reversion captures a smaller favourable move against the **same** per-instrument
round-trip cost, so the limit-at-anchor exit cannot out-earn the binding leg. The extra 15m episodes
clear the higher 15m power floor, but they land on a null-to-negative net — converting EXP-010's
UNPOWERED gap into a **definitive powered close**.

## Audit caveat (see `audit.md`)

The raw script's `REJECT_LEAK` headline is a **false trip** and is superseded
(`results/verdict_corrected.json`). Cause: the Python F-2 "future-destroy" permutes the realized-bps
array, but the referee scores the **mean**, which is **permutation-invariant** — a constant additive
plant can never collapse under it (23/24 `destroyed_pass=True`). This is a provably ill-posed control,
not a strategy leak. The **valid** future-destroy (live phase-shift shuffle) is clean, F-1 is fit, and
all 24 nets are ≤0 at CI, so the finding moves no verdict-bearing number. Audit PASS. Follow-up (new
scope): a Python-side leak control for a mean referee must break alignment causally (permute positions +
re-assemble), never permute P&L.

## Conclusion

**CF-MR-003 CONC-1 Track 2 (exec-15m) = NOT-TRADABLE (POWERED).** The form-2 limit-at-anchor MR fade does
not earn a net-positive edge on any of the 24 admitted exec-15m cells; the vehicle is faithful (F-1) and
adequately powered (plant 24/24), and the valid leak control is clean. Combined with EXP-010 (exec-1h
NOT-TRADABLE, UNPOWERED) and the CF-MR-002 exoneration, **CF-MR-003 tradability is closed**: availability
(EXP-009 SCREENED-ADMIT) does **not** survive to net at either the 1h or 15m execution horizon. Not a
P-02 rescue — the LOW prior held.

## Follow-ups (separate scopes only)

1. Redesign a non-vacuous Python-side leak control for the mean referee (position-permute + re-assemble),
   or standardize on the in-engine phase-shift shuffle as the sole future-destroy. *(methodology)*
2. No further CF-MR-003 concretization is warranted; a counted TEST read / holdout release remains
   **DEFERRED** and is now moot (no TRAIN net-positive to promote).

## Links

`design.md` · `code/run_experiment.py` · `results/verdict.json` (raw) · `results/verdict_corrected.json`
(binding) · `audit.md` · plots: `net_per_cell.png`, `episodes_vs_floor.png`, `f1_fidelity.png`,
`f2_plant_destroy.png` · runs: `data/strategy_runs/EXP-012-t2a|t2b|t2b-shuffle/`.

## GATE (post-exec) — recorded by orchestrator

**GATE: APPROVE** (2026-07-01). Verdict forensics + causal-provenance passes present (audit.md §3/§5);
per-stratum masking check done (T2a 0/14, T2b 0/10, no pooled masking); the one control defect (F-2
mean-invariant permutation-destroy) is self-caught, shown non-verdict-moving, and superseded by
`verdict_corrected.json` — no verdict-material finding, no re-execution required (operator-confirmed: verdict
NOT-TRADABLE under either reading). Signal-registry disposition recorded and family concluded.

- **Registry disposition:** CF-MR-003 CONC-1 Track 2 CLOSED **NOT-TRADABLE (powered)**; **family RETIRED**
  (SCREENED-ADMIT → NOT-TRADABLE at 1h + 15m — Phase-003 retrospective). 0 counted reads (TRAIN disclosure),
  0 new slots, holdout sealed. Multiplicity Phase-003 batch updated (both tracks; refuted/inconclusive
  branches retained). Test-read ledger: disclosure only, no counted read (no entry — mirrors EXP-010).
  Family status advanced in `candidate-families/cf-mr-003.md` + `families/cf-mr-003/INDEX.md`.
