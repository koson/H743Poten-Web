using CommunityToolkit.Maui.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.UI.Xaml.Controls;
using Poten2501.CustomControls;
using Poten2501.Models;
using Poten2501.Services;
using ScottPlot.Maui;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO.Ports;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;

namespace Poten2501.ViewModels
{
    public partial class CAViewModel : ObservableObject, INotifyPropertyChanged
    {
        //private MauiPlot mauiplot;
        //private PlotView _plotView;
        private readonly ISerialPortService _serialPortService;
        public ICommand RefreshPortsCommand { get; }
        public ICommand ConnectCommand { get; }
        public ICommand SendDataCommand { get; }
        public ICommand ClearReceivedDataCommand { get; }
         
        public ObservableCollection<string> AvailablePorts { get; } = [];
        public ObservableCollection<CADataEntry> CADataEntries { get; } = new();
        private readonly List<string> _caRawLines = new(); // Accumulate all received lines


        private readonly PlotView _plotView;
        public CAViewModel(PlotView plotView, ISerialPortService serialPortService)
        {
            _plotView = plotView;
            _serialPortService = serialPortService;
            _serialPortService.DataReceived += OnDataReceived;
            RefreshPortsCommand = new Command(RefreshPorts);
            ConnectCommand = new Command(TogglePortConnection, CanConnectOrDisconnect);
            SendDataCommand = new Command(SendData, CanSendData);
            ClearReceivedDataCommand = new Command(ClearReceivedData);
            PickerItems = ["1. (1mA/V)", "2. (100uA/V)", "3. (10uA/V)", "4. (1uA/V)"];
            SelectedPickerItem = PickerItems.FirstOrDefault();
            InductionPotential = 0.0f;   
            InductionDuration = 3.0f;    
            ElectrolysisPotential = 0.5f;
            ElectrolysisDuration = 10.0f; 
            RelaxationPotential = 0.0f;  
            RelaxationDuration = 3.0f;   
            RefreshPorts();
            WorkingFolderPath = Preferences.Default.Get(nameof(WorkingFolderPath), string.Empty);
            OnPropertyChanged(nameof(WorkingFolderPath));
        }

        private void OnDataReceived(object sender, byte[] data)
        {
            string receivedString = Encoding.UTF8.GetString(data);
            Debug.WriteLine($"Received data: {receivedString}");

            var lines = receivedString.Split(new[] { '\r', '\n' }, StringSplitOptions.RemoveEmptyEntries);

            bool updated = false;
            var dataXList = DataX?.ToList() ?? new List<double>();
            var dataYList = DataY?.ToList() ?? new List<double>();

            foreach (var line in lines)
            {
                _caRawLines.Add(line);
                if (line.StartsWith("CA,"))
                {
                    var parts = line.Split(',');
                    if (parts.Length >= 4 &&
                        double.TryParse(parts[1], out var time) &&
                        double.TryParse(parts[2], out var potential) &&
                        double.TryParse(parts[3], out var current))
                    {
                        var entry = new CADataEntry
                        {
                            Type = parts[0].Trim(),
                            Time = time,
                            Potential = potential,
                            Current = current
                        };
                        CACurrent = current;
                        CAPotential = potential;
                        App.Current?.Dispatcher.Dispatch(() => CADataEntries.Add(entry));
                        dataXList.Add(time);
                        dataYList.Add(current);
                        updated = true;
                    }
                }
            }
            if (updated)
            {
                DataX = dataXList.ToArray();
                DataY = dataYList.ToArray();
                App.Current?.Dispatcher.Dispatch(() =>
                {
                    _plotView.DataX = DataX;
                    _plotView.DataY = DataY;
                });
            }
            if (lines.Any(l => l.Contains("CA Operation Finished")))
            {
                SaveCADataToFile();
                _caRawLines.Clear();
            }
        }

