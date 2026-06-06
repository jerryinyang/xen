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
        _disposed = true;
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
            new DataField<bool>("IsFlat")
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
            new DataField<double>("PositionDelta")
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
    }

    private static string Sanitize(string value)
    {
        return value.ToLowerInvariant().Replace(" ", "_").Replace("(", "").Replace(")", "");
    }
}
