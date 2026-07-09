"""SPDR-001 follow-up: resolve analysis.md §9 threads 1-3. Reuses screen_code causal primitives.
No causality rebuilt; TRAIN-only; block-bootstrap CIs; magnitudes only (no disposition)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP / "screen_code"))
sys.path.insert(0, str(EXP / "analysis_code"))
import spdr001_screen as S            # noqa: E402
from emit_rich import _fast_block_ci_mean  # noqa: E402  (validated vs xen.evaluation)
from xen.vol_regime import wilder_atr       # noqa: E402
RES = EXP / "results"


def block_idx(n, block=5, n_boot=1500, seed=0):
    eff = max(1, min(block, n - 1)); nblk = int(np.ceil(n / eff))
    rng = np.random.default_rng(seed)
    st = rng.integers(0, n, size=(n_boot, nblk))
    return (st[:, :, None] + np.arange(eff)[None, None, :]).reshape(n_boot, -1)[:, :n] % n


def ci_fn(fn, n, seed=0):
    """Block-bootstrap CI for an arbitrary scalar fn(idx) over the time-ordered sample."""
    idx = block_idx(n, seed=seed)
    stats = np.array([fn(idx[b]) for b in range(idx.shape[0])])
    stats = stats[np.isfinite(stats)]
    return float(np.quantile(stats, .025)), float(np.quantile(stats, .975))


def ltf_dir_series(train_1m, ltf_min):
    """Causal LTF-own directional sign: +DI>-DI on the ENTRY-timeframe bars themselves, taken at
    the last CLOSED LTF bar (index t-1 for entry bar t). Pure LTF momentum, NO higher timeframe."""
    ltf = S._agg(train_1m, ltf_min).sort("CloseTime")
    h = ltf["High"].to_numpy().astype(float); l = ltf["Low"].to_numpy().astype(float)
    c = ltf["Close"].to_numpy().astype(float)
    _, pdi, mdi = S.wilder_adx_di(h, l, c, S.ADX_PERIOD)
    d = np.where(pdi > mdi, 1, -1).astype(float)
    d[~np.isfinite(pdi) | ~np.isfinite(mdi)] = 0
    prev = np.concatenate([[0.0], d[:-1]])   # last closed LTF bar (t-1)
    return prev


# --------------------------------------------------------------------------- #
# THREAD 1 — HTF increment vs plain LTF autocorrelation
# --------------------------------------------------------------------------- #
def thread1():
    cells = [  # the CI-clearing named strata (plain di) + one strongest gated interaction cell
        ("USTEC", "1h/5min"), ("BTCUSD", "1h/5min"), ("EURUSD", "1d/1h"),
        ("EURUSD", "1h/5min"), ("XAUUSD", "1h/5min"),
    ]
    rows = []
    for sym, dom in cells:
        train = S.load_train_1m(sym)
        name, htf_min, ltf_min, ratio = next(d for d in S.DOMAIN_PAIRS if d[0] == dom)
        ctx = S.build_domain_ctx(name, htf_min, ltf_min, train)
        ltfd = ltf_dir_series(train, ltf_min)
        n = ctx.n; idx = np.arange(n)
        for hmult in S.HOLD_MULTS:
            hold = ratio * hmult
            inb = idx + hold < n; ii = idx[inb]
            move = np.full(n, np.nan)
            move[ii] = (ctx.ltf_open[ii + hold] - ctx.ltf_open[ii]) / ctx.ltf_atr_prev[ii]
            valid = ctx.valid & inb & np.isfinite(move) & (ltfd != 0)
            sel = np.nonzero(valid)[0]
            if sel.size < 200:
                continue
            m = move[sel]; hd = ctx.htf_dir[sel].astype(float); ld = ltfd[sel]
            # edges
            e_htf = float((hd * m).mean()); e_ltf = float((ld * m).mean())
            rho = float((hd * ld).mean())                     # corr of the two ±1 signs (mean~0)
            mux, muz = hd.mean(), ld.mean()
            # partial (two-factor, demeaned) OLS coefficient on htf_dir controlling ltf_dir
            def alpha(ix):
                x = hd[ix] - hd[ix].mean(); z = ld[ix] - ld[ix].mean(); y = m[ix]
                sxx = (x * x).mean(); szz = (z * z).mean(); sxz = (x * z).mean()
                sxy = (x * y).mean(); szy = (z * y).mean()
                det = sxx * szz - sxz * sxz
                return (szz * sxy - sxz * szy) / det if abs(det) > 1e-12 else np.nan
            a = alpha(np.arange(sel.size))
            a_lo, a_hi = ci_fn(alpha, sel.size)
            # conflict subset: where HTF disagrees with LTF, does HTF still predict m?
            conf = hd != ld
            if conf.sum() >= 50:
                mc = m[conf]; hdc = hd[conf]
                e_conf, c_lo, c_hi = _fast_block_ci_mean(hdc * mc)
            else:
                e_conf = c_lo = c_hi = np.nan
            rows.append(dict(instrument=sym, domain=dom, hold_bars=hold, n=int(sel.size),
                edge_htf=e_htf, edge_ltf=e_ltf, sign_corr=rho,
                htf_partial=a, htf_partial_lo=a_lo, htf_partial_hi=a_hi,
                htf_share=(a / e_htf) if abs(e_htf) > 1e-9 else np.nan,
                n_conflict=int(conf.sum()), edge_htf_on_conflict=e_conf,
                conflict_lo=c_lo, conflict_hi=c_hi))
        print("  T1 done", sym, dom, flush=True)
    pl.DataFrame(rows).write_parquet(RES / "fu_thread1.parquet")


# --------------------------------------------------------------------------- #
# THREAD 2 — dispersion: normaliser mechanics vs forward-vol prediction
# --------------------------------------------------------------------------- #
def thread2():
    rows = []
    from numpy.lib.stride_tricks import sliding_window_view
    for sym in S.INSTRUMENTS:
        train = S.load_train_1m(sym)
        name, htf_min, ltf_min, ratio = next(d for d in S.DOMAIN_PAIRS if d[0] == "1h/5min")
        ctx = S.build_domain_ctx(name, htf_min, ltf_min, train)
        # long-window (500-bar) trailing LTF ATR, lagged -> slow normaliser not synced to regime
        ltf = S._agg(train, ltf_min).sort("CloseTime")
        h = ltf["High"].to_numpy().astype(float); l = ltf["Low"].to_numpy().astype(float)
        c = ltf["Close"].to_numpy().astype(float)
        atr14 = wilder_atr(h, l, c, 14)
        win = 500
        atr_slow = np.full(atr14.shape[0], np.nan)
        if atr14.shape[0] >= win:
            sw = sliding_window_view(atr14, win)
            atr_slow[win - 1:] = np.nanmean(sw, axis=1)
        atr_slow_prev = np.concatenate([[np.nan], atr_slow[:-1]])
        n = ctx.n; idx = np.arange(n)
        hold = ratio * 2  # H=24
        inb = idx + hold < n; ii = idx[inb]
        raw = np.full(n, np.nan); norm14 = np.full(n, np.nan); normslow = np.full(n, np.nan)
        mv = ctx.ltf_open[ii + hold] - ctx.ltf_open[ii]
        raw[ii] = mv / ctx.ltf_open[ii] * 1e4                       # bps
        norm14[ii] = mv / ctx.ltf_atr_prev[ii]                      # existing ATR14[t-1]
        with np.errstate(invalid="ignore"):
            normslow[ii] = mv / atr_slow_prev[ii]                   # slow ATR500
        base = ctx.valid & inb & np.isfinite(raw) & np.isfinite(normslow)
        # regime std ratio vs overall baseline, each metric
        for metric, arr in (("raw_bps", raw), ("atr14", norm14), ("atr500", normslow)):
            b_std = float(np.nanstd(arr[base]))
            from xen.vol_regime import REGIME_LOW, REGIME_MED, REGIME_HIGH
            for reg, rn in ((REGIME_LOW, "low"), (REGIME_MED, "med"), (REGIME_HIGH, "high")):
                msk = base & (ctx.atr_reg == reg)
                if msk.sum() < 100:
                    continue
                rows.append(dict(instrument=sym, metric=metric, regime=rn,
                    n=int(msk.sum()), std=float(np.nanstd(arr[msk])),
                    base_std=b_std, std_ratio=float(np.nanstd(arr[msk]) / b_std)))
        print("  T2 done", sym, flush=True)
    pl.DataFrame(rows).write_parquet(RES / "fu_thread2.parquet")


# --------------------------------------------------------------------------- #
# THREAD 3 — 4h/1h dead-zone diagnostics (structural vs artifact)
# --------------------------------------------------------------------------- #
def thread3():
    rows = []; diag = []
    for sym in S.INSTRUMENTS:
        train = S.load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in S.DOMAIN_PAIRS:
            htf = S._agg(train, htf_min).sort("CloseTime")
            ltf = S._agg(train, ltf_min).sort("CloseTime")
            ctx = S.build_domain_ctx(name, htf_min, ltf_min, train)
            # htf_dir at HTF granularity: flip rate between consecutive HTF bars
            hh = htf["High"].to_numpy().astype(float); hl = htf["Low"].to_numpy().astype(float)
            hc = htf["Close"].to_numpy().astype(float)
            _, pdi, mdi = S.wilder_adx_di(hh, hl, hc, S.ADX_PERIOD)
            hdir = np.where(pdi > mdi, 1, -1).astype(float)
            hdir[~np.isfinite(pdi) | ~np.isfinite(mdi)] = 0
            fin = hdir != 0
            flip = float(np.mean(hdir[fin][1:] != hdir[fin][:-1])) if fin.sum() > 2 else np.nan
            cov = float(ctx.valid.mean())    # fraction of LTF bars with a full valid HTF map
            diag.append(dict(instrument=sym, domain=name, n_htf_bars=int(htf.height),
                n_ltf_bars=int(ltf.height), htf_dir_flip_rate=flip,
                ltf_valid_coverage=cov, n_valid_ltf=int(ctx.valid.sum())))
        print("  T3 diag done", sym, flush=True)
    pl.DataFrame(diag).write_parquet(RES / "fu_thread3_diag.parquet")


if __name__ == "__main__":
    thread1(); thread2(); thread3()
    print("[emit_followup] wrote fu_thread1 / fu_thread2 / fu_thread3_diag")
