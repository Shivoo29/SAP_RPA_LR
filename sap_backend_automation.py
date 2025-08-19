import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import win32com.client
import pandas as pd
import time
import logging
import os
import json
import threading
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pytesseract
from PIL import ImageGrab
import re
import pythoncom  # Added for COM threading

class SAPBackendAutomationFixed:
    """
    Fixed SAP Backend Automation - No Unicode errors, No threading issues
    """
    
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_gui()
        
        # SAP Connection objects
        self.sap_gui_auto = None
        self.application = None
        self.connection = None
        self.session = None
        
        # Processing state
        self.is_running = False
        self.results = []
        self.current_part_index = 0
        self.total_parts = 0
        
    def setup_logging(self):
        """Setup logging system without Unicode characters."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/sap_backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Create custom formatter that handles Unicode safely
        class SafeFormatter(logging.Formatter):
            def format(self, record):
                # Remove or replace Unicode characters
                if hasattr(record, 'msg'):
                    record.msg = str(record.msg).encode('ascii', 'replace').decode('ascii')
                return super().format(record)
        
        # Setup file handler with UTF-8 encoding
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(SafeFormatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Setup console handler with safe encoding
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(SafeFormatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def load_config(self):
        """Load configuration."""
        default_config = {
            "sap_connection": {
                "system_name": "001. SAP ECC Production (PRD)",
                "client": "100",
                "language": "EN"
            },
            "transactions": {
                "material_display": "MM03",
                "stock_requirements": "MD04",
                "mrp_list": "MD06"
            },
            "field_mappings": {
                "md04": {
                    "material_field": "wnd[0]/usr/ctxtRM61E-MATNR",
                    "mrp_area_field": "wnd[0]/usr/ctxtRM61E-BERID",
                    "plant_field": "wnd[0]/usr/ctxtRM61E-WERKS",
                    "execute_button": "wnd[0]/tbar[1]/btn[8]",
                    "result_grid": "wnd[0]/usr/cntlGRID1/shellcont/shell",
                    "detail_window": "wnd[1]",
                    "description_field": "wnd[1]/usr/subSUB0:SAPLMGMM:2001/subSUB0:SAPLMGMM:2003/txtRMMG1-MAKTX"
                }
            },
            "default_values": {
                "mrp_area": "1000",
                "plant": ""
            },
            "ocr_fallback": {
                "enabled": True,
                "description_region": [100, 400, 700, 500],
                "confidence_threshold": 60
            }
        }
        
        config_file = "sap_backend_config.json"
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = default_config
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
                
    def setup_gui(self):
        """Setup the GUI interface."""
        self.root = tk.Tk()
        self.root.title("SAP Backend Automation - Fixed Version")
        self.root.geometry("900x800")
        
        # Styling
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, 
                               text="SAP Backend Automation System - Fixed", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Invisible automation using SAP GUI Scripting API - No mouse movement!",
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
        
        test_btn = ttk.Button(status_frame, text="Test Connection",
                             command=self.test_sap_connection)
        test_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Input Section
        input_frame = ttk.LabelFrame(main_container, text="Part Numbers Input", padding="10")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Single part
        single_frame = ttk.Frame(input_frame)
        single_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(single_frame, text="Single Part:").pack(side=tk.LEFT)
        self.single_part_var = tk.StringVar()
        single_entry = ttk.Entry(single_frame, textvariable=self.single_part_var, width=30)
        single_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Multiple parts
        multi_frame = ttk.Frame(input_frame)
        multi_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        ttk.Label(multi_frame, text="Multiple Parts (one per line):").pack(anchor=tk.W)
        self.parts_text = scrolledtext.ScrolledText(multi_frame, height=4, width=50)
        self.parts_text.pack(fill=tk.X, pady=(5, 0))
        
        # File input
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(file_frame, text="Excel File:").pack(side=tk.LEFT)
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=40)
        file_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_container, text="Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        config_grid = ttk.Frame(config_frame)
        config_grid.pack(fill=tk.X)
        
        # Transaction
        ttk.Label(config_grid, text="Transaction:").grid(row=0, column=0, sticky=tk.W)
        self.transaction_var = tk.StringVar(value="MD04")
        transaction_combo = ttk.Combobox(config_grid, textvariable=self.transaction_var,
                                        values=["MD04", "MD06", "MM03"], width=10, state="readonly")
        transaction_combo.grid(row=0, column=1, padx=(10, 20), sticky=tk.W)
        
        # MRP Area
        ttk.Label(config_grid, text="MRP Area:").grid(row=0, column=2, sticky=tk.W)
        self.mrp_area_var = tk.StringVar(value=self.config["default_values"]["mrp_area"])
        mrp_entry = ttk.Entry(config_grid, textvariable=self.mrp_area_var, width=10)
        mrp_entry.grid(row=0, column=3, padx=(10, 20), sticky=tk.W)
        
        # Plant
        ttk.Label(config_grid, text="Plant:").grid(row=0, column=4, sticky=tk.W)
        self.plant_var = tk.StringVar(value=self.config["default_values"]["plant"])
        plant_entry = ttk.Entry(config_grid, textvariable=self.plant_var, width=10)
        plant_entry.grid(row=0, column=5, padx=(10, 0), sticky=tk.W)
        
        # Control Buttons
        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="START Backend Automation",
                                   command=self.start_automation)
        self.start_btn.pack(side=tk.LEFT)
        
        self.stop_btn = ttk.Button(control_frame, text="STOP", 
                                  command=self.stop_automation, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        self.save_btn = ttk.Button(control_frame, text="Save Results",
                                  command=self.save_results, state="disabled")
        self.save_btn.pack(side=tk.RIGHT)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_container, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to start backend automation...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Current processing info
        self.current_part_var = tk.StringVar(value="")
        current_label = ttk.Label(progress_frame, textvariable=self.current_part_var,
                                 font=("Arial", 9, "bold"), foreground="blue")
        current_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Results Section
        results_frame = ttk.LabelFrame(main_container, text="Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Results tree
        columns = ("Part Number", "Description", "Material Type", "Status", "Processing Time", "Timestamp")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Description":
                self.results_tree.column(col, width=300)
            elif col == "Part Number":
                self.results_tree.column(col, width=120)
            else:
                self.results_tree.column(col, width=100)
        
        # Scrollbars for results
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(0, weight=1)
        
        # Log Section
        log_frame = ttk.LabelFrame(main_container, text="System Log", padding="10")
        log_frame.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=80)
        self.log_text.pack(fill=tk.X)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to GUI log and logger - Safe Unicode handling."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Remove Unicode characters for safe logging
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        log_entry = f"[{timestamp}] {level}: {safe_message}\n"
        
        # Add to GUI log
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Add to file log
        if level == "INFO":
            self.logger.info(safe_message)
        elif level == "ERROR":
            self.logger.error(safe_message)
        elif level == "WARNING":
            self.logger.warning(safe_message)
            
    def connect_to_sap_gui(self) -> bool:
        """Connect to SAP GUI using COM interface - Fixed threading."""
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            self.log_message("Connecting to SAP GUI Scripting API...")
            
            # Get SAP GUI Automation object
            self.sap_gui_auto = win32com.client.GetObject("SAPGUI")
            if not self.sap_gui_auto:
                raise Exception("SAP GUI not found. Please start SAP Logon.")
            
            # Get Application object
            self.application = self.sap_gui_auto.GetScriptingEngine
            if not self.application:
                raise Exception("SAP GUI Scripting not enabled. Please enable scripting in SAP.")
            
            # Get Connection
            if self.application.Children.Count > 0:
                self.connection = self.application.Children(0)
            else:
                raise Exception("No SAP connections available. Please connect to SAP.")
            
            # Get Session
            if self.connection.Children.Count > 0:
                self.session = self.connection.Children(0)
            else:
                raise Exception("No active SAP session found.")
            
            # Test the connection
            session_info = self.session.Info
            system_name = session_info.SystemName
            client = session_info.Client
            user = session_info.User
            
            self.connection_status_var.set(f"[OK] Connected: {system_name} Client {client} User {user}")
            self.log_message(f"Successfully connected to SAP: {system_name} Client {client} User {user}")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.connection_status_var.set("[X] Connection Failed")
            self.log_message(f"Failed to connect to SAP: {error_msg}", "ERROR")
            
            # Show detailed error message
            messagebox.showerror("SAP Connection Error", 
                               f"Failed to connect to SAP GUI:\n\n{error_msg}\n\n"
                               "Please ensure:\n"
                               "1. SAP Logon is running\n"
                               "2. You are logged into SAP\n"
                               "3. SAP GUI Scripting is enabled")
            return False
        finally:
            # Don't uninitialize here, keep COM initialized for the session
            pass
            
    def test_sap_connection(self):
        """Test SAP connection and basic functionality."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            self.log_message("Testing SAP connection...")
            
            # Test basic session access
            current_transaction = self.session.Info.Transaction
            screen_number = self.session.Info.ScreenNumber
            
            self.log_message(f"Current Transaction: {current_transaction}")
            self.log_message(f"Screen Number: {screen_number}")
            
            # Test navigation to MD04
            test_result = self.execute_transaction("MD04")
            if test_result:
                self.log_message("SAP connection test successful!")
                messagebox.showinfo("Success", "SAP connection test successful!\n\nBackend automation is ready to use.")
            else:
                self.log_message("SAP connection test failed!", "ERROR")
                messagebox.showerror("Error", "SAP connection test failed!")
                
        except Exception as e:
            self.log_message(f"Connection test error: {e}", "ERROR")
            messagebox.showerror("Error", f"Connection test failed:\n{e}")
        finally:
            pythoncom.CoUninitialize()
            
    def execute_transaction(self, tcode: str) -> bool:
        """Execute SAP transaction using GUI scripting - Fixed COM."""
        try:
            if not self.session:
                raise Exception("No active SAP session")
            
            self.log_message(f"Executing transaction: {tcode}")
            
            # Enter transaction code
            self.session.findById("wnd[0]/tbar[0]/okcd").text = tcode
            self.session.findById("wnd[0]").sendVKey(0)  # Press Enter
            
            time.sleep(2)  # Wait for transaction to load
            
            # Verify transaction loaded
            current_transaction = self.session.Info.Transaction
            if current_transaction.upper() == tcode.upper():
                self.log_message(f"Transaction {tcode} loaded successfully")
                return True
            else:
                self.log_message(f"Transaction may not have loaded correctly. Current: {current_transaction}")
                return True  # Continue anyway
                
        except Exception as e:
            self.log_message(f"Failed to execute transaction {tcode}: {e}", "ERROR")
            return False
            
    def extract_part_data_md04(self, part_number: str) -> Dict[str, str]:
        """Extract part data using MD04 transaction - Fixed COM threading."""
        start_time = datetime.now()
        
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            # Execute MD04 transaction
            if not self.execute_transaction("MD04"):
                raise Exception("Failed to execute MD04")
            
            # Enter material number
            material_field = self.config["field_mappings"]["md04"]["material_field"]
            try:
                self.session.findById(material_field).text = part_number
            except:
                # Fallback field mapping
                self.session.findById("wnd[0]/usr/ctxtRM61E-MATNR").text = part_number
            
            # Enter MRP Area if specified
            if self.mrp_area_var.get():
                try:
                    mrp_field = self.config["field_mappings"]["md04"]["mrp_area_field"]
                    self.session.findById(mrp_field).text = self.mrp_area_var.get()
                except:
                    # Fallback
                    self.session.findById("wnd[0]/usr/ctxtRM61E-BERID").text = self.mrp_area_var.get()
            
            # Enter Plant if specified
            if self.plant_var.get():
                try:
                    plant_field = self.config["field_mappings"]["md04"]["plant_field"]
                    self.session.findById(plant_field).text = self.plant_var.get()
                except:
                    pass
            
            # Execute the query
            self.session.findById("wnd[0]").sendVKey(0)  # Press Enter
            time.sleep(3)  # Wait for results
            
            # Extract description - multiple methods
            description = self.extract_description_multiple_methods(part_number)
            
            # Get additional information if available
            material_type = self.extract_material_type()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "part_number": part_number,
                "description": description,
                "material_type": material_type,
                "status": "SUCCESS" if description != "ERROR" else "ERROR",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MD04"
            }
            
            self.log_message(f"Successfully extracted data for {part_number}: {description[:50]}...")
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            result = {
                "part_number": part_number,
                "description": f"ERROR: {error_msg}",
                "material_type": "ERROR",
                "status": "ERROR",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MD04",
                "error": error_msg
            }
            
            self.log_message(f"Failed to extract data for {part_number}: {error_msg}", "ERROR")
            return result
        finally:
            # Keep COM initialized for the session
            pass
            
    def extract_description_multiple_methods(self, part_number: str) -> str:
        """Try multiple methods to extract part description."""
        
        # Method 1: Try to find and double-click on result row
        try:
            # Look for the results grid
            grid = self.session.findById("wnd[0]/usr/cntlGRID1/shellcont/shell")
            if grid:
                # Get row count
                row_count = grid.RowCount
                self.log_message(f"Found {row_count} rows in results grid")
                
                if row_count > 0:
                    # Double-click on first row to open details
                    grid.doubleClickCurrentCell()
                    time.sleep(2)
                    
                    # Try to extract description from detail window
                    description = self.extract_from_detail_window()
                    if description and description != "ERROR":
                        return description
                        
        except Exception as e:
            self.log_message(f"Method 1 failed: {e}", "WARNING")
        
        # Method 2: Try to extract directly from main screen
        try:
            description = self.extract_from_main_screen()
            if description and description != "ERROR":
                return description
        except Exception as e:
            self.log_message(f"Method 2 failed: {e}", "WARNING")
        
        # Method 3: Try MM03 transaction for description
        try:
            description = self.extract_using_mm03(part_number)
            if description and description != "ERROR":
                return description
        except Exception as e:
            self.log_message(f"Method 3 failed: {e}", "WARNING")
        
        return "ERROR: Could not extract description"
        
    def extract_from_detail_window(self) -> str:
        """Extract description from detail window."""
        try:
            # Check if detail window opened
            detail_windows = ["wnd[1]", "wnd[2]"]
            
            for window_id in detail_windows:
                try:
                    window = self.session.findById(window_id)
                    if window:
                        # Look for common description fields
                        description_fields = [
                            f"{window_id}/usr/subSUB0:SAPLMGMM:2001/subSUB0:SAPLMGMM:2003/txtRMMG1-MAKTX",
                            f"{window_id}/usr/txtMAKTX",
                            f"{window_id}/usr/ctxtMAKTX",
                            f"{window_id}/usr/subSUB1:SAPLMGMM:2003/txtRMMG1-MAKTX"
                        ]
                        
                        for field_id in description_fields:
                            try:
                                field = self.session.findById(field_id)
                                if field and field.text.strip():
                                    description = field.text.strip()
                                    self.log_message(f"Found description in detail window: {description}")
                                    
                                    # Close detail window
                                    self.session.findById(window_id).close()
                                    return description
                            except:
                                continue
                                
                        # Close window if no description found
                        window.close()
                        
                except:
                    continue
                    
        except Exception as e:
            self.log_message(f"Detail window extraction failed: {e}", "WARNING")
            
        return "ERROR"
        
    def extract_from_main_screen(self) -> str:
        """Extract description from main MD04 screen."""
        try:
            # Common description field locations in MD04
            description_fields = [
                "wnd[0]/usr/txtMAKTX",
                "wnd[0]/usr/ctxtMAKTX", 
                "wnd[0]/usr/subSUB1:SAPLMD04:0300/txtMAKTX",
                "wnd[0]/usr/lbl[1,5]",
                "wnd[0]/usr/lbl[2,5]"
            ]
            
            for field_id in description_fields:
                try:
                    field = self.session.findById(field_id)
                    if field and hasattr(field, 'text') and field.text.strip():
                        description = field.text.strip()
                        self.log_message(f"Found description on main screen: {description}")
                        return description
                except:
                    continue
                    
        except Exception as e:
            self.log_message(f"Main screen extraction failed: {e}", "WARNING")
            
        return "ERROR"
        
    def extract_using_mm03(self, part_number: str) -> str:
        """Extract description using MM03 transaction."""
        try:
            self.log_message(f"Trying MM03 for {part_number}")
            
            # Execute MM03
            self.session.findById("wnd[0]/tbar[0]/okcd").text = "MM03"
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(2)
            
            # Enter material number
            self.session.findById("wnd[0]/usr/ctxtRMMG1-MATNR").text = part_number
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(3)
            
            # Extract description
            description_fields = [
                "wnd[0]/usr/tabsTABSTRIP_TABBLOCK/tabpTAB01/ssubTABFRAME1:SAPLMGMM:2001/subSUB1:SAPLMGMM:2003/txtRMMG1-MAKTX",
                "wnd[0]/usr/txtRMMG1-MAKTX",
                "wnd[0]/usr/ctxtRMMG1-MAKTX"
            ]
            
            for field_id in description_fields:
                try:
                    field = self.session.findById(field_id)
                    if field and field.text.strip():
                        description = field.text.strip()
                        self.log_message(f"MM03 description found: {description}")
                        return description
                except:
                    continue
                    
        except Exception as e:
            self.log_message(f"MM03 extraction failed: {e}", "WARNING")
            
        return "ERROR"
        
    def extract_material_type(self) -> str:
        """Extract material type if available."""
        try:
            material_type_fields = [
                "wnd[0]/usr/ctxtRMMG1-MTART",
                "wnd[0]/usr/txtMTART",
                "wnd[0]/usr/ctxtMTART"
            ]
            
            for field_id in material_type_fields:
                try:
                    field = self.session.findById(field_id)
                    if field and field.text.strip():
                        return field.text.strip()
                except:
                    continue
                    
        except Exception as e:
            self.log_message(f"Material type extraction failed: {e}", "WARNING")
            
        return ""
        
    def get_parts_list(self) -> List[str]:
        """Get list of parts from various input sources."""
        parts = []
        
        # Single part
        single_part = self.single_part_var.get().strip()
        if single_part:
            parts.append(single_part)
            
        # Multiple parts from text area
        text_content = self.parts_text.get("1.0", tk.END).strip()
        if text_content:
            text_parts = [part.strip() for part in text_content.split('\n') if part.strip()]
            parts.extend(text_parts)
            
        # Parts from Excel file
        file_path = self.file_path_var.get().strip()
        if file_path and os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                # Assume first column contains part numbers
                file_parts = df.iloc[:, 0].astype(str).tolist()
                file_parts = [part.strip() for part in file_parts if part.strip() and part.strip().lower() != 'nan']
                parts.extend(file_parts)
                self.log_message(f"Loaded {len(file_parts)} parts from Excel file")
            except Exception as e:
                self.log_message(f"Error reading Excel file: {e}", "ERROR")
                
        # Remove duplicates while preserving order
        unique_parts = []
        seen = set()
        for part in parts:
            if part not in seen:
                unique_parts.append(part)
                seen.add(part)
                
        return unique_parts
        
    def browse_file(self):
        """Browse for Excel file."""
        file_path = filedialog.askopenfilename(
            title="Select Excel file with part numbers",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if file_path:
            self.file_path_var.set(file_path)
            
    def start_automation(self):
        """Start the backend automation process."""
        # Validate connection
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        # Get parts list
        parts = self.get_parts_list()
        if not parts:
            messagebox.showerror("Error", "Please enter at least one part number!")
            return
            
        # Validate transaction
        transaction = self.transaction_var.get()
        if transaction not in ["MD04", "MD06", "MM03"]:
            messagebox.showerror("Error", "Please select a valid transaction!")
            return
            
        # Start automation
        self.is_running = True
        self.total_parts = len(parts)
        self.current_part_index = 0
        self.results.clear()
        
        # Update UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.save_btn.config(state="disabled")
        
        # Clear results tree
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Setup progress bar
        self.progress_bar.config(maximum=self.total_parts)
        self.progress_var.set(f"Starting backend automation for {self.total_parts} parts...")
        
        self.log_message(f"Starting backend automation for {self.total_parts} parts using {transaction}")
        self.log_message("Running in background - no mouse movement required!")
        
        # Run automation in separate thread with proper COM initialization
        threading.Thread(target=self.run_backend_automation_fixed, args=(parts, transaction), daemon=True).start()
        
    def run_backend_automation_fixed(self, parts: List[str], transaction: str):
        """Run the complete backend automation process - Fixed COM threading."""
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            start_time = datetime.now()
            
            for i, part in enumerate(parts):
                if not self.is_running:
                    self.log_message("Automation stopped by user")
                    break
                    
                self.current_part_index = i + 1
                
                # Update progress on GUI thread
                self.root.after(0, lambda: self.update_progress(part, i + 1))
                
                # Process the part
                if transaction == "MD04":
                    result = self.extract_part_data_md04(part)
                elif transaction == "MM03":
                    result = self.extract_part_data_mm03(part)
                elif transaction == "MD06":
                    result = self.extract_part_data_md06(part)
                else:
                    result = {
                        "part_number": part,
                        "description": f"ERROR: Unsupported transaction {transaction}",
                        "material_type": "ERROR",
                        "status": "ERROR",
                        "processing_time": 0,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "transaction": transaction
                    }
                
                self.results.append(result)
                
                # Update results tree on GUI thread
                self.root.after(0, lambda r=result: self.update_results_tree(r))
                
                # Brief pause between parts to avoid overwhelming SAP
                time.sleep(0.5)
                
            # Calculate final statistics
            total_time = (datetime.now() - start_time).total_seconds()
            successful = len([r for r in self.results if r["status"] == "SUCCESS"])
            failed = len([r for r in self.results if r["status"] == "ERROR"])
            
            # Update UI on completion
            self.root.after(0, lambda: self.automation_completed(successful, failed, total_time))
            
        except Exception as e:
            error_msg = f"Backend automation failed: {e}"
            self.log_message(error_msg, "ERROR")
            self.root.after(0, lambda: self.automation_error(error_msg))
        finally:
            # Uninitialize COM for this thread
            pythoncom.CoUninitialize()
            
    def extract_part_data_mm03(self, part_number: str) -> Dict[str, str]:
        """Extract part data using MM03 transaction - Fixed COM."""
        start_time = datetime.now()
        
        try:
            # Execute MM03 transaction
            if not self.execute_transaction("MM03"):
                raise Exception("Failed to execute MM03")
            
            # Enter material number
            self.session.findById("wnd[0]/usr/ctxtRMMG1-MATNR").text = part_number
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(3)
            
            # Extract basic data
            description = ""
            material_type = ""
            
            # Try to get description
            desc_fields = [
                "wnd[0]/usr/tabsTABSTRIP_TABBLOCK/tabpTAB01/ssubTABFRAME1:SAPLMGMM:2001/subSUB1:SAPLMGMM:2003/txtRMMG1-MAKTX",
                "wnd[0]/usr/txtRMMG1-MAKTX"
            ]
            
            for field_id in desc_fields:
                try:
                    field = self.session.findById(field_id)
                    if field and field.text.strip():
                        description = field.text.strip()
                        break
                except:
                    continue
                    
            # Try to get material type
            type_fields = [
                "wnd[0]/usr/tabsTABSTRIP_TABBLOCK/tabpTAB01/ssubTABFRAME1:SAPLMGMM:2001/subSUB1:SAPLMGMM:2003/ctxtRMMG1-MTART",
                "wnd[0]/usr/ctxtRMMG1-MTART"
            ]
            
            for field_id in type_fields:
                try:
                    field = self.session.findById(field_id)
                    if field and field.text.strip():
                        material_type = field.text.strip()
                        break
                except:
                    continue
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "part_number": part_number,
                "description": description if description else "No description found",
                "material_type": material_type,
                "status": "SUCCESS" if description else "PARTIAL",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MM03"
            }
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "part_number": part_number,
                "description": f"ERROR: {str(e)}",
                "material_type": "ERROR",
                "status": "ERROR",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MM03",
                "error": str(e)
            }
            
    def extract_part_data_md06(self, part_number: str) -> Dict[str, str]:
        """Extract part data using MD06 transaction - Fixed COM."""
        start_time = datetime.now()
        
        try:
            # Execute MD06 transaction
            if not self.execute_transaction("MD06"):
                raise Exception("Failed to execute MD06")
            
            # Enter material number (MD06 has similar structure to MD04)
            self.session.findById("wnd[0]/usr/ctxtRM61E-MATNR").text = part_number
            
            # Enter MRP Area if specified
            if self.mrp_area_var.get():
                self.session.findById("wnd[0]/usr/ctxtRM61E-BERID").text = self.mrp_area_var.get()
            
            # Execute
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(3)
            
            # Extract description using similar methods as MD04
            description = self.extract_description_multiple_methods(part_number)
            material_type = self.extract_material_type()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "part_number": part_number,
                "description": description,
                "material_type": material_type,
                "status": "SUCCESS" if description != "ERROR" else "ERROR",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MD06"
            }
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            return {
                "part_number": part_number,
                "description": f"ERROR: {str(e)}",
                "material_type": "ERROR",
                "status": "ERROR",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MD06",
                "error": str(e)
            }
            
    def update_progress(self, current_part: str, part_index: int):
        """Update progress display."""
        self.progress_bar.config(value=part_index)
        self.progress_var.set(f"Processing part {part_index}/{self.total_parts}...")
        self.current_part_var.set(f"Current: {current_part}")
        
    def update_results_tree(self, result: Dict[str, str]):
        """Update the results tree with new result."""
        # Truncate long descriptions for display
        display_desc = result["description"]
        if len(display_desc) > 80:
            display_desc = display_desc[:77] + "..."
            
        # Color coding based on status
        tags = []
        if result["status"] == "SUCCESS":
            tags.append("success")
        elif result["status"] == "ERROR":
            tags.append("error")
        else:
            tags.append("warning")
        
        self.results_tree.insert("", "end", values=(
            result["part_number"],
            display_desc,
            result["material_type"],
            result["status"],
            f"{result['processing_time']}s",
            result["timestamp"]
        ), tags=tags)
        
        # Configure tag colors
        self.results_tree.tag_configure("success", foreground="green")
        self.results_tree.tag_configure("error", foreground="red")
        self.results_tree.tag_configure("warning", foreground="orange")
        
    def automation_completed(self, successful: int, failed: int, total_time: float):
        """Handle automation completion."""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.save_btn.config(state="normal")
        
        # Update progress
        self.progress_bar.config(value=self.total_parts)
        self.progress_var.set(f"[OK] Completed! {successful} successful, {failed} failed")
        self.current_part_var.set(f"Total time: {total_time:.1f} seconds")
        
        # Log completion
        avg_time = total_time / self.total_parts if self.total_parts > 0 else 0
        self.log_message(f"Backend automation completed!")
        self.log_message(f"Results: {successful} successful, {failed} failed")
        self.log_message(f"Total time: {total_time:.1f}s, Average: {avg_time:.1f}s per part")
        
        # Show completion message
        messagebox.showinfo("Automation Complete", 
                           f"Backend automation completed!\n\n"
                           f"[OK] Successful: {successful}\n"
                           f"[X] Failed: {failed}\n"
                           f"Time: {total_time:.1f} seconds\n"
                           f"Average: {avg_time:.1f}s per part\n\n"
                           f"No mouse movement was required!")
        
    def automation_error(self, error_msg: str):
        """Handle automation errors."""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        self.progress_var.set("[X] Automation failed!")
        messagebox.showerror("Automation Error", f"Backend automation failed:\n\n{error_msg}")
        
    def stop_automation(self):
        """Stop the automation process."""
        self.is_running = False
        self.log_message("Stopping automation...")
        
    def save_results(self):
        """Save results to Excel file."""
        if not self.results:
            messagebox.showwarning("Warning", "No results to save!")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SAP_Backend_Results_{timestamp}.xlsx"
            
            # Create DataFrame
            df = pd.DataFrame(self.results)
            
            # Save to Excel with multiple sheets
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Main results
                df.to_excel(writer, sheet_name='Results', index=False)
                
                # Summary statistics
                total_parts = len(self.results)
                successful = len([r for r in self.results if r["status"] == "SUCCESS"])
                failed = len([r for r in self.results if r["status"] == "ERROR"])
                avg_time = sum([r["processing_time"] for r in self.results]) / total_parts
                
                summary_data = {
                    'Metric': [
                        'Total Parts Processed',
                        'Successful Extractions',
                        'Failed Extractions',
                        'Success Rate (%)',
                        'Average Processing Time (seconds)',
                        'Total Processing Time (seconds)',
                        'Automation Method',
                        'Transaction Used'
                    ],
                    'Value': [
                        total_parts,
                        successful,
                        failed,
                        round((successful / total_parts) * 100, 1),
                        round(avg_time, 2),
                        round(sum([r["processing_time"] for r in self.results]), 2),
                        'Backend (No Mouse Movement)',
                        self.transaction_var.get()
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Error details if any
                error_results = [r for r in self.results if r["status"] == "ERROR"]
                if error_results:
                    error_df = pd.DataFrame(error_results)
                    error_df.to_excel(writer, sheet_name='Errors', index=False)
            
            self.log_message(f"Results saved to: {filename}")
            messagebox.showinfo("Success", f"Results saved successfully!\n\nFile: {filename}")
            
        except Exception as e:
            error_msg = f"Failed to save results: {e}"
            self.log_message(error_msg, "ERROR")
            messagebox.showerror("Save Error", error_msg)
            
    def run(self):
        """Start the application."""
        self.log_message("SAP Backend Automation System Started - FIXED VERSION")
        self.log_message("This system uses SAP GUI Scripting API - no mouse movement required!")
        self.log_message("Please connect to SAP to begin...")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("Application closed by user")
        finally:
            # Clean up COM objects
            try:
                if self.session:
                    self.session = None
                if self.connection:
                    self.connection = None
                if self.application:
                    self.application = None
                if self.sap_gui_auto:
                    self.sap_gui_auto = None
                pythoncom.CoUninitialize()
            except:
                pass


def main():
    """Main function to run the fixed backend automation."""
    print("="*60)
    print("SAP Backend Automation - FIXED VERSION")
    print("="*60)
    print("Fixed Issues:")
    print("1. Unicode/Emoji encoding errors")
    print("2. COM threading 'CoInitialize' errors")
    print("3. Improved error handling")
    print("="*60)
    
    try:
        app = SAPBackendAutomationFixed()
        app.run()
    except Exception as e:
        print(f"[X] Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()