using ClosedXML.Excel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using DocumentFormat.OpenXml.Spreadsheet;
using Microsoft.Maui.Storage;
using Microsoft.UI.Xaml.Controls;
using Poten2501.CustomControls;
using Poten2501.Models;
using ScottPlot.Maui;
using ScottPlot;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Data;
using System.Diagnostics;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;
using MathNet.Numerics;

namespace Poten2501.ViewModels
{
    internal class SWVAnalyseViewModel : ObservableObject, INotifyPropertyChanged
    {
        public ICommand LoadExcelCommand { get; private set; }
        public ICommand CheckboxChangedCommand => new RelayCommand<int>(async cycleNo => OnCheckboxChanged(cycleNo));

        public ICommand SaveMetedataCommand { get; private set; }



        private MauiPlot mauiPlot;
        private PlotView _plotView;
 

        private string _fileName;
        public string FileName
        {
            get => _fileName;
            set => SetProperty(ref _fileName, value);
        }

        private string _filePath;
        public string FilePath
        {
            get => _filePath;
            set => SetProperty(ref _filePath, value);
        }

        private double peakVoltage;
        public double PeakVoltage
        {
            get => peakVoltage;
            set => SetProperty(ref peakVoltage, value);
        }
        private double peakCurrent;
        public double PeakCurrent
        {
            get => peakCurrent;
            set => SetProperty(ref peakCurrent, value);
        }
        private double peakHeight;
        public double PeakHeight
        {
            get => peakHeight;
            set => SetProperty(ref peakHeight, value);
        }



        public SWVAnalyseViewModel(PlotView plotView)
        {
            _plotView = plotView;
            mauiPlot = _plotView.Plot;
            CycleNos = new ObservableCollection<int>();
            SelectedCycleNos = new ObservableCollection<int>();
            dataCycle = new Dictionary<int, ObservableCollection<Dictionary<string, object>>>();

            LoadExcelCommand = new RelayCommand(LoadExcel);
            SaveMetedataCommand = new RelayCommand(SaveMetadata);
        }

        private async void SaveMetadata()
        {
            string oroginalFilename = FileName;
            Debug.WriteLine($"Original filename: {oroginalFilename}");
            string newFilename = $"{Path.GetFileNameWithoutExtension(FileName)}_metadata.csv";
            string newFilePath = Path.Combine(FilePath, newFilename);
            Debug.WriteLine($"New filename: {newFilename}");
            Debug.WriteLine($"New file path: {newFilePath}");
            var lineToWrite = $"{Path.GetFileNameWithoutExtension(FileName)}_Cycle_{LastSelectedCycleNo.Value},{PeakVoltage},{PeakCurrent},{PeakHeight}" + Environment.NewLine;
            Debug.WriteLine($"lineToWrite = {lineToWrite}");

            try
            {
                await Task.Run(() => File.AppendAllText(newFilePath, lineToWrite));
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error writing metadata file: {ex.Message}");
            }
        }

        private DataTable loadedDataTable;
        private ObservableCollection<int> selectedCycleNos;
        public ObservableCollection<int> SelectedCycleNos
        {
            get => selectedCycleNos;
            set => SetProperty(ref selectedCycleNos, value);
        }
        public int SelectedCycleCount => SelectedCycleNos.Count;
        private ObservableCollection<int> cycleNos;
        public ObservableCollection<int> CycleNos
        {
            get => cycleNos;
            set => SetProperty(ref cycleNos, value);
        }
        private ObservableCollection<Dictionary<string, object>> filteredData;

        private Dictionary<int, ObservableCollection<Dictionary<string, object>>> dataCycle;
        public ObservableCollection<string> DataFiles { get; set; }

        private List<(double Voltage, double Current)> peaksSet;
        private List<(double Voltage, double Current)> dataset;
        public ObservableCollection<Dictionary<string, object>> FilteredData
        {
            get => filteredData;
            set => SetProperty(ref filteredData, value);
        }
        private int? _lastSelectedCycleNo;
        public int? LastSelectedCycleNo
        {
            get => _lastSelectedCycleNo;
            set => SetProperty(ref _lastSelectedCycleNo, value);
        }

