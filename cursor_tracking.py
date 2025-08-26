#!/usr/bin/env python3
"""
SAP Element Recorder - Cursor Tracking System
============================================
Records every SAP element you hover over or click on
Automatically captures: Element, Type, ID, Text, Properties
No more manual field finding - just move your cursor!

Author: SAP Automation Helper
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import win32com.client
import pythoncom
import win32gui
import win32api
import win32con
import time
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import threading
import keyboard
import mouse

class SAPElementRecorder:
    """
    SAP Element Recorder that tracks cursor and records SAP elements
    """
    
    def __init__(self):
        self.session = None
        self.is_recording = False
        self.recorded_elements = []
        self.last_element_id = None
        self.recording_thread = None
        
        self.setup_logging()
        self.setup_gui()
        
    def setup_logging(self):
        """Setup logging system."""
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        log_filename = f"logs/sap_recorder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        
    def setup_gui(self):
        """Setup the GUI interface."""
        self.root = tk.Tk()
        self.root.title("SAP Element Recorder - Cursor Tracking")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f0f0f0")
        
        # Configure styles
        style = ttk.Style()
        style.configure("Record.TButton", 
                       background="#dc3545", foreground="white",
                       font=("Arial", 10, "bold"), padding=(10, 8))
        style.configure("Stop.TButton",
                       background="#6c757d", foreground="white", 
                       font=("Arial", 10, "bold"), padding=(10, 8))
        style.configure("Connect.TButton",
                       background="#007bff", foreground="white",
                       font=("Arial", 10, "bold"), padding=(10, 8))
        style.configure("Export.TButton",
                       background="#28a745", foreground="white",
                       font=("Arial", 9, "bold"), padding=(8, 6))
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = ttk.Label(header_frame, 
                               text="SAP Element Recorder - Cursor Tracking System", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame,
                                  text="Move cursor over SAP elements to automatically record their properties",
                                  font=("Arial", 11), foreground="gray")
        subtitle_label.pack(pady=(5, 0))
        
        # Connection Section
        conn_frame = ttk.LabelFrame(main_container, text="SAP Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        conn_inner = ttk.Frame(conn_frame)
        conn_inner.pack(fill=tk.X)
        
        self.connection_status_var = tk.StringVar(value="Not Connected")
        status_label = ttk.Label(conn_inner, textvariable=self.connection_status_var,
                                font=("Arial", 11, "bold"), foreground="#dc3545")
        status_label.pack(side=tk.LEFT)
        
        connect_btn = ttk.Button(conn_inner, text="Connect to SAP",
                                command=self.connect_to_sap, style="Connect.TButton")
        connect_btn.pack(side=tk.RIGHT)
        
        # Recording Controls
        control_frame = ttk.LabelFrame(main_container, text="Recording Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        control_inner = ttk.Frame(control_frame)
        control_inner.pack(fill=tk.X)
        
        self.record_btn = ttk.Button(control_inner, text="🔴 START Recording",
                                    command=self.start_recording, style="Record.TButton")
        self.record_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_inner, text="⏹ Stop Recording", 
                                  command=self.stop_recording, state="disabled", style="Stop.TButton")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(control_inner, text="🗑 Clear All",
                              command=self.clear_results)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status and counters
        status_frame = ttk.Frame(control_inner)
        status_frame.pack(side=tk.RIGHT)
        
        self.recording_status_var = tk.StringVar(value="Ready to record")
        status_label = ttk.Label(status_frame, textvariable=self.recording_status_var,
                                font=("Arial", 10))
        status_label.pack()
        
        self.element_count_var = tk.StringVar(value="Elements recorded: 0")
        count_label = ttk.Label(status_frame, textvariable=self.element_count_var,
                               font=("Arial", 9), foreground="gray")
        count_label.pack()
        
        # Instructions
        instr_frame = ttk.LabelFrame(main_container, text="Instructions", padding="10")
        instr_frame.pack(fill=tk.X, pady=(0, 10))
        
        instructions = """1. Connect to SAP and navigate to your desired screen (MD04, etc.)
2. Click 'START Recording' 
3. Move your cursor over SAP elements you want to capture
4. Click on elements to record them with full details
5. Press ESC to stop recording, or click 'Stop Recording'
6. Export results to JSON file for future use

