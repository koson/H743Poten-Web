#!/usr/bin/env python3
"""
CV (Cyclic Voltammetry) Test Script with Real-time Plotting
Uses POTEn:CV:Start:ALL command for complete parameter setup
"""

import serial
import time
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
import threading
import os
import sys

# เพิ่มไลบรารีที่จำเป็น
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    print("Warning: tkinter not available. Using command-line interface instead.")

# เพิ่ม data management system
from file_utils import ensure_directory_exists, get_data_root_folder

# Global debug settings
ENABLE_AUTO_RANGE_DEBUG = True  # เปิด/ปิดการแสดง AUTO-RANGE debug

# เพิ่มฟังก์ชันสำหรับแปลงรูปแบบ CSV
def convert_raw_data_to_standard_format(raw_line):
    """
    แปลงข้อมูลดิบจาก STM32 ให้เป็นรูปแบบมาตรฐาน
    Input: "CV, 744, -0.3903, 123.4567, 2, 1, 1409, 2051, 0, 1392" (Current already in µA)
    Output: "CV,744,-0.3903,123.4567,2,1,1409,2051,0,1392" (Current kept as µA)
    """
    try:
        parts = [part.strip() for part in raw_line.split(',')]
        if len(parts) < 10 or parts[0] != 'CV':
            return raw_line  # ส่งคืนข้อมูลดิบถ้าไม่ใช่รูปแบบที่คาดหวัง
        
        # แปลงข้อมูลตามรูปแบบ SCPI: Type, Time(us), Potential(V), Current(µA), ...
        # หมายเหตุ: ฟิร์มแวร์ใหม่ส่ง Current เป็น µA มาแล้ว ไม่ต้องแปลงเพิ่ม
        converted_parts = [
            parts[0].strip(),  # Type
            parts[1].strip(),  # Time(us) - เก็บเป็น microseconds 
            parts[2].strip(),  # Potential(V)
            parts[3].strip(),  # Current(µA) - รับเป็น µA โดยตรง ไม่ต้องแปลง
            parts[4].strip(),  # TIA_Gain_Index
            parts[5].strip(),  # Cycle_Number
            parts[6].strip(),  # DAC1_counts
            parts[7].strip(),  # DAC2_counts
            parts[8].strip(),  # Sequence_Number
            parts[9].strip()   # ADC_Data
        ]
        
        return ','.join(converted_parts)
        
    except (ValueError, IndexError):
        return raw_line  # ส่งคืนข้อมูลดิบถ้าแปลงไม่สำเร็จ

def get_standard_csv_header():
    """ส่งคืน header สำหรับ CV ในรูปแบบมาตรฐาน"""
    return "Type,Time(us),Potential(V),Current(uA),TIA_Gain_Index,Cycle_Number,DAC1_counts,DAC2_counts,Sequence_Number,ADC_Data"

def debug_auto_range(voltage, current_ua, tia_gain_index, dac1_counts=None):
    """
    แสดงข้อมูล debug สำหรับ AUTO-RANGE
    Args:
        voltage: ศักย์ไฟฟ้า (V)
        current_ua: กระแส (µA) 
        tia_gain_index: ดัชนี TIA gain (0-3)
        dac1_counts: ค่า DAC1 (optional)
    """
    # TIA Gain values ตามที่กำหนดใน firmware
    tia_gains = {0: 1e3, 1: 10e3, 2: 100e3, 3: 1e6}  # Ohms
    current_ranges = {0: "±1mA", 1: "±100µA", 2: "±10µA", 3: "±1µA"}
    
    if tia_gain_index in tia_gains:
        rgain = tia_gains[tia_gain_index]
        range_str = current_ranges[tia_gain_index]
        
        debug_msg = f"AUTO-RANGE DEBUG: V={voltage:.4f}, Range={tia_gain_index}, RGain={rgain:.0f}, I={current_ua:.2f} µA"
        if dac1_counts is not None:
            debug_msg = debug_msg + f", DAC1={dac1_counts}"
        debug_msg = debug_msg + f" ({range_str})"
        
        print(debug_msg)
        return debug_msg
    else:
        print(f"AUTO-RANGE DEBUG: V={voltage:.4f}, Range={tia_gain_index} (UNKNOWN), I={current_ua:.2f} µA")
        return None

# แสดงข้อมูลโฟลเดอร์ที่จะใช้เก็บข้อมูล
DATA_ROOT = get_data_root_folder()
if not os.path.exists(DATA_ROOT):
    print(f"Creating data directory: {DATA_ROOT}")
    try:
        ensure_directory_exists(DATA_ROOT)
        print(f"✓ Data directory created successfully")
    except Exception as e:
        print(f"✗ Error creating directory: {e}")
        print("Data will be saved in current directory instead.")
else:
    print(f"Data will be stored in: {DATA_ROOT}")
    print(f"  └── CSV files in {os.path.join(DATA_ROOT, 'CV', 'data')}")
    print(f"  └── PNG plots in {os.path.join(DATA_ROOT, 'CV', 'plots')}")
from tkinter import ttk, messagebox

def format_current_value(current_microamperes):
    """แปลงค่ากระแสเป็นหน่วยที่เหมาะสม (µA หรือ mA) - Input already in µA"""
    # ข้อมูลเข้ามาเป็น µA แล้ว ไม่ต้องแปลง
    if abs(current_microamperes) >= 1000:
        return current_microamperes / 1000, "mA"  # แปลงจาก µA เป็น mA
    else:
        return current_microamperes, "µA"

def format_current_array(current_array):
    """แปลงอาร์เรย์ของค่ากระแสและหาหน่วยที่เหมาะสม - Input already in µA"""
    if len(current_array) == 0:
        return current_array, "µA"
    
    # ข้อมูลเข้ามาเป็น µA แล้ว
    max_current_ua = max(abs(c) for c in current_array)
    
    if max_current_ua >= 1000:
        # ใช้หน่วย mA (แปลงจาก µA เป็น mA)
        converted_array = [c / 1000 for c in current_array]
        return converted_array, "mA"
    else:
        # ใช้หน่วย µA (ใช้ตรงๆ)
        converted_array = current_array
        return converted_array, "µA"

