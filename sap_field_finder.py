import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import win32com.client
import pythoncom
import time
import json
from datetime import datetime

class EnhancedSAPFieldFinder:
    """
    Enhanced SAP Field Finder - Complete Field Discovery
    This will extract EVERY field ID from the current SAP window
    so you can tell me exactly which fields to use step by step
    """
    
    def __init__(self):
        self.setup_gui()
        self.session = None
        self.all_fields = []
        self.clickable_elements = []
        
    def setup_gui(self):
        """Setup the enhanced field finder GUI."""
        self.root = tk.Tk()
        self.root.title("Enhanced SAP Field Finder - Complete Discovery Tool")
        self.root.geometry("1400x900")
        self.root.state('zoomed')  # Maximize window
        
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = ttk.Label(header_frame, text="🔍 Enhanced SAP Field Finder - Complete Discovery Tool", 
                               font=("Arial", 18, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(header_frame, text="Extract ALL field IDs so you can guide me step-by-step!", 
                                  font=("Arial", 12), foreground="blue")
        subtitle_label.pack()
        
        # Connection Status
        status_frame = ttk.Frame(header_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_var = tk.StringVar(value="❌ Not Connected")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                font=("Arial", 12, "bold"))
        status_label.pack(side=tk.LEFT)
        
        ttk.Button(status_frame, text="🔌 Connect SAP", 
                  command=self.connect_sap).pack(side=tk.RIGHT)
        
        # Main Control Panel
        control_frame = ttk.LabelFrame(self.root, text="🎮 Discovery Controls", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 1 - Navigation
        nav_frame = ttk.Frame(control_frame)
        nav_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(nav_frame, text="📍 Go to MD04", 
                  command=self.go_to_md04).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(nav_frame, text="🔍 SCAN ALL FIELDS", 
                  command=self.complete_field_scan, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=2)
        
        ttk.Button(nav_frame, text="🖱️ Find Clickable Elements", 
                  command=self.find_clickable_elements).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(nav_frame, text="📝 Find Input Fields Only", 
                  command=self.find_input_fields_only).pack(side=tk.LEFT, padx=2)
        
        # Row 2 - Analysis
        analysis_frame = ttk.Frame(control_frame)
        analysis_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(analysis_frame, text="🎯 Find Material Fields", 
                  command=self.find_material_fields).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(analysis_frame, text="🔢 Find Number Fields", 
                  command=self.find_number_fields).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(analysis_frame, text="📋 Find All Tables/Grids", 
                  command=self.find_tables_and_grids).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(analysis_frame, text="🔲 Find Buttons", 
                  command=self.find_buttons).pack(side=tk.LEFT, padx=2)
        
        # Row 3 - Export/Clear
        export_frame = ttk.Frame(control_frame)
        export_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(export_frame, text="🗑️ Clear Results", 
                  command=self.clear_results).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(export_frame, text="💾 Export to JSON", 
                  command=self.export_to_json).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(export_frame, text="📄 Export to Text", 
                  command=self.export_to_text).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(export_frame, text="🎯 Generate Step-by-Step Guide", 
                  command=self.generate_step_guide).pack(side=tk.LEFT, padx=2)
        
        # Test Field Section
        test_frame = ttk.LabelFrame(self.root, text="🧪 Field Testing", padding="10")
        test_frame.pack(fill=tk.X, padx=10, pady=5)
        
        test_row1 = ttk.Frame(test_frame)
        test_row1.pack(fill=tk.X, pady=2)
        
        ttk.Label(test_row1, text="Field ID:").pack(side=tk.LEFT)
        self.test_field_var = tk.StringVar()
        test_entry = ttk.Entry(test_row1, textvariable=self.test_field_var, width=50)
        test_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(test_row1, text="Test Value:").pack(side=tk.LEFT, padx=(10, 0))
        self.test_value_var = tk.StringVar(value="857-A65473-106")
        value_entry = ttk.Entry(test_row1, textvariable=self.test_value_var, width=20)
        value_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_row1, text="🧪 Test Field", 
                  command=self.test_field).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(test_row1, text="👆 Click Element", 
                  command=self.click_element).pack(side=tk.LEFT, padx=5)
        
        # Statistics Panel
        stats_frame = ttk.LabelFrame(self.root, text="📊 Discovery Statistics", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.stats_text = ttk.Label(stats_frame, text="Ready to scan...", font=("Arial", 10))
        self.stats_text.pack()
        
        # Results Display with Notebook (Tabs)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: All Fields
        all_fields_frame = ttk.Frame(notebook)
        notebook.add(all_fields_frame, text="🔍 All Fields")
        
        self.all_fields_text = scrolledtext.ScrolledText(all_fields_frame, font=("Consolas", 9))
        self.all_fields_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 2: Input Fields Only
        input_fields_frame = ttk.Frame(notebook)
        notebook.add(input_fields_frame, text="📝 Input Fields")
        
        self.input_fields_text = scrolledtext.ScrolledText(input_fields_frame, font=("Consolas", 9))
        self.input_fields_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 3: Clickable Elements
        clickable_frame = ttk.Frame(notebook)
        notebook.add(clickable_frame, text="🖱️ Clickable Elements")
        
        self.clickable_text = scrolledtext.ScrolledText(clickable_frame, font=("Consolas", 9))
        self.clickable_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 4: Material-Related Fields
        material_frame = ttk.Frame(notebook)
        notebook.add(material_frame, text="🎯 Material Fields")
        
        self.material_text = scrolledtext.ScrolledText(material_frame, font=("Consolas", 9))
        self.material_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tab 5: Step-by-Step Guide
        guide_frame = ttk.Frame(notebook)
        notebook.add(guide_frame, text="📋 Step Guide")
        
        self.guide_text = scrolledtext.ScrolledText(guide_frame, font=("Consolas", 10))
        self.guide_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def log_to_tab(self, tab_widget, message):
        """Add message to specific tab."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        tab_widget.insert(tk.END, log_entry)
        tab_widget.see(tk.END)
        self.root.update_idletasks()
        
    def connect_sap(self):
        """Connect to SAP."""
        try:
            pythoncom.CoInitialize()
            
            self.log_to_tab(self.all_fields_text, "🔌 Connecting to SAP GUI...")
            sap_gui_auto = win32com.client.GetObject("SAPGUI")
            application = sap_gui_auto.GetScriptingEngine
            
            if application.Children.Count > 0:
                connection = application.Children(0)
                if connection.Children.Count > 0:
                    self.session = connection.Children(0)
                    
                    info = self.session.Info
                    self.log_to_tab(self.all_fields_text, f"✅ Connected to SAP!")
                    self.log_to_tab(self.all_fields_text, f"System: {info.SystemName}, Client: {info.Client}, User: {info.User}")
                    self.log_to_tab(self.all_fields_text, f"Current Transaction: {info.Transaction}")
                    
                    self.status_var.set(f"✅ Connected: {info.SystemName}")
                    return True
            
            raise Exception("No SAP sessions found")
            
        except Exception as e:
            self.log_to_tab(self.all_fields_text, f"❌ Connection failed: {e}")
            self.status_var.set("❌ Connection Failed")
            return False
    
    def go_to_md04(self):
        """Navigate to MD04 transaction."""
        if not self.session:
            messagebox.showerror("Error", "Connect to SAP first!")
            return
            
        try:
            self.log_to_tab(self.all_fields_text, "📍 Navigating to MD04...")
            
            # Clear transaction field
            self.session.findById("wnd[0]/tbar[0]/okcd").text = ""
            time.sleep(0.5)
            
            # Enter MD04
            self.session.findById("wnd[0]/tbar[0]/okcd").text = "MD04"
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(3)
            
            current_transaction = self.session.Info.Transaction
            self.log_to_tab(self.all_fields_text, f"✅ Current transaction: {current_transaction}")
            
            # Get screen info
            main_window = self.session.findById("wnd[0]")
            window_title = main_window.text
            self.log_to_tab(self.all_fields_text, f"Window title: {window_title}")
            
            self.log_to_tab(self.all_fields_text, "✅ Ready for complete field scan!")
            
        except Exception as e:
            self.log_to_tab(self.all_fields_text, f"❌ Error navigating to MD04: {e}")
    
    def complete_field_scan(self):
        """Complete comprehensive field scan."""
        if not self.session:
            messagebox.showerror("Error", "Connect to SAP first!")
            return
            
        try:
            self.all_fields = []
            
            self.log_to_tab(self.all_fields_text, "🔍 STARTING COMPLETE FIELD SCAN...")
            self.log_to_tab(self.all_fields_text, "=" * 80)
            
            # Get the main window
            main_window = self.session.findById("wnd[0]")
            window_title = main_window.text
            
            self.log_to_tab(self.all_fields_text, f"📋 Scanning Window: {window_title}")
            self.log_to_tab(self.all_fields_text, f"📋 Transaction: {self.session.Info.Transaction}")
            self.log_to_tab(self.all_fields_text, "")
            
            # Start recursive scan
            self.deep_scan_element(main_window, "wnd[0]", 0)
            
            # Update statistics
            total_fields = len(self.all_fields)
            input_fields = len([f for f in self.all_fields if f.get('is_input', False)])
            clickable_fields = len([f for f in self.all_fields if f.get('is_clickable', False)])
            
            stats_text = f"📊 Total Elements: {total_fields} | Input Fields: {input_fields} | Clickable: {clickable_fields}"
            self.stats_text.config(text=stats_text)
            
            self.log_to_tab(self.all_fields_text, "=" * 80)
            self.log_to_tab(self.all_fields_text, f"✅ SCAN COMPLETE! Found {total_fields} elements")
            self.log_to_tab(self.all_fields_text, f"📝 Input fields: {input_fields}")
            self.log_to_tab(self.all_fields_text, f"🖱️ Clickable elements: {clickable_fields}")
            
        except Exception as e:
            self.log_to_tab(self.all_fields_text, f"❌ Error during field scan: {e}")
    
    def deep_scan_element(self, element, path, depth):
        """Deep recursive scan of SAP element."""
        if depth > 10:  # Prevent infinite recursion
            return
            
        try:
            # Get element properties
            element_info = self.get_element_info(element, path, depth)
            
            if element_info:
                self.all_fields.append(element_info)
                
                # Log interesting elements
                if (element_info['is_input'] or 
                    element_info['is_clickable'] or 
                    element_info['has_text'] or
                    'material' in element_info['id'].lower() or
                    'matnr' in element_info['id'].lower()):
                    
                    indent = "  " * depth
                    self.log_to_tab(self.all_fields_text, f"{indent}🔍 ELEMENT: {path}")
                    self.log_to_tab(self.all_fields_text, f"{indent}   Type: {element_info['type']}")
                    self.log_to_tab(self.all_fields_text, f"{indent}   ID: {element_info['id']}")
                    
                    if element_info['text']:
                        self.log_to_tab(self.all_fields_text, f"{indent}   Text: '{element_info['text'][:50]}'")
                    
                    if element_info['is_input']:
                        self.log_to_tab(self.all_fields_text, f"{indent}   🔥 INPUT FIELD (Modifiable: {element_info['modifiable']})")
                    
                    if element_info['is_clickable']:
                        self.log_to_tab(self.all_fields_text, f"{indent}   👆 CLICKABLE")
                    
                    self.log_to_tab(self.all_fields_text, "")
            
            # Scan children
            try:
                children_count = element.Children.Count
                for i in range(children_count):
                    try:
                        child = element.Children(i)
                        child_name = getattr(child, 'Name', f'child[{i}]')
                        child_path = f"{path}/{child_name}"
                        
                        self.deep_scan_element(child, child_path, depth + 1)
                        
                    except Exception:
                        continue
                        
            except Exception:
                pass
                
        except Exception:
            pass
    
    def get_element_info(self, element, path, depth):
        """Get comprehensive information about an element."""
        try:
            info = {
                'path': path,
                'depth': depth,
                'type': getattr(element, 'Type', 'Unknown'),
                'id': getattr(element, 'Id', ''),
                'name': getattr(element, 'Name', ''),
                'text': getattr(element, 'Text', ''),
                'modifiable': getattr(element, 'Modifiable', False),
                'changeable': getattr(element, 'Changeable', False),
                'visible': getattr(element, 'Visible', False),
                'is_input': False,
                'is_clickable': False,
                'has_text': False
            }
            
            # Determine if it's an input field
            input_types = ['GuiTextField', 'GuiCTextField', 'GuiPasswordField', 'GuiComboBox']
            info['is_input'] = info['type'] in input_types and info['modifiable']
            
            # Determine if it's clickable
            clickable_types = ['GuiButton', 'GuiMenubar', 'GuiMenuItem', 'GuiTab', 'GuiCheckBox', 'GuiRadioButton']
            info['is_clickable'] = info['type'] in clickable_types or 'btn' in info['id'].lower()
            
            # Check if it has meaningful text
            info['has_text'] = len(info['text'].strip()) > 0
            
            # Add more specific properties for certain types
            if info['type'] in input_types:
                try:
                    info['max_length'] = getattr(element, 'MaxLength', 0)
                except:
                    info['max_length'] = 0
            
            if info['type'] == 'GuiButton':
                try:
                    info['tooltip'] = getattr(element, 'Tooltip', '')
                except:
                    info['tooltip'] = ''
            
            return info
            
        except Exception as e:
            return None
    
    def find_input_fields_only(self):
        """Show only input fields."""
        self.input_fields_text.delete(1.0, tk.END)
        
        if not self.all_fields:
            self.log_to_tab(self.input_fields_text, "❌ No fields scanned yet. Run 'SCAN ALL FIELDS' first!")
            return
        
        self.log_to_tab(self.input_fields_text, "📝 INPUT FIELDS ONLY:")
        self.log_to_tab(self.input_fields_text, "=" * 60)
        
        input_fields = [f for f in self.all_fields if f['is_input']]
        
        for i, field in enumerate(input_fields, 1):
            self.log_to_tab(self.input_fields_text, f"#{i:02d}. {field['path']}")
            self.log_to_tab(self.input_fields_text, f"     Type: {field['type']}")
            self.log_to_tab(self.input_fields_text, f"     ID: {field['id']}")
            self.log_to_tab(self.input_fields_text, f"     Modifiable: {field['modifiable']}")
            self.log_to_tab(self.input_fields_text, f"     Current Text: '{field['text']}'")
            if field.get('max_length', 0) > 0:
                self.log_to_tab(self.input_fields_text, f"     Max Length: {field['max_length']}")
            self.log_to_tab(self.input_fields_text, "")
        
        self.log_to_tab(self.input_fields_text, f"✅ Found {len(input_fields)} input fields")
    
    def find_clickable_elements(self):
        """Show only clickable elements."""
        self.clickable_text.delete(1.0, tk.END)
        
        if not self.all_fields:
            self.log_to_tab(self.clickable_text, "❌ No fields scanned yet. Run 'SCAN ALL FIELDS' first!")
            return
        
        self.log_to_tab(self.clickable_text, "🖱️ CLICKABLE ELEMENTS:")
        self.log_to_tab(self.clickable_text, "=" * 60)
        
        clickable_fields = [f for f in self.all_fields if f['is_clickable']]
        
        for i, field in enumerate(clickable_fields, 1):
            self.log_to_tab(self.clickable_text, f"#{i:02d}. {field['path']}")
            self.log_to_tab(self.clickable_text, f"     Type: {field['type']}")
            self.log_to_tab(self.clickable_text, f"     ID: {field['id']}")
            self.log_to_tab(self.clickable_text, f"     Text: '{field['text']}'")
            if field.get('tooltip'):
                self.log_to_tab(self.clickable_text, f"     Tooltip: '{field['tooltip']}'")
            self.log_to_tab(self.clickable_text, "")
        
        self.log_to_tab(self.clickable_text, f"✅ Found {len(clickable_fields)} clickable elements")
    
    def find_material_fields(self):
        """Find fields that might be material-related."""
        self.material_text.delete(1.0, tk.END)
        
        if not self.all_fields:
            self.log_to_tab(self.material_text, "❌ No fields scanned yet. Run 'SCAN ALL FIELDS' first!")
            return
        
        self.log_to_tab(self.material_text, "🎯 MATERIAL-RELATED FIELDS:")
        self.log_to_tab(self.material_text, "=" * 60)
        
        material_keywords = ['matnr', 'material', 'part', 'item', 'product']
        
        material_fields = []
        for field in self.all_fields:
            field_text = f"{field['id']} {field['text']} {field['path']}".lower()
            if any(keyword in field_text for keyword in material_keywords):
                material_fields.append(field)
        
        for i, field in enumerate(material_fields, 1):
            self.log_to_tab(self.material_text, f"#{i:02d}. {field['path']}")
            self.log_to_tab(self.material_text, f"     Type: {field['type']}")
            self.log_to_tab(self.material_text, f"     ID: {field['id']}")
            self.log_to_tab(self.material_text, f"     Text: '{field['text']}'")
            self.log_to_tab(self.material_text, f"     Input Field: {field['is_input']}")
            self.log_to_tab(self.material_text, f"     Clickable: {field['is_clickable']}")
            self.log_to_tab(self.material_text, "")
        
        self.log_to_tab(self.material_text, f"✅ Found {len(material_fields)} material-related fields")
    
    def find_number_fields(self):
        """Find numeric input fields."""
        if not self.all_fields:
            messagebox.showwarning("Warning", "No fields scanned yet. Run 'SCAN ALL FIELDS' first!")
            return
        
        number_fields = []
        for field in self.all_fields:
            if field['is_input'] and ('number' in field['id'].lower() or 
                                    'qty' in field['id'].lower() or
                                    'amount' in field['id'].lower() or
                                    field['text'].isdigit()):
                number_fields.append(field)
        
        self.log_to_tab(self.all_fields_text, f"🔢 Found {len(number_fields)} numeric fields")
        for field in number_fields:
            self.log_to_tab(self.all_fields_text, f"   {field['path']} - {field['text']}")
    
    def find_tables_and_grids(self):
        """Find table and grid elements."""
        if not self.all_fields:
            messagebox.showwarning("Warning", "No fields scanned yet. Run 'SCAN ALL FIELDS' first!")
            return
        
        table_types = ['GuiTableControl', 'GuiGridView', 'GuiContainerShell']
        table_fields = [f for f in self.all_fields if f['type'] in table_types]
        
        self.log_to_tab(self.all_fields_text, f"📋 Found {len(table_fields)} tables/grids")
        for field in table_fields:
            self.log_to_tab(self.all_fields_text, f"   {field['path']} - Type: {field['type']}")
    
    def find_buttons(self):
        """Find all button elements."""
        if not self.all_fields:
            messagebox.showwarning("Warning", "No fields scanned yet. Run 'SCAN ALL FIELDS' first!")
            return
        
        button_fields = [f for f in self.all_fields if f['type'] == 'GuiButton']
        
        self.log_to_tab(self.all_fields_text, f"🔲 Found {len(button_fields)} buttons")
        for field in button_fields:
            self.log_to_tab(self.all_fields_text, f"   {field['path']} - '{field['text']}'")
    
    def test_field(self):
        """Test a specific field."""
        field_id = self.test_field_var.get().strip()
        test_value = self.test_value_var.get().strip()
        
        if not field_id:
            messagebox.showwarning("Warning", "Enter a field ID to test!")
            return
        
        if not self.session:
            messagebox.showerror("Error", "Connect to SAP first!")
            return
        
        try:
            self.log_to_tab(self.all_fields_text, f"🧪 TESTING FIELD: {field_id}")
            
            field = self.session.findById(field_id)
            
            field_type = getattr(field, 'Type', 'Unknown')
            modifiable = getattr(field, 'Modifiable', False)
            current_text = getattr(field, 'Text', '')
            
            self.log_to_tab(self.all_fields_text, f"   ✅ Field found!")
            self.log_to_tab(self.all_fields_text, f"   Type: {field_type}")
            self.log_to_tab(self.all_fields_text, f"   Modifiable: {modifiable}")
            self.log_to_tab(self.all_fields_text, f"   Current text: '{current_text}'")
            
            if modifiable and test_value:
                original_text = field.text
                field.text = test_value
                time.sleep(0.5)
                
                new_text = field.text
                if new_text == test_value:
                    self.log_to_tab(self.all_fields_text, f"   ✅ Successfully set value to: '{test_value}'")
                    field.text = original_text
                    self.log_to_tab(self.all_fields_text, f"   ✅ Restored original value")
                else:
                    self.log_to_tab(self.all_fields_text, f"   ❌ Value not set correctly")
            
        except Exception as e:
            self.log_to_tab(self.all_fields_text, f"   ❌ Test failed: {e}")
    
    def click_element(self):
        """Click/activate an element."""
        field_id = self.test_field_var.get().strip()
        
        if not field_id:
            messagebox.showwarning("Warning", "Enter a field ID to click!")
            return
        
        if not self.session:
            messagebox.showerror("Error", "Connect to SAP first!")
            return
        
        try:
            self.log_to_tab(self.all_fields_text, f"👆 CLICKING ELEMENT: {field_id}")
            
            element = self.session.findById(field_id)
            element_type = getattr(element, 'Type', 'Unknown')
            
            # Try different click methods
            if element_type == 'GuiButton':
                element.press()
                self.log_to_tab(self.all_fields_text, f"   ✅ Button pressed")
            else:
                element.setFocus()
                time.sleep(0.2)
                try:
                    element.doubleClick()
                    self.log_to_tab(self.all_fields_text, f"   ✅ Double-clicked element")
                except:
                    self.log_to_tab(self.all_fields_text, f"   ✅ Focused element")
            
        except Exception as e:
            self.log_to_tab(self.all_fields_text, f"   ❌ Click failed: {e}")

    def generate_step_guide(self):
        """Generate a step-by-step guide template for the user."""
        self.guide_text.delete(1.0, tk.END)
        
        if not self.all_fields:
            self.log_to_tab(self.guide_text, "❌ No fields scanned yet. Run 'SCAN ALL FIELDS' first!")
            return
        
        # Generate comprehensive step-by-step guide
        self.log_to_tab(self.guide_text, "📋 STEP-BY-STEP WORKFLOW GUIDE")
        self.log_to_tab(self.guide_text, "=" * 80)
        self.log_to_tab(self.guide_text, "")
        self.log_to_tab(self.guide_text, "🎯 INSTRUCTIONS FOR USER:")
        self.log_to_tab(self.guide_text, "Look at the fields below and tell me exactly which ones to use!")
        self.log_to_tab(self.guide_text, "")
        self.log_to_tab(self.guide_text, "FORMAT: Tell me like this:")
        self.log_to_tab(self.guide_text, "STEP 1: Click on field #05 (the material input field)")
        self.log_to_tab(self.guide_text, "STEP 2: Enter part number in field #05")
        self.log_to_tab(self.guide_text, "STEP 3: Click on field #12 (MRP area)")
        self.log_to_tab(self.guide_text, "STEP 4: Enter '1000' in field #12")
        self.log_to_tab(self.guide_text, "STEP 5: Press Enter or click button #23")
        self.log_to_tab(self.guide_text, "etc...")
        self.log_to_tab(self.guide_text, "")
        self.log_to_tab(self.guide_text, "🔍 AVAILABLE INPUT FIELDS:")
        self.log_to_tab(self.guide_text, "-" * 50)
        
        # List all input fields with numbers
        input_fields = [f for f in self.all_fields if f['is_input']]
        for i, field in enumerate(input_fields, 1):
            self.log_to_tab(self.guide_text, f"FIELD #{i:02d}: {field['path']}")
            self.log_to_tab(self.guide_text, f"          Type: {field['type']}")
            self.log_to_tab(self.guide_text, f"          Current: '{field['text']}'")
            if 'matnr' in field['id'].lower() or 'material' in field['text'].lower():
                self.log_to_tab(self.guide_text, f"          🎯 LIKELY MATERIAL FIELD!")
            self.log_to_tab(self.guide_text, "")
        
        self.log_to_tab(self.guide_text, "🖱️ AVAILABLE CLICKABLE ELEMENTS:")
        self.log_to_tab(self.guide_text, "-" * 50)
        
        # List all clickable elements with numbers
        clickable_fields = [f for f in self.all_fields if f['is_clickable']]
        for i, field in enumerate(clickable_fields, 1):
            self.log_to_tab(self.guide_text, f"BUTTON #{i:02d}: {field['path']}")
            self.log_to_tab(self.guide_text, f"            Type: {field['type']}")
            self.log_to_tab(self.guide_text, f"            Text: '{field['text']}'")
            if 'execute' in field['text'].lower() or 'enter' in field['text'].lower():
                self.log_to_tab(self.guide_text, f"            🎯 LIKELY EXECUTE BUTTON!")
            self.log_to_tab(self.guide_text, "")
        
        self.log_to_tab(self.guide_text, "📋 TABLES AND GRIDS:")
        self.log_to_tab(self.guide_text, "-" * 50)
        
        # List tables/grids
        table_types = ['GuiTableControl', 'GuiGridView', 'GuiContainerShell']
        table_fields = [f for f in self.all_fields if f['type'] in table_types]
        for i, field in enumerate(table_fields, 1):
            self.log_to_tab(self.guide_text, f"TABLE #{i:02d}: {field['path']}")
            self.log_to_tab(self.guide_text, f"           Type: {field['type']}")
            self.log_to_tab(self.guide_text, "")
        
        self.log_to_tab(self.guide_text, "🎯 MATERIAL-RELATED FIELDS:")
        self.log_to_tab(self.guide_text, "-" * 50)
        
        # Highlight material-related fields
        material_keywords = ['matnr', 'material', 'part', 'item']
        material_fields = []
        for field in self.all_fields:
            field_text = f"{field['id']} {field['text']}".lower()
            if any(keyword in field_text for keyword in material_keywords):
                material_fields.append(field)
        
        for i, field in enumerate(material_fields, 1):
            self.log_to_tab(self.guide_text, f"MATERIAL #{i:02d}: {field['path']}")
            self.log_to_tab(self.guide_text, f"              Type: {field['type']}")
            self.log_to_tab(self.guide_text, f"              Input: {field['is_input']}")
            self.log_to_tab(self.guide_text, f"              Text: '{field['text']}'")
            self.log_to_tab(self.guide_text, "")
        
        self.log_to_tab(self.guide_text, "=" * 80)
        self.log_to_tab(self.guide_text, "🎯 NOW TELL ME THE EXACT STEPS!")
        self.log_to_tab(self.guide_text, "Copy the field paths and tell me:")
        self.log_to_tab(self.guide_text, "1. Which field to enter the part number")
        self.log_to_tab(self.guide_text, "2. Which field to enter MRP area")
        self.log_to_tab(self.guide_text, "3. Which button to click to execute")
        self.log_to_tab(self.guide_text, "4. Which table/grid will show results")
        self.log_to_tab(self.guide_text, "5. Which field will contain the description")
        self.log_to_tab(self.guide_text, "=" * 80)
        
    def export_to_json(self):
        """Export all field data to JSON."""
        if not self.all_fields:
            messagebox.showwarning("Warning", "No fields to export. Run scan first!")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                title="Save Field Data as JSON",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialname=f"sap_fields_{timestamp}.json"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'scan_info': {
                            'timestamp': datetime.now().isoformat(),
                            'transaction': self.session.Info.Transaction if self.session else 'Unknown',
                            'total_fields': len(self.all_fields)
                        },
                        'fields': self.all_fields
                    }, f, indent=2, ensure_ascii=False)
                
                self.log_to_tab(self.all_fields_text, f"💾 Exported {len(self.all_fields)} fields to: {filename}")
                messagebox.showinfo("Export Complete", f"Exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def export_to_text(self):
        """Export all field data to text file."""
        if not self.all_fields:
            messagebox.showwarning("Warning", "No fields to export. Run scan first!")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = filedialog.asksaveasfilename(
                title="Save Field Data as Text",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialname=f"sap_fields_{timestamp}.txt"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("SAP FIELD DISCOVERY REPORT\n")
                    f.write("=" * 50 + "\n")
                    f.write(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Transaction: {self.session.Info.Transaction if self.session else 'Unknown'}\n")
                    f.write(f"Total Fields: {len(self.all_fields)}\n\n")
                    
                    # Input fields
                    input_fields = [f for f in self.all_fields if f['is_input']]
                    f.write(f"INPUT FIELDS ({len(input_fields)}):\n")
                    f.write("-" * 30 + "\n")
                    for i, field in enumerate(input_fields, 1):
                        f.write(f"{i:02d}. {field['path']}\n")
                        f.write(f"    Type: {field['type']}\n")
                        f.write(f"    ID: {field['id']}\n")
                        f.write(f"    Text: '{field['text']}'\n")
                        f.write(f"    Modifiable: {field['modifiable']}\n\n")
                    
                    # Clickable elements
                    clickable_fields = [f for f in self.all_fields if f['is_clickable']]
                    f.write(f"\nCLICKABLE ELEMENTS ({len(clickable_fields)}):\n")
                    f.write("-" * 30 + "\n")
                    for i, field in enumerate(clickable_fields, 1):
                        f.write(f"{i:02d}. {field['path']}\n")
                        f.write(f"    Type: {field['type']}\n")
                        f.write(f"    Text: '{field['text']}'\n\n")
                    
                    # All fields
                    f.write(f"\nALL FIELDS ({len(self.all_fields)}):\n")
                    f.write("-" * 30 + "\n")
                    for i, field in enumerate(self.all_fields, 1):
                        f.write(f"{i:03d}. {field['path']}\n")
                        f.write(f"     Type: {field['type']}\n")
                        f.write(f"     ID: {field['id']}\n")
                        f.write(f"     Text: '{field['text']}'\n")
                        f.write(f"     Input: {field['is_input']}\n")
                        f.write(f"     Clickable: {field['is_clickable']}\n\n")
                
                self.log_to_tab(self.all_fields_text, f"📄 Exported {len(self.all_fields)} fields to: {filename}")
                messagebox.showinfo("Export Complete", f"Exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")
    
    def clear_results(self):
        """Clear all results."""
        self.all_fields_text.delete(1.0, tk.END)
        self.input_fields_text.delete(1.0, tk.END)
        self.clickable_text.delete(1.0, tk.END)
        self.material_text.delete(1.0, tk.END)
        self.guide_text.delete(1.0, tk.END)
        self.all_fields = []
        self.stats_text.config(text="Ready to scan...")
        
        self.log_to_tab(self.all_fields_text, "🗑️ Results cleared. Ready for new scan!")
    
    def run(self):
        """Run the enhanced field finder."""
        self.log_to_tab(self.all_fields_text, "🔍 Enhanced SAP Field Finder Started!")
        self.log_to_tab(self.all_fields_text, "")
        self.log_to_tab(self.all_fields_text, "📋 INSTRUCTIONS:")
        self.log_to_tab(self.all_fields_text, "1. 🔌 Connect to SAP")
        self.log_to_tab(self.all_fields_text, "2. 📍 Go to MD04 (or any SAP screen)")
        self.log_to_tab(self.all_fields_text, "3. 🔍 Click 'SCAN ALL FIELDS' for complete discovery")
        self.log_to_tab(self.all_fields_text, "4. 📋 Check different tabs for organized results")
        self.log_to_tab(self.all_fields_text, "5. 🎯 Generate Step Guide to see numbered fields")
        self.log_to_tab(self.all_fields_text, "6. 💾 Export results to share with me")
        self.log_to_tab(self.all_fields_text, "")
        self.log_to_tab(self.all_fields_text, "🎯 GOAL: Find the exact field IDs so you can tell me:")
        self.log_to_tab(self.all_fields_text, "   - Which field for part number input")
        self.log_to_tab(self.all_fields_text, "   - Which field for MRP area")
        self.log_to_tab(self.all_fields_text, "   - Which button to execute")
        self.log_to_tab(self.all_fields_text, "   - Which table shows results")
        self.log_to_tab(self.all_fields_text, "   - Which field has description")
        self.log_to_tab(self.all_fields_text, "")
        self.log_to_tab(self.all_fields_text, "🚀 Let's discover ALL the fields!")
        
        self.root.mainloop()


def main():
    """Run the enhanced field finder."""
    print("=" * 80)
    print("ENHANCED SAP FIELD FINDER - COMPLETE DISCOVERY TOOL")
    print("=" * 80)
    print()
    print("🎯 PURPOSE:")
    print("This tool will extract EVERY field ID from your SAP screen")
    print("so you can tell me exactly which fields to use step-by-step!")
    print()
    print("🔍 FEATURES:")
    print("• Complete recursive scan of all SAP elements")
    print("• Organized tabs for different field types")
    print("• Input fields detection")
    print("• Clickable elements discovery")
    print("• Material-related field highlighting")
    print("• Step-by-step guide generation")
    print("• Export to JSON/Text for sharing")
    print()
    print("📋 WORKFLOW:")
    print("1. Connect to SAP")
    print("2. Navigate to MD04")
    print("3. Run complete field scan")
    print("4. Review organized results")
    print("5. Generate step-by-step guide")
    print("6. Tell me which fields to use!")
    print()
    print("🚀 Starting Enhanced Field Finder...")
    print("=" * 80)
    
    try:
        app = EnhancedSAPFieldFinder()
        app.run()
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()