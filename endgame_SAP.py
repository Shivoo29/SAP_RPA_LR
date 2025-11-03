#!/usr/bin/env python3
"""
Fixed SAP Automation - Based on working endgame_SAP.py
=====================================================
Simple multi-part processing with data extraction and Excel export
- Uses your working SAP connection and field filling methods
- Simplified interface: MRP Area + Part Numbers text area + Start button
- Extracts specific data fields you specified
- Excel export with save dialog
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import win32com.client
import pythoncom
import pandas as pd
import time
import logging
import os
from datetime import datetime
from typing import List, Dict
import threading

class SimplifiedSAPAutomation:
    """
    Simplified SAP Automation based on working endgame_SAP.py
    """
    
    def __init__(self):
        # Field IDs from your working code
        self.field_ids = {
            "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR",
            "mrp_area_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-BERID",
        }
        
        # Data extraction field IDs (from your specifications)
        self.extraction_fields = {
            "Material": "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRESB-MATNR",
            "Part_Description": "/app/con[0]/ses[0]/wnd[0]/usr/subBLOCK:SAPLKACB:1002/txtTEXT_AUFNR", 
            "Recipient": "/app/con[0]/ses[0]/wnd[0]/usr/txtRESB-WEMPF",
            "Order": "/app/con[0]/ses[0]/wnd[0]/usr/subBLOCK:SAPLKACB:1002/ctxtCOBL-AUFNR"
        }
        
        # Next part field for loop processing
        self.next_part_field = "/app/con[0]/ses[0]/wnd[0]/usr/subINCLUDE8XX:SAPMM61R:0800/ctxtRM61R-MATNR"
        
        # SAP Connection and Data
        self.session = None
        self.extracted_data = []
        self.is_running = False
        
        # Setup
        self.setup_logging()
        self.setup_gui()
        
    def setup_logging(self):
        """Setup logging system."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/simplified_sap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
    def setup_gui(self):
        """Setup the GUI interface."""
        self.root = tk.Tk()
        self.root.title("SAP Automation - Multi-Part Processing")
        self.root.geometry("1000x800")
        
        try:
            self.root.state('zoomed')
        except:
            pass
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, 
                               text="SAP Automation - Multi-Part Processing with Excel Export", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        # SAP Connection
        connection_frame = ttk.LabelFrame(main_container, text="SAP Connection", padding="15")
        connection_frame.pack(fill=tk.X, pady=(0, 15))
        
        conn_inner = ttk.Frame(connection_frame)
        conn_inner.pack(fill=tk.X)
        
        self.connection_status_var = tk.StringVar(value="Not Connected to SAP")
        status_label = ttk.Label(conn_inner, textvariable=self.connection_status_var,
                                font=("Arial", 11, "bold"))
        status_label.pack(side=tk.LEFT)
        
        connect_btn = ttk.Button(conn_inner, text="Connect to SAP Dashboard",
                                command=self.connect_to_sap)
        connect_btn.pack(side=tk.RIGHT)
        
        # Input Section
        input_frame = ttk.LabelFrame(main_container, text="Input", padding="15")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # MRP Area
        mrp_frame = ttk.Frame(input_frame)
        mrp_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(mrp_frame, text="MRP Area:", font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        self.mrp_area_var = tk.StringVar(value="1000")
        mrp_entry = ttk.Entry(mrp_frame, textvariable=self.mrp_area_var, width=15)
        mrp_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Part Numbers
        ttk.Label(input_frame, text="Part Numbers (one per line):", font=("Arial", 11, "bold")).pack(anchor=tk.W)
        
        self.parts_text = scrolledtext.ScrolledText(input_frame, height=8, width=60, font=("Consolas", 10))
        self.parts_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Add sample data
        sample_parts = "857-A65473-106\n684-B20512-006\n813-B97886-001\n660-300316-500"
        self.parts_text.insert("1.0", sample_parts)
        
        # Controls
        control_frame = ttk.LabelFrame(main_container, text="Controls", padding="15")
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        control_inner = ttk.Frame(control_frame)
        control_inner.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(control_inner, text="Start Automation",
                                   command=self.start_automation)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_btn = ttk.Button(control_inner, text="Stop Automation", 
                                  command=self.stop_automation, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.export_btn = ttk.Button(control_inner, text="Export to Excel",
                                    command=self.export_to_excel, state="disabled")
        self.export_btn.pack(side=tk.RIGHT)
        
        # Progress
        self.progress_var = tk.StringVar(value="Ready to process")
        progress_label = ttk.Label(control_frame, textvariable=self.progress_var)
        progress_label.pack(pady=(10, 0))
        
        # Log Section
        log_frame = ttk.LabelFrame(main_container, text="Processing Log", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=100, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to GUI log and logger."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        safe_message = str(message).encode('ascii', 'replace').decode('ascii')
        log_entry = f"[{timestamp}] {level}: {safe_message}\n"
        
        # Add to GUI
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Add to file logger
        if hasattr(self, 'logger'):
            if level == "INFO":
                self.logger.info(safe_message)
            elif level == "ERROR":
                self.logger.error(safe_message)
            elif level == "WARNING":
                self.logger.warning(safe_message)
        
        # Update GUI
        self.root.update_idletasks()
        
    def connect_to_sap(self) -> bool:
        """Connect to SAP dashboard - from your working code."""
        try:
            pythoncom.CoInitialize()
            
            self.log_message("Connecting to SAP dashboard...")
            
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
                    
                    self.connection_status_var.set(f"Connected: {system_name} Client {client} User {user}")
                    self.log_message(f"Successfully connected to SAP: {system_name} Client {client} User {user}")
                    
                    return True
            
            raise Exception("No SAP sessions found")
            
        except Exception as e:
            error_msg = str(e)
            self.connection_status_var.set("Connection Failed")
            self.log_message(f"Failed to connect to SAP: {error_msg}", "ERROR")
            messagebox.showerror("SAP Connection Error", f"Failed to connect:\n{error_msg}")
            return False
    
    def verify_sap_session(self) -> bool:
        """Verify SAP session is still valid."""
        try:
            if not self.session:
                return False
            
            # Try to access session info to verify it's still active
            info = self.session.Info
            system_name = info.SystemName
            return True
            
        except Exception as e:
            self.log_message(f"SAP session verification failed: {e}", "ERROR")
            return False
    
    def start_automation(self):
        """Start the automation process."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        # Get part numbers
        parts_text = self.parts_text.get("1.0", tk.END).strip()
        if not parts_text:
            messagebox.showerror("Error", "Please enter part numbers!")
            return
        
        part_numbers = [part.strip() for part in parts_text.split('\n') if part.strip()]
        if not part_numbers:
            messagebox.showerror("Error", "No valid part numbers found!")
            return
        
        mrp_area = self.mrp_area_var.get().strip()
        if not mrp_area:
            messagebox.showerror("Error", "Please enter MRP Area!")
            return
        
        # Confirm start
        result = messagebox.askyesno("Confirm Processing", 
                                   f"Process {len(part_numbers)} part numbers?\n"
                                   f"MRP Area: {mrp_area}")
        
        if not result:
            return
        
        self.log_message(f"Starting automation for {len(part_numbers)} parts...")
        self.is_running = True
        self.extracted_data = []
        
        # Update UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")
        
        # Start processing in main thread with UI updates
        self.part_numbers_queue = part_numbers
        self.mrp_area_queue = mrp_area
        self.current_part_index = 0
        
        # Start the processing loop
        self.process_next_part_in_queue()
    
    def process_next_part_in_queue(self):
        """Process next part in queue using main thread to avoid COM issues."""
        try:
            if not self.is_running or self.current_part_index >= len(self.part_numbers_queue):
                # Processing completed
                self.finish_processing()
                return
            
            part_number = self.part_numbers_queue[self.current_part_index]
            total_parts = len(self.part_numbers_queue)
            
            # Update progress
            self.progress_var.set(f"Processing {self.current_part_index + 1}/{total_parts}: {part_number}")
            self.log_message(f"Processing part {self.current_part_index + 1}/{total_parts}: {part_number}")
            
            # Process this part
            try:
                if self.current_part_index == 0:
                    # First part
                    data = self.process_first_part(part_number, self.mrp_area_queue)
                else:
                    # Subsequent parts
                    data = self.process_next_part(part_number)
                
                if data:
                    self.extracted_data.append(data)
                    self.log_message(f"Successfully processed: {part_number}")
                else:
                    # Add empty record for failed part
                    empty_data = {col: part_number if col == 'Material' else '' for col in self.extraction_fields.keys()}
                    self.extracted_data.append(empty_data)
                    self.log_message(f"Failed to process (added empty record): {part_number}", "WARNING")
                    
            except Exception as e:
                self.log_message(f"Error processing {part_number}: {e}", "ERROR")
                empty_data = {col: part_number if col == 'Material' else '' for col in self.extraction_fields.keys()}
                self.extracted_data.append(empty_data)
            
            # Move to next part
            self.current_part_index += 1
            
            # Schedule next part processing after a short delay
            self.root.after(2000, self.process_next_part_in_queue)  # 2 second delay
            
        except Exception as e:
            self.log_message(f"Error in processing queue: {e}", "ERROR")
            self.finish_processing()
    
    def finish_processing(self):
        """Finish the processing and update UI."""
        total_parts = len(self.part_numbers_queue) if hasattr(self, 'part_numbers_queue') else 0
        successful_parts = len([d for d in self.extracted_data if any(v for k, v in d.items() if k != 'Material' and v)])
        
        self.log_message("="*60)
        self.log_message(f"Processing completed! Total: {total_parts}, Successful: {successful_parts}")
        
        self.progress_var.set(f"Completed: {successful_parts}/{total_parts}")
        self.automation_finished()
    
    def run_automation(self, part_numbers: List[str], mrp_area: str):
        """Run automation for all parts."""
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            # Verify SAP session is still valid
            if not self.verify_sap_session():
                self.log_message("SAP session is no longer valid, attempting to reconnect...", "ERROR")
                if not self.connect_to_sap():
                    self.log_message("Failed to reconnect to SAP", "ERROR")
                    return
            
            total_parts = len(part_numbers)
            successful_parts = 0
            
            self.log_message("="*60)
            
            for index, part_number in enumerate(part_numbers):
                if not self.is_running:
                    self.log_message("Processing stopped by user")
                    break
                
                # Update progress
                self.root.after(0, lambda i=index, p=part_number, t=total_parts: 
                               self.progress_var.set(f"Processing {i+1}/{t}: {p}"))
                
                self.log_message(f"Processing part {index + 1}/{total_parts}: {part_number}")
                
                try:
                    if index == 0:
                        # First part: Start from MD04
                        data = self.process_first_part(part_number, mrp_area)
                    else:
                        # Subsequent parts: Use loop method
                        data = self.process_next_part(part_number)
                    
                    if data:
                        self.extracted_data.append(data)
                        successful_parts += 1
                        self.log_message(f"Successfully processed: {part_number}")
                    else:
                        # Add empty record for failed part
                        empty_data = {col: part_number if col == 'Material' else '' for col in self.extraction_fields.keys()}
                        self.extracted_data.append(empty_data)
                        self.log_message(f"Failed to process (added empty record): {part_number}", "WARNING")
                    
                except Exception as e:
                    self.log_message(f"Error processing {part_number}: {e}", "ERROR")
                    empty_data = {col: part_number if col == 'Material' else '' for col in self.extraction_fields.keys()}
                    self.extracted_data.append(empty_data)
                
                time.sleep(2)  # Pause between parts
            
            self.log_message("="*60)
            self.log_message(f"Processing completed! Total: {total_parts}, Successful: {successful_parts}")
            
            self.root.after(0, lambda: self.progress_var.set(f"Completed: {successful_parts}/{total_parts}"))
            
        except Exception as e:
            self.log_message(f"Automation failed: {e}", "ERROR")
        finally:
            # Clean up COM for this thread
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            self.root.after(0, self.automation_finished)
    
    def process_first_part(self, part_number: str, mrp_area: str) -> Dict:
        """Process first part starting from MD04."""
        try:
            # Step 1: Navigate to MD04
            self.ensure_md04_screen()
            
            # Step 2: Fill fields
            if not self.fill_field_safely("material_field", part_number):
                raise Exception("Failed to fill material field")
            
            if not self.fill_field_safely("mrp_area_field", mrp_area):
                self.log_message("Failed to fill MRP area, continuing...", "WARNING")
            
            # Step 3: Execute query
            if not self.execute_query_automatically():
                raise Exception("Failed to execute query")
            
            # Step 4: Find MatRes and F7
            if not self.find_and_focus_matres_automatically():
                self.log_message("MatRes element not found", "ERROR")
                return None
            
            time.sleep(1)
            if not self.press_f7_automatically():
                self.log_message("Failed to press F7", "WARNING")
            
            # Step 5: Extract data
            time.sleep(3)
            data = self.extract_data_from_page()
            
            return data
            
        except Exception as e:
            self.log_message(f"Error processing first part {part_number}: {e}", "ERROR")
            return None
    
    def process_next_part(self, part_number: str) -> Dict:
        """Process subsequent parts using loop method."""
        try:
            # Step 1: Press F3 to go back
            self.log_message("Pressing F3 to go back...")
            self.session.findById("wnd[0]").sendVKey(15)  # F3 key
            time.sleep(2)
            
            # Step 2: Try multiple possible next part field locations
            self.log_message(f"Filling next part field with: {part_number}")
            
            # List of possible field IDs to try
            possible_fields = [
                "/app/con[0]/ses[0]/wnd[0]/usr/subINCLUDE8XX:SAPMM61R:0800/ctxtRM61R-MATNR",  # Original
                "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR",  # Main field
                "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-MATNR",  # Alternative
                "/app/con[0]/ses[0]/wnd[0]/usr/subINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR"  # Another possibility
            ]
            
            field_filled = False
            for field_id in possible_fields:
                try:
                    field = self.session.findById(field_id)
                    field.text = part_number
                    field.caretPosition = len(part_number)
                    time.sleep(0.5)
                    self.log_message(f"Successfully filled field using: {field_id}")
                    field_filled = True
                    break
                except Exception as e:
                    self.log_message(f"Field {field_id} not found: {e}", "WARNING")
                    continue
            
            if not field_filled:
                # Try going back to MD04 and filling the main field
                self.log_message("All next part fields failed, trying MD04 main field...")
                try:
                    # Navigate to MD04
                    self.session.findById("wnd[0]/tbar[0]/okcd").text = "MD04"
                    self.session.findById("wnd[0]").sendVKey(0)
                    time.sleep(3)
                    
                    # Fill main material field
                    main_field = self.session.findById("/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR")
                    main_field.text = part_number
                    time.sleep(0.5)
                    field_filled = True
                    self.log_message("Successfully filled main MD04 field")
                except Exception as e:
                    raise Exception(f"Failed to fill any part field: {e}")
            
            if not field_filled:
                raise Exception("Failed to fill next part field")
            
            # Step 3: Press Enter
            self.session.findById("wnd[0]").sendVKey(0)  # Enter
            time.sleep(3)
            
            # Step 4: Find MatRes and F7
            if not self.find_and_focus_matres_automatically():
                return None
            
            time.sleep(1)
            if not self.press_f7_automatically():
                self.log_message("Failed to press F7", "WARNING")
            
            # Step 5: Extract data
            time.sleep(3)
            data = self.extract_data_from_page()
            
            return data
            
        except Exception as e:
            self.log_message(f"Error processing next part {part_number}: {e}", "ERROR")
            return None
    
    def extract_data_from_page(self) -> Dict:
        """Extract data using your specified field IDs."""
        try:
            self.log_message("Extracting data from page...")
            
            data = {}
            
            for field_name, field_id in self.extraction_fields.items():
                try:
                    field = self.session.findById(field_id)
                    value = getattr(field, 'text', '').strip()
                    data[field_name] = value
                    self.log_message(f"Extracted {field_name}: {value}")
                except Exception as e:
                    self.log_message(f"Failed to extract {field_name}: {e}", "WARNING")
                    data[field_name] = ''
            
            return data
            
        except Exception as e:
            self.log_message(f"Error extracting data: {e}", "ERROR")
            return None
    
    # Your working methods from endgame_SAP.py
    def ensure_md04_screen(self):
        """Ensure we're on MD04 screen."""
        try:
            # Re-verify session before accessing
            if not self.verify_sap_session():
                raise Exception("SAP session is not valid")
                
            current_transaction = self.session.Info.Transaction
            if current_transaction.upper() != "MD04":
                self.log_message("Navigating to MD04...")
                self.session.findById("wnd[0]/tbar[0]/okcd").text = "MD04"
                self.session.findById("wnd[0]").sendVKey(0)
                time.sleep(3)
            
            try:
                individual_tab = self.session.findById("wnd[0]/usr/tabsTAB300/tabpF01")
                individual_tab.select()
                time.sleep(1)
                self.log_message("Individual access tab selected")
            except Exception as e:
                self.log_message(f"Could not select Individual tab: {e}", "WARNING")
                
        except Exception as e:
            self.log_message(f"Error ensuring MD04 screen: {e}", "ERROR")
            raise e
    
    def fill_field_safely(self, field_name: str, value: str) -> bool:
        """Fill field using your working methods."""
        try:
            field_id = self.field_ids[field_name]
            self.log_message(f"Filling {field_name} with: '{value}'")
            
            field = self.session.findById(field_id)
            
            if not hasattr(field, 'text'):
                return False
            
            # Try methods from your working code
            methods = [
                self._method_direct_assignment,
                self._method_focus_and_assign,
                self._method_sap_changeable_field,
            ]
            
            for method in methods:
                try:
                    if method(field, value):
                        current_value = getattr(field, 'text', '').strip()
                        if current_value == value:
                            return True
                except Exception:
                    continue
            
            return False
            
        except Exception as e:
            self.log_message(f"Error filling {field_name}: {e}", "ERROR")
            return False
    
    def _method_direct_assignment(self, field, value: str) -> bool:
        field.text = value
        time.sleep(0.5)
        return True
    
    def _method_focus_and_assign(self, field, value: str) -> bool:
        field.setFocus()
        time.sleep(0.3)
        field.text = value
        time.sleep(0.5)
        return True
    
    def _method_sap_changeable_field(self, field, value: str) -> bool:
        try:
            field.setFocus()
            time.sleep(0.3)
            field.text = value
            time.sleep(0.3)
            self.session.findById("wnd[0]").sendVKey(1)  # Tab
            time.sleep(0.3)
            return True
        except Exception:
            return False
    
    def execute_query_automatically(self) -> bool:
        """Execute query by pressing Enter."""
        try:
            self.log_message("Executing query by pressing Enter...")
            main_window = self.session.findById("wnd[0]")
            main_window.setFocus()
            time.sleep(0.5)
            self.session.findById("wnd[0]").sendVKey(0)  # Enter
            time.sleep(4)
            return True
        except Exception as e:
            self.log_message(f"Query execution failed: {e}", "ERROR")
            return False
    
    def find_and_focus_matres_automatically(self) -> bool:
        """Find and focus MatRes element."""
        try:
            self.log_message("Scanning for MatRes element...")
            main_window = self.session.findById("wnd[0]")
            matres_element = self.scan_for_matres_element(main_window, 0)
            
            if matres_element:
                matres_element.setFocus()
                time.sleep(0.5)
                return True
            else:
                return False
                
        except Exception as e:
            self.log_message(f"Error finding MatRes: {e}", "ERROR")
            return False
    
    def scan_for_matres_element(self, element, depth):
        """Scan for MatRes element."""
        if depth > 10:
            return None
            
        try:
            if hasattr(element, 'text'):
                text = element.text.strip()
                if text == 'MatRes':
                    return element
            
            try:
                children_count = element.Children.Count
                for i in range(children_count):
                    try:
                        child = element.Children(i)
                        result = self.scan_for_matres_element(child, depth + 1)
                        if result:
                            return result
                    except:
                        continue
            except:
                pass
                
        except:
            pass
            
        return None
    
    def press_f7_automatically(self) -> bool:
        """Press F7 to maximize."""
        try:
            self.log_message("Pressing F7 to maximize...")
            main_window = self.session.findById("wnd[0]")
            main_window.setFocus()
            time.sleep(0.3)
            self.session.findById("wnd[0]").sendVKey(7)  # F7
            time.sleep(2)
            return True
        except Exception as e:
            self.log_message(f"Failed to press F7: {e}", "ERROR")
            return False
    
    def stop_automation(self):
        """Stop automation."""
        self.is_running = False
        self.log_message("Automation stopped by user")
    
    def automation_finished(self):
        """Handle automation completion."""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        if self.extracted_data:
            self.export_btn.config(state="normal")
            messagebox.showinfo("Processing Complete", 
                               f"Processing completed!\nExtracted data for {len(self.extracted_data)} parts.")
    
    def export_to_excel(self):
        """Export to Excel with save dialog."""
        try:
            if not self.extracted_data:
                messagebox.showwarning("No Data", "No data to export!")
                return
            
            # Windows save dialog (fixed parameters)
            file_path = filedialog.asksaveasfilename(
                title="Save Excel Report",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"SAP_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if not file_path:
                return
            
            self.log_message(f"Exporting to: {file_path}")
            
            # Create and save Excel
            df = pd.DataFrame(self.extracted_data)
            df.to_excel(file_path, index=False)
            
            self.log_message(f"Successfully exported {len(self.extracted_data)} records")
            
            # Ask to open
            result = messagebox.askyesno("Export Complete", 
                                       f"Data exported successfully!\n\nOpen Excel file?")
            
            if result:
                try:
                    os.startfile(file_path)
                except Exception as e:
                    self.log_message(f"Could not open file: {e}", "WARNING")
            
        except Exception as e:
            self.log_message(f"Export failed: {e}", "ERROR")
            messagebox.showerror("Export Error", f"Failed to export:\n{e}")
    
    def run(self):
        """Run the application."""
        self.log_message("SAP Automation Started - Multi-Part Processing")
        self.root.mainloop()


def main():
    """Main function."""
    print("="*60)
    print("SAP AUTOMATION - MULTI-PART PROCESSING")
    print("="*60)
    
    try:
        app = SimplifiedSAPAutomation()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()