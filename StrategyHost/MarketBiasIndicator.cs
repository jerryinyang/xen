namespace Xen.StrategyHost;

public sealed record MarketBiasRecord(
    TimeBar Bar,
    double OscBias,
    double OscSmooth,
    string? SignState,
    string? FourWayState);

public sealed record MarketBiasWarmup(int WConverge, int W, bool Converged);

public static class MarketBiasIndicator
{
    public const int HaLen = 100;
    public const int HaLen2 = 100;
    public const int OscLen = 7;
    public const int WarmupFloor = 300;

    public const string SignBull = "bull";
    public const string SignBear = "bear";
    public const string StrongBull = "strong_bull";
    public const string WeakBull = "weak_bull";
    public const string StrongBear = "strong_bear";
    public const string WeakBear = "weak_bear";

    public static IReadOnlyList<MarketBiasRecord> Compute(IReadOnlyList<TimeBar> bars, string seed = "sma")
    {
        if (seed != "sma" && seed != "cold")
            throw new ArgumentException("seed must be 'sma' or 'cold'.", nameof(seed));

        var open = bars.Select(bar => bar.Open).ToArray();
        var high = bars.Select(bar => bar.High).ToArray();
        var low = bars.Select(bar => bar.Low).ToArray();
        var close = bars.Select(bar => bar.Close).ToArray();
        var (oscBias, oscSmooth) = Oscillator(open, high, low, close, seed);
        var signStates = SignStates(oscBias);
        var fourWayStates = FourWayStates(oscBias, oscSmooth);

        var output = new List<MarketBiasRecord>(bars.Count);
        for (var i = 0; i < bars.Count; i++)
            output.Add(new MarketBiasRecord(bars[i], oscBias[i], oscSmooth[i], signStates[i], fourWayStates[i]));
        return output;
    }

    public static MarketBiasWarmup ConvergenceWarmup(IReadOnlyList<TimeBar> bars, int floor = WarmupFloor)
    {
        var sma = Compute(bars, "sma").Select(row => row.FourWayState).ToArray();
        var cold = Compute(bars, "cold").Select(row => row.FourWayState).ToArray();
        var lastDiff = -1;
        var firstDefined = -1;

        for (var i = 0; i < sma.Length; i++)
        {
            var bothDefined = sma[i] is not null && cold[i] is not null;
            if (bothDefined && firstDefined < 0)
                firstDefined = i;
            if (bothDefined && sma[i] != cold[i])
                lastDiff = i;
        }

        var wConverge = lastDiff >= 0 ? lastDiff + 1 : firstDefined >= 0 ? firstDefined : sma.Length;
        return new MarketBiasWarmup(wConverge, Math.Max(wConverge, floor), wConverge < sma.Length);
    }

    private static (double[] OscBias, double[] OscSmooth) Oscillator(
        double[] open,
        double[] high,
        double[] low,
        double[] close,
        string seed)
    {
        var smOpen = Ema(open, HaLen, seed);
        var smHigh = Ema(high, HaLen, seed);
        var smLow = Ema(low, HaLen, seed);
        var smClose = Ema(close, HaLen, seed);
        var (haOpen, haClose) = HeikenAshi(smOpen, smHigh, smLow, smClose);
        var o2 = Ema(haOpen, HaLen2, seed);
        var c2 = Ema(haClose, HaLen2, seed);
        var oscBias = new double[open.Length];
        for (var i = 0; i < oscBias.Length; i++)
            oscBias[i] = 100.0 * (c2[i] - o2[i]);
        var oscSmooth = Ema(oscBias, OscLen, seed);
        return (oscBias, oscSmooth);
    }

    private static double[] Ema(double[] values, int length, string seed)
    {
        var output = Enumerable.Repeat(double.NaN, values.Length).ToArray();
        if (values.Length == 0)
            return output;

        var alpha = 2.0 / (length + 1.0);
        var start = 1;
        if (seed == "sma" && values.Length >= length && values.Take(length).All(double.IsFinite))
        {
            output[length - 1] = values.Take(length).Average();
            start = length;
        }
        else
        {
            output[0] = values[0];
        }

        for (var i = start; i < values.Length; i++)
        {
            var previous = output[i - 1];
            output[i] = !double.IsFinite(previous) ? values[i] : alpha * values[i] + (1.0 - alpha) * previous;
        }
        return output;
    }

    private static (double[] HaOpen, double[] HaClose) HeikenAshi(
        double[] open,
        double[] high,
        double[] low,
        double[] close)
    {
        var haClose = new double[open.Length];
        var xhaOpen = new double[open.Length];
        var haOpen = Enumerable.Repeat(double.NaN, open.Length).ToArray();
        if (open.Length == 0)
            return (haOpen, haClose);

        for (var i = 0; i < open.Length; i++)
        {
            haClose[i] = (open[i] + high[i] + low[i] + close[i]) / 4.0;
            xhaOpen[i] = (open[i] + close[i]) / 2.0;
        }

        haOpen[0] = (open[0] + close[0]) / 2.0;
        for (var i = 1; i < open.Length; i++)
            haOpen[i] = (xhaOpen[i - 1] + haClose[i - 1]) / 2.0;
        return (haOpen, haClose);
    }

    private static string?[] SignStates(double[] oscBias)
    {
        var states = new string?[oscBias.Length];
        string? previous = null;
        for (var i = 0; i < oscBias.Length; i++)
        {
            var value = oscBias[i];
            if (!double.IsFinite(value))
            {
                states[i] = null;
                continue;
            }
            if (value > 0.0)
                previous = SignBull;
            else if (value < 0.0)
                previous = SignBear;
            states[i] = previous;
        }
        return states;
    }

    private static string?[] FourWayStates(double[] oscBias, double[] oscSmooth)
    {
        var states = new string?[oscBias.Length];
        for (var i = 0; i < oscBias.Length; i++)
        {
            if (!(double.IsFinite(oscBias[i]) && double.IsFinite(oscSmooth[i])))
                continue;
            if (oscBias[i] > 0.0)
                states[i] = oscBias[i] >= oscSmooth[i] ? StrongBull : WeakBull;
            else if (oscBias[i] < 0.0)
                states[i] = oscBias[i] <= oscSmooth[i] ? StrongBear : WeakBear;
        }
        return states;
    }
}
