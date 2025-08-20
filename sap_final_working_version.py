import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import win32com.client
import pandas as pd
import time
import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import pythoncom

class SAPFinalWorkingVersion:
    """
    SAP Final Working Version - Using YOUR EXACT Field IDs!
    This version uses the field IDs discovered from your SAP system
    """
    
    def __init__(self):
        # Initialize field IDs FIRST (before GUI setup)
        self.field_ids = {
            "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR",
            "mrp_area_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-BERID",
            "plant_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-WERKS",
            "description_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/txtMT61D-MAKTX"
        }
        
        # SAP Connection objects
        self.session = None
        self.results = []
        
        # Setup logging and GUI
        self.setup_logging()
        self.setup_gui()
        
    def setup_logging(self):
        """Setup logging system."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/sap_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def setup_gui(self):
        """Setup the GUI interface."""
        self.root = tk.Tk()
        self.root.title("SAP Final Working Version - Using YOUR Field IDs")
        self.root.geometry("900x700")
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, 
                               text="SAP Automation - Final Working Version", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Using YOUR exact field IDs from scan!",
                                  font=("Arial", 10),
                                  foreground="green")
        subtitle_label.pack()
        
        # Connection Status
        status_frame = ttk.LabelFrame(main_container, text="SAP Connection Status", padding="10")
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.connection_status_var = tk.StringVar(value="[X] Not Connected")
        status_label = ttk.Label(status_frame, textvariable=self.connection_status_var,
                                font=("Arial", 10, "bold"))
        status_label.pack(side=tk.LEFT)
        
        connect_btn = ttk.Button(status_frame, text="Connect to SAP",
                                command=self.connect_to_sap_gui)
        connect_btn.pack(side=tk.RIGHT)
        
        test_btn = ttk.Button(status_frame, text="Test Fields",
                             command=self.test_all_fields)
        test_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Field Information
        info_frame = ttk.LabelFrame(main_container, text="Field Information (From Your Scan)", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = tk.Text(info_frame, height=4, wrap=tk.WORD, font=("Consolas", 8))
        info_content = f"""Material Field: {self.field_ids['material_field']}
