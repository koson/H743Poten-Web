using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.VisualBasic.FileIO;
using Poten2501.CustomControls;
using ScottPlot.Maui;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Data;
using System.Windows.Input;
using System;
using System.IO;
using NumSharp;
using System.Drawing;
using ScottPlot;
using System.Collections.Generic;
using MathNet.Numerics;
using MathNet.Numerics.LinearRegression;
using System.Diagnostics;
using CommunityToolkit.Maui.Storage;
using CommunityToolkit.Maui.Views;
using Microsoft.Maui.Storage;
using Microsoft.UI.Xaml.Controls;
using Poten2501.Models;
using CsvHelper;
using System.Globalization;
using ClosedXML.Excel;
using System.Text.RegularExpressions;
using System.Threading.Tasks;


namespace Poten2501.ViewModels
{
    public partial class CVAnalyzeViewModel : ObservableObject, INotifyPropertyChanged
    {

        // Global list variables
        private List<(double Voltage, double Current)> part1;
        private List<(double Voltage, double Current)> part2;
        private List<(double Voltage, double Current)> part3;
        private List<(double Voltage, double Current)> part4;
        private List<(double Voltage, double Current)> set1;
        private List<(double Voltage, double Current)> set2;
        private List<(double Voltage, double Current)> peaksSet1;
        private List<(double Voltage, double Current)> peaksSet2;
        public List<CVAnalyzer.DataPoint> VoltammogramData { get; private set; }
        CVAnalyzer cvAanalyzer;


        private double? _anodicPeakHeight;
        private double? AnodicPeakHeight
        {
            get => _anodicPeakHeight;
            set => SetProperty(ref _anodicPeakHeight, value);
        }

        private double _cathodicPeakHeight;
        public double CathodicPeakHeight
        {
            get => _cathodicPeakHeight;
            set => SetProperty(ref _cathodicPeakHeight, value);
        }

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



        private double _tolerance;
        public double Tolerance
        {
            get => _tolerance;
            set => SetProperty(ref _tolerance, value);
        }

        private bool _isPart1Selected;
        public bool IsPart1Selected
        {
            get => _isPart1Selected;
            set => SetProperty(ref _isPart1Selected, value);
        }

        private double? _anodicPeakCurrent;
        public double? AnodicPeakCurrent
        {
            get => _anodicPeakCurrent;
            set => SetProperty(ref _anodicPeakCurrent, value);
        }

        private double? _cathodicPeakCurrent;
        public double? CathodicPeakCurrent
        {
            get => _cathodicPeakCurrent;
            set => SetProperty(ref _cathodicPeakCurrent, value);
        }

        private double? _anodicBaselineStartCurrent;
        public double? AnodicBaselineStartCurrent
        {
            get => _anodicBaselineStartCurrent;
            set => SetProperty(ref _anodicBaselineStartCurrent, value);
        }


        private double? _anodicBaselineEndCurrent;
        public double? AnodicBaselineEndCurrent
        {
            get => _anodicBaselineEndCurrent;
            set => SetProperty(ref _anodicBaselineEndCurrent, value);
        }
        private double? _cathodicBaselineStartCurrent;
        public double? CathodicBaselineStartCurrent
        {
            get => _cathodicBaselineStartCurrent;
            set => SetProperty(ref _cathodicBaselineStartCurrent, value);
        }
        private double? _cathodicBaselineEndCurrent;
        public double? CathodicBaselineEndCurrent
        {
            get => _cathodicBaselineEndCurrent;
            set => SetProperty(ref _cathodicBaselineEndCurrent, value);
        }
        private bool _isPart2Selected;
        public bool IsPart2Selected
        {
            get => _isPart2Selected;
            set => SetProperty(ref _isPart2Selected, value);
        }

        private bool _isPart3Selected;
        public bool IsPart3Selected
        {
            get => _isPart3Selected;
            set => SetProperty(ref _isPart3Selected, value);
        }

        private bool _isPart4Selected;
        public bool IsPart4Selected
        {
            get => _isPart4Selected;
            set => SetProperty(ref _isPart4Selected, value);
        }

        private bool _isSet1Selected;
        public bool IsSet1Selected
        {
            get => _isSet1Selected;
            set => SetProperty(ref _isSet1Selected, value);
        }

        private bool _isSet2Selected;
        public bool IsSet2Selected
        {
            get => _isSet2Selected;
            set => SetProperty(ref _isSet2Selected, value);
        }
        private bool _manualSelectedAnodePeak;
        public bool ManualSelectedAnodePeak
        {
            get { return _manualSelectedAnodePeak; }
            set { _manualSelectedAnodePeak = value; }
        }

        private bool _manualSelectedCathodePeak;

        public bool ManualSelectedCathodePeak
        {
            get { return _manualSelectedCathodePeak; }
            set { _manualSelectedCathodePeak = value; }
        }

        private double _anodicPeakLocation;
        public double AnodicPeakLocation
        {
            get => _anodicPeakLocation * 1000.0;
            set
            {
                SetProperty(ref _anodicPeakLocation, value / 1000.0);
                if (peaksSet1 != null && peaksSet1.Count > 0)
                {
                    var matchingPoint = set1.OrderBy(p => Math.Abs(p.Voltage - AnodicPeakLocation)).FirstOrDefault();

                    if (matchingPoint != default)
                    {
                        peaksSet1[0] = (matchingPoint.Voltage, matchingPoint.Current);
                        AnodicPeakCurrent = matchingPoint.Current; // Update the current value
                        //Debug.WriteLine($"Anodic Peak Location: {matchingPoint.Voltage}V, {matchingPoint.Current}A");
                        ManualSelectedAnodePeak = true;
                    }
                }
            }
        }

        private double _anodicBaselineStart;
        public double AnodicBaselineStart
        {
            get => _anodicBaselineStart * 1000.0;
            set
            {
                SetProperty(ref _anodicBaselineStart, value / 1000.0);

                if (set1 != null)
                {
                    var matchingPoint = set1.OrderBy(p => Math.Abs(p.Voltage - AnodicBaselineStart)).FirstOrDefault();
                    if (matchingPoint != default)
                    {
                        AnodicBaselineStartCurrent = matchingPoint.Current; // Update the current value
                        //Debug.WriteLine($"Anodic Baseline Start: Voltage = {matchingPoint.Voltage} V, Current = {matchingPoint.Current} A");
                    }
                }
            }
            }

        private double _anodicBaselineEnd;
        public double AnodicBaselineEnd
        {
            get => _anodicBaselineEnd * 1000.0;
            set
            {
                SetProperty(ref _anodicBaselineEnd, value / 1000.0);
                if (set1 != null)
                {
                    var matchingPoint = set1.OrderBy(p => Math.Abs(p.Voltage - AnodicBaselineEnd)).FirstOrDefault();
                    if (matchingPoint != default)
                    {
                        AnodicBaselineEndCurrent = matchingPoint.Current; // Update the current value
                        //Debug.WriteLine($"Anodic Baseline End: Voltage = {matchingPoint.Voltage} V, Current = {matchingPoint.Current} A");
                    }
                }
            }
        }

        private double _cathodicPeakLocation;
        public double CathodicPeakLocation

        {
            get => _cathodicPeakLocation * 1000.0;
            set
            {
                SetProperty(ref _cathodicPeakLocation, value / 1000.0);
                if (peaksSet2 != null && peaksSet2.Count > 0)
                {
                    var matchingPoint = set2.OrderBy(p => Math.Abs(p.Voltage - CathodicPeakLocation)).FirstOrDefault();

                    if (matchingPoint != default)
                    {
                        peaksSet2[0] = (matchingPoint.Voltage, matchingPoint.Current);
                        CathodicPeakCurrent = matchingPoint.Current;
                        //Debug.WriteLine($"Cathodic Peak Location: {matchingPoint.Voltage}V, {matchingPoint.Current}A");
                        ManualSelectedCathodePeak = true;
                    }
                }
            }
        }
        private double _cathodicBaselineStart;
        public double CathodicBaselineStart
        {
            get => _cathodicBaselineStart * 1000.0;
            set => SetProperty(ref _cathodicBaselineStart, value / 1000.0);
        }

