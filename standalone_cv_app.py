#!/usr/bin/env python3
"""
H743 Potentiostat Standalone GUI Application
===========================================
Standalone CV measurement application with GUI interface
No dependency on VS Code or external terminals
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

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from test_cv_final import find_stm32_port
    CV_FUNCTIONS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: CV functions not available: {e}")
    CV_FUNCTIONS_AVAILABLE = False

class StandaloneApp:
    def __init__(self, root):
        self.root = root
        self.root.title("H743 Potentiostat - Standalone")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Process management
        self.cv_process = None
        self.output_queue = queue.Queue()
        
        self.setup_gui()
        self.check_dependencies()
        
    def setup_gui(self):
        """Setup the GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="🧪 H743 Potentiostat", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        subtitle_label = ttk.Label(main_frame, text="Standalone CV Measurement Tool", 
                                  font=("Arial", 12))
        subtitle_label.pack(pady=5)
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Device Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(conn_frame, text="Checking connection...")
        self.status_label.pack(side=tk.LEFT)
        
        self.refresh_btn = ttk.Button(conn_frame, text="🔄 Refresh", 
                                     command=self.check_connection)
        self.refresh_btn.pack(side=tk.RIGHT)
        
        # CV Parameters frame
        params_frame = ttk.LabelFrame(main_frame, text="CV Parameters", padding="10")
        params_frame.pack(fill=tk.X, pady=10)
        
        # Create parameter input grid
        params_grid = ttk.Frame(params_frame)
        params_grid.pack(fill=tk.X)
        
        # Voltage parameters
        ttk.Label(params_grid, text="Start Voltage (V):").grid(row=0, column=0, sticky="w", padx=5)
        self.start_v_var = tk.StringVar(value="1.0")
        self.start_v_entry = ttk.Entry(params_grid, textvariable=self.start_v_var, width=8)
        self.start_v_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(params_grid, text="End Voltage (V):").grid(row=0, column=2, sticky="w", padx=5)
        self.end_v_var = tk.StringVar(value="-1.0")
        self.end_v_entry = ttk.Entry(params_grid, textvariable=self.end_v_var, width=8)
        self.end_v_entry.grid(row=0, column=3, padx=5)
        
        ttk.Label(params_grid, text="Scan Rate (mV/s):").grid(row=0, column=4, sticky="w", padx=5)
        self.scan_rate_var = tk.StringVar(value="100")
        self.scan_rate_entry = ttk.Entry(params_grid, textvariable=self.scan_rate_var, width=8)
        self.scan_rate_entry.grid(row=0, column=5, padx=5)
        
        # Additional parameters
        ttk.Label(params_grid, text="Cycles:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.cycles_var = tk.StringVar(value="1")
        self.cycles_entry = ttk.Entry(params_grid, textvariable=self.cycles_var, width=8)
        self.cycles_entry.grid(row=1, column=1, padx=5)
        
        ttk.Label(params_grid, text="Step Size (mV):").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.step_size_var = tk.StringVar(value="10")
        self.step_size_entry = ttk.Entry(params_grid, textvariable=self.step_size_var, width=8)
        self.step_size_entry.grid(row=1, column=3, padx=5)
        
        ttk.Label(params_grid, text="Sample Interval (ms):").grid(row=1, column=4, sticky="w", padx=5, pady=5)
        self.sample_interval_var = tk.StringVar(value="100")
        self.sample_interval_entry = ttk.Entry(params_grid, textvariable=self.sample_interval_var, width=8)
        self.sample_interval_entry.grid(row=1, column=5, padx=5)
        
        # Preset buttons
        preset_frame = ttk.Frame(params_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(preset_frame, text="🔧 Standard", command=self.load_standard_preset, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="⚡ Fast Scan", command=self.load_fast_preset, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="🐌 Slow Scan", command=self.load_slow_preset, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="🔄 Reset", command=self.reset_parameters, width=12).pack(side=tk.RIGHT, padx=2)
        
        # Control buttons frame
        control_frame = ttk.LabelFrame(main_frame, text="CV Measurements", padding="10")
        control_frame.pack(fill=tk.X, pady=10)
        
        # Buttons
        self.single_cv_btn = ttk.Button(control_frame, text="🔬 Run Single CV Test", 
                                       command=self.run_single_cv, width=20)
        self.single_cv_btn.pack(side=tk.LEFT, padx=5)
        
        self.multi_cv_btn = ttk.Button(control_frame, text="📊 Multi-Rate CV Test", 
                                      command=self.run_multi_cv, width=20)
        self.multi_cv_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ Stop", 
                                  command=self.stop_measurement, width=15)
        self.stop_btn.pack(side=tk.RIGHT, padx=5)
        self.stop_btn.config(state="disabled")
        
        # Output frame
        output_frame = ttk.LabelFrame(main_frame, text="Output", padding="10")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Text output with scrollbar
        self.output_text = scrolledtext.ScrolledText(output_frame, height=15, 
                                                    font=("Consolas", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def check_dependencies(self):
        """Check if all dependencies are available"""
        self.log_output("🔍 Checking dependencies...")
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.log_output(f"✅ Python {python_version}")
        
        # Check CV functions
        if CV_FUNCTIONS_AVAILABLE:
            self.log_output("✅ CV functions available")
        else:
            self.log_output("❌ CV functions not available")
            
        # Check connection
        self.check_connection()
        
    def check_connection(self):
        """Check STM32 connection"""
        self.status_label.config(text="Checking...")
        self.refresh_btn.config(state="disabled")
        
        def check_thread():
            try:
                if CV_FUNCTIONS_AVAILABLE:
                    port = find_stm32_port()
                    if port and os.path.exists(port):
                        self.root.after(0, lambda: self.connection_result(True, port))
                    else:
                        self.root.after(0, lambda: self.connection_result(False, None))
                else:
                    self.root.after(0, lambda: self.connection_result(False, "No CV functions"))
            except Exception as e:
                self.root.after(0, lambda: self.connection_result(False, str(e)))
        
        threading.Thread(target=check_thread, daemon=True).start()
        
    def connection_result(self, success, info):
        """Handle connection check result"""
        if success:
            self.status_label.config(text=f"✅ Connected: {info}", foreground="green")
            self.single_cv_btn.config(state="normal")
            self.multi_cv_btn.config(state="normal")
            self.status_bar.config(text=f"STM32 ready at {info}")
            self.log_output(f"✅ STM32 connected at {info}")
        else:
            self.status_label.config(text="❌ Not connected", foreground="red")
            self.single_cv_btn.config(state="disabled")
            self.multi_cv_btn.config(state="disabled")
            self.status_bar.config(text="STM32 not found")
            self.log_output(f"❌ STM32 connection failed: {info}")
            
        self.refresh_btn.config(state="normal")
    
    def load_standard_preset(self):
        """Load standard CV parameters"""
        self.start_v_var.set("1.0")
        self.end_v_var.set("-1.0")
        self.scan_rate_var.set("100")
        self.cycles_var.set("1")
        self.step_size_var.set("10")
        self.sample_interval_var.set("100")
        self.log_output("📋 Loaded standard CV preset")
        
    def load_fast_preset(self):
        """Load fast scan CV parameters"""
        self.start_v_var.set("1.0")
        self.end_v_var.set("-1.0")
        self.scan_rate_var.set("400")
        self.cycles_var.set("1")
        self.step_size_var.set("20")
        self.sample_interval_var.set("50")
        self.log_output("⚡ Loaded fast scan preset")
        
    def load_slow_preset(self):
        """Load slow scan CV parameters"""
        self.start_v_var.set("1.0")
        self.end_v_var.set("-1.0")
        self.scan_rate_var.set("20")
        self.cycles_var.set("3")
        self.step_size_var.set("5")
        self.sample_interval_var.set("250")
        self.log_output("🐌 Loaded slow scan preset")
        
    def reset_parameters(self):
        """Reset to default parameters"""
        self.load_standard_preset()
        
    def validate_parameters(self):
        """Validate CV parameters"""
        try:
            start_v = float(self.start_v_var.get())
            end_v = float(self.end_v_var.get())
            scan_rate = float(self.scan_rate_var.get())
            cycles = int(self.cycles_var.get())
            step_size = float(self.step_size_var.get())
            sample_interval = float(self.sample_interval_var.get())
            
            # Validation rules
            if abs(start_v) > 3.0 or abs(end_v) > 3.0:
                raise ValueError("Voltage range must be within ±3.0V")
            if scan_rate <= 0 or scan_rate > 1000:
                raise ValueError("Scan rate must be between 0-1000 mV/s")
            if cycles <= 0 or cycles > 10:
                raise ValueError("Cycles must be between 1-10")
            if step_size <= 0 or step_size > 100:
                raise ValueError("Step size must be between 0-100 mV")
            if sample_interval < 10 or sample_interval > 10000:
                raise ValueError("Sample interval must be between 10-10000 ms")
                
            return True, {
                'start_v': start_v,
                'end_v': end_v,
                'scan_rate': scan_rate,
                'cycles': cycles,
                'step_size': step_size,
                'sample_interval': sample_interval
            }
            
        except ValueError as e:
            return False, str(e)
        
    def get_cv_parameters_text(self):
        """Get formatted CV parameters text"""
        _, params = self.validate_parameters()
        if isinstance(params, dict):
            return (f"Parameters: {params['start_v']}V → {params['end_v']}V, "
                   f"{params['scan_rate']} mV/s, {params['cycles']} cycles, "
                   f"{params['step_size']} mV steps, {params['sample_interval']} ms interval")
        return "Invalid parameters"
        
    def log_output(self, message):
        """Add message to output text"""
        timestamp = time.strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}\n"
        
        self.output_text.insert(tk.END, full_message)
        self.output_text.see(tk.END)
        self.root.update_idletasks()
        
    def run_single_cv(self):
        """Run single CV measurement"""
        # Validate parameters first
        valid, result = self.validate_parameters()
        if not valid:
            messagebox.showerror("Parameter Error", f"Invalid parameters:\n{result}")
            return
            
        self.log_output("🔬 Starting Single CV Test...")
        self.log_output(f"📊 {self.get_cv_parameters_text()}")
        self.start_cv_process(mode="single", params=result)
        
    def run_multi_cv(self):
        """Run multi-rate CV measurement"""
        # Validate parameters first
        valid, result = self.validate_parameters()
        if not valid:
            messagebox.showerror("Parameter Error", f"Invalid parameters:\n{result}")
            return
            
        # Show selection dialog first
        if self.show_scan_rate_dialog():
            self.log_output("📊 Starting Multi-Rate CV Test...")
            self.log_output(f"📊 Base parameters: {self.get_cv_parameters_text()}")
            self.start_cv_process(mode="multi", params=result)
        
    def show_scan_rate_dialog(self):
        """Show scan rate selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Scan Rates")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        result = {"selected": False}
        
        # Title
        ttk.Label(dialog, text="Select Scan Rates (mV/s)", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Scan rate options
        rates_frame = ttk.Frame(dialog)
        rates_frame.pack(pady=10)
        
        scan_rates = [10, 20, 50, 100, 200, 400]
        scan_vars = {}
        
        for i, rate in enumerate(scan_rates):
            row = i // 2
            col = i % 2
            
            var = tk.BooleanVar()
            scan_vars[rate] = var
            
            cb = ttk.Checkbutton(rates_frame, text=f"{rate} mV/s", variable=var)
            cb.grid(row=row, column=col, sticky="w", padx=10, pady=2)
        
        # Default selection
        scan_vars[100].set(True)
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        
        def on_ok():
            selected = [rate for rate, var in scan_vars.items() if var.get()]
            if selected:
                result["selected"] = True
                result["rates"] = selected
                self.log_output(f"📊 Selected scan rates: {selected} mV/s")
            dialog.destroy()
            
        def on_cancel():
            dialog.destroy()
            
        ttk.Button(btn_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        return result.get("selected", False)
        
    def start_cv_process(self, mode="single", params=None):
        """Start CV measurement process"""
        if self.cv_process and self.cv_process.poll() is None:
            self.log_output("⚠️ CV process already running")
            return
            
        self.progress.start()
        self.stop_btn.config(state="normal")
        self.single_cv_btn.config(state="disabled")
        self.multi_cv_btn.config(state="disabled")
        
        # Start CV process
        def run_cv():
            try:
                # Create temporary parameter file
                if params:
                    param_file = "/tmp/cv_params.txt"
                    with open(param_file, 'w') as f:
                        f.write(f"START_V={params['start_v']}\n")
                        f.write(f"END_V={params['end_v']}\n")
                        f.write(f"SCAN_RATE={params['scan_rate']}\n")
                        f.write(f"CYCLES={params['cycles']}\n")
                        f.write(f"STEP_SIZE={params['step_size']}\n")
                        f.write(f"SAMPLE_INTERVAL={params['sample_interval']}\n")
                        
                if mode == "single":
                    cmd = [sys.executable, "test_cv_final.py"]
                    if params:
                        cmd.extend(["--params", param_file])
                else:
                    cmd = [sys.executable, "test_cv_final.py"]
                    if params:
                        cmd.extend(["--params", param_file])
                
                self.cv_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    env=dict(os.environ, **{
                        'CV_START_V': str(params.get('start_v', 1.0)) if params else '1.0',
                        'CV_END_V': str(params.get('end_v', -1.0)) if params else '-1.0',
                        'CV_SCAN_RATE': str(params.get('scan_rate', 100)) if params else '100',
                        'CV_CYCLES': str(params.get('cycles', 1)) if params else '1',
                        'CV_STEP_SIZE': str(params.get('step_size', 10)) if params else '10',
                        'CV_SAMPLE_INTERVAL': str(params.get('sample_interval', 100)) if params else '100'
                    })
                )
                
                # Read output line by line
                for line in iter(self.cv_process.stdout.readline, ''):
                    if line:
                        self.root.after(0, lambda msg=line.strip(): self.log_output(msg))
                
                self.cv_process.wait()
                self.root.after(0, self.measurement_finished)
                
            except Exception as e:
                self.root.after(0, lambda: self.log_output(f"❌ Error: {e}"))
                self.root.after(0, self.measurement_finished)
        
        threading.Thread(target=run_cv, daemon=True).start()
        
    def stop_measurement(self):
        """Stop CV measurement"""
        if self.cv_process and self.cv_process.poll() is None:
            self.log_output("⏹️ Stopping measurement...")
            
            try:
                # Send interrupt signal
                if sys.platform == "win32":
                    self.cv_process.terminate()
                else:
                    os.killpg(os.getpgid(self.cv_process.pid), signal.SIGTERM)
                    
                self.cv_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log_output("⚠️ Force killing process...")
                self.cv_process.kill()
            except Exception as e:
                self.log_output(f"❌ Error stopping: {e}")
                
        self.measurement_finished()
        
    def measurement_finished(self):
        """Clean up after measurement"""
        self.progress.stop()
        self.stop_btn.config(state="disabled")
        self.single_cv_btn.config(state="normal")
        self.multi_cv_btn.config(state="normal")
        self.status_bar.config(text="Measurement finished")
        self.log_output("✅ Measurement completed")
        
    def on_closing(self):
        """Handle application closing"""
        if self.cv_process and self.cv_process.poll() is None:
            if messagebox.askokcancel("Quit", "CV measurement is running. Stop and quit?"):
                self.stop_measurement()
                self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()

def main():
    """Main function"""
    print("🚀 Starting H743 Potentiostat Standalone App...")
    
    # Check if we can create GUI
    try:
        root = tk.Tk()
        app = StandaloneApp(root)
        
        print("✅ GUI started successfully")
        print("🖥️ Use the GUI to run CV measurements")
        
        # Start GUI event loop
        root.mainloop()
        
    except Exception as e:
        print(f"❌ GUI error: {e}")
        print("💡 Make sure DISPLAY is set for GUI applications")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