MRP Area Field: {self.field_ids['mrp_area_field']}
Plant Field: {self.field_ids['plant_field']}
Description Field: {self.field_ids['description_field']}"""
        info_text.insert("1.0", info_content)
        info_text.config(state="disabled", bg="#f0f0f0")
        info_text.pack(fill=tk.X)
        
        # Input Section
        input_frame = ttk.LabelFrame(main_container, text="Part Numbers Input", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Single part
        single_frame = ttk.Frame(input_frame)
        single_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(single_frame, text="Part Number:").pack(side=tk.LEFT)
        self.single_part_var = tk.StringVar(value="857-A65473-106")
        single_entry = ttk.Entry(single_frame, textvariable=self.single_part_var, width=30)
        single_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Configuration
        config_frame = ttk.Frame(input_frame)
        config_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(config_frame, text="MRP Area:").pack(side=tk.LEFT)
        self.mrp_area_var = tk.StringVar(value="1000")
        mrp_entry = ttk.Entry(config_frame, textvariable=self.mrp_area_var, width=10)
        mrp_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(config_frame, text="Plant:").pack(side=tk.LEFT)
        self.plant_var = tk.StringVar(value="1000")
        plant_entry = ttk.Entry(config_frame, textvariable=self.plant_var, width=10)
        plant_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Control Buttons
        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="START Extraction (Using YOUR Fields)",
                                   command=self.start_extraction)
        self.start_btn.pack(side=tk.LEFT)
        
        self.manual_btn = ttk.Button(control_frame, text="Manual Field Entry",
                                    command=self.manual_field_entry)
        self.manual_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        self.save_btn = ttk.Button(control_frame, text="Save Results",
                                  command=self.save_results, state="disabled")
        self.save_btn.pack(side=tk.RIGHT)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_container, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to start...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.pack(anchor=tk.W)
        
        # Results Section
        results_frame = ttk.LabelFrame(main_container, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        columns = ("Part Number", "Description", "Status", "Method", "Timestamp")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Description":
                self.results_tree.column(col, width=400)
            else:
                self.results_tree.column(col, width=120)
        
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log Section
        log_frame = ttk.LabelFrame(main_container, text="System Log", padding="10")
        log_frame.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80)
        self.log_text.pack(fill=tk.X)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to GUI log and logger."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        log_entry = f"[{timestamp}] {level}: {safe_message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        if level == "INFO":
            self.logger.info(safe_message)
        elif level == "ERROR":
            self.logger.error(safe_message)
        elif level == "WARNING":
            self.logger.warning(safe_message)
            
        self.root.update_idletasks()
            
    def connect_to_sap_gui(self) -> bool:
        """Connect to SAP GUI."""
        try:
            pythoncom.CoInitialize()
            
            self.log_message("Connecting to SAP GUI...")
            
            sap_gui_auto = win32com.client.GetObject("SAPGUI")
            application = sap_gui_auto.GetScriptingEngine
            
            if application.Children.Count > 0:
                connection = application.Children(0)
                if connection.Children.Count > 0:
                    self.session = connection.Children(0)
                    
                    info = self.session.Info
                    system_name = info.SystemName
                    client = info.Client
                    user = info.User
                    
                    self.connection_status_var.set(f"[OK] Connected: {system_name} Client {client} User {user}")
                    self.log_message(f"Successfully connected to SAP: {system_name} Client {client} User {user}")
                    return True
            
            raise Exception("No SAP sessions found")
            
        except Exception as e:
            error_msg = str(e)
            self.connection_status_var.set("[X] Connection Failed")
            self.log_message(f"Failed to connect to SAP: {error_msg}", "ERROR")
            messagebox.showerror("SAP Connection Error", f"Failed to connect:\n{error_msg}")
            return False
            
    def test_all_fields(self):
        """Test all field IDs found in your scan."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.log_message("=== TESTING ALL FIELDS FROM YOUR SCAN ===")
        
        for field_name, field_id in self.field_ids.items():
            try:
                field = self.session.findById(field_id)
                field_type = getattr(field, 'Type', 'Unknown')
                modifiable = getattr(field, 'Modifiable', False)
                text = getattr(field, 'Text', '')
                
                self.log_message(f"[OK] {field_name}: Found")
                self.log_message(f"    Type: {field_type}, Modifiable: {modifiable}, Text: '{text}'")
                
            except Exception as e:
                self.log_message(f"[X] {field_name}: NOT FOUND - {e}", "ERROR")
                
        self.log_message("=== FIELD TEST COMPLETE ===")
        
    def go_to_md04(self):
        """Navigate to MD04 and ensure we're on the right screen."""
        try:
            self.log_message("Navigating to MD04...")
            
            # Clear and enter MD04
            self.session.findById("wnd[0]/tbar[0]/okcd").text = ""
            time.sleep(0.5)
            self.session.findById("wnd[0]/tbar[0]/okcd").text = "MD04"
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(3)
            
            # Verify we're on the right screen
            current_transaction = self.session.Info.Transaction
            window_title = self.session.findById("wnd[0]").text
            
            self.log_message(f"Current transaction: {current_transaction}")
            self.log_message(f"Window title: {window_title}")
            
            # Check if we're on the Individual access tab
            try:
                individual_tab = self.session.findById("wnd[0]/usr/tabsTAB300/tabpF01")
                if individual_tab:
                    individual_tab.select()  # Make sure Individual access tab is selected
                    time.sleep(1)
                    self.log_message("[OK] Individual access tab selected")
            except:
                self.log_message("[!] Could not select Individual access tab", "WARNING")
            
            return True
            
        except Exception as e:
            self.log_message(f"Error navigating to MD04: {e}", "ERROR")
            return False
            
    def make_field_editable(self, field_id: str) -> bool:
        """Try to make a field editable using various methods."""
        try:
            field = self.session.findById(field_id)
            
            # Method 1: Click on the field to focus it
            field.setFocus()
            time.sleep(0.5)
            
            # Method 2: Try pressing F2 to enter edit mode
            self.session.findById("wnd[0]").sendVKey(2)  # F2
            time.sleep(0.5)
            
            # Method 3: Try double-clicking
            try:
                field.doubleClick()
                time.sleep(0.5)
            except:
                pass
            
            # Check if it's now modifiable
            if getattr(field, 'Modifiable', False):
                self.log_message(f"[OK] Field is now editable: {field_id}")
                return True
            else:
                self.log_message(f"[!] Field still not editable: {field_id}", "WARNING")
                return False
                
        except Exception as e:
            self.log_message(f"Error making field editable: {e}", "ERROR")
            return False
            
    def enter_material_number(self, part_number: str) -> bool:
        """Enter material number using YOUR exact field ID."""
        try:
            self.log_message(f"Entering material number: {part_number}")
            
            material_field_id = self.field_ids["material_field"]
            
            # First, try to make the field editable
            self.make_field_editable(material_field_id)
            
            # Try to enter the material number
            field = self.session.findById(material_field_id)
            
            # Multiple methods to set the value
            methods = [
                lambda: setattr(field, 'text', part_number),
                lambda: field.setFocus() or setattr(field, 'text', part_number),
                lambda: self.send_keys_to_field(field, part_number)
            ]
            
            for i, method in enumerate(methods, 1):
                try:
                    self.log_message(f"Trying method {i} to enter material number...")
                    method()
                    time.sleep(0.5)
                    
                    # Check if it was set
                    current_text = getattr(field, 'text', '')
                    if current_text == part_number:
                        self.log_message(f"[OK] Material number entered successfully: {part_number}")
                        return True
                    else:
                        self.log_message(f"[!] Method {i} failed. Expected: '{part_number}', Got: '{current_text}'")
                        
                except Exception as e:
                    self.log_message(f"[!] Method {i} error: {e}")
                    continue
            
            # If all methods failed, try manual keyboard input
            return self.manual_keyboard_input(material_field_id, part_number)
            
        except Exception as e:
            self.log_message(f"Error entering material number: {e}", "ERROR")
            return False
            
    def send_keys_to_field(self, field, text):
        """Send keys to field using SAP sendKeys method."""
        try:
            field.setFocus()
            time.sleep(0.2)
            
            # Clear existing content
            field.caretPosition = 0
            self.session.findById("wnd[0]").sendVKey(2, 16)  # Ctrl+A
            time.sleep(0.1)
            
            # Type the new text
            for char in text:
                self.session.findById("wnd[0]").sendVKey(ord(char))
                time.sleep(0.05)
                
            return True
            
        except Exception as e:
            self.log_message(f"SendKeys method failed: {e}")
            return False
            
    def manual_keyboard_input(self, field_id: str, text: str) -> bool:
        """Manual keyboard input as last resort."""
        try:
            self.log_message("Trying manual keyboard input method...")
            
            field = self.session.findById(field_id)
            field.setFocus()
            time.sleep(0.5)
            
            # Clear field
            self.session.findById("wnd[0]").sendVKey(0, 2)  # Ctrl+A
            time.sleep(0.2)
            
            # Send each character
            for char in text:
                if char.isalnum() or char in '-_':
                    self.session.findById("wnd[0]").sendVKey(ord(char.upper()))
                    time.sleep(0.1)
            
            # Check result
            current_text = getattr(field, 'text', '')
            if current_text == text:
                self.log_message("[OK] Manual keyboard input successful")
                return True
            else:
                self.log_message(f"[!] Manual input failed. Expected: '{text}', Got: '{current_text}'")
                return False
                
        except Exception as e:
            self.log_message(f"Manual keyboard input failed: {e}", "ERROR")
            return False
            
    def extract_description_from_field(self) -> str:
        """Extract description from the description field."""
        try:
            description_field_id = self.field_ids["description_field"]
            field = self.session.findById(description_field_id)
            description = getattr(field, 'text', '').strip()
            
            if description:
                self.log_message(f"[OK] Description found: {description}")
                return description
            else:
                self.log_message("[!] Description field is empty")
                return "No description available"
                
        except Exception as e:
            self.log_message(f"Error extracting description: {e}", "ERROR")
            return "ERROR: Could not extract description"
            
    def process_part_number(self, part_number: str) -> Dict[str, str]:
        """Process a single part number using YOUR field IDs."""
        start_time = datetime.now()
        
        try:
            self.log_message(f"=== PROCESSING PART: {part_number} ===")
            
            # Navigate to MD04
            if not self.go_to_md04():
                raise Exception("Failed to navigate to MD04")
            
            # Enter material number
            if not self.enter_material_number(part_number):
                raise Exception("Failed to enter material number")
            
            # Enter MRP area if specified
            if self.mrp_area_var.get():
                try:
                    mrp_field = self.session.findById(self.field_ids["mrp_area_field"])
                    self.make_field_editable(self.field_ids["mrp_area_field"])
                    mrp_field.text = self.mrp_area_var.get()
                    self.log_message(f"[OK] MRP area entered: {self.mrp_area_var.get()}")
                except Exception as e:
                    self.log_message(f"[!] Could not enter MRP area: {e}", "WARNING")
            
            # Execute the query
            self.log_message("Executing query...")
            self.session.findById("wnd[0]").sendVKey(0)  # Press Enter
            time.sleep(3)
            
            # Check for errors
            error_msg = self.check_for_errors()
            if error_msg:
                raise Exception(f"SAP Error: {error_msg}")
            
            # Extract description
            description = self.extract_description_from_field()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "part_number": part_number,
                "description": description,
                "status": "SUCCESS" if "ERROR" not in description else "ERROR",
                "method": "Direct Field Access",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time": round(processing_time, 2)
            }
            
            self.log_message(f"[OK] Processing completed for {part_number}")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            result = {
                "part_number": part_number,
                "description": f"ERROR: {error_msg}",
                "status": "ERROR",
                "method": "Failed",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time": round(processing_time, 2)
            }
            
            self.log_message(f"[X] Processing failed for {part_number}: {error_msg}", "ERROR")
            return result
            
    def check_for_errors(self) -> str:
        """Check for SAP error messages."""
        try:
            # Check status bar
            status_bar = self.session.findById("wnd[0]/sbar")
            if status_bar and status_bar.text:
                status_text = status_bar.text
                if any(keyword in status_text.lower() for keyword in ['error', 'not found', 'does not exist']):
                    return status_text
                    
            # Check for error windows
            for window_id in ["wnd[1]", "wnd[2]"]:
                try:
                    window = self.session.findById(window_id)
                    if window and window.text:
                        window_text = window.text
                        if any(keyword in window_text.lower() for keyword in ['error', 'fehler']):
                            try:
                                window.sendVKey(0)  # Close error window
                            except:
                                pass
                            return window_text
                except:
                    continue
                    
        except Exception as e:
            self.log_message(f"Error checking for SAP errors: {e}", "WARNING")
            
        return ""
        
    def start_extraction(self):
        """Start the extraction process."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        part_number = self.single_part_var.get().strip()
        if not part_number:
            messagebox.showerror("Error", "Please enter a part number!")
            return
            
        self.start_btn.config(state="disabled")
        self.progress_var.set("Starting extraction...")
        
        try:
            result = self.process_part_number(part_number)
            self.results.append(result)
            self.update_results_tree(result)
            
            if result["status"] == "SUCCESS":
                self.progress_var.set(f"[OK] SUCCESS! Description: {result['description'][:50]}...")
                messagebox.showinfo("Success!", f"Successfully extracted description:\n\n{result['description']}")
            else:
                self.progress_var.set(f"[X] Failed: {result['description']}")
                messagebox.showerror("Failed", f"Extraction failed:\n\n{result['description']}")
                
        except Exception as e:
            self.log_message(f"Extraction error: {e}", "ERROR")
            self.progress_var.set(f"[X] Error: {e}")
            
        finally:
            self.start_btn.config(state="normal")
            self.save_btn.config(state="normal")
            
    def manual_field_entry(self):
        """Manual field entry for troubleshooting."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        manual_window = tk.Toplevel(self.root)
        manual_window.title("Manual Field Entry")
        manual_window.geometry("600x400")
        
        ttk.Label(manual_window, text="Manual Field Entry for Troubleshooting", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Field selection
        field_frame = ttk.Frame(manual_window)
        field_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(field_frame, text="Select Field:").pack(side=tk.LEFT)
        field_var = tk.StringVar()
        field_combo = ttk.Combobox(field_frame, textvariable=field_var, width=50)
        field_combo['values'] = list(self.field_ids.values())
        field_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Value entry
        value_frame = ttk.Frame(manual_window)
        value_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(value_frame, text="Value to Enter:").pack(side=tk.LEFT)
        value_var = tk.StringVar(value="857-A65473-106")
        value_entry = ttk.Entry(value_frame, textvariable=value_var, width=30)
        value_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(manual_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def manual_test():
            field_id = field_var.get()
            value = value_var.get()
            if field_id and value:
                success = self.enter_material_number(value) if "MATNR" in field_id else self.manual_keyboard_input(field_id, value)
                if success:
                    messagebox.showinfo("Success", f"Successfully entered '{value}' in field!")
                else:
                    messagebox.showerror("Failed", f"Failed to enter '{value}' in field!")
        
        ttk.Button(button_frame, text="Test Entry", command=manual_test).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Close", command=manual_window.destroy).pack(side=tk.RIGHT)
        
    def update_results_tree(self, result: Dict[str, str]):
        """Update results tree."""
        tags = ["success"] if result["status"] == "SUCCESS" else ["error"]
        
        self.results_tree.insert("", "end", values=(
            result["part_number"],
            result["description"][:80] + "..." if len(result["description"]) > 80 else result["description"],
            result["status"],
            result["method"],
            result["timestamp"]
        ), tags=tags)
        
        self.results_tree.tag_configure("success", foreground="green")
        self.results_tree.tag_configure("error", foreground="red")
        
    def save_results(self):
        """Save results to Excel file."""
        if not self.results:
            messagebox.showwarning("Warning", "No results to save!")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SAP_Final_Results_{timestamp}.xlsx"
            
            df = pd.DataFrame(self.results)
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Results', index=False)
                
                # Summary
                summary_data = {
                    'Metric': [
                        'Total Parts Processed',
                        'Successful Extractions',
                        'Failed Extractions',
                        'Success Rate (%)',
                        'Field IDs Used'
                    ],
                    'Value': [
                        len(self.results),
                        len([r for r in self.results if r["status"] == "SUCCESS"]),
                        len([r for r in self.results if r["status"] == "ERROR"]),
                        round((len([r for r in self.results if r["status"] == "SUCCESS"]) / len(self.results)) * 100, 1),
                        "Your Exact Field IDs from Scan"
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            self.log_message(f"Results saved to: {filename}")
            messagebox.showinfo("Success", f"Results saved to {filename}")
            
        except Exception as e:
            self.log_message(f"Failed to save results: {e}", "ERROR")
            messagebox.showerror("Save Error", f"Failed to save: {e}")
            
    def run(self):
        """Start the application."""
        self.log_message("SAP Final Working Version Started")
        self.log_message("Using YOUR exact field IDs from the scan!")
        self.log_message("Field IDs configured:")
        for name, field_id in self.field_ids.items():
            self.log_message(f"  {name}: {field_id}")
        self.log_message("Please connect to SAP to begin...")
        
        self.root.mainloop()


def main():
    """Main function."""
    print("="*80)
    print("SAP FINAL WORKING VERSION")
    print("="*80)
    print("This version uses YOUR EXACT field IDs discovered from the scan:")
    print()
    print("Material Field:")
    print("  /app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR")
    print()
    print("MRP Area Field:")
    print("  /app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-BERID")
    print()
    print("Plant Field:")
    print("  /app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-WERKS")
    print()
    print("Description Field:")
    print("  /app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/txtMT61D-MAKTX")
    print()
    print("Special features:")
    print("- Handles read-only fields by making them editable")
    print("- Multiple input methods (direct, keyboard, manual)")
    print("- Manual field entry tool for troubleshooting")
    print("- Uses your exact SAP system layout")
    print("="*80)
    
    try:
        app = SAPFinalWorkingVersion()
        app.run()
    except Exception as e:
        print(f"[X] Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()