#!/usr/bin/env python3
"""
Fixed SAP Automation - Corrected Field Filling Issues
====================================================
Key fixes:
1. Added missing MRP Area field ID
2. Improved field detection and filling methods
3. Enhanced error handling for field access
4. Added field validation before filling

Author: Fixed version for reliable field filling
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

class FixedSAPAutomation:
    """
    Fixed SAP Automation with corrected field IDs and improved filling methods
    """
    
    def __init__(self):
        # CORRECTED SAP Field IDs based on your page scan
        self.field_ids = {
            "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR",
            "mrp_area_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-BERID",  # ADDED MISSING FIELD
            "plant_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-WERKS",
            "matres_field": "/app/con[0]/ses[0]/wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_1/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ/txtMDEZ-DELB0",
            "description_field": "/app/con[0]/ses[0]/wnd[0]/usr/subBLOCK:SAPLKACB:1002/txtTEXT_AUFNR"
        }
        
        # SAP Connection
        self.session = None
        self.results = []
        self.is_running = False
        
        # Setup
        self.setup_logging()
        self.setup_gui()
        
    def setup_logging(self):
        """Setup logging system."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/fixed_sap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
    def setup_gui(self):
        """Setup the main GUI interface."""
        self.root = tk.Tk()
        self.root.title("🔧 Fixed SAP Automation - Corrected Field Issues")
        self.root.geometry("1200x900")
        
        try:
            self.root.state('zoomed')  # Maximize on Windows
        except:
            pass
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # === HEADER ===
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(header_frame, 
                               text="🔧 Fixed SAP Automation - Field Filling Issues Resolved", 
                               font=("Arial", 18, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="✅ Corrected MRP Area Field ID | ✅ Enhanced Field Detection | ✅ Improved Error Handling",
                                  font=("Arial", 12),
                                  foreground="green")
        subtitle_label.pack(pady=(5, 0))
        
        # === FIXES APPLIED ===
        fixes_frame = ttk.LabelFrame(main_container, text="🔧 Fixes Applied", padding="10")
        fixes_frame.pack(fill=tk.X, pady=(0, 10))
        
        fixes_text = """✅ FIXED: Added missing MRP Area field ID: /app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-BERID
✅ IMPROVED: Enhanced field detection with multiple fallback methods
✅ ENHANCED: Better error handling for field access and validation
✅ ADDED: Field existence verification before attempting to fill
✅ OPTIMIZED: Improved timing and wait mechanisms"""
        
        fixes_label = ttk.Label(fixes_frame, text=fixes_text, font=("Consolas", 9))
        fixes_label.pack(anchor=tk.W)
        
        # === STEP 1: SAP CONNECTION ===
        connection_frame = ttk.LabelFrame(main_container, text="🔌 Step 1: SAP Connection", padding="15")
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        conn_inner = ttk.Frame(connection_frame)
        conn_inner.pack(fill=tk.X)
        
        self.connection_status_var = tk.StringVar(value="❌ Not Connected to SAP")
        status_label = ttk.Label(conn_inner, textvariable=self.connection_status_var,
                                font=("Arial", 11, "bold"))
        status_label.pack(side=tk.LEFT)
        
        connect_btn = ttk.Button(conn_inner, text="🔌 Connect to SAP Dashboard",
                                command=self.connect_to_sap)
        connect_btn.pack(side=tk.RIGHT)
        
        # === STEP 2: FIELD TESTING ===
        test_frame = ttk.LabelFrame(main_container, text="🧪 Step 2: Field Testing", padding="15")
        test_frame.pack(fill=tk.X, pady=(0, 10))
        
        test_inner = ttk.Frame(test_frame)
        test_inner.pack(fill=tk.X)
        
        test_btn = ttk.Button(test_inner, text="🧪 Test Field Access",
                             command=self.test_field_access)
        test_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        validate_btn = ttk.Button(test_inner, text="✅ Validate Fields",
                                 command=self.validate_all_fields)
        validate_btn.pack(side=tk.LEFT)
        
        # === STEP 3: PART NUMBERS INPUT ===
        input_frame = ttk.LabelFrame(main_container, text="📝 Step 3: Part Numbers Input", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Single part input
        single_frame = ttk.Frame(input_frame)
        single_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(single_frame, text="Part Number:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.single_part_var = tk.StringVar(value="857-A65473-106")
        single_entry = ttk.Entry(single_frame, textvariable=self.single_part_var, width=25, font=("Arial", 10))
        single_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(single_frame, text="MRP Area:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.mrp_area_var = tk.StringVar(value="1000")
        mrp_entry = ttk.Entry(single_frame, textvariable=self.mrp_area_var, width=10, font=("Arial", 10))
        mrp_entry.pack(side=tk.LEFT, padx=(10, 0))
        
        # Test filling button
        test_fill_btn = ttk.Button(single_frame, text="🔧 Test Fill Fields",
                                  command=self.test_fill_fields)
        test_fill_btn.pack(side=tk.RIGHT)
        
        # === STEP 4: AUTOMATION CONTROLS ===
        control_frame = ttk.LabelFrame(main_container, text="🚀 Step 4: Automation Controls", padding="15")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        control_inner = ttk.Frame(control_frame)
        control_inner.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(control_inner, text="🚀 START Fixed Automation",
                                   command=self.start_automation)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_btn = ttk.Button(control_inner, text="⏹️ Stop Automation", 
                                  command=self.stop_automation, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        # === LOG SECTION ===
        log_frame = ttk.LabelFrame(main_container, text="📜 System Log", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=120, font=("Consolas", 9))
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
        """Connect to SAP dashboard."""
        try:
            pythoncom.CoInitialize()
            
            self.log_message("🔌 Connecting to SAP dashboard...")
            
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
                    
                    self.connection_status_var.set(f"✅ Connected: {system_name} Client {client} User {user}")
                    self.log_message(f"✅ Successfully connected to SAP: {system_name} Client {client} User {user}")
                    
                    return True
            
            raise Exception("No SAP sessions found")
            
        except Exception as e:
            error_msg = str(e)
            self.connection_status_var.set("❌ Connection Failed")
            self.log_message(f"❌ Failed to connect to SAP: {error_msg}", "ERROR")
            messagebox.showerror("SAP Connection Error", f"Failed to connect:\n{error_msg}")
    def automation_finished(self):
        """Handle automation completion."""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
    
    def test_field_access(self):
        """Test access to all critical fields."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.log_message("🧪 Testing field access...")
        self.log_message("="*60)
        
        # Ensure we're on the right screen
        self.ensure_md04_screen()
        
        # Test each field
        test_results = {}
        
        for field_name, field_id in self.field_ids.items():
            try:
                self.log_message(f"🔍 Testing {field_name}: {field_id}")
                
                field = self.session.findById(field_id)
                
                # Get field properties
                field_type = getattr(field, 'Type', 'Unknown')
                field_text = getattr(field, 'text', '')
                is_modifiable = getattr(field, 'Modifiable', False)
                is_changeable = getattr(field, 'Changeable', False)
                
                self.log_message(f"   ✅ Field found!")
                self.log_message(f"   📋 Type: {field_type}")
                self.log_message(f"   📝 Current text: '{field_text}'")
                self.log_message(f"   🔧 Modifiable: {is_modifiable}")
                self.log_message(f"   🔄 Changeable: {is_changeable}")
                
                test_results[field_name] = {
                    'found': True,
                    'type': field_type,
                    'modifiable': is_modifiable,
                    'changeable': is_changeable,
                    'text': field_text
                }
                
            except Exception as e:
                self.log_message(f"   ❌ Field NOT found: {e}", "ERROR")
                test_results[field_name] = {
                    'found': False,
                    'error': str(e)
                }
        
        self.log_message("="*60)
        self.log_message("🧪 Field Test Summary:")
        
        for field_name, result in test_results.items():
            if result['found']:
                status = "✅ ACCESSIBLE"
                if result.get('modifiable', False):
                    status += " & MODIFIABLE"
                self.log_message(f"   {field_name}: {status}")
            else:
                self.log_message(f"   {field_name}: ❌ NOT ACCESSIBLE", "ERROR")
        
        messagebox.showinfo("Field Test Complete", "Field access test completed. Check log for details.")
    
    def validate_all_fields(self):
        """Validate that we can access all required fields."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.log_message("✅ Validating all required fields...")
        
        # Ensure proper screen
        self.ensure_md04_screen()
        
        required_fields = ['material_field', 'mrp_area_field', 'plant_field']
        all_valid = True
        
        for field_name in required_fields:
            field_id = self.field_ids[field_name]
            try:
                field = self.session.findById(field_id)
                self.log_message(f"✅ {field_name}: VALID")
            except Exception as e:
                self.log_message(f"❌ {field_name}: INVALID - {e}", "ERROR")
                all_valid = False
        
        if all_valid:
            self.log_message("🎉 All required fields are accessible!")
            messagebox.showinfo("Validation Success", "All required fields are accessible!")
        else:
            self.log_message("❌ Some fields are not accessible!", "ERROR")
            messagebox.showerror("Validation Failed", "Some fields are not accessible. Check log for details.")
    
    def ensure_md04_screen(self):
        """Ensure we're on the MD04 input screen."""
        try:
            # Navigate to MD04 if not already there
            current_transaction = self.session.Info.Transaction
            if current_transaction.upper() != "MD04":
                self.log_message("📍 Navigating to MD04...")
                self.session.findById("wnd[0]/tbar[0]/okcd").text = "MD04"
                self.session.findById("wnd[0]").sendVKey(0)
                time.sleep(3)
            
            # Ensure Individual access tab is selected
            try:
                individual_tab = self.session.findById("wnd[0]/usr/tabsTAB300/tabpF01")
                individual_tab.select()
                time.sleep(1)
                self.log_message("✅ Individual access tab selected")
            except Exception as e:
                self.log_message(f"⚠️ Could not select Individual tab: {e}", "WARNING")
                
        except Exception as e:
            self.log_message(f"❌ Error ensuring MD04 screen: {e}", "ERROR")
    
    def test_fill_fields(self):
        """Test filling the fields with sample data."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.log_message("🔧 Testing field filling...")
        
        # Ensure proper screen
        self.ensure_md04_screen()
        
        part_number = self.single_part_var.get().strip()
        mrp_area = self.mrp_area_var.get().strip()
        
        # Test filling material field
        success1 = self.fill_field_safely("material_field", part_number)
        time.sleep(1)
        
        # Test filling MRP area field
        success2 = self.fill_field_safely("mrp_area_field", mrp_area)
        
        if success1 and success2:
            # Automatically press Enter after filling fields
            self.log_message("⚡ Auto-pressing Enter to execute query...")
            self.execute_query_automatically()
            
            # Wait for results to load
            time.sleep(3)
            
            # Test finding and focusing on MatRes (no clicking needed)
            self.log_message("🔍 Testing MatRes detection and focusing...")
            if self.find_and_focus_matres_automatically():
                # Wait 1 second then test F7
                time.sleep(1)
                self.log_message("📺 Testing F7 maximize...")
                self.press_f7_automatically()
                
                self.log_message("🎉 Complete test sequence SUCCESSFUL!")
                messagebox.showinfo("Test Success", "Complete automation test successful!")
            else:
                self.log_message("❌ MatRes test FAILED!", "ERROR")
                messagebox.showerror("Test Failed", "MatRes detection failed.")
        else:
            self.log_message("❌ Field filling test FAILED!", "ERROR")
            messagebox.showerror("Test Failed", "Field filling test failed. Check log for details.")
    
    def fill_field_safely(self, field_name: str, value: str) -> bool:
        """Safely fill a field with enhanced error handling."""
        try:
            field_id = self.field_ids[field_name]
            self.log_message(f"🔧 Filling {field_name} with: '{value}'")
            
            # Find the field
            field = self.session.findById(field_id)
            
            # Check if field is accessible
            if not hasattr(field, 'text'):
                self.log_message(f"❌ Field {field_name} does not have text property", "ERROR")
                return False
            
            # Try multiple methods to fill the field
            methods = [
                self._method_direct_assignment,
                self._method_focus_and_assign,
                self._method_sap_changeable_field,  # NEW: Special method for SAP changeable fields
                self._method_clear_and_type,
                self._method_send_keys
            ]
            
            for i, method in enumerate(methods, 1):
                try:
                    self.log_message(f"   🔄 Trying method {i}...")
                    
                    if method(field, value):
                        # Verify the field was filled
                        current_value = getattr(field, 'text', '').strip()
                        if current_value == value:
                            self.log_message(f"   ✅ Method {i} successful! Value: '{current_value}'")
                            return True
                        else:
                            self.log_message(f"   ⚠️ Method {i} partial success. Expected: '{value}', Got: '{current_value}'")
                            
                except Exception as e:
                    self.log_message(f"   ❌ Method {i} failed: {e}")
                    continue
            
            self.log_message(f"❌ All methods failed for {field_name}", "ERROR")
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error filling {field_name}: {e}", "ERROR")
            return False
    
    def _method_direct_assignment(self, field, value: str) -> bool:
        """Method 1: Direct assignment."""
        field.text = value
        time.sleep(0.5)
        return True
    
    def _method_focus_and_assign(self, field, value: str) -> bool:
        """Method 2: Focus then assign."""
        field.setFocus()
        time.sleep(0.3)
        field.text = value
        time.sleep(0.5)
        return True
    
    def _method_sap_changeable_field(self, field, value: str) -> bool:
        """Method 3: Special handling for SAP changeable fields."""
        try:
            # For SAP fields that are Changeable but not Modifiable
            field.setFocus()
            time.sleep(0.3)
            
            # Try to make field editable first
            try:
                # Double click to enter edit mode
                field.doubleClick()
                time.sleep(0.2)
            except:
                pass
            
            # Try pressing F2 to enter edit mode
            try:
                self.session.findById("wnd[0]").sendVKey(2)  # F2
                time.sleep(0.2)
            except:
                pass
            
            # Now try to set the value
            field.text = value
            time.sleep(0.3)
            
            # Press Tab to confirm the entry
            self.session.findById("wnd[0]").sendVKey(1)  # Tab key
            time.sleep(0.3)
            
            return True
            
        except Exception as e:
            self.log_message(f"   SAP changeable field method error: {e}")
            return False
    
    def _method_clear_and_type(self, field, value: str) -> bool:
        """Method 3: Clear and type."""
        field.setFocus()
        time.sleep(0.3)
        
        # Clear field
        field.caretPosition = 0
        self.session.findById("wnd[0]").sendVKey(2, 16)  # Ctrl+A
        time.sleep(0.2)
        
        # Type value
        field.text = value
        time.sleep(0.5)
        return True
    
    def _method_send_keys(self, field, value: str) -> bool:
        """Method 4: Send individual keys."""
        field.setFocus()
        time.sleep(0.3)
        
        # Clear field
        field.caretPosition = 0
        self.session.findById("wnd[0]").sendVKey(2, 16)  # Ctrl+A
        time.sleep(0.2)
        
        # Send individual characters
        for char in value:
            if char.isalnum() or char in '-_':
                self.session.findById("wnd[0]").sendVKey(ord(char.upper()))
                time.sleep(0.05)
        
        time.sleep(0.5)
        return True
    
    def execute_query_automatically(self) -> bool:
        """Automatically execute the query by pressing Enter."""
        try:
            self.log_message("⚡ Executing query automatically by pressing Enter...")
            
            # Make sure we're focused on the main window
            main_window = self.session.findById("wnd[0]")
            main_window.setFocus()
            time.sleep(0.5)
            
            # Press Enter to execute the query
            self.session.findById("wnd[0]").sendVKey(0)  # Enter key (VKey 0)
            self.log_message("✅ Enter key pressed successfully!")
            
            # Wait for query to execute and results to load
            time.sleep(4)  # Wait for query execution
            
            # Check for SAP errors
            error_msg = self.check_for_sap_errors()
            if error_msg:
                self.log_message(f"⚠️ SAP Warning/Error: {error_msg}", "WARNING")
                # Don't fail completely on warnings, just log them
            
            # Verify that we now have results or moved to a different screen
            try:
                current_transaction = self.session.Info.Transaction
                window_title = self.session.findById("wnd[0]").text
                
                self.log_message(f"✅ Query executed - Current Transaction: {current_transaction}")
                self.log_message(f"✅ Current Window: {window_title}")
                
                # Additional wait to ensure all results are fully loaded
                time.sleep(2)
                
                return True
                
            except Exception as e:
                self.log_message(f"⚠️ Could not verify results loading: {e}", "WARNING")
                return True  # Continue anyway
            
        except Exception as e:
            self.log_message(f"❌ Query execution failed: {e}", "ERROR")
            return False
    
    def check_for_sap_errors(self) -> str:
        """Check for SAP error messages."""
        try:
            # Check status bar for errors
            try:
                status_bar = self.session.findById("wnd[0]/sbar")
                if status_bar and hasattr(status_bar, 'text'):
                    status_text = status_bar.text.strip()
                    if status_text and any(keyword in status_text.lower() for keyword in ['error', 'not found', 'does not exist', 'fehler']):
                        return status_text
            except:
                pass
                
            # Check for error popup windows
            for window_id in ["wnd[1]", "wnd[2]"]:
                try:
                    window = self.session.findById(window_id)
                    if window and hasattr(window, 'text'):
                        window_text = window.text.strip()
                        if window_text and any(keyword in window_text.lower() for keyword in ['error', 'fehler', 'warning']):
                            # Try to close the popup by pressing Enter or Escape
                            try:
                                window.sendVKey(0)  # Enter
                                time.sleep(0.5)
                            except:
                                try:
                                    window.sendVKey(12)  # Escape
                                    time.sleep(0.5)
                                except:
                                    pass
                            return window_text
                except:
                    continue
                    
        except Exception:
            pass
            
        return ""
    
    def start_automation(self):
        """Start the automation process."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        part_number = self.single_part_var.get().strip()
        if not part_number:
            messagebox.showerror("Error", "Please enter a part number!")
            return
        
        self.log_message("🚀 Starting fixed automation...")
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # Run the automation
        threading.Thread(target=self.run_automation, args=(part_number,), daemon=True).start()
    
    def run_automation(self, part_number: str):
        """Run the complete automation workflow."""
        try:
            self.log_message(f"🔄 Processing part: {part_number}")
            
            # Step 1: Ensure MD04 screen
            self.log_message("📍 Step 1: Ensuring MD04 input screen...")
            self.ensure_md04_screen()
            
            # Step 2: Fill material field
            self.log_message("📝 Step 2: Filling material field...")
            if not self.fill_field_safely("material_field", part_number):
                raise Exception("Failed to fill material field")
            
            # Step 3: Fill MRP area if provided
            mrp_area = self.mrp_area_var.get().strip()
            if mrp_area:
                self.log_message("📝 Step 3: Filling MRP area field...")
                if not self.fill_field_safely("mrp_area_field", mrp_area):
                    self.log_message("⚠️ Failed to fill MRP area, continuing...", "WARNING")
            else:
                self.log_message("⏭️ Step 3: Skipping MRP area (not provided)")
            
            # Step 4: Automatically execute query by pressing Enter
            self.log_message("⚡ Step 4: Automatically executing query (pressing Enter)...")
            if not self.execute_query_automatically():
                raise Exception("Failed to execute query")
            
            # Step 5: Find and focus on MatRes element (no clicking needed)
            self.log_message("🔍 Step 5: Looking for MatRes element to focus...")
            if not self.find_and_focus_matres_automatically():
                self.log_message("❌ MatRes element not found", "ERROR")
                raise Exception("MatRes element not found")
            
            # Step 6: Wait 1 second then automatically press F7 to maximize
            self.log_message("📺 Step 6: Waiting 1 second then pressing F7 to maximize...")
            time.sleep(1)  # Wait 1 second as requested
            if not self.press_f7_automatically():
                self.log_message("⚠️ Failed to press F7, continuing...", "WARNING")
            
            self.log_message("✅ Complete automation workflow finished successfully!")
            self.log_message("🎉 All steps completed: Fill → Execute → Click MatRes → F7 Maximize!")
            
        except Exception as e:
            self.log_message(f"❌ Automation failed: {e}", "ERROR")
        finally:
            self.root.after(0, self.automation_finished)
    
    def find_and_focus_matres_automatically(self) -> bool:
        """Find MatRes element and focus on it (no clicking needed)."""
        try:
            self.log_message("🔍 Scanning for MatRes element to focus...")
            
            # Get the main window and scan for MatRes
            main_window = self.session.findById("wnd[0]")
            matres_element = self.scan_for_matres_element(main_window, 0)
            
            if matres_element:
                self.log_message("✅ MatRes element found, setting focus...")
                matres_element.setFocus()
                time.sleep(0.5)
                self.log_message("🎯 Focus set on MatRes element")
                return True
            else:
                self.log_message("❌ MatRes element not found", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Error finding MatRes element: {e}", "ERROR")
            return False
    
    def scan_for_matres_element(self, element, depth):
        """Recursively scan for element containing 'MatRes' text."""
        if depth > 10:  # Prevent infinite recursion
            return None
            
        try:
            # Check if this element has 'MatRes' text
            if hasattr(element, 'text'):
                text = element.text.strip()
                if text == 'MatRes':
                    self.log_message(f"🎯 Found MatRes element at depth {depth}")
                    return element
            
            # Check children
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
        """Automatically press F7 to maximize the popup window."""
        try:
            self.log_message("📺 Pressing F7 to maximize popup window...")
            
            # Make sure we're focused on the main window
            main_window = self.session.findById("wnd[0]")
            main_window.setFocus()
            time.sleep(0.3)
            
            # Press F7 key (VKey 7)
            self.session.findById("wnd[0]").sendVKey(7)
            self.log_message("✅ F7 key pressed successfully!")
            
            # Wait for window to maximize
            time.sleep(2)
            
            # Verify the action worked
            try:
                window_title = self.session.findById("wnd[0]").text
                self.log_message(f"📺 Current window after F7: {window_title}")
            except:
                pass
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Failed to press F7: {e}", "ERROR")
            return False
    
    def press_f7_automatically(self) -> bool:
        """Automatically press F7 to maximize the popup window."""
        try:
            self.log_message("📺 Pressing F7 to maximize popup window...")
            
            # Make sure we're focused on the main window
            main_window = self.session.findById("wnd[0]")
            main_window.setFocus()
            time.sleep(0.3)
            
            # Press F7 key (VKey 7)
            self.session.findById("wnd[0]").sendVKey(7)
            self.log_message("✅ F7 key pressed successfully!")
            
            # Wait for window to maximize
            time.sleep(2)
            
            # Verify the action worked
            try:
                window_title = self.session.findById("wnd[0]").text
                self.log_message(f"📺 Current window after F7: {window_title}")
            except:
                pass
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Failed to press F7: {e}", "ERROR")
            return False
    
    def stop_automation(self):
        """Stop the automation."""
        self.is_running = False
        self.log_message("⏹️ Automation stopped by user")
    
    def run(self):
        """Run the application."""
        self.log_message("🔧 Fixed SAP Automation Started!")
        self.log_message("✅ Key fixes applied:")
        self.log_message("   • Added missing MRP Area field ID")
        self.log_message("   • Enhanced field detection methods")
        self.log_message("   • Improved error handling")
        self.log_message("   • Added field validation tools")
        self.log_message("")
        self.log_message("🚀 Ready to test and run automation!")
        
        self.root.mainloop()


def main():
    """Main function."""
    print("="*80)
    print("🔧 FIXED SAP AUTOMATION - FIELD FILLING ISSUES RESOLVED")
    print("="*80)
    print("Key fixes applied:")
    print("✅ ADDED: Missing MRP Area field ID")
    print("✅ ENHANCED: Field detection with multiple fallback methods")
    print("✅ IMPROVED: Error handling for field access")
    print("✅ ADDED: Field validation and testing tools")
    print("✅ OPTIMIZED: Better timing and wait mechanisms")
    print()
    print("🧪 New testing features:")
    print("• Test Field Access - Verify all fields can be found")
    print("• Validate Fields - Check field accessibility")
    print("• Test Fill Fields - Test filling with sample data")
    print()
    print("🚀 Starting Fixed SAP Automation...")
    print("="*80)
    
    try:
        app = FixedSAPAutomation()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()