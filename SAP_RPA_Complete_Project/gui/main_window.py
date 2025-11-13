"""
Main GUI Window
===============
Main graphical user interface for SAP RPA automation.
Refactored to use a root.after() loop for stable, single-threaded COM access.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
from pathlib import Path
from datetime import datetime

from core.sap_connector import SAPConnector
from workflows.scenario_manager import ScenarioManager
from data.excel_manager import ExcelManager
from config import Config


class MainWindow:
    """Main application window."""
    
    def __init__(self, config: Config):
        """
        Initialize main window.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        self.sap_connector = SAPConnector()
        self.excel_manager = ExcelManager()
        self.scenario_manager = None  # Initialized after SAP connection
        
        # State for the root.after() loop
        self.is_processing = False
        self.materials_queue = []
        self.current_material_index = 0
        self.current_results = []
        
        # Setup GUI
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the main GUI window."""
        self.root = tk.Tk()
        self.root.title("SAP RPA - Multi-Scenario Automation System")
        self.root.geometry("1200x900")
        
        try:
            self.root.state('zoomed')
        except tk.TclError:
            pass # Fails on some platforms
        
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        
        self._create_header(main_container)
        self._create_connection_section(main_container)
        self._create_input_section(main_container)
        self._create_config_section(main_container)
        self._create_controls_section(main_container)
        self._create_progress_section(main_container)
        self._create_results_section(main_container)
        self._create_log_section(main_container)
    
    def _create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Label(header_frame, text="SAP RPA - Multi-Scenario Automation", font=("Arial", 18, "bold")).pack()
        ttk.Label(header_frame, text="MD04 → ERF Dashboard → KO03 Workflow", font=("Arial", 11), foreground="gray").pack()

    def _create_connection_section(self, parent):
        conn_frame = ttk.LabelFrame(parent, text="SAP Connection", padding="10")
        conn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        inner_frame = ttk.Frame(conn_frame)
        inner_frame.pack(fill=tk.X)
        self.connection_status_var = tk.StringVar(value="❌ Not Connected")
        ttk.Label(inner_frame, textvariable=self.connection_status_var, font=("Arial", 11, "bold")).pack(side=tk.LEFT)
        ttk.Button(inner_frame, text="Connect to SAP", command=self.connect_to_sap).pack(side=tk.RIGHT)

    def _create_input_section(self, parent):
        input_frame = ttk.LabelFrame(parent, text="Material Input", padding="10")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        single_frame = ttk.Frame(input_frame)
        single_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(single_frame, text="Single Material:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.single_material_var = tk.StringVar()
        ttk.Entry(single_frame, textvariable=self.single_material_var, width=30).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Label(input_frame, text="Multiple Materials (one per line):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.materials_text = scrolledtext.ScrolledText(input_frame, height=6, width=60, font=("Consolas", 9))
        self.materials_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X)
        ttk.Label(file_frame, text="Or load from Excel:").pack(side=tk.LEFT)
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50, state='readonly').pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=(5, 0))

    def _create_config_section(self, parent):
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        mrp_frame = ttk.Frame(config_frame)
        mrp_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(mrp_frame, text="MRP Area:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.mrp_area_var = tk.StringVar(value=self.config.DEFAULT_MRP_AREA)
        ttk.Entry(mrp_frame, textvariable=self.mrp_area_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        plant_frame = ttk.Frame(config_frame)
        plant_frame.pack(fill=tk.X, pady=(5, 5))
        ttk.Label(plant_frame, text="Plants to Search:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        plants_inner = ttk.Frame(plant_frame)
        plants_inner.pack(fill=tk.X, pady=(5, 0))
        self.plant_vars = {}
        for plant in self.config.AVAILABLE_PLANTS:
            var = tk.BooleanVar(value=True)
            self.plant_vars[plant] = var
            ttk.Checkbutton(plants_inner, text=f"Plant {plant}", variable=var).pack(side=tk.LEFT, padx=(0, 20))
        
        scenario_frame = ttk.Frame(config_frame)
        scenario_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(scenario_frame, text="Fallback Options:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        options_inner = ttk.Frame(scenario_frame)
        options_inner.pack(fill=tk.X, pady=(5, 0))
        self.enable_erf_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_inner, text="Enable ERF Dashboard Fallback", variable=self.enable_erf_var).pack(side=tk.LEFT, padx=(0, 20))
        self.enable_ko03_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_inner, text="Enable KO03 Fallback", variable=self.enable_ko03_var).pack(side=tk.LEFT)

    def _create_controls_section(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 10))
        self.start_btn = ttk.Button(control_frame, text="▶ Start Automation", command=self.start_automation)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.stop_btn = ttk.Button(control_frame, text="⏹ Stop", command=self.stop_automation, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        self.export_btn = ttk.Button(control_frame, text="💾 Export to Excel", command=self.export_results, state="disabled")
        self.export_btn.pack(side=tk.RIGHT)

    def _create_progress_section(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.progress_var = tk.StringVar(value="Ready to start...")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(anchor=tk.W)
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.current_material_var = tk.StringVar(value="")
        ttk.Label(progress_frame, textvariable=self.current_material_var, font=("Arial", 9, "bold"), foreground="blue").pack(anchor=tk.W, pady=(5, 0))

    def _create_results_section(self, parent):
        results_frame = ttk.LabelFrame(parent, text="Results", padding="10")
        results_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        parent.rowconfigure(6, weight=2)
        columns = ("Material", "Status", "Scenario", "Plant", "Description", "Time (s)")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=120 if col != "Description" else 300)
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

    def _create_log_section(self, parent):
        log_frame = ttk.LabelFrame(parent, text="System Log", padding="10")
        log_frame.grid(row=7, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        parent.rowconfigure(7, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=100, font=("Consolas", 9), state='disabled')
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def log_message(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update_idletasks()

    def connect_to_sap(self):
        self.log_message("Connecting to SAP...")
        if self.sap_connector.connect():
            session_info = self.sap_connector.get_session_info()
            status_text = f"✅ Connected: {session_info.get('system_name', '')} Client {session_info.get('client', '')} User {session_info.get('user', '')}"
            self.connection_status_var.set(status_text)
            self.log_message("Successfully connected to SAP", "SUCCESS")
            self.scenario_manager = ScenarioManager(self.sap_connector, self.excel_manager)
        else:
            self.connection_status_var.set("❌ Connection Failed")
            self.log_message("Failed to connect to SAP", "ERROR")
            messagebox.showerror("Connection Error", "Failed to connect to SAP. Please check SAP Logon and ensure scripting is enabled.")

    def browse_file(self):
        file_path = filedialog.askopenfilename(title="Select Excel file", filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file_path_var.set(file_path)
            self.log_message(f"Selected file: {file_path}")

    def get_materials_list(self) -> list:
        materials = []
        single = self.single_material_var.get().strip()
        if single: materials.append(single)
        text_content = self.materials_text.get("1.0", tk.END).strip()
        if text_content: materials.extend([m.strip() for m in text_content.split('\n') if m.strip()])
        file_path = self.file_path_var.get()
        if file_path: materials.extend([m['material_number'] for m in self.excel_manager.read_input_file(file_path)])
        unique_materials = list(dict.fromkeys(materials)) # Remove duplicates, preserve order
        return unique_materials

    def get_selected_plants(self) -> list:
        return [plant for plant, var in self.plant_vars.items() if var.get()]

    def start_automation(self):
        if not self.sap_connector.is_connected or self.scenario_manager is None:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
        
        self.materials_queue = self.get_materials_list()
        if not self.materials_queue:
            messagebox.showerror("Error", "Please enter at least one material number!")
            return
            
        selected_plants = self.get_selected_plants()
        if not selected_plants:
            messagebox.showerror("Error", "Please select at least one plant!")
            return

        if not messagebox.askyesno("Confirm Start", f"Process {len(self.materials_queue)} material(s)?"):
            return

        for item in self.results_tree.get_children(): self.results_tree.delete(item)
        self.current_results = []
        self.current_material_index = 0
        self.scenario_manager.reset_statistics()
        
        self.is_processing = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")
        
        self.log_message(f"Starting automation for {len(self.materials_queue)} materials...")
        self.process_next_material()

    def process_next_material(self):
        if not self.is_processing or self.current_material_index >= len(self.materials_queue):
            self.automation_finished()
            return

        material = self.materials_queue[self.current_material_index]
        total = len(self.materials_queue)
        self.update_progress(self.current_material_index + 1, total, material)

        result = self.scenario_manager.process_single_material(
            material_number=material,
            selected_plants=self.get_selected_plants(),
            mrp_area=self.mrp_area_var.get(),
            enable_erf_fallback=self.enable_erf_var.get(),
            enable_ko03_fallback=self.enable_ko03_var.get()
        )
        
        self.current_results.append(result)
        self.add_result_to_tree(result)
        
        self.current_material_index += 1
        self.root.after(100, self.process_next_material)

    def add_result_to_tree(self, result):
        status = "Success" if result.success else "Failed"
        scenario = result.scenario.value if result.scenario else "N/A"
        plant = result.plant_found or "N/A"
        desc = result.data.get('short_order_desc', result.data.get('mat_description', '')) if result.data else result.error_message
        time_taken = f"{result.processing_time:.2f}"
        
        tag = "success" if result.success else "failure"
        self.results_tree.tag_configure("success", background="#dff0d8")
        self.results_tree.tag_configure("failure", background="#f2dede")

        self.results_tree.insert("", "end", values=(result.material_number, status, scenario, plant, desc, time_taken), tags=(tag,))
        self.results_tree.yview_moveto(1)

    def update_progress(self, current, total, material):
        self.progress_bar.config(maximum=total, value=current)
        self.progress_var.set(f"Processing {current}/{total}...")
        self.current_material_var.set(f"Current: {material}")

    def automation_finished(self):
        self.is_processing = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.export_btn.config(state="normal")
        
        self.scenario_manager.log_statistics()
        stats = self.scenario_manager.get_statistics()
        self.log_message("Automation completed!", "SUCCESS")
        
        messagebox.showinfo("Automation Complete", f"Processing completed!\n\nTotal: {stats['total_processed']}\nSuccessful: {stats['total_processed'] - stats['failures']}\nFailed: {stats['failures']}")

    def stop_automation(self):
        if self.is_processing:
            self.is_processing = False
            self.log_message("Automation stopped by user.", "WARNING")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    def export_results(self):
        if not self.current_results:
            messagebox.showwarning("Warning", "No results to export!")
            return
        try:
            output_path = self.excel_manager.write_output_file(self.current_results)
            self.log_message(f"Results exported to: {output_path}", "SUCCESS")
            if messagebox.askyesno("Export Complete", "Results exported successfully!\n\nOpen file?"):
                import os
                os.startfile(output_path)
        except Exception as e:
            self.log_message(f"Export failed: {e}", "ERROR")
            messagebox.showerror("Export Error", f"Failed to export results:\n{e}")

    def run(self):
        self.log_message("SAP RPA Application Started")
        self.log_message("Please connect to SAP to begin...")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        if self.is_processing:
            if not messagebox.askyesno("Confirm Exit", "Automation is running. Are you sure you want to exit?"):
                return
        if self.sap_connector and self.sap_connector.is_connected:
            self.sap_connector.disconnect()
        self.root.destroy()