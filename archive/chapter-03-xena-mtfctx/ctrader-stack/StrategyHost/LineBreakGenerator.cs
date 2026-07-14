namespace Xen.StrategyHost;

public sealed record LineBreakLine(
    DateTime OpenTime,
    DateTime CloseTime,
    double Open,
    double High,
    double Low,
    double Close,
    int Direction,
    int Level,
    int SourceCount,
    DateTime SourceCloseTime);

public sealed class LineBreakGenerator
{
    private readonly List<LineBreakLine> _lines = new();
    private int _pendingCount;

    public LineBreakGenerator(int level = 3)
    {
        if (level < 1)
            throw new ArgumentOutOfRangeException(nameof(level), level, "level must be >= 1.");
        Level = level;
    }

    public int Level { get; }

    public IReadOnlyList<LineBreakLine> Update(TimeBar bar)
    {
        _pendingCount++;

        if (_lines.Count == 0)
        {
            return new[]
            {
                AppendLine(bar.OpenTime, bar.CloseTime, bar.Close, bar.Close, bar.Close >= bar.Open ? 1 : -1)
            };
        }

        var last = _lines[^1];
        if (last.Direction >= 0 && bar.Close > last.Close)
        {
            return new[] { AppendLine(bar.OpenTime, bar.CloseTime, last.Close, bar.Close, 1) };
        }
        if (last.Direction <= 0 && bar.Close < last.Close)
        {
            return new[] { AppendLine(bar.OpenTime, bar.CloseTime, last.Close, bar.Close, -1) };
        }

        var start = Math.Max(0, _lines.Count - Level);
        var reversalHigh = _lines.Skip(start).Max(line => line.High);
        var reversalLow = _lines.Skip(start).Min(line => line.Low);

        if (bar.Close > reversalHigh)
            return new[] { AppendLine(bar.OpenTime, bar.CloseTime, last.Close, bar.Close, 1) };
        if (bar.Close < reversalLow)
            return new[] { AppendLine(bar.OpenTime, bar.CloseTime, last.Close, bar.Close, -1) };

        return Array.Empty<LineBreakLine>();
    }

    private LineBreakLine AppendLine(
        DateTime openTime,
        DateTime closeTime,
        double open,
        double close,
        int direction)
    {
        var line = new LineBreakLine(
            openTime,
            closeTime,
            open,
            Math.Max(open, close),
            Math.Min(open, close),
            close,
            direction,
            Level,
            _pendingCount,
            closeTime);
        _lines.Add(line);
        _pendingCount = 0;
        return line;
    }
}
