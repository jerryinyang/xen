"""EXP-008 Amendment A1 forensic — why the Hurst-DFA<0.45 leg vetoed the MR screen.

Operator-requested post-mortem (2026-07-01): was the leg (a) applied to the wrong object, or (b) an
estimator unfit for this project's setting? This diagnostic answers **both**, analysis-only, TRAIN-only,
0 reads. It runs three probes and writes `results/hurst_forensics.json` + `plots/F_hurst_forensics.png`.

Probe B — synthetic OU of *known* half-life: DFA-H on the level vs increments at the design window.
Probe C — window-length dependence of DFA-H on a fixed OU.
Probe A — real deviation windows (S4_OU): level-H vs increment-H vs the fitted half-life.

Conclusion (see report.md / audit.md): DFA integrates its input, so DFA-on-*levels* scores the
integrated process → H≈1.0-1.4 for any OU level (H<0.45 structurally impossible — the proximate cause of
0/240). Even corrected to increments, H<0.45 fires only for extreme reversion (HL≈2) and needs windows
≥400 bars; at the empirical HL≈4-7 and W_s=200, H_incr≈0.5. DFA-Hurst measures long-range/increment
persistence, ≈neutral for moderate OU — it does not measure reversion-to-a-level; VR + half-life do.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from xen import cross_domain_mr as cdm

import sys
sys.path.insert(0, str(Path(__file__).parent))
import run_experiment as R  # noqa: E402

logger = logging.getLogger("EXP-008.hurst_forensics")

SEED = 20260701
W = cdm.W_S                     # design screen window (200 exec bars)
HALF_LIVES = (2, 5, 10, 24, 48)
WINDOWS = (100, 200, 400, 800)
REAL_SYMS = ("EURUSD", "XAUUSD", "BTCUSD")
N_SIM = 60


def ou_path(phi: float, n: int, rng: np.random.Generator) -> np.ndarray:
    """AR(1)/OU path x_t = phi x_{t-1} + eps (unit-variance innovations)."""
    x = np.zeros(n, dtype=np.float64)
    eps = rng.normal(size=n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + eps[t]
    return x


def probe_ou_object(rng: np.random.Generator) -> list[dict]:
    """Probe B — DFA-H on level vs increments of a known-half-life OU at the design window."""
    out = []
    for hl in HALF_LIVES:
        phi = 0.5 ** (1.0 / hl)
        hlv = [cdm.hurst_dfa(ou_path(phi, W, rng)) for _ in range(N_SIM)]
        hiv = [cdm.hurst_dfa(np.diff(ou_path(phi, W, rng))) for _ in range(N_SIM)]
        out.append({"half_life_bars": hl, "phi": round(phi, 4),
                    "H_level": round(float(np.nanmean(hlv)), 3),
                    "H_incr": round(float(np.nanmean(hiv)), 3)})
    return out


def probe_window(rng: np.random.Generator, hl: int = 10) -> list[dict]:
    """Probe C — window-length dependence of DFA-H (OU fixed at half-life ``hl``)."""
    phi = 0.5 ** (1.0 / hl)
    out = []
    for L in WINDOWS:
        hlv = [cdm.hurst_dfa(ou_path(phi, L, rng)) for _ in range(40)]
        hiv = [cdm.hurst_dfa(np.diff(ou_path(phi, L, rng))) for _ in range(40)]
        out.append({"window": L, "H_level": round(float(np.nanmean(hlv)), 3),
                    "H_incr": round(float(np.nanmean(hiv)), 3)})
    return out


def probe_real(rng: np.random.Generator) -> list[dict]:
    """Probe A — real S4_OU deviation windows: level-H vs increment-H vs fitted half-life."""
    out = []
    for sym in REAL_SYMS:
        t = R.load_train_1m(sym)
        ed = R.build_exec_domain(t, 60)
        anc = R.anchor_arrays(t, 240)
        asr = cdm.anchor_series("S4_OU", ed.close, ed.ct, anc, None)
        z_lag = np.concatenate([[np.nan], asr.z[:-1]])
        ext = np.flatnonzero((np.arange(ed.close.shape[0]) >= W)
                             & np.isfinite(z_lag) & (np.abs(z_lag) >= cdm.Z_STAR))[:400]
        hl_ = [cdm.hurst_dfa(asr.dev[i - W:i]) for i in ext]
        hi_ = [cdm.hurst_dfa(np.diff(asr.dev[i - W:i])) for i in ext]
        hlfit = [h for i in ext if np.isfinite(h := cdm.half_life(asr.dev[i - W:i]))]
        out.append({"symbol": sym, "n": int(ext.shape[0]),
                    "H_level_med": round(float(np.nanmedian(hl_)), 3),
                    "H_incr_med": round(float(np.nanmedian(hi_)), 3),
                    "frac_H_incr_lt_0.45": round(float(np.mean(np.asarray(hi_) < 0.45)), 3),
                    "fitted_HL_med_bars": round(float(np.median(hlfit)), 1) if hlfit else None})
    return out


def plot_forensics(ou_obj: list[dict], win: list[dict], real: list[dict], path: Path) -> None:
    """Two-panel: OU level/incr H vs half-life (with the 0.45 line) and window-length dependence."""
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    hls = [d["half_life_bars"] for d in ou_obj]
    ax[0].plot(hls, [d["H_level"] for d in ou_obj], "o-", label="H(level)")
    ax[0].plot(hls, [d["H_incr"] for d in ou_obj], "s-", label="H(increments)")
    ax[0].axhline(0.45, color="red", ls=":", label="screen threshold 0.45")
    ax[0].axhline(0.5, color="gray", ls="--", lw=0.7)
    ax[0].set_xlabel("OU half-life (bars)")
    ax[0].set_ylabel("DFA-H")
    ax[0].set_title("Probe B — known-OU DFA-H (window=200)")
    ax[0].legend()
    ws = [d["window"] for d in win]
    ax[1].plot(ws, [d["H_level"] for d in win], "o-", label="H(level)")
    ax[1].plot(ws, [d["H_incr"] for d in win], "s-", label="H(increments)")
    ax[1].axhline(0.45, color="red", ls=":")
    ax[1].axvline(200, color="green", ls="--", lw=0.7, label="design W_s=200")
    ax[1].set_xlabel("window length (bars)")
    ax[1].set_ylabel("DFA-H")
    ax[1].set_title("Probe C — window dependence (OU HL=10)")
    ax[1].legend()
    fig.suptitle("EXP-008 A1 forensic: DFA-Hurst is unfit as an OU-reversion screen on levels")
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    rng = np.random.default_rng(SEED)
    results = {
        "note": "EXP-008 Amendment A1 forensic — why Hurst-DFA<0.45 vetoed the MR screen.",
        "probe_B_ou_object": probe_ou_object(rng),
        "probe_C_window": probe_window(rng),
        "probe_A_real_S4_OU": probe_real(rng),
        "conclusion": ("WRONG-OBJECT (proximate): DFA integrates its input; on deviation LEVELS it "
                       "scores the integrated process -> H~1.0-1.4 for any OU level, so H<0.45 is "
                       "structurally impossible (the 0/240). ESTIMATOR-UNFIT (deeper): even on "
                       "increments, H<0.45 fires only for extreme reversion (HL~2) and needs "
                       "windows>=400; at the empirical HL~4-7 and W_s=200, H_incr~0.5. DFA-Hurst "
                       "measures long-range/increment persistence (neutral for moderate OU), not "
                       "reversion-to-a-level. VR + half-life measure reversion directly -> drop Hurst."),
    }
    RESULTS = R.RESULTS_DIR
    PLOTS = R.PLOTS_DIR
    RESULTS.mkdir(parents=True, exist_ok=True)
    PLOTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "hurst_forensics.json").write_text(json.dumps(results, indent=2))
    plot_forensics(results["probe_B_ou_object"], results["probe_C_window"],
                   results["probe_A_real_S4_OU"], PLOTS / "F_hurst_forensics.png")
    logger.info("Hurst forensic written: results/hurst_forensics.json + plots/F_hurst_forensics.png")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
