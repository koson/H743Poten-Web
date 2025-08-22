using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.IO.Ports;
using System.Runtime.CompilerServices;
using System.Text;
using System.Windows.Input;
using System.Windows.Markup;
using CommunityToolkit.Maui.Storage;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using OpenTK.Graphics.OpenGL;
using Poten2501.CustomControls;
using Poten2501.Models;
using Poten2501.Services;
using ScottPlot;
using ScottPlot.Maui;

namespace Poten2501.ViewModels
{
    public partial class DPVPageViewModel : ObservableObject, INotifyPropertyChanged
    {
        private MauiPlot mauiPlot;
        private PlotView _plotView;
        public DPVPageViewModel(PlotView plotView, ISerialPortService serialPortService)
        {
            _plotView = plotView;
            mauiPlot = _plotView.Plot;
            _serialPortService = serialPortService;
            _serialPortService.DataReceived += OnDataReceived;
            RefreshPortsCommand = new Command(RefreshPorts);
            ConnectCommand = new Command(TogglePortConnection, CanConnectOrDisconnect);
            SendDataCommand = new Command(SendData, CanSendData);
            ClearReceivedDataCommand = new Command(ClearReceivedData);
            potenDPVSettings = new PotenDPVSettings();
            PickerItems = ["1. (1mA/V)", "2. (100uA/V)", "3. (10uA/V)", "4. (1uA/V)"];
            SelectedPickerItem = PickerItems.FirstOrDefault();

            potenDPVSettings.NoOfSegments = 1;
            potenDPVSettings.InitialDirection = "UP";
            potenDPVSettings.InitialPotentialVolt = 0.0;
            potenDPVSettings.FinalPotentialVolt = 0.0;
            potenDPVSettings.LowerPotentialVolt = 0.0;
            potenDPVSettings.UpperPotentialVolt = 0.0;
            potenDPVSettings.DifferentialPulseHeight = 0.0;
            potenDPVSettings.DifferentialPulseWidth = 0.0;
            potenDPVSettings.DifferentialPulsePeriod = 0.0;
            potenDPVSettings.DifferentialPulseIncrement = 0.0;
            potenDPVSettings.DifferentialPulsePrePulseWidth = 0.0;
            potenDPVSettings.DifferentialPulsePostPulseWidth = 0.0;

            mauiPlot.Plot.Axes.SetLimitsY(-0.1, 0.1);

 
 

            RefreshPorts();
        }

        #region Interfaces
        private readonly ISerialPortService _serialPortService;
        public ICommand RefreshPortsCommand { get; }
        public ICommand ConnectCommand { get; }
        public ICommand SendDataCommand { get; }
        public ICommand ClearReceivedDataCommand { get; }
        #endregion

        #region Serialport
        [ObservableProperty]
        public partial SerialPortSettings serialPortSettings { get; set; }

        public ObservableCollection<string> AvailablePorts { get; } = [];
        public ObservableCollection<int> BaudRates { get; } = [300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200];
        #endregion

        #region Controls
        //public string ConnectButtonText => IsPortOpen ? "Disconnect" : "Connect";
        public string ConnectButtonText => _serialPortService.IsOpen ? "Disconnect" : "Connect";
        public string ButtonPortOpenText { get; set; } = "Connect";
        public bool IsOpenPortEnabled { get; set; } = true;
        public string ButtonPortCloseText { get; set; } = "Disconnect";
        public bool IsClosePortEnabled { get; set; } = false;
        #endregion

        #region ObservableProperty
        [ObservableProperty]
        public partial string NoOfSegments { get; set; }

        [ObservableProperty]
        public partial string InitialDirection { get; set; }

        [ObservableProperty]
        public partial string InitialPotentialVolt { get; set; }
        [ObservableProperty]
        public partial string FinalPotentialVolt { get; set; }
        [ObservableProperty]
        public partial string LowerPotentialVolt { get; set; }
        [ObservableProperty]
        public partial string UpperPotentialVolt { get; set; }
        [ObservableProperty]
        public partial string DifferentialPulseHeight { get; set; }

