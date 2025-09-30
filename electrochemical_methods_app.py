#!/usr/bin/env python3
"""
H743 Potentiostat - Complete Electrochemical Methods Application
==============================================================
Integrated CV, DPV, SWV measurement system with GUI interface
Based on H743_ELECTROCHEMICAL_METHODS_SPECIFICATION.md
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import queue
import subprocess
import signal
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from test_cv_final import find_stm32_port
    ELECTROCHEMICAL_FUNCTIONS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Electrochemical functions not available: {e}")
    ELECTROCHEMICAL_FUNCTIONS_AVAILABLE = False

class ElectrochemicalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧪 H743 Potentiostat - Electrochemical Methods")
        self.root.geometry("1000x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Process management
        self.measurement_process = None
        self.output_queue = queue.Queue()
        
        # Current method parameters
        self.current_method = "CV"
        self.method_params = {
            "CV": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "scan_rate": 100,  # mV/s
                "cycles": 1,
                "current_range": "Auto"
            },
            "DPV": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "step_voltage": 5,  # mV
                "pulse_amplitude": 50,  # mV
                "pulse_width": 100,  # ms
                "sample_width": 20,  # ms
                "current_range": "Auto"
            },
            "SWV": {
                "start_voltage": -0.5,
                "end_voltage": 0.5,
                "step_voltage": 5,  # mV
                "sw_amplitude": 25,  # mV
                "sw_frequency": 50,  # Hz
                "current_range": "Auto"
            }
        }
        
        self.setup_gui()
        self.check_dependencies()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main frame - Reduced padding
        main_frame = ttk.Frame(self.root, padding="8")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title - Compact
        title_label = ttk.Label(main_frame, text="🧪 H743 Potentiostat", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=5)
        
        subtitle_label = ttk.Label(main_frame, text="Electrochemical Methods", 
                                  font=("Arial", 10))
        subtitle_label.pack(pady=2)
        
        # Connection frame - Compact
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(conn_frame, text="Checking connection...")
        self.status_label.pack(side=tk.LEFT)
        
        self.refresh_btn = ttk.Button(conn_frame, text="🔄 Refresh", 
                                     command=self.check_connection)
        self.refresh_btn.pack(side=tk.RIGHT)
        
        # Method selection frame - Compact
        method_frame = ttk.LabelFrame(main_frame, text="Methods", padding="5")
        method_frame.pack(fill=tk.X, pady=5)
        
        # Create notebook for methods
        self.notebook = ttk.Notebook(method_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs for each method
        self.cv_frame = ttk.Frame(self.notebook)
        self.dpv_frame = ttk.Frame(self.notebook)
        self.swv_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.cv_frame, text="🔬 Cyclic Voltammetry (CV)")
        self.notebook.add(self.dpv_frame, text="🔍 Differential Pulse (DPV)")
        self.notebook.add(self.swv_frame, text="⚡ Square Wave (SWV)")
        
        # Setup method tabs
        self.setup_cv_tab()
        self.setup_dpv_tab()
        self.setup_swv_tab()
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        
        # Control buttons frame - Compact
        control_frame = ttk.LabelFrame(main_frame, text="Control", padding="5")
        control_frame.pack(fill=tk.X, pady=5)
        
        # Buttons
        self.start_btn = ttk.Button(control_frame, text="🚀 Start Measurement", 
                                   command=self.start_measurement, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop", 
                                  command=self.stop_measurement, width=15)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.config(state="disabled")
        
        self.export_btn = ttk.Button(control_frame, text="💾 Export Data", 
                                    command=self.export_data, width=15)
        self.export_btn.pack(side=tk.RIGHT, padx=5)
        
        # Output frame - Reduced height
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="5")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Text output with scrollbar - Reduced height
        self.output_text = scrolledtext.ScrolledText(output_frame, height=8, 
                                                    font=("Consolas", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def setup_cv_tab(self):
        """Setup Cyclic Voltammetry tab"""
        # CV Parameters - Compact
        params_frame = ttk.LabelFrame(self.cv_frame, text="CV Parameters", padding="5")
        params_frame.pack(fill=tk.X, pady=2)
        
        # Grid layout for CV parameters
        grid = ttk.Frame(params_frame)
        grid.pack(fill=tk.X)
        
        # Voltage parameters
        ttk.Label(grid, text="Start Voltage (V):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.cv_start_v = tk.StringVar(value="-0.5")
        ttk.Entry(grid, textvariable=self.cv_start_v, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(grid, text="End Voltage (V):").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.cv_end_v = tk.StringVar(value="0.5")
        ttk.Entry(grid, textvariable=self.cv_end_v, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(grid, text="Scan Rate (mV/s):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.cv_scan_rate = tk.StringVar(value="100")
        ttk.Entry(grid, textvariable=self.cv_scan_rate, width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(grid, text="Cycles:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.cv_cycles = tk.StringVar(value="1")
        ttk.Entry(grid, textvariable=self.cv_cycles, width=10).grid(row=1, column=3, padx=5)
        
        # Current range
        ttk.Label(grid, text="Current Range:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.cv_current_range = ttk.Combobox(grid, width=12, values=["Auto", "100µA", "10µA", "1µA", "100nA"])
        self.cv_current_range.set("Auto")
        self.cv_current_range.grid(row=2, column=1, padx=5)
        
        # CV Info - Compact
        info_frame = ttk.LabelFrame(self.cv_frame, text="Method Info", padding="5")
        info_frame.pack(fill=tk.X, pady=2)
        
        cv_info = """🔬 Cyclic Voltammetry: Linear voltage sweep with current measurement
