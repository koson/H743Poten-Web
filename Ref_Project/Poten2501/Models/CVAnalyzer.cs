using ScottPlot;
using System;
using System.Collections.Generic;
using System.Formats.Asn1;
using System.Globalization;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CsvHelper;
using static System.Runtime.InteropServices.JavaScript.JSType;

namespace Poten2501.Models
{
    public class CVAnalyzer
    {
        public class DataPoint
        {
            public double Voltage { get; set; }
            public double Current { get; set; }
        }

        // Linear Regression Function
        public static (double slope, double intercept) LinearRegression(List<DataPoint> points)
        {
            if (points == null || points.Count < 2)
            {
                throw new ArgumentException("At least two data points are required for linear regression.");
            }

            double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
            int n = points.Count;

            foreach (var point in points)
            {
                sumX += point.Voltage;
                sumY += point.Current;
                sumXY += point.Voltage * point.Current;
                sumX2 += point.Voltage * point.Voltage;
            }

            double slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
            double intercept = (sumY - slope * sumX) / n;

            return (slope, intercept);
        }


        // Baseline Calculation (Separate Baselines)
        public static (List<DataPoint> oxidationBaseline, List<DataPoint> reductionBaseline) CalculateSeparateBaselines(List<DataPoint> set1Data, List<DataPoint> set2Data, double prePeakStart, double prePeakEnd, double postPeakStart, double postPeakEnd)
        {

            List<DataPoint> prePeakData = set1Data.Where(p => p.Voltage >= prePeakStart && p.Voltage <= prePeakEnd).ToList();
            List<DataPoint> postPeakData = set2Data.Where(p => p.Voltage >= postPeakEnd&& p.Voltage <= postPeakStart).ToList();

            if (prePeakData.Count < 2 || postPeakData.Count < 2)
            {
                throw new ArgumentException("Not enough data points in the specified ranges for baseline calculation.");
            }


            var (prePeakSlope, prePeakIntercept) = LinearRegression(prePeakData);
            var (postPeakSlope, postPeakIntercept) = LinearRegression(postPeakData);

            // Generate baseline points.  Crucially, use the *full* voltage range for generating the baselines.
            List<DataPoint> oxidationBaseline = new List<DataPoint>();
            List<DataPoint> reductionBaseline = new List<DataPoint>();

            foreach (var dp in set1Data)
            {
                oxidationBaseline.Add(new DataPoint { Voltage = dp.Voltage, Current = prePeakSlope * dp.Voltage + prePeakIntercept });
            }

            foreach (var dp in set2Data)
            {
                reductionBaseline.Add(new DataPoint { Voltage = dp.Voltage, Current = postPeakSlope * dp.Voltage + postPeakIntercept });
            }

            return (oxidationBaseline, reductionBaseline);
        }



        // Baseline Calculation (Combined Baseline - Weighted Average)
        public static List<DataPoint> CalculateCombinedBaseline(List<DataPoint> data, double prePeakStart, double prePeakEnd, double postPeakStart, double postPeakEnd)
        {
            List<DataPoint> prePeakData = data.Where(p => p.Voltage >= prePeakStart && p.Voltage <= prePeakEnd).ToList();
            List<DataPoint> postPeakData = data.Where(p => p.Voltage >= postPeakStart && p.Voltage <= postPeakEnd).ToList();

            if (prePeakData.Count < 2 || postPeakData.Count < 2)
            {
                throw new ArgumentException("Not enough data points in the specified ranges for baseline calculation.");
            }

            var (prePeakSlope, prePeakIntercept) = LinearRegression(prePeakData);
            var (postPeakSlope, postPeakIntercept) = LinearRegression(postPeakData);

            // Weighted average of slopes and intercepts
            double totalPoints = prePeakData.Count + postPeakData.Count;
            double prePeakWeight = (double)prePeakData.Count / totalPoints;
            double postPeakWeight = (double)postPeakData.Count / totalPoints;

            double combinedSlope = (prePeakWeight * prePeakSlope) + (postPeakWeight * postPeakSlope);
            double combinedIntercept = (prePeakWeight * prePeakIntercept) + (postPeakWeight * postPeakIntercept);

            // Generate baseline points using the combined slope and intercept, across the *entire* voltage range.
            List<DataPoint> combinedBaseline = new List<DataPoint>();
            foreach (var dp in data)
            {
                combinedBaseline.Add(new DataPoint { Voltage = dp.Voltage, Current = combinedSlope * dp.Voltage + combinedIntercept });
            }

            return combinedBaseline;
        }


