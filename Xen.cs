using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using cAlgo.API;
using Parquet;
using Parquet.Data;
using Parquet.Schema;
using Xen.StrategyHost;

namespace cAlgo.Robots;

public enum XenMode
{
    StrategyHost,
    TimeBars,
    StrategyHostParity
}

public enum XenStrategy
{
    MaCrossover,
    AvwapBaseline,
    Donchian20,
    Rsi2Fade,
    CrossDomainMrLimit
}

[Robot(AccessRights = AccessRights.FullAccess, AddIndicators = false, DefaultTimeFrame="Minute")]
public class Xen : Robot
{
    private const string OutputDirectory = "/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/timebars";
    private const string StrategyRunOutputDirectory = "/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/strategy_runs";
    private const int BatchSize = 20000;

    [Parameter("Mode", DefaultValue = XenMode.StrategyHost)]
    public XenMode Mode { get; set; } = XenMode.StrategyHost;

    [Parameter("Strategy", DefaultValue = XenStrategy.MaCrossover)]
    public XenStrategy Strategy { get; set; } = XenStrategy.MaCrossover;

    [Parameter("Collect & Store Time Bars", DefaultValue = false)]
    public bool CollectTimeBars { get; set; }

    [Parameter("Analysis End UTC", DefaultValue = "")]
    public string AnalysisEndUtc { get; set; } = "";

    [Parameter("Strategy Output Directory", DefaultValue = StrategyRunOutputDirectory)]
    public string StrategyOutputDirectory { get; set; } = StrategyRunOutputDirectory;

    [Parameter("Source Parquet Path", DefaultValue = "")]
    public string SourceParquetPath { get; set; } = "";

    [Parameter("Domain Minutes", DefaultValue = 5)]
    public int DomainMinutes { get; set; } = 5;

    [Parameter("Strict Coverage", DefaultValue = true)]
    public bool StrictCoverage { get; set; } = true;

    [Parameter("Min Coverage", DefaultValue = 0.9)]
    public double MinCoverage { get; set; } = 0.9;

    [Parameter("Fast MA", DefaultValue = 20)]
    public int FastMa { get; set; } = 20;

    [Parameter("Slow MA", DefaultValue = 50)]
    public int SlowMa { get; set; } = 50;

    // EXP-010 (CONC-1): S5_SPREAD basket mates for CrossDomainMrLimit — the traded symbol's
    // asset-class class-mates (class minus self), semicolon- or comma-separated broker symbols,
    // e.g. "EURUSD;USDJPY;USDCHF;USDCAD;GBPUSD;NZDUSD". Read via MarketData.GetBars at the exec
    // TimeFrame (Hour) and averaged (log-Close, causal <= t) in-engine to form the basket.
    [Parameter("Basket Mates (CANON;...)", DefaultValue = "")]
    public string BasketMates { get; set; } = "";

    // EXP-010 T1 LEAK TRIPWIRE (§7). >0 phase-shifts the basket feed back by this many hours,
    // decorrelating the basket from the traded price: the cross-domain co-movement (the edge
    // source) is destroyed while each series' marginal + autocorrelation are preserved. The net
    // per-cell edge MUST collapse to within referee FPR (a surviving edge => leak => REJECT).
    // 0 = the live run (no shift).
    [Parameter("Basket Phase Shift Hours", DefaultValue = 0)]
    public int BasketPhaseShiftHours { get; set; }

    // EXP-012 (CONC-1 Track 2): CrossDomainMrLimit anchor series. "S5_SPREAD" = multi-symbol basket
    // (needs Basket Mates); "S3_DETREND" = single-symbol rolling-OLS trendline residual (no basket).
    [Parameter("CDM Series", DefaultValue = "S5_SPREAD")]
    public string CdmSeries { get; set; } = "S5_SPREAD";

    private TimeBarParquetWriter? _writer;
    private BarAggregator? _strategyAggregator;
    private ISignalModel? _strategyModel;
    private HoldoutFence? _strategyFence;
    private StrategyRunParquetWriter? _strategyWriter;
    private DateTime? _lastCloseTime;
    private long _capturedBars;
    private long _strategySourceBars;
    private long _strategyDomainBars;
    private bool _stoppingAtFence;
    private bool _strategyFixedRunCompleted;
    private bool _strategyHostReady;
    private string? _parityExportDirectory;

