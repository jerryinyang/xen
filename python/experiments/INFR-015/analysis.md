# INFR-015 — Analysis (data-analyst evidence)

**Emission:** synthetic CAL banks (no Nautilus emission; estimand gate N/A — no price
emission read; per design §12 N/A declarations).  
**Artifacts:** `results/design_CLS-EPISODE.json`, `results/confirm_CLS-EPISODE.json`,
`results/cal15_summary.json`, `results/cal15_run.log`.

## 1. Headline

| Bank | Cadence | no_search_cov | e2e α̂ | inflation | band |
|---|---|---:|---:|---:|---|
| DESIGN (n=80, seeds 95k/96k) | low | 0.0375 | — | — | ok (disclosure) |
| DESIGN | high | 0.0500 | — | — | ok (disclosure) |
| CONFIRM (n=200, seeds 97k/98k) | low | **0.095** | **0.135** | +0.040 | FAIL_ALPHA (selection_unsafe) |
| CONFIRM | high | **0.050** | **0.055** | +0.005 | FAIL_ALPHA (Wilson [0.031, 0.096]) |

Bite (design bank): low survival 0.125 (≤0.125), select 0.875; high survival 0.000,
select 1.000 — **bite PASS** (blocking did not kill power).

**Verdict recommended: TERMINAL-2.** Write policy held: no registry write; INFR-014 pin
`ac8a1eb6…` stands (CLS-FILTER LOW_ONLY_CERTIFY; CLS-EPISODE certified:false).

## 2. Evidence FOR the amendment mechanism (partial success)

- HIGH cadence: α̂ 0.080 (INFR-014) → **0.055**; cov 0.065 → 0.050; inflation +0.005.
  Blocks engaged everywhere (B 12–30, median 23; median n_legs 261). Where legs are
  plentiful and overlap-blocking applies, the fix moved both cov and α̂ toward target.
  0.055 is within 1 SE (0.016) of 0.05 — NEAR-MISS band per design §7, still not certified.

## 3. Evidence AGAINST (why LOW got worse, 0.075 → 0.135)

Per-row interrogation of `alpha_low_rows` (n=200):

| LOW slice | n | stage-2 pass rate |
|---|---:|---:|
| n_legs < 8 (⇒ B=1, fix inert) | 67 | **0.179** |
| n_legs 8–15 | 89 | 0.101 |
| n_legs 16–49 | 44 | 0.136 |
| B=1 | 67 | 0.179 |
| B=2–4 | 125 | 0.098–0.139 |

- Median top-1 n_legs on LOW = **11**. The dominant false-certify source is the
  **small-sample studentized LCB** (bootstrap-t on <16 legs, n_boot 200), not overlap:
  the worst cell is exactly where the block rule reduces to the legacy B=1 path.
- Bank-to-bank: design cov 0.0375 vs confirm cov 0.095 (Δ≈2.4·SE₈₀) — LOW coverage is
  also unstable across banks at these leg counts; the INFR-014 LOW read (cov 0.100)
  plus both INFR-015 banks are consistent with a small-n LCB defect of varying severity.
- Story-vs-proven: overlap correlation (INFR-015 hypothesis) is REAL but secondary on
  LOW; the primary LOW defect is leg-count starvation of the top-1 subset. HIGH result
  proves the overlap mechanism where n_legs is large.

## 4. Discipline

- No retune performed on confirm data (forbidden list in artifact `stop_condition`).
- Seeds verified in artifacts: coverage + α̂ rows both on 97000/98000 bases (Issue-9
  guard asserted at runtime).
- n_null fixed 80/200; no optional stopping; single form change.

## 5. Follow-up candidates (NEW design required — not this experiment)

1. `n_legs_floor` domain guard on stage-2 (`lcb_g_leg_studentized` already accepts
   `n_legs_floor`; out-of-domain ⇒ not certifiable) — attacks the proven LOW defect
   directly; floor must be derived (MDE/coverage curve on a design bank), not asserted.
2. Episode-level resampling unit (resample episodes, not leg-blocks).
3. Generator realism review of LOW top-1 leg starvation (n_cand 64 × thin episodes).

**Recommended experiment verdict: TERMINAL-2 (CLS-EPISODE remains uncertified); the
amendment is NOT SUPPORTED as sufficient, with the overlap mechanism SUPPORTED on HIGH
as a partial effect. XENA-EPSOSC stays blocked.**
