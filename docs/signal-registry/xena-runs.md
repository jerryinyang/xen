# XENA Run Ledger (INFR-006, item 5)

Live operational ledger for XENA portfolio runs — the portfolio-lane analogue of the
multiplicity registry + test-read ledger. **Append-only rows; never reset across
chapters.** One row per XENA run; gate spends also live in the per-universe
`xena_gate_ledger.json` (this table summarises them for cross-run accounting).

Rules (spec: `docs/references/xena-lane.md`):
- A run registers here at design time (before search) with its universe manifest +
  frozen-registry hash — registration-before-search, mirroring candidate registration.
- `eval_count` / `distinct_subsets` (§10.4) are mandatory at close: **no reported result
  without its evaluation counts.**
- Gate slots: cap 2/universe; second slot = materially different subset or new TEST data
  (operator attestation, recorded in the universe gate ledger verbatim).
- Universe status transitions (CERTIFIED/RETIRED) are operator-signed, checkpoint-level.

**Committed, pending design-time registration (checkpoint 011, CF-MTFCTX-001,
2026-07-10):** XENA-001 (MTFCTX-C1, CTRL-01 RANDOM) · XENA-002 (MTFCTX-C2, CTRL-02
MOMENTUM) · XENA-003 (MTFCTX-C3, CTRL-03 REVERSION) — 2,736 candidates each; rows land
here at each run's design completion (band pin required first).

| Run | Registered | Universe (N cands) | Registry sha256 (8) | Search band | Eval count | Distinct subsets | Certified | Gate slots spent | Outcome | Operator sign |
|---|---|---|---|---|---|---|---|---|---|---|
| XENA-001 | 2026-07-10 | MTFCTX-C1 CTRL-01 RANDOM (2,736) | 537d691a | 2021-06-02T00:01Z → 2023-03-08T00:00Z (ranking →2024-03-28; gate →2024-12-11T08:19Z) | at close | at close | — | 0/2 | OPEN (emitted 2026-07-11: candidate gate 2736/2736 PASS, estimand gate 2736/2736 PASS; search next) | pending |
| XENA-002 | 2026-07-11 | MTFCTX-C2 CTRL-02 MOMENTUM (2,736) | 537d691a | 2021-06-02T00:01Z → 2023-03-08T00:00Z (ranking →2024-03-28; gate →2024-12-11T08:19Z) | at close | at close | — | 0/2 | EXECUTING (design + QA APPROVE ×2 2026-07-11; operator execution approval 2026-07-11 — retro-read sequencing hold lifted by operator; batch emission launched) | pending |
| XENA-003 | 2026-07-11 | MTFCTX-C3 CTRL-03 REVERSION, native limit orders + m1 fills (2,736) | 537d691a | 2021-06-02T00:01Z → 2023-03-08T00:00Z (ranking →2024-03-28; gate →2024-12-11T08:19Z) | at close | at close | — | 0/2 | EXECUTING (QA APPROVE ×2 2026-07-11; operator execution approval 2026-07-11; 36-cell NativeOrders batch emission launched) | pending |