class CVPlotter:
    """Real-time CV data plotter with zoom and multi-cycle support"""
    
    def __init__(self, title="CV (Cyclic Voltammetry)", max_cycles=10, params=None):
        # เก็บข้อมูลแต่ละรอบแยกกัน
        self.cycles_data = {}  # {cycle_number: {'voltage': [], 'current': [], 'time': []}}
        self.current_cycle = 1
        self.max_cycles = max_cycles
        self.last_voltage = None
        self.voltage_direction = 1  # 1 = increasing, -1 = decreasing
        self.params = params or {}
        
        # การกรองข้อมูล
        self.data_points_added = 0
        self.voltage_range = None
        self.last_current = 0.0  # เก็บค่ากระแสล่าสุดสำหรับตรวจสอบการกระโดด
        if params:
            self.voltage_range = (params.get('lower', -1.0), params.get('upper', 1.0))
        
        # สีสำหรับแต่ละรอบ
        self.cycle_colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]
        
        # สร้างกราฟ
        plt.ion()  # Turn on interactive mode
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        
        # เก็บ line objects สำหรับแต่ละรอบ
        self.lines = {}
        
        self.ax.set_xlabel('Potential (V)', fontsize=12)
        self.ax.set_ylabel('Current (µA)', fontsize=12)  # เริ่มต้นด้วย µA
        self.ax.set_title(title, fontsize=14)
        self.ax.grid(True, alpha=0.3)
        
        # เพิ่มข้อความแสดง parameter ถ้ามี
        if self.params:
            self.add_parameter_text()
        
        # เพิ่ม scroll zoom functionality
        self.setup_zoom()
        
        # ตัวแปรสำหรับควบคุมการอัพเดต
        self.is_plotting = False
        self.data_lock = threading.Lock()
        
    def add_parameter_text(self):
        """เพิ่มข้อความแสดง parameter ในกราฟ"""
        param_text = "CV Parameters:\n"
        param_text += f"Begin: {self.params.get('begin', 'N/A')} V\n"
        param_text += f"Upper: {self.params.get('upper', 'N/A')} V\n"
        param_text += f"Lower: {self.params.get('lower', 'N/A')} V\n"
        param_text += f"Scan Rate: {self.params.get('rate', 'N/A')} V/s\n"
        param_text += f"Cycles: {self.params.get('cycles', 'N/A')}"
        
        # วางข้อความที่มุมซ้ายบน
        self.ax.text(0.02, 0.98, param_text, transform=self.ax.transAxes,
                    verticalalignment='top', horizontalalignment='left',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                    fontsize=9)

        
    def setup_zoom(self):
        """ตั้งค่าการซูมด้วย mouse wheel"""
        def on_scroll(event):
            if event.inaxes != self.ax:
                return
                
            # รับตำแหน่งเมาส์
            xdata, ydata = event.xdata, event.ydata
            if xdata is None or ydata is None:
                return
            
            # กำหนดระดับการซูม
            zoom_factor = 0.9 if event.button == 'up' else 1.1
            
            # รับขอบเขตปัจจุบัน
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # คำนวณขอบเขตใหม่
            xrange = (xlim[1] - xlim[0]) * zoom_factor
            yrange = (ylim[1] - ylim[0]) * zoom_factor
            
            # ตั้งขอบเขตใหม่โดยใช้ตำแหน่งเมาส์เป็นจุดศูนย์กลาง
            self.ax.set_xlim(
                xdata - xrange/2, 
                xdata + xrange/2
            )
            self.ax.set_ylim(
                ydata - yrange/2, 
                ydata + yrange/2
            )
            
            # รีเฟรชกราฟ
            self.fig.canvas.draw()
        
        # เชื่อมต่อ event handler
        self.fig.canvas.mpl_connect('scroll_event', on_scroll)
        
        # เพิ่ม keyboard shortcuts
        def on_key_press(event):
            if event.key == 'r':
                self.reset_view()
            elif event.key == 'c':
                self.clear_data()
                
        self.fig.canvas.mpl_connect('key_press_event', on_key_press)
        
    def detect_cycle_change(self, voltage):
        """ตรวจจับการเปลี่ยนรอบ - ปรับปรุงให้แม่นยำกว่าเดิม"""
        if self.last_voltage is None:
            self.last_voltage = voltage
            return
            
        # คำนวณการเปลี่ยนแปลงของแรงดัน
        voltage_change = voltage - self.last_voltage
        
        # กำหนด threshold เพื่อลดการเปลี่ยน cycle จาก noise
        voltage_threshold = 0.001  # 1mV threshold
        
        if abs(voltage_change) > voltage_threshold:
            current_direction = 1 if voltage_change > 0 else -1
            
            # ตรวจจับการเปลี่ยนทิศทางอย่างชัดเจน
            if (self.voltage_direction == 1 and current_direction == -1) or \
               (self.voltage_direction == -1 and current_direction == 1):
                
                # เฉพาะการเปลี่ยนจาก decreasing เป็น increasing เท่านั้นที่จะเป็นการจบรอบ
                if self.voltage_direction == -1 and current_direction == 1:
                    self.current_cycle += 1
                    if self.current_cycle > self.max_cycles:
                        self.current_cycle = self.max_cycles
                        
                self.voltage_direction = current_direction
        
        self.last_voltage = voltage
        
    def add_data_point(self, voltage, current, timestamp):
        """เพิ่มจุดข้อมูลใหม่ พร้อมการกรองข้อมูลที่ผิดปกติ"""
        with self.data_lock:
            # การกรองข้อมูลเพิ่มเติม
            if self.voltage_range:
                # ตรวจสอบว่า voltage อยู่ในช่วงที่กำหนดหรือไม่ (เผื่อ 20%)
                lower_limit = self.voltage_range[0] - 0.2
                upper_limit = self.voltage_range[1] + 0.2
                
                if voltage < lower_limit or voltage > upper_limit:
                    print(f"  --> Filtering out-of-range voltage: {voltage:.3f}V (range: {self.voltage_range[0]:.2f} to {self.voltage_range[1]:.2f}V)")
                    return
            
            # ถ้าเป็นข้อมูลจุดแรกๆ ให้เช็คการกระโดดของ voltage ที่ผิดปกติ
            if self.data_points_added < 5 and self.last_voltage is not None:
                voltage_jump = abs(voltage - self.last_voltage)
                if voltage_jump > 0.5:  # กระโดด > 0.5V ใน 1 จุด
                    print(f"  --> Filtering large voltage jump: {voltage:.3f}V (jump: {voltage_jump:.3f}V)")
                    return
            
            # ตรวจจับการเปลี่ยนรอบ
            self.detect_cycle_change(voltage)
            
            # สร้าง data structure สำหรับรอบใหม่ถ้าจำเป็น
            if self.current_cycle not in self.cycles_data:
                self.cycles_data[self.current_cycle] = {
                    'voltage': deque(maxlen=2000),
                    'current': deque(maxlen=2000), 
                    'time': deque(maxlen=2000)
                }
                
            # เพิ่มข้อมูลลงในรอบปัจจุบัน
            cycle_data = self.cycles_data[self.current_cycle]
            cycle_data['voltage'].append(voltage)
            cycle_data['current'].append(current)
            cycle_data['time'].append(timestamp)
            
            self.data_points_added += 1
    
    def update_plot(self):
        """อัพเดตกราฟ"""
        if not self.is_plotting:
            return

        with self.data_lock:
            # รวบรวมข้อมูลทั้งหมดเพื่อหาหน่วยที่เหมาะสม
            all_currents = []
            for cycle_data in self.cycles_data.values():
                all_currents.extend(list(cycle_data['current']))

            if all_currents:
                # หาหน่วยที่เหมาะสม
                converted_currents, current_unit = format_current_array(all_currents)
                self.ax.set_ylabel(f'Current ({current_unit})', fontsize=12)

            # อัพเดตแต่ละรอบ
            for cycle_num, cycle_data in self.cycles_data.items():
                if len(cycle_data['voltage']) > 0:
                    # แปลงหน่วยกระแส
                    current_list = list(cycle_data['current'])
                    if current_list:
                        converted_currents, _ = format_current_array(current_list)
                    else:
                        converted_currents = []

                    # สร้าง line ใหม่ถ้ายังไม่มี
                    if cycle_num not in self.lines:
                        color = self.cycle_colors[(cycle_num - 1) % len(self.cycle_colors)]
                        line, = self.ax.plot([], [], color=color, linewidth=2, 
                                           label=f'Cycle {cycle_num}')
                        self.lines[cycle_num] = line

                    # อัพเดตข้อมูล
                    self.lines[cycle_num].set_data(
                        list(cycle_data['voltage']), 
                        converted_currents
                    )

            # อัพเดต legend
            if len(self.lines) > 0:
                self.ax.legend(loc='upper right', fontsize=10)

            # ปรับขอบเขตของกราฟ
            self.ax.relim()
            self.ax.autoscale_view()

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
    
    def start_plotting(self):
        """เริ่มการพล็อต"""
        self.is_plotting = True
        plt.show()
    
    def stop_plotting(self):
        """หยุดการพล็อต"""
        self.is_plotting = False
    
    def save_plot(self, filename, use_external_folder=True):
        """บันทึกกราฟในโฟลเดอร์แยก"""
        try:
            # ใช้ระบบจัดการไฟล์ใหม่
            from file_utils import get_save_path_for_file
            
            # สร้างพาธสำหรับบันทึกไฟล์ (จะอยู่ในโฟลเดอร์แยกตามเทคนิคและวันที่)
            full_path = get_save_path_for_file('CV', filename, 'plots', use_external_folder)
            
            self.fig.savefig(full_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved as: {full_path}")
            return full_path
        except Exception as e:
            print(f"Error saving plot: {e}")
            return filename
    
    def clear_data(self):
        """ล้างข้อมูล"""
        with self.data_lock:
            self.cycles_data.clear()
            self.lines.clear()
            self.current_cycle = 1
            self.last_voltage = None
            self.voltage_direction = 1
            self.ax.clear()
            self.ax.set_xlabel('Potential (V)', fontsize=12)
            self.ax.set_ylabel('Current (µA)', fontsize=12)
            self.ax.set_title(self.ax.get_title(), fontsize=14)
            self.ax.grid(True, alpha=0.3)
            if self.params:
                self.add_parameter_text()
            
    def reset_view(self):
        """รีเซ็ตมุมมองกราฟ"""
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw()

def parse_cv_data_line(line, enable_debug=False):
    """แยกข้อมูล CV จากบรรทัด CSV
    Format: CV, Time(us), Voltage(V), Current(µA), TIA_Gain_Index, Cycle, DAC1, DAC2, Point No., ADC_Data
    
    Args:
        line: บรรทัดข้อมูล CSV
        enable_debug: เปิด/ปิดการแสดงข้อมูล debug AUTO-RANGE
    """
    try:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) >= 10 and parts[0] == 'CV':
            time_us = float(parts[1])         # Time in microseconds
            voltage = float(parts[2])         # Voltage in V  
            current_ua = float(parts[3])      # Current in µA (updated format)
            tia_gain_index = int(parts[4])    # TIA Gain Index (0-3)
            cycle = int(parts[5])             # Cycle number
            dac1_raw = int(parts[6])         # DAC1 (RAW)
            dac2_raw = int(parts[7])         # DAC2 (RAW)
            point_no = int(parts[8])         # Point No.
            adc_data = int(parts[9])         # ADC Data
            
            # แสดง AUTO-RANGE debug ถ้าเปิดใช้งาน
            if enable_debug:
                debug_auto_range(voltage, current_ua, tia_gain_index, dac1_raw)
            
            return time_us, voltage, current_ua, tia_gain_index, cycle, dac1_raw, dac2_raw, point_no, adc_data
    except (ValueError, IndexError) as e:
        print(f"Error parsing CV line: {e}")
        pass
    return None