        private double _cathodicBaselineEnd;
        public double CathodicBaselineEnd
        {
            get => _cathodicBaselineEnd * 1000.0;
            set => SetProperty(ref _cathodicBaselineEnd, value / 1000.0);
        }


        private ObservableCollection<Dictionary<string, object>> filteredData;

        private Dictionary<int, ObservableCollection<Dictionary<string, object>>> dataCycle;
        public ObservableCollection<string> DataFiles { get; set; }

        public ObservableCollection<Dictionary<string, object>> FilteredData
        {
            get => filteredData;
            set => SetProperty(ref filteredData, value);
        }

        private ObservableCollection<int> cycleNos;
        public ObservableCollection<int> CycleNos
        {
            get => cycleNos;
            set => SetProperty(ref cycleNos, value);
        }

        private ObservableCollection<int> selectedCycleNos;
        public ObservableCollection<int> SelectedCycleNos
        {
            get => selectedCycleNos;
            set => SetProperty(ref selectedCycleNos, value);
        }
        public int SelectedCycleCount => SelectedCycleNos.Count;

        private bool _isPeakDetectEnabled;
        private bool _isAddToProjectEnabled;

        public bool IsPeakDetectEnabled
        {
            get => _isPeakDetectEnabled;
            set => SetProperty(ref _isPeakDetectEnabled, value);
        }

        public bool IsAddToProjectEnabled
        {
            get => _isAddToProjectEnabled;
            set => SetProperty(ref _isAddToProjectEnabled, value);
        }
        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
        private DataTable loadedDataTable;
        private MauiPlot mauiPlot;
        private PlotView _plotView;
        private List<CVAnalyzer.DataPoint> oxidationBaseline;
        private List<CVAnalyzer.DataPoint> reductionBaseline;
        public CVAnalyzeViewModel(PlotView plotView)
        {
            _plotView = plotView;
            mauiPlot = _plotView.Plot;
            InitializeCommands();
            InitializeCollections();
        }
        private void InitializeCommands()
        {
            LoadCSVCommand = new RelayCommand(LoadCSV);
            ProcessDataCommand = new RelayCommand(ProcessData);
            PlotGraphCommand = new RelayCommand(PlotGraph);
            PeakDetectCommand = new RelayCommand(PeakDetect);
            NewProjectCommand = new RelayCommand(async () => await NewProjectAsync());
            OpenProjectCommand = new RelayCommand(OpenProject);
            SaveProjectCommand = new RelayCommand(SaveProject);
            SaveAsProjectCommand = new RelayCommand(SaveAsProject);
            SaveMetedataCommand = new RelayCommand(SaveMetadata);
            CloseProjectCommand = new RelayCommand(CloseProject);
            AddToProjectCommand = new RelayCommand(AddToProject);
            LoadGraphCommand = new Command<string>(ExecuteLoadGraphCommand);
            RenameCommand = new Command<string>(ExecuteRenameCommand);
            DeleteCommand = new Command<string>(ExecuteDeleteCommand);
            
            CompareChartCommand = new RelayCommand(CompareCharts);
            ComparePeaksCommand = new RelayCommand(ComparePeaks);
            EditMetaDataCommand = new Command<object>(OnEditMetaDataCommandCommandExecuted);
            FindBaselineCommand = new Command(OnFindBaseline);
            LoadEmStatDataCommand = new RelayCommand(LoadEmStatData);
            LoadExcelCommand = new RelayCommand(LoadExcel);
            LoadDataFromGraphListCommand = new Command<string>(ExecuteLoadDataFromGraphList);
        }
        private void SaveMetadata()
        {
            string originalFileName = FileName;
            int cycleNo = LastSelectedCycleNo.Value;

            if (originalFileName.StartsWith("Palmsense-CV"))
            {
                string CycleMetaData = Path.GetFileNameWithoutExtension(originalFileName)+$"_Cycle{cycleNo}";
                string MetaDataFilename = Path.GetFileNameWithoutExtension(originalFileName) + "_metadata.csv";
                var metadataFileWithPath = Path.Combine(FilePath, MetaDataFilename);

                var lineToWrite = $"{CycleMetaData}, {AnodicPeakLocation}, {AnodicPeakHeight/1e6}, {CathodicPeakLocation}, {CathodicPeakHeight / 1e6}";
                Debug.WriteLine(lineToWrite);

                // เขียนข้อมูลลงในไฟล์ (ต่อท้ายถ้ามีข้อมูลอยู่แล้ว)  
                File.AppendAllText(metadataFileWithPath, lineToWrite + Environment.NewLine);
            }
            else
            {
                string metadataFileName = Regex.Replace(originalFileName, @"(.+_E\d+_)\d+(\.csv)", "$1metadata$2");
                var metadataFileWithPath = Path.Combine(FilePath, metadataFileName);

                var lineToWrite = $"{originalFileName}, {AnodicPeakLocation}, {AnodicPeakHeight}, {CathodicPeakLocation}, {CathodicPeakHeight}";
                Debug.WriteLine(lineToWrite);

                // เขียนข้อมูลลงในไฟล์ (ต่อท้ายถ้ามีข้อมูลอยู่แล้ว)  
                File.AppendAllText(metadataFileWithPath, lineToWrite + Environment.NewLine);
            }
        }
        private void ExecuteLoadDataFromGraphList(string filemane)
        {
            LoadDataFromGraphList(filemane);
        }
        private void InitializeCollections()
        {
            CycleNos = new ObservableCollection<int>();
            SelectedCycleNos = new ObservableCollection<int>();
            dataCycle = new Dictionary<int, ObservableCollection<Dictionary<string, object>>>();
            DataFiles = new ObservableCollection<string>();
            cvAanalyzer = new();
        }
        #region command    
        public ICommand LoadCSVCommand { get; private set; }
        public ICommand ProcessDataCommand { get; private set; }
        public ICommand PlotGraphCommand { get; private set; }
        public ICommand CheckboxChangedCommand => new RelayCommand<int>(cycleNo => OnCheckboxChanged(cycleNo));
        public ICommand PeakDetectCommand { get; private set; }
        public ICommand NewProjectCommand { get; private set; }
        public ICommand OpenProjectCommand { get; private set; }
        public ICommand SaveProjectCommand { get; private set; }
        public ICommand SaveAsProjectCommand { get; private set; }
        public ICommand CloseProjectCommand { get; private set; }
        public ICommand AddToProjectCommand { get; private set; }
        public ICommand LoadGraphCommand { get; private set; }
        public ICommand RenameCommand { get; private set; }
        public ICommand DeleteCommand { get; private set; }
        public ICommand CompareChartCommand { get; private set; }
        public ICommand ComparePeaksCommand { get; private set; }
        public ICommand EditMetaDataCommand { get; private set; }
        public ICommand FindBaselineCommand { get; private set; }
        public ICommand LoadEmStatDataCommand { get; private set; }
        public ICommand LoadExcelCommand { get; private set; }
        public ICommand LoadDataFromGraphListCommand { get; private set; }
        public ICommand SaveMetedataCommand { get; private set; }

