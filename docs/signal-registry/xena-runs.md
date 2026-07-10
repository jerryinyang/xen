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

| Run | Registered | Universe (N cands) | Registry sha256 (8) | Search band | Eval count | Distinct subsets | Certified | Gate slots spent | Outcome | Operator sign |
|---|---|---|---|---|---|---|---|---|---|---|
| _(none yet — first live universe pending)_ | | | | | | | | | | |
