#!/usr/bin/env python3
"""
SAP ZERF Transaction Date Automation
=====================================
Automates date field updates in SAP ZERF transaction:
- Updates Start Date to 08/03/2025
- Updates End Date to current date
- Handles SAP date field formatting (MM/DD/YYYY)

Author: SAP Automation Script for ZERF
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import win32com.client
import pythoncom
import time
import logging
import os
from datetime import datetime
import threading

class ZERFDateAutomation:
    """
    SAP ZERF Transaction automation for updating date fields
    """
    
    def __init__(self):
        # SAP Field IDs for ZERF transaction
        self.field_ids = {
            "start_date_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctextSP$00018-LOW",
            "end_date_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctextSP$00018-HIGH"
        }
        
        # Date values
        self.start_date = "08/03/2025"  # August 3rd, 2025 in MM/DD/YYYY format
        self.end_date = datetime.now().strftime("%m/%d/%Y")  # Current date in MM/DD/YYYY
        
        # SAP Connection
        self.session = None
        self.is_running = False
        
        # Setup
        self.setup_logging()
        self.setup_gui()
        
    def setup_logging(self):
        """Setup logging system."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/zerf_automation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
    def setup_gui(self):
        """Setup the main GUI interface."""
        self.root = tk.Tk()
        self.root.title("📅 SAP ZERF Date Automation")
        self.root.geometry("1100x800")
        
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
                               text="📅 SAP ZERF Transaction - Date Field Automation", 
                               font=("Arial", 18, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Automatically updates Start Date and End Date fields in ZERF transaction",
                                  font=("Arial", 11),
                                  foreground="gray")
        subtitle_label.pack(pady=(5, 0))
        
        # === CONNECTION SECTION ===
        connection_frame = ttk.LabelFrame(main_container, text="🔌 SAP Connection", padding="15")
        connection_frame.pack(fill=tk.X, pady=(0, 10))
        
        conn_inner = ttk.Frame(connection_frame)
        conn_inner.pack(fill=tk.X)
        
        self.connection_status_var = tk.StringVar(value="❌ Not Connected to SAP")
        status_label = ttk.Label(conn_inner, textvariable=self.connection_status_var,
                                font=("Arial", 11, "bold"))
        status_label.pack(side=tk.LEFT)
        
        connect_btn = ttk.Button(conn_inner, text="🔌 Connect to SAP",
                                command=self.connect_to_sap)
        connect_btn.pack(side=tk.RIGHT)
        
        # === DATE CONFIGURATION ===
        date_frame = ttk.LabelFrame(main_container, text="📅 Date Configuration", padding="15")
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start Date
        start_date_frame = ttk.Frame(date_frame)
        start_date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(start_date_frame, text="Start Date:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.start_date_var = tk.StringVar(value=self.start_date)
        start_entry = ttk.Entry(start_date_frame, textvariable=self.start_date_var, width=15, font=("Arial", 10))
        start_entry.pack(side=tk.LEFT, padx=(10, 20))
        ttk.Label(start_date_frame, text="(Format: MM/DD/YYYY)", font=("Arial", 9), foreground="gray").pack(side=tk.LEFT)
        
        # End Date
        end_date_frame = ttk.Frame(date_frame)
        end_date_frame.pack(fill=tk.X)
        
        ttk.Label(end_date_frame, text="End Date:  ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.end_date_var = tk.StringVar(value=self.end_date)
        end_entry = ttk.Entry(end_date_frame, textvariable=self.end_date_var, width=15, font=("Arial", 10))
        end_entry.pack(side=tk.LEFT, padx=(10, 20))
        
        # Update to current date button
        update_date_btn = ttk.Button(end_date_frame, text="📅 Update to Today",
                                    command=self.update_end_date_to_today)
        update_date_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(end_date_frame, text="(Current date)", font=("Arial", 9), foreground="gray").pack(side=tk.LEFT)
        
        # === FIELD INFORMATION ===
        field_info_frame = ttk.LabelFrame(main_container, text="🔧 Field Information", padding="10")
        field_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = f"""Start Date Field ID: {self.field_ids['start_date_field']}
End Date Field ID:   {self.field_ids['end_date_field']}
Transaction Code:    ZERF
Date Format:        MM/DD/YYYY"""
        
        info_label = ttk.Label(field_info_frame, text=info_text, font=("Consolas", 9))
        info_label.pack(anchor=tk.W)
        
        # === AUTOMATION CONTROLS ===
        control_frame = ttk.LabelFrame(main_container, text="🚀 Automation Controls", padding="15")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        # Test buttons
        test_nav_btn = ttk.Button(button_frame, text="📍 Navigate to ZERF",
                                 command=self.navigate_to_zerf)
        test_nav_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_fields_btn = ttk.Button(button_frame, text="🧪 Test Field Access",
                                    command=self.test_field_access)
        test_fields_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        test_fill_btn = ttk.Button(button_frame, text="📝 Test Fill Dates",
                                  command=self.test_fill_dates)
        test_fill_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        # Main automation buttons
        self.start_btn = ttk.Button(button_frame, text="🚀 Run Full Automation",
                                   command=self.start_automation)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.execute_btn = ttk.Button(button_frame, text="⚡ Execute Query (F8)",
                                     command=self.execute_query)
        self.execute_btn.pack(side=tk.LEFT)
        
        # === LOG SECTION ===
        log_frame = ttk.LabelFrame(main_container, text="📜 System Log", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Clear log button
        clear_btn = ttk.Button(log_frame, text="🗑️ Clear Log", command=self.clear_log)
        clear_btn.pack(anchor=tk.E, pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=120, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to GUI log and logger."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        safe_message = str(message).encode('ascii', 'replace').decode('ascii')
        log_entry = f"[{timestamp}] {level}: {safe_message}\n"
        
        # Add to GUI with color coding
        self.log_text.insert(tk.END, log_entry)
        
        # Color coding for different levels
        if level == "ERROR":
            self.log_text.tag_add("error", f"end-{len(log_entry)+1}c", "end-1c")
            self.log_text.tag_config("error", foreground="red")
        elif level == "WARNING":
            self.log_text.tag_add("warning", f"end-{len(log_entry)+1}c", "end-1c")
            self.log_text.tag_config("warning", foreground="orange")
        elif level == "SUCCESS":
            self.log_text.tag_add("success", f"end-{len(log_entry)+1}c", "end-1c")
            self.log_text.tag_config("success", foreground="green")
            
        self.log_text.see(tk.END)
        
        # Add to file logger
        if hasattr(self, 'logger'):
            if level == "INFO" or level == "SUCCESS":
                self.logger.info(safe_message)
            elif level == "ERROR":
                self.logger.error(safe_message)
            elif level == "WARNING":
                self.logger.warning(safe_message)
        
        # Update GUI
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log text widget."""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Log cleared")
        
    def update_end_date_to_today(self):
        """Update end date to current date."""
        self.end_date = datetime.now().strftime("%m/%d/%Y")
        self.end_date_var.set(self.end_date)
        self.log_message(f"End date updated to: {self.end_date}")
        
    def connect_to_sap(self) -> bool:
        """Connect to SAP GUI."""
        try:
            pythoncom.CoInitialize()
            
            self.log_message("🔌 Connecting to SAP GUI...")
            
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
                    self.log_message(f"✅ Successfully connected to SAP: {system_name} Client {client} User {user}", "SUCCESS")
                    
                    # Log current transaction
                    try:
                        current_transaction = self.session.Info.Transaction
                        self.log_message(f"📍 Current transaction: {current_transaction}")
                    except:
                        pass
                    
                    return True
            
            raise Exception("No SAP sessions found")
            
        except Exception as e:
            error_msg = str(e)
            self.connection_status_var.set("❌ Connection Failed")
            self.log_message(f"❌ Failed to connect to SAP: {error_msg}", "ERROR")
            messagebox.showerror("SAP Connection Error", f"Failed to connect:\n{error_msg}")
            return False
    
    def navigate_to_zerf(self):
        """Navigate to ZERF transaction."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return False
            
        try:
            self.log_message("📍 Navigating to ZERF transaction...")
            
            # Enter transaction code
            self.session.findById("wnd[0]/tbar[0]/okcd").text = "ZERF"
            time.sleep(0.5)
            
            # Press Enter to navigate
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(2)
            
            # Verify we're in ZERF
            try:
                current_transaction = self.session.Info.Transaction
                if current_transaction.upper() == "ZERF":
                    self.log_message(f"✅ Successfully navigated to ZERF", "SUCCESS")
                    return True
                else:
                    self.log_message(f"⚠️ Current transaction: {current_transaction}", "WARNING")
            except:
                self.log_message("✅ Navigation completed (unable to verify transaction)", "SUCCESS")
                
            return True
            
        except Exception as e:
            self.log_message(f"❌ Failed to navigate to ZERF: {e}", "ERROR")
            return False
    
    def test_field_access(self):
        """Test access to date fields."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.log_message("🧪 Testing field access...")
        self.log_message("="*60)
        
        for field_name, field_id in self.field_ids.items():
            try:
                self.log_message(f"🔍 Testing {field_name}: {field_id}")
                
                field = self.session.findById(field_id)
                
                # Get field properties
                field_type = getattr(field, 'Type', 'Unknown')
                field_text = getattr(field, 'text', '')
                is_modifiable = getattr(field, 'Modifiable', False)
                is_changeable = getattr(field, 'Changeable', False)
                
                self.log_message(f"   ✅ Field found!", "SUCCESS")
                self.log_message(f"   📋 Type: {field_type}")
                self.log_message(f"   📝 Current value: '{field_text}'")
                self.log_message(f"   🔧 Modifiable: {is_modifiable}")
                self.log_message(f"   🔄 Changeable: {is_changeable}")
                
            except Exception as e:
                self.log_message(f"   ❌ Field NOT found: {e}", "ERROR")
        
        self.log_message("="*60)
        messagebox.showinfo("Test Complete", "Field access test completed. Check log for details.")
    
    def fill_date_field(self, field_name: str, date_value: str) -> bool:
        """Fill a date field with the specified value."""
        try:
            field_id = self.field_ids[field_name]
            self.log_message(f"📝 Filling {field_name} with: '{date_value}'")
            
            # Find the field
            field = self.session.findById(field_id)
            
            # Try different methods to fill the field
            methods = [
                lambda: self._fill_method_direct(field, date_value),
                lambda: self._fill_method_focus_clear_type(field, date_value),
                lambda: self._fill_method_select_all_replace(field, date_value)
            ]
            
            for i, method in enumerate(methods, 1):
                try:
                    self.log_message(f"   🔄 Trying method {i}...")
                    
                    if method():
                        # Verify the field was filled
                        time.sleep(0.5)
                        current_value = getattr(field, 'text', '').strip()
                        
                        # Check if date was set (might have different formatting)
                        if date_value.replace("/", "") in current_value.replace("/", "").replace(".", "").replace("-", ""):
                            self.log_message(f"   ✅ Successfully set to: '{current_value}'", "SUCCESS")
                            return True
                        elif current_value:
                            self.log_message(f"   ⚠️ Field updated to: '{current_value}'", "WARNING")
                            return True
                            
                except Exception as e:
                    self.log_message(f"   ❌ Method {i} failed: {e}")
                    continue
            
            self.log_message(f"❌ All methods failed for {field_name}", "ERROR")
            return False
            
        except Exception as e:
            self.log_message(f"❌ Error filling {field_name}: {e}", "ERROR")
            return False
    
    def _fill_method_direct(self, field, value: str) -> bool:
        """Direct assignment method."""
        field.text = value
        time.sleep(0.3)
        return True
    
    def _fill_method_focus_clear_type(self, field, value: str) -> bool:
        """Focus, clear, and type method."""
        field.setFocus()
        time.sleep(0.2)
        
        # Clear field
        field.text = ""
        time.sleep(0.2)
        
        # Type new value
        field.text = value
        time.sleep(0.3)
        
        # Press Tab to confirm
        try:
            self.session.findById("wnd[0]").sendVKey(1)  # Tab key
            time.sleep(0.2)
        except:
            pass
            
        return True
    
    def _fill_method_select_all_replace(self, field, value: str) -> bool:
        """Select all and replace method."""
        field.setFocus()
        time.sleep(0.2)
        
        # Select all (Ctrl+A)
        try:
            field.caretPosition = 0
            self.session.findById("wnd[0]").sendVKey(1, 1)  # Ctrl+A
            time.sleep(0.2)
        except:
            pass
        
        # Type new value
        field.text = value
        time.sleep(0.3)
        return True
    
    def test_fill_dates(self):
        """Test filling both date fields."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.log_message("📝 Testing date field filling...")
        
        # Get current date values
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        
        # Validate date format
        if not self.validate_date_format(start_date) or not self.validate_date_format(end_date):
            messagebox.showerror("Invalid Date", "Please use MM/DD/YYYY format for dates!")
            return
        
        # Fill start date
        success1 = self.fill_date_field("start_date_field", start_date)
        time.sleep(1)
        
        # Fill end date
        success2 = self.fill_date_field("end_date_field", end_date)
        
        if success1 and success2:
            self.log_message("✅ Date fields filled successfully!", "SUCCESS")
            messagebox.showinfo("Success", "Date fields filled successfully!")
        else:
            self.log_message("⚠️ Some date fields may not have been filled correctly", "WARNING")
            messagebox.showwarning("Warning", "Some date fields may not have been filled correctly. Check log for details.")
    
    def validate_date_format(self, date_str: str) -> bool:
        """Validate date format MM/DD/YYYY."""
        try:
            parts = date_str.split("/")
            if len(parts) != 3:
                return False
                
            month, day, year = parts
            
            if len(month) != 2 or len(day) != 2 or len(year) != 4:
                return False
                
            # Validate ranges
            if not (1 <= int(month) <= 12):
                return False
            if not (1 <= int(day) <= 31):
                return False
            if not (1900 <= int(year) <= 2100):
                return False
                
            return True
            
        except:
            return False
    
    def execute_query(self):
        """Execute the query by pressing F8."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        try:
            self.log_message("⚡ Executing query (pressing F8)...")
            
            # Press F8 (Execute)
            self.session.findById("wnd[0]").sendVKey(8)
            self.log_message("✅ F8 pressed - Query executed!", "SUCCESS")
            
            # Wait for execution
            time.sleep(3)
            
            # Check for any SAP messages
            self.check_for_sap_messages()
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Failed to execute query: {e}", "ERROR")
            return False
    
    def check_for_sap_messages(self):
        """Check for SAP status messages."""
        try:
            # Check status bar
            try:
                status_bar = self.session.findById("wnd[0]/sbar")
                if status_bar and hasattr(status_bar, 'text'):
                    status_text = status_bar.text.strip()
                    if status_text:
                        if any(keyword in status_text.lower() for keyword in ['error', 'fehler']):
                            self.log_message(f"❌ SAP Error: {status_text}", "ERROR")
                        elif any(keyword in status_text.lower() for keyword in ['warning', 'warnung']):
                            self.log_message(f"⚠️ SAP Warning: {status_text}", "WARNING")
                        else:
                            self.log_message(f"ℹ️ SAP Message: {status_text}")
            except:
                pass
                
        except:
            pass
    
    def start_automation(self):
        """Start the full automation process."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        # Validate dates
        start_date = self.start_date_var.get().strip()
        end_date = self.end_date_var.get().strip()
        
        if not self.validate_date_format(start_date) or not self.validate_date_format(end_date):
            messagebox.showerror("Invalid Date", "Please use MM/DD/YYYY format for dates!")
            return
        
        self.log_message("🚀 Starting full automation...", "SUCCESS")
        self.is_running = True
        self.start_btn.config(state="disabled")
        
        # Run automation in separate thread
        threading.Thread(target=self.run_full_automation, daemon=True).start()
    
    def run_full_automation(self):
        """Run the complete automation workflow."""
        try:
            self.log_message("="*60)
            self.log_message("🔄 STARTING ZERF DATE AUTOMATION WORKFLOW")
            self.log_message("="*60)
            
            # Step 1: Navigate to ZERF
            self.log_message("📍 Step 1: Navigating to ZERF transaction...")
            if not self.navigate_to_zerf():
                raise Exception("Failed to navigate to ZERF")
            time.sleep(2)
            
            # Step 2: Fill Start Date
            start_date = self.start_date_var.get().strip()
            self.log_message(f"📝 Step 2: Setting Start Date to {start_date}...")
            if not self.fill_date_field("start_date_field", start_date):
                self.log_message("⚠️ Start date may not have been set correctly", "WARNING")
            time.sleep(1)
            
            # Step 3: Fill End Date
            end_date = self.end_date_var.get().strip()
            self.log_message(f"📝 Step 3: Setting End Date to {end_date}...")
            if not self.fill_date_field("end_date_field", end_date):
                self.log_message("⚠️ End date may not have been set correctly", "WARNING")
            time.sleep(1)
            
            # Step 4: Execute Query
            self.log_message("⚡ Step 4: Executing query (F8)...")
            if not self.execute_query():
                self.log_message("⚠️ Query execution may have encountered issues", "WARNING")
            
            self.log_message("="*60)
            self.log_message("✅ AUTOMATION WORKFLOW COMPLETED!", "SUCCESS")
            self.log_message(f"Start Date: {start_date}")
            self.log_message(f"End Date: {end_date}")
            self.log_message("="*60)
            
            messagebox.showinfo("Automation Complete", 
                              f"ZERF automation completed!\n\nStart Date: {start_date}\nEnd Date: {end_date}")
            
        except Exception as e:
            self.log_message(f"❌ Automation failed: {e}", "ERROR")
            messagebox.showerror("Automation Failed", f"Automation failed:\n{e}")
        finally:
            self.root.after(0, self.automation_finished)
    
    def automation_finished(self):
        """Reset UI after automation completes."""
        self.is_running = False
        self.start_btn.config(state="normal")
        self.log_message("🏁 Automation process finished")
    
    def run(self):
        """Run the application."""
        self.log_message("📅 SAP ZERF Date Automation Started!")
        self.log_message(f"Default Start Date: {self.start_date}")
        self.log_message(f"Default End Date: {self.end_date}")
        self.log_message("")
        self.log_message("Instructions:")
        self.log_message("1. Click 'Connect to SAP' to establish connection")
        self.log_message("2. Optionally test navigation and field access")
        self.log_message("3. Adjust dates if needed")
        self.log_message("4. Click 'Run Full Automation' to execute")
        self.log_message("")
        self.log_message("Ready to begin...")
        
        self.root.mainloop()


def main():
    """Main function."""
    print("="*80)
    print("📅 SAP ZERF TRANSACTION - DATE FIELD AUTOMATION")
    print("="*80)
    print("This script automates date field updates in SAP ZERF transaction:")
    print("• Start Date: 08/03/2025")
    print("• End Date: Current date")
    print("• Transaction Code: ZERF")
    print()
    print("Features:")
    print("✅ Automatic navigation to ZERF")
    print("✅ Date field detection and filling")
    print("✅ Query execution with F8")
    print("✅ Comprehensive error handling")
    print("✅ Step-by-step testing capabilities")
    print()
    print("🚀 Starting GUI application...")
    print("="*80)
    
    try:
        app = ZERFDateAutomation()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()