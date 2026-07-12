"""One-time generator for the INFR-007 pinned parity corpus.

Runs every corpus case on the PYTHON oracle backend (the authority) and pins the sha256
digests to `tests/data/xena_fold_parity_hashes.json`. Regenerate ONLY after an
operator-approved change to the oracle semantics; the whole point of the pin is that a
Rust/toolchain upgrade must re-prove itself against digests it cannot regenerate.

Usage: .venv/bin/python tests/gen_xena_fold_parity_corpus.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_xena_fold_parity import (ROOT, HASHES, _load_xena001_streams,  # noqa: E402
                                   corpus_cases, result_digest)

from xen.xena.oracle import OracleConfig, evaluate  # noqa: E402


def main() -> None:
    t0 = time.time()
    streams = _load_xena001_streams()
    ids = sorted(s.candidate_id for s in streams)
    cases = corpus_cases(ids, ROOT / "python" / "experiments" / "XENA-001" / "results")
    print(f"{len(streams)} streams, {len(cases)} corpus cases", flush=True)
    out = []
    for i, case in enumerate(cases):
        cfg = OracleConfig(charge_costs=case["charge_costs"], backend="python")
        res = evaluate(set(case["subset"]), streams, cfg, segment=tuple(case["segment"]))
        out.append({"case": case["case"], "digest": result_digest(res)})
        if i % 25 == 0:
            print(f"  {i}/{len(cases)} ({time.time()-t0:.0f}s)", flush=True)
    HASHES.parent.mkdir(parents=True, exist_ok=True)
    HASHES.write_text(json.dumps(
        {"generated": "python-backend authority, INFR-007",
         "n_cases": len(out), "cases": out}, indent=1))
    print(f"pinned {len(out)} digests to {HASHES} in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