    protected override void OnStart()
    {
        if (Bars.TimeFrame != TimeFrame.Minute)
            throw new InvalidOperationException("Xen must run on a 1-minute chart.");

        if (IsStrategyHostParityMode())
        {
            RunStrategyHostParityExport();
            Stop();
            return;
        }

        if (IsStrategyHostMode())
        {
            try
            {
                StartStrategyHost();
            }
            catch (Exception ex)
            {
                Print("Xen strategy host failed to start: {0}", ex.Message);
                Stop();
            }
            return;
        }

        if (!CollectTimeBars)
        {
            Print(
                "Xen: time-bar collection disabled (Collect & Store Time Bars = false) for {0}. No data written.",
                SymbolName);
            Stop();
            return;
        }

        _writer = new TimeBarParquetWriter(OutputDirectory, SymbolName, Server.Time, DateTime.UtcNow, BatchSize);
        Print("Xen started for {0}. Collecting completed 1-minute bars.", SymbolName);
    }

    protected override void OnBar()
    {
        if (IsStrategyHostParityMode())
            return;
        if (IsStrategyHostMode())
        {
            if (_strategyHostReady)
                RunStrategyHostOnCompletedBar();
        }
        else
            CaptureCompletedBar();
    }

    protected override void OnStop()
    {
        try
        {
            if (IsStrategyHostMode())
            {
                if (!_stoppingAtFence && !_strategyFixedRunCompleted)
                    FlushStrategyDomainBars();
                // EXP-029: serialize the AVWAP per-bounce detail table so the Python
                // parity harness can rebuild matched controls (no signal oracle).
                if (_strategyModel is AvwapBounceModel avwapModel)
                    _strategyWriter?.SetAvwapEventDetails(avwapModel.EventDetails);
                _strategyWriter?.Dispose();
            }
            else
            {
                _writer?.Dispose();
            }
        }
        finally
        {
            if (IsStrategyHostMode())
            {
                Print(
                    "Xen strategy host stopped for {0}. Source bars={1}, domain bars={2}.",
                    SymbolName,
                    _strategySourceBars,
                    _strategyDomainBars);
            }
            else if (IsStrategyHostParityMode())
            {
                Print(
                    "Xen strategy-host parity export stopped for {0}. Output={1}",
                    SymbolName,
                    _parityExportDirectory ?? "");
            }
            else
            {
                Print("Xen stopped for {0}. Captured {1} completed bars.", SymbolName, _capturedBars);
            }
        }
    }

    private void CaptureCompletedBar()
    {
        var index = Bars.Count - 2;
        if (index < 0)
            return;

        var openTime = Bars.OpenTimes[index];
        var closeTime = openTime.AddMinutes(1);
        var open = Bars.OpenPrices[index];
        var high = Bars.HighPrices[index];
        var low = Bars.LowPrices[index];
        var close = Bars.ClosePrices[index];

        if (_lastCloseTime.HasValue && closeTime <= _lastCloseTime.Value)
            throw new InvalidOperationException("Bar CloseTime is not strictly increasing.");

        if (high < Math.Max(open, close) || low > Math.Min(open, close))
            throw new InvalidOperationException("Bar OHLC integrity check failed.");

        _writer?.Append(new TimeBarRecord(
            SymbolName,
            openTime,
            closeTime,
            open,
            high,
            low,
            close,
            Convert.ToInt64(Bars.TickVolumes[index])));
        _lastCloseTime = closeTime;
        _capturedBars++;
    }

