using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using CommunityToolkit.Maui.Storage;
using Poten2501.CustomControls;
using Poten2501.Models;
using Poten2501.Services;
using ScottPlot;
using ScottPlot.Maui;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO.Ports;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;
using Windows.Media.Core;
using Windows.Storage;

namespace Poten2501.ViewModels
{
    public partial class CVViewModel : ObservableObject, INotifyPropertyChanged
    {
        #region Interfaces
        private readonly ISerialPortService _serialPortService;
        public ICommand RefreshPortsCommand { get; }
        public ICommand ConnectCommand { get; }
        public ICommand SendDataCommand { get; }
        public ICommand ClearReceivedDataCommand { get; }
        public ObservableCollection<double> Data { get; } = [];
        public ICommand AddDataPointCommand { get; }
        #endregion

        [ObservableProperty]
        private string electrodeNo = "E1"; // Selected electrode number

        public List<string> ElectrodeOptions { get; } = new List<string>
        {
            "E1", "E2", "E3", "E4", "E5"
        };

        [ObservableProperty]
        private int sweepRatemVPerSecond = 100; // Default value

        public List<int> SweepRateOptions { get; } = new List<int>
    {
        20, 50, 100, 200, 400
    };

        #region Serialport
        [ObservableProperty]
        public partial SerialPortSettings _serialPortSettings { get; set; }
        public ObservableCollection<string> AvailablePorts { get; } = [];

        private static readonly ObservableCollection<int> observableCollection = [300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200];
        public ObservableCollection<int> BaudRates { get; } = observableCollection;

        readonly List<CVData> cvData = [];

        [ObservableProperty]
        public partial Plot CVPlot { get; set; }

        [ObservableProperty]
        public partial PotenCVSettings CvSettings { get; set; } = new();

        [ObservableProperty]
        public partial string SelectedPickerItem { get; set; }
        private List<string> _pickerItems;
        public List<string> PickerItems
        {
            get => _pickerItems;
            set => SetProperty(ref _pickerItems, value);
        }