Hotkeys: F1=Start Recording, F2=Stop Recording, ESC=Emergency Stop"""
        
        instr_label = ttk.Label(instr_frame, text=instructions, font=("Arial", 9), justify=tk.LEFT)
        instr_label.pack(anchor=tk.W)
        
        # Results Section
        results_frame = ttk.LabelFrame(main_container, text="Recorded Elements", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Results treeview
        columns = ("Element", "Type", "ID", "Text", "Properties")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12)
        
        # Configure columns
        self.results_tree.heading("Element", text="Element Name")
        self.results_tree.heading("Type", text="Type")
        self.results_tree.heading("ID", text="SAP ID")
        self.results_tree.heading("Text", text="Text/Value")
        self.results_tree.heading("Properties", text="Properties")
        
        self.results_tree.column("Element", width=150)
        self.results_tree.column("Type", width=120)
        self.results_tree.column("ID", width=300)
        self.results_tree.column("Text", width=150)
        self.results_tree.column("Properties", width=200)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        h_scroll = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack treeview and scrollbars
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Export buttons
        export_frame = ttk.Frame(results_frame)
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(export_frame, text="📁 Export to JSON",
                  command=self.export_to_json, style="Export.TButton").pack(side=tk.LEFT)
        ttk.Button(export_frame, text="📋 Copy Field IDs",
                  command=self.copy_field_ids, style="Export.TButton").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(export_frame, text="📄 Generate Code",
                  command=self.generate_code, style="Export.TButton").pack(side=tk.LEFT, padx=(10, 0))
        
        # Log Section
        log_frame = ttk.LabelFrame(main_container, text="Activity Log", padding="10")
        log_frame.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, width=120, font=("Consolas", 8))
        self.log_text.pack(fill=tk.X)
        
        # Setup hotkeys
        self.setup_hotkeys()
        
    def setup_hotkeys(self):
        """Setup global hotkeys for recording control."""
        try:
            keyboard.add_hotkey('f1', self.hotkey_start_recording)
            keyboard.add_hotkey('f2', self.hotkey_stop_recording) 
            keyboard.add_hotkey('esc', self.emergency_stop)
            self.log_message("Hotkeys registered: F1=Start, F2=Stop, ESC=Emergency Stop")
        except Exception as e:
            self.log_message(f"Could not register hotkeys: {e}", "WARNING")
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to GUI log and logger."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        safe_message = str(message).encode('ascii', 'replace').decode('ascii')
        log_entry = f"[{timestamp}] {level}: {safe_message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        if hasattr(self, 'logger'):
            if level == "INFO":
                self.logger.info(safe_message)
            elif level == "ERROR":
                self.logger.error(safe_message)
            elif level == "WARNING":
                self.logger.warning(safe_message)
        
        self.root.update_idletasks()
        
    def connect_to_sap(self) -> bool:
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
    
    def start_recording(self):
        """Start recording SAP elements."""
        if not self.session:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
            
        self.is_recording = True
        self.record_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.recording_status_var.set("🔴 RECORDING - Move cursor over SAP elements")
        
        self.log_message("Started element recording - move cursor over SAP elements")
        
        # Start recording in separate thread
        self.recording_thread = threading.Thread(target=self.recording_loop, daemon=True)
        self.recording_thread.start()
        
    def recording_loop(self):
        """Main recording loop that tracks cursor position."""
        try:
            while self.is_recording:
                try:
                    # Get cursor position
                    cursor_pos = win32gui.GetCursorPos()
                    
                    # Get window under cursor
                    hwnd = win32gui.WindowFromPoint(cursor_pos)
                    window_text = win32gui.GetWindowText(hwnd)
                    
                    # Check if we're over a SAP window
                    if "SAP" in window_text or self.is_sap_window(hwnd):
                        # Try to get SAP element at cursor position
                        element_info = self.get_sap_element_at_cursor(cursor_pos)
                        if element_info and element_info.get('id') != self.last_element_id:
                            self.record_element(element_info)
                            self.last_element_id = element_info.get('id')
                    
                    time.sleep(0.1)  # Small delay to avoid excessive CPU usage
                    
                except Exception as e:
                    # Don't spam errors during recording
                    if self.is_recording:  # Only log if still recording
                        pass  # Silently continue
                        
        except Exception as e:
            self.log_message(f"Recording loop error: {e}", "ERROR")
    
    def is_sap_window(self, hwnd) -> bool:
        """Check if window is a SAP window."""
        try:
            class_name = win32gui.GetClassName(hwnd)
            window_text = win32gui.GetWindowText(hwnd)
            return "SAP" in class_name or "SAP" in window_text
        except:
            return False
    
    def get_sap_element_at_cursor(self, cursor_pos) -> Optional[Dict]:
        """Get SAP element information at cursor position."""
        try:
            if not self.session:
                return None
                
            # Get active window
            active_window = self.session.ActiveWindow
            if not active_window:
                return None
            
            # Try to find element at screen coordinates
            # This is a simplified approach - SAP GUI scripting doesn't directly support
            # coordinate-to-element mapping, so we'll enumerate visible elements
            return self.find_element_near_cursor(active_window, cursor_pos)
            
        except Exception as e:
            return None
    
    def find_element_near_cursor(self, container, cursor_pos, depth=0):
        """Recursively find SAP element near cursor position."""
        if depth > 5:  # Prevent deep recursion
            return None
            
        try:
            children_count = container.Children.Count
            for i in range(children_count):
                try:
                    child = container.Children(i)
                    
                    # Get element properties
                    element_type = getattr(child, 'Type', 'Unknown')
                    element_id = getattr(child, 'Id', '')
                    element_text = getattr(child, 'Text', '')
                    
                    # Check if element has screen position
                    try:
                        screen_left = getattr(child, 'ScreenLeft', None)
                        screen_top = getattr(child, 'ScreenTop', None)
                        width = getattr(child, 'Width', None)
                        height = getattr(child, 'Height', None)
                        
                        if all(v is not None for v in [screen_left, screen_top, width, height]):
                            # Check if cursor is within element bounds
                            if (screen_left <= cursor_pos[0] <= screen_left + width and
                                screen_top <= cursor_pos[1] <= screen_top + height):
                                
                                return self.extract_element_info(child)
                                
                    except:
                        pass
                    
                    # Recursively check children
                    result = self.find_element_near_cursor(child, cursor_pos, depth + 1)
                    if result:
                        return result
                        
                except:
                    continue
                    
        except:
            pass
            
        return None
    
    def extract_element_info(self, element) -> Dict:
        """Extract comprehensive information from SAP element."""
        try:
            info = {
                'timestamp': datetime.now().strftime("%H:%M:%S"),
                'element_name': '',
                'type': getattr(element, 'Type', 'Unknown'),
                'id': getattr(element, 'Id', ''),
                'text': getattr(element, 'Text', ''),
                'properties': {}
            }
            
            # Extract additional properties
            properties = [
                'Name', 'Modifiable', 'Changeable', 'ScreenLeft', 'ScreenTop',
                'Width', 'Height', 'Tooltip', 'DefaultTooltip', 'CaretPosition'
            ]
            
            for prop in properties:
                try:
                    value = getattr(element, prop, None)
                    if value is not None:
                        info['properties'][prop] = str(value)
                except:
                    pass
            
            # Generate friendly element name
            if info['text']:
                info['element_name'] = info['text'][:30]
            elif info['properties'].get('Name'):
                info['element_name'] = info['properties']['Name'][:30]
            else:
                info['element_name'] = f"{info['type']}_{len(self.recorded_elements)+1}"
            
            return info
            
        except Exception as e:
            return None
    
    def record_element(self, element_info: Dict):
        """Record element information."""
        try:
            self.recorded_elements.append(element_info)
            
            # Update GUI
            self.root.after(0, self.update_results_display, element_info)
            self.root.after(0, self.update_counters)
            
            # Log the recording
            self.log_message(f"Recorded: {element_info['element_name']} [{element_info['type']}]")
            
        except Exception as e:
            self.log_message(f"Error recording element: {e}", "ERROR")
    
    def update_results_display(self, element_info: Dict):
        """Update the results treeview with new element."""
        try:
            properties_str = f"Modifiable: {element_info['properties'].get('Modifiable', 'N/A')}"
            if element_info['properties'].get('ScreenLeft'):
                properties_str += f", Pos: ({element_info['properties']['ScreenLeft']}, {element_info['properties']['ScreenTop']})"
            
            self.results_tree.insert("", "end", values=(
                element_info['element_name'],
                element_info['type'],
                element_info['id'],
                element_info['text'][:30] + "..." if len(element_info['text']) > 30 else element_info['text'],
                properties_str
            ))
            
            # Auto-scroll to bottom
            children = self.results_tree.get_children()
            if children:
                self.results_tree.see(children[-1])
                
        except Exception as e:
            pass
    
    def update_counters(self):
        """Update element counter display."""
        count = len(self.recorded_elements)
        self.element_count_var.set(f"Elements recorded: {count}")
    
    def stop_recording(self):
        """Stop recording SAP elements."""
        self.is_recording = False
        self.record_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.recording_status_var.set("Recording stopped")
        
        count = len(self.recorded_elements)
        self.log_message(f"Recording stopped - captured {count} elements")
    
    def clear_results(self):
        """Clear all recorded results."""
        if messagebox.askyesno("Confirm Clear", "Clear all recorded elements?"):
            self.recorded_elements.clear()
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            self.update_counters()
            self.log_message("All results cleared")
    
    def export_to_json(self):
        """Export recorded elements to JSON file."""
        if not self.recorded_elements:
            messagebox.showwarning("Warning", "No elements to export!")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sap_elements_recorded_{timestamp}.json"
            
            export_data = {
                'export_info': {
                    'timestamp': datetime.now().isoformat(),
                    'total_elements': len(self.recorded_elements),
                    'sap_system': self.connection_status_var.get()
                },
                'elements': self.recorded_elements
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"Elements exported to: {filename}")
            messagebox.showinfo("Export Successful", f"Recorded elements exported to:\n{filename}")
            
        except Exception as e:
            self.log_message(f"Export error: {e}", "ERROR")
            messagebox.showerror("Export Error", f"Failed to export elements:\n{e}")
    
    def copy_field_ids(self):
        """Copy all field IDs to clipboard."""
        if not self.recorded_elements:
            messagebox.showwarning("Warning", "No elements to copy!")
            return
            
        try:
            field_ids = []
            for element in self.recorded_elements:
                if element['id']:
                    field_ids.append(f'"{element["element_name"]}": "{element["id"]}"')
            
            field_ids_text = "{\n    " + ",\n    ".join(field_ids) + "\n}"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(field_ids_text)
            
            self.log_message(f"Copied {len(field_ids)} field IDs to clipboard")
            messagebox.showinfo("Copied", f"Copied {len(field_ids)} field IDs to clipboard!")
            
        except Exception as e:
            self.log_message(f"Copy error: {e}", "ERROR")
    
    def generate_code(self):
        """Generate Python code template using recorded elements."""
        if not self.recorded_elements:
            messagebox.showwarning("Warning", "No elements to generate code from!")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_sap_code_{timestamp}.py"
            
            code_template = self.create_code_template()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(code_template)
            
            self.log_message(f"Generated code template: {filename}")
            messagebox.showinfo("Code Generated", f"Generated Python code template:\n{filename}")
            
        except Exception as e:
            self.log_message(f"Code generation error: {e}", "ERROR")
    
    def create_code_template(self) -> str:
        """Create Python code template from recorded elements."""
        field_ids = {}
        for element in self.recorded_elements:
            if element['id']:
                clean_name = element['element_name'].replace(' ', '_').replace('-', '_').lower()
                field_ids[clean_name] = element['id']
        
        code = f'''# Generated SAP Automation Code
# Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Elements recorded: {len(self.recorded_elements)}

import win32com.client
import pythoncom
import time

class GeneratedSAPAutomation:
    def __init__(self):
        # Recorded field IDs
        self.field_ids = {{
'''
        
        for name, field_id in field_ids.items():
            code += f'            "{name}": "{field_id}",\n'
        
        code += '''        }
        
        self.session = None
    
    def connect_to_sap(self):
        """Connect to SAP GUI."""
        pythoncom.CoInitialize()
        sap_gui_auto = win32com.client.GetObject("SAPGUI")
        application = sap_gui_auto.GetScriptingEngine
        connection = application.Children(0)
        self.session = connection.Children(0)
    
    def fill_field(self, field_name, value):
        """Fill a field using recorded field ID."""
        try:
            field_id = self.field_ids[field_name]
            field = self.session.findById(field_id)
            field.text = value
            return True
        except Exception as e:
            print(f"Error filling {field_name}: {e}")
            return False

# Example usage:
# automation = GeneratedSAPAutomation()
# automation.connect_to_sap()
# automation.fill_field("material_field", "123456")
'''
        
        return code
    
    def hotkey_start_recording(self):
        """Hotkey handler for starting recording."""
        if not self.is_recording and self.session:
            self.start_recording()
    
    def hotkey_stop_recording(self):
        """Hotkey handler for stopping recording."""
        if self.is_recording:
            self.stop_recording()
    
    def emergency_stop(self):
        """Emergency stop for recording."""
        if self.is_recording:
            self.stop_recording()
            self.log_message("Emergency stop activated!", "WARNING")
    
    def run(self):
        """Run the application."""
        self.log_message("SAP Element Recorder Started")
        self.log_message("Connect to SAP and start recording to capture element information")
        self.log_message("Use hotkeys: F1=Start Recording, F2=Stop, ESC=Emergency Stop")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.log_message("Application closed")
        finally:
            try:
                keyboard.unhook_all_hotkeys()
            except:
                pass


def main():
    """Main function."""
    print("="*60)
    print("SAP ELEMENT RECORDER - CURSOR TRACKING SYSTEM")
    print("="*60)
    print("Features:")
    print("• Automatic element detection via cursor movement")
    print("• Records: Element, Type, ID, Text, Properties")
    print("• Real-time recording with visual feedback")
    print("• Export to JSON and generate Python code")
    print("• Hotkey support: F1=Start, F2=Stop, ESC=Emergency")
    print()
    print("Instructions:")
    print("1. Connect to SAP")
    print("2. Navigate to your SAP screen (MD04, etc.)")
    print("3. Start recording")
    print("4. Move cursor over elements you want to capture")
    print("5. Export results when done")
    print("="*60)
    
    try:
        app = SAPElementRecorder()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()