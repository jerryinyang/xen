namespace Xen.StrategyHost;

public sealed record RenkoBrick(
    DateTime OpenTime,
    DateTime CloseTime,
    double Open,
    double High,
    double Low,
    double Close,
    int Direction,
    double BrickSize,
    int ATRPeriod,
    int SourceCount,
    DateTime SourceCloseTime);

public sealed class RenkoGenerator
{
    private readonly Queue<double> _trueRanges = new();
    private double? _anchorClose;
    private double? _previousClose;
    private int _pendingCount;

    public RenkoGenerator(int atrPeriod = 14)
    {
        if (atrPeriod < 1)
            throw new ArgumentOutOfRangeException(nameof(atrPeriod), atrPeriod, "atrPeriod must be >= 1.");
        AtrPeriod = atrPeriod;
    }

    public int AtrPeriod { get; }

    public IReadOnlyList<RenkoBrick> Update(TimeBar bar)
    {
        _pendingCount++;

        _anchorClose ??= bar.Close;

        var trueRange = TrueRange(bar.High, bar.Low);
        _trueRanges.Enqueue(trueRange);
        if (_trueRanges.Count > AtrPeriod)
            _trueRanges.Dequeue();
        _previousClose = bar.Close;

        if (_trueRanges.Count < AtrPeriod)
            return Array.Empty<RenkoBrick>();

        var brickSize = _trueRanges.Sum() / AtrPeriod;
        if (brickSize <= 0.0)
            return Array.Empty<RenkoBrick>();

        var rows = new List<RenkoBrick>();
        while (_anchorClose.HasValue && bar.Close >= _anchorClose.Value + brickSize)
        {
            rows.Add(AppendBrick(
                bar.OpenTime,
                bar.CloseTime,
                _anchorClose.Value,
                _anchorClose.Value + brickSize,
                brickSize,
                1));
        }
        while (_anchorClose.HasValue && bar.Close <= _anchorClose.Value - brickSize)
        {
            rows.Add(AppendBrick(
                bar.OpenTime,
                bar.CloseTime,
                _anchorClose.Value,
                _anchorClose.Value - brickSize,
                brickSize,
                -1));
        }
        return rows;
    }

    private double TrueRange(double high, double low)
    {
        if (!_previousClose.HasValue)
            return high - low;
        return Math.Max(high - low, Math.Max(Math.Abs(high - _previousClose.Value), Math.Abs(low - _previousClose.Value)));
    }

    private RenkoBrick AppendBrick(
        DateTime openTime,
        DateTime closeTime,
        double open,
        double close,
        double brickSize,
        int direction)
    {
        var brick = new RenkoBrick(
            openTime,
            closeTime,
            open,
            Math.Max(open, close),
            Math.Min(open, close),
            close,
            direction,
            brickSize,
            AtrPeriod,
            _pendingCount,
            closeTime);
        _anchorClose = close;
        _pendingCount = 0;
        return brick;
    }
}