        #endregion
        public void LoadDataFromGraphList(string fileName)
        {
            var settings = Settings.Load();
            string projectRoot;

            if (!string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory))
            {
                projectRoot = settings.LastUsedDirectory;
            }
            else
            {
                projectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
            }
            string dataDirectory = Path.Combine(projectRoot, "data");
            string filePath = Path.Combine(dataDirectory, fileName);
            if (File.Exists(filePath))
            {
                Debug.WriteLine($"File {filePath} found.");
                try
                {
                    VoltammogramData = CVAnalyzer.ReadDataFromCsv(filePath);
                }
                catch (Exception ex)
                {
                    Debug.WriteLine($"Error reading CSV file: {ex.Message}");
                    return; // Exit if there's an error reading the file.
                }

                ProcessVoltammogramData();
            }
            else
            {
                Debug.WriteLine($"File {filePath} does not exist.");
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

            //Debug.WriteLine($"maxVoltage = {maxVoltage}, index = {maxVoltageIndex}");

            // Find the index of the minimum voltage
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

            //Debug.WriteLine($"minVoltage = {minVoltage}, index = {minVoltageIndex}");

            // Find all zero crossing indices
            List<int> zeroCrossingIndices = new List<int>();
            for (int i = 1; i < allData.Count; i++)
            {
                if ((allData[i - 1].Voltage < 0 && allData[i].Voltage >= 0) ||
                    (allData[i - 1].Voltage >= 0 && allData[i].Voltage < 0))
                {
                    zeroCrossingIndices.Add(i);
                }
            }

            //Debug.WriteLine("Zero Crossing Indices:");
            //foreach (var index in zeroCrossingIndices)
            //{
            //    Debug.WriteLine(index);
            //}

            try
            {
                // Separate the data into four parts
                part1 = allData.Take(maxVoltageIndex + 1).ToList();
                //part2 = allData.Skip(maxVoltageIndex).TakeWhile(p => p.Voltage >= 0).ToList();
                part2 = allData.Skip(maxVoltageIndex).ToList();
                part3 = allData.SkipWhile(p => p.Voltage >= 0).Take(minVoltageIndex - zeroCrossingIndices.Last()).ToList();
                part4 = allData.Skip(minVoltageIndex).ToList();

                // Combine into two sets
                //set1 = part4.Concat(part1).ToList();
                set1 = part1.ToList();
                //set2 = part2.Concat(part3).ToList();
                set2 = part2.ToList();

                // Find peaks in set1 and set2
                if (ManualSelectedAnodePeak == false)
                {
                    peaksSet1 = cvAanalyzer.FindPeaks(set1, positive: true);
                }
                if (ManualSelectedCathodePeak == false)
                {
                    peaksSet2 = cvAanalyzer.FindPeaks(set2, positive: false);
                }
                List<CVAnalyzer.DataPoint> set1Data = set1.Select(p => new CVAnalyzer.DataPoint { Voltage = p.Voltage, Current = p.Current }).ToList();
                List<CVAnalyzer.DataPoint> set2Data = set2.Select(p => new CVAnalyzer.DataPoint { Voltage = p.Voltage, Current = p.Current }).ToList();
                (oxidationBaseline, reductionBaseline) = CVAnalyzer.CalculateSeparateBaselines(set1Data, set2Data, AnodicBaselineStart, AnodicBaselineEnd, CathodicBaselineStart, CathodicBaselineEnd);

                PlotVoltammogramData();
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error processing voltammogram data: {ex.Message}");
            }
        }

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
                    EnableButtons();
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error loading Excel file: {ex.Message}");
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

