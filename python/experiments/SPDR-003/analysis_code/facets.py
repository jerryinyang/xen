"""SPDR-003 stage-5 analyst re-derivation. Fresh-context, blind of SPDR-001/002 findings.

Re-derives the per-trade forward-return series from the causal primitives (build_domain_ctx,
build_fill_table) and computes Facet A (base reversion own-failure per stratum) and Facet B (HTF
own conditional effect per stratum), plus subordinate lift / Control-C phase-shift / dose-response.
No local P&L accounting (L-18): availability/return stats only. Per-stratum, no pooled verdict.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import polars as pl

EXP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EXP / "screen_code"))
sys.path.insert(0, str(EXP.parent / "SPDR-001" / "screen_code"))
import spdr001_screen as S1
import spdr003_screen as S3
from xen.evaluation import block_bootstrap_ci, trimmed_mean

RES = EXP / "results"; RES.mkdir(exist_ok=True)
N_BOOT = 4000
N_SEEDS_CI = 5
BLOCK = 10
RNG_BATTERY = 25


def bb(x, block=BLOCK):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if x.size < 2:
        return dict(stat=float(x.mean()) if x.size else np.nan, ci=[np.nan, np.nan],
                    lo_seed=[np.nan, np.nan])
    blk = int(min(block, max(1, x.size - 1)))
    r = block_bootstrap_ci(x, np.mean, block=blk, n_boot=N_BOOT, n_seeds=N_SEEDS_CI)
    return dict(stat=float(r["stat"]), ci=[float(r["ci"][0]), float(r["ci"][1])],
                lo_seed=[float(r["ci_low_seed_range"][0]), float(r["ci_low_seed_range"][1])])


def diff_bb(a, b, block=BLOCK, seed=0):
    """Two-sample circular-block bootstrap CI for mean(a)-mean(b)."""
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    b = np.asarray(b, float); b = b[np.isfinite(b)]
    if a.size < 2 or b.size < 2:
        d = (a.mean() if a.size else np.nan) - (b.mean() if b.size else np.nan)
        return float(d), [np.nan, np.nan]
    ba = int(min(block, a.size - 1)); bb_ = int(min(block, b.size - 1))
    diffs = []
    for s in range(N_SEEDS_CI):
        rng = np.random.default_rng(1000 + seed * 13 + s)
        na = int(np.ceil(a.size / ba)); nb = int(np.ceil(b.size / bb_))
        for _ in range(N_BOOT // N_SEEDS_CI):
            sa = rng.integers(0, a.size, na)
            ra = np.concatenate([np.take(a, np.arange(st, st + ba), mode="wrap") for st in sa])[:a.size]
            sb = rng.integers(0, b.size, nb)
            rb = np.concatenate([np.take(b, np.arange(st, st + bb_), mode="wrap") for st in sb])[:b.size]
            diffs.append(ra.mean() - rb.mean())
    diffs = np.array(diffs)
    return float(a.mean() - b.mean()), [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]


def none_entries(ctx, fside, hold):
    n = ctx.n
    elig = ctx.valid & (fside != 0) & (np.arange(n) + hold < n)
    idx = np.nonzero(elig)[0]
    if idx.size == 0:
        return np.array([], dtype=np.int64)
    return S1.greedy_entries(idx, hold)


def fwd_all(ctx, fprice, fside, ent, hold, atr_fixed):
    side = fside[ent].astype(float)
    exit_ = ctx.ltf_open[ent + hold]
    fill = fprice[ent]
    move = side * (exit_ - fill)
    r_atr = move / ctx.ltf_atr_prev[ent]
    r_bps = move / fill * 1e4
    r_fix = move / atr_fixed
    ok = np.isfinite(r_atr) & np.isfinite(r_bps)
    return ent[ok], r_atr[ok], r_bps[ok], r_fix[ok], side[ok]


def facetA_stats(r_atr, r_bps):
    n = r_atr.size
    mean = float(r_atr.mean()); med = float(np.median(r_atr)); std = float(r_atr.std())
    skew = float(((r_atr - mean) ** 3).mean() / (std ** 3)) if std > 0 else np.nan
    hit = float((r_atr > 0).mean())
    tail_pos = float((r_atr > 2).mean()); tail_neg = float((r_atr < -2).mean())
    # drop worst 5% (most negative)
    k = max(1, int(np.ceil(0.05 * n)))
    order = np.argsort(r_atr)
    keep = order[k:]
    mean_excl_w5 = float(r_atr[keep].mean())
    # worst-decile contribution to the SUM
    kd = max(1, int(np.ceil(0.10 * n)))
    worst_sum = float(r_atr[order[:kd]].sum()); total = float(r_atr.sum())
    wd_contrib = float(worst_sum / total) if total != 0 else np.nan
    return dict(mean_atr=mean, median_atr=med, std_atr=std, skew=skew, hitrate=hit,
                tail_pos_2atr=tail_pos, tail_neg_2atr=tail_neg, mean_excl_worst5=mean_excl_w5,
                worst_decile_sum_frac=wd_contrib, mean_bps=float(r_bps.mean()),
                median_bps=float(np.median(r_bps)))


def name_failure(a, ci_atr):
    modes = []
    ci_excl0 = np.isfinite(ci_atr[0]) and (ci_atr[0] > 0 or ci_atr[1] < 0)
    if abs(a["hitrate"] - 0.5) < 0.02 and not ci_excl0:
        modes.append("a:no-directional-edge")
    if a["median_atr"] > 0 and a["mean_atr"] < a["median_atr"] - 0.05:
        modes.append("b:tail-eaten(median>mean)")
    if a["median_atr"] > 0 and a["mean_atr"] < 0:
        modes.append("b:tail-flips-sign")
    if abs(a["mean_excl_worst5"] - a["mean_atr"]) > abs(a["mean_atr"]) and abs(a["mean_atr"]) > 1e-6:
        modes.append("d:loss-concentration")
    return ";".join(modes) if modes else "none-dominant"


def run():
    facetA, facetB, cond_cells, subord = [], [], [], []
    for sym in S1.INSTRUMENTS:
        train = S1.load_train_1m(sym)
        for name, htf_min, ltf_min, ratio in S1.DOMAIN_PAIRS:
            ctx = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=0)
            ctx_sh = S1.build_domain_ctx(name, htf_min, ltf_min, train,
                                         shift_htf=S1.PHASE_SHIFT_HTF_BARS)
            fside, fprice = S3.build_fill_table(ctx, train)
            atr_fixed = float(np.nanmedian(ctx.ltf_atr_prev[ctx.valid]))
            fill_rate = float(np.mean(fside != 0))
            n_signal = int(np.sum(fside != 0))
            holds = [ratio * m for m in S1.HOLD_MULTS]
            for m, hold in zip(S1.HOLD_MULTS, holds):
                ent = none_entries(ctx, fside, hold)
                if ent.size == 0:
                    continue
                ent, r_atr, r_bps, r_fix, side = fwd_all(ctx, fprice, fside, ent, hold, atr_fixed)
                nfill = r_atr.size
                a = facetA_stats(r_atr, r_bps)
                cib = bb(r_atr)
                cibps = bb(r_bps)
                # Control B: random-timing matched battery (percentile of none-arm mean)
                pool = np.nonzero(ctx.valid & (fside != 0) & (np.arange(ctx.n) + hold < ctx.n))[0]
                bat = np.empty(RNG_BATTERY)
                for k in range(RNG_BATTERY):
                    rng = np.random.default_rng(20000 + k)
                    take = min(nfill, pool.size)
                    e2 = np.sort(rng.choice(pool, take, replace=False))
                    sd = rng.choice(np.array([-1, 1], np.int8), take).astype(float)
                    mv = sd * (ctx.ltf_open[e2 + hold] - fprice[e2]) / ctx.ltf_atr_prev[e2]
                    mv = mv[np.isfinite(mv)]
                    bat[k] = mv.mean() if mv.size else np.nan
                bat = bat[np.isfinite(bat)]
                pct = float((bat < a["mean_atr"]).mean() * 100) if bat.size else np.nan
                facetA.append(dict(instrument=sym, domain=name, hold_mult=m, hold_bars=hold,
                    n_fill=nfill, fill_rate=fill_rate, n_signal=n_signal,
                    mean_atr=a["mean_atr"], ci_atr_lo=cib["ci"][0], ci_atr_hi=cib["ci"][1],
                    ci_atr_lo_seed_lo=cib["lo_seed"][0], ci_atr_lo_seed_hi=cib["lo_seed"][1],
                    median_atr=a["median_atr"], mean_bps=a["mean_bps"], median_bps=a["median_bps"],
                    ci_bps_lo=cibps["ci"][0], ci_bps_hi=cibps["ci"][1],
                    hitrate=a["hitrate"], std_atr=a["std_atr"], skew=a["skew"],
                    tail_pos_2atr=a["tail_pos_2atr"], tail_neg_2atr=a["tail_neg_2atr"],
                    mean_excl_worst5=a["mean_excl_worst5"], worst_decile_sum_frac=a["worst_decile_sum_frac"],
                    rand_battery_mean=float(bat.mean()) if bat.size else np.nan,
                    none_pctile_in_battery=pct,
                    failure_mode=name_failure(a, cib["ci"])))

                # ------- Facet B: HTF state as conditioning variable (same none-arm entries) -----
                hd = ctx.htf_dir[ent]; adxb = ctx.adx_bucket[ent]; atrr = ctx.atr_reg[ent]
                def grp(mask, arr):
                    v = arr[mask]; return v
                # DI spread
                mp = hd == 1; mm_ = hd == -1
                di_spread, di_ci = diff_bb(r_atr[mp], r_atr[mm_], seed=1)
                # conditional means per bucket for ADX and ATR
                adx_means = {b: float(r_atr[adxb == b].mean()) if (adxb == b).sum() else np.nan
                             for b in (0, 1, 2)}
                atr_means = {b: float(r_atr[atrr == b].mean()) if (atrr == b).sum() else np.nan
                             for b in (0, 1, 2)}
                adx_vals = [v for v in adx_means.values() if np.isfinite(v)]
                atr_vals = [v for v in atr_means.values() if np.isfinite(v)]
                adx_range = (max(adx_vals) - min(adx_vals)) if len(adx_vals) >= 2 else np.nan
                atr_range = (max(atr_vals) - min(atr_vals)) if len(atr_vals) >= 2 else np.nan
                # dispersion modulation across ATR regime (normaliser guard: atr / bps / fixed)
                def disp_ratio(vals, lab):
                    stds = [vals[lab == b].std() for b in (0, 1, 2) if (lab == b).sum() > 5]
                    stds = [s for s in stds if np.isfinite(s) and s > 0]
                    return (max(stds) / min(stds)) if len(stds) >= 2 else np.nan
                # sign-prediction excess per DI state
                hit_p = float((r_atr[mp] > 0).mean()) if mp.sum() else np.nan
                hit_m = float((r_atr[mm_] > 0).mean()) if mm_.sum() else np.nan
                facetB.append(dict(instrument=sym, domain=name, hold_mult=m, hold_bars=hold,
                    n_plus=int(mp.sum()), n_minus=int(mm_.sum()),
                    di_spread_atr=di_spread, di_spread_ci_lo=di_ci[0], di_spread_ci_hi=di_ci[1],
                    E_plus=float(r_atr[mp].mean()) if mp.sum() else np.nan,
                    E_minus=float(r_atr[mm_].mean()) if mm_.sum() else np.nan,
                    adx_cond_range_atr=adx_range, atr_cond_range_atr=atr_range,
                    adx0=adx_means[0], adx1=adx_means[1], adx2=adx_means[2],
                    atrL=atr_means[0], atrM=atr_means[1], atrH=atr_means[2],
                    disp_ratio_atr=disp_ratio(r_atr, atrr),
                    disp_ratio_bps=disp_ratio(r_bps, atrr),
                    disp_ratio_fixed=disp_ratio(r_fix, atrr),
                    hit_excess_plus=hit_p - 0.5 if np.isfinite(hit_p) else np.nan,
                    hit_excess_minus=hit_m - 0.5 if np.isfinite(hit_m) else np.nan))

                # granular conditional cells (magnitude table)
                for lab, val, arr in [("dir+1", 1, hd), ("dir-1", -1, hd),
                                      ("adx<25", 0, adxb), ("adx25-75", 1, adxb), ("adx>=75", 2, adxb),
                                      ("atrL", 0, atrr), ("atrM", 1, atrr), ("atrH", 2, atrr)]:
                    mk = arr == val
                    if mk.sum() < 2:
                        cond_cells.append(dict(instrument=sym, domain=name, hold_bars=hold,
                            state=lab, n=int(mk.sum()), mean_atr=np.nan, ci_lo=np.nan, ci_hi=np.nan,
                            hitrate=np.nan, std_atr=np.nan)); continue
                    c = bb(r_atr[mk])
                    cond_cells.append(dict(instrument=sym, domain=name, hold_bars=hold, state=lab,
                        n=int(mk.sum()), mean_atr=c["stat"], ci_lo=c["ci"][0], ci_hi=c["ci"][1],
                        hitrate=float((r_atr[mk] > 0).mean()), std_atr=float(r_atr[mk].std())))

                # ------- Subordinate: DI-confirm lift + Control C phase-shift collapse -----
                di_elig = ctx.valid & (fside != 0) & (fside == ctx.htf_dir) & (np.arange(ctx.n) + hold < ctx.n)
                di_idx = np.nonzero(di_elig)[0]
                if di_idx.size:
                    de = S1.greedy_entries(di_idx, hold)
                    de, dr, _, _, _ = fwd_all(ctx, fprice, fside, de, hold, atr_fixed)
                    di_mean = float(dr.mean()); di_n = dr.size
                    lift, lift_ci = diff_bb(dr, r_atr, seed=2)
                else:
                    di_mean = np.nan; di_n = 0; lift = np.nan; lift_ci = [np.nan, np.nan]
                # phase-shift DI arm
                sh_elig = ctx_sh.valid & (fside != 0) & (fside == ctx_sh.htf_dir) & (np.arange(ctx_sh.n) + hold < ctx_sh.n)
                sh_idx = np.nonzero(sh_elig)[0]
                if sh_idx.size:
                    se = S1.greedy_entries(sh_idx, hold)
                    se, sr, _, _, _ = fwd_all(ctx_sh, fprice, fside, se, hold, atr_fixed)
                    sh_mean = float(sr.mean())
                    # phase-shifted DI conditional spread
                    hsd = ctx_sh.htf_dir[se]
                    sh_spread, _ = diff_bb(sr[hsd == 1], sr[hsd == -1], seed=3)
                else:
                    sh_mean = np.nan; sh_spread = np.nan
                collapse = float(sh_spread / di_spread) if (np.isfinite(di_spread) and di_spread != 0) else np.nan
                subord.append(dict(instrument=sym, domain=name, hold_bars=hold,
                    di_arm_mean=di_mean, di_arm_n=di_n, none_mean=a["mean_atr"],
                    lift_di_minus_none=lift, lift_ci_lo=lift_ci[0], lift_ci_hi=lift_ci[1],
                    phaseshift_di_arm_mean=sh_mean,
                    di_spread=di_spread, phaseshift_di_spread=sh_spread,
                    control_c_collapse_frac=collapse))
            del ctx, ctx_sh, fside, fprice

    for tbl, nm in [(facetA, "facetA_base_failure"), (facetB, "facetB_htf_conditional"),
                    (cond_cells, "conditional_cells_magnitude"), (subord, "subordinate_lift_controlC")]:
        df = pl.DataFrame(tbl)
        df.write_parquet(RES / f"{nm}.parquet")
        df.write_csv(RES / f"{nm}.csv")
        print(nm, df.shape)


if __name__ == "__main__":
    run()
