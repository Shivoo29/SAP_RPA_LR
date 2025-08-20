import tkinter as tk
from tkinter import ttk, scrolledtext
import win32com.client
import pythoncom
import time

class SAPFieldFinder:
    """
    SAP Field Finder - Discovers field IDs for any SAP screen
    This will help us find the correct field IDs for your MD04 screen
    """
    
    def __init__(self):
        self.setup_gui()
        self.session = None
        
    def setup_gui(self):
        """Setup the field finder GUI."""
        self.root = tk.Tk()
        self.root.title("SAP Field Finder - Find Correct Field IDs")
        self.root.geometry("1000x700")
        
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="SAP Field Finder Tool", 
                               font=("Arial", 16, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Discover the correct field IDs for your SAP screen", 
                                  font=("Arial", 10), foreground="blue")
        subtitle_label.pack()
        
        # Connection Status
        self.status_var = tk.StringVar(value="Not Connected")
        status_label = ttk.Label(header_frame, textvariable=self.status_var, 
                                font=("Arial", 12, "bold"))
        status_label.pack(pady=5)
        
        # Control Buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="1. Connect to SAP", 
                  command=self.connect_sap).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="2. Go to MD04", 
                  command=self.go_to_md04).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="3. Find All Fields", 
                  command=self.find_all_fields).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="4. Find Input Fields", 
                  command=self.find_input_fields).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="5. Test Field", 
                  command=self.test_field).pack(side=tk.LEFT, padx=5)
        
        # Test Field Section
        test_frame = ttk.LabelFrame(self.root, text="Test Specific Field", padding="10")
        test_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(test_frame, text="Field ID to test:").pack(side=tk.LEFT)
        self.test_field_var = tk.StringVar()
        test_entry = ttk.Entry(test_frame, textvariable=self.test_field_var, width=40)
        test_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(test_frame, text="Test Value:").pack(side=tk.LEFT, padx=(10, 0))
        self.test_value_var = tk.StringVar(value="857-A65473-106")
        value_entry = ttk.Entry(test_frame, textvariable=self.test_value_var, width=20)
        value_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_frame, text="Test This Field", 
                  command=self.test_specific_field).pack(side=tk.LEFT, padx=5)
        
        # Quick Field Buttons
        quick_frame = ttk.LabelFrame(self.root, text="Quick Field Tests", padding="10")
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Common material field IDs to test
        common_fields = [
            ("Material Field 1", "wnd[0]/usr/ctxtRM61E-MATNR"),
            ("Material Field 2", "wnd[0]/usr/ctxtMANTR"),
            ("Material Field 3", "wnd[0]/usr/txtMANTR"),
            ("Material Field 4", "wnd[0]/usr/ctxtMATNR"),
            ("Material Field 5", "wnd[0]/usr/ctxtRMMG1-MATNR")
        ]
        
        for name, field_id in common_fields:
            ttk.Button(quick_frame, text=name, 
                      command=lambda f=field_id: self.quick_test_field(f)).pack(side=tk.LEFT, padx=2)
        
        # Results Display
        results_frame = ttk.LabelFrame(self.root, text="Field Discovery Results", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create text widget with scrollbar
        self.results_text = scrolledtext.ScrolledText(results_frame, height=25, width=120, font=("Consolas", 9))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        
        # Bottom buttons
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(bottom_frame, text="Clear Results", 
                  command=self.clear_results).pack(side=tk.LEFT)
        
        ttk.Button(bottom_frame, text="Generate Code", 
                  command=self.generate_code).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(bottom_frame, text="Export Results", 
                  command=self.export_results).pack(side=tk.RIGHT)
        
    def log(self, message):
        """Add message to results."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.results_text.insert(tk.END, log_entry)
        self.results_text.see(tk.END)
        self.root.update_idletasks()
        
    def connect_sap(self):
        """Connect to SAP."""
        try:
            pythoncom.CoInitialize()
            
            self.log("Connecting to SAP GUI...")
            sap_gui_auto = win32com.client.GetObject("SAPGUI")
            application = sap_gui_auto.GetScriptingEngine
            
            if application.Children.Count > 0:
                connection = application.Children(0)
                if connection.Children.Count > 0:
                    self.session = connection.Children(0)
                    
                    info = self.session.Info
                    self.log(f"[OK] Connected to SAP!")
                    self.log(f"System: {info.SystemName}, Client: {info.Client}, User: {info.User}")
                    self.log(f"Current Transaction: {info.Transaction}")
                    
                    self.status_var.set(f"Connected: {info.SystemName}")
                    return True
            
            raise Exception("No SAP sessions found")
            
        except Exception as e:
            self.log(f"[X] Connection failed: {e}")
            self.status_var.set("Connection Failed")
            return False
    
    def go_to_md04(self):
        """Navigate to MD04 transaction."""
        if not self.session:
            self.log("[X] Not connected to SAP")
            return
            
        try:
            self.log("Navigating to MD04...")
            
            # Clear transaction field
            self.session.findById("wnd[0]/tbar[0]/okcd").text = ""
            time.sleep(0.5)
            
            # Enter MD04
            self.session.findById("wnd[0]/tbar[0]/okcd").text = "MD04"
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(3)
            
            current_transaction = self.session.Info.Transaction
            self.log(f"[OK] Current transaction: {current_transaction}")
            
            # Get screen info
            main_window = self.session.findById("wnd[0]")
            window_title = main_window.text
            self.log(f"Window title: {window_title}")
            
        except Exception as e:
            self.log(f"[X] Error navigating to MD04: {e}")
    
    def find_all_fields(self):
        """Find all available fields on the current screen."""
        if not self.session:
            self.log("[X] Not connected to SAP")
            return
            
        try:
            self.log("=== SCANNING ALL FIELDS ON CURRENT SCREEN ===")
            
            # Get the main window
            main_window = self.session.findById("wnd[0]")
            self.log(f"Window: {main_window.text}")
            
            # Recursively scan for fields
            self.scan_container(main_window, "wnd[0]", 0)
            
        except Exception as e:
            self.log(f"[X] Error scanning fields: {e}")
    
    def scan_container(self, container, path, depth):
        """Recursively scan a container for fields."""
        if depth > 5:  # Prevent infinite recursion
            return
            
        try:
            # Get children count
            try:
                children_count = container.Children.Count
            except:
                return
            
            for i in range(children_count):
                try:
                    child = container.Children(i)
                    child_path = f"{path}/{child.Name}" if hasattr(child, 'Name') else f"{path}/child[{i}]"
                    
                    # Get element type and properties
                    element_type = getattr(child, 'Type', 'Unknown')
                    element_text = getattr(child, 'Text', '')
                    element_id = getattr(child, 'Id', '')
                    
                    # Check if it's an input field
                    is_input = False
                    field_info = ""
                    
                    if element_type in ['GuiTextField', 'GuiCTextField', 'GuiPasswordField']:
                        is_input = True
                        try:
                            modifiable = getattr(child, 'Modifiable', False)
                            field_info = f"(Modifiable: {modifiable})"
                        except:
                            field_info = "(Input field)"
                    
                    # Log interesting fields
                    if is_input or element_text or 'matnr' in element_id.lower() or 'material' in element_text.lower():
                        indent = "  " * depth
                        self.log(f"{indent}[FIELD] {child_path}")
                        self.log(f"{indent}  Type: {element_type} {field_info}")
                        self.log(f"{indent}  ID: {element_id}")
                        if element_text:
                            self.log(f"{indent}  Text: '{element_text[:50]}'")
                        self.log("")
                    
                    # Recursively scan children
                    self.scan_container(child, child_path, depth + 1)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            pass
    
    def find_input_fields(self):
        """Find only input fields that could be material number fields."""
        if not self.session:
            self.log("[X] Not connected to SAP")
            return
            
        try:
            self.log("=== SCANNING FOR INPUT FIELDS ===")
            
            # Common patterns for material number fields
            material_patterns = [
                "wnd[0]/usr/ctxtRM61E-MATNR",
                "wnd[0]/usr/ctxtMANTR", 
                "wnd[0]/usr/txtMANTR",
                "wnd[0]/usr/ctxtMATNR",
                "wnd[0]/usr/ctxtRMMG1-MATNR",
                "wnd[0]/usr/ctxtMaterial",
                "wnd[0]/usr/txtMaterial",
                "wnd[0]/usr/subSUB0:SAPL*/usr/ctxtRM61E-MATNR",
                "wnd[0]/usr/subSUB1:SAPL*/usr/ctxtRM61E-MATNR"
            ]
            
            # Test each pattern
            for pattern in material_patterns:
                try:
                    if '*' in pattern:
                        # Skip wildcard patterns for now
                        continue
                        
                    field = self.session.findById(pattern)
                    if field:
                        field_type = getattr(field, 'Type', 'Unknown')
                        modifiable = getattr(field, 'Modifiable', False)
                        text = getattr(field, 'Text', '')
                        
                        self.log(f"[FOUND] {pattern}")
                        self.log(f"  Type: {field_type}")
                        self.log(f"  Modifiable: {modifiable}")
                        self.log(f"  Current text: '{text}'")
                        self.log("")
                        
                except:
                    continue
            
            # Also scan for any text fields
            self.log("=== SCANNING FOR ANY TEXT FIELDS ===")
            self.scan_for_text_fields()
            
        except Exception as e:
            self.log(f"[X] Error finding input fields: {e}")
    
    def scan_for_text_fields(self):
        """Scan for any text input fields."""
        try:
            # Try different usr containers
            containers = [
                "wnd[0]/usr",
                "wnd[0]/usr/subSUB0:SAPLMD04:0300",
                "wnd[0]/usr/subSUB1:SAPLMD04:0300", 
                "wnd[0]/usr/tabsTS_MD04/tabpTAB01/ssubTS_MD04:SAPLMD04:0300"
            ]
            
            for container_path in containers:
                try:
                    container = self.session.findById(container_path)
                    if container:
                        self.log(f"Scanning container: {container_path}")
                        self.find_text_fields_in_container(container, container_path)
                        
                except:
                    continue
                    
        except Exception as e:
            self.log(f"Error scanning for text fields: {e}")
    
    def find_text_fields_in_container(self, container, base_path):
        """Find text fields in a specific container."""
        try:
            children_count = container.Children.Count
            for i in range(children_count):
                try:
                    child = container.Children(i)
                    child_type = getattr(child, 'Type', 'Unknown')
                    
                    if child_type in ['GuiTextField', 'GuiCTextField']:
                        child_id = getattr(child, 'Id', '')
                        modifiable = getattr(child, 'Modifiable', False)
                        text = getattr(child, 'Text', '')
                        
                        if modifiable:  # Only show modifiable fields
                            full_path = f"{base_path}/{child_id}" if child_id else f"{base_path}/field[{i}]"
                            self.log(f"[TEXT FIELD] {full_path}")
                            self.log(f"  Type: {child_type}")
                            self.log(f"  Current text: '{text}'")
                            self.log("")
                            
                except:
                    continue
                    
        except:
            pass
    
    def test_field(self):
        """Test the field ID entered in the text box."""
        field_id = self.test_field_var.get().strip()
        if not field_id:
            self.log("[X] Please enter a field ID to test")
            return
            
        self.test_specific_field_id(field_id)
    
    def quick_test_field(self, field_id):
        """Quick test for common field IDs."""
        self.test_field_var.set(field_id)
        self.test_specific_field_id(field_id)
    
    def test_specific_field(self):
        """Test the specific field with a value."""
        field_id = self.test_field_var.get().strip()
        test_value = self.test_value_var.get().strip()
        
        if not field_id:
            self.log("[X] Please enter a field ID to test")
            return
            
        if not self.session:
            self.log("[X] Not connected to SAP")
            return
            
        try:
            self.log(f"=== TESTING FIELD: {field_id} ===")
            
            # Try to find the field
            field = self.session.findById(field_id)
            
            # Get field properties
            field_type = getattr(field, 'Type', 'Unknown')
            modifiable = getattr(field, 'Modifiable', False)
            current_text = getattr(field, 'Text', '')
            
            self.log(f"[OK] Field found!")
            self.log(f"  Type: {field_type}")
            self.log(f"  Modifiable: {modifiable}")
            self.log(f"  Current text: '{current_text}'")
            
            if modifiable and test_value:
                # Try to set the value
                original_text = field.text
                field.text = test_value
                time.sleep(0.5)
                
                # Check if it was set
                new_text = field.text
                if new_text == test_value:
                    self.log(f"[OK] Successfully set value to: '{test_value}'")
                    
                    # Restore original value
                    field.text = original_text
                    self.log(f"[OK] Restored original value: '{original_text}'")
                else:
                    self.log(f"[!] Value not set correctly. Expected: '{test_value}', Got: '{new_text}'")
            
            self.log("")
            
        except Exception as e:
            self.log(f"[X] Field test failed: {e}")
            self.log("")
    
    def test_specific_field_id(self, field_id):
        """Test if a specific field ID exists."""
        if not self.session:
            self.log("[X] Not connected to SAP")
            return
            
        try:
            self.log(f"Testing field: {field_id}")
            field = self.session.findById(field_id)
            
            field_type = getattr(field, 'Type', 'Unknown')
            modifiable = getattr(field, 'Modifiable', False)
            text = getattr(field, 'Text', '')
            
            self.log(f"  [OK] FOUND - Type: {field_type}, Modifiable: {modifiable}, Text: '{text}'")
            
        except Exception as e:
            self.log(f"  [X] NOT FOUND - {e}")
    
    def clear_results(self):
        """Clear the results text."""
        self.results_text.delete(1.0, tk.END)
    
    def generate_code(self):
        """Generate code based on found fields."""
        if not self.session:
            self.log("[X] Not connected to SAP")
            return
            
        self.log("=== GENERATING CODE FOR FOUND FIELDS ===")
        self.log("")
        self.log("# Based on your SAP system, use these field IDs:")
        self.log("")
        
        # Test the most likely fields and generate code
        material_fields = [
            "wnd[0]/usr/ctxtRM61E-MATNR",
            "wnd[0]/usr/ctxtMANTR", 
            "wnd[0]/usr/txtMANTR",
            "wnd[0]/usr/ctxtMATNR"
        ]
        
        working_field = None
        for field_id in material_fields:
            try:
                field = self.session.findById(field_id)
                if field and getattr(field, 'Modifiable', False):
                    working_field = field_id
                    break
            except:
                continue
        
        if working_field:
            self.log(f"# Material field found: {working_field}")
            self.log(f"self.session.findById(\"{working_field}\").text = part_number")
        else:
            self.log("# No working material field found - manual investigation needed")
            
        self.log("")
    
    def export_results(self):
        """Export results to a file."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"sap_field_scan_{timestamp}.txt"
            
            with open(filename, 'w') as f:
                f.write(self.results_text.get(1.0, tk.END))
            
            self.log(f"Results exported to: {filename}")
            
        except Exception as e:
            self.log(f"Export failed: {e}")
    
    def run(self):
        """Run the field finder."""
        self.log("SAP Field Finder Tool Started")
        self.log("This tool will help you find the correct field IDs for your SAP system")
        self.log("")
        self.log("Instructions:")
        self.log("1. Click 'Connect to SAP'")
        self.log("2. Click 'Go to MD04'") 
        self.log("3. Click 'Find All Fields' or 'Find Input Fields'")
        self.log("4. Test specific fields using the test section")
        self.log("5. Generate code for working fields")
        self.log("")
        
        self.root.mainloop()


def main():
    """Run the field finder."""
    app = SAPFieldFinder()
    app.run()


if __name__ == "__main__":
    main()