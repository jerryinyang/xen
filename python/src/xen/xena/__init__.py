"""XENA portfolio-construction framework (INFR-006 base; INFR-009 adjudication redesign).

Subset selection over a universe of engine-emitted candidate strategies via a
shared-capital portfolio oracle, LAHC search (intensive ``g_gross`` score), and an
evidence package (not absolute-F certification).

* INFR-006 design: `python/experiments/INFR-006/design.md` (frozen v3 — **superseded**)
* INFR-009 redesign: `python/experiments/INFR-009/design.md` (P0–P2 shipped; P3+ gated)
* Spec: `docs/references/xena-lane.md` (default route **SUSPENDED** until P4 acceptance)

Modules: oracle, ingest, search, certify, final_gate, calibration, score, economics,
fill_basis, high_cadence_null.
"""
