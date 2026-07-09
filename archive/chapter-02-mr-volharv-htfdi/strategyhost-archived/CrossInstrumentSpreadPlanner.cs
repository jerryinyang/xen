namespace Xen.StrategyHost;

// ===========================================================================
// CF-MR-004 (EXP-013) — Cross-instrument spread mean-reversion PLANNER.
//
// PURE, cAlgo-free, from-scratch family logic (L-13). It does NOT adjudicate
// fills or emit records — it only computes, from ≤ t-1 completed 4h bars, the
// precalculated resting-bracket levels the robot places as real cTrader pending
// orders. cTrader's backtester (m1) owns fill resolution (Route A). This replaces
// the earlier self-adjudicating ISignalModel, which computed fills on 4h OHLC —
// a vectorized residue that could not capture intrabar reversion.
//
// Execution model (operator-ratified 2026-07-01):
//   Resting bracket, NO z pre-gate. Each 4h bar (when flat), from ≤ t-1 anchor/σ:
//     sell-limit  = exp(anchorLog + Z*·σ)   (upper band → short the overextension)
//     buy-limit   = exp(anchorLog − Z*·σ)   (lower band → long the underextension)
//     exit (TP)   = exp(anchorLog)           (anchor mean; form-2, fixed at entry)
//   The band level IS the trigger; whichever fills opens the position and the
//   sibling is cancelled. z is provenance only (informative-not-gating, L-12).
//   HorizonBars is still computed below but is DORMANT — the robot applies NO horizon
//   exit (HYP-003 / amendment-003; the proposal enforces no other exits). Kept only so
//   HalfLife feeds the availability event-horizon; never used as a time-stop.
//
// 4 series (selected by ctor):
//   S5_SPREAD  : rolling-β basket  (OLS logClose ~ feedLog over Wa 4h bars)
//   S6_PAIR    : fixed-ratio pair  (β=1, single peer; spread = logClose − feedLog)
//   S7_BASKET  : fixed-weight basket (equal weights, β=1; spread = logClose − feedLog)
//   S8_RVINDEX : relative-value index (BASKET spread minus rolling median W=MedianW=90) — EXP-014
//                F-fix: basket feed (equal-weight mates) − RollingMedian_90, per the doc's headline
//                practical variation (was pair−median-60 in EXP-013; finding F).
// The feed supplies feedLog = equal-weight mean of mate log(Close) (basket) or a
// single peer log(Close) (pair), causal ≤ t, computed by the robot's cTrader feed.
//
// CAUSAL CONTRACT: Observe(k) is called ONLY with a fully completed 4h bar k
// (traded logClose + feed basket log at k). It refreshes rested state THROUGH k.
// CurrentBracket() then returns the levels the robot arms for period k+1. No
// forming-bar OHLC is ever read; the bracket for k+1 depends only on bars ≤ k.
// ===========================================================================
public sealed class CrossInstrumentSpreadPlanner
{
    // Predeclared constants (EXP-013/design.md; fresh decisions, not inherited).
    public const int WZ = 200;               // z-score / σ window (4h bars)
    public const double ZStar = 2.0;         // DEFAULT band multiple on σ (HYP-003: axis {1.5, 2.0})
    public const int Wa = 200;               // S5 OLS window (4h bars)
    public const int MedianW = 90;           // S8 rolling median window (4h bars) — EXP-014 F-fix (was 60);
                                             // headline "practical variation" = basket − RollingMedian_90 (S8
                                             // feed is a basket via conf mates, not a single pair — finding F).
    public const int HorizonCap = 48;        // H_i = min(HorizonCap, 3·HL_i)
    public const double HorizonHlMult = 3.0;

    public const string SeriesS5 = "S5_SPREAD";
    public const string SeriesS6 = "S6_PAIR";
    public const string SeriesS7 = "S7_BASKET";
    public const string SeriesS8 = "S8_RVINDEX";

    private readonly string _series;
    private readonly double _zStar;          // entry band multiple on σ (HYP-003 axis: 1.5 | 2.0)

    private readonly List<double> _logClose = new();
    private readonly List<double> _feedLog = new();
    private readonly List<double> _spread = new();
    private List<double>? _rawSpread;        // S8 only: raw pair spread for rolling median

    // Rested state through the last observed bar k.
    private double _anchorLog = double.NaN;  // S5: OLS fit; S6/7: feedLog+mean; S8: feedLog+Ct+mean
    private double _spreadValue = double.NaN;
    private double _z = double.NaN;
    private double _sigma = double.NaN;
    private double _mean = double.NaN;
    private double _hl = double.NaN;
    private double _vr = double.NaN;
    private double _beta = double.NaN;
    private bool _windowFull;                // ≥ WZ finite spreads in the trailing window (full estimation window)

    public CrossInstrumentSpreadPlanner(string series, double zStar = ZStar)
    {
        if (series != SeriesS5 && series != SeriesS6 && series != SeriesS7 && series != SeriesS8)
            throw new ArgumentException($"Unknown series '{series}' (expected {SeriesS5}|{SeriesS6}|{SeriesS7}|{SeriesS8}).");
        _series = series;
        _zStar = zStar > 0.0 ? zStar : ZStar;
    }

