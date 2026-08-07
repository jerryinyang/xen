# Quarantined pre-AMENDMENT-7 exploratory scripts

These scripts predate the R1–R5 floor fix. They recompute `2.8/√n` floors and/or emit
`WASH` / `UNPOWERED` / `NOT_RESOLVABLE` labels. They are **not** on the emission path
(`analyse.py` does not import them) and must not be used to write `analysis.md`.

Do not restore them to `analysis_code/` without rewriting to the AMENDMENT-7 contract.
