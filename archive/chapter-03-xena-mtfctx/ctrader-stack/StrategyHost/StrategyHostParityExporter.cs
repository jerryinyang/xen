using System.Globalization;
using System.Text.Json;

namespace Xen.StrategyHost;

public static class StrategyHostParityExporter
{
    private static readonly DomainSpec[] DomainSpecs =
    {
        new("5m", 5, null),
        new("1h", 60, 0.90),
        new("4h", 240, 0.90)
    };

    public static string Export(string inputPath, string outputDirectory, DateTime analysisEndUtc)
    {
        var fence = new HoldoutFence(analysisEndUtc);
        var sourceBars = TimeBarParquetReader.ReadBefore(inputPath, fence);
        EnsureSorted(sourceBars);

        Directory.CreateDirectory(outputDirectory);
        WriteMetadata(inputPath, outputDirectory, fence, sourceBars);
        WriteLineBreak(Path.Combine(outputDirectory, "linebreak.csv"), sourceBars);
        WriteRenko(Path.Combine(outputDirectory, "renko.csv"), sourceBars);
        WriteHeikenAshi(Path.Combine(outputDirectory, "heiken_ashi.csv"), sourceBars);

        foreach (var spec in DomainSpecs)
        {
            var domainBars = BarAggregator.Aggregate(sourceBars, spec.PeriodMinutes, spec.MinCoverage);
            WriteTimeBars(Path.Combine(outputDirectory, $"bar_aggregator_{spec.Label}.csv"), domainBars);
            WriteMarketBias(Path.Combine(outputDirectory, $"market_bias_{spec.Label}.csv"), domainBars);
            WriteMarketBiasWarmup(Path.Combine(outputDirectory, $"market_bias_warmup_{spec.Label}.csv"), domainBars);
            WriteMovingAverageCrossover(outputDirectory, spec, sourceBars, fence);
            WriteDonchian(outputDirectory, spec, sourceBars, fence);
        }

        return outputDirectory;
    }