def clear_stm32_state(ser):
    """ล้างสถานะ STM32 และหยุดการทำงานที่อาจค้างอยู่"""
    print("Clearing STM32 state...")
    
    try:
        # 1. ส่งคำสั่งหยุดหลายรอบ
        for i in range(3):
            ser.write(b'POTEn:ABORt\n')
            time.sleep(0.2)
            print(f"  Sent ABORT command #{i+1}")
        
        # 2. ล้างข้อมูลที่ค้างอยู่ใน buffer
        discarded_lines = 0
        start_clear = time.time()
        while time.time() - start_clear < 2:  # ล้างเป็นเวลา 2 วินาที
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                discarded_lines += 1
                if discarded_lines <= 5:  # แสดงข้อมูลที่ถูกทิ้งไป 5 บรรทัดแรก
                    print(f"  Discarded: {line}")
                elif discarded_lines == 6:
                    print(f"  ... (continuing to discard data)")
            else:
                time.sleep(0.05)
        
        print(f"  Discarded {discarded_lines} lines of old data")
        
        # 3. ส่งคำสั่งเช็คสถานะ
        ser.write(b'*IDN?\n')
        time.sleep(0.3)
        
        # 4. อ่าน response และตรวจสอบ
        response_received = False
        for attempt in range(5):
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                print(f"  Status check response: {response}")
                if "MANUFACTURE" in response or "STM32" in response:
                    response_received = True
                    break
            time.sleep(0.2)
        
        if response_received:
            print("  STM32 state cleared successfully!")
            return True
        else:
            print("  Warning: No valid response from STM32")
            return False
            
    except Exception as e:
        print(f"  Error clearing STM32 state: {e}")
        return False

def test_cv_scan():
    """Test CV using POTEn:CV:Start:ALL command with real-time plotting"""
    ser = None
    try:
        # เชื่อมต่อ STM32
        ser = serial.Serial('COM10', 115200, timeout=2)
        time.sleep(1)
        
        print('=== CV (Cyclic Voltammetry) Test with Real-time Plotting ===')
        print('Connected to STM32 via USB CDC\n')
        
        # ล้างสถานะ STM32 และหยุดการทำงานที่อาจค้างอยู่
        if not clear_stm32_state(ser):
            print("Warning: Could not fully clear STM32 state, but continuing...")
        
        print("Device connection verified!\n")
        
        # CV Test Parameters - ใช้ scan rates ที่ตรงกับงานจริง
        test_cases = [
            {
                'name': 'CV Test 1: Medium scan rate',
                'begin': -1.0,    # Begin potential (V)
                'upper': 1.0,    # Upper potential (V) 
                'lower': -1.0,   # Lower potential (V)
                'rate': 0.05,     # 50 mV/s
                'cycles': 3      # Number of cycles
            }
        ]
        
        for i, test in enumerate(test_cases):
            print(f"--- {test['name']} ---")
            print(f"Parameters:")
            print(f"  Begin: {test['begin']} V")
            print(f"  Upper: {test['upper']} V")
            print(f"  Lower: {test['lower']} V")
            print(f"  Scan Rate: {test['rate']} V/s")
            print(f"  Cycles: {test['cycles']}")
            
            # สร้าง plotter สำหรับการทดสอบนี้
            plotter = CVPlotter(f"{test['name']} - Real-time CV Plot", test['cycles'], test)
            
            # คำนวณเวลาที่ต้องใช้ในการ scan
            voltage_range = abs(test['upper'] - test['lower'])  # ช่วง voltage รวม
            time_per_cycle = (voltage_range * 2) / test['rate']  # เวลา 1 cycle (up + down)
            total_scan_time = time_per_cycle * test['cycles']    # เวลารวม
            timeout_buffer = total_scan_time + 30  # เผื่อ buffer 30s
            
            print(f"  Estimated scan time: {total_scan_time:.1f}s (timeout: {timeout_buffer:.1f}s)")
            
            # แจ้งเตือนสำหรับ scan rate ต่ำ
            if test['rate'] <= 0.02:  # 20mV/s หรือต่ำกว่า
                print(f"  Note: This is a slow scan (≤20mV/s), will take {total_scan_time/60:.1f} minutes")
            
            # เริ่มการพล็อต
            plotter.start_plotting()
            
            # สร้างคำสั่ง CV Start ALL
            # POTEn:CV:Start:ALL {begin},{upper},{lower},{scan_rate},{cycles}
            cmd = f"POTEn:CV:Start:ALL {test['begin']},{test['upper']},{test['lower']},{test['rate']},{test['cycles']}"
            print(f"\nSending: {cmd}")
            
            ser.write((cmd + '\n').encode())
            
            # รอผลลัพธ์
            print("Collecting CV data...")
            start_time = time.time()
            data_count = 0
            total_cv_lines = 0  # นับข้อมูล CV ทั้งหมดที่ได้รับ
            last_data_time = start_time
            cv_data_lines = []  # เก็บข้อมูล CV สำหรับบันทึกไฟล์
            
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                
                # ตรวจสอบ timeout (ใช้เวลาที่คำนวณได้)
                if elapsed > timeout_buffer:
                    print(f"  --> TIMEOUT reached ({timeout_buffer:.1f}s)")
                    break
                
                # อ่านข้อมูล
                if ser.in_waiting > 0:
                    line = ser.readline().decode().strip()
                    if line:
                        last_data_time = current_time
                        
                        # แสดงข้อมูลทั้งหมดพร้อม timestamp
                        print(f"  [{elapsed:6.1f}s] {line}")
                        
                        # ตรวจสอบและแยกข้อมูล CV สำหรับการพล็อต (ใช้ global debug setting)
                        cv_data = parse_cv_data_line(line, enable_debug=ENABLE_AUTO_RANGE_DEBUG)
                        if cv_data:
                            time_us, voltage, current_ua, tia_gain_index, cycle, dac1_raw, dac2_raw, point_no, adc_data = cv_data
                            total_cv_lines += 1  # นับข้อมูล CV ที่ได้รับ
                            
                            # time_us เป็น microseconds, แปลงเป็น ms เพื่อใช้ในการตรวจสอบ
                            delta_time_ms = time_us / 1000
                                
                            # ตรวจสอบ delta time ที่ผิดปกติ (เวลาแปลกๆ > 300ms)
                            # รองรับ scan rate ต่ำสุด 10mV/s ที่ใช้เวลา 110+ วินาที
                            if delta_time_ms > 300:  # เพิ่ม threshold สำหรับ CV scan ช้าๆ
                                print(f"  --> Skipping abnormal delta time: {delta_time_ms:.0f}ms")
                                continue                            # ข้าม data points แรกๆ เฉพาะ 3 จุดแรก (stabilization)
                            if total_cv_lines <= 3:
                                print(f"  --> Skipping initial stabilization: CV line {total_cv_lines} (Δt={delta_time_ms:.0f}ms)")
                                data_count += 1  # นับแต่ไม่ใส่กราฟ
                                cv_data_lines.append(line)  # เก็บไว้ในไฟล์
                                continue
                            
                            # ตรวจสอบการกระโดดของกระแสที่รุนแรง (ใช้ adaptive threshold)
                            if data_count > 3:  # เช็ค jump หลังจากข้าม stabilization แล้ว
                                current_jump = abs(current_ua - plotter.last_current)  # µA (ข้อมูลเป็น µA แล้ว)
                                last_current_ua = plotter.last_current  # ข้อมูลเป็น µA แล้ว
                                
                                # ใช้ adaptive threshold ตามขนาดของกระแส
                                max_current = max(abs(last_current_ua), abs(current_ua))
                                if max_current > 100:
                                    threshold = 350  # µA สำหรับกระแสสูง
                                else:
                                    threshold = 200  # µA สำหรับกระแสต่ำ
                                
                                if current_jump > threshold:
                                    print(f"  --> Skipping large current jump: ΔI={current_jump:.1f}µA (threshold={threshold}µA, Δt={delta_time_ms:.0f}ms)")
                                    continue
                            
                            # ข้อมูลผ่านการกรองแล้ว - เพิ่มเข้ากราฟ
                            #print(f"  --> Adding data: V={voltage:.3f}V, I={current_ua:.1f}µA, Δt={delta_time_ms:.0f}ms")
                            plotter.add_data_point(voltage, current_ua, elapsed)
                            plotter.update_plot()
                            plotter.last_current = current_ua  # เก็บค่ากระแสล่าสุด
                            data_count += 1
                            cv_data_lines.append(line)  # เก็บบรรทัดข้อมูลสำหรับบันทึกไฟล์
                        
                        # ตรวจสอบสัญญาณจบการสแกน
                        if "CV Operation Finished" in line or "CV scan completed" in line or "CV measurement finished" in line:
                            print(f"  --> CV scan completed at {elapsed:.1f}s")
                            break
                            
                        # ไม่ใช้ "CV Started" เป็นสัญญาณจบ เพราะมันเป็นการเริ่มต้น
                        if line.startswith("CV Started with params:"):
                            print(f"  --> CV scan starting...")
                            continue  # ไม่หยุด ให้อ่านข้อมูลต่อ
                
                # ตรวจสอบการไม่มีข้อมูลนานเกินไป
                if current_time - last_data_time > 15:
                    print(f"  --> No data for 15s - assuming scan complete")
                    break
                
                time.sleep(0.02)
            
            elapsed = time.time() - start_time
            rate = data_count / elapsed if elapsed > 0 else 0
            print(f"Result: {data_count} points in {elapsed:.1f}s ({rate:.1f} pts/s)")
            
            # บันทึกกราฟ
            plot_filename = f"cv_test_{i+1}_{int(time.time())}.png"
            plotter.save_plot(plot_filename)
            
            # บันทึกข้อมูล CSV
            if cv_data_lines:
                csv_filename = f"cv_data_{i+1}_{int(time.time())}.csv"
                save_cv_data_to_file(csv_filename, cv_data_lines)
            
            # หยุดการพล็อตและรอผู้ใช้
            plotter.stop_plotting()
            
            # รอสักครู่ก่อนการทดสอบต่อไป
            if i < len(test_cases) - 1:  # ไม่ใช่การทดสอบสุดท้าย
                input("\nPress Enter to continue to next test...")
                plt.close('all')  # ปิดกราฟก่อนไปการทดสอบต่อไป
            
            print()  # บรรทัดว่าง
        
        print('=== CV Testing Complete ===')
        
    except KeyboardInterrupt:
        print("\n\n=== USER INTERRUPTED ===")
        print("Cleaning up and stopping STM32...")
        if ser is not None:
            # หยุดการทำงานของ STM32 อย่างแน่นอน
            for i in range(5):
                ser.write(b'POTEn:ABORt\n')
                time.sleep(0.1)
            print("STM32 stop commands sent.")
        raise  # ส่งต่อ KeyboardInterrupt เพื่อจบโปรแกรม
        
    except serial.SerialException as e:
        print(f'Serial Error: {e}')
        print("Please check connection and try again.")
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if ser is not None:
            # ทำความสะอาดสุดท้าย
            try:
                print("Final cleanup...")
                ser.write(b'POTEn:ABORt\n')
                time.sleep(0.1)  # ลดเวลารอ
                ser.close()
                print("Serial connection closed.")
            except Exception as cleanup_error:
                print(f"Cleanup warning: {cleanup_error}")
                # Force close หากมีปัญหา
                try:
                    ser.close()
                except:
                    pass
        plt.close('all')
        print("Program finished successfully!")

