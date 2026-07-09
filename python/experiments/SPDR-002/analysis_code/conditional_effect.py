"""SPDR-002 reframe facets (operator 2026-07-07).
FACET A: base naive-momentum's OWN failure, per stratum (distribution, decay, loss concentration,
         random-timing percentile) — so the object HTF conditions is characterised.
FACET B: HTF state as a CONDITIONING VARIABLE — how much the LTF forward-return distribution MOVES
         as HTF state varies (between-HTF-state spread of conditional means + CI; disp_ratio range;
         DI sign-conditioning magnitude), independent of the lift-over-baseline lens.
Emits results/base_failure.{parquet,csv} and results/htf_conditional_effect.{parquet,csv}.
Reuses causal primitives only (blind of SPDR-001 findings)."""
import numpy as np, polars as pl
from pathlib import Path
import sys
EXP = Path(__file__).resolve().parents[1]
RES = EXP / "results"
sys.path.insert(0, str(EXP.parent / "SPDR-001" / "screen_code"))
sys.path.insert(0, str(EXP / "screen_code"))
import spdr001_screen as S1
import spdr002_screen as S2
from xen.evaluation import block_bootstrap_ci
from xen.zigzag import wilder_atr

INSTR, DOMAINS, HOLD_MULTS, N_SEEDS = S1.INSTRUMENTS, S1.DOMAIN_PAIRS, S1.HOLD_MULTS, S1.N_SEEDS
FLOOR = 30


def two_sample(rhi, rlo, block=5, nb=2500, seed=1):
    def boot(x):
        n = len(x); eb = max(1, min(block, n - 1)); nbk = int(np.ceil(n / eb))
        rng = np.random.default_rng(seed)
        out = np.empty(nb)
        for b in range(nb):
            st = rng.integers(0, n, nbk)
            idx = (st[:, None] + np.arange(eb)).ravel() % n
            out[b] = x[idx][:n].mean()
        return out
    if len(rhi) < 2 or len(rlo) < 2:
        return np.nan, [np.nan, np.nan]
    d = boot(rhi) - boot(rlo)
    return float(rhi.mean() - rlo.mean()), [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]


def arm(ctx, sig, hold, mask):
    n = ctx.n
    elig = ctx.valid & mask & (sig != 0) & (np.arange(n) + hold < n)
    idx = np.nonzero(elig)[0]
    if idx.size == 0:
        return np.array([]), np.array([])
    ent = S1.greedy_entries(idx, hold)
    r = sig[ent] * (ctx.ltf_open[ent + hold] - ctx.ltf_open[ent]) / ctx.ltf_atr_prev[ent]
    return ent, r


def rand_pct(ctx, mean, n_target, hold, mask):
    n = ctx.n
    pool = np.nonzero(ctx.valid & mask & (np.arange(n) + hold < n))[0]
    if pool.size == 0 or n_target == 0:
        return np.nan
    ms = np.empty(N_SEEDS)
    for k in range(N_SEEDS):
        rng = np.random.default_rng(10_000 + k)
        take = min(n_target, pool.size)
        e = np.sort(rng.choice(pool, take, replace=False))
        s = rng.choice(np.array([-1, 1], np.int8), take)
        ms[k] = float(np.mean(s * (ctx.ltf_open[e + hold] - ctx.ltf_open[e]) / ctx.ltf_atr_prev[e]))
    return float((ms < mean).mean())


def downside_conc(r):
    """fraction of total loss mass carried by the worst 5% of trades; mean excl worst 5%."""
    if r.size < 20:
        return np.nan, np.nan
    neg_sum = r[r < 0].sum()
    k = max(1, int(0.05 * r.size))
    worst = np.sort(r)[:k]
    frac = float(worst.sum() / neg_sum) if neg_sum < 0 else np.nan
    thr = np.percentile(r, 5)
    excl = float(r[r > thr].mean())
    return frac, excl


def skew(r):
    m, s = r.mean(), r.std()
    return float(np.mean(((r - m) / s) ** 3)) if s > 0 else np.nan


