# INFR-001 Amendment R1 — Former/Latter Execution-Model Reconciliation

**Date:** 2026-06-06
**Type:** Design reconciliation (infrastructure). Changes no experiment verdict and does not touch the frozen referee suite.
**Affects:** `design.md` (now revised to v2), and the in-flight implementation (StrategyHost/, `python/src/xen/signals/`, VAL-002).

---

## Why this amendment exists

The first finalized `design.md` (the version committed when implementation began) was internally contradictory: it described a "cTrader strategy host" yet also mandated a **fixed-bar run over the collected Parquet (no live feed)** and named **Python the reference oracle** that C# is byte-validated against. That is the **"former"** model — a local C# reimplementation proven byte-for-byte against a parallel Python generation engine.

The operator's intent, confirmed in discussion and now encoded in `design.md` §0, is the **"latter"** model: strategies run as **real cAlgo robots inside cTrader's engine**, on cTrader's feed, emitting datasets during the run — exactly as `Xen.cs` generates the timebars. Python is **validation/ingestion only**; only signal-generation code is ported to C#. This matches `signal-registry/README.md` concern #4 verbatim.

Because the implementer worked from the contradictory committed design (without the discussion context), the implementation faithfully built the **former**. This amendment pins the boundary so the redirect is unambiguous.

---

## The boundary (binding)

| Dimension | FORMER (superseded) | LATTER (binding, design.md v2) |
| --- | --- | --- |
| Where strategies run | C# executed locally over collected Parquet | **Inside cTrader's algo engine** (Automate/backtester) on cTrader's feed |
| Role of the C# port | parallel reimplementation, byte-validated vs Python | **signal-generation toolkit** cAlgos call natively in-engine |
| Role of Python | parallel **generation oracle** | **validation + ingestion only** — never generates strategy signals |
| Parity standard | exact numeric (e.g. 1e-8) over identical local data | **one-time transcription test** (fixtures) **+ behavioral** reproduction via an actual cTrader run |
| Price source for evaluation | re-derived from local Parquet | **the real OHLC the cAlgo emits from its own run** |
| Reproducibility standard | byte-identical | **behavioral** (suite reproduces the known verdict); cTrader runs are not byte-deterministic |

The superseded decision token `D-oracle` is withdrawn; it is replaced by `D-exec`, `D-parity`, and `D-cost` in `design.md` v2.

---

## Implications for the in-flight implementation

The review (this session) found the implementation correct in its parts but built to the former. Per the keep/redirect/drop split:

- **Keep:** the five C# generator ports (transcription-correct), `HoldoutFence`, the causal MA logic, the cAlgo `OnBar` strategy-host skeleton, and the suite-reproduction methodology.
- **Redirect:** emit the real OHLC the strategy executed on; de-leak model-specific columns (`FastValue`/`SlowValue`) from the generic position record; make the cTrader `OnBar` path the validated path (transcription on fixtures + behavioral via a real cTrader run); reconcile `architecture.md`/`dataset-reference.md` to v2.
- **Drop/demote:** `python/src/xen/signals/` as a *generation* engine → replace with a thin **ingestion harness** (read emitted `positions.parquet` → route to the frozen suite); demote the console byte-parity run from a VAL-002 *closure* path to a developer smoke test.

VAL-002 stays open (IN DEVELOPMENT) until a real cTrader run supplies the behavioral closure; the console-only parity does not close it.

---

*R1 records that the implementation is a faithful build of a superseded design, not a defect, and fixes the source of truth (design.md v2) so the redirect proceeds from a non-contradictory baseline.*
