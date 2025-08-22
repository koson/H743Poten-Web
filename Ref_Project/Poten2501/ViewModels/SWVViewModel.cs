using CommunityToolkit.Maui.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Poten2501.CustomControls;
using Poten2501.Models;
using Poten2501.Services;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO.Ports;
using System.Runtime.CompilerServices;
using System.Text;
using System.Windows.Input;
#if WINDOWS
using System.Media;
#endif

namespace Poten2501.ViewModels
{
    public partial class SWVViewModel : ObservableObject, INotifyPropertyChanged
    {
        #region 1. Properties: General

        private string _workingFolderPath;
        public string WorkingFolderPath
        {
            get => _workingFolderPath;
            set
            {
                if (_workingFolderPath != value)
                {
                    _workingFolderPath = value;
                    OnPropertyChanged(nameof(WorkingFolderPath));
                    SaveWorkingFolderPath();
                }
            }
        }
        private string _projectName;
        public string ProjectName
        {
            get => _projectName;
            set
            {
                if (_projectName != value)
                {
                    _projectName = value;
                    OnPropertyChanged(nameof(ProjectName));
                }
            }
        }

        private string _fileName;
        public string FileName
        {
            get => _fileName;
            set
            {
                if (_fileName != value)
                {
                    _fileName = value;
                    OnPropertyChanged(nameof(FileName));
                }
            }
        }
        private bool _keepPreviousLines = true;
        public bool KeepPreviousLines
        {
            get => _keepPreviousLines;
            set
            {
                if (_keepPreviousLines != value)
                {
                    _keepPreviousLines = value;
                    OnPropertyChanged(nameof(KeepPreviousLines));
                }
            }
        }
        #endregion

        #region 2. Properties: Measurement Parameters
        private double _frequency;
        public double Frequency
        {
            get => _frequency;
            set
            {
                if (_frequency != value)
                {
                    _frequency = value;
                    OnPropertyChanged(nameof(Frequency));
                }
            }
        }

        private double _amplitude;
        public double Amplitude
        {
            get => _amplitude;
            set
            {
                if (_amplitude != value)
                {
                    _amplitude = value;
                    OnPropertyChanged(nameof(Amplitude));
                }
            }
        }

        private double _stepPotential;
        public double StepPotential
        {
            get => _stepPotential;
            set
            {
                if (_stepPotential != value)
                {
                    _stepPotential = value;
                    OnPropertyChanged(nameof(StepPotential));
                }
            }
        }

        private double _startPotential;
        public double StartPotential
        {
            get => _startPotential;
            set
            {
                if (_startPotential != value)
                {
                    _startPotential = value;
                    OnPropertyChanged(nameof(StartPotential));
                }
            }
        }

        private double _endPotential;
        public double EndPotential
        {
            get => _endPotential;
            set
            {
                if (_endPotential != value)
                {
                    _endPotential = value;
                    OnPropertyChanged(nameof(EndPotential));
                }
            }
        }
        [ObservableProperty]
        public partial string SelectedPickerItem { get; set; }
        private int _scanCycle;
        public int ScanCycle
        {
            get => _scanCycle;
            set
            {
                if (_scanCycle != value)
                {
                    _scanCycle = value;
                    OnPropertyChanged(nameof(ScanCycle));
                }
            }
        }

        private string _electrodeNo = "E1"; // Selected electrode number
        public string ElectrodeNo
        {
            get => _electrodeNo;
            set
            {
                if (_electrodeNo != value)
                {
                    _electrodeNo = value;
                    OnPropertyChanged(nameof(ElectrodeNo));
                }
            }
        }

        public List<string> ElectrodeOptions { get; } = new List<string>
        {
            "E1", "E2", "E3", "E4", "E5"
        };
        private double _swvVoltage;
        public double SwvVoltage
        {
            get => _swvVoltage;
            set
            {
                if (_swvVoltage != value)
                {
                    _swvVoltage = value;
                    OnPropertyChanged(nameof(SwvVoltage));
                }
            }
        }
        private double _swvCurrent;
        public double SwvCurrent
        {
            get => _swvCurrent;
            set
            {
                if (_swvCurrent != value)
                {
                    _swvCurrent = value;
                    OnPropertyChanged(nameof(SwvCurrent));
                }
            }
        }