    public string Series => _series;

    // Append a completed 4h bar k and refresh rested state through k.
    // logClose = ln(traded Close_k); feedLog = mean mate ln(Close) (basket) or single peer ln(Close), ≤ k.
    public void Observe(double logClose, double feedLog)
    {
        _logClose.Add(logClose);
        _feedLog.Add(feedLog);

        double spread, betaT, s5Anchor;
        ComputeRawSpread(logClose, feedLog, out spread, out betaT, out s5Anchor);
        _spread.Add(spread);

        var window = TailFinite(_spread, WZ);
        _windowFull = window.Length >= WZ;   // require the full WZ estimation window before trading
        _sigma = Std(window);
        _mean = Mean(window);
        _anchorLog = ComputeAnchorLog(feedLog, s5Anchor);
        _beta = betaT;
        _spreadValue = spread;

        if (_series == SeriesS5)
            _z = double.IsFinite(spread) && _sigma > 0.0 ? spread / _sigma : double.NaN;
        else
            _z = double.IsFinite(spread) && _sigma > 0.0 ? (spread - _mean) / _sigma : double.NaN;

        _vr = VarianceRatio(window, 4);
        _hl = HalfLife(window);
    }

    // Bracket levels for the NEXT period, from rested state (≤ k). Warmup until σ ready.
    public SpreadBracket CurrentBracket()
    {
        var warmup = !_windowFull || double.IsNaN(_anchorLog) || double.IsNaN(_sigma) || _sigma <= 0.0;
        if (warmup)
            return new SpreadBracket { Warmup = true, HorizonBars = HorizonCap };

        var band = _zStar * _sigma;
        return new SpreadBracket
        {
            Warmup = false,
            SellLimitPrice = Math.Exp(_anchorLog + band),   // upper band (short)
            BuyLimitPrice = Math.Exp(_anchorLog - band),    // lower band (long)
            ExitPrice = Math.Exp(_anchorLog),               // anchor mean (form-2 TP)
            HorizonBars = HorizonFromHalfLife(_hl),
            Z = _z, AnchorLog = _anchorLog, Sigma = _sigma, Spread = _spreadValue,
            Mean = _mean, Vr = _vr, Hl = _hl, Beta = _beta
        };
    }

    // Raw spread (no mean dependence). For S5, also outputs the OLS anchor fitted value.
    private void ComputeRawSpread(double logClose, double feedLog,
                                  out double spread, out double beta, out double s5Anchor)
    {
        spread = double.NaN; beta = double.NaN; s5Anchor = double.NaN;
        if (!double.IsFinite(feedLog)) return;
        switch (_series)
        {
            case SeriesS5:
                s5Anchor = RollingBetaFit(out beta);
                spread = double.IsFinite(s5Anchor) ? logClose - s5Anchor : double.NaN;
                break;
            case SeriesS6:
            case SeriesS7:
                spread = logClose - feedLog;
                break;
            case SeriesS8:
                var r = logClose - feedLog;
                _rawSpread ??= new List<double>();
                _rawSpread.Add(r);
                var ct = RollingMedian(TailFinite(_rawSpread, MedianW));
                spread = double.IsFinite(ct) ? r - ct : double.NaN;
                break;
        }
    }

    // Anchor log = the exit-mean target: S5 OLS fit; S6/7 feedLog+mean; S8 feedLog+Ct+mean.
    private double ComputeAnchorLog(double feedLog, double s5Anchor)
    {
        if (_series == SeriesS5)
            return s5Anchor;
        if (!double.IsFinite(feedLog) || !double.IsFinite(_mean))
            return double.NaN;
        if (_series == SeriesS8)
        {
            var ct = _rawSpread != null ? RollingMedian(TailFinite(_rawSpread, MedianW)) : double.NaN;
            return double.IsFinite(ct) ? feedLog + ct + _mean : double.NaN;
        }
        return feedLog + _mean;  // S6 / S7
    }

    private static int HorizonFromHalfLife(double halfLife)
    {
        if (!double.IsFinite(halfLife) || halfLife <= 0.0) return HorizonCap;
        var h = (int)Math.Floor(HorizonHlMult * halfLife);
        if (h < 1) h = 1;
        return Math.Min(HorizonCap, h);
    }

    // --- Statistical helpers (from scratch — L-13; standard formulas, new implementation).

    private static double[] TailFinite(List<double> list, int n)
    {
        var result = new List<double>(n);
        for (var i = Math.Max(0, list.Count - n); i < list.Count; i++)
            if (double.IsFinite(list[i]))
                result.Add(list[i]);
        return result.ToArray();
    }

    private static double Mean(double[] vals)
    {
        if (vals.Length == 0) return double.NaN;
        var s = 0.0;
        foreach (var v in vals) s += v;
        return s / vals.Length;
    }

