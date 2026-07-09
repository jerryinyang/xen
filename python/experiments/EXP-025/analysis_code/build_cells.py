"""EXP-025 T1 — build the per-trade TRAIN dataset (analyst's own code).

TRAIN quarantine: analysis window = first 70% of canonical m1 rows (engine fence,
analysis_end_utc in run_metadata). TRAIN = first 70% of the analysis window's m1 rows
(design §13 precedent: TRAIN cut at the 0.49*N m1 row). Trades with EntryTime >= cut
are TEST — dropped here unread. Folds F0/F1/F2 = chronological 60/20/20 of TRAIN trades.
"""
import glob, json, os, sys
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RUNS = os.path.join(ROOT, "data", "strategy_runs")
TB = os.path.join(ROOT, "data", "timebars")
OUT = os.path.join(os.path.dirname(__file__), "..", "results")

SYMBOLS = ("EURUSD GBPUSD USDJPY USDCHF USDCAD AUDUSD NZDUSD EURJPY GBPJPY AUDJPY "
           "USTEC US500 US2000 JP225 AUS200 US30 STOXX50 DE40 HK50 UK100 XAUUSD BTCUSD").split()


def train_cut_utc(sym: str) -> pd.Timestamp:
    cands = sorted(glob.glob(os.path.join(TB, f"timebars_{sym.lower()}_20210602_*.parquet")))
    assert cands, f"no canonical m1 file for {sym}"
    ts = pd.read_parquet(cands[0], columns=["OpenTime"])["OpenTime"]
    return ts.iloc[int(len(ts) * 0.7 * 0.7)]


def main() -> None:
    cuts = {s: train_cut_utc(s) for s in SYMBOLS}
    pd.Series(cuts).astype(str).to_json(os.path.join(OUT, "train_cuts.json"), indent=2)

    rows, meta = [], []
    for conf in sorted(glob.glob(os.path.join(RUNS, "EXP-025-t1-x*-h*"))):
        base = os.path.basename(conf)                      # EXP-025-t1-x3-h24
        x = int(base.split("-t1-x")[1].split("-h")[0])
        h = int(base.split("-h")[1])
        for d in sorted(glob.glob(os.path.join(conf, "htfdi_*"))):
            m = json.load(open(os.path.join(d, "run_metadata.json")))
            sym = m["symbol"]
            t = pd.read_parquet(os.path.join(d, "cis_trades.parquet"))
            n_all = len(t)
            n_cens = int(t["Censored"].sum())
            t = t[~t["Censored"].astype(bool)].copy()
            cut = cuts[sym]
            t["EntryTime"] = pd.to_datetime(t["EntryTime"])
            n_test = int((t["EntryTime"] >= cut).sum())
            t = t[t["EntryTime"] < cut].sort_values("EntryTime").reset_index(drop=True)
            n = len(t)
            f0, f1 = int(n * 0.6), int(n * 0.8)
            t["fold"] = "F0"
            t.loc[f0:f1 - 1, "fold"] = "F1"
            t.loc[f1:, "fold"] = "F2"
            t["symbol"], t["x"], t["h"] = sym, x, h
            keep = ["symbol", "x", "h", "fold", "EntryTime", "ExitTime", "Direction",
                    "EntryFillPrice", "ExitFillPrice", "RealizedBps", "BarsHeld",
                    "MaeBps", "MfeBps", "EntryVolRegime", "HtfPlusDi", "HtfMinusDi",
                    "HtfAdx", "HtfAtr", "HtfBarCloseTime", "ExitReason"]
            rows.append(t[keep])
            meta.append(dict(symbol=sym, x=x, h=h, n_emitted=n_all, n_censored=n_cens,
                             n_test_quarantined=n_test, n_train=n,
                             train_cut=str(cut)))
    df = pd.concat(rows, ignore_index=True)
    df.to_parquet(os.path.join(OUT, "train_trades.parquet"))
    pd.DataFrame(meta).to_csv(os.path.join(OUT, "cell_counts.csv"), index=False)
    print("cells:", len(meta), "train trades:", len(df))
    print(df.groupby("symbol").size().to_string())


if __name__ == "__main__":
    sys.exit(main())
