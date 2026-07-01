namespace Xen.StrategyHost;

// ===========================================================================
// CF-MR-003 CONC-1 (EXP-010 T1 / EXP-012 T2) — form-2 limit-at-anchor mean-reversion
// fade, computed IN-ENGINE (L-01). PRICE-PRIMARY.
//
// EXP-012 (Track 2, exec-15m) adds a SINGLE-SYMBOL S3_DETREND anchor (rolling-OLS
// log(price)~time trendline residual, RollingOlsTimeFit) alongside the S5_SPREAD
// multi-symbol basket anchor below; selected by the `series` ctor arg. Both share the
// identical form-2 limit / VR∧HL selector / |z|>=2 fade / horizon-fallback machinery —
// only the anchor a_t differs (S3: trendline; S5: rolling-β basket). The comment below
// describes the S5 anchor; S3 replaces the basket-β anchor with the OLS-time trendline.
//
// ADMITTED VEHICLE (xen.cross_domain_mr.anchor_series S5 branch — exec-grid β,
// NOT anchor-domain-fit). Per exec (1h) bar t, on log-price of the traded symbol:
//   basket_t = mean over class-mates (class minus self) of log(Close), exec grid,
//              aligned by CloseTime  (IBasketFeed, causal <= t)
//   a_t      = beta_t*basket_t + alpha_t,  (beta,alpha) = OLS logClose ~ basket over
//              the trailing W_Z=200 exec bars, evaluated at the current basket
//   dev_t    = logClose_t - a_t
//   z_t      = dev_t / std(dev over trailing W_Z)          (rolling_std_z)
//   VR_t     = variance_ratio(dev over trailing W_S, q=4)  (Lo-MacKinlay)
//   HL_t     = AR(1) half-life(dev over trailing W_S)
// Selector (entry-eligible) at t-1: VR<1-VR_DELTA(=0.9) AND 0<HL<=HL_MAX(=48).
// Extreme probe: |z| >= Z_STAR(=2). Fade = trade against the deviation sign.
//
// STRATEGY (form-2, /REENTRY=none, all decisions rested from t-1):
//   * Entry = a LIVE LIMIT at the z=+/-Z_STAR band-edge price mapped from t-1 state:
//       upper band  P_hi = exp(a[t-1] + Z_STAR*sigma[t-1]) -> SHORT (dev extreme +)
//       lower band  P_lo = exp(a[t-1] - Z_STAR*sigma[t-1]) -> LONG  (dev extreme -)
//     placed only when flat AND the selector+extreme fired at t-1; fills intrabar iff
//     the bar's range touches it (fill AT the limit price). (Operationalization note:
//     the design specifies "live limit at the <=t-1 extreme-deviation price level (the
//     z=+/-2 band mapped to price)"; the band-edge price is that mapping. Flagged for
//     audit.)
//   * Exit  = form-2 favourable LIMIT at the anchor mean a_target = exp(a[t-1]),
//     refreshed each bar from t-1; long exits when High>=a_target, short when
//     Low<=a_target; fill AT a_target. Fallback = horizon stop H_i=min(48,3*HL_i)
//     exec bars (HL fixed at entry) -> market close at the bar Close (pays cost).
//
// CAUSAL CONTRACT (decide-before-fold, mirrors RsiFadeModel). Entering OnBar(bar_t),
// all _rested* reflect state THROUGH t-1. Decisions use only those + bar_t execution
// prices (Open, and High/Low for a limit resting from t-1 — no look-ahead). Only AFTER
// emitting does the model fold bar_t (append logClose_t, basket_t) and refresh _rested*
// for t+1. The forming bar's own Close is never read for a decision. A fresh entry's
// exit limit is active from the NEXT bar (exit checked only on an already-held position).
//
// EMISSION: per bar — heldPosition (position the bar's return accrues to, incl. an exit
// bar), real domain-bar OHLC, EntryFillPrice / ExitFillPrice (engine-realized limit or
// market fills; NaN otherwise), and the causal provenance Anchor(=a_target price)/Dev/Z/
// Vr/Hl/Beta rested from t-1 (T2 causal-provenance trace). Python assembles open-to-open
// realized returns + intra-position MTM from these (no re-derived edge — L-01/P-09).
// ===========================================================================
public sealed class CrossDomainMrLimitModel : ISignalModel
{
    // Frozen selector constants (xen.cross_domain_mr; never tuned — L-12).
    private const int WZ = 200;          // beta / std-z / sigma window (exec bars)
    private const int WS = 200;          // MR-screen window (exec bars)
    private const int VrQ = 4;           // variance-ratio aggregation
    private const double VrDelta = 0.10; // VR leg passes iff VR < 1 - VrDelta
    private const double HlMax = 48.0;   // half-life leg passes iff 0 < HL <= HlMax
    private const double ZStar = 2.0;    // extreme probe on |z|
    private const int HorizonCap = 48;   // H_i = min(HorizonCap, 3*HL_i)
    private const double HorizonHlMult = 3.0;

