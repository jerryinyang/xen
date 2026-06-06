namespace Xen.StrategyHost;

public sealed record TimeBar(
    string Symbol,
    DateTime OpenTime,
    DateTime CloseTime,
    double Open,
    double High,
    double Low,
    double Close,
    long TickVolume,
    int SourceBars = 1);