    private static void WriteMetadata(
        string inputPath,
        string outputDirectory,
        HoldoutFence fence,
        IReadOnlyList<TimeBar> sourceBars)
    {
        var payload = new
        {
            input_path = inputPath,
            input_file = Path.GetFileName(inputPath),
            symbol = sourceBars.Count > 0 ? sourceBars[0].Symbol : null,
            analysis_end_utc = fence.AnalysisEndUtc.ToString("O", CultureInfo.InvariantCulture),
            generated_utc = DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture),
            source_rows = sourceBars.Count,
            domains = DomainSpecs.Select(spec => new
            {
                label = spec.Label,
                period_minutes = spec.PeriodMinutes,
                min_coverage = spec.MinCoverage
            }).ToArray()
        };
        File.WriteAllText(
            Path.Combine(outputDirectory, "export_metadata.json"),
            JsonSerializer.Serialize(payload, new JsonSerializerOptions { WriteIndented = true }));
    }

    private static void WriteLineBreak(string path, IReadOnlyList<TimeBar> sourceBars)
    {
        var generator = new LineBreakGenerator(level: 3);
        using var writer = CreateCsv(path, "OpenTime,CloseTime,Open,High,Low,Close,Direction,Level,SourceCount,SourceCloseTime");
        foreach (var bar in sourceBars)
        {
            foreach (var line in generator.Update(bar))
            {
                writer.WriteLine(string.Join(
                    ",",
                    Time(line.OpenTime),
                    Time(line.CloseTime),
                    Float(line.Open),
                    Float(line.High),
                    Float(line.Low),
                    Float(line.Close),
                    line.Direction.ToString(CultureInfo.InvariantCulture),
                    line.Level.ToString(CultureInfo.InvariantCulture),
                    line.SourceCount.ToString(CultureInfo.InvariantCulture),
                    Time(line.SourceCloseTime)));
            }
        }
    }

    private static void WriteRenko(string path, IReadOnlyList<TimeBar> sourceBars)
    {
        var generator = new RenkoGenerator(atrPeriod: 14);
        using var writer = CreateCsv(path, "OpenTime,CloseTime,Open,High,Low,Close,Direction,BrickSize,ATRPeriod,SourceCount,SourceCloseTime");
        foreach (var bar in sourceBars)
        {
            foreach (var brick in generator.Update(bar))
            {
                writer.WriteLine(string.Join(
                    ",",
                    Time(brick.OpenTime),
                    Time(brick.CloseTime),
                    Float(brick.Open),
                    Float(brick.High),
                    Float(brick.Low),
                    Float(brick.Close),
                    brick.Direction.ToString(CultureInfo.InvariantCulture),
                    Float(brick.BrickSize),
                    brick.ATRPeriod.ToString(CultureInfo.InvariantCulture),
                    brick.SourceCount.ToString(CultureInfo.InvariantCulture),
                    Time(brick.SourceCloseTime)));
            }
        }
    }

    private static void WriteHeikenAshi(string path, IReadOnlyList<TimeBar> sourceBars)
    {
        var generator = new HeikenAshiGenerator();
        using var writer = CreateCsv(path, "OpenTime,CloseTime,HAOpen,HAHigh,HALow,HAClose,RealOpen,RealHigh,RealLow,RealClose,Direction,SourceCount");
        foreach (var bar in sourceBars)
        {
            var ha = generator.Update(bar);
            writer.WriteLine(string.Join(
                ",",
                Time(ha.OpenTime),
                Time(ha.CloseTime),
                Float(ha.HAOpen),
                Float(ha.HAHigh),
                Float(ha.HALow),
                Float(ha.HAClose),
                Float(ha.RealOpen),
                Float(ha.RealHigh),
                Float(ha.RealLow),
                Float(ha.RealClose),
                ha.Direction.ToString(CultureInfo.InvariantCulture),
                ha.SourceCount.ToString(CultureInfo.InvariantCulture)));
        }
    }

    private static void WriteTimeBars(string path, IReadOnlyList<TimeBar> bars)
    {
        using var writer = CreateCsv(path, "Symbol,OpenTime,CloseTime,Open,High,Low,Close,TickVolume,SourceBars");
        foreach (var bar in bars)
        {
            writer.WriteLine(string.Join(
                ",",
                Csv(bar.Symbol),
                Time(bar.OpenTime),
                Time(bar.CloseTime),
                Float(bar.Open),
                Float(bar.High),
                Float(bar.Low),
                Float(bar.Close),
                bar.TickVolume.ToString(CultureInfo.InvariantCulture),
                bar.SourceBars.ToString(CultureInfo.InvariantCulture)));
        }
    }

    private static void WriteMarketBias(string path, IReadOnlyList<TimeBar> bars)
    {
        var records = MarketBiasIndicator.Compute(bars);
        using var writer = CreateCsv(path, "CloseTime,osc_bias,osc_smooth,sign_state,four_way_state");
        foreach (var record in records)
        {
            writer.WriteLine(string.Join(
                ",",
                Time(record.Bar.CloseTime),
                Float(record.OscBias),
                Float(record.OscSmooth),
                Csv(record.SignState ?? string.Empty),
                Csv(record.FourWayState ?? string.Empty)));
        }
    }

    private static void WriteMarketBiasWarmup(string path, IReadOnlyList<TimeBar> bars)
    {
        var warmup = MarketBiasIndicator.ConvergenceWarmup(bars);
        using var writer = CreateCsv(path, "w_converge,W,converged");
        writer.WriteLine(string.Join(
            ",",
            warmup.WConverge.ToString(CultureInfo.InvariantCulture),
            warmup.W.ToString(CultureInfo.InvariantCulture),
            warmup.Converged ? "true" : "false"));
    }

    private static void WriteMovingAverageCrossover(
        string outputDirectory,
        DomainSpec spec,
        IReadOnlyList<TimeBar> sourceBars,
        HoldoutFence fence)
    {
        var runner = new StrategyHostRunner(
            new BarAggregator(spec.PeriodMinutes, spec.MinCoverage),
            new MovingAverageCrossoverModel(),
            fence,
            spec.Label);
        var updates = runner.Run(sourceBars);

        using var positions = CreateCsv(
            Path.Combine(outputDirectory, $"ma_crossover_positions_{spec.Label}.csv"),
            "SourceCloseTime,Domain,Strategy,Position,SignalValue,RealOpen,RealHigh,RealLow,RealClose,Warmup,IsFlat");
        using var events = CreateCsv(
            Path.Combine(outputDirectory, $"ma_crossover_events_{spec.Label}.csv"),
            "SourceCloseTime,Domain,Strategy,EventType,Position,PreviousPosition,SignalValue");
        using var trades = CreateCsv(
            Path.Combine(outputDirectory, $"ma_crossover_trades_{spec.Label}.csv"),
            "SourceCloseTime,Domain,Strategy,Action,PreviousPosition,Position,Price,PositionDelta,TradeSequence");

        foreach (var update in updates)
        {
            var position = update.Position;
            positions.WriteLine(string.Join(
                ",",
                Time(position.SourceCloseTime),
                Csv(position.Domain),
                Csv(position.Strategy),
                position.Position.ToString(CultureInfo.InvariantCulture),
                Float(position.SignalValue),
                Float(position.RealOpen),
                Float(position.RealHigh),
                Float(position.RealLow),
                Float(position.RealClose),
                position.Warmup ? "true" : "false",
                position.IsFlat ? "true" : "false"));

            foreach (var eventRecord in update.Events)
            {
                events.WriteLine(string.Join(
                    ",",
                    Time(eventRecord.SourceCloseTime),
                    Csv(eventRecord.Domain),
                    Csv(eventRecord.Strategy),
                    Csv(eventRecord.EventType),
                    eventRecord.Position.ToString(CultureInfo.InvariantCulture),
                    eventRecord.PreviousPosition.ToString(CultureInfo.InvariantCulture),
                    Float(eventRecord.SignalValue)));
            }

            foreach (var trade in update.Trades)
            {
                trades.WriteLine(string.Join(
                    ",",
                    Time(trade.SourceCloseTime),
                    Csv(trade.Domain),
                    Csv(trade.Strategy),
                    Csv(trade.Action),
                    trade.PreviousPosition.ToString(CultureInfo.InvariantCulture),
                    trade.Position.ToString(CultureInfo.InvariantCulture),
                    Float(trade.Price),
                    Float(trade.PositionDelta),
                    trade.TradeSequence.ToString(CultureInfo.InvariantCulture)));
            }
        }
    }

    private static void WriteDonchian(
        string outputDirectory,
        DomainSpec spec,
        IReadOnlyList<TimeBar> sourceBars,
        HoldoutFence fence)
    {
        var runner = new StrategyHostRunner(
            new BarAggregator(spec.PeriodMinutes, spec.MinCoverage),
            new DonchianBreakoutModel(),
            fence,
            spec.Label);
        var updates = runner.Run(sourceBars);

        using var positions = CreateCsv(
            Path.Combine(outputDirectory, $"donchian_20_positions_{spec.Label}.csv"),
            "SourceCloseTime,Domain,Strategy,Position,SignalValue,RealOpen,RealHigh,RealLow,RealClose,Warmup,IsFlat");
        foreach (var update in updates)
        {
            var position = update.Position;
            positions.WriteLine(string.Join(
                ",",
                Time(position.SourceCloseTime),
                Csv(position.Domain),
                Csv(position.Strategy),
                position.Position.ToString(CultureInfo.InvariantCulture),
                Float(position.SignalValue),
                Float(position.RealOpen),
                Float(position.RealHigh),
                Float(position.RealLow),
                Float(position.RealClose),
                position.Warmup ? "true" : "false",
                position.IsFlat ? "true" : "false"));
        }
    }

    private static StreamWriter CreateCsv(string path, string header)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path) ?? ".");
        var writer = new StreamWriter(path, append: false);
        writer.WriteLine(header);
        return writer;
    }

    private static string Float(double value)
    {
        return double.IsNaN(value) ? "NaN" : value.ToString("R", CultureInfo.InvariantCulture);
    }

    private static string Time(DateTime value)
    {
        return AsUtc(value).ToString("O", CultureInfo.InvariantCulture);
    }

    private static string Csv(string value)
    {
        if (!(value.Contains(',') || value.Contains('"') || value.Contains('\n') || value.Contains('\r')))
            return value;
        return "\"" + value.Replace("\"", "\"\"") + "\"";
    }

    private static DateTime AsUtc(DateTime value)
    {
        return value.Kind switch
        {
            DateTimeKind.Utc => value,
            DateTimeKind.Local => value.ToUniversalTime(),
            _ => DateTime.SpecifyKind(value, DateTimeKind.Utc)
        };
    }

    private static void EnsureSorted(IReadOnlyList<TimeBar> bars)
    {
        for (var i = 1; i < bars.Count; i++)
        {
            if (bars[i].CloseTime < bars[i - 1].CloseTime)
                throw new InvalidOperationException("Source bars must be sorted by CloseTime.");
        }
    }

    private sealed record DomainSpec(string Label, int PeriodMinutes, double? MinCoverage);
}
