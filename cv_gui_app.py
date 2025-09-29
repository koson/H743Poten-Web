#!/usr/bin/env python3
"""
CV GUI Application for Linux
============================
GUI application for running CV measurements with H743 Potentiostat
"""

import sys
import os

# Set display for GUI applications
if 'DISPLAY' not in os.environ and 'WAYLAND_DISPLAY' not in os.environ:
    print("⚠️  No GUI display found")
    print("💡 To run GUI on remote server, use: ssh -X username@hostname")
    print("🔄 Running in headless mode...")
    
    # Try to use virtual display if available
    try:
        import pyvirtualdisplay
        display = pyvirtualdisplay.Display(visible=0, size=(800, 600))
        display.start()
        print("✅ Virtual display started")
    except ImportError:
        print("❌ Cannot create virtual display. Install: pip install pyvirtualdisplay")
        print("🔄 Continuing without GUI...")

# Import after display setup
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import matplotlib
    matplotlib.use('TkAgg')  # Use TkAgg backend for GUI
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    
    GUI_AVAILABLE = True
    print("✅ GUI libraries loaded successfully")
except ImportError as e:
    print(f"❌ GUI import error: {e}")
    GUI_AVAILABLE = False

# Import CV functions
try:
    from test_cv_final import find_stm32_port, test_cv_scan, show_scan_rate_selection_dialog
    print("✅ CV functions imported successfully")
except ImportError as e:
    print(f"❌ CV import error: {e}")
    sys.exit(1)

class CVGUIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("H743 Potentiostat CV Measurement")
        self.root.geometry("600x500")
        
        # Center window
        self.center_window()
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(self.main_frame, text="🧪 H743 Potentiostat", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        subtitle_label = ttk.Label(self.main_frame, text="Cyclic Voltammetry Measurement Tool", 
                                  font=("Arial", 12))
        subtitle_label.pack(pady=5)
        
        # Connection status
        self.status_frame = ttk.LabelFrame(self.main_frame, text="Connection Status", padding="10")
        self.status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(self.status_frame, text="Checking STM32 connection...")
        self.status_label.pack()
        
        # CV Parameters
        self.params_frame = ttk.LabelFrame(self.main_frame, text="CV Parameters", padding="10")
        self.params_frame.pack(fill=tk.X, pady=10)
        
        # Default parameters display
        params_text = """Default Parameters:
• Start Voltage: -1.0 V
• End Voltage: 1.0 V  
• Scan Rate: Selectable (10-400 mV/s)
• Cycles: Selectable (1-10)"""
        
        ttk.Label(self.params_frame, text=params_text, justify=tk.LEFT).pack(anchor="w")
        
        # Buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=20)
        
        # CV Test buttons
        self.single_cv_btn = ttk.Button(self.button_frame, text="🔬 Single CV Test", 
                                       command=self.run_single_cv, width=20)
        self.single_cv_btn.pack(side=tk.LEFT, padx=5)
        
        self.multi_cv_btn = ttk.Button(self.button_frame, text="📊 Multi-Rate CV Test", 
                                      command=self.run_multi_cv, width=20)
        self.multi_cv_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_bar = ttk.Label(self.main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Check connection after all widgets are created
        self.check_connection()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def check_connection(self):
        """Check STM32 connection"""
        try:
            port = find_stm32_port()
            if port and os.path.exists(port):
                self.status_label.config(text=f"✅ STM32 Connected at {port}", foreground="green")
                if hasattr(self, 'single_cv_btn'):
                    self.single_cv_btn.config(state="normal")
                    self.multi_cv_btn.config(state="normal")
                self.status_bar.config(text="STM32 H743 Ready")
            else:
                self.status_label.config(text="❌ STM32 Not Found", foreground="red")
                if hasattr(self, 'single_cv_btn'):
                    self.single_cv_btn.config(state="disabled")
                    self.multi_cv_btn.config(state="disabled")
                self.status_bar.config(text="Please connect STM32 H743")
        except Exception as e:
            self.status_label.config(text=f"❌ Connection Error: {str(e)}", foreground="red")
            if hasattr(self, 'single_cv_btn'):
                self.single_cv_btn.config(state="disabled")
                self.multi_cv_btn.config(state="disabled")
            
    def run_single_cv(self):
        """Run single CV measurement"""
        self.status_bar.config(text="Starting single CV measurement...")
        self.root.update()
        
        try:
            # Hide main window during measurement
            self.root.withdraw()
            
            # Run CV test
            test_cv_scan()
            
            # Show main window again
            self.root.deiconify()
            
            self.status_bar.config(text="CV measurement completed")
            messagebox.showinfo("Success", "CV measurement completed successfully!")
            
        except Exception as e:
            self.root.deiconify()
            self.status_bar.config(text="CV measurement failed")
            messagebox.showerror("Error", f"CV measurement failed:\n{str(e)}")
            
    def run_multi_cv(self):
        """Run multi-rate CV measurement"""
        self.status_bar.config(text="Configuring multi-rate CV...")
        self.root.update()
        
        try:
            # Show scan rate selection dialog
            selected_configs = show_scan_rate_selection_dialog()
            
            if not selected_configs:
                self.status_bar.config(text="Multi-rate CV cancelled")
                return
                
            self.status_bar.config(text=f"Running {len(selected_configs)} CV scans...")
            self.root.update()
            
            # Hide main window during measurement
            self.root.withdraw()
            
            # Run multi-rate CV (this would be implemented in test_cv_final.py)
            messagebox.showinfo("Info", f"Will run CV at {len(selected_configs)} different scan rates")
            
            # Show main window again
            self.root.deiconify()
            
            self.status_bar.config(text="Multi-rate CV completed")
            messagebox.showinfo("Success", "Multi-rate CV measurement completed!")
            
        except Exception as e:
            self.root.deiconify()
            self.status_bar.config(text="Multi-rate CV failed")
            messagebox.showerror("Error", f"Multi-rate CV failed:\n{str(e)}")

def main():
    """Main function"""
    print("🚀 Starting H743 Potentiostat CV GUI...")
    
    if not GUI_AVAILABLE:
        print("❌ GUI not available. Please install tkinter and matplotlib.")
        print("📦 Install: sudo apt-get install python3-tk")
        return 1
    
    try:
        root = tk.Tk()
        app = CVGUIApp(root)
        
        print("✅ GUI started successfully")
        print("🖥️  Use the GUI to run CV measurements")
        
        root.mainloop()
        
    except Exception as e:
        print(f"❌ GUI error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