        [ObservableProperty]
        public partial string DifferentialPulseWidth { get; set; }

        [ObservableProperty]
        public partial string DifferentialPulsePeriod { get; set; }

        [ObservableProperty]
        public partial string DifferentialPulseIncrement { get; set; }

        [ObservableProperty]
        public partial string DifferentialPulsePrePulseWidth { get; set; }

        [ObservableProperty]
        public partial string DifferentialPulsePostPulseWidth { get; set; }

        [ObservableProperty]
        public partial string SelectedPickerItem { get; set; }
        #endregion ObservableProperty

        #region Entry Commands

        private List<string> _pickerItems;
        public List<string> PickerItems
        {
            get => _pickerItems;
            set => SetProperty(ref _pickerItems, value);
        }

        partial void OnNoOfSegmentsChanged(string oldValue, string newValue)
        {
            var result = int.TryParse(newValue, out int number);
            if (result)
            {
                if (number > 0)
                {
                    potenDPVSettings.NoOfSegments = number;
                    NoOfSegments = newValue;
                }
                else
                {
                    NoOfSegments = oldValue;
                }
            }
            else
            {
                NoOfSegments = oldValue;
            }
        }


        private bool isEntryNoOfSegmentsEnabled;
        public bool IsEntryNoOfSegmentsEnabled
        {
            get => isEntryNoOfSegmentsEnabled;
            set
            {
                if (isEntryNoOfSegmentsEnabled != value)
                {
                    isEntryNoOfSegmentsEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool isEntryInitialPotentialVoltEnabled;
        public bool IsEntryInitialPotentialVoltEnabled
        {
            get => isEntryInitialPotentialVoltEnabled;
            set
            {
                if (isEntryInitialPotentialVoltEnabled != value)
                {
                    isEntryInitialPotentialVoltEnabled = value;
                    OnPropertyChanged();
                }
            }
        }


        private bool isEntryFinalPotentialVoltEnabled;
        public bool IsEntryFinalPotentialVoltEnabled
        {
            get => isEntryFinalPotentialVoltEnabled;
            set
            {
                if (isEntryFinalPotentialVoltEnabled != value)
                {
                    isEntryFinalPotentialVoltEnabled = value;
                    OnPropertyChanged();
                }
            }
        }



        private bool isEntryLowerPotentialVoltEnabled;
        public bool IsEntryLowerPotentialVoltEnabled
        {
            get => isEntryLowerPotentialVoltEnabled;
            set
            {
                if (isEntryLowerPotentialVoltEnabled != value)
                {
                    isEntryLowerPotentialVoltEnabled = value;
                    OnPropertyChanged();
                }
            }

        }



        private bool isEntryUpperPotentialVoltEnabled;
        public bool IsEntryUpperPotentialVoltEnabled
        {
            get => isEntryUpperPotentialVoltEnabled;
            set
            {
                if (isEntryUpperPotentialVoltEnabled != value)
                {
                    isEntryUpperPotentialVoltEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool isEntryDifferentialPulseHeightEnabled;
        public bool IsEntryDifferentialPulseHeightEnabled
        {
            get => isEntryDifferentialPulseHeightEnabled;
            set
            {
                if (isEntryDifferentialPulseHeightEnabled != value)
                {
                    isEntryDifferentialPulseHeightEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool isEntryDifferentialPulseWidthEnabled;
        public bool IsEntryDifferentialPulseWidthEnabled
        {
            get => isEntryDifferentialPulseWidthEnabled;
            set
            {
                if (isEntryDifferentialPulseWidthEnabled != value)
                {
                    isEntryDifferentialPulseWidthEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool isEntryDifferentialPulsePeriodEnabled;
        public bool IsEntryDifferentialPulsePeriodEnabled
        {
            get => isEntryDifferentialPulsePeriodEnabled;
            set
            {
                if (isEntryDifferentialPulsePeriodEnabled != value)
                {
                    isEntryDifferentialPulsePeriodEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool isEntryDifferentialPulseIncrementEnabled;
        public bool IsEntryDifferentialPulseIncrementEnabled
        {
            get => isEntryDifferentialPulseIncrementEnabled;
            set
            {
                if (isEntryDifferentialPulseIncrementEnabled != value)
                {
                    isEntryDifferentialPulseIncrementEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool isEntryDifferentialPulsePrePulseWidthEnabled;
        public bool IsEntryDifferentialPulsePrePulseWidthEnabled
        {
            get => isEntryDifferentialPulsePrePulseWidthEnabled;
            set
            {
                if (isEntryDifferentialPulsePrePulseWidthEnabled != value)
                {
                    isEntryDifferentialPulsePrePulseWidthEnabled = value;
                    OnPropertyChanged();
                }
            }
        }

        private bool isEntryDifferentialPulsePostPulseWidthEnabled;
        public bool IsEntryDifferentialPulsePostPulseWidthEnabled
        {
            get => isEntryDifferentialPulsePostPulseWidthEnabled;
            set
            {
                if (isEntryDifferentialPulsePostPulseWidthEnabled != value)
                {
                    isEntryDifferentialPulsePostPulseWidthEnabled = value;
                    OnPropertyChanged();
                }
            }
        }
        partial void OnInitialDirectionChanged(string oldValue, string newValue)
        {
            if (newValue == "UP" || newValue == "DOWN")
            {
                potenDPVSettings.InitialDirection = newValue;
                InitialDirection = newValue;
            }
            else
            {
                InitialDirection = oldValue;
            }
        }
        partial void OnInitialPotentialVoltChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                InitialPotentialVolt = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.InitialPotentialVolt = number;
                InitialPotentialVolt = newValue;
            }
            else
            {
                InitialPotentialVolt = oldValue;
            }
        }
        partial void OnFinalPotentialVoltChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                FinalPotentialVolt = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.FinalPotentialVolt = number;
                FinalPotentialVolt = newValue;
            }
            else
            {
                FinalPotentialVolt = oldValue;
            }
        }
        partial void OnLowerPotentialVoltChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                LowerPotentialVolt = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.LowerPotentialVolt = number;
                LowerPotentialVolt = newValue;
            }
            else
            {
                LowerPotentialVolt = oldValue;
            }
        }
        partial void OnUpperPotentialVoltChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                UpperPotentialVolt = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.UpperPotentialVolt = number;
                UpperPotentialVolt = newValue;
            }
            else
            {
                UpperPotentialVolt = oldValue;
            }
        }
        partial void OnDifferentialPulseHeightChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                DifferentialPulseHeight = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.DifferentialPulseHeight = number;
                DifferentialPulseHeight = newValue;
            }
            else
            {
                DifferentialPulseHeight = oldValue;
            }
        }
        partial void OnDifferentialPulseWidthChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                DifferentialPulseWidth = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.DifferentialPulseWidth = number;
                DifferentialPulseWidth = newValue;
            }
            else
            {
                DifferentialPulseWidth = oldValue;
            }
        }
        partial void OnDifferentialPulsePeriodChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                DifferentialPulsePeriod = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.DifferentialPulsePeriod = number;
                DifferentialPulsePeriod = newValue;
            }
            else
            {
                DifferentialPulsePeriod = oldValue;
            }


        }
        partial void OnDifferentialPulseIncrementChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                DifferentialPulseIncrement = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.DifferentialPulseIncrement = number;
                DifferentialPulseIncrement = newValue;
            }
            else
            {
                DifferentialPulseIncrement = oldValue;
            }

        }
        partial void OnDifferentialPulsePrePulseWidthChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                DifferentialPulsePrePulseWidth = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.DifferentialPulsePrePulseWidth = number;
                DifferentialPulsePrePulseWidth = newValue;
            }
            else
            {
                DifferentialPulsePrePulseWidth = oldValue;
            }
        }