        private void SaveCADataToFile()
        {
            if (string.IsNullOrEmpty(WorkingFolderPath) || string.IsNullOrEmpty(FileName))
                return;

            // Find the first line with "Induction Potential:"
            int startIdx = _caRawLines.FindIndex(l => l.Contains("Induction Potential:"));
            if (startIdx == -1)
                startIdx = 0;

            var linesToSave = _caRawLines.Skip(startIdx)
                .Where(l => !l.Contains("Chronoamperometry Measurement StartCAScan()"))
                .ToList();

            // Prepare output with header and only CA, lines in the requested format
            var outputLines = new List<string> { "Mode,Time,Potential,Current" };
            foreach (var line in linesToSave)
            {
                if (line.StartsWith("CA,"))
                {
                    var parts = line.Split(',');
                    if (parts.Length >= 4)
                    {
                        outputLines.Add($"{parts[0].Trim()},{parts[1].Trim()},{parts[2].Trim()},{parts[3].Trim()}");
                    }
                } 
            }

            string filePath = Path.Combine(WorkingFolderPath, FileName);
            try
            {
                File.WriteAllLines(filePath, outputLines);
                Debug.WriteLine($"CA data saved to {filePath}");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error saving CA data: {ex.Message}");
            }
        }

        private string _dataToSend;
        public string DataToSend
        {
            get => _dataToSend;
            set
            {
                if (_dataToSend != value)
                {
                    _dataToSend = value;
                    OnPropertyChanged(nameof(DataToSend));
                    UpdateSendDataCanExecute();
                }
            }
        }
        private List<string> _pickerItems;
        public List<string> PickerItems
        {
            get => _pickerItems;
            set => SetProperty(ref _pickerItems, value);
        }

        private int _noOfCycles = 1;
        public int NoOfCycles
        {
            get => _noOfCycles;
            set
            {
                if (_noOfCycles != value)
                {
                    _noOfCycles = value;
                    OnPropertyChanged(nameof(NoOfCycles));
                }
            }
        }

        private double _caPotential;
        public double CAPotential
        {
            get => _caPotential;
            set
            {
                if (_caPotential != value)
                {
                    _caPotential = value;
                    OnPropertyChanged(nameof(CAPotential));
                }
            }
        }

        private double _caCurrent;
        public double CACurrent
        {
            get => _caCurrent;
            set
            {
                if (_caCurrent != value)
                {
                    _caCurrent = value;
                    OnPropertyChanged(nameof(CACurrent));
                }
            }
        }

        private double _inductionPotential;     // Potential during the induction phase
        public double InductionPotential
        {
            get => _inductionPotential;
            set
            {
                if (_inductionPotential != value)
                {
                    _inductionPotential = value;
                    OnPropertyChanged(nameof(InductionPotential));
                }
            }
        }

        private double _inductionDuration;      // Duration of the induction phase
        public double InductionDuration
        {
            get => _inductionDuration;
            set
            {
                if (_inductionDuration != value)
                {
                    _inductionDuration = value;
                    OnPropertyChanged(nameof(InductionDuration));
                }
            }
        }

        private double _electrolysisPotential;  // Potential during the electrolysis phase
        public double ElectrolysisPotential
        {
            get => _electrolysisPotential;
            set
            {
                if (_electrolysisPotential != value)
                {
                    _electrolysisPotential = value;
                    OnPropertyChanged(nameof(ElectrolysisPotential));
                }
            }
        }

        private double _electrolysisDuration;   // Duration of the electrolysis phase
        public double ElectrolysisDuration
        {
            get => _electrolysisDuration;
            set
            {
                if (_electrolysisDuration != value)
                {
                    _electrolysisDuration = value;
                    OnPropertyChanged(nameof(ElectrolysisDuration));
                }
            }
        }
        private double _relaxationPotential;    // Potential during the relaxation phase
        public double RelaxationPotential
        {
            get => _relaxationPotential;
            set
            {
                if (_relaxationPotential != value)
                {
                    _relaxationPotential = value;
                    OnPropertyChanged(nameof(RelaxationPotential));
                }
            }
        }
        private double _relaxationDuration;     // Duration of the relaxation phase
        public double RelaxationDuration
        {
            get => _relaxationDuration;
            set
            {
                if (_relaxationDuration != value)
                {
                    _relaxationDuration = value;
                    OnPropertyChanged(nameof(RelaxationDuration));
                }
            }
        }