    private void StartStrategyHost()
    {
        if (!TryParseAnalysisEndUtc(AnalysisEndUtc, out var analysisEndUtc))
            throw new InvalidOperationException("Analysis End UTC must be explicit, e.g. 2026-01-01T00:00:00Z.");

        var minCoverage = StrictCoverage ? (double?)null : MinCoverage;
        var domain = DomainLabel(DomainMinutes);
        _strategyFence = new HoldoutFence(analysisEndUtc);
        _strategyAggregator = new BarAggregator(DomainMinutes, minCoverage);
        _strategyModel = CreateStrategyModel();
        _strategyWriter = new StrategyRunParquetWriter(
            StrategyOutputDirectory,
            _strategyModel.StrategyName,
            SymbolName,
            domain,
            _strategyFence,
            BuildStrategyParameters(minCoverage));

        _strategyHostReady = true;

        Print(
            "Xen strategy host started for {0} {1}; AnalysisEndUtc={2:o}; output={3}",
            SymbolName,
            domain,
            _strategyFence.AnalysisEndUtc,
            _strategyWriter.RunDirectory);

        if (!string.IsNullOrWhiteSpace(SourceParquetPath))
        {
            RunFixedParquetStrategyHost(domain);
            Stop();
        }
    }

    private void RunStrategyHostOnCompletedBar()
    {
        if (_strategyAggregator is null || _strategyFence is null)
            throw new InvalidOperationException("Xen strategy host was not initialised.");

        var index = Bars.Count - 2;
        if (index < 0)
            return;

        var openTime = Bars.OpenTimes[index];
        var closeTime = openTime.AddMinutes(1);

        if (_lastCloseTime.HasValue && closeTime <= _lastCloseTime.Value)
            throw new InvalidOperationException("Bar CloseTime is not strictly increasing.");
        _lastCloseTime = closeTime;

        if (_strategyFence.ShouldStopBeforeProcessing(closeTime))
        {
            _stoppingAtFence = true;
            FlushStrategyDomainBars();
            Stop();
            return;
        }

        var bar = new TimeBar(
            SymbolName,
            openTime,
            closeTime,
            Bars.OpenPrices[index],
            Bars.HighPrices[index],
            Bars.LowPrices[index],
            Bars.ClosePrices[index],
            Convert.ToInt64(Bars.TickVolumes[index]));

        if (bar.High < Math.Max(bar.Open, bar.Close) || bar.Low > Math.Min(bar.Open, bar.Close))
            throw new InvalidOperationException("Bar OHLC integrity check failed.");

        _strategySourceBars++;
        ProcessStrategyDomainBars(_strategyAggregator.Update(bar));
    }

    private void FlushStrategyDomainBars()
    {
        if (_strategyAggregator is null)
            return;
        ProcessStrategyDomainBars(_strategyAggregator.Flush());
    }

    private void ProcessStrategyDomainBars(IEnumerable<TimeBar> bars)
    {
        if (_strategyModel is null || _strategyFence is null || _strategyWriter is null)
            throw new InvalidOperationException("Xen strategy host was not initialised.");

        var domain = DomainLabel(DomainMinutes);
        foreach (var bar in bars)
        {
            if (_strategyFence.ShouldStopBeforeProcessing(bar.CloseTime))
                return;
            var update = _strategyModel.OnBar(bar, domain);
            _strategyWriter.Append(update);
            _strategyDomainBars++;
        }
    }

    private void RunFixedParquetStrategyHost(string domain)
    {
        if (_strategyAggregator is null || _strategyModel is null || _strategyFence is null || _strategyWriter is null)
            throw new InvalidOperationException("Xen strategy host was not initialised.");

        var sourceBars = TimeBarParquetReader.ReadBefore(SourceParquetPath, _strategyFence);
        var runner = new StrategyHostRunner(_strategyAggregator, _strategyModel, _strategyFence, domain);
        var updates = runner.Run(sourceBars);
        foreach (var update in updates)
            _strategyWriter.Append(update);

        _strategySourceBars = sourceBars.Count;
        _strategyDomainBars = updates.Count;
        _strategyFixedRunCompleted = true;
    }

    private void RunStrategyHostParityExport()
    {
        if (!TryParseAnalysisEndUtc(AnalysisEndUtc, out var analysisEndUtc))
            throw new InvalidOperationException("Analysis End UTC must be explicit, e.g. 2026-01-01T00:00:00Z.");
        if (string.IsNullOrWhiteSpace(SourceParquetPath))
            throw new InvalidOperationException("Source Parquet Path is required for StrategyHostParity mode.");

        var stamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
        _parityExportDirectory = Path.Combine(
            StrategyOutputDirectory,
            $"parity_{SanitizeLabel(SymbolName)}_{stamp}");
        StrategyHostParityExporter.Export(SourceParquetPath, _parityExportDirectory, analysisEndUtc);
        Print(
            "Xen strategy-host parity export completed for {0}; AnalysisEndUtc={1:o}; output={2}",
            SymbolName,
            analysisEndUtc,
            _parityExportDirectory);
    }

