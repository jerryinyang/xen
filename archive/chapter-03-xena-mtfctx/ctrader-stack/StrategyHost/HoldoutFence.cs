namespace Xen.StrategyHost;

public sealed class HoldoutFence
{
    public HoldoutFence(DateTime analysisEndUtc)
    {
        AnalysisEndUtc = AsUtc(analysisEndUtc);
    }

    public DateTime AnalysisEndUtc { get; }

    public bool ShouldStopBeforeProcessing(DateTime sourceCloseTime)
    {
        return AsUtc(sourceCloseTime) >= AnalysisEndUtc;
    }

    public void AssertCanEmit(DateTime sourceCloseTime)
    {
        var timestamp = AsUtc(sourceCloseTime);
        if (timestamp >= AnalysisEndUtc)
        {
            throw new InvalidOperationException(
                $"Refusing to emit strategy output at or after AnalysisEndUtc: {timestamp:o} >= {AnalysisEndUtc:o}");
        }
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
}