        partial void OnDifferentialPulsePostPulseWidthChanged(string oldValue, string newValue)
        {
            if (newValue == "-" || newValue == "." || newValue == "-.")
            {
                DifferentialPulsePostPulseWidth = newValue;
                return;
            }

            var result = double.TryParse(newValue, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number);
            if (result)
            {
                potenDPVSettings.DifferentialPulsePostPulseWidth = number;
                DifferentialPulsePostPulseWidth = newValue;
            }
            else
            {
                DifferentialPulsePostPulseWidth = oldValue;
            }
        }


        partial void OnSelectedPickerItemChanged(string oldValue, string newValue)
        {
            // Handle the logic when the selected picker item changes
        }
        #endregion Entry Commands

        #region Serialport Commands

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
            byte[] data = Encoding.UTF8.GetBytes(DataToSend);
            _serialPortService.WriteData(data);
            _serialPortService.WriteData(Encoding.UTF8.GetBytes(Environment.NewLine));
        }

        private bool CanSendData()
        {
            return !string.IsNullOrEmpty(DataToSend) && _serialPortService.IsOpen;
        }

        List<Tuple<double, double>> DPVwaveform = new List<Tuple<double, double>>();
        List<Tuple<double, double>> DPVCurrentBefore = new List<Tuple<double, double>>();
        List<Tuple<double, double>> DPVCurrentAfter = new List<Tuple<double, double>>();
        private void OnDataReceived(object sender, byte[] data)
        {
            const bool includeSourceCurrent = false;
            string receivedString = Encoding.UTF8.GetString(data);
            ReceivedData = receivedString;
            string[] words = receivedString.Split(',');
            if (receivedString.StartsWith("DPV"))
            {
                if (double.TryParse(words[1], out double _time) && 
                    double.TryParse(words[2], out double _rampPotential) && 
                    double.TryParse(words[3], out double _currentAfter) && 
                    double.TryParse(words[4], out double _currentBefore))
                {
                    DPVCurrentAfter.Add(new Tuple<double, double>(_rampPotential, _currentAfter ));
                    DPVCurrentBefore.Add(new Tuple<double, double>(_rampPotential, _currentBefore));
                    DPVwaveform.Add(new Tuple<double, double>(_rampPotential, (_currentAfter - _currentBefore)));
                    var dpvCurrentAfterX = DPVCurrentAfter.Select(d => d.Item1).ToArray();
                    var dpvCurrentAfterY = DPVCurrentAfter.Select(d => d.Item2).ToArray();
                    var dpvCurrentBeforeX = DPVCurrentBefore.Select(d => d.Item1).ToArray();
                    var dpvCurrentBeforeY = DPVCurrentBefore.Select(d => d.Item2).ToArray();
                    var dpvWaveformX = DPVwaveform.Select(d => d.Item1).ToArray();
                    var dpvWaveformY = DPVwaveform.Select(d => d.Item2).ToArray();
                    if(includeSourceCurrent == true)
                    {
                        _plotView.AdditionalDataX = new[] { dpvWaveformX, dpvCurrentAfterX, dpvCurrentBeforeX };
                        _plotView.AdditionalDataY = new[] { dpvWaveformY, dpvCurrentAfterY, dpvCurrentBeforeY };
                    }
                    else
                    {
                        _plotView.AdditionalDataX = new[] { dpvWaveformX };
                        _plotView.AdditionalDataY = new[] { dpvWaveformY };
                    }
                    //_plotView.AdditionalDataX = new[] { dpvWaveformX, dpvCurrentAfterX, dpvCurrentBeforeX };
                    //_plotView.AdditionalDataY = new[] { dpvWaveformY, dpvCurrentAfterY, dpvCurrentBeforeY };
                    //_plotView.AdditionalDataX = new[] { dpvWaveformX };
                    //_plotView.AdditionalDataY = new[] { dpvWaveformY };
                    //mauiPlot.Plot.Axes.SetLimitsY(0, 2.5);

                    DpvVoltage = _rampPotential;
                    DpvCurrent = _currentAfter - _currentBefore;
                }
            }
            else
            {
                // Handle parsing error
            }
        }
        #endregion Serialport Commands

