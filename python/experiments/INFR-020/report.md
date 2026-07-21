# INFR-020 — Report: Multi-Timeframe Signed-Bar Apparatus

**Item:** INFR-020 · **Completed:** 2026-07-22 · **Family:** CF-SIGAUC-001 apparatus ·
**Checkpoint:** 015 §D6 · **Band:** DESIGN only · **TEST/holdout:** never read ·
**Counted reads / slots:** 0 / 0

## Outcome

**COMPLETE — Run-10 pins accepted by the operator (2026-07-22).**

Operator verdict: **“Freeze and commit.”** The accepted manifest is
`results/pins.json`, sha256
`5f170b717e350fb7c0cf1647cd1b78fb88a1fa212ed50dce83ec1049af44f6c5`.
This freezes apparatus inputs for SPDR-009; it is not evidence that S9 has an edge.

## Purpose and scope

Checkpoint-015 D6 widened SPDR-009 from 1d/1m to four HTF/LTF pairs. INFR-020 supplies the
shared, outcome-free machinery required to compare them:

- seasonal baselines for 5m, 15m, and 1h;
- class thresholds for all 194 symbols at 1m and all three coarse timeframes;
- 1h/4h operational sessions and wall-clock initial balances;
- causal 1m structural levels and one shared candidate/session/availability contract;
- count-only contact-zone censuses and measured coverage.

No return, excursion, P&L, hypothesis contrast, TEST row, or holdout row was produced.

## Frozen deliverables

| Artifact | SHA-256 |
|---|---|
| `reproduction_battery.json` | `c29bf4fece02044a231ce96d8e805dba5f78191dde1040b5899365efb2a77092` |
| `gap_excision_report.json` | `c1fe4aaf012ed874787e01db9c2c04867e1732a1a697093166bb64c7a8a88ae0` |
| `seasonal_baselines_mtf.parquet` | `86c81937cbee23f76a62bd4051394f59da3deb2230e7dd958fc573cee38a12c1` |
| `class_thresholds_mtf.json` | `745fb435eeb9e70fec88d55a32e6dfce38b4c02619824f9cff4d51ca3dcb3ae7` |
| `sessions_mtf.json` | `c55cd8806bba048f90e48795fdcab021738d9984a1602ca14f164a0f05b262df` |
| `class_thresholds_1m.json` | `dee853ad96f11754f410aa8c0a7632b0a782029dee0b770b500a74a9f959e9fc` |
| `zone_scale_census.json` | `f64e0d22355f8c5f3c5acafff598ae43fa0e84cfac9acc6f9e88fbd458487f1e` |
| `zone_scale_census_d1_ibwidth.json` | `76c3d4b58c00361d081de9225e226db2fe2aa86a56f17c18ec23e0e046705f0c` |
| `coverage_report.json` | `68dac757a4c96f0989da902805e11265e8108f7555f3d02df6a66f2dafc3a424` |

Predecessor pins remained unchanged: baseline `1b7244c8…`, column contract `e3b9fd9b…`,
and catalog fence `35d3375e…`.

## Final verification

| Check | Result |
|---|---|
| Clean execution | Full W1→W5 rebuild; no `--from-w5`; terminal `ok=true`, 194 symbols |
| Regression suite | 263 passed, 4 skipped; focused Run-10 suite 49 passed, 1 skipped |
| Reproduction battery | Full mode, all checks pass, 194 symbols, including D4 provenance A11 |
| Golden traces | SPDR-007 and SPDR-008 pass |
| Pin integrity | All nine hashes independently recomputed and matched |
| Census accounting | 776 primary cells + 194 D1 sensitivity cells; every identity holds |
| Outcome/accounting ban | No outcome schema or local accounting path found |
| Data fence | No artifact data timestamp on/after 2023-03-01 except generation metadata |

Run 10 independently rebuilt D4 and D3 examples from raw 1m bars. D4 totals reconcile to
640 candidates, 43 anchor-straddling, 66 IB-self-made, 43 prior-self-made, 634 measured,
and 6 no-level. Missing/null formation provenance raises; tied extrema use their earliest
edge-setting minute.

Measured median COMPLETE-window retention is 0.38505 / 0.20110 / 0.08815 at 5m/15m/1h.
At the 0.50 floor, SPDR-009 receives 72 / 47 / 31 usable coarse-pair symbols; activity
conditioning remains binding on every coarse-pair interpretation.

## QA history and residual risk

QA Runs 1–9 found and drove repairs to grid sizing, incomplete-window handling, pin coverage,
candidate identity, shared availability, census accounting, and self-made level exclusion.
Fresh-context **Run 10 APPROVE** found no open issue. The principal remaining limitation is
scientific, not apparatus integrity: coarse pairs describe continuously traded windows and an
uneven cross-section.

## Registry disposition

**Not applicable — infrastructure apparatus only.** No candidate was screened, no family status
changed, no slot was consumed, and no counted TEST read occurred. CF-SIGAUC-001 remains REGISTERED.

## Handoff

SPDR-009 may now implement against the exact hashes above. Its next gates are developer
implementation, fresh-context design-to-code QA, and explicit operator execution approval.

## Artifacts

| Artifact | Path |
|---|---|
| Design | [design.md](design.md) |
| QA record | [qa-review.md](qa-review.md) |
| Implementation | [code/](code/) |
| Freeze manifest and outputs | [results/](results/) |
| Run-9/10 fix map | [code/FIXES-QA6.md](code/FIXES-QA6.md) |