        [ObservableProperty]
        public partial string SelectedPickerItem { get; set; }

        #region Working Folder
        public string WorkingFolderPath
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(WorkingFolderPath));
                    UpdateFileName(1);
                    Preferences.Default.Set(nameof(WorkingFolderPath), value);
                }
            }
        }

        private void UpdateFileName(int noOfCycle)
        {
            if (!string.IsNullOrEmpty(WorkingFolderPath) && !string.IsNullOrEmpty(ProjectName))
            {
                // Always ensure the extension is ".csv"
                var baseName = $"{ProjectName}_{DateTime.Now:yyyyMMdd_HHmmss}_SCan_{noOfCycle}";
                baseName = baseName.Replace('.', '_');
                
                // Limit the base name if needed, but always add ".csv"
                int maxBaseLength = 80 - 4; // 4 for ".csv"
                if (baseName.Length > maxBaseLength)
                    baseName = baseName.Substring(0, maxBaseLength);



                FileName = $"{baseName}.csv";
                Debug.WriteLine(FileName);

            }
            else
            {
                FileName = string.Empty;
            }
        }

        public string ProjectName
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(ProjectName));
                    UpdateFileName(1);
                }
            }
        }
        public string FileName
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(FileName));
                }
            }
        }

        #endregion

        #region Commands

        [RelayCommand]
        private async Task SelectProjectFolder()
        {
            try
            {
                var result = await FolderPicker.PickAsync(default);
                if (result?.Folder != null)
                {
                    WorkingFolderPath = $"{result.Folder.Path}";
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

        [RelayCommand]
        private void ClearChart()
        {
            _plotView.Clear();
            CADataEntries.Clear();
            DataX = Array.Empty<double>();
            DataY = Array.Empty<double>();
            ClearReceivedData();
            _caRawLines.Clear();
            Debug.WriteLine("Chart cleared.");
        }

        [RelayCommand]
        private void UpdateCurrentRange(string CurrRange)
        {

            string dataToSend = "POTEn:DPV:CURRent:RANGe " + CurrRange[0];
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]  
        private async Task StartCAScan()
        {
            if (string.IsNullOrEmpty(WorkingFolderPath) || string.IsNullOrEmpty(ProjectName) || string.IsNullOrEmpty(FileName))
            {
                // Show an error message or handle the case where the folder or file name is not set
                return;
            }

            for (int i = 0; i < NoOfCycles; i++)
            {
                UpdateFileName(i + 1);
                clearChartCommand.Execute(null); // Clear the chart before starting a new scan

                string dataToSend = $"POTEn:CA:STARt  {InductionPotential}, {InductionDuration}, {ElectrolysisPotential}, {ElectrolysisDuration}, {RelaxationPotential}, {RelaxationDuration}";
                DataToSend = dataToSend;
                Debug.WriteLine($"Starting CA scan... {dataToSend}");
                await Task.Run(() => SendData());
                Debug.WriteLine($"CA scan started, wait scan to completed..");

                await WaitForScanCompletionAsync();
                Debug.WriteLine($"CA scan completed");
            }
        }

        private async Task WaitForScanCompletionAsync()
        {
            var tcs = new TaskCompletionSource<bool>();

            // Assuming OnDataReceived signals the end of a scan
            void OnScanCompleted(object sender, byte[] data)
            {
                string receivedString = Encoding.UTF8.GetString(data);
                Debug.WriteLine($"Received data: {receivedString}");
                if (receivedString.Contains("CA Operation Finished")) // Replace with actual completion signal
                {
                    _serialPortService.DataReceived -= OnScanCompleted;
                    tcs.SetResult(true);
                }
            }
            _serialPortService.DataReceived += OnScanCompleted;
            await tcs.Task; // Await the TaskCompletionSource's Task instead of returning it directly
        }



        #endregion

        public string ReceivedData
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(ReceivedData));
                }
            }
        }
        private void ClearReceivedData()
        {
            ReceivedData = string.Empty;
        }


        private double[] _dataX;
        public double[] DataX
        {
            get => _dataX;
            set => SetProperty(ref _dataX, value);
        }

        private double[] _dataY;
        public double[] DataY
        {
            get => _dataY;
            set => SetProperty(ref _dataY, value);
        }



        #region Serial Port
        [ObservableProperty]
        public partial SerialPortSettings serialPortSettings { get; set; }
        public string ConnectButtonText => _serialPortService.IsOpen ? "Disconnect" : "Connect";
        public ObservableCollection<int> BaudRates { get; } = [300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200];
        public bool IsPortOpen
        {
            get => _serialPortService.IsOpen;
            set
            {
                if (_serialPortService.IsOpen != value)
                {
                    _serialPortService.IsOpen = value;
                    OnPropertyChanged(nameof(IsPortOpen));
                    OnPropertyChanged(nameof(ConnectButtonText));
                    UpdateConnectButtonState();
                    UpdateSendDataCanExecute();
                }
            }
        }
        private void OpenPort()
        {
            if (_serialPortService.OpenPort(SelectedPort, SelectedBaudRate, 8, StopBits.One, Parity.None))
            {
                IsPortOpen = true;
            }
            else
            {
                // Handle error
            }
        }
        private void ClosePort()
        {
            _serialPortService.ClosePort();
            IsPortOpen = false;
        }
        private string _selectedPort;
        public string SelectedPort
        {
            get => _selectedPort;
            set
            {
                if (_selectedPort != value)
                {
                    _selectedPort = value;
                    OnPropertyChanged(nameof(SelectedPort));
                    UpdateConnectButtonState();
                }
            }
        }
        private bool CanConnectOrDisconnect()
        {
            return !string.IsNullOrEmpty(SelectedPort);
        }
        private void TogglePortConnection()
        {
            if (IsPortOpen)
            {
                ClosePort();
            }
            else
            {
                OpenPort();
            }
            OnPropertyChanged(nameof(IsPortOpen));
            OnPropertyChanged(nameof(ConnectButtonText));
            UpdateConnectButtonState();
            UpdateSendDataCanExecute();
        }
        private void RefreshPorts()
        {
            AvailablePorts.Clear();
            var ports = _serialPortService.GetAvailablePorts();
            foreach (var port in ports)
            {
                AvailablePorts.Add(port);
            }
        }
        private void SendData()
        {
            byte[] data = Encoding.UTF8.GetBytes(DataToSend);
            _serialPortService.WriteData(data);
            _serialPortService.WriteData(Encoding.UTF8.GetBytes(Environment.NewLine));
        }

        private bool CanSendData()
        {
            return !string.IsNullOrEmpty(DataToSend) && _serialPortService.IsOpen;
        }
        private void UpdateSendDataCanExecute()
        {
            ((Command)SendDataCommand).ChangeCanExecute();
        }
        private void UpdateConnectButtonState()
        {
            ((Command)ConnectCommand).ChangeCanExecute();
        }
        private int _selectedBaudRate = 115200; // Default baud rate
        public int SelectedBaudRate
        {
            get => _selectedBaudRate;
            set
            {
                if (_selectedBaudRate != value)
                {
                    _selectedBaudRate = value;
                    serialPortSettings.BaudRate = _selectedBaudRate;
                    OnPropertyChanged(nameof(SelectedBaudRate));
                }
            }
        }

        #endregion




        public new event PropertyChangedEventHandler PropertyChanged;
        protected new void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