def test_cv_individual_commands():
    """Test CV using individual parameter commands (backup method)"""
    try:
        ser = serial.Serial('COM6', 115200, timeout=2)
        time.sleep(1)
        
        print('\n=== CV Individual Commands Test ===')
        
        # CV individual commands
        cv_commands = [
            '*IDN?',
            'POTEn:VOLTage:BEGIn 0.0',      # Begin voltage
            'POTEn:VOLTage:UPPEr 0.5',      # Upper voltage limit
            'POTEn:VOLTage:LOWEr -0.5',     # Lower voltage limit  
            'POTEn:RATE:SWEEp 0.1',         # Scan rate (V/s)
            'POTEn:NUMCycles 1',            # Number of cycles
            'POTEn:PPS 100',                # Points per second
            'POTEn:CALCulate:SCANpattern',  # Calculate scan pattern
            'POTEn:CYCLic:Start',           # Start CV scan
        ]
        
        for cmd in cv_commands:
            print(f'\n> {cmd}')
            ser.write((cmd + '\n').encode())
            time.sleep(0.3)
            
            # อ่าน response
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if response:
                    print(f'< {response}')
            
            time.sleep(0.2)
        
        # รอผลลัพธ์จาก scan
        print("\nWaiting for scan results...")
        for i in range(20):
            if ser.in_waiting > 0:
                response = ser.readline().decode().strip()
                if response:
                    print(f"Scan: {response}")
            time.sleep(0.5)
        
        ser.close()
        print('\n=== Individual Commands Test Complete ===')
        
    except Exception as e:
        print(f'Error: {e}')

def save_cv_data_to_file(filename, cv_data_lines, use_external_folder=True):
    """บันทึกข้อมูล CV ลงไฟล์ CSV ในโฟลเดอร์แยก พร้อมแปลงเป็นรูปแบบมาตรฐาน"""
    try:
        # ใช้ระบบจัดการไฟล์ใหม่
        from file_utils import get_save_path_for_file
        
        # สร้างพาธสำหรับบันทึกไฟล์ (จะอยู่ในโฟลเดอร์แยกตามเทคนิคและวันที่)
        full_path = get_save_path_for_file('CV', filename, 'data', use_external_folder)
        
        # บันทึกไฟล์ด้วยรูปแบบมาตรฐาน
        with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
            # เขียน header แบบใหม่ที่ถูกต้อง
            csvfile.write(get_standard_csv_header() + '\n')
            
            # แปลงและเขียนข้อมูลแต่ละบรรทัด
            converted_count = 0
            for line in cv_data_lines:
                converted_line = convert_raw_data_to_standard_format(line)
                csvfile.write(converted_line + '\n')
                if converted_line != line:  # นับจำนวนบรรทัดที่ถูกแปลง
                    converted_count += 1
            
        print(f"  --> CV data saved to: {full_path}")
        print(f"  --> Converted {converted_count}/{len(cv_data_lines)} data lines to standard format")
        print(f"  --> Header: {get_standard_csv_header()}")
        return full_path
    except Exception as e:
        print(f"  --> Error saving CV data: {e}")
        return filename

