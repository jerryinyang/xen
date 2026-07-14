namespace Xen.StrategyHost;

public sealed class StrategyHostRunner
{
    private readonly BarAggregator _aggregator;
    private readonly ISignalModel _model;
    private readonly HoldoutFence _fence;
    private readonly string _domain;

    public StrategyHostRunner(
        BarAggregator aggregator,
        ISignalModel model,
        HoldoutFence fence,
        string domain)
    {
        _aggregator = aggregator;
        _model = model;
        _fence = fence;
        _domain = domain;
    }

    public IReadOnlyList<SignalUpdate> Run(IEnumerable<TimeBar> sourceBars)
    {
        var output = new List<SignalUpdate>();
        foreach (var sourceBar in sourceBars)
        {
            if (_fence.ShouldStopBeforeProcessing(sourceBar.CloseTime))
            {
                output.AddRange(ProcessDomainBars(_aggregator.Flush()));
                return output;
            }

            output.AddRange(ProcessDomainBars(_aggregator.Update(sourceBar)));
        }

        output.AddRange(ProcessDomainBars(_aggregator.Flush()));
        return output;
    }

    private IReadOnlyList<SignalUpdate> ProcessDomainBars(IEnumerable<TimeBar> domainBars)
    {
        var output = new List<SignalUpdate>();
        foreach (var domainBar in domainBars)
        {
            if (_fence.ShouldStopBeforeProcessing(domainBar.CloseTime))
                break;

            var update = _model.OnBar(domainBar, _domain);
            AssertWithinFence(update);
            output.Add(update);
        }
        return output;
    }

    private void AssertWithinFence(SignalUpdate update)
    {
        _fence.AssertCanEmit(update.Position.SourceCloseTime);
        foreach (var eventRecord in update.Events)
            _fence.AssertCanEmit(eventRecord.SourceCloseTime);
        foreach (var trade in update.Trades)
            _fence.AssertCanEmit(trade.SourceCloseTime);
    }
}
