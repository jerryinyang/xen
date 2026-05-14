using System;
using System.Collections.Generic;
using System.IO;
using cAlgo.API;
using Parquet;
using Parquet.Data;
using Parquet.Schema;

namespace cAlgo.Robots;

[Robot(AccessRights = AccessRights.FullAccess, AddIndicators = false, DefaultTimeFrame="Minute")]
public class Xen : Robot
{
    private const string OutputDirectory = "/Users/jerryinyang/cAlgo/Sources/Robots/Xen/Xen/data/timebars";
    private const int BatchSize = 20000;

    private TimeBarParquetWriter? _writer;
    private DateTime? _lastCloseTime;
    private long _capturedBars;

    protected override void OnStart()
    {
        if (Bars.TimeFrame != TimeFrame.Minute)
            throw new InvalidOperationException("Xen must run on a 1-minute chart.");

        _writer = new TimeBarParquetWriter(OutputDirectory, SymbolName, Server.Time, DateTime.UtcNow, BatchSize);
        Print("Xen started for {0}. Collecting completed 1-minute bars.", SymbolName);
    }

    protected override void OnBar()
    {
        CaptureCompletedBar();
    }

    protected override void OnStop()
    {
        try
        {
            _writer?.Dispose();
        }
        finally
        {
            Print("Xen stopped for {0}. Captured {1} completed bars.", SymbolName, _capturedBars);
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