def plot_cv_from_file(filename):
    """อ่านและพล็อตข้อมูล CV จากไฟล์ พร้อมรองรับทั้งรูปแบบเก่าและใหม่"""
    try:
        cv_data_list = []

        with open(filename, 'r') as f:
            lines = f.readlines()

        print(f"พบข้อมูล {len(lines)} บรรทัด")
        
        # ตรวจสอบรูปแบบ header เพื่อกำหนดวิธีการ parse
        header = lines[0].strip() if lines else ""
        is_new_format = "Time(us)" in header and "Current(uA)" in header
        
        if is_new_format:
            print("ตรวจพบรูปแบบใหม่ (มาตรฐาน)")
            print(f"Header: {header}")
        else:
            print("ตรวจพบรูปแบบเก่า")

        # ข้าม header line และ parse ข้อมูล
        for i, line in enumerate(lines[1:], 1):
            parts = [part.strip() for part in line.split(',')]
            if len(parts) >= 8 and parts[0] == 'CV':
                try:
                    if is_new_format:
                        # รูปแบบใหม่: Type,Time(us),Potential(V),Current(uA),TIA_Gain_Index,Cycle_Number,DAC1_counts,DAC2_counts,Sequence_Number,ADC_Data
                        time_us = float(parts[1])  # เวลาเป็น microseconds
                        voltage = float(parts[2])  # ศักย์เป็น Volts
                        current_ua = float(parts[3])  # กระแสเป็น µA (ส่งมาเป็น µA แล้ว)
                        current_a = current_ua  # เก็บเป็น µA สำหรับการ plot โดยตรง
                        tia_gain = int(parts[4]) if len(parts) > 4 else 0
                        cycle_num = int(parts[5]) if len(parts) > 5 else 1
                        sequence = int(parts[8]) if len(parts) > 8 else i
                    else:
                        # รูปแบบเก่า: Type,Point,Time,Voltage,Current,Extra1,Extra2,Extra3
                        time_us = float(parts[2])  # เวลาเป็น microseconds 
                        voltage = float(parts[3])  # แรงดันเป็น Volts
                        current_a = float(parts[4])  # กระแสเป็น Amperes
                        tia_gain = int(parts[5]) if len(parts) > 5 else 0
                        cycle_num = int(parts[6]) if len(parts) > 6 else 1
                        sequence = int(parts[7]) if len(parts) > 7 else i
                    
                    cv_data_list.append([time_us, voltage, current_a, tia_gain, cycle_num, sequence])
                except (ValueError, IndexError) as e:
                    print(f"Error parsing line {i}: {e}")
                    continue

        print(f"พบข้อมูล CV ที่ถูกต้อง: {len(cv_data_list)} จุด")

        if len(cv_data_list) < 10:
            print("ข้อมูลไม่เพียงพอสำหรับการพล็อต!")
            return

        # แปลงเป็น numpy arrays
        cv_data = np.array(cv_data_list)
        times_us = cv_data[:, 0]
        voltages = cv_data[:, 1]
        currents = cv_data[:, 2]  # ค่า current เป็น Amperes แล้ว
        tia_gains = cv_data[:, 3]
        cycle_nums = cv_data[:, 4]
        sequences = cv_data[:, 5]

        print(f"ข้อมูลดิบ:")
        print(f"  Time: {times_us.min():.0f} ถึง {times_us.max():.0f} µs")
        print(f"  Voltage: {voltages.min():.3f}V ถึง {voltages.max():.3f}V")
        print(f"  Current: {currents.min():.1f}µA ถึง {currents.max():.1f}µA")
        
        # แสดงข้อมูลเพิ่มเติม
        unique_cycles = np.unique(cycle_nums)
        print(f"  Cycles: {len(unique_cycles)} รอบ")
        if len(unique_cycles) > 1:
            print(f"  Cycle numbers: {unique_cycles}")

        # สร้างกราฟ
        plt.figure(figsize=(12, 8))

        # CV plot หลัก
        plt.subplot(2, 2, 1)
        
        # พล็อตแยกตามรอบถ้ามีหลายรอบ
        if len(unique_cycles) > 1:
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_cycles)))
            for i, cycle in enumerate(unique_cycles):
                mask = cycle_nums == cycle
                if np.sum(mask) > 0:
                    plt.plot(voltages[mask], currents[mask], 
                           color=colors[i], linewidth=1.5, alpha=0.8, 
                           label=f'Cycle {int(cycle)}')
            plt.legend()
        else:
            plt.plot(voltages, currents, 'b-', linewidth=1.5, alpha=0.8)
            
        plt.xlabel('Potential (V)')
        plt.ylabel('Current (µA)')
        plt.title(f'CV Plot - {os.path.basename(filename)}')
        plt.grid(True, alpha=0.3)

        # เพิ่มข้อมูลสถิติ
        plt.text(0.02, 0.98, f'จุดข้อมูล: {len(voltages)}\nรอบ: {len(unique_cycles)}', 
                transform=plt.gca().transAxes, fontsize=9, 
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        # กราฟ time series
        plt.subplot(2, 2, 2)
        plt.plot(times_us / 1000, currents, 'r-', linewidth=1, alpha=0.7)
        plt.xlabel('Time (ms)')
        plt.ylabel('Current (µA)')
        plt.title('Current vs Time')
        plt.grid(True, alpha=0.3)
        
        # กราฟ potential vs time  
        plt.subplot(2, 2, 3)
        plt.plot(times_us / 1000, voltages, 'g-', linewidth=1.5, alpha=0.8)
        plt.xlabel('Time (ms)')
        plt.ylabel('Potential (V)')
        plt.title('Applied Potential')
        plt.grid(True, alpha=0.3)
        
        # กราฟ TIA gain usage (ถ้ามีข้อมูล)
        plt.subplot(2, 2, 4)
        unique_gains, gain_counts = np.unique(tia_gains, return_counts=True)
        gain_labels = [f'Range {int(g)}' for g in unique_gains]
        plt.bar(gain_labels, gain_counts, alpha=0.7, color=['red', 'orange', 'yellow', 'green'][:len(unique_gains)])
        plt.xlabel('TIA Gain Range')
        plt.ylabel('Data Points')
        plt.title('Current Range Usage')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Error plotting CV from file: {e}")
        import traceback
        traceback.print_exc()

def detect_cycles_from_data(voltages, threshold=0.1):
    """ตรวจหา cycle changes จากข้อมูล voltage array"""
    if len(voltages) < 3:
        return []
    
    cycles = []
    current_cycle = 0
    direction = None  # 'up' หรือ 'down'
    last_voltage = voltages[0]
    peak_found = False
    valley_found = False
    
    for i, voltage in enumerate(voltages[1:], 1):
        voltage_diff = voltage - last_voltage
        
        if abs(voltage_diff) > threshold:  # มีการเปลี่ยนแปลงที่สำคัญ
            if voltage_diff > 0:  # กำลังขึ้น
                if direction == 'down' and valley_found:
                    current_cycle += 1
                    valley_found = False
                    peak_found = False
                direction = 'up'
            else:  # กำลังลง
                if direction == 'up' and peak_found:
                    current_cycle += 1
                    peak_found = False
                    valley_found = False
                direction = 'down'
            
            # ตรวจ peak/valley
            if direction == 'up' and i > 1 and voltages[i-2] < last_voltage < voltage:
                valley_found = True
            elif direction == 'down' and i > 1 and voltages[i-2] > last_voltage > voltage:
                peak_found = True
        
        cycles.append(current_cycle)
        last_voltage = voltage
    
    return [0] + cycles  # เพิ่ม cycle 0 สำหรับจุดแรก

def quick_test_current_file():
    """ทดสอบไฟล์ CV ปัจจุบันอย่างรวดเร็ว"""
    import os
    
    # หาไฟล์ CV ล่าสุด
    import glob
    cv_files = sorted(glob.glob("cv_data_*.csv"), key=os.path.getmtime, reverse=True)
    
    if cv_files:
        latest_file = cv_files[0]
        print(f"ทดสอบไฟล์ล่าสุด: {latest_file}")
        plot_cv_from_file(latest_file)
    else:
        print("ไม่พบไฟล์ CV data")

def test_cv_plot_from_existing_file():
    """ทดสอบการพล็อต CV จากไฟล์ที่มีอยู่แล้ว พร้อมการกรองข้อมูล"""
    import glob
    
    # หาไฟล์ CV ที่มีอยู่
    cv_files = glob.glob("cv_data_*.csv")
    
    if not cv_files:
        print("ไม่พบไฟล์ CV data")
        return
    
    print("ไฟล์ CV ที่พบ:")
    for i, file in enumerate(cv_files):
        print(f"  {i+1}. {file}")
    
    # ให้ผู้ใช้เลือกไฟล์
    try:
        choice = int(input("เลือกไฟล์ (1-{}): ".format(len(cv_files)))) - 1
        if 0 <= choice < len(cv_files):
            selected_file = cv_files[choice]
            print(f"กำลังพล็อต: {selected_file}")
            plot_cv_from_file(selected_file)
        else:
            print("ตัวเลือกไม่ถูกต้อง")
    except ValueError:
        print("กรุณาป้อนตัวเลข")

def test_swv_scan():
    """Test SWV using POTEn:SWV:Start:ALL command with real-time plotting"""
    ser = None
    try:
        # เชื่อมต่อ STM32
        ser = serial.Serial('COM6', 115200, timeout=2)
        time.sleep(1)

        print('=== SWV (Square Wave Voltammetry) Test with Real-time Plotting ===')
        print('Connected to STM32 via USB CDC\n')

        # ล้างสถานะ STM32 และหยุดการทำงานที่อาจค้างอยู่
        if not clear_stm32_state(ser):
            print("Warning: Could not fully clear STM32 state, but continuing...")

        print("Device connection verified!\n")

        # SWV Test Parameters
        test_params = {
            'begin': -0.4,    # Begin potential (V)
            'upper': 0.7,    # Upper potential (V)
            'lower': -0.4,   # Lower potential (V)
            'step': 0.01,    # Step potential (V)
            'amplitude': 0.025,  # Pulse amplitude (V)
            'frequency': 10,  # Frequency (Hz)
            'cycles': 3      # Number of cycles
        }

        print("SWV Parameters:")
        for key, value in test_params.items():
            print(f"  {key.capitalize()}: {value}")

        # สร้าง plotter สำหรับการทดสอบนี้
        plotter = CVPlotter("SWV - Real-time Plot", test_params['cycles'], test_params)

        # คำนวณเวลาที่ต้องใช้ในการ scan
        voltage_range = abs(test_params['upper'] - test_params['lower'])  # ช่วง voltage รวม
        time_per_cycle = (voltage_range / test_params['step']) / test_params['frequency']  # เวลา 1 cycle
        total_scan_time = time_per_cycle * test_params['cycles']    # เวลารวม
        timeout_buffer = total_scan_time + 30  # เผื่อ buffer 30s

        print(f"  Estimated scan time: {total_scan_time:.1f}s (timeout: {timeout_buffer:.1f}s)")

        # เริ่มการพล็อต
        plotter.start_plotting()

        # สร้างคำสั่ง SWV Start ALL
        # POTEn:SWV:Start:ALL {begin},{upper},{lower},{step},{amplitude},{frequency},{cycles}
        cmd = f"POTEn:SWV:Start:ALL {test_params['begin']},{test_params['upper']},{test_params['lower']},{test_params['step']},{test_params['amplitude']},{test_params['frequency']},{test_params['cycles']}"
        print(f"\nSending: {cmd}")

        ser.write((cmd + '\n').encode())

        # รอผลลัพธ์
        print("Collecting SWV data...")
        start_time = time.time()
        data_count = 0
        swv_data_lines = []  # เก็บข้อมูล SWV สำหรับบันทึกไฟล์

        while True:
            current_time = time.time()
            elapsed = current_time - start_time

            # ตรวจสอบ timeout
            if elapsed > timeout_buffer:
                print(f"  --> TIMEOUT reached ({timeout_buffer:.1f}s)")
                break

            # อ่านข้อมูล
            if ser.in_waiting > 0:
                line = ser.readline().decode().strip()
                if line:
                    print(f"  [{elapsed:6.1f}s] {line}")

                    # ตรวจสอบและแยกข้อมูล SWV สำหรับการพล็อต
                    swv_data = parse_cv_data_line(line)
                    if swv_data:
                        time_ms, voltage, current, current_gain, cycle, adc0_raw, dac1_raw, point_no, dac0_raw = swv_data
                        plotter.add_data_point(voltage, current, elapsed)
                        plotter.update_plot()
                        data_count += 1
                        swv_data_lines.append(line)  # เก็บบรรทัดข้อมูลสำหรับบันทึกไฟล์

                    # ตรวจสอบสัญญาณจบการสแกน
                    if "SWV Operation Finished" in line or "SWV scan completed" in line:
                        print(f"  --> SWV scan completed at {elapsed:.1f}s")
                        break

            time.sleep(0.02)

        elapsed = time.time() - start_time
        rate = data_count / elapsed if elapsed > 0 else 0
        print(f"Result: {data_count} points in {elapsed:.1f}s ({rate:.1f} pts/s)")

        # บันทึกกราฟ
        plot_filename = f"swv_test_{int(time.time())}.png"
        plotter.save_plot(plot_filename)

        # บันทึกข้อมูล CSV
        if swv_data_lines:
            csv_filename = f"swv_data_{int(time.time())}.csv"
            save_cv_data_to_file(csv_filename, swv_data_lines)

        # หยุดการพล็อต
        plotter.stop_plotting()

        print('=== SWV Testing Complete ===')

    except KeyboardInterrupt:
        print("\n\n=== USER INTERRUPTED ===")
        print("Cleaning up and stopping STM32...")
        if ser is not None:
            for i in range(5):
                ser.write(b'POTEn:ABORt\n')
                time.sleep(0.1)
            print("STM32 stop commands sent.")
        raise

    except serial.SerialException as e:
        print(f"Serial Error: {e}")
        print("Please check connection and try again.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if ser is not None:
            try:
                print("Final cleanup...")
                ser.write(b'POTEn:ABORt\n')
                time.sleep(0.1)
                ser.close()
                print("Serial connection closed.")
            except Exception as cleanup_error:
                print(f"Cleanup warning: {cleanup_error}")
                try:
                    ser.close()
                except:
                    pass
        plt.close('all')
        print("Program finished successfully!")

# เพิ่มคลาส MultiScanCVPlotter เพื่อแสดงกราฟรวมของแต่ละ scan rate
class MultiScanCVPlotter:
    """แสดงผล CV หลายรอบสแกนในอัตราเดียวกัน"""
    
    def __init__(self, scan_rate, title=None):
        self.scan_rate = scan_rate
        self.title = title or f"CV {scan_rate} mV/s - Multiple Scans"
        self.scan_data = {}  # เก็บข้อมูลแยกตาม scan number
        
        # สร้างกราฟหลัก
        self.fig, self.ax = plt.subplots(figsize=(10, 8))
        self.ax.set_xlabel('Potential (V)', fontsize=12)
        self.ax.set_ylabel('Current (µA)', fontsize=12)
        self.ax.set_title(self.title, fontsize=14)
        self.ax.grid(True, alpha=0.3)
        
        # color cycle สำหรับหลาย scan
        self.colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k', 
                      'tab:orange', 'tab:purple', 'tab:brown']
        
        # เพิ่ม parameter text
        self.param_text = f"CV Parameters:\nScan Rate: {scan_rate} mV/s"
        self.ax.text(0.02, 0.98, self.param_text, transform=self.ax.transAxes,
                    verticalalignment='top', horizontalalignment='left',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                    fontsize=9)
        
    def add_scan_data(self, scan_num, voltages, currents):
        """เพิ่มข้อมูลสแกนใหม่"""
        self.scan_data[scan_num] = {
            'voltages': voltages,
            'currents': currents
        }
        
    def update_plot(self):
        """อัพเดตกราฟด้วยข้อมูลทั้งหมด"""
        # ล้างกราฟ แต่คงไว้ซึ่งตัวเลือกต่างๆ
        self.ax.clear()
        
        # พล็อตข้อมูลทุกสแกนด้วยสีที่ต่างกัน
        all_currents = []
        for scan_num, data in sorted(self.scan_data.items()):
            color_idx = (scan_num - 1) % len(self.colors)
            label = f'Cycle {scan_num}'
            
            # ข้อมูลเป็น µA แล้ว ไม่ต้องแปลง
            currents_uA = data['currents']  # ใช้ตรงๆ เพราะเป็น µA แล้ว
            all_currents.extend(currents_uA)
            
            # พล็อตเส้น
            self.ax.plot(data['voltages'], currents_uA, 
                        color=self.colors[color_idx], 
                        linewidth=2, alpha=0.8, label=label)
        
        # ตั้งค่าแกน
        if all_currents:
            max_current = max(abs(min(all_currents)), abs(max(all_currents)))
            nice_limit = get_nice_range(all_currents)
            self.ax.set_ylim(-nice_limit, nice_limit)
            
        # ตั้งค่ากราฟ
        self.ax.set_xlabel('Potential (V)', fontsize=12)
        self.ax.set_ylabel('Current (µA)', fontsize=12)
        self.ax.set_title(self.title, fontsize=14)
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc='best')
        
        # เพิ่ม parameter text อีกครั้ง (เพราะ clear แล้ว)
        self.ax.text(0.02, 0.98, self.param_text, transform=self.ax.transAxes,
                  verticalalignment='top', horizontalalignment='left',
                  bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                  fontsize=9)
        
        # ปรับ layout
        self.fig.tight_layout()
        
    def save_plot(self, filename=None, use_external_folder=True):
        """บันทึกกราฟรวมในโฟลเดอร์แยก"""
        try:
            if filename is None:
                ts = int(time.time())
                filename = f"cv_combined_{self.scan_rate}mVps_{ts}.png"
            
            # ใช้ระบบจัดการไฟล์ใหม่
            from file_utils import get_save_path_for_file
            
            # สร้างพาธสำหรับบันทึกไฟล์ (จะอยู่ในโฟลเดอร์แยกตามเทคนิคและวันที่)
            full_path = get_save_path_for_file('CV', filename, 'plots', use_external_folder)
            
            self.update_plot()
            self.fig.savefig(full_path, dpi=300, bbox_inches='tight')
            print(f"Combined plot saved as: {full_path}")
            return full_path
        except Exception as e:
            print(f"Error saving combined plot: {e}")
            return None
    
    def show(self):
        """แสดงกราฟรวม"""
        self.update_plot()
        plt.show()

