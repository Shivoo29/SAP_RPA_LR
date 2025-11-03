#!/usr/bin/env python3
"""
Simple SAP Element Scanner
Records SAP field IDs by scanning the current screen
Works with any transaction code - no cursor tracking needed
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import win32com.client
import pythoncom
import time
import json
import logging
import os
from datetime import datetime
from typing import List, Dict

class SimpleSAPScanner:
    """
    Simple SAP element scanner that finds all fields on current screen
    """
    
    def __init__(self):
        self.session = None
        self.found_elements = []
        
        self.setup_logging()
        self.setup_gui()
        
    def setup_logging(self):
        """Setup logging system."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/sap_scanner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
    def setup_gui(self):
        """Setup simple GUI interface."""
        self.root = tk.Tk()
        self.root.title("SAP Element Scanner")
        self.root.geometry("1000x700")
        
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="SAP Element Scanner", 
                              font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Connection frame
        conn_frame = tk.LabelFrame(main_frame, text="SAP Connection", font=("Arial", 10, "bold"))
        conn_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        conn_inner = tk.Frame(conn_frame)
        conn_inner.pack(fill=tk.X, padx=10, pady=10)
        
        self.status_var = tk.StringVar(value="Not Connected")
        status_label = tk.Label(conn_inner, textvariable=self.status_var, font=("Arial", 10))
        status_label.pack(side=tk.LEFT)
        
        connect_btn = tk.Button(conn_inner, text="Connect to SAP", 
                               command=self.connect_to_sap, font=("Arial", 9))
        connect_btn.pack(side=tk.RIGHT)
        
        # Controls frame
        control_frame = tk.LabelFrame(main_frame, text="Scanner Controls", font=("Arial", 10, "bold"))
        control_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        control_inner = tk.Frame(control_frame)
        control_inner.pack(fill=tk.X, padx=10, pady=10)
        
        scan_btn = tk.Button(control_inner, text="Scan Current Screen", 
                            command=self.scan_current_screen, font=("Arial", 9))
        scan_btn.pack(side=tk.LEFT)
        
        clear_btn = tk.Button(control_inner, text="Clear Results", 
                             command=self.clear_results, font=("Arial", 9))
        clear_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Transaction input
        tk.Label(control_inner, text="Current Transaction:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(20, 5))
        self.tcode_var = tk.StringVar()
        tcode_entry = tk.Entry(control_inner, textvariable=self.tcode_var, width=10, font=("Arial", 9))
        tcode_entry.pack(side=tk.LEFT)
        
        nav_btn = tk.Button(control_inner, text="Navigate", 
                           command=self.navigate_to_transaction, font=("Arial", 9))
        nav_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Results count
        self.count_var = tk.StringVar(value="Elements found: 0")
        count_label = tk.Label(control_inner, textvariable=self.count_var, font=("Arial", 9))
        count_label.pack(side=tk.RIGHT)
        
        # Results frame
        results_frame = tk.LabelFrame(main_frame, text="Found Elements", font=("Arial", 10, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        # Results listbox with scrollbar
        list_frame = tk.Frame(results_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.results_listbox = tk.Listbox(list_frame, font=("Consolas", 8))
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Export buttons
        export_frame = tk.Frame(results_frame)
        export_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        export_json_btn = tk.Button(export_frame, text="Export JSON", 
                                   command=self.export_json, font=("Arial", 9))
        export_json_btn.pack(side=tk.LEFT)
        
        copy_ids_btn = tk.Button(export_frame, text="Copy Field IDs", 
                                command=self.copy_field_ids, font=("Arial", 9))
        copy_ids_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Log frame
        log_frame = tk.LabelFrame(main_frame, text="Log", font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.X, padx=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=("Consolas", 8))
        self.log_text.pack(fill=tk.X, padx=10, pady=10)
        
    def log_message(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.logger.info(message)
        self.root.update_idletasks()
        
    def connect_to_sap(self):
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
                    
                    self.status_var.set(f"Connected: {system_name} Client {client} User {user}")
                    self.log_message(f"Connected to SAP: {system_name} Client {client} User {user}")
                    
                    # Get current transaction
                    current_tcode = info.Transaction
                    self.tcode_var.set(current_tcode)
                    
                    return True
            
            raise Exception("No SAP sessions found")
            
        except Exception as e:
            self.status_var.set("Connection Failed")
            self.log_message(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect to SAP:\n{e}")
            return False
    
    def navigate_to_transaction(self):
        """Navigate to specified transaction."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        tcode = self.tcode_var.get().strip().upper()
        if not tcode:
            messagebox.showerror("Error", "Please enter a transaction code!")
            return
            
        try:
            self.log_message(f"Navigating to {tcode}...")
            
            self.session.findById("wnd[0]/tbar[0]/okcd").text = tcode
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(2)
            
            current_tcode = self.session.Info.Transaction
            if current_tcode.upper() == tcode:
                self.log_message(f"Successfully navigated to {tcode}")
            else:
                self.log_message(f"Navigation may have failed. Current: {current_tcode}")
                
        except Exception as e:
            self.log_message(f"Navigation error: {e}")
            messagebox.showerror("Navigation Error", f"Failed to navigate to {tcode}:\n{e}")
    
    def scan_current_screen(self):
        """Scan current SAP screen for all elements."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.log_message("Starting screen scan...")
        self.found_elements.clear()
        self.results_listbox.delete(0, tk.END)
        
        try:
            # Get current window
            main_window = self.session.findById("wnd[0]")
            current_tcode = self.session.Info.Transaction
            
            self.log_message(f"Scanning transaction: {current_tcode}")
            
            # Scan all elements recursively
            self.scan_element(main_window, "wnd[0]", 0)
            
            # Update display
            self.update_results_display()
            self.count_var.set(f"Elements found: {len(self.found_elements)}")
            
            self.log_message(f"Scan complete. Found {len(self.found_elements)} elements")
            
        except Exception as e:
            self.log_message(f"Scan error: {e}")
            messagebox.showerror("Scan Error", f"Failed to scan screen:\n{e}")
    
    def scan_element(self, element, path, depth):
        """Recursively scan SAP element and its children."""
        if depth > 10:  # Prevent infinite recursion
            return
            
        try:
            # Get element properties
            element_type = getattr(element, 'Type', 'Unknown')
            element_id = getattr(element, 'Id', '')
            element_text = getattr(element, 'Text', '')
            
            # Only record elements that have IDs and are useful
            if element_id and self.is_useful_element(element_type, element_text):
                element_info = {
                    'name': self.generate_element_name(element_text, element_type, len(self.found_elements)),
                    'type': element_type,
                    'id': element_id,
                    'text': element_text,
                    'path': path
                }
                
                self.found_elements.append(element_info)
            
            # Scan children
            try:
                children_count = element.Children.Count
                for i in range(children_count):
                    try:
                        child = element.Children(i)
                        child_path = f"{path}/child[{i}]"
                        self.scan_element(child, child_path, depth + 1)
                    except:
                        continue
            except:
                pass
                
        except:
            pass
    
    def is_useful_element(self, element_type, element_text):
        """Check if element is useful for automation."""
        useful_types = [
            'GuiTextField', 'GuiCTextField', 'GuiPasswordField',
            'GuiButton', 'GuiCheckBox', 'GuiRadioButton',
            'GuiComboBox', 'GuiComboBoxEntry'
        ]
        
        # Include if it's a useful type
        if element_type in useful_types:
            return True
            
        # Include if it has meaningful text
        if element_text and len(element_text.strip()) > 0:
            return True
            
        return False
    
    def generate_element_name(self, text, element_type, index):
        """Generate friendly name for element."""
        if text and text.strip():
            # Clean up text for use as name
            name = text.strip()[:30]
            name = ''.join(c if c.isalnum() or c in ' -_' else '' for c in name)
            return name.strip()
        
        # Generate name from type
        type_name = element_type.replace('Gui', '').lower()
        return f"{type_name}_{index + 1}"
    
    def update_results_display(self):
        """Update the results listbox."""
        for element in self.found_elements:
            display_text = f"{element['name']:<20} | {element['type']:<15} | {element['id']}"
            self.results_listbox.insert(tk.END, display_text)
    
    def clear_results(self):
        """Clear all results."""
        self.found_elements.clear()
        self.results_listbox.delete(0, tk.END)
        self.count_var.set("Elements found: 0")
        self.log_message("Results cleared")
    
    def export_json(self):
        """Export results to JSON file."""
        if not self.found_elements:
            messagebox.showwarning("Warning", "No elements to export!")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tcode = self.tcode_var.get() or "unknown"
            filename = f"sap_elements_{tcode}_{timestamp}.json"
            
            export_data = {
                'scan_info': {
                    'timestamp': datetime.now().isoformat(),
                    'transaction': tcode,
                    'total_elements': len(self.found_elements),
                    'sap_system': self.status_var.get()
                },
                'elements': self.found_elements
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"Elements exported to: {filename}")
            messagebox.showinfo("Export Success", f"Exported to {filename}")
            
        except Exception as e:
            self.log_message(f"Export error: {e}")
            messagebox.showerror("Export Error", f"Export failed:\n{e}")
    
    def copy_field_ids(self):
        """Copy field IDs to clipboard in Python dictionary format."""
        if not self.found_elements:
            messagebox.showwarning("Warning", "No elements to copy!")
            return
            
        try:
            # Create field IDs dictionary
            field_ids = {}
            for element in self.found_elements:
                clean_name = element['name'].lower().replace(' ', '_').replace('-', '_')
                clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '_')
                if clean_name:
                    field_ids[clean_name] = element['id']
            
            # Format as Python dictionary
            lines = ["self.field_ids = {"]
            for name, field_id in field_ids.items():
                lines.append(f'    "{name}": "{field_id}",')
            lines.append("}")
            
            dict_text = "\n".join(lines)
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(dict_text)
            
            self.log_message(f"Copied {len(field_ids)} field IDs to clipboard")
            messagebox.showinfo("Copied", f"Copied {len(field_ids)} field IDs as Python dictionary!")
            
        except Exception as e:
            self.log_message(f"Copy error: {e}")
            messagebox.showerror("Copy Error", f"Copy failed:\n{e}")
    
    def run(self):
        """Run the application."""
        self.log_message("SAP Element Scanner started")
        self.log_message("Instructions:")
        self.log_message("1. Connect to SAP")
        self.log_message("2. Navigate to desired transaction")
        self.log_message("3. Click 'Scan Current Screen'")
        self.log_message("4. Export or copy field IDs")
        
        self.root.mainloop()


def main():
    """Main function."""
    print("SAP Element Scanner")
    print("Simple tool to find field IDs for any transaction")
    print("No colors, no fancy UI - just functionality")
    
    try:
        app = SimpleSAPScanner()
        app.run()
    except Exception as e:
        print(f"Failed to start: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()