        // Corrected Current (Subtract Baseline)
        public static List<DataPoint> SubtractBaseline(List<DataPoint> data, List<DataPoint> baseline)
        {
            if (data.Count != baseline.Count)
            {
                throw new ArgumentException("Data and baseline must have the same number of points.");
            }

            List<DataPoint> correctedData = new List<DataPoint>();
            for (int i = 0; i < data.Count; i++)
            {
                // Important:  Ensure voltage values match *exactly* before subtracting.
                if (Math.Abs(data[i].Voltage - baseline[i].Voltage) > 1e-9) // Use a small tolerance for floating-point comparisons
                {
                    throw new ArgumentException($"Voltage mismatch at index {i}: Data voltage = {data[i].Voltage}, Baseline voltage = {baseline[i].Voltage}");
                }
                correctedData.Add(new DataPoint { Voltage = data[i].Voltage, Current = data[i].Current - baseline[i].Current });
            }
            return correctedData;
        }

        // Read data from CSV file
        public static List<DataPoint> ReadDataFromCsv(string filePath)
        {
            using (var reader = new StreamReader(filePath))
            using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
            {
                return csv.GetRecords<DataPoint>().ToList();
            }
        }

        public double CalculatePeakHeight(double peakVoltage, List<CVAnalyzer.DataPoint> baseline, List<(double Voltage, double Current)> dataSet)
        {
            var closestBaselinePoint = baseline.OrderBy(p => Math.Abs(p.Voltage - peakVoltage)).FirstOrDefault();
            if (closestBaselinePoint != null)
            {
                var peakPoint = dataSet.FirstOrDefault(p => p.Voltage == peakVoltage);
                if (peakPoint != default)
                {
                    return peakPoint.Current - closestBaselinePoint.Current;
                }
            }
            return 0;
        }
        public (double, double) FindBaselineRangeFromDerivative(List<double> derivative, List<CVAnalyzer.DataPoint> data, double tolerance, int minWindowWidth, int maxWindowWidth)
        {
            int longestStartIndex = 0;
            int longestEndIndex = 0;
            int maxLength = 0;
            for (int windowStart = 0; windowStart <= derivative.Count - minWindowWidth; windowStart++)
            {
                for (int windowEnd = windowStart + minWindowWidth; windowEnd <= Math.Min(derivative.Count - 1, windowStart + maxWindowWidth); windowEnd++)
                {
                    bool isConstant = true;
                    for (int i = windowStart + 1; i <= windowEnd; i++)
                    {
                        if (Math.Abs(derivative[i] - derivative[i - 1]) > tolerance)
                        {
                            isConstant = false;
                            break;
                        }
                    }
                    if (isConstant)
                    {
                        int currentLength = windowEnd - windowStart + 1;
                        if (currentLength > maxLength)
                        {
                            maxLength = currentLength;
                            longestStartIndex = windowStart;
                            longestEndIndex = windowEnd;
                        }
                    }
                }
            }
            var startVoltage = data[longestStartIndex].Voltage;
            var endVoltage = data[longestEndIndex].Voltage;
            return (Math.Min(startVoltage, endVoltage), Math.Max(startVoltage, endVoltage));
        }

        public bool IsLinearSegment(List<(double Voltage, double Current)> data, int startIndex, int endIndex, double tolerance)
        {
            if (endIndex - startIndex < 2)
                return false;
            var segment = data.Skip(startIndex).Take(endIndex - startIndex + 1).ToList();
            var (slope, intercept) = CVAnalyzer.LinearRegression(segment.Select(p => new CVAnalyzer.DataPoint { Voltage = p.Voltage, Current = p.Current }).ToList());
            foreach (var point in segment)
            {
                double expectedCurrent = slope * point.Voltage + intercept;
                if (Math.Abs(point.Current - expectedCurrent) > tolerance)
                {
                    return false;
                }
            }
            return true;
        }
        public List<double> CalculateCurrentDifferences(List<CVAnalyzer.DataPoint> data)
        {
            List<double> currentDifferences = new List<double>();
            for (int i = 1; i < data.Count; i++)
            {
                double difference = data[i].Current - data[i - 1].Current;
                currentDifferences.Add(difference);
            }
            return currentDifferences;
        }
        public List<double> CalculateCurrentDerivative(List<CVAnalyzer.DataPoint> data)
        {
            List<double> currentDerivative = new List<double>();
            for (int i = 1; i < data.Count; i++)
            {
                double dCurrent = data[i].Current - data[i - 1].Current;
                double dVoltage = data[i].Voltage - data[i - 1].Voltage;
                double derivative = dCurrent / dVoltage;
                currentDerivative.Add(derivative);
            }
            return currentDerivative;
        }
        public List<(double Voltage, double Current)> FindPeaks(List<(double Voltage, double Current)> data, bool positive)
        {
            List<(double Voltage, double Current)> peaks = new List<(double Voltage, double Current)>();
            for (int i = 1; i < data.Count - 1; i++)
            {
                if (positive)
                {
                    if (data[i].Current > data[i - 1].Current && data[i].Current > data[i + 1].Current)
                    {
                        peaks.Add(data[i]);
                    }
                }
                else
                {
                    if (data[i].Current < data[i - 1].Current && data[i].Current < data[i + 1].Current)
                    {
                        peaks.Add(data[i]);
                    }
                }
            }
            return peaks;
        }
    }
}
