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
    StrategyHostParity,
    // EXP-013 (CF-MR-004): native cTrader pending-order execution. The robot places REAL
    // limit orders and cTrader's backtester (m1) owns fill resolution — no self-adjudicated
    // fills on aggregated bars (the Route-A faithful build; see CrossInstrumentSpreadPlanner).
    NativeOrders
}

public enum XenStrategy
{
    MaCrossover,
    AvwapBaseline,
    Donchian20,
    Rsi2Fade,
    CrossDomainMrLimit,
    CrossInstrumentSpreadMr,
    // EXP-019 (CF-VOLHARV-001): seeded random-timing fixed-hold market legs — runs in
    // Mode=NativeOrders only (see Xen.RandomHold.cs).
    RandomHold,
    // EXP-020 (CF-VOLHARV-001 HYP-002): structure harvest arms — Mode=NativeOrders only
    // (see Xen.StructureHarvest.cs). RebalanceHarvest = ARM R; GridHarvest = ARM G.
    RebalanceHarvest,
    GridHarvest,
    // EXP-025 (CF-HTFDI-001/HYP-A): CTRL-02 X-bar breakout gated by last-closed 1h ±DI.
    // Exits E0/E2/E3/E5/E6 run in Mode=StrategyHost (HtfDiBreakoutModel); exits E1/E4
    // (native stop/limit brackets, m1 fills) run in Mode=NativeOrders (Xen.HtfDiNative.cs).
    HtfDiBreakout
}

