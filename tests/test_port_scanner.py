"""
Tests for port scanner functionality
"""

import unittest
from unittest.mock import patch, MagicMock
from hardware.port_scanner import get_available_ports, find_stm32_ports, test_port_connection

class TestPortScanner(unittest.TestCase):
    
    @patch('serial.tools.list_ports.comports')
    def test_get_available_ports(self, mock_comports):
        # Create mock port
        mock_port = MagicMock()
        mock_port.device = 'COM3'
        mock_port.description = 'STM32 Virtual COM Port'
        mock_port.hwid = 'USB VID:PID=0483:374B'
        mock_port.manufacturer = 'STMicroelectronics'
        mock_port.vid = 0x0483
        mock_port.pid = 0x374B
        
        mock_comports.return_value = [mock_port]
        
        ports = get_available_ports()
        
        self.assertEqual(len(ports), 1)
        self.assertEqual(ports[0]['device'], 'COM3')
        self.assertEqual(ports[0]['description'], 'STM32 Virtual COM Port')
        self.assertEqual(ports[0]['manufacturer'], 'STMicroelectronics')
        
    @patch('hardware.port_scanner.get_available_ports')
    def test_find_stm32_ports(self, mock_get_ports):
        mock_get_ports.return_value = [
            {
                'device': 'COM3',
                'description': 'STM32 Virtual COM Port',
                'manufacturer': 'STMicroelectronics',
                'hwid': 'USB VID:PID=0483:374B',
                'vid': 0x0483,
                'pid': 0x374B
            },
            {
                'device': 'COM4',
                'description': 'Generic Serial Port',
                'manufacturer': 'FTDI',
                'hwid': 'USB VID:PID=0403:6001',
                'vid': 0x0403,
                'pid': 0x6001
            }
        ]
        
        stm32_ports = find_stm32_ports()
        
        self.assertEqual(len(stm32_ports), 1)
        self.assertEqual(stm32_ports[0]['device'], 'COM3')
        
    @patch('serial.Serial')
    def test_port_connection(self, mock_serial):
        # Test successful connection
        self.assertTrue(test_port_connection('COM3'))
        
        # Test failed connection
        mock_serial.side_effect = Exception('Connection failed')
        self.assertFalse(test_port_connection('COM3'))
        
if __name__ == '__main__':
    unittest.main()
