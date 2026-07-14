namespace Xen.StrategyHost;

public interface ISignalModel
{
    string StrategyName { get; }

    SignalUpdate OnBar(TimeBar bar, string domain);
}