        private async void LoadEmStatData()
        {
            try
            {
                var result = await FilePicker.Default.PickAsync(new PickOptions
                {
                    PickerTitle = "Please select an EMStat file",
                    FileTypes = new FilePickerFileType(new Dictionary<DevicePlatform, IEnumerable<string>>
                {
                    { DevicePlatform.iOS, new[] { "public.data" } },
                    { DevicePlatform.Android, new[] { "application/octet-stream" } },
                    { DevicePlatform.WinUI, new[] { ".emstat" } },
                    { DevicePlatform.Tizen, new[] { "application/octet-stream" } }
                })
                });

                if (result != null)
                {
                    var filePath = result.FullPath;
                    // Load and process the EMStat file
                    // Implement the logic to read and process the EMStat file
                    // For example, you can parse the file and update the ViewModel properties accordingly
                    Debug.WriteLine($"Loaded EMStat file: {filePath}");
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error loading EMStat file: {ex.Message}");
            }
        }

        public bool IsCycleSelected(int cycleNo)
        {
            return SelectedCycleNos.Contains(cycleNo);
        }
        private async void LoadCSV()
        {
            try
            {
                var result = await FilePicker.Default.PickAsync(new PickOptions
                {
                    PickerTitle = "Please select a CSV file",
                    FileTypes = new FilePickerFileType(new Dictionary<DevicePlatform, IEnumerable<string>>
                    {
                        { DevicePlatform.iOS, new[] { "public.comma-separated-values-text" } },
                        { DevicePlatform.Android, new[] { "text/csv" } },
                        { DevicePlatform.WinUI, new[] { ".csv" } },
                        { DevicePlatform.Tizen, new[] { "text/csv" } }
                    })
                });
                if (result != null)
                {
                    var filePath = result.FullPath;
                    loadedDataTable = LoadCsvIntoDataTable(filePath);
                    FileName = Path.GetFileName(filePath);   
                    FilePath = Path.GetDirectoryName(filePath);
                    UpdateCycleNos(loadedDataTable);
                    EnableButtons();
                }
            }
            catch (Exception)
            {
                // Handle exception
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
        private void EnableButtons()
        {
            IsPeakDetectEnabled = true;
            IsAddToProjectEnabled = true;
        }
        private DataTable LoadCsvIntoDataTable(string filePath)
        {
            DataTable dataTable = new DataTable();

            try
            {
                using (TextFieldParser parser = new TextFieldParser(filePath))
                {
                    parser.TextFieldType = FieldType.Delimited;
                    parser.SetDelimiters(",");

                    // Add columns
                    string[] headers = parser.ReadFields();
                    ValidateHeaders(headers);

                    foreach (string header in headers)
                    {
                        dataTable.Columns.Add(header);
                    }

                    // Add rows
                    while (!parser.EndOfData)
                    {
                        string[] fields = parser.ReadFields();
                        ValidateFields(fields, headers.Length);
                        dataTable.Rows.Add(fields);
                    }
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error loading CSV file: {ex.Message}");
                // Optionally, rethrow or handle the exception as needed
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
        private void ValidateFields(string[] fields, int expectedFieldCount)
        {
            if (fields == null || fields.Length != expectedFieldCount)
            {
                throw new InvalidDataException("CSV file contains rows with inconsistent field counts.");
            }
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
        private void ProcessData()
        {
            // Implement the logic to process the data
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
        private async Task NewProjectAsync()
        {
            try
            {
                var settings = Settings.Load();
                var result = await FolderPicker.PickAsync(default);

                if (result?.Folder != null)
                {
                    string projectRoot = result.Folder.Path;
                    settings.LastUsedDirectory = projectRoot;
                    settings.Save();

                    Directory.CreateDirectory(Path.Combine(projectRoot, "working"));
                    Directory.CreateDirectory(Path.Combine(projectRoot, "plots"));
                    Directory.CreateDirectory(Path.Combine(projectRoot, "reports"));
                    Directory.CreateDirectory(Path.Combine(projectRoot, "log"));
                    Directory.CreateDirectory(Path.Combine(projectRoot, "data"));
                    Directory.CreateDirectory(Path.Combine(projectRoot, "metadata"));

                    // Create project configuration file and metadata file
                    string metadataFilePath = Path.Combine(projectRoot, "metadata", "metadata.txt");
                    File.WriteAllText(metadataFilePath, "Positive and Negative peak potentials and currents and peak height");

                    // Load project files into the DataFiles collection
                    LoadProjectFiles();
                }
                else
                {
                    Debug.WriteLine("Folder selection was canceled or failed.");
                }
            }
            catch (Exception ex)
            {
                Debug.WriteLine(ex.Message);
            }
        }
        private void OpenProject()
        {
            // Implement the logic for opening an existing project
            LoadProjectFiles();
        }
        private void SaveProject()
        {
            // Implement the logic for saving the current project
            /*            
                string projectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
                if (Directory.Exists(projectRoot))
                {
                    // Save project data
                    string metadataFilePath = Path.Combine(projectRoot, "metadata", "metadata.txt");
                    File.WriteAllText(metadataFilePath, "Updated metadata content");
                }
            */

        }
        private void SaveAsProject()
        {
            // Implement the logic for saving the current project as a new project
            /*
                        string newProjectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "NewProjectAs");
                        Directory.CreateDirectory(newProjectRoot);
                        Directory.CreateDirectory(Path.Combine(newProjectRoot, "working"));
                        Directory.CreateDirectory(Path.Combine(newProjectRoot, "plots"));
                        Directory.CreateDirectory(Path.Combine(newProjectRoot, "reports"));
                        Directory.CreateDirectory(Path.Combine(newProjectRoot, "log"));
                        Directory.CreateDirectory(Path.Combine(newProjectRoot, "data"));
                        Directory.CreateDirectory(Path.Combine(newProjectRoot, "metadata"));

                        // Save project data
                        string metadataFilePath = Path.Combine(newProjectRoot, "metadata", "metadata.txt");
                        File.WriteAllText(metadataFilePath, "Updated metadata content for Save As");

            */
        }
        private void CloseProject()
        {
            // Implement the logic for closing the current project

            /*
                        string projectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
                        if (Directory.Exists(projectRoot))
                        {
                            Directory.Delete(projectRoot, true);
                        }
            */
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
            UpdateButtonStates();
            PeakDetect();
            PlotGraph();
            PeakDetect();
        }
        private void UpdateButtonStates()
        {
            //IsPeakDetectEnabled = SelectedCycleCount == 1;
            //IsAddToProjectEnabled = SelectedCycleCount == 1;
        }

        private double[] dataX;
        public double[] DataX
        {
            get
            {
                return dataX;
            }
            set
            {
                dataX = value;
                OnPropertyChanged(nameof(DataX));
            }
        }
        private double[] dataY;
        private int? _lastSelectedCycleNo;
        public double[] DataY
        {
            get
            {
                return dataY;
            }
            set
            {
                dataY = value;
                OnPropertyChanged(nameof(DataY));
            }
        }
        public int? LastSelectedCycleNo
        {
            get => _lastSelectedCycleNo;
            set => SetProperty(ref _lastSelectedCycleNo, value);
        }
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
        private void PlotDetectedPeaks(double[] potential, double[] current, double[] baseline, double[] correctedCurrent, int peakIndex, int negativePeakIndex)
        {
            int positivePeakIndex = FindPeakIndex(correctedCurrent);
            double positivePeakPotential = potential[positivePeakIndex];
            double positivePeakCurrent = correctedCurrent[positivePeakIndex];
            double negativePeakPotential = potential[negativePeakIndex];
            double negativePeakCurrent = correctedCurrent[negativePeakIndex];

            mauiPlot.Plot.Clear();
            var currentPlot = mauiPlot.Plot.Add.Scatter(potential, current, color: ScottPlot.Color.FromHex("#FF00FF"));
            currentPlot.LegendText = "Input current";

            var positiveVlinePlot = mauiPlot.Plot.Add.VerticalLine(positivePeakPotential, color: ScottPlot.Color.FromHex("#FF0000"));
            positiveVlinePlot.Text = positiveVlinePlot.LegendText = "Positive Peak";
            positiveVlinePlot.LabelOffsetY = 10;
            positiveVlinePlot.IsVisible = true;
            positiveVlinePlot.LabelOppositeAxis = true;

            var Label1 = mauiPlot.Plot.Add.Text($"({potential[positivePeakIndex]} V, {current[positivePeakIndex]} A)", potential[positivePeakIndex] + 10e-3, current[positivePeakIndex] + 5e-7);
            Label1.LabelBackgroundColor = ScottPlot.Color.FromHex("#FFeeee");
            Label1.LabelFontSize = 16;
            Label1.LabelBold = true;
            Label1.LabelPixelPadding = new ScottPlot.PixelPadding(10, 10, 10, 10);

            var negativeVlinePlot = mauiPlot.Plot.Add.VerticalLine(negativePeakPotential, color: ScottPlot.Color.FromHex("#0000FF"));
            negativeVlinePlot.Text = negativeVlinePlot.LegendText = "Negative Peak";
            negativeVlinePlot.LabelOffsetY = 10;
            negativeVlinePlot.IsVisible = true;
            negativeVlinePlot.LabelOppositeAxis = true;

            var Label2 = mauiPlot.Plot.Add.Text($"({potential[negativePeakIndex]} V, {current[negativePeakIndex]} A)", potential[negativePeakIndex] + 10e-3, current[negativePeakIndex] - 2e-7);
            Label2.LabelBackgroundColor = ScottPlot.Color.FromHex("#eeeeFF");
            Label2.LabelFontSize = 16;
            Label2.LabelBold = true;

            mauiPlot.Plot.XLabel("Potential (V)");
            mauiPlot.Plot.YLabel("Curent (A)");
            mauiPlot.Plot.ShowLegend();
            mauiPlot.Refresh();
        }
        public static double[] FitLinearBaseline(double[] potential, double[] current)
        {
            // ใช้ MathNet.Numerics สำหรับการประมาณเส้นตรง
            var coefficients = Fit.Line(potential, current);
            double slope = coefficients.Item1;
            double intercept = coefficients.Item2;
            double[] baseline = new double[potential.Length];
            for (int i = 0; i < potential.Length; i++)
            {
                baseline[i] = slope * potential[i] + intercept;
            }
            return baseline;
        }
        public static double[] SubtractBaseline(double[] current, double[] baseline)
        {
            return current.Zip(baseline, (c, b) => c - b).ToArray();
        }
        public static int FindPeakIndex(double[] correctedCurrent)
        {
            int peakIndex = 0;
            double maxCurrent = correctedCurrent[0];

            for (int i = 1; i < correctedCurrent.Length; i++)
            {
                if (correctedCurrent[i] > maxCurrent)
                {
                    maxCurrent = correctedCurrent[i];
                    peakIndex = i;
                }
            }
            return peakIndex;
        }
        public static int FindNegativePeakIndex(double[] correctedCurrent)
        {
            int peakIndex = 0;
            double minCurrent = correctedCurrent[0];

            for (int i = 1; i < correctedCurrent.Length; i++)
            {
                if (correctedCurrent[i] < minCurrent)
                {
                    minCurrent = correctedCurrent[i];
                    peakIndex = i;
                }
            }
            return peakIndex;
        }
        private void AddToProject()
        {
            if (LastSelectedCycleNo.HasValue && dataCycle.ContainsKey(LastSelectedCycleNo.Value))
            {
                var cycleData = dataCycle[LastSelectedCycleNo.Value];
                var potential = cycleData.Select(d => Convert.ToDouble(d["Voltage"])).ToArray();
                var current = cycleData.Select(d => Convert.ToDouble(d["Current"])).ToArray();

                var settings = Settings.Load();
                string projectRoot;

                if (!string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory))
                {
                    projectRoot = settings.LastUsedDirectory;
                }
                else
                {
                    projectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
                }

                string dataDirectory = Path.Combine(projectRoot, "data");
                Directory.CreateDirectory(dataDirectory);

                string fileName = $"Cycle_{LastSelectedCycleNo.Value}.csv";
                string filePath = Path.Combine(dataDirectory, fileName);

                using (var writer = new StreamWriter(filePath))
                {
                    writer.WriteLine("Voltage,Current");
                    for (int i = 0; i < potential.Length; i++)
                    {
                        writer.WriteLine($"{potential[i]},{current[i]}");
                    }
                }

                // Add the file name to the DataFiles collection
                DataFiles.Add(fileName);

                Debug.WriteLine($"Data for cycle {LastSelectedCycleNo.Value} added to project.");
            }
            else
            {
                Debug.WriteLine("No cycle selected or data not available for the selected cycle.");
            }
        }
        private void LoadProjectFiles()
        {
            var settings = Settings.Load();
            string projectRoot;

            if (!string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory))
            {
                projectRoot = settings.LastUsedDirectory;
            }
            else
            {
                projectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
            }

            string dataDirectory = Path.Combine(projectRoot, "data");

            if (Directory.Exists(dataDirectory))
            {
                var files = Directory.GetFiles(dataDirectory);
                DataFiles.Clear();
                foreach (var file in files)
                {
                    DataFiles.Add(Path.GetFileName(file));
                    Debug.WriteLine($"DataFiles.Count =  {DataFiles.Count}");
                }
            }
        }
        private void ExecuteLoadGraphCommand(string fileName)
        {
            LoadGraph(fileName);
        }
        private void LoadGraph(string fileName)
        {
            // Disable the buttons when LoadGraph is called
            //IsPeakDetectEnabled = false;
            //IsAddToProjectEnabled = false;
            var settings = Settings.Load();
            string projectRoot;

            if (!string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory))
            {
                projectRoot = settings.LastUsedDirectory;
            }
            else
            {
                projectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
            }

            string dataDirectory = Path.Combine(projectRoot, "data");
            string filePath = Path.Combine(dataDirectory, fileName);

            if (File.Exists(filePath))
            {
                var dataTable = LoadCsvIntoDataTable(filePath);
                var dataX = dataTable.AsEnumerable().Select(row => Convert.ToDouble(row["Voltage"])).ToArray();
                var dataY = dataTable.AsEnumerable().Select(row => Convert.ToDouble(row["Current"])).ToArray();

                var potential = dataTable.AsEnumerable().Select(row => Convert.ToDouble(row["Voltage"])).ToArray();
                var current = dataTable.AsEnumerable().Select(row => Convert.ToDouble(row["Current"])).ToArray();

                var baseline = FitLinearBaseline(potential, current);
                var correctedCurrent = SubtractBaseline(current, baseline);

                int positivePeakIndex = FindPeakIndex(correctedCurrent);
                int negativePeakIndex = FindNegativePeakIndex(correctedCurrent);

                double positivePeakPotential = potential[positivePeakIndex];
                double positivePeakCurrent = correctedCurrent[positivePeakIndex];
                double negativePeakPotential = potential[negativePeakIndex];
                double negativePeakCurrent = correctedCurrent[negativePeakIndex];

                Debug.WriteLine($"Positive Peak detected at potential: {positivePeakPotential} V, current: {positivePeakCurrent} A");
                Debug.WriteLine($"Negative Peak detected at potential: {negativePeakPotential} V, current: {negativePeakCurrent} A");

                mauiPlot.Plot.Clear();

                var currentPlot = mauiPlot.Plot.Add.Scatter(potential, current, color: ScottPlot.Color.FromHex("#FF00FF"));
                currentPlot.LegendText = "Input current";

                var positiveVlinePlot = mauiPlot.Plot.Add.VerticalLine(positivePeakPotential, color: ScottPlot.Color.FromHex("#FF0000"));
                positiveVlinePlot.Text = positiveVlinePlot.LegendText = "Positive Peak";
                positiveVlinePlot.LabelOffsetY = 10;
                positiveVlinePlot.IsVisible = true;
                positiveVlinePlot.LabelOppositeAxis = true;

                var Label1 = mauiPlot.Plot.Add.Text($"({potential[positivePeakIndex]} V, {current[positivePeakIndex]} A)", potential[positivePeakIndex] + 10e-3, current[positivePeakIndex] + 5e-7);
                Label1.LabelBackgroundColor = ScottPlot.Color.FromHex("#FFeeee");
                Label1.LabelFontSize = 16;
                Label1.LabelBold = true;
                Label1.LabelPixelPadding = new ScottPlot.PixelPadding(10, 10, 10, 10);

                var negativeVlinePlot = mauiPlot.Plot.Add.VerticalLine(negativePeakPotential, color: ScottPlot.Color.FromHex("#0000FF"));
                negativeVlinePlot.Text = negativeVlinePlot.LegendText = "Negative Peak";
                negativeVlinePlot.LabelOffsetY = 10;
                negativeVlinePlot.IsVisible = true;
                negativeVlinePlot.LabelOppositeAxis = true;

                var Label2 = mauiPlot.Plot.Add.Text($"({potential[negativePeakIndex]} V, {current[negativePeakIndex]} A)", potential[negativePeakIndex] + 10e-3, current[negativePeakIndex] - 2e-7);
                Label2.LabelBackgroundColor = ScottPlot.Color.FromHex("#eeeeFF");
                Label2.LabelFontSize = 16;
                Label2.LabelBold = true;

                mauiPlot.Plot.XLabel("Potential (V)");
                mauiPlot.Plot.YLabel("Current (A)");
                mauiPlot.Plot.Axes.AutoScale();
                mauiPlot.Plot.ShowLegend();
                mauiPlot.Refresh();
            }
            else
            {
                Debug.WriteLine($"File {filePath} does not exist.");
            }
        }
        private async void ExecuteRenameCommand(string fileName)
        {
            // Implement the logic to rename the file
            string newFileName = await Application.Current.MainPage.DisplayPromptAsync("Rename", "Enter new name:", initialValue: fileName);
            if (!string.IsNullOrEmpty(newFileName) && newFileName != fileName)
            {
                var settings = Settings.Load();
                string projectRoot = !string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory)
                    ? settings.LastUsedDirectory
                    : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");

                string dataDirectory = Path.Combine(projectRoot, "data");
                string oldFilePath = Path.Combine(dataDirectory, fileName);
                string newFilePath = Path.Combine(dataDirectory, newFileName);

                if (File.Exists(oldFilePath))
                {
                    File.Move(oldFilePath, newFilePath);
                    DataFiles[DataFiles.IndexOf(fileName)] = newFileName;
                    LoadProjectFiles();
                }
            }
        }
        private async void ExecuteDeleteCommand(string fileName)
        {
            bool isConfirmed = await Application.Current.MainPage.DisplayAlert(
                "Confirm Delete",
                $"Are you sure you want to delete the file '{fileName}'?",
                "Yes",
                "No");

            if (isConfirmed)
            {
                var settings = Settings.Load();
                string projectRoot = !string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory)
                    ? settings.LastUsedDirectory
                    : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");

                string dataDirectory = Path.Combine(projectRoot, "data");
                string filePath = Path.Combine(dataDirectory, fileName);

                if (File.Exists(filePath))
                {
                    File.Delete(filePath);
                    DataFiles.Remove(fileName);
                    LoadProjectFiles();
                }
            }
        }
        private void CompareCharts()
        {
            var settings = Settings.Load();
            string projectRoot = GetProjectRoot(settings);

            string dataDirectory = Path.Combine(projectRoot, "data");
            string metadataDirectory = Path.Combine(projectRoot, "metadata");
            string metadataFilePath = Path.Combine(metadataDirectory, "metadata.csv");

            EnsureDirectoryExists(metadataDirectory);

            var metadataList = new List<string>();

            if (Directory.Exists(dataDirectory))
            {
                var files = Directory.GetFiles(dataDirectory, "*.csv");

                var plt = mauiPlot.Plot;
                plt.Clear();

                // Define a list of colors to use for the data series
                var colors = new List<string> { "#000000", "#FF0000", "#0000FF", "#008800", "#aaaa00", "#FF00FF", "#00aaaa" };

                int colorIndex = 0;
                foreach (var file in files)
                {
                    var dataTable = LoadCsvIntoDataTable(file);
                    var x = dataTable.AsEnumerable().Select(row => Convert.ToDouble(row["Voltage"])).ToArray();
                    var y = dataTable.AsEnumerable().Select(row => Convert.ToDouble(row["Current"])).ToArray();

                    var baseline = FitLinearBaseline(x, y);
                    var correctedCurrent = SubtractBaseline(y, baseline);

                    int positivePeakIndex = FindPeakIndex(correctedCurrent);
                    int negativePeakIndex = FindNegativePeakIndex(correctedCurrent);

                    double positivePeakPotential = x[positivePeakIndex];
                    double positivePeakCurrent = correctedCurrent[positivePeakIndex];
                    double negativePeakPotential = x[negativePeakIndex];
                    double negativePeakCurrent = correctedCurrent[negativePeakIndex];
                    double concentration = 1.0e-3; //mM

                    // Calculate peak heights
                    double positivePeakHeight = positivePeakCurrent - baseline[positivePeakIndex];
                    double negativePeakHeight = negativePeakCurrent - baseline[negativePeakIndex];

                    // Add metadata to the list
                    metadataList.Add($"{Path.GetFileName(file)},{positivePeakPotential},{positivePeakCurrent},{positivePeakHeight},{negativePeakPotential},{negativePeakCurrent},{negativePeakHeight},{concentration}");

                    var scatter = plt.Add.Scatter(x, y);
                    scatter.Color = ScottPlot.Color.FromHex(colors[colorIndex % colors.Count]); // Set unique color for each file
                    scatter.LegendText = Path.GetFileName(file);
                    colorIndex++;
                }

                plt.XLabel("Potential (V)");
                plt.YLabel("Current (A)");
                plt.Add.Legend();
                plt.Axes.AutoScale();
                mauiPlot.Refresh();

                WriteMetadataToFile(metadataFilePath, metadataList);
            }
            else
            {
                Debug.WriteLine($"Data directory {dataDirectory} does not exist.");
            }
        }
        private string GetProjectRoot(Settings settings)
        {
            return !string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory)
                ? settings.LastUsedDirectory
                : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
        }
        private void EnsureDirectoryExists(string directoryPath)
        {
            if (!Directory.Exists(directoryPath))
            {
                Directory.CreateDirectory(directoryPath);
            }
        }
        private void WriteMetadataToFile(string metadataFilePath, List<string> metadataList)
        {
            using (var writer = new StreamWriter(metadataFilePath))
            {
                writer.WriteLine("FileName,PositivePeakPotential,PositivePeakCurrent,PositivePeakHeight,NegativePeakPotential,NegativePeakCurrent,NegativePeakHeight,Concentration");
                foreach (var metadata in metadataList)
                {
                    writer.WriteLine(metadata);
                }
            }
        }
        private void ComparePeaks()
        {
            var settings = Settings.Load();
            string projectRoot;

            if (!string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory))
            {
                projectRoot = settings.LastUsedDirectory;
            }
            else
            {
                projectRoot = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");
            }

            string metadataDirectory = Path.Combine(projectRoot, "metadata");
            string metadataFilePath = Path.Combine(metadataDirectory, "metadata.csv");

            if (File.Exists(metadataFilePath))
            {
                var plt = mauiPlot.Plot;
                mauiPlot.Plot.Clear();

                var positivePeakPotentials = new List<double>();
                var positivePeakCurrents = new List<double>();
                var positivePeakHeights = new List<double>();
                var negativePeakPotentials = new List<double>();
                var negativePeakCurrents = new List<double>();
                var negativePeakHeights = new List<double>();
                var concentrations = new List<double>();

                using (var reader = new StreamReader(metadataFilePath))
                {
                    // Skip the header line
                    reader.ReadLine();

                    while (!reader.EndOfStream)
                    {
                        var line = reader.ReadLine();
                        var values = line.Split(',');

                        positivePeakPotentials.Add(Convert.ToDouble(values[1]));
                        positivePeakCurrents.Add(Convert.ToDouble(values[2]));
                        positivePeakHeights.Add(Convert.ToDouble(values[3]));
                        negativePeakPotentials.Add(Convert.ToDouble(values[4]));
                        negativePeakCurrents.Add(Convert.ToDouble(values[5]));
                        negativePeakHeights.Add(Convert.ToDouble(values[6]));
                        concentrations.Add(Convert.ToDouble(values[7]));
                    }
                }

                PlotPositivePeakHeights(plt, positivePeakHeights, concentrations);

                PlotNegativePeakHeights(plt, negativePeakHeights, concentrations);

                Coordinates pt1, pt2;
                PlotPositivePeakTrendLine(plt, positivePeakHeights, concentrations);

                PlotNegativePeakTrendLine(plt, negativePeakHeights, concentrations, out pt1, out pt2);

                // Set axis labels
                plt.XLabel("Concentration (mM)");
                plt.YLabel("Peak height (A)");
                plt.Add.Legend();
                mauiPlot.Plot.Axes.AutoScale();
                mauiPlot.Refresh();
            }
            else
            {
                Debug.WriteLine($"Metadata file {metadataFilePath} does not exist.");
            }
        }
        private static void PlotNegativePeakTrendLine(Plot plt, List<double> negativePeakHeights, List<double> concentrations, out Coordinates pt1, out Coordinates pt2)
        {
            // plot the negative regression line
            ScottPlot.Statistics.LinearRegression negReg = new(concentrations.ToArray(), negativePeakHeights.ToArray());
            pt1 = new(concentrations.ToArray().First(), negReg.GetValue(concentrations.ToArray().First()));
            pt2 = new(concentrations.ToArray().Last(), negReg.GetValue(concentrations.ToArray().Last()));
            var negLine = plt.Add.Line(pt1, pt2);
            negLine.MarkerSize = 0;
            negLine.LineWidth = 2;
            negLine.LineColor = ScottPlot.Color.FromHex("#0000FF");
            negLine.LinePattern = LinePattern.Dashed;
            negLine.LegendText = "Negative peak regression";

            // Format the formula with R-squared to show more decimal places
            string negFormulaWithRSquared = $"y = {negReg.Slope:E4}x + {negReg.Offset:E4}  (R² =  {negReg.Rsquared:F4})";
            var negRegText = plt.Add.Text(negFormulaWithRSquared, pt1);
            negRegText.LabelFontSize = 16;
        }
        private static void PlotPositivePeakTrendLine(Plot plt, List<double> positivePeakHeights, List<double> concentrations)
        {
            // plot positive regression line
            ScottPlot.Statistics.LinearRegression posReg = new(concentrations.ToArray(), positivePeakHeights.ToArray());

            Coordinates pt1 = new(concentrations.ToArray().First(), posReg.GetValue(concentrations.ToArray().First()));
            Coordinates pt2 = new(concentrations.ToArray().Last(), posReg.GetValue(concentrations.ToArray().Last()));
            var posLine = plt.Add.Line(pt1, pt2);
            posLine.MarkerSize = 0;
            posLine.LineWidth = 2;
            posLine.LinePattern = LinePattern.Dashed;
            posLine.LineColor = ScottPlot.Color.FromHex("#FF0000");
            posLine.LegendText = "Positive peak regression";

            string posFormulaWithRSquared = $"y = {posReg.Slope:E4}x + {posReg.Offset:E4} (R² = {posReg.Rsquared:F4})";
            var posRegText = plt.Add.Text(posFormulaWithRSquared, pt1);
            posRegText.LabelFontSize = 16;
        }
        private static void PlotNegativePeakHeights(Plot plt, List<double> negativePeakHeights, List<double> concentrations)
        {
            // Plot negative peak heights
            var negativeHeightScatter = plt.Add.Scatter(concentrations.ToArray(), negativePeakHeights.ToArray());
            negativeHeightScatter.Color = ScottPlot.Color.FromHex("#AAAAFF");
            negativeHeightScatter.LegendText = "Negative Peak Heights";
            negativeHeightScatter.MarkerSize = 10;
            negativeHeightScatter.MarkerShape = MarkerShape.FilledCircle;
            negativeHeightScatter.MarkerColor = ScottPlot.Color.FromHex("#0000FF");
            negativeHeightScatter.LineWidth = 0;
        }
        private static void PlotPositivePeakHeights(Plot plt, List<double> positivePeakHeights, List<double> concentrations)
        {
            // Plot positive peak heights
            var positiveHeightScatter = plt.Add.Scatter(concentrations.ToArray(), positivePeakHeights.ToArray());
            positiveHeightScatter.LegendText = "Positive Peak Heights";
            positiveHeightScatter.MarkerSize = 10;
            positiveHeightScatter.MarkerShape = MarkerShape.FilledCircle;
            positiveHeightScatter.MarkerColor = ScottPlot.Color.FromHex("#FF0000");
            positiveHeightScatter.LineWidth = 0;
        }
        private void OnEditMetaDataCommandCommandExecuted(object parameter)
        {
            if (parameter is string fileName)
            {
                ExecuteAddConcentrationCommand(fileName);
            }
            // Implement the action for the new command
        }
        private async void ExecuteAddConcentrationCommand(string fileName)
        {
            string concentration = await Application.Current.MainPage.DisplayPromptAsync($"Add Concentration to {fileName}", "Enter concentration value:");
            if (!string.IsNullOrEmpty(concentration))
            {
                AddConcentrationToMetadata(fileName, concentration);
            }
        }
        private void AddConcentrationToMetadata(string fileName, string concentration)
        {
            var settings = Settings.Load();
            string projectRoot = !string.IsNullOrEmpty(settings.LastUsedDirectory) && Directory.Exists(settings.LastUsedDirectory)
                ? settings.LastUsedDirectory
                : Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments), "CurrentProject");