• Used for redox studies and reaction mechanisms"""
        
        ttk.Label(info_frame, text=cv_info, justify=tk.LEFT, font=("Arial", 9)).pack(anchor="w")
        
    def setup_dpv_tab(self):
        """Setup Differential Pulse Voltammetry tab"""
        # DPV Parameters - Compact
        params_frame = ttk.LabelFrame(self.dpv_frame, text="DPV Parameters", padding="5")
        params_frame.pack(fill=tk.X, pady=2)
        
        # Grid layout for DPV parameters
        grid = ttk.Frame(params_frame)
        grid.pack(fill=tk.X)
        
        # Voltage parameters
        ttk.Label(grid, text="Start Voltage (V):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.dpv_start_v = tk.StringVar(value="-0.5")
        ttk.Entry(grid, textvariable=self.dpv_start_v, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(grid, text="End Voltage (V):").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.dpv_end_v = tk.StringVar(value="0.5")
        ttk.Entry(grid, textvariable=self.dpv_end_v, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(grid, text="Step Voltage (mV):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.dpv_step_v = tk.StringVar(value="10")
        ttk.Entry(grid, textvariable=self.dpv_step_v, width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(grid, text="Pulse Amplitude (mV):").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.dpv_pulse_amp = tk.StringVar(value="50")
        ttk.Entry(grid, textvariable=self.dpv_pulse_amp, width=10).grid(row=1, column=3, padx=5)
        
        ttk.Label(grid, text="Pulse Width (ms):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.dpv_pulse_width = tk.StringVar(value="50")
        ttk.Entry(grid, textvariable=self.dpv_pulse_width, width=10).grid(row=2, column=1, padx=5)
        
        ttk.Label(grid, text="Sample Width (ms):").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        self.dpv_sample_width = tk.StringVar(value="100")
        ttk.Entry(grid, textvariable=self.dpv_sample_width, width=10).grid(row=2, column=3, padx=5)
        
        # Current range
        ttk.Label(grid, text="Current Range:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.dpv_current_range = ttk.Combobox(grid, width=12, values=["Auto", "100µA", "10µA", "1µA", "100nA"])
        self.dpv_current_range.set("Auto")
        self.dpv_current_range.grid(row=3, column=1, padx=5)
        
        # DPV Info - Compact
        info_frame = ttk.LabelFrame(self.dpv_frame, text="Method Info", padding="5")
        info_frame.pack(fill=tk.X, pady=2)
        
        dpv_info = """🔍 Differential Pulse Voltammetry: Enhanced sensitivity with voltage pulses