        #region working folder
        public string WorkingFolderPath
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(WorkingFolderPath));
                }
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
        #endregion

        [RelayCommand]
        private void UpdateNoOfCycle(string value)
        {
            string dataToSend = "POTEn:NUMCycles " + value;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void UpdateSweepRate(string mVps)
        {
            string dataToSend = "POTEn:RATE:SWEEp " + mVps;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void UpdatePointPerSec(string PPS)
        {
            string dataToSend = "POTEn:PPS " + PPS;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void UpdateCurrentRange(string CurrRange)
        {
            string dataToSend = "POTEn:CURRent:RANGe " + PickerItems.IndexOf(CurrRange).ToString();
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void UpdateUpperVoltage(string value)
        {
            string dataToSend = "POTEn:VOLTage:UPPEr " + value;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void UpdateBeginVoltage(string value)
        {
            string dataToSend = "POTEn:VOLTage:BEGIn " + value;
            DataToSend = dataToSend;
            SendData();
        }


        [RelayCommand]
        private void UpdateLowerVoltage(string value)
        {
            string dataToSend = "POTEn:VOLTage:LOWEr " + value;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void UpdateIdleVoltage(string value)
        {
            string dataToSend = "POTEn:VOLTage:IDLE " + value;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void UpdateIdleTime(string value)
        {
            string dataToSend = "POTEn:TIME:IDLE " + value;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void CalculateScanPattern(string value)
        {
            string dataToSend = "POTEn:CALCulate:SCANpattern " + value;
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private async Task StartCVScan()
        {
            IsEntryNumberOfCVCycleEnabled = false;
            IsEntrySweepRatemVPerSecondEnabled = true;  // temporary enabled
            IsEntryPointPerSecondEnabled = false;
            IsEntryCurrentRangeAmpareEnabled = false;
            IsEntryUpperPotentialVoltEnabled = false;
            IsEntryBeginPotentialVoltEnabled = false;
            IsEntryLowerPotentialVoltEnabled = false;
            IsEntryIdlePotentialVoltEnabled = false;
            IsEntryIdleTimeSecondEnabled = false;

            UpdateNoOfCycle(NumberOfCVCycle.ToString());
            await Task.Delay(50);

            UpdateSweepRate(SweepRatemVPerSecond.ToString());
            await Task.Delay(50);

            UpdatePointPerSec(PointPerSecond.ToString());
            await Task.Delay(50);

            UpdateCurrentRange(SelectedPickerItem);
            await Task.Delay(50);

            UpdateUpperVoltage(UpperPotentialVolt.ToString());
            await Task.Delay(50);

            UpdateLowerVoltage(LowerPotentialVolt.ToString());
            await Task.Delay(50);

            UpdateBeginVoltage(BeginPotentialVolt.ToString());
            await Task.Delay(50);

            UpdateIdleVoltage(IdlePotentialVolt.ToString());
            await Task.Delay(50);

            UpdateIdleTime(IdleTimeSecond.ToString());
            await Task.Delay(50);

            string dataToSend = "POTEn:CYCLic:Start";
            DataToSend = dataToSend;
            FileName = GenerateFileName();

            // Remove any extra dots in the file name
            string fileNameWithoutExtension = Path.GetFileNameWithoutExtension(FileName);
            string extension = Path.GetExtension(FileName);
            string modifiedFileName = fileNameWithoutExtension.Replace('.', '_') + extension;
            FileName = modifiedFileName;

            WriteOutputFileHeader();
            Debug.WriteLine($"FileName = {FileName}");
            SendData();
        }

        private void WriteOutputFileHeader()
        {
            string header = "Mode,TimeStamp(us),REVoltage,WEVoltage,WECurrentRange,CycleNo,DAC_CH1,DAC_CH2,counter,LUTData";
            string filePath = Path.Combine(WorkingFolderPath, FileName);
            File.WriteAllText(filePath, header + Environment.NewLine);
        }

        [RelayCommand]
        private void AbortCVScan()
        {
            IsEntryNumberOfCVCycleEnabled = true;
            IsEntryCurrentRangeAmpareEnabled = true;
            IsEntryIdlePotentialVoltEnabled = true;
            IsEntryIdleTimeSecondEnabled = true;
            IsEntryPointPerSecondEnabled = true;
            IsEntrySweepRatemVPerSecondEnabled = true;
            IsEntryUpperPotentialVoltEnabled = true;
            IsEntryLowerPotentialVoltEnabled = true;
            IsEntryBeginPotentialVoltEnabled = true;
            string dataToSend = "POTEn:ABORt";
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private void ClearChart()
        {
            PlotVIXS.Clear();
            PlotVIYS.Clear();
            DataX = [.. PlotVIXS];
            DataY = [.. PlotVIYS];
        }
        #endregion

        #region Controls
        public string ConnectButtonText => _serialPortService.IsOpen ? "Disconnect" : "Connect";
        public string ButtonPortOpenText { get; set; } = "Connect";
        public bool IsOpenPortEnabled { get; set; } = true;
        public string ButtonPortCloseText { get; set; } = "Disconnect";
        public bool IsClosePortEnabled { get; set; } = false;
        #endregion

        private void ConfigureZoomLimits()
        {
            if (CVPlot != null)
            {
                CVPlot.Axes.SetLimitsY(-2e-6, 2e-6); // Set X-axis zoom limits
            }
        }
        public CVViewModel(ISerialPortService serialPortService)
        {
            // Serial port setting
            _serialPortService = serialPortService;
            //_serialPortService.DataReceived += OnDataReceived;
            RefreshPortsCommand = new Command(RefreshPorts);
            ConnectCommand = new Command(TogglePortConnection, CanConnectOrDisconnect);
            SendDataCommand = new Command(SendData, CanSendData);
            ClearReceivedDataCommand = new Command(ClearReceivedData);
            SerialPortSettings1 = new SerialPortSettings
            {
                BaudRate = 115200
            };
            PickerItems = ["1. (1mA/V)", "2. (100uA/V)", "3. (10uA/V)", "4. (1uA/V)"];
            SelectedPickerItem = PickerItems.FirstOrDefault();
            RefreshPorts();
            CvSettings.MinVoltage = 0.0;
            CvSettings.MaxVoltage = 0.0;
            CvSettings.NoOfCycles = 3;

            CVPlot = new Plot();
            ConfigureZoomLimits();
            PlotVIXS = [];
            PlotVIYS = [];

            IsEntryNumberOfCVCycleEnabled = true;
            IsEntryCurrentRangeAmpareEnabled = true;
            IsEntryIdlePotentialVoltEnabled = true;
            IsEntryIdleTimeSecondEnabled = true;
            IsEntryPointPerSecondEnabled = true;
            IsEntrySweepRatemVPerSecondEnabled = true;
            IsEntryUpperPotentialVoltEnabled = true;
            IsEntryLowerPotentialVoltEnabled = true;
            IsEntryBeginPotentialVoltEnabled = true;

            WorkingFolderPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments));
        }






        private double _pointSize;
        public double PointSize
        {
            get => _pointSize;
            set
            {
                if (_pointSize != value)
                {
                    _pointSize = value;
                    OnPropertyChanged(nameof(PointSize));
                }
            }
        }

        #region Serial port methods
        public string SelectedPort
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(SelectedPort));
                    UpdateConnectButtonState();
                }
            }
        }

        public int SelectedBaudRate
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    _serialPortSettings.BaudRate = field;
                    OnPropertyChanged(nameof(SelectedBaudRate));
                }
            }
        } = 115200;

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

        public string DataToSend
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(DataToSend));
                    UpdateSendDataCanExecute();
                }
            }
        }
        private void UpdateSendDataCanExecute()
        {
            ((Command)SendDataCommand).ChangeCanExecute();
        }
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

        private void ClearReceivedData()
        {
            ReceivedData = string.Empty;
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

        private bool CanConnectOrDisconnect()
        {
            return !string.IsNullOrEmpty(SelectedPort);
        }

        private void UpdateConnectButtonState()
        {
            ((Command)ConnectCommand).ChangeCanExecute();
        }
        private void SendData()
        {
            Debug.WriteLine($"Sending data: {DataToSend}");
            byte[] data = Encoding.UTF8.GetBytes(DataToSend);
            _serialPortService.WriteData(data);
            _serialPortService.WriteData(Encoding.UTF8.GetBytes(Environment.NewLine));
        }

        private bool CanSendData()
        {
            return !string.IsNullOrEmpty(DataToSend) && _serialPortService.IsOpen;
        }

        private readonly List<double> PlotVIXS = [];
        private readonly List<double> PlotVIYS = [];

        private readonly Stopwatch _updateStopwatch = new Stopwatch();
        private double _currentRange;
        public double CurrentRange
        {
            get => _currentRange;
            set
            {
                if (_currentRange != value)
                {
                    _currentRange = value;
                    OnPropertyChanged(nameof(CurrentRange));
                }
            }
        }

        private void OnDataReceived(object sender, byte[] data)
        {
            string receivedString = Encoding.UTF8.GetString(data);
            ReceivedData = receivedString;

            // Append received data to a text file
            if (FileName == null)
            {
                FileName = GenerateFileName();
                Debug.WriteLine($"FileName = {FileName}");
            }
            // Ensure FileName has .csv extension
            if (!FileName.EndsWith(".csv"))
            {
                FileName += ".csv";
            }
            string filePath = Path.Combine(WorkingFolderPath, FileName);
            File.AppendAllText(filePath, receivedString);

            string[] words = receivedString.Split(',');

            if (receivedString.StartsWith("CV") &&
                double.TryParse(words[1], out double _time) &&
                double.TryParse(words[2], out double _reVoltage) &&
                double.TryParse(words[3], out double _weVoltage) &&
                int.TryParse(words[4], out int _currentRange) &&
                int.TryParse(words[5], out int _cycleNo) &&
                int.TryParse(words[8], out int _counter))
            {
                //// Skip the first point if _reVoltage is far from BeginPotentialVolt
                //const double threshold = 0.1; // Define a threshold for acceptable deviation
                //if (Math.Abs(_reVoltage - BeginPotentialVolt) > threshold && PlotVIXS.Count == 0 && PlotVIYS.Count == 0)
                //{
                //    return;
                //}

                cvData.Add(new CVData
                {
                    Index = 0,
                    REVoltage = _reVoltage,
                    TimeStamp = _time,
                    WEVoltage = _weVoltage,
                    WECurrentRange = _currentRange,
                    CycleNo = _cycleNo

                });

                CycleCount = _cycleNo;
                CurrentRange = _currentRange;
                // Throttle updates to 5 times per second
                if (!_updateStopwatch.IsRunning || _updateStopwatch.ElapsedMilliseconds >= 50)
                {
                    _updateStopwatch.Restart();
                    if (_counter >= 5)
                    {
                        if (CVPlot != null)
                        {
                            CvVoltage = _reVoltage;
                            CvCurrent = _weVoltage;
                            PlotVIXS.Add(_reVoltage);
                            PlotVIYS.Add(_weVoltage);
                            DataX = [.. PlotVIXS];
                            DataY = [.. PlotVIYS];
                        }
                    }
                }
            }
            else
            {
                // Handle parsing error
            }
        }

        public double[] DataX
        {
            get;
            set
            {
                field = value;
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(DataX)));
            }
        }

        public double[] DataY
        {
            get;
            set
            {
                field = value;
                PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(nameof(DataY)));
            }
        }

        public SerialPortSettings SerialPortSettings1 { get => _serialPortSettings; set => _serialPortSettings = value; }
        #endregion

        #region properties




        public int CycleCount
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(CycleCount));
                }
            }
        }


        public int NumberOfCVCycle
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(NumberOfCVCycle));
                }
            }
        }
        //public double SweepRatemVPerSecond
        //{
        //    get;
        //    set
        //    {
        //        if (field != value)
        //        {
        //            field = value;
        //            OnPropertyChanged(nameof(SweepRatemVPerSecond));
        //        }
        //    }
        //}
        public double PointPerSecond
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(PointPerSecond));
                }
            }
        }
        public double CurrentRangeAmpare
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(CurrentRangeAmpare));
                }
            }
        }

        public double BeginPotentialVolt
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(BeginPotentialVolt));
                }
            }
        }
        public double LowerPotentialVolt
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(LowerPotentialVolt));
                }
            }
        }
        public double UpperPotentialVolt
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(UpperPotentialVolt));
                }
            }
        }
        public double IdlePotentialVolt
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IdlePotentialVolt));
                }
            }
        }
        public double IdleTimeSecond
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IdleTimeSecond));
                }
            }
        }
        public bool IsEntryNumberOfCVCycleEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryNumberOfCVCycleEnabled));
                }
            }
        }

        public bool IsEntrySweepRatemVPerSecondEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntrySweepRatemVPerSecondEnabled));
                }
            }
        }

        public bool IsEntryPointPerSecondEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryPointPerSecondEnabled));
                }
            }
        }

        public bool IsEntryCurrentRangeAmpareEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryCurrentRangeAmpareEnabled));
                }
            }
        }

        public bool IsEntryBeginPotentialVoltEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryBeginPotentialVoltEnabled));
                }
            }
        }

        public bool IsEntryLowerPotentialVoltEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryLowerPotentialVoltEnabled));
                }
            }
        }

        public bool IsEntryUpperPotentialVoltEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryUpperPotentialVoltEnabled));
                }
            }
        }

        public bool IsEntryIdlePotentialVoltEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryIdlePotentialVoltEnabled));
                }
            }
        }

        public bool IsEntryIdleTimeSecondEnabled
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(IsEntryIdleTimeSecondEnabled));
                }
            }
        }
        public double CvVoltage
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(CvVoltage));
                }
            }
        }

        public double CvCurrent
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(CvCurrent));
                }
            }
        }


        public new event PropertyChangedEventHandler PropertyChanged;
        protected new virtual void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
        private string GenerateFileName()
        {
            string fileName = $"{ProjectName}_{SweepRatemVPerSecond}mVpS_{ElectrodeNo}_{DateTime.Now:yyMMddHHmm}.csv";
            // Limit the length of the file name to 32 characters including the extension
            if (fileName.Length > 48)
            {
                int maxLength = 44; // 32 - 4 (".csv")
                string shortProjectName = ProjectName.Length > maxLength ? ProjectName.Substring(0, maxLength) : ProjectName;
                fileName = $"{shortProjectName}_{DateTime.Now:yyMMddHHmm}.csv";
            }
            return fileName;
        }

        internal void SubscribeSerialPort()
        {
            _serialPortService.DataReceived += OnDataReceived;
        }

        internal void UnsubscribeSerialPort()
        {
            _serialPortService.DataReceived -= OnDataReceived;
        }
        #endregion

    }
}