[Robot(AccessRights = AccessRights.FullAccess, AddIndicators = false, DefaultTimeFrame="Minute")]
public partial class Xen : Robot
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

    // EXP-013 (CF-MR-004): Cross-instrument spread MR series. S5_SPREAD = rolling-β basket;
    // S6_PAIR = fixed-ratio pair (β=1, single peer); S7_BASKET = fixed-weight basket (equal);
    // S8_RVINDEX = relative-value index (pair + rolling median). 4h anchor domain only, no lower-domain.
    [Parameter("CIS Series", DefaultValue = "S5_SPREAD")]
    public string CisSeries { get; set; } = "S5_SPREAD";

    // EXP-014 (CF-MR-004 HYP-002) — reentry axis. "none" = single open leg, cancel all on fill
    // (binding PRIMARY); "allow" = refill the base band (z*=2.0), concurrent legs; "extend" = arm
    // the z*∈{2.0,2.5,3.0} ladder, one fill per deeper level, concurrent legs. Multi-leg netting
    // engine handles all three (proposal /REENTRY).
    [Parameter("CIS Reentry", DefaultValue = "none")]
    public string CisReentry { get; set; } = "none";

    // EXP-014 A/B recalc→fill arm. false = R (refresh: re-arm the bracket each 4h bar);
    // true = S (static: place the bracket once when flat, leave until filled/horizon). Lifecycle-
    // changing → a separate labeled run per arm (design §6).
    [Parameter("CIS Static Arm", DefaultValue = false)]
    public bool CisStaticArm { get; set; }

    // DEPRECATED (HYP-003 / amendment-003): the fix/trail split is removed — single-leg exit is ALWAYS the
    // moving-mean form-2 (refresh to exp(anchorLog) each bar) + form-1, no horizon. This param is retained
    // for back-compat only and no longer affects the single-leg exit. (Was: false=fixed entry-referential
    // limit, true=trailing moving anchor.)
    [Parameter("CIS Trail", DefaultValue = false)]
    public bool CisTrail { get; set; }

    // HYP-003 (amendment-003): both-leg variant. When true, an S8 spread signal opens a grouped spread
    // position — short the traded instrument AND long each equal-weight basket mate — held as one unit and
    // exited jointly on form-1 (spread reverts through the mean). Captures peer-side reversion the single
    // traded-instrument limit cannot (audit M1). reentry is forced to none for both-leg.
    [Parameter("CIS Both Leg", DefaultValue = false)]
    public bool CisBothLeg { get; set; }

    // HYP-003 (amendment-003): entry deviation-magnitude axis. Base band = CisZStar·σ; the reentry
    // ladder is derived as {z*, z*+0.5, z*+1.0}. Axis values: 2.0 (default) and 1.5 (more aggressive,
    // less-extreme entry). Threaded to the planner + the robot's ladder.
    [Parameter("CIS ZStar", DefaultValue = 2.0)]
    public double CisZStar { get; set; } = 2.0;

    // HYP-003 (amendment-003 A10) — both-leg entry sub-axis (only when CisBothLeg=true).
    // "market" = market-fill all N+1 legs the instant the ≤t-1-close S8 spread breaches ±z*·σ
    //   (clean group, no desync). "limit" = ATOMIC: A rests band-limits at exp(anchorLog±z*·σ),
    //   mates rest limits at their ≤t-1 close on A-fill; if the full N+1 group is not filled by the
    //   next domain bar, market-unwind any filled legs (flat) — only a full-group fill survives.
    [Parameter("CIS Both Leg Entry", DefaultValue = "market")]
    public string CisBothLegEntry { get; set; } = "market";

    // HYP-004 (amendment-004) — single-leg EXIT-SET axis. "moving" = E0 faithful moving-mean
    // (form-1 event reversion + refreshing form-2 at the moving anchor; the EXP-014b baseline).
    // "frozen_tp" = E1: TP limit frozen at the entry-time anchor a_entry per leg (set at the fill,
    // never modified); no SL, no time-stop, form-1 disabled. "frozen_tp_sl" = E2: E1 + SL stop
    // frozen at the symmetric outward barrier o±D (o = entry fill, D = |o − a_entry|).
    // "bracket" = E3: E2 + hard time-stop ⌈3·HL_entry⌉ domain bars (cap 48) → market close.
    // E3 reproduces the symmetry two-barrier availability race exactly. Single-leg only.
    // EXP-018 (CF-MR-005 HYP-003) — arm A "harvest" exit set: refreshing form-2 TP at the MOVING
    // anchor mean + per-leg ⌈3·HL_entry⌉ time-stop (cap 48), NO stop-loss, NO form-1 event exit
    // (design §4 arm A names exactly {moving TP, time-stop}). Arm B ("braked") = existing "bracket".
    [Parameter("CIS Exit Set", DefaultValue = "moving")]
    public string CisExitSet { get; set; } = "moving";

    // EXP-018 CAUSAL-MISALIGNMENT TRIPWIRE (design §5, entry-delay +1): >0 delays the DECISION
    // state (bracket + logClose) by N completed domain bars — arming, exits, TP refresh, and leg
    // provenance all condition on t-1-N instead of t-1. 0 = live (identical code path, zero drift).
    [Parameter("CIS Entry Delay Bars", DefaultValue = 0)]
    public int CisEntryDelayBars { get; set; }

    // EXP-018 RANDOM-TIMING LADDER DESTROY (design §5, operator-resolved 2026-07-04): path to a
    // pre-generated seeded schedule CSV (open_time_utc,level,dir,hold_bars). When set, the robot
    // places NO band limits: it market-enters at each scheduled bar's next open and market-exits
    // after the scheduled matched hold (drawn from the live arm's realized per-level BarsHeld) —
    // an exposure-matched carry read. No TP, no form-1, no SL (L-08: exits must not re-import the
    // anchor, or near-anchor random entries close instantly and bias the null toward collapse).
    [Parameter("CIS Schedule Path", DefaultValue = "")]
    public string CisSchedulePath { get; set; } = "";

    // EXP-019 (CF-VOLHARV-001) — RandomHold schedule CSV (open_time_utc,level,dir,hold_bars;
    // level unused/0; hold ∈ {6,12,24,48}), pre-generated from (seed, engine bar calendar) only —
    // never prices. EMPTY = calendar-emission run: no orders, per-bar records only (the calendar
    // the schedule generator consumes; deviation D1 in Xen.RandomHold.cs).
    [Parameter("RH Schedule Path", DefaultValue = "")]
    public string RhSchedulePath { get; set; } = "";

    // EXP-019 provenance label only (the schedule is already fully determined by its CSV): the
    // generator seed recorded into run_metadata so each of the 25 seeded runs is identifiable.
    [Parameter("RH Seed", DefaultValue = 0)]
    public int RhSeed { get; set; }

    // EXP-019 inventory cap: a scheduled entry landing when this many legs are open is SKIPPED
    // (logged cap_skip), never deferred — deterministic (design §4).
    [Parameter("RH Max Open Legs", DefaultValue = 6)]
    public int RhMaxOpenLegs { get; set; } = 6;

    // EXP-020 (CF-VOLHARV-001 HYP-002) — structure-harvest twin flag. ARM R: true = the
    // unrebalanced same-mix B&H twin (init only, never rebalances). ARM G: true = the
    // direction-INVERTED momentum grid (stop entries, unwind one level away from A).
    [Parameter("SH Twin", DefaultValue = false)]
    public bool ShTwin { get; set; }

    // EXP-020 ARM R band b_w in WEIGHT terms (A1 table, candidate-blind from EXP-019;
    // tripwire 2: values byte-diffed against derive_exp020_params.py output).
    [Parameter("SH Band W", DefaultValue = 0.0)]
    public double ShBandW { get; set; }

    // EXP-020 ARM G grid spacing g in bps of the monthly anchor (A1 table; tripwire 2).
    [Parameter("SH Grid Bps", DefaultValue = 0.0)]
    public double ShGridBps { get; set; }

    // EXP-020 TRIPWIRE 1 (entry-delay +1): 1 delays every decision input (rebalance weight,
    // month-boundary reset, level arming) by one completed 4h bar. 0 = live, identical path.
    [Parameter("SH Delay Bars", DefaultValue = 0)]
    public int ShDelayBars { get; set; }

    // EXP-025 (CF-HTFDI-001/HYP-A) — HtfDiBreakout vehicle parameters (design §3).
    // X = breakout lookback (grid {2,3,4,5,8}); Hold = E0 fixed-hold bars (grid {12,24,36,48}).
    [Parameter("HTFDI X", DefaultValue = 3)]
    public int HtfX { get; set; } = 3;

    [Parameter("HTFDI Hold", DefaultValue = 24)]
    public int HtfHold { get; set; } = 24;

    // Exit object: e0 (fixed hold) | e2 (trailing X channel) | e3 (Heiken-Ashi trail) |
    // e5 (HTF-DI flip) | e6 (opposite breakout) run in StrategyHost; e1 (triple-barrier
    // TP 3.0x/SL 1.5x entry-frozen 1h ATR + 96-bar backstop) | e4 (SL 1.5x only + backstop)
    // require Mode=NativeOrders (native stop/limit, m1 fills — never StrategyHost self-fill).
    [Parameter("HTFDI Exit", DefaultValue = "e0")]
    public string HtfExit { get; set; } = "e0";

    // Gate arm: di (the vehicle) | adx (CTRL-NULLSENT ADX-only sentinel) | battery
    // (CTRL-RND-BATTERY seeded random direction on the DI-gated event timestamps) |
    // state (CTRL-REF-RANDOM substrate: per-bar HTF state emission, no trades).
    [Parameter("HTFDI Gate", DefaultValue = "di")]
    public string HtfGate { get; set; } = "di";

    // CTRL-RND-BATTERY pre-registered seeds 1001-1025 (design §6). Required iff Gate=battery.
    [Parameter("HTFDI Battery Seed", DefaultValue = 0)]
    public int HtfBatterySeed { get; set; }

    // EXP-025 LEAK TRIPWIRE (design §6): rolls the ENTIRE 1h DI/ATR/regime stream back by
    // this many CLOSED 1h bars (+60 = the registered phase-shift arm). 0 = live.
    [Parameter("HTFDI Shift Bars", DefaultValue = 0)]
    public int HtfShiftBars { get; set; }

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

        if (Mode == XenMode.NativeOrders)
        {
            try
            {
                if (Strategy == XenStrategy.RandomHold)
                    StartRandomHold();
                else if (Strategy == XenStrategy.RebalanceHarvest)
                    StartRebalanceHarvest();
                else if (Strategy == XenStrategy.GridHarvest)
                    StartGridHarvest();
                else if (Strategy == XenStrategy.HtfDiBreakout)
                    StartHtfDiNative();
                else
                    StartNativeOrders();
            }
            catch (Exception ex)
            {
                Print("Xen native-orders failed to start: {0}", ex.Message);
                Stop();
            }
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
        if (Mode == XenMode.NativeOrders)
        {
            if (_rhReady)
                RunRandomHoldOnBar();
            else if (_rebReady)
                RunRebalanceHarvestOnBar();
            else if (_gridReady)
                RunGridHarvestOnBar();
            else if (_hdReady)
                RunHtfDiNativeOnBar();
            else if (_nativeReady)
                RunNativeOrdersOnBar();
            return;
        }
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
            if (Mode == XenMode.NativeOrders)
            {
                if (_rhReady)
                    FlushRandomHoldCensored();   // EXP-019: censored open legs (should be empty — D3)
                else if (_rebReady)
                    FlushRebalanceSummary();     // EXP-020 ARM R: no leg ledger; summary print only
                else if (_gridReady)
                    FlushGridCensored();         // EXP-020 ARM G: fence-open inventory → censored rows
                else if (_hdReady)
                    FlushHtfDiNativeCensored();  // EXP-025 E1/E4: fence-open bracket leg → censored row
                else
                    FlushOpenLegsAsCensored();   // EXP-014b: emit still-open legs as censored open_at_end rows
                _strategyWriter?.Dispose();
            }
            else if (IsStrategyHostMode())
            {
                if (!_stoppingAtFence && !_strategyFixedRunCompleted)
                    FlushStrategyDomainBars();
                // EXP-029: serialize the AVWAP per-bounce detail table so the Python
                // parity harness can rebuild matched controls (no signal oracle).
                if (_strategyModel is AvwapBounceModel avwapModel)
                    _strategyWriter?.SetAvwapEventDetails(avwapModel.EventDetails);
                // EXP-025: a fence-open trade is emitted as a censored open_at_end row.
                if (_strategyModel is HtfDiBreakoutModel htfdiModel && _strategyWriter is not null)
                {
                    htfdiModel.FlushOpenAsCensored(DomainLabel(DomainMinutes));
                    foreach (var row in htfdiModel.DrainTradeRows())
                        _strategyWriter.AppendCisTrade(row);
                }
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
            if (_strategyModel is HtfDiBreakoutModel htfdi)
                foreach (var row in htfdi.DrainTradeRows())
                    _strategyWriter.AppendCisTrade(row);
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
        {
            _strategyWriter.Append(update);
            if (_strategyModel is HtfDiBreakoutModel htfdi)
                foreach (var row in htfdi.DrainTradeRows())
                    _strategyWriter.AppendCisTrade(row);
        }

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
            // CF-MR-004 runs via native cTrader pending orders (Mode=NativeOrders), not as a
            // self-adjudicating StrategyHost model — see StartNativeOrders / the planner.
            XenStrategy.CrossInstrumentSpreadMr => throw new InvalidOperationException(
                "CrossInstrumentSpreadMr runs in Mode=NativeOrders (native pending orders), not StrategyHost."),
            XenStrategy.RandomHold => throw new InvalidOperationException(
                "RandomHold (EXP-019) runs in Mode=NativeOrders (native market orders), not StrategyHost."),
            XenStrategy.RebalanceHarvest or XenStrategy.GridHarvest => throw new InvalidOperationException(
                "RebalanceHarvest/GridHarvest (EXP-020) run in Mode=NativeOrders, not StrategyHost."),
            XenStrategy.HtfDiBreakout => CreateHtfDiBreakoutModel(),
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

    private ISignalModel CreateHtfDiBreakoutModel()
    {
        if (DomainMinutes != 5)
            throw new InvalidOperationException(
                $"HtfDiBreakout (EXP-025) is 1h/5min only; DomainMinutes must be 5, got {DomainMinutes}.");
        var exit = ParseHtfExit(HtfExit);
        if (exit is null)
            throw new InvalidOperationException(
                $"HTFDI Exit '{HtfExit}' runs in Mode=NativeOrders (native stop/limit, m1 fills — L-14), not StrategyHost.");
        var gate = ParseHtfGate(HtfGate);
        return new HtfDiBreakoutModel(HtfX, HtfHold, exit.Value, gate, HtfBatterySeed, HtfShiftBars);
    }

    // e1/e4 → null (NativeOrders-only); anything unknown throws.
    private static HtfDiExit? ParseHtfExit(string raw)
    {
        return raw.Trim().ToLowerInvariant() switch
        {
            "e0" => HtfDiExit.E0FixedHold,
            "e2" => HtfDiExit.E2TrailXChannel,
            "e3" => HtfDiExit.E3HeikenAshi,
            "e5" => HtfDiExit.E5DiFlip,
            "e6" => HtfDiExit.E6OppositeBreak,
            "e1" or "e4" => null,
            _ => throw new InvalidOperationException($"Unknown HTFDI Exit '{raw}' (e0|e1|e2|e3|e4|e5|e6).")
        };
    }

    private static HtfDiGateMode ParseHtfGate(string raw)
    {
        return raw.Trim().ToLowerInvariant() switch
        {
            "di" => HtfDiGateMode.Di,
            "adx" => HtfDiGateMode.AdxSentinel,
            "battery" => HtfDiGateMode.Battery,
            "state" => HtfDiGateMode.StateOnly,
            _ => throw new InvalidOperationException($"Unknown HTFDI Gate '{raw}' (di|adx|battery|state).")
        };
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
            case XenStrategy.CrossInstrumentSpreadMr:
                parameters["series"] = CisSeries;
                parameters["execution"] = "native_ctrader_pending_orders_m1";
                parameters["entry"] = "resting_bracket_no_z_gate";  // limits at anchor±Z*σ; band IS the trigger
                parameters["w_z"] = CrossInstrumentSpreadPlanner.WZ;
                parameters["z_star"] = CisZStar;
                parameters["w_a"] = CrossInstrumentSpreadPlanner.Wa;
                parameters["median_w"] = CrossInstrumentSpreadPlanner.MedianW;  // EXP-014 F-fix: 90 (S8 basket−median-90)
                parameters["direction"] = "fade_both_directions";
                parameters["domain"] = _nativeDomain;             // HYP-003: 1h or 4h decision domain
                // HYP-004 (amendment-004) — exit-set axis: moving (E0) | frozen_tp | frozen_tp_sl | bracket.
                parameters["exit_set_axis"] = _exitSet;
                parameters["exit_set"] = _scheduleMode
                    ? "random_timing_matched_hold_market_exit_only"
                    : _harvestExit
                        ? "harvest_moving_tp+time_stop_3xHL_cap48_no_sl_no_form1"
                        : _frozenExit
                            ? "frozen_tp_at_entry_anchor" + (_frozenSl ? "+sl_outward_oD" : "")
                              + (_frozenTimeStop ? "+time_stop_3xHL_cap48" : "")
                            : "form1_event_reversion+form2_moving_mean_limit";  // E0: no horizon
                parameters["form2_exit"] = CisBothLeg
                    ? (_harvestExit
                        ? "both_leg_joint_form1_at_spread_mean+group_time_stop_3xHL_cap48"
                        : "both_leg_joint_form1_at_spread_mean_no_separate_form2")
                    : (_frozenExit
                        ? "tp_frozen_at_entry_time_anchor_never_modified"
                        : "moving_anchor_mean_modify_tp_each_bar_favorable_asserted");
                parameters["form1"] = _frozenExit || _harvestExit || _scheduleMode
                    ? (CisBothLeg && _harvestExit
                        ? "both_leg_joint_spread_reversion_is_the_harvest_exit"
                        : "disabled_this_exit_set")
                    : "spread_reverted_through_mean_close_next_bar_open";
                // EXP-018 control-arm provenance
                parameters["entry_delay_bars"] = CisEntryDelayBars;
                parameters["schedule_path"] = CisSchedulePath;
                parameters["schedule_mode"] = _scheduleMode;
                parameters["both_leg"] = CisBothLeg
                    ? "short_instrument_plus_long_equal_weight_basket_grouped_spread_position"
                    : "single_leg_traded_instrument_only";
                parameters["open_at_end"] = "censored_disclosed_excluded_from_realized_referee";
                parameters["reentry"] = CisBothLeg ? "none" : CisReentry;   // both-leg forces none
                parameters["both_leg_entry"] = CisBothLeg ? _bothLegEntry : "n/a_single_leg";  // A10 market|limit
                parameters["ladder_z_stars"] = string.Join(";", _ladderZStars);
                parameters["recalc_fill_arm"] = "R_refresh_per_bar";        // HYP-003: R only (S dropped)
                parameters["target"] = "form2_limit_at_moving_anchor_mean";
                parameters["breach_policy"] = "skip_le_t1_close+disclose_live_bidask";
                parameters["min_mate_rule"] = "valid_basket_bar_requires_full_predeclared_membership";
                parameters["trend_measure"] = "ema20_minus_ema50_over_sigma_close_wz";
                parameters["vol_regime"] = "spread_sigma_tercile_over_trailing_500_domain_bars";
                parameters["basket_mates"] = BasketMates;
                parameters["basket_phase_shift_bars"] = BasketPhaseShiftHours;  // 0 live; >0 leak tripwire (4h bars)
                break;
            case XenStrategy.RandomHold:
                // EXP-019 (CF-VOLHARV-001) provenance — the schedule fully determines behavior.
                parameters["execution"] = "native_ctrader_market_orders_m1";
                parameters["schedule_path"] = RhSchedulePath;
                parameters["schedule_seed"] = RhSeed;
                parameters["calendar_emission_mode"] = string.IsNullOrWhiteSpace(RhSchedulePath);
                parameters["max_open_legs"] = RhMaxOpenLegs;
                parameters["entry"] = "unconditional_scheduled_market_at_bar_open";
                parameters["exit_set"] = "matched_hold_market_only_no_tp_no_sl_no_refresh";
                parameters["hold_grid"] = "6;12;24;48_round_robin_in_schedule_order";
                parameters["sizing"] = "fixed_min_volume_never_varied";
                parameters["cap_policy"] = "skip_logged_cap_skip_never_deferred";
                parameters["open_at_end"] = "censored_disclosed_excluded_from_realized";
                break;
            case XenStrategy.HtfDiBreakout:
                // EXP-025 (CF-HTFDI-001/HYP-A) provenance — design §3 vehicle table.
                parameters["signal"] = "ctrl02_x_bar_breakout_confirmed_close_enter_next_open";
                parameters["x"] = HtfX;
                parameters["hold_bars"] = HtfHold;
                parameters["exit"] = HtfExit;
                parameters["gate"] = HtfGate;
                parameters["battery_seed"] = HtfBatterySeed;
                parameters["htf"] = "clock_aligned_utc_1h_from_5min_wilder_dmi14_atr14";
                parameters["htf_gate_rule"] = "last_closed_1h_bar_closetime_lt_entry_open_code_asserted";
                parameters["htf_warmup_closed_bars"] = WilderHtfState.MinClosedBars;
                parameters["atr_regime"] = "trailing_2016_closed_1h_atr_terciles_unset_until_full";
                parameters["adx_sentinel_median"] = "trailing_2016_closed_1h_adx_median_D1";
                parameters["phase_shift_bars"] = HtfShiftBars;   // 0 live; 60 = leak tripwire arm
                parameters["position"] = "one_at_a_time_fixed_unit_signals_ignored_while_open";
                parameters["open_at_end"] = "censored_disclosed_excluded_from_realized";
                break;
            case XenStrategy.RebalanceHarvest:
                // EXP-020 ARM R provenance (design §3 + A1 params; tripwire 2 byte-diff).
                parameters["execution"] = "native_ctrader_market_orders_m1";
                parameters["arm"] = ShTwin ? "R_twin_unrebalanced_bh_mix" : "R_banded_rebalance";
                parameters["w_star"] = 0.5;
                parameters["band_w"] = ShBandW;
                parameters["entry_delay_bars"] = ShDelayBars;      // 0 live; 1 tripwire 1
                parameters["trigger"] = "abs_weight_dev_ge_band_at_t-1_close_trade_next_open";
                parameters["estimand"] = "per_bar_path_PortWeight_Units_Cash+trade_blotter_no_leg_ledger";
                parameters["sizing"] = "virtual_portfolio_real_position_ge_20_vol_steps_per_trade";
                break;
            case XenStrategy.GridHarvest:
                // EXP-020 ARM G provenance (design §3 + 2026-07-05 twin clarification; A1 params).
                parameters["execution"] = "native_ctrader_pending_orders_m1";
                parameters["arm"] = ShTwin ? "G_twin_inverted_momentum_grid" : "G_mr_grid";
                parameters["anchor"] = "previous_calendar_month_close_monthly_reset_inventory_carried";
                parameters["grid_bps"] = ShGridBps;
                parameters["levels_per_side"] = GridLevelsPerSide;
                parameters["max_open_legs"] = GridMaxOpenLegs;
                parameters["entry_delay_bars"] = ShDelayBars;      // 0 live; 1 tripwire 1
                parameters["unwind"] = ShTwin
                    ? "tp_one_level_AWAY_from_anchor_stop_entries"
                    : "tp_one_level_TOWARD_anchor_limit_entries";
                parameters["cap_policy"] = "level_order_not_placed_at_cap_logged_cap_skip";
                parameters["open_at_end"] = "censored_disclosed_excluded_from_realized";
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

    // =======================================================================
    // EXP-013 (CF-MR-004) — NATIVE-ORDER EXECUTION (Route A).
    // The robot decides on the 4h anchor grid (≤ t-1) and places REAL cTrader
    // pending limit orders; cTrader's m1 backtester owns fill resolution. No
    // self-adjudicated fills on aggregated bars. Emission = per-4h-bar position
    // record with ENGINE fill prices (EntryFillPrice/ExitFillPrice), so the Python
    // suite adjudicates on the engine's realized fills. Holdout fence = the backtest
    // --end date; every emitted SourceCloseTime is asserted < AnalysisEndUtc.
    // =======================================================================
    private const string NativeStrategyName = "cross_instrument_spread_mr";
    // EXP-014 faithful full-exit constants. Ladder z*-levels for /REENTRY=extend (base first);
    // trend EMA fast/slow + σ_close window; vol-regime tercile history window (design §6/§7).
    // HYP-003: reentry ladder derived from the base z* axis at start = {z*, z*+0.5, z*+1.0}
    // (z*=2.0 → {2.0,2.5,3.0}; z*=1.5 → {1.5,2.0,2.5}). Set in StartNativeOrders from CisZStar.
    private double[] _ladderZStars = { 2.0, 2.5, 3.0 };
    private const int TrendFast = 20;
    private const int TrendSlow = 50;
    private const int TrendSigmaWindow = CrossInstrumentSpreadPlanner.WZ;  // σ_close window = WZ (200)
    private const int VolHistWindow = 500;    // trailing spread-σ history for the vol-regime tercile
    private CrossInstrumentSpreadPlanner _planner = null!;
    private CrossInstrumentBasketFeed _cisFeed = null!;
    private Bars _h4 = null!;
    private bool _nativeReady;
    private bool _nativeStopping;
    private int _h4Index = -1;                 // index of last processed completed domain bar
    private DateTime? _lastProcessedH4Open;
    private string _nativeDomain = "4h";        // set in StartNativeOrders = DomainLabel(DomainMinutes)
    private int _nativeDomainMinutes = 240;     // HYP-003: 60 (1h) or 240 (4h)
    private string _orderLabel = "";
    private double _orderVolume;
    private long _nativeTradeSeq;
    private SpreadBracket _lastBracket;
    private List<SignalEventRecord> _periodEvents = new();
    private List<StrategyTradeRecord> _periodTrades = new();

    // --- EXP-014 reentry / arm mode (resolved once at start) -------------------------------
    private string _reentryMode = "none";      // none | allow | extend
    private bool _staticArm;                   // true = S (place-once); false = R (refresh/bar)
    private bool _bracketPlacedStatic;         // S arm: whether the resting bracket is currently placed
    private bool _trail;                       // EXP-014b: true = trailing form-2 (moving anchor); false = fixed exit

    // --- HYP-004 exit-set axis (resolved once at start) --------------------------------------
    // moving (E0) | frozen_tp (E1) | frozen_tp_sl (E2) | bracket (E3). Frozen modes bypass the
    // moving form-2 refresh AND form-1 entirely; each leg carries its own bracket frozen at fill.
    private string _exitSet = "moving";
    private bool _frozenExit;                  // any of E1/E2/E3
    private bool _frozenSl;                    // E2/E3: SL at the outward barrier o±D
    private bool _frozenTimeStop;              // E3: ⌈3·HL_entry⌉ time-stop (cap 48)
    private bool _harvestExit;                 // EXP-018 arm A: moving TP + time-stop, no SL/form-1
    private const int FrozenHorizonCap = 48;   // matches the availability race H_CAP

    // --- EXP-018 decision-state delay (entry-delay tripwire) --------------------------------
    // All DECISIONS (arming, form-1 test, TP refresh, leg provenance) read _decisionBracket /
    // _decisionLogClose; the per-bar EMISSION keeps the current bar's bracket (provenance of the
    // bar itself). delay=0 → decision state == current state (bit-identical live path).
    private SpreadBracket _decisionBracket = new() { Warmup = true };
    private double _decisionLogClose = double.NaN;
    private readonly Queue<(SpreadBracket Bracket, double LogClose)> _delayQueue = new();

    // --- EXP-018 random-timing schedule state ------------------------------------------------
    private bool _scheduleMode;
    private sealed record ScheduledEntry(DateTime OpenTimeUtc, int Level, int Dir, int HoldBars);
    private List<ScheduledEntry> _schedule = new();
    private int _scheduleCursor;

    // --- EXP-014 multi-leg netting engine --------------------------------------------------
    // One NativeLeg per open position (concurrent under allow/extend; ≤1 under none). Matched to
    // the cTrader Position by Id. Exit reason is staged in _pendingCloseReason before a market
    // ClosePosition and consumed by the (possibly async) close event.
    private sealed class NativeLeg
    {
        public long PositionId;
        public int Dir;                        // +1 long / −1 short
        public int LadderLevel;                // 0 = z*=2.0, 1 = 2.5, 2 = 3.0
        public double EntryFill;
        public int EntryH4Index;
        public DateTime EntryTime;
        public double EntryZ, EntrySpread, EntryAnchorPrice, EntrySigma;
        public double EntryTrendZ; public int EntryTrendDir; public int EntryVolRegime;
        // EXP-014b: entry-referential fixed exit = EntryFill·exp(dir·band), band = Z*·σ locked at the arm
        // bar. Set once at open; used as the fixed form-2 TP (NaN under trailing). MAE/MFE track the
        // dir-signed adverse/favorable excursion over the hold for the forensic per-trade lens.
        public double FixedExit = double.NaN;
        public double MaeBps;                  // most adverse (min dir-signed return, bps)
        public double MfeBps;                  // most favorable (max dir-signed return, bps)
        // HYP-004 frozen bracket (E1-E3): FixedExit doubles as the frozen TP (= a_entry). SlPrice =
        // outward barrier o±D (NaN under E1/moving). HorizonBars = ⌈3·HL_entry⌉ cap 48 (0 = none).
        public double SlPrice = double.NaN;
        public int HorizonBars;
    }
    private readonly List<NativeLeg> _legs = new();
    private readonly Dictionary<long, string> _pendingCloseReason = new();
    // Closed-trade rows staged during a period (market + limit exits) and flushed to cis_trades in
    // EmitNativePosition with SourceCloseTime = the emitted bar's 4h closeTime (fence-consistent).
    private sealed class ClosedTrade
    {
        public NativeLeg Leg = null!;
        public double ExitFill;
        public string Reason = "";
        public DateTime ExitTime;
        public double ExitAnchorPrice;
        public double ExitSpread;
        public int BarsHeld;
    }
    private readonly List<ClosedTrade> _periodClosed = new();
    // Emission direction convention (CF-MR-003): the entry bar carries the entered dir; hold/exit
    // bars carry the dir held into the period. Concurrent legs are always same-side, so net sign
    // == that side. For the binding PRIMARY (reentry=none) this reduces to the single-leg case.
    private int _periodStartSign;              // net sign of legs held into the period being emitted
    private int _periodEntryDir;               // dir of any entry that filled during this period (0 if none)
    private double _pendingEntryFill = double.NaN;   // representative last entry fill this period (emit)
    private double _pendingExitFill = double.NaN;    // representative last exit fill this period (emit)

    // --- EXP-014 conditioner state (trend on traded 4h; vol regime on spread-σ history) ----
    private readonly List<double> _h4Close = new();     // trailing traded closes for σ_close(WZ)
    private double _ema20 = double.NaN;
    private double _ema50 = double.NaN;
    private readonly List<double> _sigmaHist = new();   // trailing spread-σ for the vol tercile
    private double _trendZ = double.NaN;
    private int _trendDir;
    private int _volRegime = -1;

    private void StartNativeOrders()
    {
        if (DomainMinutes != 240 && DomainMinutes != 60)
            throw new InvalidOperationException(
                $"NativeOrders CF-MR-004 (HYP-003) is 1h or 4h anchor; DomainMinutes must be 60 or 240, got {DomainMinutes}.");
        _nativeDomainMinutes = DomainMinutes;
        _nativeDomain = DomainLabel(DomainMinutes);
        var nativeTimeFrame = DomainMinutes == 60 ? TimeFrame.Hour : TimeFrame.Hour4;
        if (!TryParseAnalysisEndUtc(AnalysisEndUtc, out var analysisEndUtc))
            throw new InvalidOperationException("Analysis End UTC must be explicit, e.g. 2026-01-01T00:00:00Z.");

        _planner = new CrossInstrumentSpreadPlanner(CisSeries, CisZStar);   // throws on unknown series
        _reentryMode = (CisReentry ?? "none").Trim().ToLowerInvariant();
        if (_reentryMode != "none" && _reentryMode != "allow" && _reentryMode != "extend")
            throw new InvalidOperationException(
                $"CIS Reentry must be none|allow|extend, got '{CisReentry}'.");
        _staticArm = CisStaticArm;
        _trail = CisTrail;
        _exitSet = (CisExitSet ?? "moving").Trim().ToLowerInvariant();
        if (_exitSet != "moving" && _exitSet != "frozen_tp" && _exitSet != "frozen_tp_sl"
            && _exitSet != "bracket" && _exitSet != "harvest")
            throw new InvalidOperationException(
                $"CIS Exit Set must be moving|frozen_tp|frozen_tp_sl|bracket|harvest, got '{CisExitSet}'.");
        _harvestExit = _exitSet == "harvest";
        _frozenExit = _exitSet != "moving" && !_harvestExit;
        _frozenSl = _exitSet == "frozen_tp_sl" || _exitSet == "bracket";
        _frozenTimeStop = _exitSet == "bracket";
        if (_frozenExit && CisBothLeg)
            throw new InvalidOperationException("CIS Exit Set frozen modes are single-leg only (HYP-004).");
        if (CisEntryDelayBars < 0)
            throw new InvalidOperationException("CIS Entry Delay Bars must be >= 0.");
        if (!string.IsNullOrWhiteSpace(CisSchedulePath))
        {
            _schedule = LoadSchedule(CisSchedulePath.Trim());
            _scheduleMode = true;
            if (CisEntryDelayBars > 0)
                throw new InvalidOperationException(
                    "Schedule mode and entry-delay are separate control arms — do not combine.");
        }
        var z0 = CisZStar > 0.0 ? CisZStar : CrossInstrumentSpreadPlanner.ZStar;
        _ladderZStars = new[] { z0, z0 + 0.5, z0 + 1.0 };   // HYP-003 base-z* + reentry ladder
        _bothLeg = CisBothLeg;                              // HYP-003 A10 — grouped-spread variant (Increment B)
        var mates = ParseMates(BasketMates);
        if (mates.Count == 0)
            throw new InvalidOperationException(
                "NativeOrders CF-MR-004 requires Basket Mates (basket for S5/S7/S8, single peer for S6).");
        _cisFeed = new CrossInstrumentBasketFeed(this, mates, BasketPhaseShiftHours, nativeTimeFrame);
        _h4 = MarketData.GetBars(nativeTimeFrame, SymbolName);
        _strategyFence = new HoldoutFence(analysisEndUtc);
        _strategyWriter = new StrategyRunParquetWriter(
            StrategyOutputDirectory, NativeStrategyName, SymbolName, _nativeDomain,
            _strategyFence, BuildStrategyParameters(null));
        _orderLabel = $"cis_{SanitizeLabel(SymbolName)}_{CisSeries}";
        _orderVolume = Symbol.NormalizeVolumeInUnits(Symbol.VolumeInUnitsMin);

        if (_bothLeg)
            InitBothLeg(mates, nativeTimeFrame);

        Positions.Opened += OnNativePositionOpened;
        Positions.Closed += OnNativePositionClosed;
        _nativeReady = true;

        Print(
            "Xen CF-MR-004 NativeOrders {0} for {1}: {2}/{3} mates; reentry={4}; arm={5}; exit_set={6}; phase_shift_bars={7}; AnalysisEndUtc={8:o}; out={9}",
            CisSeries, SymbolName, _cisFeed.ResolvedCount, mates.Count, _reentryMode,
            _staticArm ? "S_static" : "R_refresh", _exitSet, BasketPhaseShiftHours,
            _strategyFence.AnalysisEndUtc, _strategyWriter.RunDirectory);
    }

    private void RunNativeOrdersOnBar()
    {
        if (_nativeStopping)
            return;
        var latest = _h4.Count - 2;   // last fully-completed 4h bar
        if (latest <= _h4Index)
            return;
        for (var i = _h4Index + 1; i <= latest; i++)
            if (!ProcessCompletedH4Bar(i, armOrders: i == latest))
                return;   // hit fence
    }

    // Process one completed domain bar i: Observe (≤ i), update conditioners, apply the exit set to
    // open legs (form-1 event reversion at the moving mean; NO horizon), refresh the moving-mean form-2
    // TP each bar, emit the per-bar record, and (on the latest bar) re-arm. HYP-003: single-leg exit is
    // the moving-mean artifact (form-2 refreshes to exp(anchorLog) + form-1); the fixed exit is dropped.
    private bool ProcessCompletedH4Bar(int i, bool armOrders)
    {
        var openTime = _h4.OpenTimes[i];
        var closeTime = openTime.AddMinutes(_nativeDomainMinutes);
        if (_strategyFence!.ShouldStopBeforeProcessing(closeTime))
        {
            _nativeStopping = true;
            Stop();
            return false;
        }

        var close = _h4.ClosePrices[i];
        var logClose = close > 0.0 ? Math.Log(close) : double.NaN;
        var feedLog = _cisFeed.BasketLogAt(openTime);
        var mateCount = _cisFeed.LastMateCount;
        var mateGap = mateCount < _cisFeed.ExpectedMates;   // min-mate rule: basket bar invalid on any gap
        _planner.Observe(logClose, feedLog);
        _lastBracket = _planner.CurrentBracket();
        UpdateConditioners(close);

        // EXP-018 decision-state delay: decisions condition on the state N bars back (tripwire arm);
        // delay=0 → decision state == the just-observed state (live path, bit-identical to HYP-004).
        if (CisEntryDelayBars <= 0)
        {
            _decisionBracket = _lastBracket;
            _decisionLogClose = logClose;
        }
        else
        {
            _delayQueue.Enqueue((_lastBracket, logClose));
            if (_delayQueue.Count > CisEntryDelayBars)
            {
                var d = _delayQueue.Dequeue();
                _decisionBracket = d.Bracket;
                _decisionLogClose = d.LogClose;
            }
            else
            {
                _decisionBracket = new SpreadBracket { Warmup = true };
                _decisionLogClose = double.NaN;
            }
        }

        // HYP-003 A10 — both-leg grouped-spread path (Increment B). Fully self-contained; the
        // single-leg netting engine below is untouched. Shares Observe/conditioners/bracket above.
        if (_bothLeg)
        {
            ProcessBothLegBar(i, armOrders, logClose, close, mateCount, mateGap, closeTime);
            _h4Index = i;
            _lastProcessedH4Open = openTime;
            return true;
        }

        // Track per-leg adverse/favorable excursion at every completed bar's close (forensic lens).
        if (_legs.Count > 0)
            UpdateLegExcursions(close);

        // Proposal-faithful exits at THIS bar's boundary (open of i+1; open-to-open). form-1 = spread
        // reverted through mean → market close. NO horizon (unspecified in the proposal). A non-reverting
        // position rides until form-1/form-2 fires or the fence stops it (then censored, open_at_end).
        var form1Any = false;
        if (!_frozenExit && !_harvestExit && !_scheduleMode && armOrders && _legs.Count > 0
            && double.IsFinite(_decisionBracket.AnchorLog) && double.IsFinite(_decisionLogClose))
            form1Any = ApplyEventExits(i, _decisionLogClose);

        // HYP-004 E3 / EXP-018 arm A time-stop: close legs held ≥ their frozen ⌈3·HL_entry⌉
        // horizon at market (exit at next open). E1/E2 have no time exit; E0 uses form-1/form-2.
        if ((_frozenTimeStop || _harvestExit) && !_scheduleMode && armOrders && _legs.Count > 0)
            ApplyFrozenTimeStop(i);

        // EXP-018 random-timing arm: matched-hold market exits only (no TP/form-1/SL — L-08).
        if (_scheduleMode && armOrders && _legs.Count > 0)
            ApplyMatchedHoldExits(i);

        // Form-2 exit (E0 moving-mean + EXP-018 harvest). Each bar, modify every surviving leg's
        // TP to the moving anchor mean exp(anchorLog_t); favorable-asserted per (re)placement.
        // E1-E3 legs are never touched — their bracket is frozen at the fill (HYP-004).
        var refreshedTp = double.NaN;
        if (!_frozenExit && !_scheduleMode && armOrders && _legs.Count > 0 && !_decisionBracket.Warmup)
            refreshedTp = RefreshForm2Targets(close);

        EmitNativePosition(i, closeTime, mateCount, mateGap, refreshedTp, form1Any);
        _pendingEntryFill = double.NaN;
        _pendingExitFill = double.NaN;

        if (armOrders)
        {
            if (_scheduleMode)
                FireScheduledEntries(i);
            else
                RearmBracket(_decisionLogClose, mateGap);
        }

        _h4Index = i;
        _lastProcessedH4Open = openTime;
        return true;
    }

    private void EmitNativePosition(int i, DateTime closeTime, int mateCount, bool mateGap,
                                    double refreshedTp, bool form1Any)
    {
        var b = _lastBracket;
        var heldPosition = _periodEntryDir != 0 ? _periodEntryDir : _periodStartSign;
        var closeI = _h4.ClosePrices[i];

        // Base-level (z*=2.0) armed band prices + breach flags for emission (deeper ladder levels
        // are recorded per fill in cis_trades). Breach = binding ≤t-1-close test + live disclosure.
        double armSell = double.NaN, armBuy = double.NaN;
        bool breachSell = false, breachBuy = false, liveBreachSell = false, liveBreachBuy = false;
        if (!b.Warmup && double.IsFinite(b.AnchorLog) && b.Sigma > 0.0)
        {
            var band = _ladderZStars[0] * b.Sigma;
            armSell = Math.Exp(b.AnchorLog + band);
            armBuy = Math.Exp(b.AnchorLog - band);
            breachSell = armSell <= closeI;          // ≤ t-1 confirmed close (binding breach test)
            breachBuy = armBuy >= closeI;
            liveBreachSell = armSell <= Symbol.Bid;  // live bid/ask (disclosure)
            liveBreachBuy = armBuy >= Symbol.Ask;
        }

        // Aggregate intra-position MTM over surviving legs (L-09), marked at RealClose.
        double mtm = double.NaN;
        if (_legs.Count > 0)
        {
            var acc = 0.0; var n = 0;
            foreach (var leg in _legs)
                if (leg.EntryFill > 0.0) { acc += leg.Dir * (closeI - leg.EntryFill) / leg.EntryFill * 1e4; n++; }
            if (n > 0) mtm = acc;
        }

        var rec = new SignalPositionRecord(
            SourceCloseTime: closeTime, Domain: _nativeDomain, Strategy: NativeStrategyName,
            Position: heldPosition, SignalValue: b.Z,
            RealOpen: _h4.OpenPrices[i], RealHigh: _h4.HighPrices[i],
            RealLow: _h4.LowPrices[i], RealClose: closeI,
            Warmup: b.Warmup, IsFlat: heldPosition == 0,
            ExitFillPrice: _pendingExitFill, EntryFillPrice: _pendingEntryFill,
            Anchor: b.Warmup ? double.NaN : Math.Exp(b.AnchorLog),
            Dev: b.Spread, Z: b.Z, Vr: b.Vr, Hl: b.Hl, Beta: b.Beta,
            ArmSellPrice: armSell, ArmBuyPrice: armBuy, Sigma: b.Sigma, SpreadMean: b.Mean,
            MateCount: mateCount, MateExpected: _cisFeed.ExpectedMates, MateGap: mateGap,
            TrendZ: _trendZ, TrendDir: _trendDir, VolRegime: _volRegime,
            BreachSkipSell: breachSell, BreachSkipBuy: breachBuy,
            LiveBreachSkipSell: liveBreachSell, LiveBreachSkipBuy: liveBreachBuy,
            OpenLegs: _legs.Count, MtmBps: mtm, RefreshedTp: refreshedTp, Form1Any: form1Any);
        _strategyWriter!.Append(new SignalUpdate(rec, _periodEvents, _periodTrades));
        _periodEvents = new List<SignalEventRecord>();
        _periodTrades = new List<StrategyTradeRecord>();

        // Flush closed-trade rows realized within the period ending at closeTime (fence-consistent).
        foreach (var ct in _periodClosed)
        {
            var bps = ct.Leg.EntryFill > 0.0
                ? ct.Leg.Dir * (ct.ExitFill - ct.Leg.EntryFill) / ct.Leg.EntryFill * 1e4
                : double.NaN;
            _strategyWriter!.AppendCisTrade(new CisTradeRecord(
                SourceCloseTime: closeTime, Domain: _nativeDomain, Strategy: NativeStrategyName, Series: CisSeries,
                EntryTime: ct.Leg.EntryTime, ExitTime: ct.ExitTime, Direction: ct.Leg.Dir, LadderLevel: ct.Leg.LadderLevel,
                EntryFillPrice: ct.Leg.EntryFill, ExitFillPrice: ct.ExitFill, ExitReason: ct.Reason,
                BarsHeld: ct.BarsHeld, RealizedBps: bps,
                EntryZ: ct.Leg.EntryZ, EntrySpread: ct.Leg.EntrySpread, EntryAnchorPrice: ct.Leg.EntryAnchorPrice,
                EntrySigma: ct.Leg.EntrySigma, ExitAnchorPrice: ct.ExitAnchorPrice, ExitSpread: ct.ExitSpread,
                EntryTrendZ: ct.Leg.EntryTrendZ, EntryTrendDir: ct.Leg.EntryTrendDir, EntryVolRegime: ct.Leg.EntryVolRegime,
                FixedExitPrice: ct.Leg.FixedExit, MaeBps: ct.Leg.MaeBps, MfeBps: ct.Leg.MfeBps, Censored: 0,
                SlPrice: ct.Leg.SlPrice, HorizonBars: ct.Leg.HorizonBars));
        }
        _periodClosed.Clear();

        // Advance period-direction trackers for the next period.
        _periodStartSign = NetSign();
        _periodEntryDir = 0;
    }

    // Arm the resting bracket(s) for the next period. R (refresh): cancel + re-arm each bar. S
    // (static): place once when flat and leave until filled/horizon. /REENTRY=none arms only the
    // base band (z*=2.0) and holds off while a leg is open; extend arms the full z*-ladder; allow
    // re-arms the base band each bar (concurrent legs). Skip a side breached vs the ≤t-1 close
    // (binding, don't chase) or through the live market; skip entirely on a min-mate gap.
    private void RearmBracket(double logClose, bool mateGap)
    {
        var b = _decisionBracket;   // == _lastBracket at delay 0; N-bar-old state on the tripwire arm
        if (!_staticArm)
        {
            if (_reentryMode == "none" && _legs.Count > 0)
                return;                       // no new entries while a leg is open (none)
            CancelOurPendingOrders();
            _bracketPlacedStatic = false;
        }
        else
        {
            if (_legs.Count > 0 || _bracketPlacedStatic)
                return;                       // static: leave the resting bracket until filled/horizon
            CancelOurPendingOrders();
        }
        if (b.Warmup || mateGap || !(b.Sigma > 0.0) || !double.IsFinite(b.AnchorLog) || !double.IsFinite(logClose))
            return;

        var closeI = Math.Exp(logClose);      // ≤ t-1 confirmed close price (binding breach reference)
        var levels = _reentryMode == "extend" ? _ladderZStars.Length : 1;
        var placedAny = false;
        for (var lv = 0; lv < levels; lv++)
        {
            var band = _ladderZStars[lv] * b.Sigma;
            var sell = RoundPrice(Math.Exp(b.AnchorLog + band));
            var buy = RoundPrice(Math.Exp(b.AnchorLog - band));
            if (sell > closeI && sell > Symbol.Bid)   // not through ≤t-1 close nor the live market
            {
                PlaceLimitOrder(TradeType.Sell, SymbolName, _orderVolume, sell, _orderLabel, null, null, null, lv.ToString());
                placedAny = true;
            }
            if (buy < closeI && buy < Symbol.Ask)
            {
                PlaceLimitOrder(TradeType.Buy, SymbolName, _orderVolume, buy, _orderLabel, null, null, null, lv.ToString());
                placedAny = true;
            }
        }
        if (_staticArm && placedAny)
            _bracketPlacedStatic = true;
    }

    // Close one leg's position at market with a staged exit reason (consumed by the close event,
    // async-safe). Used for form-1 (event reversion) and horizon exits.
    private void CloseLegMarket(long positionId, string reason)
    {
        _pendingCloseReason[positionId] = reason;
        foreach (var p in Positions)
            if (p.Label == _orderLabel && p.Id == positionId) { ClosePosition(p); break; }
    }

    private void CancelOurPendingOrders()
    {
        var toCancel = new List<PendingOrder>();
        foreach (var o in PendingOrders)
            if (o.Label == _orderLabel)
                toCancel.Add(o);
        foreach (var o in toCancel)
            CancelPendingOrder(o);
    }

    private void OnNativePositionOpened(PositionOpenedEventArgs args)
    {
        var pos = args.Position;
        if (_bothLeg && pos.Label == _bothLegLabel)
        {
            OnBothLegOpened(pos);
            return;
        }
        if (pos.Label != _orderLabel)
            return;
        var dir = pos.TradeType == TradeType.Sell ? -1 : 1;
        // Schedule mode encodes "level;hold_bars" in the comment; live limit orders carry the level.
        var level = 0;
        var scheduledHold = 0;
        if (_scheduleMode)
        {
            var parts = (pos.Comment ?? "").Split(';');
            if (parts.Length >= 1) int.TryParse(parts[0], out level);
            if (parts.Length >= 2) int.TryParse(parts[1], out scheduledHold);
        }
        else
            level = int.TryParse(pos.Comment, out var lv) ? lv : 0;
        var b = _decisionBracket;   // decision-state provenance (== _lastBracket at delay 0)
        // Entry-referential FIXED exit (proposal semantics): unwind the locked dislocation from the
        // ACTUAL fill. band = Z*·σ at the arm bar (level's ladder z*); exit = EntryFill·exp(dir·band)
        // (short dir=−1 → exp(−band) lower; long dir=+1 → exp(+band) higher). Locked once, never moved.
        var lvl = level >= 0 && level < _ladderZStars.Length ? level : 0;
        var band = _ladderZStars[lvl] * b.Sigma;
        var fixedExit = b.Sigma > 0.0 ? pos.EntryPrice * Math.Exp(dir * band) : double.NaN;
        var leg = new NativeLeg
        {
            PositionId = pos.Id, Dir = dir, LadderLevel = level, EntryFill = pos.EntryPrice,
            EntryH4Index = _h4Index, EntryTime = Server.Time,
            EntryZ = b.Z, EntrySpread = b.Spread,
            EntryAnchorPrice = b.Warmup ? double.NaN : Math.Exp(b.AnchorLog),
            EntrySigma = b.Sigma, EntryTrendZ = _trendZ, EntryTrendDir = _trendDir, EntryVolRegime = _volRegime,
            FixedExit = fixedExit   // forensic disclosure only (HYP-003 exit = moving-mean, not this level)
        };
        _legs.Add(leg);
        _periodEntryDir = dir;                 // mark this period's active direction (entry bar)
        _pendingEntryFill = pos.EntryPrice;

        if (_scheduleMode)
        {
            // EXP-018 random-timing arm: NO TP/SL — the leg exits only by its matched hold
            // (market close after scheduledHold bars) or the fence (censored). L-08: re-importing
            // the anchor exit would collapse near-anchor random entries instantly and bias the null.
            leg.HorizonBars = scheduledHold > 0 ? scheduledHold : FrozenHorizonCap;
        }
        else if (!_frozenExit)
        {
            // E0: set the initial form-2 TP to the moving anchor mean exp(anchorLog) (refreshed each bar,
            // HYP-003). Assert favorable before placement (long: TP>fill; short: TP<fill). fixedExit is a
            // forensic disclosure column only (the entry-referential level the dropped fixed exit would use).
            var target = b.ExitPrice;
            if (double.IsFinite(target))
            {
                var rt = RoundPrice(target);
                var favorable = dir > 0 ? rt > pos.EntryPrice : rt < pos.EntryPrice;
                if (favorable)
                    pos.ModifyTakeProfitPrice(rt);
            }
            // EXP-018 arm A (harvest): per-leg ⌈3·HL_entry⌉ time-stop, cap 48 (design §4) —
            // bounds e1-style censoring. No SL, no form-1 (the moving TP above is the exit).
            if (_harvestExit)
                leg.HorizonBars = double.IsFinite(b.Hl) && b.Hl > 0.0
                    ? Math.Min(FrozenHorizonCap, (int)Math.Ceiling(3.0 * b.Hl))
                    : FrozenHorizonCap;
        }
        else
        {
            // HYP-004 E1-E3: freeze the leg's bracket AT THE FILL TICK from the ≤t-1 arm bracket —
            // TP at a_entry (the entry-time anchor), optional SL at the symmetric outward barrier
            // o±D, optional ⌈3·HL_entry⌉ horizon. Attached natively to the position so same-bar m1
            // exits work (live orders rest from the first tick — no next-bar activation lag). Never
            // modified afterwards; the moving refresh and form-1 paths skip these legs entirely.
            var aEntry = b.Warmup || !double.IsFinite(b.AnchorLog) ? double.NaN : Math.Exp(b.AnchorLog);
            if (double.IsFinite(aEntry) && aEntry > 0.0)
            {
                var tp = RoundPrice(aEntry);
                var favorable = dir > 0 ? tp > pos.EntryPrice : tp < pos.EntryPrice;
                if (favorable)
                    pos.ModifyTakeProfitPrice(tp);
                leg.FixedExit = tp;                       // frozen TP (E1-E3 semantics of FixedExitPrice)
                var d = Math.Abs(pos.EntryPrice - aEntry);
                if (_frozenSl && d > 0.0)
                {
                    var sl = RoundPrice(dir > 0 ? pos.EntryPrice - d : pos.EntryPrice + d);
                    pos.ModifyStopLossPrice(sl);
                    leg.SlPrice = sl;
                }
                if (_frozenTimeStop)
                    leg.HorizonBars = double.IsFinite(b.Hl) && b.Hl > 0.0
                        ? Math.Min(FrozenHorizonCap, (int)Math.Ceiling(3.0 * b.Hl))
                        : FrozenHorizonCap;
            }
        }

        // Reentry order management: none → cancel all pendings; allow/extend → cancel only the
        // opposite side (keep same-side deeper levels / re-armable base for concurrent legs).
        if (_reentryMode == "none")
            CancelOurPendingOrders();
        else
            CancelOppositeSide(dir);

        _periodTrades.Add(new StrategyTradeRecord(
            Server.Time, _nativeDomain, NativeStrategyName, dir > 0 ? "buy" : "sell",
            0, dir, pos.EntryPrice, Math.Abs(dir), ++_nativeTradeSeq));
        _periodEvents.Add(new SignalEventRecord(
            Server.Time, _nativeDomain, NativeStrategyName, "enter_fade_limit", dir, 0, b.Z));
    }

    private void OnNativePositionClosed(PositionClosedEventArgs args)
    {
        var pos = args.Position;
        if (_bothLeg && pos.Label == _bothLegLabel)
        {
            OnBothLegClosed(pos);
            return;
        }
        if (pos.Label != _orderLabel)
            return;
        var leg = _legs.FirstOrDefault(l => l.PositionId == pos.Id);
        var fill = ClosingPriceOf(pos.Id);
        _pendingExitFill = fill;
        // Reason default: E0 = form-2 favorable limit (cTrader TP fill). Frozen modes (E1-E3): an
        // unstaged close is the native TP or SL filling — attribute by fill proximity to the two
        // frozen prices (tp_anchor vs sl_outward; E1 has no SL → always tp_anchor). A staged reason
        // (time_stop / open_at_end) overrides.
        string unstaged;
        if (!_frozenExit)
            unstaged = "form2_favorable_limit";
        else
        {
            var l = leg;
            unstaged = l != null && double.IsFinite(l.SlPrice) && double.IsFinite(fill)
                       && Math.Abs(fill - l.SlPrice) < Math.Abs(fill - l.FixedExit)
                ? "sl_outward" : "tp_anchor";
        }
        var reason = _pendingCloseReason.TryGetValue(pos.Id, out var r) ? r : unstaged;
        _pendingCloseReason.Remove(pos.Id);
        var prev = leg?.Dir ?? (pos.TradeType == TradeType.Sell ? -1 : 1);
        if (leg != null)
        {
            _periodClosed.Add(new ClosedTrade
            {
                Leg = leg, ExitFill = fill, Reason = reason, ExitTime = Server.Time,
                ExitAnchorPrice = _lastBracket.Warmup ? double.NaN : Math.Exp(_lastBracket.AnchorLog),
                ExitSpread = _lastBracket.Spread, BarsHeld = Math.Max(0, _h4Index - leg.EntryH4Index)
            });
            _legs.Remove(leg);
        }
        if (_legs.Count == 0)
            _bracketPlacedStatic = false;      // static: allow a fresh bracket after the episode ends
        _periodTrades.Add(new StrategyTradeRecord(
            Server.Time, _nativeDomain, NativeStrategyName, prev > 0 ? "sell" : "buy",
            prev, 0, fill, Math.Abs(prev), ++_nativeTradeSeq));
        _periodEvents.Add(new SignalEventRecord(
            Server.Time, _nativeDomain, NativeStrategyName, reason, 0, prev, _lastBracket.Z));
    }

    private double ClosingPriceOf(long positionId)
    {
        for (var k = History.Count - 1; k >= 0; k--)
            if (History[k].PositionId == positionId)
                return History[k].ClosingPrice;
        return double.NaN;
    }

    // Cancel only the opposite-side resting limits after a directional fill (allow/extend keep the
    // same-side ladder / re-armable base band for concurrent legs).
    private void CancelOppositeSide(int dir)
    {
        var oppType = dir > 0 ? TradeType.Sell : TradeType.Buy;
        var toCancel = new List<PendingOrder>();
        foreach (var o in PendingOrders)
            if (o.Label == _orderLabel && o.TradeType == oppType)
                toCancel.Add(o);
        foreach (var o in toCancel)
            CancelPendingOrder(o);
    }

    // Apply form-1 (event reversion) exits to open legs at this bar's boundary. sc = logClose −
    // anchorLog (S5: OLS residual; S6/7/8: spread − mean). Short reverts when sc ≤ 0, long when
    // sc ≥ 0 → close at market (open of i+1). NO horizon (EXP-014b: proposal enforces no other
    // exits). Returns whether any form-1 fired. All decision inputs are ≤ t-1 (bar i completed).
    private bool ApplyEventExits(int i, double logClose)
    {
        var sc = logClose - _decisionBracket.AnchorLog;
        var toClose = new List<long>();
        foreach (var leg in _legs)
        {
            var reverted = (leg.Dir < 0 && sc <= 0.0) || (leg.Dir > 0 && sc >= 0.0);
            if (reverted)
                toClose.Add(leg.PositionId);
        }
        foreach (var id in toClose)
            CloseLegMarket(id, "form1_reversion");
        return toClose.Count > 0;
    }

    // HYP-004 E3: market-close every leg held ≥ its frozen horizon (⌈3·HL_entry⌉, cap 48). The fill
    // bar counts as bar 1 (EntryH4Index = the ≤t-1 arm bar), matching the availability race window
    // [entry .. entry+H−1]; the close decision at completed bar i executes at the open of i+1.
    private void ApplyFrozenTimeStop(int i)
    {
        var toClose = new List<long>();
        foreach (var leg in _legs)
            if (leg.HorizonBars > 0 && i - leg.EntryH4Index >= leg.HorizonBars)
                toClose.Add(leg.PositionId);
        foreach (var id in toClose)
            CloseLegMarket(id, "time_stop");
    }

    // EXP-018 random-timing arm: market-close every leg held ≥ its scheduled matched hold. The
    // matched hold is a seeded draw from the live arm's realized per-level BarsHeld distribution
    // (exposure-matched carry read — operator-resolved 2026-07-04).
    private void ApplyMatchedHoldExits(int i)
    {
        var toClose = new List<long>();
        foreach (var leg in _legs)
            if (leg.HorizonBars > 0 && i - leg.EntryH4Index >= leg.HorizonBars)
                toClose.Add(leg.PositionId);
        foreach (var id in toClose)
            CloseLegMarket(id, "matched_hold");
    }

    // EXP-018 random-timing arm: market-enter each scheduled entry whose OpenTime == bar i's
    // OpenTime (fills at the next open — same convention as the both-leg market entry). The
    // schedule is strictly time-sorted; stale rows (before the first processed bar) are skipped.
    private void FireScheduledEntries(int i)
    {
        var openTime = _h4.OpenTimes[i];
        while (_scheduleCursor < _schedule.Count && _schedule[_scheduleCursor].OpenTimeUtc < openTime)
            _scheduleCursor++;   // stale (bar not processed at this time) — skipped, disclosed in logs
        while (_scheduleCursor < _schedule.Count && _schedule[_scheduleCursor].OpenTimeUtc == openTime)
        {
            var e = _schedule[_scheduleCursor++];
            ExecuteMarketOrder(e.Dir > 0 ? TradeType.Buy : TradeType.Sell, SymbolName, _orderVolume,
                _orderLabel, null, null, $"{e.Level};{e.HoldBars}");
        }
    }

    // Schedule CSV: header + rows "open_time_utc,level,dir,hold_bars" (ISO-8601 UTC; dir ∈ {-1,+1};
    // hold_bars ≥ 1), strictly non-decreasing in time. Generated seeded from the live arm's emission
    // by tools/ctrader-cli/experiments/gen_exp018_schedules.py — never hand-written.
    private static List<ScheduledEntry> LoadSchedule(string path)
    {
        if (!System.IO.File.Exists(path))
            throw new InvalidOperationException($"CIS Schedule Path not found: {path}");
        var rows = new List<ScheduledEntry>();
        var last = DateTime.MinValue;
        foreach (var line in System.IO.File.ReadAllLines(path))
        {
            var t = line.Trim();
            if (t.Length == 0 || t.StartsWith("open_time", StringComparison.OrdinalIgnoreCase) || t.StartsWith("#"))
                continue;
            var f = t.Split(',');
            if (f.Length < 4)
                throw new InvalidOperationException($"Bad schedule row (need 4 fields): '{t}'");
            if (!DateTime.TryParse(f[0], CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal, out var ts))
                throw new InvalidOperationException($"Bad schedule timestamp: '{f[0]}'");
            var level = int.Parse(f[1], CultureInfo.InvariantCulture);
            var dir = int.Parse(f[2], CultureInfo.InvariantCulture);
            var hold = int.Parse(f[3], CultureInfo.InvariantCulture);
            if (dir != 1 && dir != -1)
                throw new InvalidOperationException($"Bad schedule dir (must be ±1): '{t}'");
            if (hold < 1)
                throw new InvalidOperationException($"Bad schedule hold_bars (must be ≥1): '{t}'");
            if (ts < last)
                throw new InvalidOperationException($"Schedule not time-sorted at: '{t}'");
            last = ts;
            rows.Add(new ScheduledEntry(ts, level, dir, hold));
        }
        if (rows.Count == 0)
            throw new InvalidOperationException($"Schedule is empty: {path}");
        return rows;
    }

    // Refresh the moving form-2 TP (anchor mean) for every open leg; assert favorable placement
    // before each modify (long: TP > mark; short: TP < mark) — skip adverse (finding F guard).
    private double RefreshForm2Targets(double mark)
    {
        var target = _decisionBracket.ExitPrice;   // exp(moving anchorLog); decision-state (delay-aware)
        if (!double.IsFinite(target))
            return double.NaN;
        var rt = RoundPrice(target);
        var representative = double.NaN;
        foreach (var p in Positions)
        {
            if (p.Label != _orderLabel)
                continue;
            var dir = p.TradeType == TradeType.Sell ? -1 : 1;
            var favorable = dir > 0 ? rt > mark : rt < mark;
            if (!favorable)
                continue;                       // leave the prior TP; never place an adverse target
            p.ModifyTakeProfitPrice(rt);
            representative = rt;
        }
        return representative;
    }

    private int NetSign()
    {
        var s = 0;
        foreach (var leg in _legs)
            s += leg.Dir;
        return Math.Sign(s);
    }

    // Update per-leg adverse/favorable excursion from the current 4h close (dir-signed return, bps).
    // MAE = running min (most adverse), MFE = running max (most favorable); both start at 0 (entry).
    private void UpdateLegExcursions(double close)
    {
        if (!(close > 0.0))
            return;
        foreach (var leg in _legs)
        {
            if (!(leg.EntryFill > 0.0))
                continue;
            var bps = leg.Dir * (close - leg.EntryFill) / leg.EntryFill * 1e4;
            if (bps < leg.MaeBps) leg.MaeBps = bps;
            if (bps > leg.MfeBps) leg.MfeBps = bps;
        }
    }

    // At the fence/stop, emit any still-open legs as censored open_at_end rows — excluded from the
    // realized-P&L referee (RealizedBps NaN), disclosed for the survival count. Marked at the last close.
    private void FlushOpenLegsAsCensored()
    {
        if (_bothLeg)
        {
            FlushBothLegCensored();
            return;
        }
        if (_strategyWriter == null || _h4 == null || _legs.Count == 0)
            return;
        var idx = _h4Index >= 0 && _h4Index < _h4.Count ? _h4Index : _h4.Count - 1;
        if (idx < 0)
            return;
        var mark = _h4.ClosePrices[idx];
        var closeTime = _h4.OpenTimes[idx].AddMinutes(_nativeDomainMinutes);
        var anchor = _lastBracket.Warmup ? double.NaN : Math.Exp(_lastBracket.AnchorLog);
        foreach (var leg in _legs)
            _strategyWriter.AppendCisTrade(new CisTradeRecord(
                SourceCloseTime: closeTime, Domain: _nativeDomain, Strategy: NativeStrategyName, Series: CisSeries,
                EntryTime: leg.EntryTime, ExitTime: closeTime, Direction: leg.Dir, LadderLevel: leg.LadderLevel,
                EntryFillPrice: leg.EntryFill, ExitFillPrice: mark, ExitReason: "open_at_end",
                BarsHeld: Math.Max(0, _h4Index - leg.EntryH4Index), RealizedBps: double.NaN,
                EntryZ: leg.EntryZ, EntrySpread: leg.EntrySpread, EntryAnchorPrice: leg.EntryAnchorPrice,
                EntrySigma: leg.EntrySigma, ExitAnchorPrice: anchor, ExitSpread: _lastBracket.Spread,
                EntryTrendZ: leg.EntryTrendZ, EntryTrendDir: leg.EntryTrendDir, EntryVolRegime: leg.EntryVolRegime,
                FixedExitPrice: leg.FixedExit, MaeBps: leg.MaeBps, MfeBps: leg.MfeBps, Censored: 1,
                SlPrice: leg.SlPrice, HorizonBars: leg.HorizonBars));
    }

    // Update the per-bar conditioner state from the traded 4h close (≤ t-1). Trend = (EMA20 −
    // EMA50)/σ_close(WZ); vol regime = tercile of the current spread-σ in the trailing σ history.
    private void UpdateConditioners(double close)
    {
        if (close > 0.0)
        {
            if (double.IsNaN(_ema20)) { _ema20 = close; _ema50 = close; }
            else
            {
                _ema20 += (2.0 / (TrendFast + 1)) * (close - _ema20);
                _ema50 += (2.0 / (TrendSlow + 1)) * (close - _ema50);
            }
            _h4Close.Add(close);
            if (_h4Close.Count > TrendSigmaWindow)
                _h4Close.RemoveAt(0);
            var sigmaClose = ConditionerStd(_h4Close);
            _trendZ = sigmaClose > 0.0 ? (_ema20 - _ema50) / sigmaClose : double.NaN;
            _trendDir = double.IsNaN(_trendZ) ? 0 : Math.Sign(_trendZ);
        }
        var sig = _lastBracket.Sigma;
        if (double.IsFinite(sig))
        {
            _sigmaHist.Add(sig);
            if (_sigmaHist.Count > VolHistWindow)
                _sigmaHist.RemoveAt(0);
            _volRegime = VolTercile(_sigmaHist, sig);
        }
    }

    private static int VolTercile(List<double> hist, double val)
    {
        if (hist.Count < 3)
            return -1;
        var below = 0;
        foreach (var v in hist)
            if (v < val) below++;
        var frac = (double)below / hist.Count;
        return frac < 1.0 / 3.0 ? 0 : frac < 2.0 / 3.0 ? 1 : 2;
    }

    private static double ConditionerStd(List<double> vals)
    {
        if (vals.Count < 2)
            return double.NaN;
        var m = 0.0;
        foreach (var v in vals) m += v;
        m /= vals.Count;
        var ss = 0.0;
        foreach (var v in vals) { var d = v - m; ss += d * d; }
        return Math.Sqrt(ss / (vals.Count - 1));
    }

    private double RoundPrice(double price)
    {
        return Math.Round(price, Symbol.Digits);
    }

    // CF-MR-004 cross-instrument basket feed — FROM SCRATCH (L-13), 4h anchor domain, EXACT
    // CloseTime alignment (no carry-forward — fixes the CF-MR-003 F-1 artifact). Equal-weight
    // mean of mate ln(Close) at the bar whose OpenTime == the requested 4h OpenTime; a mate with
    // no bar at that slot is skipped (explicit gap policy); NaN if none aligns. Phase-shift
    // (leak tripwire) subtracts whole 4h bars from each mate's own index, keeping a valid but
    // time-decorrelated basket. Distinct from MarketDataBasketFeed (that stays 1h/CONC-1 for the
    // retired CF-MR-003 model; not reused here).
    private sealed class CrossInstrumentBasketFeed
    {
        private readonly List<Bars> _bars = new();
        private readonly List<int> _cursor = new();
        private readonly int _phaseShiftBars;
        private readonly int _expectedMates;

        public CrossInstrumentBasketFeed(Xen bot, IReadOnlyList<string> mates, int phaseShiftBars,
                                         TimeFrame timeFrame)
        {
            _phaseShiftBars = Math.Max(0, phaseShiftBars);
            _expectedMates = mates.Count;   // full predeclared membership (min-mate rule, design §4)
            foreach (var mate in mates)
            {
                Bars? bars = null;
                try
                {
                    if (bot.Symbols.GetSymbol(mate) != null)
                        bars = bot.MarketData.GetBars(timeFrame, mate);
                }
                catch (Exception ex)
                {
                    bot.Print("CF-MR-004 feed: mate '{0}' unresolved ({1}) — skipped.", mate, ex.Message);
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

        // Full predeclared class-mate membership (min-mate-count rule): the basket bar is VALID
        // only if LastMateCount == ExpectedMates (design §4). A shortfall → basket invalid → the
        // robot arms no new order that bar (β/anchor composition stays fixed; no silent mate-drop).
        public int ExpectedMates => _expectedMates;
        public int LastMateCount { get; private set; }

        // Equal-weight mean of mate ln(Close) at EXACTLY OpenTime == openTime. Monotonic cursor
        // (openTime is non-decreasing across calls). No carry-forward: an unaligned mate is skipped
        // (recorded in LastMateCount so the min-mate rule + audit can bound the invalid-bar rate).
        public double BasketLogAt(DateTime openTime)
        {
            var sum = 0.0;
            var used = 0;
            for (var m = 0; m < _bars.Count; m++)
            {
                var bars = _bars[m];
                var c = _cursor[m];
                while (c < bars.Count && bars.OpenTimes[c] < openTime)
                    c++;
                _cursor[m] = c;
                if (c >= bars.Count || bars.OpenTimes[c] != openTime)
                    continue;                      // exact-alignment gap → skip this mate
                var idx = c - _phaseShiftBars;      // leak-tripwire time-decorrelation (0 = live)
                if (idx < 0)
                    continue;
                var px = bars.ClosePrices[idx];
                if (px > 0.0)
                {
                    sum += Math.Log(px);
                    used++;
                }
            }
            LastMateCount = used;
            return used > 0 ? sum / used : double.NaN;
        }
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