        public List<Tuple<double, double>> PotentialCurrentPairs { get; } = new();
        private string _frequencyPickerItem = "1";
        public string FrequencyPickerItem
        {
            get => _frequencyPickerItem;
            set
            {
                if (_frequencyPickerItem != value)
                {
                    _frequencyPickerItem = value;
                    OnPropertyChanged(nameof(FrequencyPickerItem));
                }
            }
        }
        private List<string> _pickerItems;
        public List<string> PickerItems
        {
            get => _pickerItems;
            set => SetProperty(ref _pickerItems, value);
        }
        partial void OnSelectedPickerItemChanged(string value)
        {
            if (double.TryParse(value, out double selectedFrequency))
            {
                Frequency = selectedFrequency; // Update the frequency property
                Debug.WriteLine($"Frequency updated to: {Frequency}");
            }
            else
            {
                Debug.WriteLine("Invalid frequency value selected.");
            }
        }

        #endregion

        #region 3. Properties: Plot Data
        public ObservableCollection<double> DataX { get; } = new();
        public ObservableCollection<double> DataY { get; } = new();
        public PlotView SWVPlot { get; }
        #endregion

        #region 4. Properties: Serial Port
        public ISerialPortService SerialPortService { get; }
        public ObservableCollection<string> AvailablePorts { get; } = new();
        public ObservableCollection<int> BaudRates { get; } = new() { 300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200 };

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
        [ObservableProperty]
        public partial SerialPortSettings serialPortSettings { get; set; }
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
                }
            }
        }

        private string _receivedData;
        public string ReceivedData
        {
            get => _receivedData;
            set
            {
                if (_receivedData != value)
                {
                    _receivedData = value;
                    OnPropertyChanged(nameof(ReceivedData));
                }
            }
        }
        public string ConnectButtonText => SerialPortService.IsOpen ? "Disconnect" : "Connect";

        #endregion

        #region 5. Commands
        public ICommand RefreshPortsCommand { get; }
        public ICommand ConnectCommand { get; }
        public ICommand SendDataCommand { get; }
        #endregion

        #region 6. Constructor
        public SWVViewModel(PlotView sWVPlot, ISerialPortService serialPortService)
        {
            SWVPlot = sWVPlot;
            SerialPortService = serialPortService;
            PickerItems = ["1", "2", "5", "10", "20"];
            SelectedPickerItem = PickerItems[3];
            //SerialPortService.DataReceived += OnDataReceived;

            // Initialize serial port commands
            RefreshPortsCommand = new RelayCommand(RefreshPorts);
            ConnectCommand = new RelayCommand(TogglePortConnection, CanConnectOrDisconnect);
            SendDataCommand = new RelayCommand(SendData, CanSendData);

            Amplitude = 0.03;
            StepPotential = 0.01;
            StartPotential = -0.4;
            EndPotential = 0.7;
            ScanCycle = 1;

            ProjectName = "Project1"; // Default project name
            LoadWorkingFolderPath();
            RefreshPorts();
        }
        #endregion

        #region 7. Methods: File Operations
        private void SaveWorkingFolderPath()
        {
            Preferences.Set(nameof(WorkingFolderPath), WorkingFolderPath);
        }
        private void LoadWorkingFolderPath()
        {
            WorkingFolderPath = Preferences.Get(nameof(WorkingFolderPath), string.Empty);
        }
        [RelayCommand]
        private async void SelectProjectFolder()
        {
            Debug.WriteLine("SelectProjectFolder().");
            try
            {
                var folderPickerResult = await FolderPicker.Default.PickAsync(cancellationToken: default);

                if (folderPickerResult != null && folderPickerResult.IsSuccessful && folderPickerResult.Folder != null)
                {
                    WorkingFolderPath = folderPickerResult.Folder.Path;
                    Debug.WriteLine($"Project path = {folderPickerResult.Folder.Path}");
                }
            }
            catch (Exception ex)
            {
                // Handle exceptions (e.g., user cancels the picker)
                Debug.WriteLine($"Error selecting folder: {ex.Message}");
            }
        }
        private void SaveCycleDataToFile(int cycle)
        {
            try
            {
                // Ensure WorkingFolderPath and ProjectName are valid
                if (string.IsNullOrEmpty(WorkingFolderPath) || string.IsNullOrEmpty(ProjectName))
                {
                    Debug.WriteLine("WorkingFolderPath or ProjectName is not set. Cannot save data.");
                    return;
                }

                // Define the file name and path
                string fileName = $"{ProjectName}_{ElectrodeNo}_{Frequency}Hz_Cycle_{cycle}_{DateTime.Now:yyyyMMdd_HHmmss}.csv";
                FileName = fileName; // Update the FileName property
                string filePath = Path.Combine(WorkingFolderPath, fileName);

                // Create the file and write the data
                using (var writer = new StreamWriter(filePath))
                {
                    writer.WriteLine("Potential,Current"); // Header
                    for (int i = 0; i < DataX.Count; i++)
                    {
                        writer.WriteLine($"{DataX[i]},{DataY[i]}");
                    }
                }

                Debug.WriteLine($"Cycle {cycle} data saved to {filePath}");
            }
            catch (Exception ex)
            {
                Debug.WriteLine($"Error saving cycle {cycle} data: {ex.Message}");
            }
        }
        #endregion

        #region 8. Methods: Serial Port
        private void RefreshPorts()
        {
            AvailablePorts.Clear();
            var ports = SerialPortService.GetAvailablePorts();
            foreach (var port in ports)
            {
                AvailablePorts.Add(port);
            }
        }
        private void TogglePortConnection()
        {
            if (SerialPortService.IsOpen)
            {
                ClosePort();
            }
            else
            {
                OpenPort();
            }
            OnPropertyChanged(nameof(ConnectButtonText));
        }
        private void OpenPort()
        {
            if (SerialPortService.OpenPort(SelectedPort, SelectedBaudRate, 8, StopBits.One, Parity.None))
            {
                Debug.WriteLine("Port opened successfully.");
            }
            else
            {
                Debug.WriteLine("Failed to open port.");
            }
        }
        private void ClosePort()
        {
            SerialPortService.ClosePort();
            Debug.WriteLine("Port closed.");
        }

        private void SendData()
        {
            if (!string.IsNullOrEmpty(DataToSend))
            {
                byte[] data = Encoding.UTF8.GetBytes(DataToSend);
                SerialPortService.WriteData(data);
                SerialPortService.WriteData(Encoding.UTF8.GetBytes(Environment.NewLine));
            }
        }
        private bool CanConnectOrDisconnect()
        {
            return !string.IsNullOrEmpty(SelectedPort);
        }

        private bool CanSendData()
        {
            return !string.IsNullOrEmpty(DataToSend) && SerialPortService.IsOpen;
        }
        private void UpdateConnectButtonState()
        {
            if (ConnectCommand is RelayCommand relayCommand)
            {
                relayCommand.NotifyCanExecuteChanged();
            }
        }
        private void OnDataReceived(object sender, byte[] data)
        {
            string receivedString = Encoding.UTF8.GetString(data);

            // Split the received string
            var parts = receivedString.Split(',');

            if (parts.Length == 7) // Ensure the data has exactly 7 parts
            {
                string potentialString = parts[3];
                string currentString = parts[6];

                if (double.TryParse(potentialString, out double potential) &&
                    double.TryParse(currentString, out double current))
                {
                    // Add the pair to the list
                    PotentialCurrentPairs.Add(new Tuple<double, double>(potential, current));
                    SwvVoltage = potential;
                    SwvCurrent = current;
                    // Update the plot
                    DataX.Add(potential);
                    DataY.Add(current);
                    SWVPlot.DataX = DataX.ToArray();
                    SWVPlot.DataY = DataY.ToArray();
                }
                else
                {
                    Debug.WriteLine("Invalid potential or current format.");
                }
            }
            else
            {
                Debug.WriteLine("Invalid data format.");
            }
        }

        #endregion

        #region 9. Methods: Plot Operations
        [RelayCommand]
        private void ClearChart()
        {
            Debug.WriteLine("ClearChart() invoked.");
            // Clear the data collections
            DataX.Clear();
            DataY.Clear();
            // Clear the plot data
            SWVPlot.DataX = Array.Empty<double>();
            SWVPlot.DataY = Array.Empty<double>();
            // Optionally clear additional data if needed
            SWVPlot.AdditionalDataX = null;
            SWVPlot.AdditionalDataY = null;
            Debug.WriteLine("Plot data cleared.");
        }

        #endregion

        #region 10. Methods: Scanning
        [RelayCommand]
        private async Task StartSWVScanAsync()
        {
            Debug.WriteLine($"StartSWVScan() initiated for {ScanCycle} cycles.");

            // Store previous lines if the user wants to keep them
            var previousDataX = new List<double[]>();
            var previousDataY = new List<double[]>();

            for (int cycle = 1; cycle <= ScanCycle; cycle++)
            {
                Debug.WriteLine($"Starting cycle {cycle} of {ScanCycle}.");

                // Save the current line if the user wants to keep previous lines
                if (KeepPreviousLines && DataX.Count > 0 && DataY.Count > 0)
                {
                    previousDataX.Add(DataX.ToArray());
                    previousDataY.Add(DataY.ToArray());
                }

                // Clear the data for a new line
                DataX.Clear();
                DataY.Clear();

                // Prepare the data to send for the current scan cycle
                string dataToSend = $"POTEn:SWV:Start {Frequency},{Amplitude},{StepPotential},{StartPotential},{EndPotential}";
                DataToSend = dataToSend;

                Debug.WriteLine($"Sending data: {dataToSend}");
                await Task.Run(() => SendData());

                // Wait for hardware to signal completion of the current scan
                await WaitForScanCompletionAsync();

                // Save the data from this cycle to a file
                SaveCycleDataToFile(cycle);

                // Update the plot with the new line and optionally include previous lines
                if (KeepPreviousLines)
                {
                    SWVPlot.AdditionalDataX = previousDataX.ToArray();
                    SWVPlot.AdditionalDataY = previousDataY.ToArray();
                }
                else
                {
                    SWVPlot.AdditionalDataX = null;
                    SWVPlot.AdditionalDataY = null;
                }
                Debug.WriteLine($"Cycle {cycle} completed.");
            }
            Debug.WriteLine("All scan cycles completed.");
            // Show popup dialog
            #if WINDOWS
                        System.Media.SystemSounds.Beep.Play();
            #endif
            await Shell.Current.DisplayAlert("Info", "All scan cycles completed.", "OK");
            // ...
        }
        private Task WaitForScanCompletionAsync()
        {
            var tcs = new TaskCompletionSource<bool>();

            // Assuming OnDataReceived signals the end of a scan
            void OnScanCompleted(object sender, byte[] data)
            {
                string receivedString = Encoding.UTF8.GetString(data);
                if (receivedString.Contains("SWV Operation Finished")) // Replace with actual completion signal
                {
                    SerialPortService.DataReceived -= OnScanCompleted;
                    tcs.SetResult(true);
                }
            }
            SerialPortService.DataReceived += OnScanCompleted;
            return tcs.Task;
        }
        [RelayCommand]
        private void AbortSWVScan()
        {
            // Logic to abort SWV scan
            Debug.WriteLine("AbortSWVScan().");
        }

        internal void SubscribeSerialPort()
        {
            SerialPortService.DataReceived += OnDataReceived;
        }

        internal void UnsubscribeSerialPort()
        {
            SerialPortService.DataReceived -= OnDataReceived;
        }
        #endregion
    }
}