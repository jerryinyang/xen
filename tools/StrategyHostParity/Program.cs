using System;
using System.Collections.Generic;
using System.Globalization;
using Xen.StrategyHost;

namespace StrategyHostParity;

internal static class Program
{
    public static int Main(string[] args)
    {
        try
        {
            var options = Options.Parse(args);
            var analysisEndUtc = ParseUtc(options.AnalysisEndUtc);
            StrategyHostParityExporter.Export(
                options.InputPath,
                options.OutputDirectory,
                analysisEndUtc);
            return 0;
        }
        catch (Exception exc)
        {
            Console.Error.WriteLine(exc.Message);
            return 1;
        }
    }

    private static DateTime ParseUtc(string value)
    {
        if (!DateTime.TryParse(
                value,
                CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal,
                out var parsed))
        {
            throw new ArgumentException($"Invalid --analysis-end value: {value}");
        }
        return parsed;
    }

    private sealed record Options(string InputPath, string OutputDirectory, string AnalysisEndUtc)
    {
        public static Options Parse(IReadOnlyList<string> args)
        {
            string? input = null;
            string? output = null;
            string? analysisEnd = null;

            for (var i = 0; i < args.Count; i++)
            {
                var key = args[i];
                if (key is "--input" && i + 1 < args.Count)
                    input = args[++i];
                else if (key is "--output" && i + 1 < args.Count)
                    output = args[++i];
                else if (key is "--analysis-end" && i + 1 < args.Count)
                    analysisEnd = args[++i];
                else if (key is "--help" or "-h")
                    throw new ArgumentException("Usage: StrategyHostParity --input <timebars.parquet> --output <dir> --analysis-end <utc iso>");
                else
                    throw new ArgumentException($"Unknown or incomplete argument: {key}");
            }

            if (string.IsNullOrWhiteSpace(input))
                throw new ArgumentException("--input is required.");
            if (string.IsNullOrWhiteSpace(output))
                throw new ArgumentException("--output is required.");
            if (string.IsNullOrWhiteSpace(analysisEnd))
                throw new ArgumentException("--analysis-end is required.");

            return new Options(input, output, analysisEnd);
        }
    }
}