        #region DPV 
        private readonly List<double> PlotVIXS = [];
        private readonly List<double> PlotVIYS = [];

        private readonly PotenDPVSettings potenDPVSettings;
        DPVParameters parameters;

        public double DpvVoltage
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(DpvVoltage));
                }
            }
        }

        public double DpvCurrent
        {
            get;
            set
            {
                if (field != value)
                {
                    field = value;
                    OnPropertyChanged(nameof(DpvCurrent));
                }
            }
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
        public struct DPVParameters
        {
            public double InitialPotential;
            public double FinalPotential;
            public double ScanRate; // Volts per second
            public double PulseAmplitude;
            public double PulseWidth; // Seconds
            public double PulsePeriod; // Seconds
        }

        public List<Tuple<double, double>> GenerateDPVWaveform(DPVParameters parameters)
        {
            List<Tuple<double, double>> waveform = new List<Tuple<double, double>>();
            double currentPotential = parameters.InitialPotential;
            double time = 0.0;
            double scanTime = Math.Abs(parameters.FinalPotential - parameters.InitialPotential) / parameters.ScanRate;
            int numSteps = (int)(scanTime / parameters.PulsePeriod); // Approximate number of pulses

            for (int i = 0; i < numSteps; ++i)
            {
                // Ramp to the potential before the pulse
                double rampPotential = parameters.InitialPotential + i * parameters.PulsePeriod * parameters.ScanRate;
                SetPotential(time, rampPotential); // Set the potential on your hardware
                time += parameters.PulsePeriod * 1000 * 0.5;
                SetPotential(time, rampPotential);
                // Pulse
                SetPotential(time, rampPotential + parameters.PulseAmplitude); // Apply pulse
                time += parameters.PulseWidth * 1000;
                double currentAfterPulse = ReadCurrent(); // Read current
                SetPotential(time, rampPotential + parameters.PulseAmplitude);
                SetPotential(time, parameters.InitialPotential + (i + 1) * parameters.PulsePeriod * parameters.ScanRate); // Return to the potential before the pulse
                time += parameters.PulsePeriod * 1000 * 0.5 - parameters.PulseWidth * 1000;
                double currentBeforePulse = ReadCurrent(); // Read current just before the pulse
                SetPotential(time, parameters.InitialPotential + (i + 1) * parameters.PulsePeriod * parameters.ScanRate);
                // Store the data point
                waveform.Add(new Tuple<double, double>(rampPotential, currentAfterPulse - currentBeforePulse));
            }
            return waveform;
        }
        private List<Tuple<double, double>> DPVSignal = new List<Tuple<double, double>>();

        void SetPotential(double time, double rampPotential)
        {
            // Add the time and rampPotential to the DPVSignal list
            DPVSignal.Add(new Tuple<double, double>(time, rampPotential));

            // Replace with your hardware-specific code to set the potential.
            // writer.WriteLine($"{time}, {rampPotential}");
        }

        double ReadCurrent()
        {
            // Replace with your hardware-specific code to read the current.
            // Return the measured current.
            return 0.0; // Example placeholder - replace with actual reading.
        }

        private void EnableDPVEntryFields(bool enable)
        {
            IsEntryNoOfSegmentsEnabled = enable;
            IsEntryInitialPotentialVoltEnabled = enable;
            IsEntryFinalPotentialVoltEnabled = enable;
            IsEntryLowerPotentialVoltEnabled = enable;
            IsEntryUpperPotentialVoltEnabled = enable;
            IsEntryDifferentialPulseHeightEnabled = enable;
            IsEntryDifferentialPulseWidthEnabled = enable;
            IsEntryDifferentialPulsePeriodEnabled = enable;
            IsEntryDifferentialPulseIncrementEnabled = enable;
            IsEntryDifferentialPulsePrePulseWidthEnabled = enable;
            IsEntryDifferentialPulsePostPulseWidthEnabled = enable;
        }

        [RelayCommand]
        private async Task StartDPVScan()
        {
            EnableDPVEntryFields(false);

            _ = UpdateNoOfSegmentsAsync();
            await Task.Delay(50);
            _ = UpdateInitialPotentialVoltAsync();
            await Task.Delay(50);
            _ = UpdateFinalPotentialVoltAsync();
            await Task.Delay(50);
            _ = UpdateLowerPotentialVoltAsync();
            await Task.Delay(50);
            _ = UpdateUpperPotentialVoltAsync();
            await Task.Delay(50);
            _ = UpdateDifferentialPulseHeightAsync();
            await Task.Delay(50);
            _ = UpdateDifferentialPulseWidthAsync();
            await Task.Delay(50);
            _ = UpdateDifferentialPulsePeriodAsync();
            await Task.Delay(50);
            _ = UpdateDifferentialPulseIncrementAsync();
            await Task.Delay(50);
            _ = UpdateDifferentialPulsePrePulseWidthAsync();
            await Task.Delay(50);
            _ = UpdateDifferentialPulsePostPulseWidthAsync();
            await Task.Delay(50);

            //TODO: add code call UpdateCurrentRange()  to the hardware, use entCurrentGain picker item
            UpdateCurrentRange(SelectedPickerItem);
            await Task.Delay(50);

            DPVwaveform.Clear();
            DPVCurrentAfter.Clear();
            DPVCurrentBefore.Clear();
            DPVwaveform.Clear();
            _plotView.Clear();

            string dataToSend = "POTEn:DPV:Start";
            DataToSend = dataToSend;
            await Task.Run(() => SendData());
            await Task.Delay(50);
        }


        [RelayCommand]
        private async Task AbortDPVScan()
        {
            EnableDPVEntryFields(true);

            string dataToSend = "POTEn:DPV:Abort";
            DataToSend = dataToSend;
            await Task.Run(() => SendData());
        }

        [RelayCommand]
        private async Task GenerateDPVSignal()
        {
            parameters.InitialPotential = potenDPVSettings.InitialPotentialVolt;
            parameters.FinalPotential = potenDPVSettings.FinalPotentialVolt;
            parameters.ScanRate = 0.05;
            parameters.PulseAmplitude = potenDPVSettings.DifferentialPulseHeight;
            parameters.PulseWidth = potenDPVSettings.DifferentialPulseWidth;
            parameters.PulsePeriod = potenDPVSettings.DifferentialPulsePeriod;

            // Clear DPVSignal before generating new data
            DPVSignal.Clear();
            List<Tuple<double, double>> dpvData = await Task.Run(() => GenerateDPVWaveform(parameters));

            // Extract X and Y data from dpvData
            var dpvDataX = dpvData.Select(d => d.Item1).ToArray();
            var dpvDataY = dpvData.Select(d => d.Item2).ToArray();

            // Extract X and Y data from DPVSignal
            var dpvSignalX = DPVSignal.Select(d => d.Item1).ToArray();
            var dpvSignalY = DPVSignal.Select(d => d.Item2).ToArray();

            //_plotView.DataX = dpvDataX;
            //_plotView.DataY = dpvDataY;

            _plotView.AdditionalDataX = new[] { dpvSignalX };
            _plotView.AdditionalDataY = new[] { dpvSignalY };
        }

        #endregion DPV Commands

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

        #endregion

        #region RelayCommands
        [RelayCommand]
        private async Task UpdateNoOfSegmentsAsync()
        {
            ReceivedData += "No of Segments: " + NoOfSegments + Environment.NewLine;
            string dataToSend = "POTEn:DPV:NUMSegments " + NoOfSegments;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }


        [RelayCommand]
        private void UpdateCurrentRange(string CurrRange)
        {

            string dataToSend = "POTEn:DPV:CURRent:RANGe " + CurrRange[0];
            DataToSend = dataToSend;
            SendData();
        }

        [RelayCommand]
        private async Task UpdateInitialPotentialVoltAsync()
        {
            string convertedValue = ConvertToAppropriateUnit(InitialPotentialVolt);
            ReceivedData += "Initial Potential Volt: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:VOLT:INIT " + InitialPotentialVolt;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);

        }
        [RelayCommand]
        private async Task UpdateFinalPotentialVoltAsync()
        {
            string convertedValue = ConvertToAppropriateUnit(FinalPotentialVolt);
            ReceivedData += "Final Potential Volt: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:VOLT:FINAL " + FinalPotentialVolt;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }
        [RelayCommand]
        private async Task UpdateLowerPotentialVoltAsync()
        {
            string convertedValue = ConvertToAppropriateUnit(LowerPotentialVolt);
            ReceivedData += "Lower Potential Volt: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:VOLT:LOWER " + LowerPotentialVolt;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }

        [RelayCommand]
        private async Task UpdateUpperPotentialVoltAsync()
        {
            string convertedValue = ConvertToAppropriateUnit(UpperPotentialVolt);
            ReceivedData += "Upper Potential Volt: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:VOLT:UPPER " + UpperPotentialVolt;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }

        [RelayCommand]
        private async Task UpdateDifferentialPulseHeightAsync()
        {
            string convertedValue = ConvertToAppropriateUnit(DifferentialPulseHeight);
            ReceivedData += "Differential Pulse Height: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:VOLT:PULSe:HEIGht " + DifferentialPulseHeight;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }

        [RelayCommand]
        private async Task UpdateDifferentialPulseWidthAsync()
        {
            string convertedValue = ConvertToAppropriateTimeUnit(DifferentialPulseWidth);
            ReceivedData += "Differential Pulse Width: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:TIME:PULSe:WIDTH " + DifferentialPulseWidth;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }

        [RelayCommand]
        private async Task UpdateDifferentialPulsePeriodAsync()
        {
            string convertedValue = ConvertToAppropriateTimeUnit(DifferentialPulsePeriod);
            ReceivedData += "Differential Pulse Period: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:TIME:PULSe:PERIod " + DifferentialPulsePeriod;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }

        [RelayCommand]
        private async Task UpdateDifferentialPulseIncrementAsync()
        {
            string convertedValue = ConvertToAppropriateTimeUnit(DifferentialPulseIncrement);
            ReceivedData += "Differential Pulse Increment: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:VOLT:PULSe:INCR " + DifferentialPulseIncrement;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }

        [RelayCommand]
        private async Task UpdateDifferentialPulsePrePulseWidthAsync()
        {
            string convertedValue = ConvertToAppropriateTimeUnit(DifferentialPulsePrePulseWidth);
            ReceivedData += "Differential Pulse Pre-Pulse Width: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:TIME:PULSE:PRE " + DifferentialPulsePrePulseWidth;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
        }

        [RelayCommand]
        private async Task UpdateDifferentialPulsePostPulseWidthAsync()
        {
            string convertedValue = ConvertToAppropriateTimeUnit(DifferentialPulsePostPulseWidth);
            ReceivedData += "Differential Pulse Post-Pulse Width: " + convertedValue + Environment.NewLine;
            string dataToSend = "POTEn:DPV:TIME:PULSE:POST " + DifferentialPulsePostPulseWidth;
            DataToSend = dataToSend;
            SendData();
            await Task.Delay(50);
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

        private string ConvertToAppropriateUnit(string voltage)
        {
            if (double.TryParse(voltage, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number))
            {
                string unit;
                double displayValue;

                if (number == 0.0)
                {
                    displayValue = number;
                    unit = "V";
                }
                else if (Math.Abs(number) < 0.001)
                {
                    displayValue = number * 1_000_000;
                    unit = "uV";
                }
                else if (Math.Abs(number) < 1)
                {
                    displayValue = number * 1000;
                    unit = "mV";
                }
                else
                {
                    displayValue = number;
                    unit = "V";
                }

                return displayValue.ToString("F0") + unit;
            }
            return voltage;
        }

        private string ConvertToAppropriateTimeUnit(string time)
        {
            if (double.TryParse(time, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out double number))
            {
                string unit;
                double displayValue;

                if (number < 1)
                {
                    displayValue = number * 1000;
                    unit = "ms";
                }
                else
                {
                    displayValue = number;
                    unit = "s";
                }

                return displayValue.ToString("F0") + unit;
            }
            return time;
        }
        #endregion RelayCommands

        public new event PropertyChangedEventHandler PropertyChanged;

        protected new void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