    private static double Std(double[] vals)
    {
        if (vals.Length < 2) return double.NaN;
        var m = Mean(vals);
        if (!double.IsFinite(m)) return double.NaN;
        var ss = 0.0;
        foreach (var v in vals) { var d = v - m; ss += d * d; }
        return Math.Sqrt(ss / (vals.Length - 1));
    }

    private static double Variance(double[] vals)
    {
        if (vals.Length < 2) return double.NaN;
        var m = Mean(vals);
        if (!double.IsFinite(m)) return double.NaN;
        var ss = 0.0;
        foreach (var v in vals) { var d = v - m; ss += d * d; }
        return ss / (vals.Length - 1);
    }

    // Lo-MacKinlay variance ratio VR(q) = Var(q-diff) / (q · Var(1-diff)) of the spread series.
    private static double VarianceRatio(double[] vals, int q)
    {
        if (vals.Length < q * 2) return double.NaN;
        var n = vals.Length;
        var ret1 = new double[n - 1];
        for (var i = 0; i < n - 1; i++) ret1[i] = vals[i + 1] - vals[i];
        var var1 = Variance(ret1);
        if (var1 <= 0.0) return double.NaN;
        var retQ = new double[n - q];
        for (var i = 0; i < n - q; i++) retQ[i] = vals[i + q] - vals[i];
        var varQ = Variance(retQ);
        if (!double.IsFinite(varQ)) return double.NaN;
        return varQ / (q * var1);
    }

    // AR(1) half-life = -ln(2) / ln(φ), φ = Cov(S_t, S_{t-1}) / Var(S_{t-1}).
    private static double HalfLife(double[] vals)
    {
        if (vals.Length < 3) return double.NaN;
        var n = vals.Length - 1;
        var x = new double[n];
        var y = new double[n];
        for (var i = 0; i < n; i++) { x[i] = vals[i]; y[i] = vals[i + 1]; }
        var meanX = Mean(x); var meanY = Mean(y);
        if (!double.IsFinite(meanX) || !double.IsFinite(meanY)) return double.NaN;
        var cov = 0.0; var varX = 0.0;
        for (var i = 0; i < n; i++) { cov += (x[i] - meanX) * (y[i] - meanY); varX += (x[i] - meanX) * (x[i] - meanX); }
        cov /= n; varX /= n;
        if (varX <= 0.0) return double.NaN;
        var phi = cov / varX;
        if (phi <= 0.0 || phi >= 1.0) return double.NaN;
        return -Math.Log(2.0) / Math.Log(phi);
    }

    private static double RollingMedian(double[] vals)
    {
        if (vals.Length == 0) return double.NaN;
        var sorted = (double[])vals.Clone();
        Array.Sort(sorted);
        var mid = sorted.Length / 2;
        return sorted.Length % 2 == 0 ? (sorted[mid - 1] + sorted[mid]) / 2.0 : sorted[mid];
    }

    // OLS logClose ~ feedLog over the trailing Wa bars (both finite). Returns the fitted
    // value at the current (last) feedLog; outputs β. NaN until Wa finite pairs exist.
    private double RollingBetaFit(out double beta)
    {
        beta = double.NaN;
        var n = _logClose.Count;
        if (n < Wa) return double.NaN;
        var xs = new List<double>(Wa);
        var ys = new List<double>(Wa);
        for (var i = n - Wa; i < n; i++)
            if (double.IsFinite(_logClose[i]) && double.IsFinite(_feedLog[i]))
            {
                xs.Add(_feedLog[i]);
                ys.Add(_logClose[i]);
            }
        if (xs.Count < 10) return double.NaN;
        var meanX = Mean(xs.ToArray()); var meanY = Mean(ys.ToArray());
        if (!double.IsFinite(meanX) || !double.IsFinite(meanY)) return double.NaN;
        var cov = 0.0; var varX = 0.0;
        for (var i = 0; i < xs.Count; i++) { cov += (xs[i] - meanX) * (ys[i] - meanY); varX += (xs[i] - meanX) * (xs[i] - meanX); }
        cov /= xs.Count; varX /= xs.Count;
        if (varX <= 0.0) return double.NaN;
        beta = cov / varX;
        var alpha = meanY - beta * meanX;
        var currentFeed = _feedLog[^1];
        return double.IsFinite(currentFeed) ? beta * currentFeed + alpha : double.NaN;
    }
}

// Precalculated resting-bracket levels for one period (all from ≤ t-1). Prices are
// real traded-instrument prices (spread inverted); NaN/Warmup until σ is ready.
public struct SpreadBracket
{
    public bool Warmup;
    public double SellLimitPrice;   // upper band exp(anchorLog + Z*σ) — short entry limit
    public double BuyLimitPrice;    // lower band exp(anchorLog − Z*σ) — long entry limit
    public double ExitPrice;        // exp(anchorLog) — anchor-mean exit (form-2 TP)
    public int HorizonBars;         // H_i = min(48, 3·HL) 4h bars
    public double Z, AnchorLog, Sigma, Spread, Mean, Vr, Hl, Beta;  // provenance (informative)
}
