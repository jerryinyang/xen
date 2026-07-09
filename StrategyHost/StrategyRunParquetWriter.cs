using System.Text.Json;
using Parquet;
using Parquet.Data;
using Parquet.Schema;

namespace Xen.StrategyHost;

public sealed class StrategyRunParquetWriter : IDisposable
{
    private readonly HoldoutFence _fence;
    private readonly string _runDirectory;
    private readonly List<SignalPositionRecord> _positions = new();
    private readonly List<SignalEventRecord> _events = new();
    private readonly List<StrategyTradeRecord> _trades = new();
    // EXP-014 (CF-MR-004 HYP-002): per-closed-trade table (empty for every other model).
    private readonly List<CisTradeRecord> _cisTrades = new();
    // EXP-029: optional per-bounce AVWAP detail table (serialized AvwapEventDetail),
    // consumed by the Python parity harness to rebuild matched controls without a
    // signal oracle. Set once at run end via SetAvwapEventDetails; empty for other models.
    private IReadOnlyList<AvwapEventDetail> _avwapEventDetails = Array.Empty<AvwapEventDetail>();
    private bool _disposed;

    public StrategyRunParquetWriter(
        string outputRoot,
        string strategy,
        string symbol,
        string domain,
        HoldoutFence fence,
        IReadOnlyDictionary<string, object?> parameters)
    {
        _fence = fence;
        Directory.CreateDirectory(outputRoot);
        var stamp = DateTime.UtcNow.ToString("yyyyMMdd_HHmmss");
        _runDirectory = Path.Combine(outputRoot, $"{Sanitize(strategy)}_{Sanitize(symbol)}_{Sanitize(domain)}_{stamp}");
        Directory.CreateDirectory(_runDirectory);

        var metadata = new
        {
            strategy,
            symbol,
            domain,
            analysis_end_utc = fence.AnalysisEndUtc.ToString("o"),
            parameters,
            generated_utc = DateTime.UtcNow.ToString("o"),
            qualification_input = "positions.parquet",
            trade_blotter_diagnostic_only = true
        };
        File.WriteAllText(
            Path.Combine(_runDirectory, "run_metadata.json"),
            JsonSerializer.Serialize(metadata, new JsonSerializerOptions { WriteIndented = true }));
    }

    public string RunDirectory => _runDirectory;

    /// <summary>
    /// Register the model's per-bounce AVWAP detail rows (EXP-029). Call once before
    /// Dispose; rows are fence-asserted on their trigger time and written to
    /// <c>avwap_events.parquet</c>. No-op for models that produce no such detail.
    /// </summary>
    public void SetAvwapEventDetails(IReadOnlyList<AvwapEventDetail> details)
    {
        foreach (var detail in details)
            _fence.AssertCanEmit(detail.TriggerTime);
        _avwapEventDetails = details;
    }

    /// <summary>
    /// Register one closed-trade row (EXP-014). Fence-asserted on its exit-bar time; written to
    /// <c>cis_trades.parquet</c> at Dispose. No-op-shaped for models that emit no such rows.
    /// </summary>
    public void AppendCisTrade(CisTradeRecord trade)
    {
        _fence.AssertCanEmit(trade.SourceCloseTime);
        _cisTrades.Add(trade);
    }

    public void Append(SignalUpdate update)
    {
        _fence.AssertCanEmit(update.Position.SourceCloseTime);
        _positions.Add(update.Position);

        foreach (var eventRecord in update.Events)
        {
            _fence.AssertCanEmit(eventRecord.SourceCloseTime);
            _events.Add(eventRecord);
        }

        foreach (var trade in update.Trades)
        {
            _fence.AssertCanEmit(trade.SourceCloseTime);
            _trades.Add(trade);
        }
    }

