"""
Main GUI Window
===============
Main graphical user interface for SAP RPA automation.
Refactored to use a root.after() loop for stable, single-threaded COM access.
Enhanced with modern styling and better progress indicators.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import logging
from pathlib import Path
from datetime import datetime
import time

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

        # Timer tracking
        self.start_time = None
        self.elapsed_time = 0

        # Live statistics
        self.live_success_count = 0
        self.live_failure_count = 0

        # Setup GUI
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the main GUI window."""
        self.root = tk.Tk()
        self.root.title("SAP RPA - Multi-Scenario Automation System")
        self.root.geometry("1400x950")

        # Apply modern theme
        style = ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')

        # Configure custom styles
        style.configure('Header.TLabel', font=('Arial', 18, 'bold'), foreground='#2c3e50')
        style.configure('Subheader.TLabel', font=('Arial', 11), foreground='#7f8c8d')
        style.configure('Success.TLabel', font=('Arial', 10, 'bold'), foreground='#27ae60')
        style.configure('Error.TLabel', font=('Arial', 10, 'bold'), foreground='#e74c3c')
        style.configure('Info.TLabel', font=('Arial', 10, 'bold'), foreground='#3498db')
        style.configure('Big.TButton', font=('Arial', 11, 'bold'), padding=10)

        # Futuristic progress bar style
        style.configure('Futuristic.Horizontal.TProgressbar',
                       troughcolor='#1a1a2e',
                       background='#0f3460',
                       darkcolor='#16213e',
                       lightcolor='#533483',
                       bordercolor='#0f3460',
                       thickness=25)

        try:
            self.root.state('zoomed')
        except tk.TclError:
            pass # Fails on some platforms

        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=3)
        main_container.columnconfigure(1, weight=1)

        # Left column - main controls
        left_frame = ttk.Frame(main_container)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)

        self._create_header(left_frame)
        self._create_connection_section(left_frame)
        self._create_input_section(left_frame)
        self._create_config_section(left_frame)
        self._create_controls_section(left_frame)
        self._create_progress_section(left_frame)
        self._create_results_section(left_frame)
        self._create_log_section(left_frame)

        # Right column - statistics panel
        self._create_statistics_panel(main_container)

        # Configure row weights for proper scaling
        for i in range(8):
            left_frame.rowconfigure(i, weight=0)
        left_frame.rowconfigure(6, weight=2)  # Results section
        left_frame.rowconfigure(7, weight=1)  # Log section
        main_container.rowconfigure(0, weight=1)
    
    def _create_header(self, parent):
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        ttk.Label(header_frame, text="SAP RPA - Multi-Scenario Automation", style='Header.TLabel').pack()
        ttk.Label(header_frame, text="MD04 → ERF Dashboard → KO03 Workflow", style='Subheader.TLabel').pack(pady=(2, 0))

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
        progress_frame = ttk.LabelFrame(parent, text="⚡ Progress Monitor", padding="15")
        progress_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        # Main progress info
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.StringVar(value="⏸ Ready to start...")
        ttk.Label(status_frame, textvariable=self.progress_var, font=("Arial", 11, "bold"), foreground="#0f3460").pack(side=tk.LEFT)

        self.elapsed_time_var = tk.StringVar(value="⏱ 00:00")
        ttk.Label(status_frame, textvariable=self.elapsed_time_var, font=("Arial", 11, "bold"), foreground="#16a085").pack(side=tk.RIGHT)

        # Futuristic progress bar container with border effect
        progress_container = tk.Frame(progress_frame, bg="#0f3460", highlightbackground="#533483", highlightthickness=2)
        progress_container.pack(fill=tk.X, pady=(0, 10))

        # Progress bar with futuristic style
        self.progress_bar = ttk.Progressbar(
            progress_container,
            mode='determinate',
            style='Futuristic.Horizontal.TProgressbar',
            length=400
        )
        self.progress_bar.pack(fill=tk.X, padx=2, pady=2)

        # Percentage display
        self.progress_percent_var = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_percent_var, font=("Arial", 10, "bold"), foreground="#533483").pack()

        # Current material and scenario
        detail_frame = ttk.Frame(progress_frame)
        detail_frame.pack(fill=tk.X, pady=(10, 0))

        self.current_material_var = tk.StringVar(value="")
        ttk.Label(detail_frame, textvariable=self.current_material_var, font=("Arial", 10, "bold"), foreground="#0f3460").pack(anchor=tk.W)

        self.current_scenario_var = tk.StringVar(value="")
        ttk.Label(detail_frame, textvariable=self.current_scenario_var, font=("Arial", 9), foreground="#533483").pack(anchor=tk.W, pady=(3, 0))

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

    def _create_statistics_panel(self, parent):
        """Create right-side statistics panel."""
        stats_frame = ttk.LabelFrame(parent, text="Live Statistics", padding="15")
        stats_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Title
        ttk.Label(stats_frame, text="Session Statistics", font=("Arial", 12, "bold"), foreground="#2c3e50").pack(pady=(0, 15))

        # Statistics display
        stats_container = ttk.Frame(stats_frame)
        stats_container.pack(fill=tk.BOTH, expand=True)

        # Total Processed
        self._create_stat_row(stats_container, "Total Processed:", "0", "total_processed", row=0, color="#34495e")

        # Success Count
        self._create_stat_row(stats_container, "✓ Successful:", "0", "success_count", row=1, color="#27ae60")

        # Failure Count
        self._create_stat_row(stats_container, "✗ Failed:", "0", "failure_count", row=2, color="#e74c3c")

        # Success Rate
        self._create_stat_row(stats_container, "Success Rate:", "0%", "success_rate", row=3, color="#3498db")

        # Separator
        ttk.Separator(stats_container, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        # Scenario breakdown
        ttk.Label(stats_container, text="Scenario Breakdown:", font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        self._create_stat_row(stats_container, "MD04 (MatRes/OrdRes/DepReq):", "0", "scenario_1", row=6, color="#16a085")
        self._create_stat_row(stats_container, "ERF Dashboard:", "0", "scenario_2", row=7, color="#2980b9")
        self._create_stat_row(stats_container, "ERF → KO03:", "0", "scenario_3", row=8, color="#8e44ad")

        # Separator
        ttk.Separator(stats_container, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        # Current session info
        ttk.Label(stats_container, text="Session Info:", font=("Arial", 10, "bold")).grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        self.session_start_var = tk.StringVar(value="Not started")
        ttk.Label(stats_container, text="Started:", font=("Arial", 9)).grid(row=11, column=0, sticky=tk.W)
        ttk.Label(stats_container, textvariable=self.session_start_var, font=("Arial", 9, "bold"), foreground="#7f8c8d").grid(row=11, column=1, sticky=tk.E)

        self.session_duration_var = tk.StringVar(value="00:00:00")
        ttk.Label(stats_container, text="Duration:", font=("Arial", 9)).grid(row=12, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(stats_container, textvariable=self.session_duration_var, font=("Arial", 9, "bold"), foreground="#3498db").grid(row=12, column=1, sticky=tk.E, pady=(5, 0))

        # Average time per material
        self.avg_time_var = tk.StringVar(value="0.0s")
        ttk.Label(stats_container, text="Avg. Time/Material:", font=("Arial", 9)).grid(row=13, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(stats_container, textvariable=self.avg_time_var, font=("Arial", 9, "bold"), foreground="#16a085").grid(row=13, column=1, sticky=tk.E, pady=(5, 0))

    def _create_stat_row(self, parent, label_text, initial_value, var_name, row, color="#000000"):
        """Helper to create a statistic row."""
        ttk.Label(parent, text=label_text, font=("Arial", 10)).grid(row=row, column=0, sticky=tk.W, pady=5)
        var = tk.StringVar(value=initial_value)
        setattr(self, f"{var_name}_var", var)
        ttk.Label(parent, textvariable=var, font=("Arial", 12, "bold"), foreground=color).grid(row=row, column=1, sticky=tk.E, pady=5)

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

        # Reset statistics
        self.live_success_count = 0
        self.live_failure_count = 0
        self.start_time = time.time()
        self.session_start_var.set(datetime.now().strftime("%H:%M:%S"))
        self._reset_statistics()

        self.is_processing = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")

        self.log_message(f"🚀 Starting automation for {len(self.materials_queue)} materials...")
        self.process_next_material()

        self._update_timer()

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

        # Update live statistics
        if result.success:
            self.live_success_count += 1
        else:
            self.live_failure_count += 1
        self._update_statistics()

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
        percentage = int((current / total) * 100) if total > 0 else 0
        self.progress_var.set(f"▶ Processing {current}/{total}")
        self.progress_percent_var.set(f"{percentage}%")
        self.current_material_var.set(f"📦 Current Material: {material}")
        self.current_scenario_var.set("🔄 Running MD04 → ERF Dashboard → KO03 workflow...")

    def automation_finished(self):
        self.is_processing = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.export_btn.config(state="normal")

        # Calculate statistics from results
        total = len(self.current_results)
        successful = sum(1 for r in self.current_results if r.success)
        failed = total - successful

        # Update progress to 100%
        self.progress_percent_var.set("100%")
        self.progress_var.set(f"✅ Completed {total}/{total}")

        self.log_message("✅ Automation completed!", "SUCCESS")

        messagebox.showinfo("Automation Complete", f"Processing completed!\n\nTotal: {total}\nSuccessful: {successful}\nFailed: {failed}")

    def stop_automation(self):
        if self.is_processing:
            self.is_processing = False
            self.log_message("⏹ Automation stopped by user.", "WARNING")
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

    def _update_timer(self):
        """Update the elapsed time display."""
        if self.is_processing and self.start_time:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)

            self.elapsed_time_var.set(f"⏱ {minutes:02d}:{seconds:02d}")
            self.session_duration_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Schedule next update
            self.root.after(1000, self._update_timer)

    def _reset_statistics(self):
        """Reset all statistics displays."""
        self.total_processed_var.set("0")
        self.success_count_var.set("0")
        self.failure_count_var.set("0")
        self.success_rate_var.set("0%")
        self.scenario_1_var.set("0")
        self.scenario_2_var.set("0")
        self.scenario_3_var.set("0")
        self.session_duration_var.set("00:00:00")
        self.avg_time_var.set("0.0s")

    def _update_statistics(self):
        """Update live statistics display."""
        # Calculate statistics from current_results
        total = len(self.current_results)
        successful = sum(1 for r in self.current_results if r.success)
        failures = total - successful

        # Count scenario breakdowns
        from data.data_models import ScenarioType
        scenario_1 = sum(1 for r in self.current_results if r.success and r.scenario == ScenarioType.MD04_MATRES_FOUND)
        scenario_2 = sum(1 for r in self.current_results if r.success and r.scenario == ScenarioType.ERF_DIRECT_EXTRACTION)
        scenario_3 = sum(1 for r in self.current_results if r.success and r.scenario == ScenarioType.ERF_WITH_KO03)

        self.total_processed_var.set(str(total))
        self.success_count_var.set(str(successful))
        self.failure_count_var.set(str(failures))

        if total > 0:
            success_rate = (successful / total) * 100
            self.success_rate_var.set(f"{success_rate:.1f}%")

            # Calculate average time
            if self.start_time:
                elapsed = time.time() - self.start_time
                avg_time = elapsed / total
                self.avg_time_var.set(f"{avg_time:.1f}s")
        else:
            self.success_rate_var.set("0%")
            self.avg_time_var.set("0.0s")

        # Scenario breakdown
        self.scenario_1_var.set(str(scenario_1))
        self.scenario_2_var.set(str(scenario_2))
        self.scenario_3_var.set(str(scenario_3))

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