    private bool IsStrategyHostMode()
    {
        return Mode == XenMode.StrategyHost;
    }

    private bool IsStrategyHostParityMode()
    {
        return Mode == XenMode.StrategyHostParity;
    }

    private ISignalModel CreateStrategyModel()
    {
        return Strategy switch
        {
            XenStrategy.MaCrossover => new MovingAverageCrossoverModel(FastMa, SlowMa),
            XenStrategy.AvwapBaseline => new AvwapBounceModel(FastMa, SlowMa),
            XenStrategy.Donchian20 => new DonchianBreakoutModel(),
            XenStrategy.Rsi2Fade => new RsiFadeModel(),
            XenStrategy.CrossDomainMrLimit => CreateCrossDomainMrLimitModel(),
            _ => throw new InvalidOperationException($"Unsupported strategy: {Strategy}")
        };
    }

    private ISignalModel CreateCrossDomainMrLimitModel()
    {
        // T1 (EXP-010) = exec-1h; T2 (EXP-012) = exec-15m. The model is grid-relative (WZ/WS/horizon are
        // bar counts), so both are valid; reject other domains as a safety rail.
        if (DomainMinutes != 60 && DomainMinutes != 15)
            throw new InvalidOperationException(
                $"CrossDomainMrLimit is exec-1h (T1) or exec-15m (T2) only; DomainMinutes must be 60 or 15, got {DomainMinutes}.");
        if (CdmSeries == CrossDomainMrLimitModel.SeriesS3)
        {
            // T2a: single-symbol rolling-OLS trendline residual — no basket feed.
            Print("Xen CONC-1 S3_DETREND (single-symbol) for {0}, domain={1}m.", SymbolName, DomainMinutes);
            return new CrossDomainMrLimitModel(null, CrossDomainMrLimitModel.SeriesS3);
        }
        var mates = ParseMates(BasketMates);
        if (mates.Count == 0)
            throw new InvalidOperationException("CrossDomainMrLimit S5_SPREAD requires Basket Mates (S5 class-mates).");
        var feed = new MarketDataBasketFeed(this, mates, BasketPhaseShiftHours);
        Print("Xen CONC-1 S5_SPREAD basket feed for {0}: {1}/{2} mates resolved ({3}); phase_shift_hours={4}.",
            SymbolName, feed.ResolvedCount, mates.Count, string.Join(",", mates), BasketPhaseShiftHours);
        return new CrossDomainMrLimitModel(feed, CrossDomainMrLimitModel.SeriesS5);
    }

    private static List<string> ParseMates(string raw)
    {
        var mates = new List<string>();
        if (string.IsNullOrWhiteSpace(raw))
            return mates;
        foreach (var token in raw.Split(new[] { ';', ',' }, StringSplitOptions.RemoveEmptyEntries))
        {
            var m = token.Trim();
            if (m.Length > 0)
                mates.Add(m);
        }
        return mates;
    }

    private IReadOnlyDictionary<string, object?> BuildStrategyParameters(double? minCoverage)
    {
        var parameters = new Dictionary<string, object?>
        {
            ["strategy"] = Strategy.ToString(),
            ["domain_minutes"] = DomainMinutes,
            ["strict_coverage"] = StrictCoverage,
            ["min_coverage"] = minCoverage
        };
        switch (Strategy)
        {
            case XenStrategy.MaCrossover:
                parameters["fast_ma"] = FastMa;
                parameters["slow_ma"] = SlowMa;
                break;
            case XenStrategy.AvwapBaseline:
                parameters["fast_ma"] = FastMa;
                parameters["slow_ma"] = SlowMa;
                parameters["volume_exponent"] = AvwapBounceModel.VolumeExponent;
                parameters["band_multiplier"] = AvwapBounceModel.BandMultiplier;
                break;
            case XenStrategy.Donchian20:
                parameters["lookback"] = 20;
                break;
            case XenStrategy.Rsi2Fade:
                parameters["rsi_period"] = 2;
                parameters["low_extreme"] = 10.0;
                parameters["high_extreme"] = 90.0;
                parameters["exit"] = "rct_causal_di_minus_1";
                break;
            case XenStrategy.CrossDomainMrLimit:
                parameters["series"] = CdmSeries == CrossDomainMrLimitModel.SeriesS3
                    ? "S3_DETREND_rolling_ols_time"
                    : "S5_SPREAD_exec_grid_beta";
                parameters["w_z"] = 200;
                parameters["w_s"] = 200;
                parameters["vr_q"] = 4;
                parameters["vr_delta"] = 0.10;
                parameters["hl_max"] = 48.0;
                parameters["z_star"] = 2.0;
                parameters["direction"] = "fade";
                parameters["reentry"] = "none";
                parameters["target"] = "form2_limit_at_anchor_mean";
                parameters["exit_fallback"] = "horizon_min48_3xHL_market_close";
                parameters["basket_mates"] = BasketMates;
                parameters["basket_phase_shift_hours"] = BasketPhaseShiftHours;   // 0 live; >0 leak tripwire
                break;
        }
        return parameters;
    }