# เพิ่มฟังก์ชันสำหรับการคำนวณ nice range (เหมือนใน SWV)
def get_nice_range(values):
    """คำนวณช่วงที่ "ลงตัว" สำหรับค่าต่างๆ เช่น 0.1, 1, 2, 5, 10, 20, 50, 100"""
    if not values:
        return 1.0
    
    max_abs = max(abs(max(values)), abs(min(values)))
    if max_abs == 0:
        return 1.0
    
    # สร้างช่วงมาตรฐานแบบ 1-2-5 series
    nice_ranges = [
        0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 5, 10, 20, 25, 50, 100, 
        200, 250, 500, 1000, 2000, 5000, 10000
    ]
    
    # เลือกช่วงแรกที่ใหญ่กว่าค่าสูงสุด (เผื่อ 20%)
    for nice_range in nice_ranges:
        if nice_range > max_abs * 1.2:
            print(f"  Nice range: ±{nice_range} µA (max: {max_abs:.3f} µA)")
            return nice_range
    
    # ถ้าไม่มีช่วงที่เหมาะสม ใช้ค่าสูงสุด * 1.5
    return max_abs * 1.5

# เพิ่มฟังก์ชันดึงข้อมูล CV จากไฟล์ CSV
def extract_cv_data_from_csv(csv_file):
    """อ่านข้อมูล CV จากไฟล์ CSV และส่งคืน voltages, currents"""
    try:
        voltages = []
        currents = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            # ข้าม header
            next(f)
            
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 4 and parts[0].upper() == 'CV':
                    try:
                        voltage = float(parts[2])  # Voltage
                        current = float(parts[3])  # Current
                        voltages.append(voltage)
                        currents.append(current)
                    except (ValueError, IndexError):
                        continue
        
        return voltages, currents
    except Exception as e:
        print(f"Error reading CSV file {csv_file}: {e}")
        return [], []

# เพิ่มฟังก์ชันสำหรับ dialog เลือก scan rate และจำนวนรอบ
def show_scan_rate_selection_dialog():
    """แสดง dialog เลือก scan rate และจำนวนรอบสแกน"""
    if not HAS_TKINTER:
        return show_scan_rate_selection_cli()
        
    # สร้างฟังก์ชันสำหรับตรวจสอบความถูกต้องของจำนวนรอบ
    def validate_cycles(value):
        if value == "":
            return True
        try:
            val = int(value)
            return val > 0 and val <= 10
        except ValueError:
            return False
    
    root = tk.Tk()
    root.title("CV Scan Rate Selection")
    root.geometry("450x350")
    
    # ตั้งค่าให้หน้าต่างอยู่ตรงกลาง
    root.eval('tk::PlaceWindow . center')
    
    frame = ttk.Frame(root, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="Select Scan Rates and Cycles", font=("Arial", 14)).pack(pady=10)
    
    # ข้อความคำอธิบาย
    ttk.Label(frame, text="Choose scan rates (mV/s) and number of cycles for each:").pack(anchor="w", pady=5)
    
    # สร้าง frame สำหรับตัวเลือก scan rates
    rates_frame = ttk.Frame(frame)
    rates_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    # เลือก scan rates
    scan_rates = [10, 20, 50, 100, 200, 400]
    scan_vars = {}
    cycle_entries = {}
    
    # สร้างตัวเลือก scan rates และช่องใส่จำนวนรอบ
    for i, rate in enumerate(scan_rates):
        row = i // 3
        col = i % 3
        
        # สร้าง Frame สำหรับแต่ละ scan rate
        rate_frame = ttk.Frame(rates_frame)
        rate_frame.grid(row=row, column=col, padx=10, pady=5, sticky="w")
        
        # Checkbox และ label
        scan_vars[rate] = tk.BooleanVar(value=False)
        ttk.Checkbutton(rate_frame, variable=scan_vars[rate]).grid(row=0, column=0)
        ttk.Label(rate_frame, text=f"{rate} mV/s").grid(row=0, column=1, sticky="w")
        
        # ช่องใส่จำนวนรอบ
        ttk.Label(rate_frame, text="Cycles:").grid(row=0, column=2, padx=5)
        
        validate_cmd = (root.register(validate_cycles), '%P')
        entry = ttk.Entry(rate_frame, width=3, validate="key", validatecommand=validate_cmd)
        entry.grid(row=0, column=3)
        entry.insert(0, "3")  # ค่าเริ่มต้น
        cycle_entries[rate] = entry
    
    # คำแนะนำ
    ttk.Label(frame, text="Note: Maximum 10 cycles per scan rate\n"
                       "Recommended: 2-3 cycles for typical analysis").pack(pady=5)
    
    # เพิ่มปุ่ม Start และ Cancel
    button_frame = ttk.Frame(frame)
    button_frame.pack(pady=10, fill=tk.X)
    
    result = [[]]  # ใช้ list เก็บผลลัพธ์เพื่อให้แก้ไขใน callback
    
    def on_start():
        # ตรวจสอบว่ามีการเลือกอย่างน้อย 1 scan rate
        selected_configs = []
        for rate, var in scan_vars.items():
            if var.get():
                try:
                    cycles = int(cycle_entries[rate].get())
                    if cycles <= 0 or cycles > 10:
                        cycles = 3  # ถ้าไม่ถูกต้อง ใช้ค่าเริ่มต้น
                    selected_configs.append((rate, cycles))
                except (ValueError, TypeError):
                    selected_configs.append((rate, 3))  # ค่าเริ่มต้น
        
        if not selected_configs:
            messagebox.showwarning("No Selection", "Please select at least one scan rate.")
            return
        
        result[0] = selected_configs
        root.destroy()
    
    def on_cancel():
        result[0] = []  # ส่งคืนลิสต์ว่าง
        root.destroy()
    
    # แสดงปุ่ม
    ttk.Button(button_frame, text="Start Scans", command=on_start).pack(side=tk.RIGHT, padx=5)
    ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.RIGHT, padx=5)
    
    # เลือกอัน 100 mV/s เป็นค่าเริ่มต้น
    if 100 in scan_vars:
        scan_vars[100].set(True)
    
    root.mainloop()
    
    # ส่งคืนผลลัพธ์
    return result[0]

