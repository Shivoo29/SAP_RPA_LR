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

class SAPBackendSingleThread:
    """
    SAP Backend Automation - Single Thread Version (No Threading Issues!)
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
        self.results = []
        
    def setup_logging(self):
        """Setup logging system without Unicode characters."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/sap_single_thread_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Setup file handler with UTF-8 encoding
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Setup console handler with safe encoding
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def load_config(self):
        """Load configuration."""
        default_config = {
            "default_values": {
                "mrp_area": "1000",
                "plant": ""
            }
        }
        
        config_file = "sap_single_thread_config.json"
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
        self.root.title("SAP Backend Automation - Single Thread (FIXED)")
        self.root.geometry("900x700")
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, 
                               text="SAP Backend Automation - Single Thread Fix", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="No threading issues - Direct COM automation!",
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
        
        # Control Buttons
        control_frame = ttk.Frame(main_container)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="START Automation (Single Thread)",
                                   command=self.start_automation_single_thread)
        self.start_btn.pack(side=tk.LEFT)
        
        self.save_btn = ttk.Button(control_frame, text="Save Results",
                                  command=self.save_results, state="disabled")
        self.save_btn.pack(side=tk.RIGHT)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_container, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to start automation...")
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
        columns = ("Part Number", "Description", "Status", "Processing Time", "Timestamp")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Description":
                self.results_tree.column(col, width=400)
            elif col == "Part Number":
                self.results_tree.column(col, width=150)
            else:
                self.results_tree.column(col, width=120)
        
        # Scrollbars for results
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
            
        # Update GUI immediately
        self.root.update_idletasks()
            
    def connect_to_sap_gui(self) -> bool:
        """Connect to SAP GUI using COM interface - Main thread only."""
        try:
            # Initialize COM for main thread
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
            
            messagebox.showerror("SAP Connection Error", 
                               f"Failed to connect to SAP GUI:\n\n{error_msg}\n\n"
                               "Please ensure:\n"
                               "1. SAP Logon is running\n"
                               "2. You are logged into SAP\n"
                               "3. SAP GUI Scripting is enabled")
            return False
            
    def test_sap_connection(self):
        """Test SAP connection and basic functionality."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        try:
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
                messagebox.showinfo("Success", "SAP connection test successful!\n\nSingle-thread automation is ready!")
            else:
                self.log_message("SAP connection test failed!", "ERROR")
                messagebox.showerror("Error", "SAP connection test failed!")
                
        except Exception as e:
            self.log_message(f"Connection test error: {e}", "ERROR")
            messagebox.showerror("Error", f"Connection test failed:\n{e}")
            
    def execute_transaction(self, tcode: str) -> bool:
        """Execute SAP transaction using GUI scripting - Main thread."""
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
        """Extract part data using MD04 transaction - Main thread only."""
        start_time = datetime.now()
        
        try:
            self.log_message(f"Processing part: {part_number}")
            
            # Execute MD04 transaction
            if not self.execute_transaction("MD04"):
                raise Exception("Failed to execute MD04")
            
            # Enter material number
            try:
                self.session.findById("wnd[0]/usr/ctxtRM61E-MATNR").text = part_number
                self.log_message(f"Entered material number: {part_number}")
            except Exception as e:
                self.log_message(f"Could not enter material number: {e}", "ERROR")
                raise Exception(f"Could not enter material number: {e}")
            
            # Enter MRP Area if specified
            if self.mrp_area_var.get():
                try:
                    self.session.findById("wnd[0]/usr/ctxtRM61E-BERID").text = self.mrp_area_var.get()
                    self.log_message(f"Entered MRP area: {self.mrp_area_var.get()}")
                except:
                    self.log_message("Could not enter MRP area (may not be required)", "WARNING")
            
            # Execute the query
            self.log_message("Executing query...")
            self.session.findById("wnd[0]").sendVKey(0)  # Press Enter
            time.sleep(3)  # Wait for results
            
            # Check for error messages first
            error_msg = self.check_for_errors()
            if error_msg:
                raise Exception(f"SAP Error: {error_msg}")
            
            # Extract description using multiple methods
            description = self.extract_description_all_methods(part_number)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                "part_number": part_number,
                "description": description,
                "status": "SUCCESS" if description and "ERROR" not in description else "ERROR",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MD04"
            }
            
            if result["status"] == "SUCCESS":
                self.log_message(f"[OK] Successfully extracted: {description[:50]}...")
            else:
                self.log_message(f"[X] Failed to extract description for {part_number}")
            
            return result
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            result = {
                "part_number": part_number,
                "description": f"ERROR: {error_msg}",
                "status": "ERROR",
                "processing_time": round(processing_time, 2),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "transaction": "MD04",
                "error": error_msg
            }
            
            self.log_message(f"[X] Failed to extract data for {part_number}: {error_msg}", "ERROR")
            return result
            
    def check_for_errors(self) -> str:
        """Check for SAP error messages."""
        try:
            # Check for error popup windows
            error_windows = ["wnd[1]", "wnd[2]"]
            
            for window_id in error_windows:
                try:
                    window = self.session.findById(window_id)
                    if window and window.text:
                        window_text = window.text
                        if any(keyword in window_text.lower() for keyword in ['error', 'fehler', 'warning']):
                            self.log_message(f"Error window detected: {window_text}")
                            # Try to close the error window
                            try:
                                window.sendVKey(0)  # Press Enter to close
                            except:
                                pass
                            return window_text
                except:
                    continue
                    
            # Check status bar for errors
            try:
                status_bar = self.session.findById("wnd[0]/sbar")
                if status_bar and status_bar.text:
                    status_text = status_bar.text
                    if any(keyword in status_text.lower() for keyword in ['error', 'not found', 'does not exist']):
                        self.log_message(f"Status bar error: {status_text}")
                        return status_text
            except:
                pass
                
        except Exception as e:
            self.log_message(f"Error checking for SAP errors: {e}", "WARNING")
            
        return ""
        
    def extract_description_all_methods(self, part_number: str) -> str:
        """Try all methods to extract part description."""
        
        # Method 1: Look for results grid and double-click
        try:
            self.log_message("Method 1: Checking results grid...")
            grid = self.session.findById("wnd[0]/usr/cntlGRID1/shellcont/shell")
            if grid:
                row_count = grid.RowCount
                self.log_message(f"Found results grid with {row_count} rows")
                
                if row_count > 0:
                    # Select and double-click first row
                    grid.currentCellRow = 0
                    grid.selectedRows = "0"
                    grid.doubleClickCurrentCell()
                    time.sleep(2)
                    
                    # Check detail window
                    description = self.extract_from_detail_window()
                    if description and description != "ERROR":
                        return description
                        
        except Exception as e:
            self.log_message(f"Method 1 failed: {e}", "WARNING")
        
        # Method 2: Look on main screen
        try:
            self.log_message("Method 2: Checking main screen...")
            description = self.extract_from_main_screen()
            if description and description != "ERROR":
                return description
        except Exception as e:
            self.log_message(f"Method 2 failed: {e}", "WARNING")
        
        # Method 3: Try MM03 for description
        try:
            self.log_message("Method 3: Trying MM03...")
            description = self.extract_using_mm03(part_number)
            if description and description != "ERROR":
                return description
        except Exception as e:
            self.log_message(f"Method 3 failed: {e}", "WARNING")
        
        return "ERROR: Could not extract description using any method"
        
    def extract_from_detail_window(self) -> str:
        """Extract description from detail window."""
        try:
            detail_windows = ["wnd[1]", "wnd[2]"]
            
            for window_id in detail_windows:
                try:
                    window = self.session.findById(window_id)
                    if window:
                        self.log_message(f"Found detail window: {window_id}")
                        
                        # Common description field locations
                        description_fields = [
                            f"{window_id}/usr/subSUB0:SAPLMGMM:2001/subSUB0:SAPLMGMM:2003/txtRMMG1-MAKTX",
                            f"{window_id}/usr/txtMAKTX",
                            f"{window_id}/usr/ctxtMAKTX",
                            f"{window_id}/usr/txtRMMG1-MAKTX"
                        ]
                        
                        for field_id in description_fields:
                            try:
                                field = self.session.findById(field_id)
                                if field and field.text.strip():
                                    description = field.text.strip()
                                    self.log_message(f"Found description: {description}")
                                    
                                    # Close detail window
                                    window.close()
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
            description_fields = [
                "wnd[0]/usr/txtMAKTX",
                "wnd[0]/usr/ctxtMAKTX", 
                "wnd[0]/usr/subSUB1:SAPLMD04:0300/txtMAKTX"
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
            if not self.execute_transaction("MM03"):
                return "ERROR"
            
            # Enter material number
            self.session.findById("wnd[0]/usr/ctxtRMMG1-MATNR").text = part_number
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(3)
            
            # Check for errors
            error_msg = self.check_for_errors()
            if error_msg:
                return f"ERROR: {error_msg}"
            
            # Extract description
            description_fields = [
                "wnd[0]/usr/tabsTABSTRIP_TABBLOCK/tabpTAB01/ssubTABFRAME1:SAPLMGMM:2001/subSUB1:SAPLMGMM:2003/txtRMMG1-MAKTX",
                "wnd[0]/usr/txtRMMG1-MAKTX"
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
        
    def get_parts_list(self) -> List[str]:
        """Get list of parts from input sources."""
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
                
        # Remove duplicates while preserving order
        unique_parts = []
        seen = set()
        for part in parts:
            if part not in seen:
                unique_parts.append(part)
                seen.add(part)
                
        return unique_parts
        
    def start_automation_single_thread(self):
        """Start automation in single thread - NO THREADING ISSUES!"""
        # Validate connection
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        # Get parts list
        parts = self.get_parts_list()
        if not parts:
            messagebox.showerror("Error", "Please enter at least one part number!")
            return
            
        # Clear previous results
        self.results.clear()
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        # Setup progress
        total_parts = len(parts)
        self.progress_bar.config(maximum=total_parts)
        self.progress_var.set(f"Starting single-thread automation for {total_parts} parts...")
        
        # Disable start button
        self.start_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        
        self.log_message(f"Starting single-thread automation for {total_parts} parts")
        self.log_message("Running in main thread - no threading issues!")
        
        start_time = datetime.now()
        
        try:
            # Process each part in main thread
            for i, part in enumerate(parts):
                # Update progress
                self.progress_bar.config(value=i + 1)
                self.progress_var.set(f"Processing part {i+1}/{total_parts}...")
                self.current_part_var.set(f"Current: {part}")
                self.root.update_idletasks()  # Update GUI
                
                # Process the part
                transaction = self.transaction_var.get()
                if transaction == "MD04":
                    result = self.extract_part_data_md04(part)
                else:
                    result = {
                        "part_number": part,
                        "description": f"ERROR: Transaction {transaction} not implemented yet",
                        "status": "ERROR",
                        "processing_time": 0,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "transaction": transaction
                    }
                
                self.results.append(result)
                
                # Update results tree
                self.update_results_tree(result)
                
                # Small delay between parts
                time.sleep(0.5)
                
            # Calculate statistics
            total_time = (datetime.now() - start_time).total_seconds()
            successful = len([r for r in self.results if r["status"] == "SUCCESS"])
            failed = len([r for r in self.results if r["status"] == "ERROR"])
            
            # Update final status
            self.progress_var.set(f"[OK] Completed! {successful} successful, {failed} failed")
            self.current_part_var.set(f"Total time: {total_time:.1f} seconds")
            
            self.log_message(f"[OK] Single-thread automation completed!")
            self.log_message(f"Results: {successful} successful, {failed} failed")
            self.log_message(f"Total time: {total_time:.1f}s")
            
            # Show completion message
            messagebox.showinfo("Automation Complete", 
                               f"Single-thread automation completed!\n\n"
                               f"[OK] Successful: {successful}\n"
                               f"[X] Failed: {failed}\n"
                               f"Time: {total_time:.1f} seconds\n"
                               f"No threading issues!")
            
        except Exception as e:
            self.log_message(f"Automation error: {e}", "ERROR")
            messagebox.showerror("Automation Error", f"Automation failed:\n\n{e}")
        finally:
            # Re-enable buttons
            self.start_btn.config(state="normal")
            self.save_btn.config(state="normal")
            
    def update_results_tree(self, result: Dict[str, str]):
        """Update the results tree with new result."""
        # Truncate long descriptions for display
        display_desc = result["description"]
        if len(display_desc) > 100:
            display_desc = display_desc[:97] + "..."
            
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
            result["status"],
            f"{result['processing_time']}s",
            result["timestamp"]
        ), tags=tags)
        
        # Configure tag colors
        self.results_tree.tag_configure("success", foreground="green")
        self.results_tree.tag_configure("error", foreground="red")
        self.results_tree.tag_configure("warning", foreground="orange")
        
        # Scroll to show new item
        children = self.results_tree.get_children()
        if children:
            self.results_tree.see(children[-1])
        
    def save_results(self):
        """Save results to Excel file."""
        if not self.results:
            messagebox.showwarning("Warning", "No results to save!")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"SAP_SingleThread_Results_{timestamp}.xlsx"
            
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
                avg_time = sum([r["processing_time"] for r in self.results]) / total_parts if total_parts > 0 else 0
                
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
                        round((successful / total_parts) * 100, 1) if total_parts > 0 else 0,
                        round(avg_time, 2),
                        round(sum([r["processing_time"] for r in self.results]), 2),
                        'Single Thread (No Threading Issues)',
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
        self.log_message("SAP Backend Automation - Single Thread Version Started")
        self.log_message("This version runs in main thread - NO THREADING ISSUES!")
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
    """Main function to run the single-thread automation."""
    print("="*60)
    print("SAP Backend Automation - SINGLE THREAD FIX")
    print("="*60)
    print("This version solves the threading marshalling issue!")
    print("All automation runs in the main thread.")
    print("No more 'marshalled for a different thread' errors!")
    print("="*60)
    
    try:
        app = SAPBackendSingleThread()
        app.run()
    except Exception as e:
        print(f"[X] Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()