using Parquet;
using Parquet.Schema;

namespace Xen.StrategyHost;

public static class TimeBarParquetReader
{
    private static readonly string[] AnalysisSliceMarkers = { "analysis70", "analysis_slice", "first70" };
    private const long NanosecondsPerTick = 100;

    public static IReadOnlyList<TimeBar> ReadBefore(string path, HoldoutFence fence)
    {
        if (!File.Exists(path))
            throw new FileNotFoundException("Time-bar Parquet file not found.", path);

        AssertPreSlicedAnalysisInput(path);
        var output = new List<TimeBar>();
        using var reader = ParquetReader.CreateAsync(path).GetAwaiter().GetResult();
        var symbolField = reader.Schema.FindDataField("Symbol");
        var openTimeField = reader.Schema.FindDataField("OpenTime");
        var closeTimeField = reader.Schema.FindDataField("CloseTime");
        var openField = reader.Schema.FindDataField("Open");
        var highField = reader.Schema.FindDataField("High");
        var lowField = reader.Schema.FindDataField("Low");
        var closeField = reader.Schema.FindDataField("Close");
        var tickVolumeField = reader.Schema.FindDataField("TickVolume");

        for (var groupIndex = 0; groupIndex < reader.RowGroupCount; groupIndex++)
        {
            using var rowGroup = reader.OpenRowGroupReader(groupIndex);
            var symbols = ReadColumn<string>(rowGroup, symbolField);
            var openTimes = ReadDateTimeColumn(rowGroup, openTimeField);
            var closeTimes = ReadDateTimeColumn(rowGroup, closeTimeField);
            var opens = ReadColumn<double>(rowGroup, openField);
            var highs = ReadColumn<double>(rowGroup, highField);
            var lows = ReadColumn<double>(rowGroup, lowField);
            var closes = ReadColumn<double>(rowGroup, closeField);
            var tickVolumes = ReadColumn<long>(rowGroup, tickVolumeField);

            for (var rowIndex = 0; rowIndex < rowGroup.RowCount; rowIndex++)
            {
                if (fence.ShouldStopBeforeProcessing(closeTimes[rowIndex]))
                    return output;

                output.Add(new TimeBar(
                    symbols[rowIndex],
                    openTimes[rowIndex],
                    closeTimes[rowIndex],
                    opens[rowIndex],
                    highs[rowIndex],
                    lows[rowIndex],
                    closes[rowIndex],
                    tickVolumes[rowIndex]));
            }
        }

        return output;
    }

    private static void AssertPreSlicedAnalysisInput(string path)
    {
        var fileName = Path.GetFileName(path).ToLowerInvariant();
        if (AnalysisSliceMarkers.Any(marker => fileName.Contains(marker, StringComparison.Ordinal)))
            return;

        throw new InvalidOperationException(
            "Fixed-Parquet replay requires an explicitly pre-sliced first-70 analysis input. " +
            "Use a file name containing analysis70, analysis_slice, or first70 so the final holdout " +
            "partition is never opened by the replay reader.");
    }

    private static T[] ReadColumn<T>(IParquetRowGroupReader rowGroup, DataField field)
    {
        var column = rowGroup.ReadColumnAsync(field).GetAwaiter().GetResult();
        return column.Data.Cast<T>().ToArray();
    }

    private static DateTime[] ReadDateTimeColumn(IParquetRowGroupReader rowGroup, DataField field)
    {
        // Parquet.Net 4.x maps only millisecond/microsecond timestamps to DateTime; the canonical
        // polars TIMESTAMP(NANOS) time-bar columns fall back to their physical INT64
        // nanoseconds-since-Unix-epoch payload (and the columns are nullable). Box each element and
        // dispatch on its runtime type so every representation re-hydrates to a UTC DateTime.
        var data = rowGroup.ReadColumnAsync(field).GetAwaiter().GetResult().Data;
        var result = new DateTime[data.Length];
        for (var rowIndex = 0; rowIndex < data.Length; rowIndex++)
        {
            result[rowIndex] = data.GetValue(rowIndex) switch
            {
                DateTime value => value,
                DateTimeOffset value => value.UtcDateTime,
                long nanoseconds => NanosecondsSinceEpochToUtc(nanoseconds),
                null => throw new InvalidOperationException(
                    $"Null timestamp in required column '{field.Name}' at row {rowIndex}."),
                var value => throw new InvalidOperationException(
                    $"Unsupported timestamp representation for column '{field.Name}': {value.GetType().Name}.")
            };
        }

        return result;
    }

    private static DateTime NanosecondsSinceEpochToUtc(long nanoseconds)
    {
        return DateTime.UnixEpoch.AddTicks(nanoseconds / NanosecondsPerTick);
    }
}