def show_scan_rate_selection_cli():
    """Command-line interface สำหรับเลือก scan rate และจำนวนรอบ"""
    print("\n=== CV Scan Rate Selection (CLI Mode) ===")
    print("Available scan rates: 10, 20, 50, 100, 200, 400 mV/s")
    print("Example input: '100:3,200:2' (100mV/s with 3 cycles, 200mV/s with 2 cycles)")
    print("Or just press Enter for default: 100mV/s with 3 cycles")
    
    try:
        user_input = input("Enter scan rates and cycles (rate:cycles,rate:cycles...): ").strip()
        
        if not user_input:
            # ค่าเริ่มต้น
            return [(100, 3)]
        
        selected_configs = []
        for part in user_input.split(','):
            if ':' in part:
                rate_str, cycles_str = part.split(':')
                rate = int(rate_str.strip())
                cycles = int(cycles_str.strip())
                
                # ตรวจสอบความถูกต้อง
                if rate in [10, 20, 50, 100, 200, 400] and 1 <= cycles <= 10:
                    selected_configs.append((rate, cycles))
                else:
                    print(f"Warning: Invalid rate/cycles {rate}:{cycles}, skipping...")
            else:
                # ถ้าไม่มี : ให้ใช้ 3 cycles เป็นค่าเริ่มต้น
                rate = int(part.strip())
                if rate in [10, 20, 50, 100, 200, 400]:
                    selected_configs.append((rate, 3))
                else:
                    print(f"Warning: Invalid rate {rate}, skipping...")
        
        if not selected_configs:
            print("No valid configurations. Using default: 100mV/s with 3 cycles")
            return [(100, 3)]
        
        print(f"Selected configurations: {selected_configs}")
        confirm = input("Proceed with these settings? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            return selected_configs
        else:
            return []
            
    except (ValueError, KeyboardInterrupt):
        print("Invalid input or cancelled. Using default: 100mV/s with 3 cycles")
        return [(100, 3)]

# เพิ่มฟังก์ชันทดสอบ CV แบบ multi scan rate
def test_cv_multi_scan_rate():
    """Test CV ด้วย scan rates ที่หลากหลาย และแต่ละ scan rate ทำหลายรอบได้"""
    ser = None
    
    # เลือก scan rates และจำนวนรอบ
    print("Opening scan rate selection dialog...")
    scan_configs = show_scan_rate_selection_dialog()
    
    if not scan_configs:
        print("No scan rates selected. Exiting.")
        return

    # Ensure scan_configs is a list, not None
    if scan_configs is None:
        scan_configs = []

    print(f"Selected configurations: {scan_configs}")
    
    try:
        # เชื่อมต่อ STM32
        ser = serial.Serial('COM6', 115200, timeout=2)
        time.sleep(1)
        
        print('\n=== CV Multi-Scan Rate Test ===')
        print('Connected to STM32 via USB CDC\n')
        
        # ล้างสถานะ STM32 และหยุดการทำงานที่อาจค้างอยู่
        if not clear_stm32_state(ser):
            print("Warning: Could not fully clear STM32 state, but continuing...")
        
        print("Device connection verified!\n")
        
        # พารามิเตอร์พื้นฐาน (ยกเว้น scan rate และจำนวนรอบ)
        base_params = {
            'begin': -0.4,    # Begin potential (V)
            'upper': 0.7,     # Upper potential (V)
            'lower': -0.4,    # Lower potential (V)
        }
        
        print("Base CV Parameters:")
        for key, value in base_params.items():
            print(f"  {key.capitalize()}: {value}")
            
        # คำนวณจำนวนสแกนทั้งหมด
        total_scans = sum(cycles for _, cycles in scan_configs)
        current_scan = 0
        
        print(f"\nStarting {total_scans} total scans across {len(scan_configs)} scan rates...")
        
        # เก็บผลลัพธ์
        all_results = []
        scan_rate_data = {}
        
        # ทดสอบแต่ละ scan rate
        for scan_rate, cycles in scan_configs:
            print(f"\n{'='*60}")
            print(f"Processing {scan_rate} mV/s - {cycles} cycle(s)")
            print(f"{'='*60}")
            
            # สร้าง plotter สำหรับ scan rate นี้
            rate_plotter = MultiScanCVPlotter(scan_rate, f"CV {scan_rate} mV/s - Combined Cycles")
            
            # ทำแต่ละรอบ
            for cycle_num in range(1, cycles + 1):
                current_scan += 1
                try:
                    # สร้างพารามิเตอร์สำหรับรอบนี้
                    test_params = base_params.copy()
                    test_params['rate'] = scan_rate / 1000  # แปลงเป็น V/s
                    test_params['cycles'] = cycles  # ใส่จำนวนรอบทั้งหมดที่ต้องการ
                    
                    print(f"\n=== CV Scan at {scan_rate} mV/s ({cycles} cycles) ===")
                    
                    # สร้าง plotter สำหรับรอบนี้
                    plotter = CVPlotter(f"CV {scan_rate} mV/s - {cycles} cycles", cycles, test_params)
                    
                    # คำนวณเวลาที่ต้องใช้ในการ scan
                    voltage_range = abs(test_params['upper'] - test_params['lower'])  # ช่วง voltage รวม
                    time_per_cycle = (voltage_range * 2) / test_params['rate']  # เวลา 1 cycle (up + down)
                    total_scan_time = time_per_cycle * test_params['cycles']  # เวลารวมทุกรอบ
                    safety_buffer = 40  # เผื่อ buffer 40s
                    timeout_buffer = total_scan_time + safety_buffer
                    
                    print(f"  Timeout calculation:")
                    print(f"    Voltage range: {voltage_range:.1f}V")
                    print(f"    Time per cycle: {time_per_cycle:.1f}s")
                    print(f"    Total scan time ({test_params['cycles']} cycles): {total_scan_time:.1f}s")
                    print(f"    Safety buffer: {safety_buffer:.1f}s")
                    print(f"    Total timeout: {timeout_buffer:.1f}s")
                    print(f"  Estimated scan time: {total_scan_time:.1f}s")
                    
                    # เคลียร์ buffer
                    print("  Clearing serial buffer...")
                    cleared_bytes = 0
                    while ser.in_waiting > 0:
                        ser.read(ser.in_waiting)
                        cleared_bytes += ser.in_waiting
                    if cleared_bytes > 0:
                        print(f"    Cleared {cleared_bytes} bytes (total: {cleared_bytes})")
                    
                    # เริ่มการพล็อต
                    plotter.start_plotting()
                    
                    # สร้างคำสั่ง CV Start ALL
                    # POTEn:CV:Start:ALL {begin},{upper},{lower},{scan_rate},{cycles}
                    cmd = f"POTEn:CV:Start:ALL {test_params['begin']},{test_params['upper']},{test_params['lower']},{test_params['rate']},{test_params['cycles']}"
                    print(f"  Sending: {cmd}")
                    
                    ser.write((cmd + '\n').encode())
                    
                    # รอการตอบสนองเริ่มต้น
                    print("  Waiting 2.0s for initial response...")
                    time.sleep(2)
                    
                    # รอผลลัพธ์
                    print("  Collecting data...")
                    start_time = time.time()
                    data_count = 0
                    last_data_time = start_time
                    cv_data_lines = []  # เก็บข้อมูล CV สำหรับบันทึกไฟล์
                    scan_completed = False
                    
                    while True:
                        current_time = time.time()
                        elapsed = current_time - start_time
                        
                        # ตรวจสอบ timeout
                        if elapsed > timeout_buffer:
                            print(f"  --> TIMEOUT reached ({timeout_buffer:.1f}s)")
                            break
                        
                        # อ่านข้อมูล
                        if ser.in_waiting > 0:
                            line = ser.readline().decode().strip()
                            if line:
                                last_data_time = current_time
                                
                                # ตรวจสอบสัญญาณจบการสแกน
                                if "CV Operation Finished" in line or "CV scan completed" in line or "CV measurement finished" in line:
                                    print(f"  --> CV scan completed at {elapsed:.1f}s")
                                    scan_completed = True
                                    break
                                
                                # แสดงข้อมูลเฉพาะข้อมูลแรกๆ
                                if data_count < 5 or data_count % 50 == 0:
                                    print(f"    [{elapsed:6.1f}s] {line}")
                                
                                            # ตรวจสอบและแยกข้อมูล CV สำหรับการพล็อต (ใช้ global debug setting)
                            cv_data = parse_cv_data_line(line, enable_debug=ENABLE_AUTO_RANGE_DEBUG)
                            if cv_data:
                                time_us, voltage, current_ua, tia_gain_index, cycle, dac1_raw, dac2_raw, point_no, adc_data = cv_data
                                
                                # ข้าม data points แรกๆ (stabilization)
                                if data_count < 3:
                                    cv_data_lines.append(line)  # เก็บไว้ในไฟล์
                                    data_count += 1
                                    continue
                                
                                # เพิ่มข้อมูลเข้ากราฟ
                                plotter.add_data_point(voltage, current_ua, elapsed)
                                plotter.update_plot()
                                data_count += 1
                                cv_data_lines.append(line)  # เก็บบรรทัดข้อมูลสำหรับบันทึกไฟล์
                                
                                # แสดงความก้าวหน้าเป็นระยะ
                                if data_count % 50 == 0 and data_count > 0:
                                    print(f"    Progress: {data_count} points, {elapsed:.1f}s")
                        
                        # ตรวจสอบการไม่มีข้อมูลนานเกินไป
                        if current_time - last_data_time > 10:
                            print(f"  --> No data for 10s - assuming scan complete")
                            break
                        
                        time.sleep(0.02)
                    
                    elapsed = time.time() - start_time
                    rate = data_count / elapsed if elapsed > 0 else 0
                    print(f"  Result: {data_count} points in {elapsed:.1f}s ({rate:.1f} pts/s)")
                    
                    # บันทึกกราฟ
                    plot_filename = f"cv_{scan_rate}mVps_cycle{cycle_num}_{int(time.time())}.png"
                    plotter.save_plot(plot_filename)
                    print(f"  Plot saved: {plot_filename}")
                    
                    # บันทึกข้อมูล CSV
                    csv_filename = None
                    csv_full_path = None
                    if cv_data_lines:
                        csv_filename = f"cv_{scan_rate}mVps_cycle{cycle_num}_{int(time.time())}.csv"
                        csv_full_path = save_cv_data_to_file(csv_filename, cv_data_lines)
                        print(f"  Data saved: {csv_filename}")
                    
                    # หยุดการพล็อตรอบนี้
                    plotter.stop_plotting()
                    
                    # เพิ่มข้อมูลเข้า combined plot
                    if csv_full_path:  # ใช้พาธเต็มแทน
                        try:
                            voltages, currents = extract_cv_data_from_csv(csv_full_path)
                            if voltages and currents:
                                rate_plotter.add_scan_data(cycle_num, voltages, currents)
                                print(f"  → Added cycle {cycle_num} data to combined plot")
                        except Exception as data_error:
                            print(f"  → Error adding data to combined plot: {data_error}")
                    
                    # บันทึกผลลัพธ์
                    result = {
                        'success': scan_completed,
                        'scan_rate': scan_rate,
                        'cycle_num': cycle_num,
                        'points': data_count,
                        'plot_file': plot_filename,
                        'csv_file': csv_filename,
                        'elapsed': elapsed
                    }
                    all_results.append(result)
                    
                    # แสดงสถานะ
                    status = "✓" if scan_completed else "✗"
                    print(f"  {status} Completed scan {current_scan}/{total_scans} "
                          f"({scan_rate} mV/s, cycle {cycle_num})")
                    
                except Exception as scan_error:
                    print(f"  ✗ Scan error: {scan_error}")
                    all_results.append({
                        'success': False,
                        'scan_rate': scan_rate,
                        'cycle_num': cycle_num,
                        'error': str(scan_error)
                    })
                    
                    # ถามว่าต้องการทำต่อหรือไม่
                    if current_scan < total_scans:
                        try:
                            continue_choice = input(f"  Continue with remaining {total_scans-current_scan} scans? (y/n): ")
                            if continue_choice.lower() not in ['y', 'yes']:
                                print("  User requested to stop scanning.")
                                break
                        except (KeyboardInterrupt, EOFError):
                            print("  User interrupted. Stopping.")
                            break
                
                # พักระหว่างรอบ (ยกเว้นรอบสุดท้าย)
                if current_scan < total_scans:
                    print("  Pausing 2 seconds before next scan...")
                    time.sleep(2)
            
            # บันทึก combined plot หลังทำทุกรอบในแต่ละ scan rate
            if rate_plotter.scan_data:  # มีข้อมูลอย่างน้อย 1 รอบ
                combined_filename = f"cv_combined_{scan_rate}mVps_{int(time.time())}.png"
                rate_plotter.save_plot(combined_filename)
                
                # เก็บข้อมูลสรุป
                scan_rate_data[scan_rate] = {
                    'combined_plot': combined_filename,
                    'cycle_count': len(rate_plotter.scan_data),
                    'plotter': rate_plotter
                }
                
                print(f"\n► Combined plot for {scan_rate} mV/s created with {len(rate_plotter.scan_data)} cycles")
                print(f"  File: {combined_filename}")
        
        # สรุปผล
        print(f"\n{'='*60}")
        print("CV Multi-Scan Rate Summary")
        print(f"{'='*60}")
        
        successful_scans = sum(1 for r in all_results if r.get('success'))
        failed_scans = len(all_results) - successful_scans
        print(f"Total scans attempted: {len(all_results)}")
        print(f"Successful scans: {successful_scans}")
        print(f"Failed scans: {failed_scans}")
        
        if successful_scans > 0:
            print("\nSuccessful scans:")
            for r in all_results:
                if r.get('success'):
                    print(f"  ✓ {r['scan_rate']} mV/s, Cycle {r['cycle_num']}: {r.get('points', 0)} data points")
        
        if failed_scans > 0:
            print("\nFailed scans:")
            for r in all_results:
                if not r.get('success'):
                    print(f"  ✗ {r['scan_rate']} mV/s, Cycle {r['cycle_num']}: {r.get('error','Unknown error')}")
        
        if scan_rate_data:
            print("\nCombined Plots:")
            for rate, data in sorted(scan_rate_data.items()):
                print(f"  • {rate} mV/s: {data['cycle_count']} cycles - {data['combined_plot']}")
        
        print(f"{'='*60}")
        
        # ถามว่าต้องการแสดงกราฟรวมหรือไม่
        try:
            show_plots = input("\nShow combined plots? (y/n): ").strip().lower()
            if show_plots in ['y', 'yes']:
                for rate, data in sorted(scan_rate_data.items()):
                    if 'plotter' in data:
                        print(f"Showing plot for {rate} mV/s...")
                        data['plotter'].show()
        except (KeyboardInterrupt, EOFError):
            pass
    
    except KeyboardInterrupt:
        print("\n\n=== USER INTERRUPTED ===")
        print("Cleaning up and stopping STM32...")
        if ser is not None:
            # หยุดการทำงานของ STM32 อย่างแน่นอน
            for i in range(5):
                ser.write(b'POTEn:ABORt\n')
                time.sleep(0.1)
            print("STM32 stop commands sent.")
    
    except serial.SerialException as e:
        print(f'Serial Error: {e}')
        print("Please check connection and try again.")
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if ser is not None:
            # ทำความสะอาดสุดท้าย
            try:
                print("Serial connection closed.")
                ser.close()
            except Exception as cleanup_error:
                print(f"Cleanup warning: {cleanup_error}")
                # Force close หากมีปัญหา
                try:
                    ser.close()
                except:
                    pass
        print("Program finished.")

# แก้ไขฟังก์ชัน main เพื่อเพิ่มตัวเลือกใหม่
if __name__ == "__main__":
    # เลือกโหมดการทำงาน
    print("=== CV Analysis Tool ===")
    print("1. Run new CV test (original)")
    print("2. Run CV multi-scan rate test (new)")
    print("3. Plot existing CV data file")
    print("4. Quick test latest CV file")
    
    try:
        mode = input("Select mode (1-4): ").strip()
        
        if mode == "1":
            test_cv_scan()
        elif mode == "2":
            test_cv_multi_scan_rate()
        elif mode == "3":
            test_cv_plot_from_existing_file()
        elif mode == "4":
            quick_test_current_file()
        else:
            print("Invalid mode selection, running CV multi-scan rate test...")
            test_cv_multi_scan_rate()
            
    except KeyboardInterrupt:
        print("\n=== Program cancelled by user ===")
        print("STM32 state has been cleared")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nIf problems persist, try resetting the STM32")
