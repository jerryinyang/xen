# INFR-010 Phase B — Status

**Status:** Phase B VERIFY PASS (2026-07-14)  
**Pin:** `nautilus_trader==1.230.0` @ macOS-26.5.2-arm64 / CPython 3.13.1

## Completed (§6 Phase B)

| Step | Result |
|------|--------|
| 1. uv pin + platform record | PASS — `python/pyproject.toml`, `uv.lock`, `artifacts/nautilus_pin.json` (also copied to INFR-011/artifacts/) |
| 2. Instrument-ID convention | PASS — `BTCUSDT` → `BTCUSDT-LINEAR.BYBIT` (`xen.nautilus.instrument_ids`) |
| 3a. MA-cross smoke (BacktestNode + engine) | PASS — 500 iters, 38 fills, 19 positions |
| 3b. L2_MBP smoke | PASS — 104 fills, book bid/ask 0.5000/0.5001 |
| 4. Determinism 3× | PASS — event_log sha256 `e1baebe5…` ×3 byte-identical |
| 5. Emission contract v1 + adjudication shim | PASS — reconcile_ok on smoke emission |

## Artifacts

- `artifacts/nautilus_pin.json`
- `code/instrument_id_convention.md`
- `code/emission_contract_v1.md`
- `results/{nautilus_pin,smoke_bar,smoke_l2,determinism,phase_b_verify}.json`
- Sample emissions: `data/nautilus_runs/INFR-010-smoke-{bar,l2}-1.230.0/`
- Package: `python/src/xen/nautilus/`

## Stop

At verify block. Phase C (governance rebind) / D (VAL) / E (MBP skeleton) not started.
INFR-011 catalog ingest unblocked on pin.