    // EXP-012 (CONC-1 Track 2): anchor series. S5_SPREAD = multi-symbol exec-grid rolling-beta basket
    // (EXP-010, T2b); S3_DETREND = SINGLE-SYMBOL rolling-OLS log(price)~time trendline residual (T2a).
    // Both feed the identical form-2 limit/selector/VR/HL/horizon machinery; only the anchor differs.
    public const string SeriesS5 = "S5_SPREAD";
    public const string SeriesS3 = "S3_DETREND";
    private readonly string _series;
    private readonly IBasketFeed? _basket;   // null for S3_DETREND (no basket)

    // Per-bar history (exec-grid, appended at fold; index k == bar k).
    private readonly List<double> _logClose = new();
    private readonly List<double> _basketLog = new();
    private readonly List<double> _dev = new();     // dev[k] = logClose[k]-a[k]; NaN until W_Z ready

    // Rested decision inputs computed from state THROUGH t-1 (refreshed at end of OnBar).
    private double _restedAnchorLog = double.NaN;    // a[t-1]
    private double _restedDev = double.NaN;
    private double _restedZ = double.NaN;
    private double _restedSigma = double.NaN;        // std(dev) over W_Z ending t-1
    private double _restedVr = double.NaN;
    private double _restedHl = double.NaN;
    private double _restedBeta = double.NaN;

    // Open-position state.
    private int _position;                // -1/0/+1 held into the next bar
    private double _entryFillPrice = double.NaN;
    private double _exitAnchorLog = double.NaN;   // a_target log fixed at entry (a[entry-1])
    private int _horizon;                 // H_i exec bars, fixed at entry
    private int _barsInPos;
    private long _tradeSequence;

    public CrossDomainMrLimitModel(IBasketFeed? basketFeed, string series = SeriesS5,
                                   string strategyName = "cross_domain_mr_limit")
    {
        _series = series;
        if (_series != SeriesS5 && _series != SeriesS3)
            throw new ArgumentException($"Unknown CDM series '{series}' (expected {SeriesS5}|{SeriesS3}).");
        if (_series == SeriesS5 && basketFeed is null)
            throw new ArgumentNullException(nameof(basketFeed), "S5_SPREAD requires a basket feed.");
        _basket = basketFeed;   // S3_DETREND: null (single-symbol, no basket)
        StrategyName = strategyName;
    }

    public string StrategyName { get; }

