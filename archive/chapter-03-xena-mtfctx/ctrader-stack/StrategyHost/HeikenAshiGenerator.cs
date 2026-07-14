namespace Xen.StrategyHost;

public sealed record HeikenAshiBar(
    DateTime OpenTime,
    DateTime CloseTime,
    double HAOpen,
    double HAHigh,
    double HALow,
    double HAClose,
    double RealOpen,
    double RealHigh,
    double RealLow,
    double RealClose,
    int Direction,
    int SourceCount);

public sealed class HeikenAshiGenerator
{
    private double? _previousHaOpen;
    private double? _previousHaClose;

    public HeikenAshiBar Update(TimeBar bar)
    {
        var haClose = (bar.Open + bar.High + bar.Low + bar.Close) / 4.0;
        var haOpen = !_previousHaOpen.HasValue || !_previousHaClose.HasValue
            ? (bar.Open + bar.Close) / 2.0
            : (_previousHaOpen.Value + _previousHaClose.Value) / 2.0;
        var haHigh = Math.Max(bar.High, Math.Max(haOpen, haClose));
        var haLow = Math.Min(bar.Low, Math.Min(haOpen, haClose));

        _previousHaOpen = haOpen;
        _previousHaClose = haClose;

        return new HeikenAshiBar(
            bar.OpenTime,
            bar.CloseTime,
            haOpen,
            haHigh,
            haLow,
            haClose,
            bar.Open,
            bar.High,
            bar.Low,
            bar.Close,
            haClose >= haOpen ? 1 : -1,
            1);
    }
}
