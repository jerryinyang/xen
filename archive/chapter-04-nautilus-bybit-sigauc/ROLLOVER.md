# Chapter 04 Rollover — Nautilus, Bybit, Signed Auction

**Closed:** 2026-07-22

**Archive:** `chapter-04-nautilus-bybit-sigauc`

**Close tag:** `chapter-04-close`

## Extract

Chapter 04 was distilled into the live read-first canon before any artifact moved.

- Updated: `docs/knowledge-base/{INDEX,data-architecture,evaluation-framework,
  families-explored,lessons-and-amendments,methodology-canon,pitfalls-ledger}.md`.
- Added atomic memory for family dispositions, matched-random timing, signed-volume provenance,
  unusable `SpreadBps`, volatility-amplified direction, and the Chapter 05 entry gate.
- Carried forward: EPSOSC refuted; HTFCAP characterised but sub-cost; SIGAUC closed after three
  nulls; exact taker-side volume is valid; stored `SpreadBps` is not executable spread; matched
  random timing is the binding timing control; high volatility repeatedly amplified directional
  continuation without establishing deployable net edge.
- Signal registry, multiplicity history, test-read ledger, and holdout obligations remained live.

## Archive

All moves used `git mv`; the archive is a historical snapshot, not an active research input.

### Experiments and documentation

- 20 experiment directories: `INFR-010`–`INFR-018` excluding `INFR-019`, `INFR-020`,
  `SPDR-004`–`SPDR-009`, `VAL-008`, `XENA-EPSOSC-001/002`, and `XENA-HTFCAP-001`.
- Prior `python/experiments/INDEX.md`.
- Complete prior `docs/experiments-docs/` tree: master index, family indexes, checkpoints, and
  reflections.

### Source snapshot and live split

The archive contains all 74 tracked Chapter 04 `python/src/xen/` files.

**Restored live — 33 neutral/reusable files:**

- Root: `__init__.py`, `adjudication.py`, `bar_aggregator.py`, `estimand_validation.py`,
  `evaluation.py`.
- All seven tracked `xen/nautilus/` files.
- Eighteen `xen/xena/` files, excluding the three obsolete calibration variants below.
- `sigbar/__init__.py`, `sigbar/baselines.py`, `sigbar/data_types.py`.

`xen/__init__.py` now exports only retained modules. Fence and template paths were rebound to the
archived, hash-pinned INFR artifacts so the live neutral infrastructure remains functional.

**Archive-only — 41 files:**

- 18 legacy/root research modules: ASS, availability/capture/domain infrastructure, expectancy,
  financing, chart generators, portfolio/referee stacks, volatility regime, walk-forward and
  zigzag.
- XENA calibration variants: `calibration_p3.py`, `calibration_p3c.py`, `calibration_pbf.py`.
- All five `orderflow/` files, both `signals/` files, all four `indicators/` files.
- Nine thesis-specific signed-bar modules: absorb, acceptance, classes, fences, LTF, profile,
  sessions, spine and trap.

Ten tests tied solely to archived generators, order flow, signed-bar experiments, signals, or old
XENA calibrations moved to `tests-deprecated/`. The 23 retained test files cover the live surface.

## Renew

Chapter 05 opens as a clean, explicitly blocked pre-experiment slate.

| Change | Files | Enforcement |
|---|---|---|
| Fixed Chapter 05 route: TRAIN-only SPDR characterisation → one frozen Nautilus EXP if separately authorised; no XENA or historical TEST | `docs/references/chapter-05-governance.md`, pipeline config, active indexes | Research pipeline must read the live gate before registration/design/execution |
| Cost/data correctness before research | governance doc, `docs/experiments-docs/INDEX.md`, KB + memory | Live index remains `BLOCKED ON COST/DATA PREFLIGHT` until all eight items have evidence, focused tests and fresh-context QA |
| Fresh active surfaces | `python/experiments/INDEX.md`; empty checkpoint/family/reflection dirs | No active experiment or family exists; registration remains a separate operator decision |
| Archived infrastructure remains addressable | pipeline/developer skills, retained fence modules, dataset/architecture references, path-sensitive tests | All active references resolve to the Chapter 04 archive; retained tests exercise the rebound paths |
| Bad spread meaning corrected in the data reference | `docs/references/dataset-reference.md` | Field is labelled unusable and cannot be a T1 cost source; access-path quarantine remains a blocking preflight item |

The §7 cost/data implementation was not performed during rollover. No cost function, signed-bar
access path, funding logic, pin-verification logic, family card, research design, outcome, TEST row,
or holdout row was created or read.

## Verification

- `git diff --check`: pass.
- Live/archive source counts: 33 / 74 tracked files; approved archive-only split: 41.
- Archive inventory: 20 experiment directories, complete experiment-docs snapshot, 10 deprecated
  tests.
- Active slate: zero experiment directories; fresh indexes present; checkpoint directory empty.
- Retained suite: `181 passed, 4 skipped` (`pytest python/tests`, Python 3.13.1).
- Rollover verifier: recorded after the close commit/tag; expected command:
  `python3 .agents/skills/chapter-rollover/scripts/verify_rollover.py --root . --chapter 04`.
- Sampled history check: `git log --follow` on a moved file is performed after commit.