    private static bool TryParseAnalysisEndUtc(string value, out DateTime result)
    {
        return DateTime.TryParse(
            value,
            CultureInfo.InvariantCulture,
            DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal,
            out result);
    }

    private static string DomainLabel(int domainMinutes)
    {
        return domainMinutes switch
        {
            5 => "5m",
            60 => "1h",
            240 => "4h",
            _ => $"{domainMinutes}m"
        };
    }

    private static string SanitizeLabel(string value)
    {
        return value.ToLowerInvariant().Replace(" ", "_").Replace("(", "").Replace(")", "");
    }

    // EXP-010 (CONC-1): S5_SPREAD basket feed over cAlgo secondary-symbol 1h bars
    // (MarketData.GetBars — the XRSI-V1 multi-symbol pattern). Causal by construction:
    // LogPriceAt(at) uses only mate bars whose CloseTime (OpenTime + 1h) <= `at`, so the
    // forming/future mate bar is never read. A monotone per-mate cursor makes the repeated
    // increasing-time lookups O(1) amortized. Unresolved mates are skipped (drop-to-available
    // mean, matching build_baskets np.nanmean); no resolvable mate at `at` -> NaN (flat).
    private sealed class MarketDataBasketFeed : IBasketFeed
    {
        private readonly List<Bars> _bars = new();
        private readonly List<int> _cursor = new();
        private readonly int _phaseShiftHours;   // >0 = leak-tripwire decorrelation (EXP-010 §7)

        public MarketDataBasketFeed(Xen bot, IReadOnlyList<string> mates, int phaseShiftHours = 0)
        {
            _phaseShiftHours = Math.Max(0, phaseShiftHours);
            foreach (var mate in mates)
            {
                Bars? bars = null;
                try
                {
                    if (bot.Symbols.GetSymbol(mate) != null)
                        bars = bot.MarketData.GetBars(TimeFrame.Hour, mate);
                }
                catch (Exception ex)
                {
                    bot.Print("CONC-1 basket: mate '{0}' unresolved ({1}) — skipped.", mate, ex.Message);
                    bars = null;
                }
                if (bars != null)
                {
                    _bars.Add(bars);
                    _cursor.Add(0);
                }
            }
        }

        public int ResolvedCount => _bars.Count;

        public double LogPriceAt(DateTime at)
        {
            if (_phaseShiftHours > 0)
                at = at.AddHours(-_phaseShiftHours);   // decorrelate basket from the traded price (tripwire)
            double sum = 0.0;
            int used = 0;
            for (var m = 0; m < _bars.Count; m++)
            {
                var bars = _bars[m];
                var c = _cursor[m];
                while (c + 1 < bars.Count && bars.OpenTimes[c + 1].AddHours(1) <= at)
                    c++;
                _cursor[m] = c;
                if (c < bars.Count && bars.OpenTimes[c].AddHours(1) <= at)
                {
                    var px = bars.ClosePrices[c];
                    if (px > 0.0)
                    {
                        sum += Math.Log(px);
                        used++;
                    }
                }
            }
            return used > 0 ? sum / used : double.NaN;
        }
    }

