# Xen Experiments — Chapter 03

Per-experiment artifacts live here (`EXP-*/`, `VAL-*/`, `INFR-*/`: design.md, code, results,
report.md). Chapter 02 is archived at `archive/chapter-02-mr-volharv-htfdi/experiments/`.
Read `docs/knowledge-base/` before designing anything.

| ID | Family | Status | Verdict |
|----|--------|--------|---------|
| INFR-008 | infrastructure (XENA oracle) | COMPLETE 2026-07-12 | NEUTRAL amendment: fold-kernel k-way merge restructure + grid_increments binning rework + GIL release; bitwise re-proven (pins unchanged, rid-0 replay); 45-subset eval ~65→21 ms, grid_increments ~25→11 ms, 3× thread scaling |
| INFR-007 | infrastructure (XENA oracle) | COMPLETE 2026-07-12 | NEUTRAL amendment: oracle event fold → Rust `xena_fold`, bit-identical (500-case pinned corpus + rid-0 replay), ~15×/eval; default backend now `rust`; 1-ULP cross-platform libm caveat → one universe = one platform |