    public SignalUpdate OnBar(TimeBar bar, string domain)
    {
        var warmup = double.IsNaN(_restedAnchorLog) || double.IsNaN(_restedSigma);
        var events = new List<SignalEventRecord>();
        var trades = new List<StrategyTradeRecord>();

        var heldPosition = _position;
        var entryFill = double.NaN;
        var exitFill = double.NaN;

        if (!warmup)
        {
            // --- Exit leg first: form-2 anchor limit (rested a_target) on an open position,
            //     else horizon fallback -> market close.
            if (_position != 0)
            {
                _barsInPos++;
                var aTarget = Math.Exp(_exitAnchorLog);
                var anchorTouched = _position == 1 ? bar.High >= aTarget : bar.Low <= aTarget;
                if (anchorTouched)
                {
                    // Gap-through fill: a limit the bar opened already through fills at the Open (the
                    // first realizable price), never at a price outside the bar's traded range.
                    exitFill = _position == 1
                        ? (bar.Open >= aTarget ? bar.Open : aTarget)     // sell limit (favourable, above)
                        : (bar.Open <= aTarget ? bar.Open : aTarget);    // buy limit (favourable, below)
                    trades.Add(MakeTrade(bar, domain, _position, 0, exitFill));
                    events.Add(MakeEvent(bar, domain, "exit_anchor_limit", 0, _position));
                    _position = 0;
                }
                else if (_barsInPos >= _horizon)
                {
                    exitFill = bar.Close;   // market fallback at the horizon bar close (pays cost)
                    trades.Add(MakeTrade(bar, domain, _position, 0, exitFill));
                    events.Add(MakeEvent(bar, domain, "exit_horizon_market", 0, _position));
                    _position = 0;
                }
            }

            // --- Entry leg: only when flat and the selector+extreme fired at t-1. A fresh
            //     entry's exit limit becomes active on the NEXT bar (/REENTRY=none).
            if (_position == 0 && double.IsNaN(exitFill) && SelectorFired(out var dir, out var limitPrice))
            {
                var entryTouched = dir == 1 ? bar.Low <= limitPrice : bar.High >= limitPrice;
                if (entryTouched)
                {
                    // Gap-through fill: a limit the bar opened already through fills at the Open, never
                    // outside the traded range (an over-range fill is a non-executable / mispriced entry).
                    var fill = dir == 1
                        ? (bar.Open <= limitPrice ? bar.Open : limitPrice)   // buy limit (lower band)
                        : (bar.Open >= limitPrice ? bar.Open : limitPrice);  // sell limit (upper band)
                    _position = dir;
                    heldPosition = dir;
                    entryFill = fill;
                    _entryFillPrice = fill;
                    _exitAnchorLog = _restedAnchorLog;                       // a_target = a[t-1], fixed
                    _horizon = HorizonBars(_restedHl);
                    _barsInPos = 0;
                    trades.Add(MakeTrade(bar, domain, 0, dir, limitPrice));
                    events.Add(MakeEvent(bar, domain, "enter_fade_limit", dir, 0));
                }
            }
        }

        var emitted = BuildPosition(bar, domain, heldPosition, warmup, entryFill, exitFill);

        // --- Fold bar_t: append logClose_t, basket_t; recompute a_t/dev_t; refresh _rested* for t+1.
        FoldAndRefresh(bar);
        return new SignalUpdate(emitted, events, trades);
    }

    // True iff, from t-1 rested state, the VR&HL selector passed AND |z|>=Z_STAR; yields the fade
    // direction (+1 long / -1 short) and the band-edge limit price.
    private bool SelectorFired(out int dir, out double limitPrice)
    {
        dir = 0;
        limitPrice = double.NaN;
        var selectorPass = double.IsFinite(_restedVr) && _restedVr < 1.0 - VrDelta
                           && double.IsFinite(_restedHl) && _restedHl > 0.0 && _restedHl <= HlMax;
        if (!selectorPass || !double.IsFinite(_restedZ) || Math.Abs(_restedZ) < ZStar)
            return false;
        if (_restedZ >= ZStar)          // dev extreme positive -> price above anchor -> SHORT the upper band
        {
            dir = -1;
            limitPrice = Math.Exp(_restedAnchorLog + ZStar * _restedSigma);
        }
        else                            // dev extreme negative -> LONG the lower band
        {
            dir = 1;
            limitPrice = Math.Exp(_restedAnchorLog - ZStar * _restedSigma);
        }
        return true;
    }

    private static int HorizonBars(double halfLife)
    {
        var h = (int)Math.Floor(HorizonHlMult * halfLife);
        if (h < 1) h = 1;
        return Math.Min(HorizonCap, h);
    }

