using Parquet;
using Parquet.Schema;

namespace Xen.StrategyHost;

public static class TimeBarParquetReader
{
    public static IReadOnlyList<TimeBar> ReadBefore(string path, HoldoutFence fence)
    {
        if (!File.Exists(path))
            throw new FileNotFoundException("Time-bar Parquet file not found.", path);

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
            var openTimes = ReadColumn<DateTime>(rowGroup, openTimeField);
            var closeTimes = ReadColumn<DateTime>(rowGroup, closeTimeField);
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

    private static T[] ReadColumn<T>(IParquetRowGroupReader rowGroup, DataField field)
    {
        var column = rowGroup.ReadColumnAsync(field).GetAwaiter().GetResult();
        return column.Data.Cast<T>().ToArray();
    }
}
