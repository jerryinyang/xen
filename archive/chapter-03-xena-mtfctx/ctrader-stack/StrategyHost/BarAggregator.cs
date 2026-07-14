namespace Xen.StrategyHost;

public sealed class BarAggregator
{
    private static readonly DateTime Epoch = new(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc);

    private readonly int _periodMinutes;
    private readonly double? _minCoverage;
    private readonly List<TimeBar> _bucket = new();
    private long? _bucketKey;
    private DateTime? _previousCloseTime;

    public BarAggregator(int periodMinutes, double? minCoverage = null)
    {
        if (periodMinutes < 2)
            throw new ArgumentOutOfRangeException(nameof(periodMinutes), periodMinutes, "periodMinutes must be >= 2.");
        if (minCoverage.HasValue && (minCoverage.Value <= 0.0 || minCoverage.Value > 1.0))
            throw new ArgumentOutOfRangeException(nameof(minCoverage), minCoverage, "minCoverage must be in (0, 1] or null.");

        _periodMinutes = periodMinutes;
        _minCoverage = minCoverage;
    }

    public IReadOnlyList<TimeBar> Update(TimeBar bar)
    {
        if (_previousCloseTime.HasValue && bar.CloseTime < _previousCloseTime.Value)
            throw new InvalidOperationException("Source bars must be sorted by CloseTime.");
        _previousCloseTime = bar.CloseTime;

        var key = BucketKey(bar.CloseTime, _periodMinutes);
        if (!_bucketKey.HasValue)
        {
            _bucketKey = key;
            _bucket.Add(bar);
            return Array.Empty<TimeBar>();
        }

        if (key != _bucketKey.Value)
        {
            var emitted = BuildIfRetained();
            _bucket.Clear();
            _bucketKey = key;
            _bucket.Add(bar);
            return emitted is null ? Array.Empty<TimeBar>() : new[] { emitted };
        }

        _bucket.Add(bar);
        return Array.Empty<TimeBar>();
    }

    public IReadOnlyList<TimeBar> Flush()
    {
        var emitted = BuildIfRetained();
        _bucket.Clear();
        _bucketKey = null;
        return emitted is null ? Array.Empty<TimeBar>() : new[] { emitted };
    }

    public static IReadOnlyList<TimeBar> Aggregate(IEnumerable<TimeBar> sourceBars, int periodMinutes, double? minCoverage = null)
    {
        var aggregator = new BarAggregator(periodMinutes, minCoverage);
        var output = new List<TimeBar>();
        foreach (var bar in sourceBars)
            output.AddRange(aggregator.Update(bar));
        output.AddRange(aggregator.Flush());
        return output;
    }

    private TimeBar? BuildIfRetained()
    {
        if (_bucket.Count == 0)
            return null;

        var required = _minCoverage.HasValue
            ? Math.Max(2, (int)Math.Ceiling(_minCoverage.Value * _periodMinutes))
            : _periodMinutes;
        if (_minCoverage.HasValue)
        {
            if (_bucket.Count < required)
                return null;
        }
        else if (_bucket.Count != required)
        {
            return null;
        }

        var first = _bucket[0];
        var last = _bucket[^1];
        return new TimeBar(
            first.Symbol,
            first.OpenTime,
            last.CloseTime,
            first.Open,
            _bucket.Max(bar => bar.High),
            _bucket.Min(bar => bar.Low),
            last.Close,
            _bucket.Sum(bar => bar.TickVolume),
            _bucket.Count);
    }

    private static long BucketKey(DateTime closeTime, int periodMinutes)
    {
        var utc = closeTime.Kind switch
        {
            DateTimeKind.Utc => closeTime,
            DateTimeKind.Local => closeTime.ToUniversalTime(),
            _ => DateTime.SpecifyKind(closeTime, DateTimeKind.Utc)
        };
        var seconds = (long)(utc - Epoch).TotalSeconds;
        return (seconds - 1) / (periodMinutes * 60L);
    }
}