    // Append bar_t state and recompute the rested decision inputs for t+1 (windows ending t).
    private void FoldAndRefresh(TimeBar bar)
    {
        var logClose = Math.Log(bar.Close);
        _logClose.Add(logClose);

        // a_t: S5 = rolling-beta over the trailing W_Z (basket -> logClose) at basket_t; S3 = rolling-OLS
        // log(price)~time trendline fitted at the window end (single-symbol, no basket).
        double aT, betaT;
        if (_series == SeriesS3)
        {
            aT = RollingOlsTimeFit(out betaT);
        }
        else
        {
            _basketLog.Add(_basket!.LogPriceAt(bar.CloseTime));   // causal (mates <= t); NaN if unpowered
            aT = RollingBetaFit(out betaT);
        }
        _dev.Add(double.IsFinite(aT) ? logClose - aT : double.NaN);

        // Refresh rested = state through t (used to decide at t+1).
        _restedAnchorLog = aT;
        _restedBeta = betaT;
        var devWindowZ = TailFinite(_dev, WZ);
        _restedSigma = Std(devWindowZ);
        _restedDev = _dev[^1];
        _restedZ = double.IsFinite(_restedDev) && _restedSigma > 0.0 ? _restedDev / _restedSigma : double.NaN;
        var devWindowS = TailFinite(_dev, WS);
        _restedVr = VarianceRatio(devWindowS, VrQ);
        _restedHl = HalfLife(devWindowS);
    }

    // OLS logClose ~ basket over the trailing W_Z bars (both finite), fitted at the current basket.
    // Mirrors cross_domain_mr.rolling_beta_fit. Returns NaN (and NaN beta) if the window is short or
    // the basket variance is degenerate / any pair is non-finite.
    private double RollingBetaFit(out double beta)
    {
        beta = double.NaN;
        var n = _logClose.Count;
        if (n < WZ)
            return double.NaN;
        int start = n - WZ;
        double sx = 0, sy = 0;
        for (int i = start; i < n; i++)
        {
            var x = _basketLog[i];
            var y = _logClose[i];
            if (!double.IsFinite(x) || !double.IsFinite(y))
                return double.NaN;                 // require a full finite window (matches np.all(isfinite))
            sx += x; sy += y;
        }
        double mx = sx / WZ, my = sy / WZ;
        double sxx = 0, sxy = 0;
        for (int i = start; i < n; i++)
        {
            var xc = _basketLog[i] - mx;
            sxx += xc * xc;
            sxy += xc * (_logClose[i] - my);
        }
        if (!(sxx > 0.0))
            return double.NaN;
        beta = sxy / sxx;
        double alpha = my - beta * mx;
        return beta * _basketLog[n - 1] + alpha;   // fitted at current basket (window end)
    }

    // S3_DETREND anchor: rolling OLS log(price) ~ time over the trailing W_Z bars, fitted at the window
    // END (t = W_Z-1). Mirrors cross_domain_mr.rolling_ols_fit (time regressor = 0..W_Z-1; fitted value
    // alpha + beta*(W_Z-1)). Single-symbol, no basket. NaN if the window is short or any y is non-finite.
    private double RollingOlsTimeFit(out double beta)
    {
        beta = double.NaN;
        var n = _logClose.Count;
        if (n < WZ)
            return double.NaN;
        int start = n - WZ;
        double sy = 0;
        for (int i = start; i < n; i++)
        {
            if (!double.IsFinite(_logClose[i]))
                return double.NaN;                 // require a full finite window (matches np.all(isfinite))
            sy += _logClose[i];
        }
        double mt = (WZ - 1) / 2.0;                // mean of time regressor 0..W_Z-1
        double my = sy / WZ;
        double sxx = 0, sxy = 0;
        for (int k = 0; k < WZ; k++)
        {
            double tc = k - mt;
            sxx += tc * tc;
            sxy += tc * (_logClose[start + k] - my);
        }
        if (!(sxx > 0.0))
            return double.NaN;
        beta = sxy / sxx;
        double alpha = my - beta * mt;
        return alpha + beta * (WZ - 1);            // fitted at the window end (t = W_Z-1)
    }

