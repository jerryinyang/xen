using System;
using System.Globalization;
using Xen.StrategyHost;

namespace HtfDiSmoke;

// EXP-025 developer smoke harness: drives HtfDiBreakoutModel over a local m1 parquet
// through the SAME BarAggregator/StrategyHostRunner/HoldoutFence/StrategyRunParquetWriter
// stack the cTrader host uses (StrategyHostParity precedent), so the emission contract and
// the estimand gate can be checked before any credentialed engine run. It does NOT generate
// golden-trace expectations (QA diffs the designer's §13 table against the emission).
internal static class Program
{
    public static int Main(string[] args)
    {
        try
        {
            string? input = null, output = null, analysisEnd = null, exit = "e0", gate = "di";
            int x = 3, hold = 24, seed = 0, shift = 0;
            for (var i = 0; i < args.Length; i++)
            {
                switch (args[i])
                {
                    case "--input": input = args[++i]; break;
                    case "--output": output = args[++i]; break;
                    case "--analysis-end": analysisEnd = args[++i]; break;
                    case "--x": x = int.Parse(args[++i]); break;
                    case "--hold": hold = int.Parse(args[++i]); break;
                    case "--exit": exit = args[++i]; break;
                    case "--gate": gate = args[++i]; break;
                    case "--seed": seed = int.Parse(args[++i]); break;
                    case "--shift": shift = int.Parse(args[++i]); break;
                    default: throw new ArgumentException($"Unknown arg {args[i]}");
                }
            }
            if (input is null || output is null || analysisEnd is null)
                throw new ArgumentException(
                    "Usage: HtfDiSmoke --input <m1.parquet> --output <dir> --analysis-end <utc> " +
                    "[--x N] [--hold N] [--exit e0|e2|e3|e5|e6] [--gate di|adx|battery|state] [--seed N] [--shift N]");

            var analysisEndUtc = DateTime.Parse(analysisEnd, CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
            var exitKind = exit.ToLowerInvariant() switch
            {
                "e0" => HtfDiExit.E0FixedHold,
                "e2" => HtfDiExit.E2TrailXChannel,
                "e3" => HtfDiExit.E3HeikenAshi,
                "e5" => HtfDiExit.E5DiFlip,
                "e6" => HtfDiExit.E6OppositeBreak,
                _ => throw new ArgumentException($"exit {exit} not smoke-runnable (e1/e4 are native-only)")
            };
            var gateKind = gate.ToLowerInvariant() switch
            {
                "di" => HtfDiGateMode.Di,
                "adx" => HtfDiGateMode.AdxSentinel,
                "battery" => HtfDiGateMode.Battery,
                "state" => HtfDiGateMode.StateOnly,
                _ => throw new ArgumentException($"unknown gate {gate}")
            };

            var fence = new HoldoutFence(analysisEndUtc);
            var model = new HtfDiBreakoutModel(x, hold, exitKind, gateKind, seed, shift);
            var aggregator = new BarAggregator(5, null);   // strict, matching the 5m harness setting
            var symbol = System.IO.Path.GetFileName(input).Split('_')[1].ToUpperInvariant();
            var writer = new StrategyRunParquetWriter(output, model.StrategyName, symbol, "5m", fence,
                new System.Collections.Generic.Dictionary<string, object?>
                {
                    ["strategy"] = "HtfDiBreakout(smoke)", ["x"] = x, ["hold_bars"] = hold,
                    ["exit"] = exit, ["gate"] = gate, ["battery_seed"] = seed, ["phase_shift_bars"] = shift,
                    ["domain_minutes"] = 5, ["strict_coverage"] = true, ["min_coverage"] = (double?)null
                });

            var source = TimeBarParquetReader.ReadBefore(input, fence);
            var runner = new StrategyHostRunner(aggregator, model, fence, "5m");
            var updates = runner.Run(source);
            long tradeRows = 0;
            foreach (var update in updates)
            {
                writer.Append(update);
                foreach (var row in model.DrainTradeRows()) { writer.AppendCisTrade(row); tradeRows++; }
            }
            model.FlushOpenAsCensored("5m");
            foreach (var row in model.DrainTradeRows()) { writer.AppendCisTrade(row); tradeRows++; }
            var runDir = writer.RunDirectory;
            writer.Dispose();
            Console.WriteLine($"smoke ok: source_bars={source.Count} domain_bars={updates.Count} " +
                              $"trade_rows={tradeRows} run_dir={runDir}");
            return 0;
        }
        catch (Exception exc)
        {
            Console.Error.WriteLine(exc);
            return 1;
        }
    }
}