base_rows, cond_rows = [], []
for sym in INSTR:
    train = S1.load_train_1m(sym)
    for name, htf_min, ltf_min, ratio in DOMAINS:
        ctx = S1.build_domain_ctx(name, htf_min, ltf_min, train, shift_htf=0)
        sig = S2.momentum_signal(ctx)
        allmask = np.ones(ctx.n, bool)
        for m in HOLD_MULTS:
            hold = ratio * m
            ent_b, rb = arm(ctx, sig, hold, allmask)
            if rb.size == 0:
                continue
            bcc = block_bootstrap_ci(rb, np.mean, block=5, n_boot=3000, n_seeds=5)
            frac, excl = downside_conc(rb)
            rb_bps = sig[ent_b] * (ctx.ltf_open[ent_b + hold] - ctx.ltf_open[ent_b]) / ctx.ltf_open[ent_b] * 1e4
            bps_ci = block_bootstrap_ci(rb_bps, np.mean, block=5, n_boot=3000, n_seeds=5)
            worst_dec = np.sort(rb)[:max(1, int(0.1 * rb.size))]
            base_rows.append({"instrument": sym, "domain": name, "hold_mult": m, "hold_bars": hold,
                "n": int(rb.size), "mean": float(rb.mean()), "ci_lo": bcc["ci"][0], "ci_hi": bcc["ci"][1],
                "mean_bps": float(rb_bps.mean()), "bps_ci_lo": bps_ci["ci"][0], "bps_ci_hi": bps_ci["ci"][1],
                "median": float(np.median(rb)),
                "std": float(rb.std()), "skew": skew(rb), "hitrate": float((rb > 0).mean()),
                "tail_mass_2atr": float((np.abs(rb) > 2).mean()),
                "left_tail_2atr": float((rb < -2).mean()), "right_tail_2atr": float((rb > 2).mean()),
                "q01": float(np.percentile(rb, 1)), "q99": float(np.percentile(rb, 99)),
                "q05": float(np.percentile(rb, 5)), "q95": float(np.percentile(rb, 95)),
                "worst5pct_loss_share": frac, "mean_excl_worst5": excl,
                "worst_decile_mean_contrib": float(worst_dec.sum() / rb.size),
                "rand_timing_pct": rand_pct(ctx, float(rb.mean()), rb.size, hold, allmask)})

            # FACET B: HTF conditioning
            def bucket_effect(labels, vals):
                arms = {}
                for v in vals:
                    _, r = arm(ctx, sig, hold, labels == v)
                    if r.size >= FLOOR:
                        arms[v] = r
                if len(arms) < 2:
                    return None
                means = {v: r.mean() for v, r in arms.items()}
                hv = max(means, key=means.get); lv = min(means, key=means.get)
                rng_, ci = two_sample(arms[hv], arms[lv])
                disp = {v: r.std() for v, r in arms.items()}
                return {"range": rng_, "range_ci_lo": ci[0], "range_ci_hi": ci[1],
                        "hi_state": int(hv), "lo_state": int(lv),
                        "hi_mean": float(means[hv]), "lo_mean": float(means[lv]),
                        "disp_ratio_range": float(max(disp.values()) / min(disp.values())),
                        "n_states": len(arms)}
            adx = bucket_effect(ctx.adx_bucket, [0, 1, 2])
            atr = bucket_effect(ctx.atr_reg, [0, 1, 2])
            # DI sign-conditioning: momentum-agrees-with-HTF vs momentum-disagrees
            _, r_ag = arm(ctx, sig, hold, ctx.htf_dir == sig)   # note: mask applied post via sig!=0 in arm
            # build agree/disagree directly:
            n = ctx.n
            base_elig = ctx.valid & (sig != 0) & (np.arange(n) + hold < n)
            ag = base_elig & (sig == ctx.htf_dir); dg = base_elig & (sig == -ctx.htf_dir)
            ea = S1.greedy_entries(np.nonzero(ag)[0], hold) if ag.any() else np.array([], int)
            ed = S1.greedy_entries(np.nonzero(dg)[0], hold) if dg.any() else np.array([], int)
            ra = sig[ea] * (ctx.ltf_open[ea + hold] - ctx.ltf_open[ea]) / ctx.ltf_atr_prev[ea] if ea.size else np.array([])
            rd = sig[ed] * (ctx.ltf_open[ed + hold] - ctx.ltf_open[ed]) / ctx.ltf_atr_prev[ed] if ed.size else np.array([])
            di_eff, di_ci = (two_sample(ra, rd) if (ra.size >= FLOOR and rd.size >= FLOOR) else (np.nan, [np.nan, np.nan]))
            cond_rows.append({"instrument": sym, "domain": name, "hold_mult": m, "hold_bars": hold,
                "base_n": int(rb.size),
                "adx_range": adx["range"] if adx else np.nan,
                "adx_range_ci_lo": adx["range_ci_lo"] if adx else np.nan,
                "adx_range_ci_hi": adx["range_ci_hi"] if adx else np.nan,
                "adx_hi_state": adx["hi_state"] if adx else None, "adx_lo_state": adx["lo_state"] if adx else None,
                "adx_disp_ratio_range": adx["disp_ratio_range"] if adx else np.nan, "adx_n_states": adx["n_states"] if adx else 0,
                "atr_range": atr["range"] if atr else np.nan,
                "atr_range_ci_lo": atr["range_ci_lo"] if atr else np.nan,
                "atr_range_ci_hi": atr["range_ci_hi"] if atr else np.nan,
                "atr_hi_state": atr["hi_state"] if atr else None, "atr_lo_state": atr["lo_state"] if atr else None,
                "atr_disp_ratio_range": atr["disp_ratio_range"] if atr else np.nan, "atr_n_states": atr["n_states"] if atr else 0,
                "di_sign_effect": di_eff, "di_ci_lo": di_ci[0], "di_ci_hi": di_ci[1],
                "di_agree_n": int(ra.size), "di_disagree_n": int(rd.size),
                "di_agree_mean": float(ra.mean()) if ra.size else np.nan,
                "di_disagree_mean": float(rd.mean()) if rd.size else np.nan})
        print(f"  {sym} {name} done", flush=True)
        del ctx