    public void Dispose()
    {
        if (_disposed)
            return;

        WritePositions(Path.Combine(_runDirectory, "positions.parquet"), _positions);
        WriteEvents(Path.Combine(_runDirectory, "events.parquet"), _events);
        WriteTrades(Path.Combine(_runDirectory, "trade_blotter.parquet"), _trades);
        WriteCisTrades(Path.Combine(_runDirectory, "cis_trades.parquet"), _cisTrades);
        if (_avwapEventDetails.Count > 0)
            WriteAvwapEvents(Path.Combine(_runDirectory, "avwap_events.parquet"), _avwapEventDetails);
        _disposed = true;
    }

    // EXP-029: serialize the per-bounce AVWAP detail table (already-computed model
    // state). Carries the regime / direction / anchor / frozen-target / pyramid
    // metadata the Python parity harness needs to rebuild matched controls.
    private static void WriteAvwapEvents(string path, IReadOnlyList<AvwapEventDetail> rows)
    {
        var fields = new DataField[]
        {
            new DataField<DateTime>("SourceCloseTime"),   // == TriggerTime
            new DataField<string>("Domain"),
            new DataField<int>("RegimeId"),
            new DataField<int>("Direction"),
            new DataField<bool>("IsPyramidBounce"),
            new DataField<int>("BounceIndexInRegime"),
            new DataField<int>("AnchorIdx"),
            new DataField<DateTime>("AnchorTime"),
            new DataField<double>("AnchorPrice"),
            new DataField<int>("TriggerIdx"),
            new DataField<double>("TriggerClose"),
            new DataField<double>("AvwapAtTrigger"),
            new DataField<double>("FavorableTargetAtTrigger"),
            new DataField<double>("AdverseTargetAtTrigger"),
            new DataField<int>("AnchorAgeBars"),
            // EXP-029 (F01): the C#-executed completion per bounce, so the Python
            // harness can grade the corrected concurrent-completion code per event.
            new DataField<int>("ExitIdx"),
            new DataField<DateTime>("ExitTime"),
            new DataField<double>("ExitClose"),
            new DataField<string>("ExitReason"),
            new DataField<int>("ExitBars"),
            new DataField<double>("ExitLifetimeBps")
        };
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write);
        using var writer = ParquetWriter.CreateAsync(new ParquetSchema(fields), stream).GetAwaiter().GetResult();
        writer.CompressionMethod = CompressionMethod.Zstd;
        if (rows.Count == 0)
            return;
        using var groupWriter = writer.CreateRowGroup();
        groupWriter.WriteColumnAsync(new DataColumn(fields[0], rows.Select(row => row.TriggerTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[1], rows.Select(row => row.Domain).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[2], rows.Select(row => row.RegimeId).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[3], rows.Select(row => row.Direction).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[4], rows.Select(row => row.IsPyramidBounce).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[5], rows.Select(row => row.BounceIndexInRegime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[6], rows.Select(row => row.AnchorIdx).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[7], rows.Select(row => row.AnchorTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[8], rows.Select(row => row.AnchorPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[9], rows.Select(row => row.TriggerIdx).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[10], rows.Select(row => row.TriggerClose).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[11], rows.Select(row => row.AvwapAtTrigger).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[12], rows.Select(row => row.FavorableTargetAtTrigger).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[13], rows.Select(row => row.AdverseTargetAtTrigger).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[14], rows.Select(row => row.AnchorAgeBars).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[15], rows.Select(row => row.ExitIdx).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[16], rows.Select(row => row.ExitTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[17], rows.Select(row => row.ExitClose).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[18], rows.Select(row => row.ExitReason).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[19], rows.Select(row => row.ExitBars).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[20], rows.Select(row => row.ExitLifetimeBps).ToArray())).GetAwaiter().GetResult();
    }

    private static void WritePositions(string path, IReadOnlyList<SignalPositionRecord> rows)
    {
        var fields = new DataField[]
        {
            new DataField<DateTime>("SourceCloseTime"),
            new DataField<string>("Domain"),
            new DataField<string>("Strategy"),
            new DataField<int>("Position"),
            new DataField<double>("SignalValue"),
            new DataField<double>("RealOpen"),
            new DataField<double>("RealHigh"),
            new DataField<double>("RealLow"),
            new DataField<double>("RealClose"),
            new DataField<bool>("Warmup"),
            new DataField<bool>("IsFlat"),
            // EXP-029: per-bar regime state (sentinel -1/0 for non-regime models).
            new DataField<int>("RegimeId"),
            new DataField<int>("RegimeDirection"),
            // EXP-006: causal reversion-completion limit fill price on exit bars (NaN otherwise).
            new DataField<double>("ExitFillPrice"),
            // EXP-010 (CONC-1): limit-entry fill price + causal decision provenance (NaN otherwise).
            new DataField<double>("EntryFillPrice"),
            new DataField<double>("Anchor"),
            new DataField<double>("Dev"),
            new DataField<double>("Z"),
            new DataField<double>("Vr"),
            new DataField<double>("Hl"),
            new DataField<double>("Beta"),
            // EXP-014 rich per-bar state (§11). Sentinels for every non-CIS model.
            new DataField<double>("ArmSellPrice"),
            new DataField<double>("ArmBuyPrice"),
            new DataField<double>("Sigma"),
            new DataField<double>("SpreadMean"),
            new DataField<int>("MateCount"),
            new DataField<int>("MateExpected"),
            new DataField<bool>("MateGap"),
            new DataField<double>("TrendZ"),
            new DataField<int>("TrendDir"),
            new DataField<int>("VolRegime"),
            new DataField<bool>("BreachSkipSell"),
            new DataField<bool>("BreachSkipBuy"),
            new DataField<bool>("LiveBreachSkipSell"),
            new DataField<bool>("LiveBreachSkipBuy"),
            new DataField<int>("OpenLegs"),
            new DataField<double>("MtmBps"),
            new DataField<double>("RefreshedTp"),
            new DataField<bool>("Form1Any"),
            // EXP-020 ARM R per-bar virtual-portfolio state (NaN for other models).
            new DataField<double>("PortWeight"),
            new DataField<double>("PortUnits"),
            new DataField<double>("PortCash")
        };
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write);
        using var writer = ParquetWriter.CreateAsync(new ParquetSchema(fields), stream).GetAwaiter().GetResult();
        writer.CompressionMethod = CompressionMethod.Zstd;
        if (rows.Count == 0)
            return;
        using var groupWriter = writer.CreateRowGroup();
        groupWriter.WriteColumnAsync(new DataColumn(fields[0], rows.Select(row => row.SourceCloseTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[1], rows.Select(row => row.Domain).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[2], rows.Select(row => row.Strategy).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[3], rows.Select(row => row.Position).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[4], rows.Select(row => row.SignalValue).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[5], rows.Select(row => row.RealOpen).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[6], rows.Select(row => row.RealHigh).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[7], rows.Select(row => row.RealLow).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[8], rows.Select(row => row.RealClose).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[9], rows.Select(row => row.Warmup).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[10], rows.Select(row => row.IsFlat).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[11], rows.Select(row => row.RegimeId).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[12], rows.Select(row => row.RegimeDirection).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[13], rows.Select(row => row.ExitFillPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[14], rows.Select(row => row.EntryFillPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[15], rows.Select(row => row.Anchor).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[16], rows.Select(row => row.Dev).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[17], rows.Select(row => row.Z).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[18], rows.Select(row => row.Vr).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[19], rows.Select(row => row.Hl).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[20], rows.Select(row => row.Beta).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[21], rows.Select(row => row.ArmSellPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[22], rows.Select(row => row.ArmBuyPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[23], rows.Select(row => row.Sigma).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[24], rows.Select(row => row.SpreadMean).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[25], rows.Select(row => row.MateCount).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[26], rows.Select(row => row.MateExpected).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[27], rows.Select(row => row.MateGap).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[28], rows.Select(row => row.TrendZ).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[29], rows.Select(row => row.TrendDir).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[30], rows.Select(row => row.VolRegime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[31], rows.Select(row => row.BreachSkipSell).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[32], rows.Select(row => row.BreachSkipBuy).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[33], rows.Select(row => row.LiveBreachSkipSell).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[34], rows.Select(row => row.LiveBreachSkipBuy).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[35], rows.Select(row => row.OpenLegs).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[36], rows.Select(row => row.MtmBps).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[37], rows.Select(row => row.RefreshedTp).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[38], rows.Select(row => row.Form1Any).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[39], rows.Select(row => row.PortWeight).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[40], rows.Select(row => row.PortUnits).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[41], rows.Select(row => row.PortCash).ToArray())).GetAwaiter().GetResult();
    }

    // EXP-014 (CF-MR-004 HYP-002): per-closed-trade table for leg-level analysis (exit reason /
    // ladder level / trend / vol). Empty (header-only) for every non-CIS model.
    private static void WriteCisTrades(string path, IReadOnlyList<CisTradeRecord> rows)
    {
        var fields = new DataField[]
        {
            new DataField<DateTime>("SourceCloseTime"),
            new DataField<string>("Domain"),
            new DataField<string>("Strategy"),
            new DataField<string>("Series"),
            new DataField<DateTime>("EntryTime"),
            new DataField<DateTime>("ExitTime"),
            new DataField<int>("Direction"),
            new DataField<int>("LadderLevel"),
            new DataField<double>("EntryFillPrice"),
            new DataField<double>("ExitFillPrice"),
            new DataField<string>("ExitReason"),
            new DataField<int>("BarsHeld"),
            new DataField<double>("RealizedBps"),
            new DataField<double>("EntryZ"),
            new DataField<double>("EntrySpread"),
            new DataField<double>("EntryAnchorPrice"),
            new DataField<double>("EntrySigma"),
            new DataField<double>("ExitAnchorPrice"),
            new DataField<double>("ExitSpread"),
            new DataField<double>("EntryTrendZ"),
            new DataField<int>("EntryTrendDir"),
            new DataField<int>("EntryVolRegime"),
            new DataField<double>("FixedExitPrice"),
            new DataField<double>("MaeBps"),
            new DataField<double>("MfeBps"),
            new DataField<int>("Censored"),
            new DataField<string>("LegSymbol"),
            new DataField<long>("SpreadPositionId"),
            new DataField<double>("SlPrice"),
            new DataField<int>("HorizonBars"),
            new DataField<double>("BreakoutRef"),
            new DataField<int>("SignalX"),
            new DataField<double>("HtfPlusDi"),
            new DataField<double>("HtfMinusDi"),
            new DataField<double>("HtfAdx"),
            new DataField<double>("HtfAtr"),
            new DataField<DateTime>("HtfBarCloseTime")
        };
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write);
        using var writer = ParquetWriter.CreateAsync(new ParquetSchema(fields), stream).GetAwaiter().GetResult();
        writer.CompressionMethod = CompressionMethod.Zstd;
        if (rows.Count == 0)
            return;
        using var groupWriter = writer.CreateRowGroup();
        groupWriter.WriteColumnAsync(new DataColumn(fields[0], rows.Select(r => r.SourceCloseTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[1], rows.Select(r => r.Domain).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[2], rows.Select(r => r.Strategy).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[3], rows.Select(r => r.Series).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[4], rows.Select(r => r.EntryTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[5], rows.Select(r => r.ExitTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[6], rows.Select(r => r.Direction).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[7], rows.Select(r => r.LadderLevel).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[8], rows.Select(r => r.EntryFillPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[9], rows.Select(r => r.ExitFillPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[10], rows.Select(r => r.ExitReason).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[11], rows.Select(r => r.BarsHeld).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[12], rows.Select(r => r.RealizedBps).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[13], rows.Select(r => r.EntryZ).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[14], rows.Select(r => r.EntrySpread).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[15], rows.Select(r => r.EntryAnchorPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[16], rows.Select(r => r.EntrySigma).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[17], rows.Select(r => r.ExitAnchorPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[18], rows.Select(r => r.ExitSpread).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[19], rows.Select(r => r.EntryTrendZ).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[20], rows.Select(r => r.EntryTrendDir).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[21], rows.Select(r => r.EntryVolRegime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[22], rows.Select(r => r.FixedExitPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[23], rows.Select(r => r.MaeBps).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[24], rows.Select(r => r.MfeBps).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[25], rows.Select(r => r.Censored).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[26], rows.Select(r => r.LegSymbol).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[27], rows.Select(r => r.SpreadPositionId).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[28], rows.Select(r => r.SlPrice).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[29], rows.Select(r => r.HorizonBars).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[30], rows.Select(r => r.BreakoutRef).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[31], rows.Select(r => r.SignalX).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[32], rows.Select(r => r.HtfPlusDi).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[33], rows.Select(r => r.HtfMinusDi).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[34], rows.Select(r => r.HtfAdx).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[35], rows.Select(r => r.HtfAtr).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[36], rows.Select(r => r.HtfBarCloseTime).ToArray())).GetAwaiter().GetResult();
    }

    private static void WriteEvents(string path, IReadOnlyList<SignalEventRecord> rows)
    {
        var fields = new DataField[]
        {
            new DataField<DateTime>("SourceCloseTime"),
            new DataField<string>("Domain"),
            new DataField<string>("Strategy"),
            new DataField<string>("EventType"),
            new DataField<int>("Position"),
            new DataField<int>("PreviousPosition"),
            new DataField<double>("SignalValue")
        };
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write);
        using var writer = ParquetWriter.CreateAsync(new ParquetSchema(fields), stream).GetAwaiter().GetResult();
        writer.CompressionMethod = CompressionMethod.Zstd;
        if (rows.Count == 0)
            return;
        using var groupWriter = writer.CreateRowGroup();
        groupWriter.WriteColumnAsync(new DataColumn(fields[0], rows.Select(row => row.SourceCloseTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[1], rows.Select(row => row.Domain).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[2], rows.Select(row => row.Strategy).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[3], rows.Select(row => row.EventType).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[4], rows.Select(row => row.Position).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[5], rows.Select(row => row.PreviousPosition).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[6], rows.Select(row => row.SignalValue).ToArray())).GetAwaiter().GetResult();
    }

    private static void WriteTrades(string path, IReadOnlyList<StrategyTradeRecord> rows)
    {
        var fields = new DataField[]
        {
            new DataField<DateTime>("SourceCloseTime"),
            new DataField<string>("Domain"),
            new DataField<string>("Strategy"),
            new DataField<string>("Action"),
            new DataField<int>("PreviousPosition"),
            new DataField<int>("Position"),
            new DataField<double>("Price"),
            new DataField<double>("PositionDelta"),
            new DataField<long>("TradeSequence")
        };
        using var stream = new FileStream(path, FileMode.Create, FileAccess.Write);
        using var writer = ParquetWriter.CreateAsync(new ParquetSchema(fields), stream).GetAwaiter().GetResult();
        writer.CompressionMethod = CompressionMethod.Zstd;
        if (rows.Count == 0)
            return;
        using var groupWriter = writer.CreateRowGroup();
        groupWriter.WriteColumnAsync(new DataColumn(fields[0], rows.Select(row => row.SourceCloseTime).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[1], rows.Select(row => row.Domain).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[2], rows.Select(row => row.Strategy).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[3], rows.Select(row => row.Action).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[4], rows.Select(row => row.PreviousPosition).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[5], rows.Select(row => row.Position).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[6], rows.Select(row => row.Price).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[7], rows.Select(row => row.PositionDelta).ToArray())).GetAwaiter().GetResult();
        groupWriter.WriteColumnAsync(new DataColumn(fields[8], rows.Select(row => row.TradeSequence).ToArray())).GetAwaiter().GetResult();
    }

    private static string Sanitize(string value)
    {
        return value.ToLowerInvariant().Replace(" ", "_").Replace("(", "").Replace(")", "");
    }
}