        // Method to be executed by the command
        private async void LoadExcel()
        {
            try
            {
                var result = await FilePicker.Default.PickAsync(new PickOptions
                {
                    PickerTitle = "Please select an Excel file",
                    FileTypes = new FilePickerFileType(new Dictionary<DevicePlatform, IEnumerable<string>>
            {
                { DevicePlatform.iOS, new[] { "public.data" } },
                { DevicePlatform.Android, new[] { "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" } },
                { DevicePlatform.WinUI, new[] { ".xlsx" } },
                { DevicePlatform.Tizen, new[] { "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" } }
            })
                });

                if (result != null)
                {
                    SelectedCycleNos.Clear();
                    CycleNos.Clear();
                    dataCycle.Clear();
                    FilteredData = null;
                    LastSelectedCycleNo = null;

                    var filePath = result.FullPath;
                    loadedDataTable = LoadExcelIntoDataTable(filePath);
                    FileName = Path.GetFileName(filePath);
                    FilePath = Path.GetDirectoryName(filePath);
                    UpdateCycleNos(loadedDataTable);
                    //EnableButtons();
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error loading Excel file: {ex.Message}");
            }
        }

        private void UpdateCycleNos(DataTable dataTable)
        {
            var cycleNoList = dataTable.AsEnumerable()
                                       .Select(row => Convert.ToInt32(row["CycleNo"]))
                                       .Distinct()
                                       .ToList();
            CycleNos.Clear();
            foreach (var cycleNo in cycleNoList)
            {
                CycleNos.Add(cycleNo);
            }
        }

        private DataTable LoadExcelIntoDataTable(string filePath)
        {
            DataTable dataTable = new DataTable();

            try
            {
                using (var workbook = new XLWorkbook(filePath))
                {
                    var worksheet = workbook.Worksheets.First();
                    var rows = worksheet.RowsUsed();

                    // Use the second row as headers
                    var headers = rows.Skip(1).First().Cells().Select(cell => cell.Value.ToString()).ToArray();
                    ValidateHeaders(headers);

                    dataTable.Columns.Add("Counter");
                    dataTable.Columns.Add("REVoltage");
                    dataTable.Columns.Add("WEVoltage");
                    dataTable.Columns.Add("CycleNo");

                    // Add rows
                    var dataRows = rows.Skip(2).ToList(); // Skip the first two rows (headers)
                    int rowCount = dataRows.Count;
                    int colCount = headers.Length;

                    int counter = 1;
                    for (int col = 0; col < colCount; col += 2)
                    {
                        for (int row = 0; row < rowCount; row++)
                        {
                            var reVoltage = dataRows[row].Cell(col + 1).Value.ToString();
                            var weCurrent = dataRows[row].Cell(col + 2).Value.ToString();
                            if (!string.IsNullOrEmpty(reVoltage) && !string.IsNullOrEmpty(weCurrent))
                            {
                                var fields = new string[4];
                                fields[0] = counter.ToString();
                                fields[1] = reVoltage;
                                fields[2] = weCurrent;
                                fields[3] = (col / 2 + 1).ToString();
                                dataTable.Rows.Add(fields);
                                counter++;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error loading Excel file: {ex.Message}");
            }
            return dataTable;
        }
        private void ValidateHeaders(string[] headers)
        {
            if (headers == null || headers.Length == 0)
            {
                throw new InvalidDataException("CSV file is missing headers.");
            }
        }

        private void OnCheckboxChanged(int cycleNo)
        {
            if (SelectedCycleNos.Contains(cycleNo))
            {
                SelectedCycleNos.Remove(cycleNo);
            }
            else
            {
                SelectedCycleNos.Add(cycleNo);
                LastSelectedCycleNo = cycleNo; // Update the last selected cycle number

            }

            OnPropertyChanged(nameof(SelectedCycleNos));
            OnPropertyChanged(nameof(LastSelectedCycleNo));
            FilterDataByCycleNos(loadedDataTable, SelectedCycleNos);
            //UpdateButtonStates();
            PeakDetect();
            PlotGraph();
            PlotBaseline();
            PlotPeakPoint();
            PlotPeakVerticalLine();
            PlotAnnotation();

            //PeakDetect();
        }

        private void PlotAnnotation()
        {
            var plt = mauiPlot.Plot;
            var annotationPlot = plt.Add.Annotation($"Cycle No: {LastSelectedCycleNo.Value}\nPeak Voltage {PeakVoltage:F4}\nPeak Current {PeakCurrent:F4}\nPeak Height {PeakHeight:F4}");
            annotationPlot.LabelFontSize = 16;
            annotationPlot.Alignment = ScottPlot.Alignment.UpperRight;

            plt.ShowLegend();
            mauiPlot.Refresh();
        }

        private void PlotPeakVerticalLine()
        {
            if (peaksSet == null || peaksSet.Count == 0 || dataset == null || dataset.Count == 0)
                return;

            var plt = mauiPlot.Plot;
            var peak = peaksSet[0];

            // Fit baseline using the same method as PlotBaseline
            double[] baseline = FitBaselineByMinBeforeAfterPeak(dataset);
            double[] voltages = dataset.Select(d => d.Voltage).ToArray();

            // Find the index of the peak in the dataset
            int peakIdx = dataset.FindIndex(d => d.Voltage == peak.Voltage && d.Current == peak.Current);
            if (peakIdx < 0 || peakIdx >= voltages.Length)
                return;

            double x = peak.Voltage;
            double yPeak = peak.Current;
            double yBaseline = baseline[peakIdx];

            // Draw vertical line from baseline to peak
            var vline = plt.Add.Line(
                x1: x, y1: yBaseline,
                x2: x, y2: yPeak
            );
            vline.LineColor = ScottPlot.Color.FromHex("#FF0000"); // Set the color using the LineColor property
            vline.LineWidth = 2;
            vline.LegendText = "Peak Height";

            plt.ShowLegend();
            mauiPlot.Refresh();
        }

        private void PlotPeakPoint()
        {
            if (peaksSet == null || peaksSet.Count == 0)
                return;

            var plt = mauiPlot.Plot;

            // Plot the first peak as a highlighted point
            var peak = peaksSet[0];
            var scatter = plt.Add.Marker(
                x: peak.Voltage,
                y: peak.Current,
                size: 10,
                shape: ScottPlot.MarkerShape.FilledCircle
            );
            scatter.MarkerColor = ScottPlot.Color.FromHex("#FF0000"); // Set the color using the MarkerColor property
            scatter.LegendText = "Peak";

            plt.ShowLegend();
            mauiPlot.Refresh();
        }

        private void PlotBaseline()
        {
            if (dataset == null || dataset.Count == 0)
                return;

            // Fit linear baseline
            double[] x = dataset.Select(d => d.Voltage).ToArray();
            //double[] baseline = FitLinearBaseline(dataset);
            double[] baseline = FitBaselineByMinBeforeAfterPeak(dataset);

            // Plot baseline on the same plot
            var plt = mauiPlot.Plot;
            var baselinePlot = plt.Add.Scatter(x, baseline, color: ScottPlot.Color.FromHex("#FF9900"));
            baselinePlot.LegendText = "Baseline";
            baselinePlot.LinePattern = ScottPlot.LinePattern.Dashed;
            baselinePlot.MarkerSize = 0;

            plt.ShowLegend();
            mauiPlot.Refresh();
        }

        public List<CVAnalyzer.DataPoint> VoltammogramData { get; private set; }
        private void PeakDetect()
        {
            if (LastSelectedCycleNo.HasValue && dataCycle.ContainsKey(LastSelectedCycleNo.Value))
            {
                var cycleData = dataCycle[LastSelectedCycleNo.Value];
                VoltammogramData = cycleData.Select(d => new CVAnalyzer.DataPoint
                {
                    Voltage = Convert.ToDouble(d["Voltage"]),
                    Current = Convert.ToDouble(d["Current"])
                }).ToList();
                ProcessVoltammogramData();
            }
            else
            {
                Debug.WriteLine("No cycle selected or data not available for the selected cycle.");
            }
        }

        private void ProcessVoltammogramData()
        {
            double maxVoltage = VoltammogramData.Max(p => p.Voltage);
            double minVoltage = VoltammogramData.Min(p => p.Voltage);
            List<(double Voltage, double Current)> allData = VoltammogramData.Select(dp => (dp.Voltage, dp.Current)).ToList();
            // Find the index of the maximum voltage
            int maxVoltageIndex = -1;
            maxVoltage = double.MinValue;
            for (int i = 0; i < allData.Count; i++)
            {
                if (allData[i].Voltage > maxVoltage)
                {
                    maxVoltage = allData[i].Voltage;
                    maxVoltageIndex = i;
                }
            }
            int minVoltageIndex = -1;
            minVoltage = double.MaxValue;
            for (int i = 0; i < allData.Count; i++)
            {
                if (allData[i].Voltage < minVoltage)
                {
                    minVoltage = allData[i].Voltage;
                    minVoltageIndex = i;
                }
            }
            List<int> zeroCrossingIndices = new List<int>();
            for (int i = 1; i < allData.Count; i++)
            {
                if ((allData[i - 1].Voltage < 0 && allData[i].Voltage >= 0) ||
                    (allData[i - 1].Voltage >= 0 && allData[i].Voltage < 0))
                {
                    zeroCrossingIndices.Add(i);
                }
            }
            dataset = allData.ToList();
            try 
            {
                peaksSet = FindPeaks(dataset, positive: true);
                PeakVoltage = peaksSet[0].Voltage;
                PeakCurrent = peaksSet[0].Current;
                //double[] baseline = FitLinearBaseline(dataset);
                Debug.WriteLine($"Peak voltage: {peaksSet[0].Voltage} Peak current: {peaksSet[0].Current}");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error processing voltammogram data: {ex.Message}");
            }
        }
        public double[] FitLinearBaseline(List<(double Voltage, double Current)> data)
        {
            // เลือกเฉพาะช่วงขอบ (เช่น 20% แรกและ 20% สุดท้าย)
            int n = data.Count;
            int edgeCount = Math.Max(3, n / 5); // อย่างน้อย 3 จุด

            var left = data.Take(edgeCount).ToList();
            var right = data.Skip(n - edgeCount).ToList();

            var x = left.Concat(right).Select(d => d.Voltage).ToArray();
            var y = left.Concat(right).Select(d => d.Current).ToArray();

            var (slope, intercept) = Fit.Line(x, y);

            // สร้าง baseline สำหรับทุกจุด
            var allX = data.Select(d => d.Voltage).ToArray();
            double[] baseline = new double[allX.Length];
            for (int i = 0; i < allX.Length; i++)
                baseline[i] = slope * allX[i] + intercept;
            return baseline;
        }

        public double[] FitBaselineByMinBeforeAfterPeak(List<(double Voltage, double Current)> data)
        {
            if (data == null || data.Count < 3)
                return Enumerable.Repeat(0.0, data.Count).ToArray();

            // หา peak จริง (ไม่ใช่ค่ามากสุด)
            var peaks = FindPeaks(data, positive: true);
            if (peaks.Count == 0)
                return Enumerable.Repeat(0.0, data.Count).ToArray();

            // ใช้ตำแหน่งของ peak แรกที่เจอ
            var peak = peaks[0];
            int peakIdx = data.FindIndex(d => d.Voltage == peak.Voltage && d.Current == peak.Current);

            // หา index ของ current ต่ำสุดก่อน peak
            int minBeforeIdx = 0;
            if (peakIdx > 0)
                minBeforeIdx = data.Take(peakIdx)
                                   .Select((d, i) => (Current: d.Current, Index: i))
                                   .OrderBy(t => t.Current)
                                   .First().Index;

            // หา index ของ current ต่ำสุดหลัง peak
            int minAfterIdx = data.Count - 1;
            if (peakIdx < data.Count - 1)
                minAfterIdx = data.Skip(peakIdx + 1)
                                  .Select((d, i) => (Current: d.Current, Index: i + peakIdx + 1))
                                  .OrderBy(t => t.Current)
                                  .First().Index;

            // เตรียมข้อมูลสำหรับ fit baseline
            var x = new[] { data[minBeforeIdx].Voltage, data[minAfterIdx].Voltage };
            var y = new[] { data[minBeforeIdx].Current, data[minAfterIdx].Current };

            // Fit เส้นตรงผ่านสองจุด
            double slope = (y[1] - y[0]) / (x[1] - x[0]);
            double intercept = y[0] - slope * x[0];

            // สร้าง baseline สำหรับทุกจุด
            var allX = data.Select(d => d.Voltage).ToArray();
            double[] baseline = new double[allX.Length];
            for (int i = 0; i < allX.Length; i++)
                baseline[i] = slope * allX[i] + intercept;

            PeakHeight = peaksSet[0].Current - baseline[peakIdx];

            return baseline;
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
                        bool risingBefore = false, fallingAfter = false;
                        for (int j = i - 1; j >= 0; j--)
                        {
                            if (data[j].Current < data[j + 1].Current)
                                risingBefore = true;
                            else break;
                        }
                        for (int j = i + 1; j < data.Count; j++)
                        {
                            if (data[j].Current < data[j - 1].Current)
                                fallingAfter = true;
                            else break;
                        }
                        if (risingBefore && fallingAfter)
                            peaks.Add(data[i]);
                    }
                }
                else
                {
                    if (data[i].Current < data[i - 1].Current && data[i].Current < data[i + 1].Current)
                    {
                        bool fallingBefore = false, risingAfter = false;
                        for (int j = i - 1; j >= 0; j--)
                        {
                            if (data[j].Current > data[j + 1].Current)
                                fallingBefore = true;
                            else break;
                        }
                        for (int j = i + 1; j < data.Count; j++)
                        {
                            if (data[j].Current > data[j - 1].Current)
                                risingAfter = true;
                            else break;
                        }
                        if (fallingBefore && risingAfter)
                            peaks.Add(data[i]);
                    }
                }
            }
            // Sort peaks by absolute current descending (highest peak first)
            if (positive)
                peaks = peaks.OrderByDescending(p => p.Current).ToList();
            else
                peaks = peaks.OrderBy(p => p.Current).ToList();
            return peaks;
        }
        private void FilterDataByCycleNos(DataTable dataTable, ObservableCollection<int> cycleNos)
        {
            dataCycle.Clear();
            foreach (DataRow row in dataTable.Rows)
            {
                int cycleNo = Convert.ToInt32(row["CycleNo"]);
                if (cycleNos.Contains(cycleNo))
                {
                    var dict = new Dictionary<string, object>
                    {
                        { "Counter", row["counter"] },
                        { "Voltage", row["REVoltage"] },
                        { "Current", row["WEVoltage"] }
                    };

                    if (!dataCycle.ContainsKey(cycleNo))
                    {
                        dataCycle[cycleNo] = new ObservableCollection<Dictionary<string, object>>();
                    }
                    dataCycle[cycleNo].Add(dict);
                }
            }
            FilteredData = new ObservableCollection<Dictionary<string, object>>(dataCycle.SelectMany(kvp => kvp.Value));
        }

        private void PlotGraph()
        {
            var plt = new ScottPlot.Plot();

            // Define a list of colors to use for the data series
            var colors = new List<string> { "#000000", "#FF0000", "#0000FF", "#008800", "#aaaa00", "#FF00FF", "#00aaaa" };

            var additionalDataX = new List<double[]>();
            var additionalDataY = new List<double[]>();

            int colorIndex = 0;
            foreach (var cycleData in dataCycle)
            {
                var x = cycleData.Value.Select(d => Convert.ToDouble(d["Voltage"])).ToArray();
                var y = cycleData.Value.Select(d => Convert.ToDouble(d["Current"])).ToArray();

                additionalDataX.Add(x);
                additionalDataY.Add(y);

                var scatter = plt.Add.Scatter(x, y);
                scatter.Color = ScottPlot.Color.FromHex(colors[colorIndex % colors.Count]); // Set unique color for each CycleNo
                colorIndex++;
            }
            plt.Add.Legend();
            _plotView.AdditionalDataX = additionalDataX.ToArray();
            _plotView.AdditionalDataY = additionalDataY.ToArray();
        }
    }
}
