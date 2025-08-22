using Poten2501.Services;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO.Ports;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Input;

namespace Poten2501.ViewModels
{
    public partial class MainPageViewModel : INotifyPropertyChanged
    {
        private readonly ISerialPortService _serialPortService;
        private string _selectedPort;
        private int _selectedBaudRate = 115200; // Default baud rate
        private string _receivedData;
        private string _dataToSend;
        private bool _isPortOpen = false;

        public ObservableCollection<string> AvailablePorts { get; } = [];
        public ObservableCollection<int> BaudRates { get; } = [300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200];

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

        public int SelectedBaudRate
        {
            get => _selectedBaudRate;
            set
            {
                if (_selectedBaudRate != value)
                {
                    _selectedBaudRate = value;
                    OnPropertyChanged(nameof(SelectedBaudRate));
                }
            }
        }

        public string ReceivedData
        {
            get => _receivedData;
            private set
            {
                if (_receivedData != value)
                {
                    _receivedData = value;
                    OnPropertyChanged(nameof(ReceivedData));
                }
            }
        }

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
                    //((Command)SendDataCommand).ChangeCanExecute();
                }
            }
        }
        private void UpdateSendDataCanExecute()
        {
            ((Command)SendDataCommand).ChangeCanExecute();
        }
        public bool IsPortOpen
        {
            get => _isPortOpen;
            set
            {
                if (_isPortOpen != value)
                {
                    _isPortOpen = value;
                    OnPropertyChanged(nameof(IsPortOpen));
                    OnPropertyChanged(nameof(ConnectButtonText));
                    UpdateConnectButtonState();
                    UpdateSendDataCanExecute();
                }
            }
        }
        public string ConnectButtonText => IsPortOpen ? "Disconnect" : "Connect";

        public ICommand RefreshPortsCommand { get; }
        public ICommand ConnectCommand { get; }
        public ICommand SendDataCommand { get; }
        public ICommand ClearReceivedDataCommand { get; }

        public string ButtonPortOpenText { get; set; } = "Connect";
        public bool IsOpenPortEnabled { get; set; } = true;
        public string ButtonPortCloseText { get; set; } = "Disconnect";
        public bool IsClosePortEnabled { get; set; } = false;



        public MainPageViewModel(ISerialPortService serialPortService)
        {
            _serialPortService = serialPortService;
            _serialPortService.DataReceived += OnDataReceived;

            RefreshPortsCommand = new Command(RefreshPorts);
            ConnectCommand = new Command(TogglePortConnection, CanConnectOrDisconnect);
            SendDataCommand = new Command(SendData, CanSendData);
            ClearReceivedDataCommand = new Command(ClearReceivedData);
            RefreshPorts();
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
            return !string.IsNullOrEmpty(DataToSend) && IsPortOpen;
        }

        private void OnDataReceived(object sender, byte[] data)
        {
            string receivedString = Encoding.UTF8.GetString(data);
            ReceivedData += receivedString;
        }

        public event PropertyChangedEventHandler PropertyChanged;
        protected virtual void OnPropertyChanged(string propertyName)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
}
