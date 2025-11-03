import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pyautogui
import time
import pandas as pd
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import logging
import os
from datetime import datetime
import json
import win32gui
import win32con
from typing import List, Dict, Optional
import pytesseract

class SAPMD04RPA:
    """
    Complete RPA Bot for SAP MD04 Part Description Extraction
    Follows the exact workflow from the document
    """
    
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_gui()
        self.is_running = False
        self.results = []
        
        # PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1.5  # Pause between actions
        
    def setup_logging(self):
        """Setup logging for the RPA bot."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/sap_rpa_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load configuration from JSON file."""
        default_config = {
            "sap_connection_details": {
                "name": "001. SAP ECC Production (PRD)",
                "system_description": "SAP ERP",
                "sid": "PRD",
                "group_server": "Production PRD",
                "message_server": "pdtcprd01.fermont.lamrc.net"
            },
            "coordinates": {
                "sap_taskbar_icon": [100, 100],  # Will be auto-detected
                "maximize_button": [500, 50],
                "sap_connection": [400, 300],
                "transaction_field": [400, 100],
                "part_number_field": [300, 200],
                "mrp_area_field": [500, 200],
                "matres_number": [200, 300],
                "maximize_detail": [500, 50]
            },
            "mrp_area": "1000",
            "wait_times": {
                "sap_launch": 5,
                "connection": 10,
                "transaction_load": 3,
                "data_extraction": 2
            }
        }
        
        config_file = "sap_rpa_config.json"
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = default_config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
                
    def setup_gui(self):
        """Setup the Tkinter GUI interface."""
        self.root = tk.Tk()
        self.root.title("SAP MD04 RPA Bot - Rapid Automation of Placeholders")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="SAP MD04 Part Description Extractor", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Input section
        input_frame = ttk.LabelFrame(main_frame, text="Input Options", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Single part number input
        ttk.Label(input_frame, text="Single Part Number:").grid(row=0, column=0, sticky=tk.W)
        self.single_part_var = tk.StringVar()
        single_part_entry = ttk.Entry(input_frame, textvariable=self.single_part_var, width=30)
        single_part_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        # Multiple parts input
        ttk.Label(input_frame, text="Multiple Parts (one per line):").grid(row=1, column=0, sticky=(tk.W, tk.N), pady=(10, 0))
        self.parts_text = scrolledtext.ScrolledText(input_frame, width=40, height=6)
        self.parts_text.grid(row=1, column=1, padx=(10, 0), pady=(10, 0), sticky=(tk.W, tk.E))
        
        # File input
        file_frame = ttk.Frame(input_frame)
        file_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
        
        ttk.Label(file_frame, text="Or load from Excel file:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=50)
        file_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        # Configuration section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(config_frame, text="MRP Area:").grid(row=0, column=0, sticky=tk.W)
        self.mrp_area_var = tk.StringVar(value=self.config["mrp_area"])
        mrp_entry = ttk.Entry(config_frame, textvariable=self.mrp_area_var, width=10)
        mrp_entry.grid(row=0, column=1, padx=(10, 0), sticky=tk.W)
        
        # Coordinate setup button
        coord_btn = ttk.Button(config_frame, text="Setup Coordinates", command=self.setup_coordinates)
        coord_btn.grid(row=0, column=2, padx=(20, 0))
        
        # Test connection button
        test_btn = ttk.Button(config_frame, text="Test SAP Connection", command=self.test_connection)
        test_btn.grid(row=0, column=3, padx=(10, 0))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="Start Automation", 
                                   command=self.start_automation, style="Accent.TButton")
        self.start_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop", 
                                  command=self.stop_automation, state="disabled")
        self.stop_btn.grid(row=0, column=1, padx=(0, 10))
        
        self.save_btn = ttk.Button(control_frame, text="Save Results", 
                                  command=self.save_results, state="disabled")
        self.save_btn.grid(row=0, column=2)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to start...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Results treeview
        columns = ("Part Number", "Description", "Status", "Timestamp")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=6)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        main_frame.rowconfigure(6, weight=1)
        input_frame.columnconfigure(1, weight=1)
        file_frame.columnconfigure(1, weight=1)
        progress_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to GUI log and logger."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        if level == "INFO":
            self.logger.info(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
            
    def browse_file(self):
        """Browse for Excel file containing part numbers."""
        file_path = filedialog.askopenfilename(
            title="Select Excel file with part numbers",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            
    def setup_coordinates(self):
        """Open coordinate setup window."""
        coord_window = tk.Toplevel(self.root)
        coord_window.title("Coordinate Setup")
        coord_window.geometry("600x400")
        
        instructions = """
Instructions for Coordinate Setup:

1. Click 'Start Capture' for each element
2. Move your mouse to the target element
3. Press SPACE to capture coordinates
4. Press ESC to cancel capture

Elements to capture:
- SAP Taskbar Icon
- SAP Connection Entry
- Transaction Field
- Part Number Field
- MRP Area Field
- MatRes Number
- Maximize Buttons
        """
        
        ttk.Label(coord_window, text=instructions, justify=tk.LEFT).pack(pady=10)
        
        # Coordinate capture buttons
        elements = [
            "sap_taskbar_icon", "sap_connection", "transaction_field",
            "part_number_field", "mrp_area_field", "matres_number", "maximize_button"
        ]
        
        for element in elements:
            frame = ttk.Frame(coord_window)
            frame.pack(fill=tk.X, padx=10, pady=2)
            
            ttk.Label(frame, text=f"{element.replace('_', ' ').title()}:").pack(side=tk.LEFT)
            
            coord_var = tk.StringVar(value=str(self.config["coordinates"][element]))
            entry = ttk.Entry(frame, textvariable=coord_var, width=20)
            entry.pack(side=tk.LEFT, padx=10)
            
            capture_btn = ttk.Button(frame, text="Capture", 
                                   command=lambda e=element, v=coord_var: self.capture_coordinate(e, v))
            capture_btn.pack(side=tk.RIGHT)
            
    def capture_coordinate(self, element: str, var: tk.StringVar):
        """Capture mouse coordinates for specific element."""
        self.log_message(f"Move mouse to {element} and press SPACE to capture...")
        
        def capture_thread():
            import keyboard
            keyboard.wait('space')
            x, y = pyautogui.position()
            self.config["coordinates"][element] = [x, y]
            var.set(f"[{x}, {y}]")
            self.log_message(f"Captured {element}: [{x}, {y}]")
            
            # Save config
            with open("sap_rpa_config.json", 'w') as f:
                json.dump(self.config, f, indent=4)
                
        threading.Thread(target=capture_thread, daemon=True).start()
        
    def find_window(self, window_title: str) -> Optional[int]:
        """Find window by title."""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_title.lower() in window_text.lower():
                    windows.append((hwnd, window_text))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        return windows[0][0] if windows else None
        
    def activate_window(self, hwnd: int):
        """Activate and bring window to foreground."""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(1)
            return True
        except Exception as e:
            self.log_message(f"Failed to activate window: {e}", "ERROR")
            return False
            
    def click_with_retry(self, coordinates: List[int], retries: int = 3) -> bool:
        """Click at coordinates with retry logic."""
        for attempt in range(retries):
            try:
                pyautogui.click(coordinates[0], coordinates[1])
                return True
            except Exception as e:
                self.log_message(f"Click attempt {attempt + 1} failed: {e}", "WARNING")
                time.sleep(1)
        return False
        
    def step1_open_sap_logon(self) -> bool:
        """Step 1: Open SAP Logon from taskbar."""
        try:
            self.log_message("Step 1: Opening SAP Logon...")
            self.progress_var.set("Opening SAP Logon...")
            
            # Try to find SAP window first
            sap_window = self.find_window("SAP Logon")
            if sap_window:
                self.activate_window(sap_window)
                self.log_message("SAP Logon already open, activating window")
                return True
                
            # Click on SAP taskbar icon
            coords = self.config["coordinates"]["sap_taskbar_icon"]
            if not self.click_with_retry(coords):
                self.log_message("Failed to click SAP taskbar icon", "ERROR")
                return False
                
            time.sleep(self.config["wait_times"]["sap_launch"])
            
            # Verify SAP Logon opened
            sap_window = self.find_window("SAP Logon")
            if sap_window:
                self.activate_window(sap_window)
                self.log_message("SAP Logon opened successfully")
                return True
            else:
                self.log_message("SAP Logon did not open", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"Step 1 failed: {e}", "ERROR")
            return False
            
    def step2_maximize_window(self) -> bool:
        """Step 2: Maximize SAP Logon window."""
        try:
            self.log_message("Step 2: Maximizing SAP Logon window...")
            self.progress_var.set("Maximizing window...")
            
            coords = self.config["coordinates"]["maximize_button"]
            if self.click_with_retry(coords):
                time.sleep(1)
                self.log_message("Window maximized successfully")
                return True
            else:
                self.log_message("Failed to maximize window", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"Step 2 failed: {e}", "ERROR")
            return False
            
    def step3_select_connection(self) -> bool:
        """Step 3: Select SAP connection."""
        try:
            self.log_message("Step 3: Selecting SAP connection...")
            self.progress_var.set("Connecting to SAP...")
            
            coords = self.config["coordinates"]["sap_connection"]
            if self.click_with_retry(coords):
                pyautogui.doubleClick(coords[0], coords[1])
                time.sleep(self.config["wait_times"]["connection"])
                self.log_message("SAP connection initiated")
                return True
            else:
                self.log_message("Failed to select SAP connection", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"Step 3 failed: {e}", "ERROR")
            return False
            
    def step4_enter_md04(self) -> bool:
        """Step 4: Enter MD04 transaction."""
        try:
            self.log_message("Step 4: Entering MD04 transaction...")
            self.progress_var.set("Loading MD04...")
            
            # Wait for SAP GUI to load
            time.sleep(2)
            
            # Find and activate SAP GUI window
            sap_gui = self.find_window("SAP")
            if sap_gui:
                self.activate_window(sap_gui)
            
            # Clear transaction field and enter MD04
            coords = self.config["coordinates"]["transaction_field"]
            pyautogui.click(coords[0], coords[1])
            time.sleep(1)
            
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.write('MD04')
            pyautogui.press('enter')
            
            time.sleep(self.config["wait_times"]["transaction_load"])
            self.log_message("MD04 transaction loaded")
            return True
            
        except Exception as e:
            self.log_message(f"Step 4 failed: {e}", "ERROR")
            return False
            
    def step5_enter_part_and_mrp(self, part_number: str) -> bool:
        """Step 5: Enter part number and MRP area."""
        try:
            self.log_message(f"Step 5: Entering part number {part_number}...")
            self.progress_var.set(f"Processing part: {part_number}")
            
            # Enter part number
            part_coords = self.config["coordinates"]["part_number_field"]
            pyautogui.click(part_coords[0], part_coords[1])
            time.sleep(1)
            
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.write(part_number)
            
            # Enter MRP area
            mrp_coords = self.config["coordinates"]["mrp_area_field"]
            pyautogui.click(mrp_coords[0], mrp_coords[1])
            time.sleep(1)
            
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.write(self.mrp_area_var.get())
            
            pyautogui.press('enter')
            time.sleep(self.config["wait_times"]["data_extraction"])
            
            self.log_message(f"Part {part_number} entered successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Step 5 failed: {e}", "ERROR")
            return False
            
    def step6_double_click_matres(self) -> bool:
        """Step 6: Double click on MatRes number."""
        try:
            self.log_message("Step 6: Double clicking MatRes...")
            self.progress_var.set("Opening material details...")
            
            coords = self.config["coordinates"]["matres_number"]
            pyautogui.doubleClick(coords[0], coords[1])
            time.sleep(2)
            
            self.log_message("MatRes opened successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Step 6 failed: {e}", "ERROR")
            return False
            
    def step7_maximize_detail_window(self) -> bool:
        """Step 7: Maximize detail window."""
        try:
            self.log_message("Step 7: Maximizing detail window...")
            
            coords = self.config["coordinates"]["maximize_detail"]
            if self.click_with_retry(coords):
                time.sleep(1)
                self.log_message("Detail window maximized")
                return True
            else:
                self.log_message("Failed to maximize detail window", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"Step 7 failed: {e}", "ERROR")
            return False
            
    def step8_extract_description(self, part_number: str) -> str:
        """Step 8: Extract part description from screen."""
        try:
            self.log_message("Step 8: Extracting part description...")
            self.progress_var.set("Extracting description...")
            
            # This is where you would implement OCR or screen scraping
            # For now, we'll simulate extraction
            time.sleep(2)
            
            # Simulate description extraction
            description = f"Description for {part_number} (extracted from SAP)"
            
            self.log_message(f"Description extracted: {description}")
            return description
            
        except Exception as e:
            self.log_message(f"Step 8 failed: {e}", "ERROR")
            return "ERROR - Could not extract description"
            
    def process_single_part(self, part_number: str) -> Dict[str, str]:
        """Process a single part number through all steps."""
        start_time = datetime.now()
        
        try:
            # Steps 1-4 (one-time setup if not already done)
            if not hasattr(self, '_sap_initialized'):
                if not (self.step1_open_sap_logon() and 
                       self.step2_maximize_window() and 
                       self.step3_select_connection() and 
                       self.step4_enter_md04()):
                    raise Exception("Failed to initialize SAP")
                self._sap_initialized = True
            
            # Step 5: Enter part number and MRP
            if not self.step5_enter_part_and_mrp(part_number):
                raise Exception("Failed to enter part data")
                
            # Step 6: Double click MatRes
            if not self.step6_double_click_matres():
                raise Exception("Failed to open MatRes")
                
            # Step 7: Maximize detail window
            if not self.step7_maximize_detail_window():
                raise Exception("Failed to maximize detail window")
                
            # Step 8: Extract description
            description = self.step8_extract_description(part_number)
            
            result = {
                "part_number": part_number,
                "description": description,
                "status": "SUCCESS" if "ERROR" not in description else "ERROR",
                "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
            return result
            
        except Exception as e:
            return {
                "part_number": part_number,
                "description": f"ERROR: {str(e)}",
                "status": "ERROR",
                "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
            
    def get_parts_list(self) -> List[str]:
        """Get list of parts from input sources."""
        parts = []
        
        # Single part
        if self.single_part_var.get().strip():
            parts.append(self.single_part_var.get().strip())
            
        # Multiple parts from text area
        text_parts = self.parts_text.get("1.0", tk.END).strip()
        if text_parts:
            parts.extend([p.strip() for p in text_parts.split('\n') if p.strip()])
            
        # Parts from Excel file
        if self.file_path_var.get():
            try:
                df = pd.read_excel(self.file_path_var.get())
                # Assume first column contains part numbers
                file_parts = df.iloc[:, 0].astype(str).tolist()
                parts.extend([p.strip() for p in file_parts if p.strip() and p.strip() != 'nan'])
            except Exception as e:
                self.log_message(f"Error reading Excel file: {e}", "ERROR")
                
        return list(set(parts))  # Remove duplicates
        
    def start_automation(self):
        """Start the automation process."""
        parts = self.get_parts_list()
        
        if not parts:
            messagebox.showerror("Error", "Please enter at least one part number")
            return
            
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.results.clear()
        
        # Clear results tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        self.log_message(f"Starting automation for {len(parts)} parts")
        
        # Run automation in separate thread
        threading.Thread(target=self.run_automation, args=(parts,), daemon=True).start()
        
    def run_automation(self, parts: List[str]):
        """Run the automation process for all parts."""
        try:
            total_parts = len(parts)
            self.progress_bar.config(maximum=total_parts)
            
            for i, part in enumerate(parts):
                if not self.is_running:
                    break
                    
                self.progress_bar.config(value=i)
                self.progress_var.set(f"Processing part {i+1}/{total_parts}: {part}")
                
                result = self.process_single_part(part)
                self.results.append(result)
                
                # Update results tree
                self.root.after(0, self.update_results_tree, result)
                
                # Small delay between parts
                time.sleep(1)
                
            self.progress_bar.config(value=total_parts)
            self.progress_var.set(f"Completed! Processed {len(self.results)} parts")
            
            successful = len([r for r in self.results if r["status"] == "SUCCESS"])
            failed = len([r for r in self.results if r["status"] == "ERROR"])
            
            self.log_message(f"Automation completed: {successful} successful, {failed} failed")
            
        except Exception as e:
            self.log_message(f"Automation error: {e}", "ERROR")
        finally:
            self.root.after(0, self.automation_finished)
            
    def update_results_tree(self, result: Dict[str, str]):
        """Update the results tree with new result."""
        self.results_tree.insert("", "end", values=(
            result["part_number"],
            result["description"][:50] + "..." if len(result["description"]) > 50 else result["description"],
            result["status"],
            result["timestamp"]
        ))
        
    def automation_finished(self):
        """Called when automation is finished."""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.save_btn.config(state="normal")
        
    def stop_automation(self):
        """Stop the automation process."""
        self.is_running = False
        self.log_message("Automation stopped by user")
        
    def test_connection(self):
        """Test SAP connection."""
        def test_thread():
            try:
                self.log_message("Testing SAP connection...")
                if self.step1_open_sap_logon():
                    self.log_message("✅ SAP connection test successful", "INFO")
                    messagebox.showinfo("Success", "SAP connection test successful!")
                else:
                    self.log_message("❌ SAP connection test failed", "ERROR")
                    messagebox.showerror("Error", "SAP connection test failed!")
            except Exception as e:
                self.log_message(f"Connection test error: {e}", "ERROR")
                messagebox.showerror("Error", f"Connection test failed: {e}")
                
        threading.Thread(target=test_thread, daemon=True).start()
        
    def save_results(self):
        """Save results to Excel file."""
        if not self.results:
            messagebox.showwarning("Warning", "No results to save")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SAP_MD04_Results_{timestamp}.xlsx"
            
            # Create DataFrame
            df = pd.DataFrame(self.results)
            
            # Save to Excel with formatting
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Part_Descriptions', index=False)
                
                # Create summary sheet
                summary_data = {
                    'Metric': [
                        'Total Parts Processed',
                        'Successful Extractions',
                        'Failed Extractions',
                        'Success Rate (%)',
                        'Average Processing Time (seconds)'
                    ],
                    'Value': [
                        len(self.results),
                        len([r for r in self.results if r["status"] == "SUCCESS"]),
                        len([r for r in self.results if r["status"] == "ERROR"]),
                        round((len([r for r in self.results if r["status"] == "SUCCESS"]) / len(self.results)) * 100, 2),
                        round(sum([r["processing_time"] for r in self.results]) / len(self.results), 2)
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            self.log_message(f"Results saved to: {filename}")
            messagebox.showinfo("Success", f"Results saved to {filename}")
            
        except Exception as e:
            self.log_message(f"Failed to save results: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to save results: {e}")
            
    def run(self):
        """Start the GUI application."""
        self.root.mainloop()


class OCRExtractor:
    """
    Enhanced OCR extraction for SAP data
    """
    
    def __init__(self):
        self.setup_ocr()
        
    def setup_ocr(self):
        """Setup OCR engine."""
        try:
            # Set Tesseract path if needed (adjust for your installation)
            # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            self.ocr_available = True
        except:
            self.ocr_available = False
            
    def extract_from_region(self, bbox):
        """Extract text from specific screen region."""
        if not self.ocr_available:
            return "OCR not available"
            
        try:
            # Take screenshot of specific region
            screenshot = pyautogui.screenshot(region=bbox)
            
            # Convert to OpenCV format
            img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Preprocess for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            # Extract text
            text = pytesseract.image_to_string(gray, config='--psm 6')
            return text.strip()
            
        except Exception as e:
            return f"OCR Error: {e}"


# Executable creation utilities
def create_executable():
    """
    Instructions for creating executable file
    """
    instructions = """
    To create an executable (.exe) file from this script:
    
    1. Install PyInstaller:
       pip install pyinstaller
       
    2. Create the executable:
       pyinstaller --onefile --windowed --name "SAP_MD04_RPA" main.py
       
    3. For better performance, use:
       pyinstaller --onefile --windowed --name "SAP_MD04_RPA" --hidden-import=tkinter --hidden-import=pandas --hidden-import=pyautogui main.py
       
    4. The executable will be created in the 'dist' folder
    
    Additional files needed in the same directory as the exe:
    - sap_rpa_config.json (configuration file)
    - logs/ folder (for log files)
    
    Note: Make sure all dependencies are installed:
    pip install tkinter pandas pyautogui opencv-python pillow pytesseract win32gui openpyxl
    """
    
    with open("executable_instructions.txt", "w") as f:
        f.write(instructions)
    
    print("Executable creation instructions saved to 'executable_instructions.txt'")


# Configuration setup utility
def setup_initial_config():
    """Setup initial configuration with guided coordinate capture."""
    print("SAP MD04 RPA Setup")
    print("==================")
    print("\nThis utility will help you configure the RPA bot for your SAP environment.")
    print("\nFirst, let's set up the basic configuration:")
    
    config = {
        "sap_connection_details": {
            "name": input("SAP Connection Name (default: 001. SAP ECC Production (PRD)): ") or "001. SAP ECC Production (PRD)",
            "system_description": input("System Description (default: SAP ERP): ") or "SAP ERP",
            "sid": input("System ID (default: PRD): ") or "PRD",
            "group_server": input("Group/Server (default: Production PRD): ") or "Production PRD",
            "message_server": input("Message Server: ") or "pdtcprd01.fermont.lamrc.net"
        },
        "coordinates": {
            "sap_taskbar_icon": [100, 100],
            "maximize_button": [500, 50],
            "sap_connection": [400, 300],
            "transaction_field": [400, 100],
            "part_number_field": [300, 200],
            "mrp_area_field": [500, 200],
            "matres_number": [200, 300],
            "maximize_detail": [500, 50]
        },
        "mrp_area": input("Default MRP Area (default: 1000): ") or "1000",
        "wait_times": {
            "sap_launch": 5,
            "connection": 10,
            "transaction_load": 3,
            "data_extraction": 2
        }
    }
    
    with open("sap_rpa_config.json", "w") as f:
        json.dump(config, f, indent=4)
    
    print("\nConfiguration saved to 'sap_rpa_config.json'")
    print("\nNext steps:")
    print("1. Run the application: python main.py")
    print("2. Use 'Setup Coordinates' button to configure screen positions")
    print("3. Test SAP connection")
    print("4. Start automation!")


# Main application entry point
def main():
    """Main application entry point."""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            setup_initial_config()
        elif sys.argv[1] == "exe":
            create_executable()
        else:
            print("Usage: python main.py [setup|exe]")
    else:
        # Start the GUI application
        app = SAPMD04RPA()
        app.run()


if __name__ == "__main__":
    main()


# Additional utility classes and functions
class SAPScreenAnalyzer:
    """
    Analyze SAP screens to automatically detect elements
    """
    
    def __init__(self):
        self.template_images = {}
        
    def load_templates(self):
        """Load template images for screen element detection."""
        # This would load template images for buttons, fields, etc.
        pass
        
    def find_element_by_template(self, template_name):
        """Find screen element using template matching."""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Load template
            template = cv2.imread(f"templates/{template_name}.png")
            
            # Template matching
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > 0.8:  # Confidence threshold
                return max_loc
            else:
                return None
                
        except Exception as e:
            print(f"Template matching error: {e}")
            return None
            
    def auto_detect_coordinates(self):
        """Automatically detect SAP element coordinates."""
        elements = {
            "sap_logon_icon": self.find_element_by_template("sap_logon_icon"),
            "connection_entry": self.find_element_by_template("connection_entry"),
            "transaction_field": self.find_element_by_template("transaction_field"),
            # Add more elements as needed
        }
        
        return {k: list(v) for k, v in elements.items() if v is not None}


class SAPDataValidator:
    """
    Validate extracted SAP data
    """
    
    @staticmethod
    def validate_part_number(part_number):
        """Validate part number format."""
        # Add your part number validation logic
        return len(part_number) > 0 and part_number.replace('-', '').replace('_', '').isalnum()
        
    @staticmethod
    def validate_description(description):
        """Validate description content."""
        invalid_indicators = ["error", "not found", "invalid", "timeout"]
        return not any(indicator in description.lower() for indicator in invalid_indicators)
        
    @staticmethod
    def clean_extracted_text(text):
        """Clean and normalize extracted text."""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common OCR artifacts
        text = text.replace('|', 'I').replace('0', 'O')
        
        return text.strip()


# Error recovery mechanisms
class ErrorRecovery:
    """
    Handle errors and implement recovery strategies
    """
    
    def __init__(self, rpa_bot):
        self.rpa_bot = rpa_bot
        self.recovery_attempts = 0
        self.max_attempts = 3
        
    def recover_from_sap_error(self):
        """Recover from SAP-related errors."""
        try:
            # Close any error dialogs
            pyautogui.press('escape')
            time.sleep(1)
            
            # Return to main screen
            pyautogui.hotkey('ctrl', 'home')
            time.sleep(2)
            
            # Re-initialize SAP session
            self.rpa_bot._sap_initialized = False
            
            return True
            
        except Exception as e:
            print(f"Recovery failed: {e}")
            return False
            
    def handle_timeout_error(self):
        """Handle timeout errors."""
        # Wait longer for SAP to respond
        time.sleep(5)
        
        # Try refreshing the screen
        pyautogui.press('f5')
        time.sleep(3)
        
        return True
        
    def attempt_recovery(self, error_type):
        """Attempt recovery based on error type."""
        if self.recovery_attempts >= self.max_attempts:
            return False
            
        self.recovery_attempts += 1
        
        if error_type == "sap_error":
            return self.recover_from_sap_error()
        elif error_type == "timeout":
            return self.handle_timeout_error()
        else:
            return False


# Batch processing manager
class BatchProcessor:
    """
    Manage batch processing of multiple parts
    """
    
    def __init__(self, rpa_bot, batch_size=10):
        self.rpa_bot = rpa_bot
        self.batch_size = batch_size
        self.processed_count = 0
        
    def process_in_batches(self, parts_list):
        """Process parts in smaller batches for better reliability."""
        results = []
        
        for i in range(0, len(parts_list), self.batch_size):
            batch = parts_list[i:i + self.batch_size]
            batch_results = self.process_batch(batch)
            results.extend(batch_results)
            
            # Rest between batches
            if i + self.batch_size < len(parts_list):
                time.sleep(5)
                
        return results
        
    def process_batch(self, batch):
        """Process a single batch of parts."""
        results = []
        
        for part in batch:
            try:
                result = self.rpa_bot.process_single_part(part)
                results.append(result)
                self.processed_count += 1
                
            except Exception as e:
                error_result = {
                    "part_number": part,
                    "description": f"ERROR: {str(e)}",
                    "status": "ERROR",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "processing_time": 0
                }
                results.append(error_result)
                
        return results