• Used for trace analysis and low concentrations"""
        
        ttk.Label(info_frame, text=dpv_info, justify=tk.LEFT, font=("Arial", 9)).pack(anchor="w")
        
    def setup_swv_tab(self):
        """Setup Square Wave Voltammetry tab"""
        # SWV Parameters - Compact
        params_frame = ttk.LabelFrame(self.swv_frame, text="SWV Parameters", padding="5")
        params_frame.pack(fill=tk.X, pady=2)
        
        # Grid layout for SWV parameters
        grid = ttk.Frame(params_frame)
        grid.pack(fill=tk.X)
        
        # Voltage parameters
        ttk.Label(grid, text="Start Voltage (V):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.swv_start_v = tk.StringVar(value="-0.5")
        ttk.Entry(grid, textvariable=self.swv_start_v, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(grid, text="End Voltage (V):").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.swv_end_v = tk.StringVar(value="0.5")
        ttk.Entry(grid, textvariable=self.swv_end_v, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(grid, text="Step Voltage (mV):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.swv_step_v = tk.StringVar(value="5")
        ttk.Entry(grid, textvariable=self.swv_step_v, width=10).grid(row=1, column=1, padx=5)
        
        ttk.Label(grid, text="SW Amplitude (mV):").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.swv_sw_amp = tk.StringVar(value="25")
        ttk.Entry(grid, textvariable=self.swv_sw_amp, width=10).grid(row=1, column=3, padx=5)
        
        ttk.Label(grid, text="SW Frequency (Hz):").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.swv_frequency = tk.StringVar(value="5")
        ttk.Entry(grid, textvariable=self.swv_frequency, width=10).grid(row=2, column=1, padx=5)
        
        # Current range
        ttk.Label(grid, text="Current Range:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        self.swv_current_range = ttk.Combobox(grid, width=12, values=["Auto", "100µA", "10µA", "1µA", "100nA"])
        self.swv_current_range.set("Auto")
        self.swv_current_range.grid(row=2, column=3, padx=5)
        
        # Preconcentration section - Compact layout
        precon_frame = ttk.LabelFrame(params_frame, text="Preconcentration (Optional)", padding="5")
        precon_frame.pack(fill=tk.X, pady=2)
        
        # Enable checkbox first
        self.swv_enable_precon = tk.BooleanVar(value=False)
        ttk.Checkbutton(precon_frame, text="Enable Preconcentration", 
                       variable=self.swv_enable_precon,
                       command=self.toggle_precon_controls).pack(anchor="w", pady=2)
        
        # Compact grid for precon parameters
        precon_grid = ttk.Frame(precon_frame)
        precon_grid.pack(fill=tk.X, pady=2)
        
        # Row 1: Potentials
        ttk.Label(precon_grid, text="Pot1(V):").grid(row=0, column=0, sticky="w", padx=2)
        self.swv_precon_pot1 = tk.StringVar(value="-1.9")
        self.precon_pot1_entry = ttk.Entry(precon_grid, textvariable=self.swv_precon_pot1, width=8, state="disabled")
        self.precon_pot1_entry.grid(row=0, column=1, padx=2)
        
        ttk.Label(precon_grid, text="Pot2(V):").grid(row=0, column=2, sticky="w", padx=2)
        self.swv_precon_pot2 = tk.StringVar(value="-0.5")
        self.precon_pot2_entry = ttk.Entry(precon_grid, textvariable=self.swv_precon_pot2, width=8, state="disabled")
        self.precon_pot2_entry.grid(row=0, column=3, padx=2)
        
        # Row 2: Times and Presets
        ttk.Label(precon_grid, text="Time(s):").grid(row=1, column=0, sticky="w", padx=2)
        self.swv_precon_time = tk.StringVar(value="60")
        self.precon_time_entry = ttk.Entry(precon_grid, textvariable=self.swv_precon_time, width=8, state="disabled")
        self.precon_time_entry.grid(row=1, column=1, padx=2)
        self.swv_precon_time.trace('w', self.update_precon_warning)
        
        ttk.Label(precon_grid, text="Equil(s):").grid(row=1, column=2, sticky="w", padx=2)
        self.swv_equil_time = tk.StringVar(value="10")
        self.equil_time_entry = ttk.Entry(precon_grid, textvariable=self.swv_equil_time, width=8, state="disabled")
        self.equil_time_entry.grid(row=1, column=3, padx=2)
        
        # Compact preset buttons
        preset_frame = ttk.Frame(precon_grid)
        preset_frame.grid(row=2, column=0, columnspan=4, pady=2)
        
        ttk.Button(preset_frame, text="60s", width=6,
                  command=lambda: self.set_precon_preset(60, 10)).pack(side=tk.LEFT, padx=1)
        ttk.Button(preset_frame, text="120s", width=6,
                  command=lambda: self.set_precon_preset(120, 15)).pack(side=tk.LEFT, padx=1)
        ttk.Button(preset_frame, text="240s", width=6,
                  command=lambda: self.set_precon_preset(240, 20)).pack(side=tk.LEFT, padx=1)
        ttk.Button(preset_frame, text="600s", width=6,
                  command=lambda: self.set_precon_preset(600, 30)).pack(side=tk.LEFT, padx=1)
        
        # Warning and progress - compact
        self.precon_warning = ttk.Label(precon_frame, text="⚠️  Long time", foreground="orange", font=("Arial", 8))
        self.precon_warning.pack(anchor="w")
        self.precon_warning.pack_forget()  # Hide initially
        
        # Progress indicator (initially hidden)
        self.progress_frame = ttk.Frame(precon_frame)
        self.progress_frame.pack(fill="x", pady=2)
        self.progress_frame.pack_forget()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate', length=200)
        self.progress_bar.pack(fill="x")
        self.progress_label = ttk.Label(self.progress_frame, text="", font=("Arial", 8))
        self.progress_label.pack()
        
        # Compact SWV Info
        info_frame = ttk.LabelFrame(self.swv_frame, text="Method Info", padding="5")
        info_frame.pack(fill=tk.X, pady=2)
        
        swv_info = """⚡ Square Wave Voltammetry: Fast scanning with high sensitivity