    private sealed class TimeBarParquetWriter : IDisposable
    {
        private readonly int _batchSize;
        private readonly FileStream _stream;
        private readonly ParquetWriter _writer;
        private readonly DataField[] _fields;

        private readonly List<string> _symbol = new();
        private readonly List<DateTime> _openTime = new();
        private readonly List<DateTime> _closeTime = new();
        private readonly List<double> _open = new();
        private readonly List<double> _high = new();
        private readonly List<double> _low = new();
        private readonly List<double> _close = new();
        private readonly List<long> _tickVolume = new();

        public TimeBarParquetWriter(string outputDirectory, string symbol, DateTime serverTime, DateTime localTime, int batchSize)
        {
            if (batchSize < 1)
                throw new ArgumentOutOfRangeException(nameof(batchSize), batchSize, "Batch size must be at least 1.");

            _batchSize = batchSize;
            Directory.CreateDirectory(outputDirectory);

            var sanitizedSymbol = SanitizeSymbol(symbol);
            var serverStamp = serverTime.ToString("yyyyMMdd_HHmmss");
            var localStamp = localTime.ToString("yyyyMMdd_HHmmss");
            var path = Path.Combine(outputDirectory, $"timebars_{sanitizedSymbol}_{serverStamp}_{localStamp}.parquet");

            _fields = new DataField[]
            {
                new DataField<string>("Symbol"),
                new DataField<DateTime>("OpenTime"),
                new DataField<DateTime>("CloseTime"),
                new DataField<double>("Open"),
                new DataField<double>("High"),
                new DataField<double>("Low"),
                new DataField<double>("Close"),
                new DataField<long>("TickVolume")
            };

            _stream = new FileStream(path, FileMode.Create, FileAccess.Write);
            _writer = ParquetWriter.CreateAsync(new ParquetSchema(_fields), _stream).GetAwaiter().GetResult();
            _writer.CompressionMethod = CompressionMethod.Zstd;
        }

        public void Append(TimeBarRecord bar)
        {
            if (bar.CloseTime <= DateTime.MinValue.AddYears(1) || bar.CloseTime > DateTime.UtcNow.AddYears(1))
                return;
            if (bar.High < Math.Max(bar.Open, bar.Close) || bar.Low > Math.Min(bar.Open, bar.Close))
                return;

            _symbol.Add(bar.Symbol);
            _openTime.Add(bar.OpenTime);
            _closeTime.Add(bar.CloseTime);
            _open.Add(bar.Open);
            _high.Add(bar.High);
            _low.Add(bar.Low);
            _close.Add(bar.Close);
            _tickVolume.Add(bar.TickVolume);

            if (_symbol.Count >= _batchSize)
                Flush();
        }

        public void Dispose()
        {
            Flush();
            _writer.Dispose();
            _stream.Flush();
            _stream.Dispose();
        }

        private void Flush()
        {
            if (_symbol.Count == 0)
                return;

            using var groupWriter = _writer.CreateRowGroup();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[0], _symbol.ToArray())).GetAwaiter().GetResult();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[1], _openTime.ToArray())).GetAwaiter().GetResult();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[2], _closeTime.ToArray())).GetAwaiter().GetResult();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[3], _open.ToArray())).GetAwaiter().GetResult();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[4], _high.ToArray())).GetAwaiter().GetResult();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[5], _low.ToArray())).GetAwaiter().GetResult();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[6], _close.ToArray())).GetAwaiter().GetResult();
            groupWriter.WriteColumnAsync(new DataColumn(_fields[7], _tickVolume.ToArray())).GetAwaiter().GetResult();
            Clear();
        }

        private void Clear()
        {
            _symbol.Clear();
            _openTime.Clear();
            _closeTime.Clear();
            _open.Clear();
            _high.Clear();
            _low.Clear();
            _close.Clear();
            _tickVolume.Clear();
        }

        private static string SanitizeSymbol(string symbol)
        {
            return symbol.ToLowerInvariant().Replace(" ", "_").Replace("(", "").Replace(")", "");
        }
    }

    private sealed record TimeBarRecord(
        string Symbol,
        DateTime OpenTime,
        DateTime CloseTime,
        double Open,
        double High,
        double Low,
        double Close,
        long TickVolume);
}