            string metadataDirectory = Path.Combine(projectRoot, "metadata");
            string metadataFilePath = Path.Combine(metadataDirectory, "metadata.csv");

            if (!Directory.Exists(metadataDirectory))
            {
                Directory.CreateDirectory(metadataDirectory);
            }

            if (File.Exists(metadataFilePath))
            {
                var lines = File.ReadAllLines(metadataFilePath).ToList();
                var fileLine = lines.FirstOrDefault(line => line.StartsWith(fileName));
                if (fileLine != null)
                {
                    lines.Remove(fileLine);
                    var parts = fileLine.Split(',');
                    parts[^1] = concentration;
                    fileLine = string.Join(",", parts);
                    //fileLine += $",{concentration}";
                    lines.Add(fileLine);
                }
                else
                {
                    lines.Add($"{fileName},,,,,,,{concentration}");
                }
                File.WriteAllLines(metadataFilePath, lines);
            }
            else
            {
                using (var writer = new StreamWriter(metadataFilePath))
                {
                    writer.WriteLine("FileName,PositivePeakPotential,PositivePeakCurrent,PositivePeakHeight,NegativePeakPotential,NegativePeakCurrent,NegativePeakHeight,Concentration");
                    writer.WriteLine($"{fileName},,,,,,,{concentration}");
                }
            }
        }
        public void OnFindBaseline()
        {
            Debug.WriteLine("Find Baseline");

            // Specify the path to your CSV file. Use a directory where the application has write permissions.
            string documentsPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
            string csvFilePath = Path.Combine(documentsPath, "voltammogram_data.csv");

            // Create a dummy CSV file (for demonstration purposes)
            // In a real scenario, you'd already have this file.
            if (!File.Exists(csvFilePath))
            {
                using (var writer = new StreamWriter(csvFilePath))
                using (var csv = new CsvWriter(writer, CultureInfo.InvariantCulture))
                {
                    var dummyData = new List<CVAnalyzer.DataPoint>()
                            {
                                new CVAnalyzer.DataPoint { Voltage = -0.4, Current = -12.2 },
                                new CVAnalyzer.DataPoint { Voltage = -0.3, Current = -4.2 },
                                new CVAnalyzer.DataPoint { Voltage = -0.2, Current = -3.0 },
                                new CVAnalyzer.DataPoint { Voltage = -0.1, Current = -2.3 },
                                new CVAnalyzer.DataPoint { Voltage = 0.0, Current = -1.5 },
                                new CVAnalyzer.DataPoint { Voltage = 0.1, Current = 5.5 },
                                new CVAnalyzer.DataPoint { Voltage = 0.2, Current = 8.6 },
                                new CVAnalyzer.DataPoint { Voltage = 0.3, Current = 6.0 },
                                new CVAnalyzer.DataPoint { Voltage = 0.4, Current = 4.5 },
                                new CVAnalyzer.DataPoint { Voltage = 0.5, Current = 3.9 },
                                new CVAnalyzer.DataPoint { Voltage = 0.6, Current = 4.0 },
                            };
                    csv.WriteRecords(dummyData);
                }
                Debug.WriteLine($"Created dummy CSV file at: {csvFilePath}");
            }
            else
            {
                Debug.WriteLine($"Using existing CSV file at: {csvFilePath}");
            }

            // 2. Read the data
            try
            {
                VoltammogramData = CVAnalyzer.ReadDataFromCsv(csvFilePath);
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error reading CSV file: {ex.Message}");
                return; // Exit if there's an error reading the file.
            }

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

            Debug.WriteLine($"maxVoltage = {maxVoltage}, index = {maxVoltageIndex}");

            // Find the index of the minimum voltage
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

            Debug.WriteLine($"minVoltage = {minVoltage}, index = {minVoltageIndex}");

            // Find all zero crossing indices
            List<int> zeroCrossingIndices = new List<int>();
            for (int i = 1; i < allData.Count; i++)
            {
                if ((allData[i - 1].Voltage < 0 && allData[i].Voltage >= 0) ||
                    (allData[i - 1].Voltage >= 0 && allData[i].Voltage < 0))
                {
                    zeroCrossingIndices.Add(i);
                }
            }

            Debug.WriteLine("Zero Crossing Indices:");
            foreach (var index in zeroCrossingIndices)
            {
                Debug.WriteLine(index);
            }

            // Separate the data into four parts
            part1 = allData.Take(maxVoltageIndex + 1).ToList();
            part2 = allData.Skip(maxVoltageIndex).TakeWhile(p => p.Voltage >= 0).ToList();
            part3 = allData.SkipWhile(p => p.Voltage >= 0).Take(minVoltageIndex - zeroCrossingIndices.Last()).ToList();
            part4 = allData.Skip(minVoltageIndex).ToList();

            // Combine into two sets
            set1 = part4.Concat(part1).ToList();
            set2 = part2.Concat(part3).ToList();

            // Find peaks in set1 and set2
            if (ManualSelectedAnodePeak == false)
            {
                peaksSet1 = cvAanalyzer.FindPeaks(set1, positive: true);
            }
            if (ManualSelectedCathodePeak == false)
            {
                peaksSet2 = cvAanalyzer.FindPeaks(set2, positive: false);
            }


            //// Find baseline range from current derivative
            //int minWindowWidth = 5;
            //int maxWindowWidth = (int)(0.4 * VoltammogramData.Count);
            //baselineRange = cvAanalyzer.FindBaselineRangeFromDerivative(currentDerivative, VoltammogramData, Tolerance, minWindowWidth, maxWindowWidth);

            List<CVAnalyzer.DataPoint> set1Data = set1.Select(p => new CVAnalyzer.DataPoint { Voltage = p.Voltage, Current = p.Current }).ToList();
            List<CVAnalyzer.DataPoint> set2Data = set2.Select(p => new CVAnalyzer.DataPoint { Voltage = p.Voltage, Current = p.Current }).ToList();
            (oxidationBaseline, reductionBaseline) = CVAnalyzer.CalculateSeparateBaselines(set1Data, set2Data, AnodicBaselineStart, AnodicBaselineEnd, CathodicBaselineStart, CathodicBaselineEnd);

            //var anodicPeakHeight = CalculatePeakHeight(peaksSet1[0].Voltage, oxidationBaseline);


            //Debug.WriteLine($"Baseline Range: {baselineRange.Item1}V to {baselineRange.Item2}V");
            PlotVoltammogramData();
        }
        public void PlotVoltammogramData()
        {
            var plt = mauiPlot.Plot;
            mauiPlot.Plot.Clear();
            var voltammogramDataPlot = plt.Add.Scatter(
                VoltammogramData.Select(p => p.Voltage).ToArray(),
                VoltammogramData.Select(p => p.Current).ToArray(),
                ScottPlot.Color.FromHex("#0000FF")
            );
            voltammogramDataPlot.LegendText = "Original Data";
            voltammogramDataPlot.MarkerSize = 5;

            if (IsPart1Selected)
            {
                var part1Plot = plt.Add.Scatter(
                    part1.Select(p => p.Voltage).ToArray(),
                    part1.Select(p => p.Current).ToArray(),
                    ScottPlot.Color.FromHex("#FF0000")
                );
                part1Plot.LegendText = "Part 1";
                part1Plot.MarkerSize = 5;
            }

            if (IsPart2Selected)
            {
                var part2Plot = plt.Add.Scatter(
                    part2.Select(p => p.Voltage).ToArray(),
                    part2.Select(p => p.Current).ToArray(),
                    ScottPlot.Color.FromHex("#00FF00")
                );
                part2Plot.LegendText = "Part 2";
                part2Plot.MarkerSize = 5;
            }

            if (IsPart3Selected)
            {
                var part3Plot = plt.Add.Scatter(
                    part3.Select(p => p.Voltage).ToArray(),
                    part3.Select(p => p.Current).ToArray(),
                    ScottPlot.Color.FromHex("#00ddff")
                );
                part3Plot.LegendText = "Part 3";
                part3Plot.MarkerSize = 5;
            }

            if (IsPart4Selected)
            {
                var part4Plot = plt.Add.Scatter(
                    part4.Select(p => p.Voltage).ToArray(),
                    part4.Select(p => p.Current).ToArray(),
                    ScottPlot.Color.FromHex("#FFFF00")
                );
                part4Plot.LegendText = "Part 4";
                part4Plot.MarkerSize = 5;
            }

            if (IsSet1Selected)
            {
                var set1Plot = plt.Add.Scatter(
                    set1.Select(p => p.Voltage).ToArray(),
                    set1.Select(p => p.Current).ToArray(),
                    ScottPlot.Color.FromHex("#FF00FF")
                );
                set1Plot.LegendText = "Set 1";
                set1Plot.MarkerSize = 5;
            }

            if (IsSet2Selected)
            {
                var set2Plot = plt.Add.Scatter(
                    set2.Select(p => p.Voltage).ToArray(),
                    set2.Select(p => p.Current).ToArray(),
                    ScottPlot.Color.FromHex("#00FFFF")
                );
                set2Plot.LegendText = "Set 2";
                set2Plot.MarkerSize = 5;
            }

            var oxidationBaselineVoltage = oxidationBaseline.Select(p => p.Voltage).ToArray();
            var oxidationBaselineCurrent = oxidationBaseline.Select(p => p.Current).ToArray();

            var oxidationBaselinePlot = plt.Add.Scatter(
                oxidationBaselineVoltage,
                oxidationBaselineCurrent,
                ScottPlot.Color.FromHex("#FF00FF")
            );
            oxidationBaselinePlot.LegendText = "Oxidation Baseline";
            oxidationBaselinePlot.MarkerSize = 0;
            oxidationBaselinePlot.LinePattern = LinePattern.Dashed;

            var reductionBaselinePlot = plt.Add.Scatter(
                reductionBaseline.Select(p => p.Voltage).ToArray(),
                reductionBaseline.Select(p => p.Current).ToArray(),
                ScottPlot.Color.FromHex("#00aa00")
            );
            reductionBaselinePlot.LegendText = "Reduction Baseline";
            reductionBaselinePlot.MarkerSize = 0;
            reductionBaselinePlot.LinePattern = LinePattern.Dashed;

            var anodicBaselineStartMarker = plt.Add.Marker(AnodicBaselineStart,
                set1.OrderBy(p => Math.Abs(p.Voltage - AnodicBaselineStart)).FirstOrDefault().Current,
                ScottPlot.MarkerShape.Eks, size: 15, color: ScottPlot.Color.FromHex("#aa55aa"));
            anodicBaselineStartMarker.LineWidth = 3;

            var anodicBaselineEndMarker = plt.Add.Marker(AnodicBaselineEnd,
                            set1.OrderBy(p => Math.Abs(p.Voltage - AnodicBaselineEnd)).FirstOrDefault().Current,
                            ScottPlot.MarkerShape.Eks, size: 15, color: ScottPlot.Color.FromHex("#ee55ee"));
            anodicBaselineEndMarker.LineWidth = 3;

            var cathodicBaselineStart = plt.Add.Marker(CathodicBaselineStart,
                            set2.OrderBy(p => Math.Abs(p.Voltage - CathodicBaselineStart)).FirstOrDefault().Current,
                            ScottPlot.MarkerShape.Eks, size: 15, color: ScottPlot.Color.FromHex("#55aa55"));
            cathodicBaselineStart.LineWidth = 3;

            var cathodicBaselineEnd = plt.Add.Marker(CathodicBaselineEnd,
                            set2.OrderBy(p => Math.Abs(p.Voltage - CathodicBaselineEnd)).FirstOrDefault().Current,
                            ScottPlot.MarkerShape.Eks, size: 15, color: ScottPlot.Color.FromHex("#55bb55"));
            cathodicBaselineEnd.LineWidth = 3;



            if (peaksSet1.Count > 0)
            {
                var firstPeak = peaksSet1[0];
                var peaksSet1Plot = plt.Add.Scatter(
                    firstPeak.Voltage,
                    firstPeak.Current,
                    ScottPlot.Color.FromHex("#FF0000")
                );
                peaksSet1Plot.LegendText = "Peaks Set 1";
                var firstPeakPlot = plt.Add.Marker(firstPeak.Voltage, firstPeak.Current, ScottPlot.MarkerShape.FilledCircle, size: 10, color: ScottPlot.Color.FromHex("#FF0000"));
                firstPeakPlot.LineWidth = 3;
            }

            if (peaksSet2.Count > 0)
            {
                var firstPeak = peaksSet2[0];
                var peaksSet2Plot = plt.Add.Scatter(
                    firstPeak.Voltage, 
                    firstPeak.Current, 
                    ScottPlot.Color.FromHex("#008000") );
                peaksSet2Plot.LegendText = "Peaks Set 2";
                var firstPeakPlot = plt.Add.Marker(firstPeak.Voltage, firstPeak.Current, ScottPlot.MarkerShape.FilledCircle, size: 10, color: ScottPlot.Color.FromHex("#008000"));
                firstPeakPlot.LineWidth = 3;
            }

            // Plot line from peaksSet1[0].Current to intersect with oxidationBaseline
            var peakCurrent = peaksSet1[0].Current;
            var peakVoltage = peaksSet1[0].Voltage;
            var baselineCurrent = oxidationBaseline?.OrderBy(p => Math.Abs(p.Voltage - peakVoltage)).FirstOrDefault()?.Current ?? 0;

            var intersectionLineAnodic = plt.Add.ScatterLine(
                new double[] { peakVoltage, peakVoltage },
                new double[] { peakCurrent, baselineCurrent },
                ScottPlot.Color.FromHex("#FF0000")
            );
            intersectionLineAnodic.LinePattern = LinePattern.Dashed;

            peakCurrent = peaksSet2[0].Current;
            peakVoltage = peaksSet2[0].Voltage;
            baselineCurrent = reductionBaseline?.OrderBy(p => Math.Abs(p.Voltage - peakVoltage)).FirstOrDefault()?.Current ?? 0;

            var intersectionLineCathodic = plt.Add.ScatterLine(
                new double[] { peakVoltage, peakVoltage },
                new double[] { peakCurrent, baselineCurrent },
                ScottPlot.Color.FromHex("#008000")
            );
            intersectionLineCathodic.LinePattern = LinePattern.Dashed;

            // Display anodicPeakHeight on chart
            var anodicPeakHeight = new CVAnalyzer().CalculatePeakHeight(peaksSet1[0].Voltage, oxidationBaseline, set1);
            var cathodicPeakHeight = new CVAnalyzer().CalculatePeakHeight(peaksSet2[0].Voltage, reductionBaseline, set2);
            AnodicPeakHeight = Math.Abs(anodicPeakHeight);
            CathodicPeakHeight = Math.Abs(cathodicPeakHeight);

            var annotationPlot = plt.Add.Annotation($"Anodic Peak Height: {anodicPeakHeight:E3} µA\nCathodic Peak Height: {cathodicPeakHeight:E3} µA");
            annotationPlot.Alignment = Alignment.UpperRight;
            //.Position(peakVoltage, peakCurrent + anodicPeakHeight / 2);

            plt.Title($"Voltammogram Data Segmentation Cycle {LastSelectedCycleNo.Value}");
            plt.XLabel("Potential (V)");
            plt.YLabel("Current (µA)");
            plt.ShowLegend();
            plt.Axes.AutoScale();
            mauiPlot.Refresh();
        }
    }
}