• Used for rapid analysis and kinetic studies"""
        
        ttk.Label(info_frame, text=swv_info, justify=tk.LEFT, font=("Arial", 9)).pack(anchor="w")
    
    def toggle_precon_controls(self):
        """Enable/disable preconcentration controls based on checkbox"""
        state = "normal" if self.swv_enable_precon.get() else "disabled"
        
        self.precon_pot1_entry.config(state=state)
        self.precon_pot2_entry.config(state=state)
        self.precon_time_entry.config(state=state)
        self.equil_time_entry.config(state=state)
        
        # Update warning visibility
        self.update_precon_warning()
    
    def update_precon_warning(self, *args):
        """Update preconcentration warning based on time settings"""
        if self.swv_enable_precon.get():
            try:
                precon_time = float(self.swv_precon_time.get())
                equil_time = float(self.swv_equil_time.get())
                total_time = precon_time + equil_time
                
                if total_time > 120:  # Show warning for total > 2 minutes
                    minutes = total_time / 60
                    self.precon_warning.config(text=f"⚠️  Total: {minutes:.1f}min")
                    self.precon_warning.pack(anchor="w", pady=2)
                else:
                    self.precon_warning.pack_forget()
            except ValueError:
                self.precon_warning.pack_forget()
        else:
            self.precon_warning.pack_forget()
    
    def set_precon_preset(self, precon_time, equil_time):
        """Set preconcentration preset values"""
        if self.swv_enable_precon.get():
            self.swv_precon_time.set(str(precon_time))
            self.swv_equil_time.set(str(equil_time))
            self.update_precon_warning()
    
    def show_progress_indicator(self, total_time):
        """Show progress indicator for long processes"""
        self.progress_frame.pack(fill="x", pady=2)
        self.progress_bar['maximum'] = total_time
        self.progress_bar['value'] = 0
        self.progress_label.config(text=f"Starting... (0/{total_time:.0f}s)")
    
    def update_progress(self, current_time, total_time, status=""):
        """Update progress indicator"""
        if hasattr(self, 'progress_bar'):
            self.progress_bar['value'] = current_time
            remaining = total_time - current_time
            progress_pct = (current_time / total_time) * 100
            self.progress_label.config(text=f"{status} {progress_pct:.0f}% ({remaining:.0f}s left)")
            self.root.update_idletasks()
    
    def hide_progress_indicator(self):
        """Hide progress indicator"""
        if hasattr(self, 'progress_frame'):
            self.progress_frame.pack_forget()
            
    def on_tab_changed(self, event):
        """Handle tab change event"""
        selection = event.widget.select()
        tab_text = event.widget.tab(selection, "text")
        
        if "CV" in tab_text:
            self.current_method = "CV"
        elif "DPV" in tab_text:
            self.current_method = "DPV"
        elif "SWV" in tab_text:
            self.current_method = "SWV"
            
        self.status_bar.config(text=f"Selected method: {self.current_method}")
        
    def check_dependencies(self):
        """Check if all dependencies are available"""
        self.log_output("🔍 Checking electrochemical methods...")
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.log_output(f"✅ Python {python_version}")
        
        # Check electrochemical functions
        if ELECTROCHEMICAL_FUNCTIONS_AVAILABLE:
            self.log_output("✅ Electrochemical methods available")
        else:
            self.log_output("❌ Electrochemical methods not available")
            
        # Check connection
        self.check_connection()
        
    def check_connection(self):
        """Check STM32 connection"""
        self.status_label.config(text="Checking...")
        self.refresh_btn.config(state="disabled")
        
        def check_thread():
            try:
                if ELECTROCHEMICAL_FUNCTIONS_AVAILABLE:
                    port = find_stm32_port()
                    if port and os.path.exists(port):
                        self.root.after(0, lambda: self.connection_result(True, port))
                    else:
                        self.root.after(0, lambda: self.connection_result(False, None))
                else:
                    self.root.after(0, lambda: self.connection_result(False, "No functions"))
            except Exception as e:
                self.root.after(0, lambda: self.connection_result(False, str(e)))
        
        threading.Thread(target=check_thread, daemon=True).start()
        
    def connection_result(self, success, info):
        """Handle connection check result"""
        if success:
            self.status_label.config(text=f"✅ Connected: {info}", foreground="green")
            self.start_btn.config(state="normal")
            self.status_bar.config(text=f"STM32 ready at {info}")
            self.log_output(f"✅ STM32 connected at {info}")
        else:
            self.status_label.config(text="❌ Not connected", foreground="red")
            self.start_btn.config(state="disabled")
            self.status_bar.config(text="STM32 not found")
            self.log_output(f"❌ STM32 connection failed: {info}")
            
        self.refresh_btn.config(state="normal")
        
    def get_current_parameters(self):
        """Get parameters for current method"""
        try:
            if self.current_method == "CV":
                return {
                    "start_voltage": float(self.cv_start_v.get()),
                    "end_voltage": float(self.cv_end_v.get()),
                    "scan_rate": float(self.cv_scan_rate.get()),
                    "cycles": int(self.cv_cycles.get()),
                    "current_range": self.cv_current_range.get()
                }
            elif self.current_method == "DPV":
                return {
                    "start_voltage": float(self.dpv_start_v.get()),
                    "end_voltage": float(self.dpv_end_v.get()),
                    "step_voltage": float(self.dpv_step_v.get()) / 1000,  # mV to V
                    "pulse_amplitude": float(self.dpv_pulse_amp.get()) / 1000,  # mV to V
                    "pulse_width": float(self.dpv_pulse_width.get()) / 1000,  # ms to s
                    "sample_width": float(self.dpv_sample_width.get()) / 1000,  # ms to s
                    "current_range": self.dpv_current_range.get()
                }
            elif self.current_method == "SWV":
                params = {
                    "start_voltage": float(self.swv_start_v.get()),
                    "end_voltage": float(self.swv_end_v.get()),
                    "step_voltage": float(self.swv_step_v.get()) / 1000,  # mV to V
                    "sw_amplitude": float(self.swv_sw_amp.get()) / 1000,  # mV to V
                    "sw_frequency": float(self.swv_frequency.get()),
                    "current_range": self.swv_current_range.get(),
                    "enable_precon": 1 if self.swv_enable_precon.get() else 0,
                    "precon_pot1": float(self.swv_precon_pot1.get()),
                    "precon_pot2": float(self.swv_precon_pot2.get()),
                    "precon_time": float(self.swv_precon_time.get()),
                    "equil_time": float(self.swv_equil_time.get())
                }
                return params
        except ValueError as e:
            raise ValueError(f"Invalid parameter values: {e}")
            
    def validate_parameters(self):
        """Validate current method parameters"""
        try:
            params = self.get_current_parameters()
            
            # Common validations
            if abs(params["start_voltage"]) > 2.5 or abs(params["end_voltage"]) > 2.5:
                raise ValueError("Voltage range must be within ±2.5V")
                
            if self.current_method == "CV":
                if params["scan_rate"] <= 0 or params["scan_rate"] > 10000:
                    raise ValueError("Scan rate must be between 0-10000 mV/s")
                if params["cycles"] <= 0 or params["cycles"] > 100:
                    raise ValueError("Cycles must be between 1-100")
                    
            elif self.current_method == "DPV":
                if params["step_voltage"] <= 0 or params["step_voltage"] > 0.1:
                    raise ValueError("Step voltage must be between 0-100 mV")
                if params["pulse_amplitude"] <= 0 or params["pulse_amplitude"] > 0.5:
                    raise ValueError("Pulse amplitude must be between 0-500 mV")
                if params["pulse_width"] < 0.01 or params["pulse_width"] > 1.0:
                    raise ValueError("Pulse width must be between 10-1000 ms")
                    
            elif self.current_method == "SWV":
                if params["step_voltage"] <= 0 or params["step_voltage"] > 0.1:
                    raise ValueError("Step voltage must be between 0-100 mV")
                if params["sw_amplitude"] <= 0 or params["sw_amplitude"] > 0.5:
                    raise ValueError("SW amplitude must be between 0-500 mV")
                if params["sw_frequency"] < 1 or params["sw_frequency"] > 1000:
                    raise ValueError("SW frequency must be between 1-1000 Hz")
                    
            return True, params
            
        except ValueError as e:
            return False, str(e)
            
    def start_measurement(self):
        """Start electrochemical measurement"""
        # Validate parameters
        valid, result = self.validate_parameters()
        if not valid:
            messagebox.showerror("Parameter Error", f"Invalid parameters:\n{result}")
            return
            
        self.log_output(f"🚀 Starting {self.current_method} measurement...")
        self.log_output(f"📊 Method: {self.current_method}")
        
        # Log parameters
        for key, value in result.items():
            if isinstance(value, float):
                self.log_output(f"   {key}: {value:.3f}")
            else:
                self.log_output(f"   {key}: {value}")
        
        self.start_measurement_process(result)
        
    def start_measurement_process(self, params):
        """Start measurement process"""
        if self.measurement_process and self.measurement_process.poll() is None:
            self.log_output("⚠️ Measurement already running")
            return
            
        self.progress.start()
        self.stop_btn.config(state="normal")
        self.start_btn.config(state="disabled")
        
        # Show progress indicator for SWV with preconcentration
        if self.current_method == "SWV" and params.get('enable_precon', 0):
            total_precon_time = params.get('precon_time', 60) + params.get('equil_time', 10)
            self.show_progress_indicator(total_precon_time)
            self.log_output(f"⏳ Starting SWV with {total_precon_time:.0f}s preconcentration...")
        
        # Start measurement process
        def run_measurement():
            try:
                # Set environment variables and command based on method
                if self.current_method == "CV":
                    env_vars = {
                        'CV_START_V': str(params.get('start_voltage', 0)),
                        'CV_END_V': str(params.get('end_voltage', 0)),
                        'CV_SCAN_RATE': str(params.get('scan_rate', 100)),
                        'CV_CYCLES': str(params.get('cycles', 1))
                    }
                    cmd = [sys.executable, "test_cv_final.py"]
                    
                elif self.current_method == "DPV":
                    env_vars = {
                        'DPV_START_V': str(params.get('start_voltage', -0.5)),
                        'DPV_END_V': str(params.get('end_voltage', 0.5)),
                        'DPV_PULSE_AMP': str(params.get('pulse_amplitude', 0.05)),
                        'DPV_STEP_V': str(params.get('step_voltage', 0.01)),
                        'DPV_PULSE_WIDTH': str(params.get('pulse_width', 0.05)),
                        'DPV_SAMPLE_WIDTH': str(params.get('sample_width', 0.1))
                    }
                    cmd = [sys.executable, "test_dpv_plot.py"]
                    
                elif self.current_method == "SWV":
                    env_vars = {
                        'SWV_START_V': str(params.get('start_voltage', -0.5)),
                        'SWV_END_V': str(params.get('end_voltage', 0.5)),
                        'SWV_STEP_V': str(params.get('step_voltage', 0.005)),
                        'SWV_AMPLITUDE': str(params.get('sw_amplitude', 0.05)),
                        'SWV_FREQUENCY': str(params.get('sw_frequency', 5)),
                        'SWV_ENABLE_PRECON': str(params.get('enable_precon', 0)),
                        'SWV_PRECON_POT1': str(params.get('precon_pot1', -1.9)),
                        'SWV_PRECON_POT2': str(params.get('precon_pot2', -0.5)),
                        'SWV_PRECON_TIME': str(params.get('precon_time', 60)),
                        'SWV_EQUIL_TIME': str(params.get('equil_time', 10))
                    }
                    cmd = [sys.executable, "test_swv_simple.py"]
                else:
                    raise ValueError(f"Unknown method: {self.current_method}")
                
                env_vars['ELECTROCHEMICAL_METHOD'] = self.current_method
                
                self.measurement_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    env=dict(os.environ, **env_vars)
                )
                
                # Read output line by line
                for line in iter(self.measurement_process.stdout.readline, ''):
                    if line:
                        line_stripped = line.strip()
                        self.root.after(0, lambda msg=line_stripped: self.log_output(msg))
                        
                        # Parse progress for SWV preconcentration
                        if self.current_method == "SWV" and "PRECON_PROGRESS" in line_stripped:
                            try:
                                # Parse: PRECON_PROGRESS,STEP1,30.0,240.0
                                parts = line_stripped.split(',')
                                if len(parts) >= 4:
                                    current_time = float(parts[2])
                                    total_time = float(parts[3])
                                    self.root.after(0, lambda c=current_time, t=total_time: 
                                                   self.update_progress(c, t, "Preconcentration:"))
                            except (ValueError, IndexError):
                                pass
                        elif "PRECON_FINISHED" in line_stripped:
                            self.root.after(0, self.hide_progress_indicator)
                
                self.measurement_process.wait()
                self.root.after(0, self.measurement_finished)
                
            except Exception as e:
                self.root.after(0, lambda: self.log_output(f"❌ Error: {e}"))
                self.root.after(0, self.measurement_finished)
        
        threading.Thread(target=run_measurement, daemon=True).start()
        
    def stop_measurement(self):
        """Stop measurement"""
        if self.measurement_process and self.measurement_process.poll() is None:
            self.log_output("⏹️ Stopping measurement...")
            
            try:
                if sys.platform == "win32":
                    self.measurement_process.terminate()
                else:
                    os.killpg(os.getpgid(self.measurement_process.pid), signal.SIGTERM)
                    
                self.measurement_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log_output("⚠️ Force killing process...")
                self.measurement_process.kill()
            except Exception as e:
                self.log_output(f"❌ Error stopping: {e}")
                
        self.measurement_finished()
        
    def measurement_finished(self):
        """Clean up after measurement"""
        self.progress.stop()
        self.stop_btn.config(state="disabled")
        self.start_btn.config(state="normal")
        self.status_bar.config(text=f"{self.current_method} measurement finished")
        self.log_output(f"✅ {self.current_method} measurement completed")
        self.hide_progress_indicator()  # Hide progress indicator
        
    def export_data(self):
        """Export measurement data"""
        self.log_output("💾 Export functionality will be implemented...")
        messagebox.showinfo("Export", f"Data export for {self.current_method} will be available soon!")
        
    def log_output(self, message):
        """Add message to output text"""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.output_text.insert(tk.END, full_message)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def on_closing(self):
        """Handle application closing"""
        if self.measurement_process and self.measurement_process.poll() is None:
            if messagebox.askokcancel("Quit", "Measurement is running. Stop and quit?"):
                self.stop_measurement()
                self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()

def main():
    """Main function"""
    print("🚀 Starting H743 Potentiostat - Complete Electrochemical Methods...")
    
    # Check if we can create GUI
    try:
        root = tk.Tk()
        app = ElectrochemicalApp(root)
        
        print("✅ Electrochemical Methods GUI started successfully")
        print("🧪 Ready for CV, DPV, SWV measurements")
        
        # Start GUI event loop
        root.mainloop()
        
    except Exception as e:
        print(f"❌ GUI error: {e}")
        print("💡 Make sure DISPLAY is set for GUI applications")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