bf = pl.DataFrame(base_rows, strict=False); bf.write_parquet(RES / "base_failure.parquet")
bf.with_columns([pl.col(c).round(4) for c in bf.columns if bf[c].dtype in (pl.Float64,)]).write_csv(RES / "base_failure.csv")
ce = pl.DataFrame(cond_rows, strict=False); ce.write_parquet(RES / "htf_conditional_effect.parquet")
ce.with_columns([pl.col(c).round(4) for c in ce.columns if ce[c].dtype in (pl.Float64,)]).write_csv(RES / "htf_conditional_effect.csv")
print("wrote base_failure + htf_conditional_effect")

# ---- console digest for the write-up ----
print("\n=== FACET A: base momentum failure (per stratum) ===")
print(bf.select(["instrument","domain","hold_mult","n","mean","ci_lo","ci_hi","std","skew","hitrate",
                 "worst5pct_loss_share","rand_timing_pct"]).sort(["domain","instrument","hold_mult"]).to_pandas().to_string())
print("\n=== FACET B: HTF conditional effect (between-state range + CI) ===")
print(ce.select(["instrument","domain","hold_mult","adx_range","adx_range_ci_lo","adx_range_ci_hi","adx_disp_ratio_range",
                 "atr_range","atr_range_ci_lo","atr_range_ci_hi","atr_disp_ratio_range",
                 "di_sign_effect","di_ci_lo","di_ci_hi"]).sort(["domain","instrument","hold_mult"]).to_pandas().to_string())
# which conditional-effect ranges are CI-clear
adxc = ce.filter((pl.col("adx_range_ci_lo")>0)); atrc = ce.filter((pl.col("atr_range_ci_lo")>0))
dic = ce.filter((pl.col("di_ci_lo")>0)|(pl.col("di_ci_hi")<0))
print(f"\nADX between-state range CI>0: {adxc.height}/{ce.height}; ATR: {atrc.height}/{ce.height}; DI sign CI-excl-0: {dic.height}/{ce.height}")