    // Lo-MacKinlay VR(q) on a level series (cross_domain_mr.variance_ratio). NaN if degenerate.
    private static double VarianceRatio(double[] x, int q)
    {
        int n = x.Length;
        if (n < q + 2)
            return double.NaN;
        var d1 = new double[n - 1];
        for (int i = 1; i < n; i++) d1[i - 1] = x[i] - x[i - 1];
        var dq = new double[n - q];
        for (int i = q; i < n; i++) dq[i - q] = x[i] - x[i - q];
        double v1 = VarDdof1(d1);
        double vq = VarDdof1(dq);
        if (!(v1 > 0.0) || !double.IsFinite(vq))
            return double.NaN;
        return vq / (q * v1);
    }

    // AR(1) mean-reversion half-life on a level series (cross_domain_mr.half_life). NaN if phi outside (0,1).
    private static double HalfLife(double[] x)
    {
        int n = x.Length;
        if (n < 3)
            return double.NaN;
        var lag = new double[n - 1];
        var cur = new double[n - 1];
        for (int i = 1; i < n; i++) { lag[i - 1] = x[i - 1]; cur[i - 1] = x[i]; }
        double lagMean = Mean(lag), curMean = Mean(cur);
        double sxx = 0, sxy = 0;
        for (int i = 0; i < lag.Length; i++)
        {
            var xc = lag[i] - lagMean;
            sxx += xc * xc;
            sxy += xc * (cur[i] - curMean);
        }
        if (!(sxx > 0.0))
            return double.NaN;
        double phi = sxy / sxx;
        if (!(phi > 0.0 && phi < 1.0))
            return double.NaN;
        return -Math.Log(2.0) / Math.Log(phi);
    }

    // Trailing up-to-`w` finite tail of a list (mirrors passing the finite trailing window).
    private static double[] TailFinite(List<double> src, int w)
    {
        int n = src.Count;
        int take = Math.Min(w, n);
        var buf = new List<double>(take);
        for (int i = n - take; i < n; i++)
            if (double.IsFinite(src[i]))
                buf.Add(src[i]);
        return buf.ToArray();
    }

    private static double Mean(double[] x)
    {
        double s = 0;
        for (int i = 0; i < x.Length; i++) s += x[i];
        return s / x.Length;
    }

    private static double VarDdof1(double[] x)
    {
        int n = x.Length;
        if (n < 2) return double.NaN;
        double m = Mean(x), s = 0;
        for (int i = 0; i < n; i++) { var d = x[i] - m; s += d * d; }
        return s / (n - 1);
    }

    private static double Std(double[] x)
    {
        var v = VarDdof1(x);
        return double.IsFinite(v) && v > 0.0 ? Math.Sqrt(v) : double.NaN;
    }

    private SignalPositionRecord BuildPosition(
        TimeBar bar, string domain, int heldPosition, bool warmup, double entryFill, double exitFill)
    {
        var anchorPrice = double.IsFinite(_restedAnchorLog) ? Math.Exp(_restedAnchorLog) : double.NaN;
        return new SignalPositionRecord(
            bar.CloseTime,
            domain,
            StrategyName,
            heldPosition,
            warmup ? double.NaN : _restedZ,     // SignalValue carries the rested z that drove the decision
            bar.Open,
            bar.High,
            bar.Low,
            bar.Close,
            warmup,
            heldPosition == 0,
            RegimeId: -1,
            RegimeDirection: 0,
            ExitFillPrice: exitFill,
            EntryFillPrice: entryFill,
            Anchor: anchorPrice,
            Dev: _restedDev,
            Z: _restedZ,
            Vr: _restedVr,
            Hl: _restedHl,
            Beta: _restedBeta);
    }

    private SignalEventRecord MakeEvent(
        TimeBar bar, string domain, string eventType, int position, int previousPosition)
    {
        return new SignalEventRecord(
            bar.CloseTime, domain, StrategyName, eventType, position, previousPosition, _restedZ);
    }

    private StrategyTradeRecord MakeTrade(
        TimeBar bar, string domain, int previousPosition, int position, double price)
    {
        var action = position != 0
            ? (position > 0 ? "enter_long" : "enter_short")
            : (previousPosition > 0 ? "exit_long" : "exit_short");
        return new StrategyTradeRecord(
            bar.CloseTime, domain, StrategyName, action, previousPosition, position,
            price, Math.Abs(position - previousPosition), _tradeSequence++);
    }
}
