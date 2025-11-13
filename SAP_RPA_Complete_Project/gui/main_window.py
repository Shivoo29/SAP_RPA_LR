"""
Main GUI Window
===============
Main graphical user interface for SAP RPA automation.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
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
        self.scenario_manager = ScenarioManager(None, self.excel_manager) # Pass None for the connector
        
        # State
        self.is_processing = False
        self.current_results = []
        
        # Setup GUI
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the main GUI window."""
        self.root = tk.Tk()
        self.root.title("SAP RPA - Multi-Scenario Automation System")
        self.root.geometry("1200x900")
        
        # Try to maximize
        try:
            self.root.state('zoomed')
        except:
            pass
        
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(0, weight=1)
        
        # Header
        self._create_header(main_container)
        
        # SAP Connection
        self._create_connection_section(main_container)
        
        # Input Section
        self._create_input_section(main_container)
        
        # Configuration
        self._create_config_section(main_container)
        
        # Controls
        self._create_controls_section(main_container)
        
        # Progress
        self._create_progress_section(main_container)
        
        # Results
        self._create_results_section(main_container)
        
        # Log
        self._create_log_section(main_container)
    
    def _create_header(self, parent):
        """Create header section."""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame,
            text="SAP RPA - Multi-Scenario Automation",
            font=("Arial", 18, "bold")
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            header_frame,
            text="MD04 → ERF Dashboard → KO03 Workflow",
            font=("Arial", 11),
            foreground="gray"
        )
        subtitle_label.pack()
    
    def _create_connection_section(self, parent):
        """Create SAP connection section."""
        conn_frame = ttk.LabelFrame(parent, text="SAP Connection", padding="10")
        conn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        inner_frame = ttk.Frame(conn_frame)
        inner_frame.pack(fill=tk.X)
        
        self.connection_status_var = tk.StringVar(value="❌ Not Connected")
        status_label = ttk.Label(
            inner_frame,
            textvariable=self.connection_status_var,
            font=("Arial", 11, "bold")
        )
        status_label.pack(side=tk.LEFT)
        
        ttk.Button(
            inner_frame,
            text="Connect to SAP",
            command=self.connect_to_sap
        ).pack(side=tk.RIGHT)
    
    def _create_input_section(self, parent):
        """Create input section."""
        input_frame = ttk.LabelFrame(parent, text="Material Input", padding="10")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Single material
        single_frame = ttk.Frame(input_frame)
        single_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(single_frame, text="Single Material:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.single_material_var = tk.StringVar()
        ttk.Entry(single_frame, textvariable=self.single_material_var, width=30).pack(side=tk.LEFT, padx=(10, 0))
        
        # Multiple materials
        ttk.Label(input_frame, text="Multiple Materials (one per line):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.materials_text = scrolledtext.ScrolledText(input_frame, height=6, width=60, font=("Consolas", 9))
        self.materials_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        # File input
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.X)
        
        ttk.Label(file_frame, text="Or load from Excel:").pack(side=tk.LEFT)
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50, state='readonly').pack(side=tk.LEFT, padx=(10, 0))
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_config_section(self, parent):
        """Create configuration section."""
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding="10")
        config_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # MRP Area
        mrp_frame = ttk.Frame(config_frame)
        mrp_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(mrp_frame, text="MRP Area:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.mrp_area_var = tk.StringVar(value=self.config.DEFAULT_MRP_AREA)
        ttk.Entry(mrp_frame, textvariable=self.mrp_area_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Plant Selection
        plant_frame = ttk.Frame(config_frame)
        plant_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(plant_frame, text="Plants to Search:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Checkboxes for each plant
        self.plant_vars = {}
        plants_inner = ttk.Frame(plant_frame)
        plants_inner.pack(fill=tk.X, pady=(5, 0))
        
        for plant in self.config.AVAILABLE_PLANTS:
            var = tk.BooleanVar(value=True)  # All plants selected by default
            self.plant_vars[plant] = var
            ttk.Checkbutton(
                plants_inner,
                text=f"Plant {plant}",
                variable=var
            ).pack(side=tk.LEFT, padx=(0, 20))
        
        # Scenario Options
        scenario_frame = ttk.Frame(config_frame)
        scenario_frame.pack(fill=tk.X)
        
        ttk.Label(scenario_frame, text="Fallback Options:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        options_inner = ttk.Frame(scenario_frame)
        options_inner.pack(fill=tk.X, pady=(5, 0))
        
        self.enable_erf_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_inner,
            text="Enable ERF Dashboard Fallback",
            variable=self.enable_erf_var
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        self.enable_ko03_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_inner,
            text="Enable KO03 Fallback",
            variable=self.enable_ko03_var
        ).pack(side=tk.LEFT)
    
    def _create_controls_section(self, parent):
        """Create control buttons."""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_btn = ttk.Button(
            control_frame,
            text="▶ Start Automation",
            command=self.start_automation
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="⏹ Stop",
            command=self.stop_automation,
            state="disabled"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_btn = ttk.Button(
            control_frame,
            text="💾 Export to Excel",
            command=self.export_results,
            state="disabled"
        )
        self.export_btn.pack(side=tk.RIGHT)
    
    def _create_progress_section(self, parent):
        """Create progress section."""
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_var = tk.StringVar(value="Ready to start...")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        self.current_material_var = tk.StringVar(value="")
        ttk.Label(
            progress_frame,
            textvariable=self.current_material_var,
            font=("Arial", 9, "bold"),
            foreground="blue"
        ).pack(anchor=tk.W, pady=(5, 0))
    
    def _create_results_section(self, parent):
        """Create results section."""
        results_frame = ttk.LabelFrame(parent, text="Results", padding="10")
        results_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        parent.rowconfigure(6, weight=2)
        
        # Results tree
        columns = ("Material", "Status", "Scenario", "Plant", "Description", "Time (s)")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=8)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "Description":
                self.results_tree.column(col, width=300)
            elif col == "Material":
                self.results_tree.column(col, width=150)
            else:
                self.results_tree.column(col, width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def _create_log_section(self, parent):
        """Create log section."""
        log_frame = ttk.LabelFrame(parent, text="System Log", padding="10")
        log_frame.grid(row=7, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        parent.rowconfigure(7, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=100, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add message to GUI log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def connect_to_sap(self):
        """Connect to SAP."""
        self.log_message("Connecting to SAP...")
        
        if self.sap_connector.connect():
            session_info = self.sap_connector.get_session_info()
            self.connection_status_var.set(
                f"✅ Connected: {session_info.get('system_name', '')} "
                f"Client {session_info.get('client', '')} "
                f"User {session_info.get('user', '')}"
            )
            self.log_message("Successfully connected to SAP", "SUCCESS")
            
        else:
            self.connection_status_var.set("❌ Connection Failed")
            self.log_message("Failed to connect to SAP", "ERROR")
            messagebox.showerror("Connection Error", "Failed to connect to SAP. Please check SAP Logon.")
    
    def browse_file(self):
        """Browse for Excel input file."""
        file_path = filedialog.askopenfilename(
            title="Select Excel file with material numbers",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
            self.log_message(f"Selected file: {file_path}")
    
    def get_materials_list(self) -> list:
        """Get list of materials from input."""
        materials = []
        
        # Single material
        single = self.single_material_var.get().strip()
        if single:
            materials.append(single)
        
        # Multiple materials from text area
        text_content = self.materials_text.get("1.0", tk.END).strip()
        if text_content:
            text_materials = [m.strip() for m in text_content.split('\n') if m.strip()]
            materials.extend(text_materials)
        
        # Materials from Excel file
        file_path = self.file_path_var.get()
        if file_path:
            file_materials_data = self.excel_manager.read_input_file(file_path)
            file_materials = [m['material_number'] for m in file_materials_data]
            materials.extend(file_materials)
        
        # Remove duplicates while preserving order
        unique_materials = []
        seen = set()
        for material in materials:
            if material not in seen:
                unique_materials.append(material)
                seen.add(material)
        
        return unique_materials
    
    def get_selected_plants(self) -> list:
        """Get list of selected plants."""
        return [plant for plant, var in self.plant_vars.items() if var.get()]
    
    def start_automation(self):
        """Start automation process."""
        # Validate connection
        if not self.sap_connector.is_connected:
            messagebox.showerror("Error", "Please connect to SAP first!")
            return
        
        # Get materials
        materials = self.get_materials_list()
        if not materials:
            messagebox.showerror("Error", "Please enter at least one material number!")
            return
        
        # Get selected plants
        selected_plants = self.get_selected_plants()
        if not selected_plants:
            messagebox.showerror("Error", "Please select at least one plant!")
            return
        
        # Confirm start
        result = messagebox.askyesno(
            "Confirm Start",
            f"Process {len(materials)} material(s) with:\n"
            f"- Plants: {', '.join(selected_plants)}\n"
            f"- ERF Fallback: {'Enabled' if self.enable_erf_var.get() else 'Disabled'}\n"
            f"- KO03 Fallback: {'Enabled' if self.enable_ko03_var.get() else 'Disabled'}\n\n"
            f"Continue?"
        )
        
        if not result:
            return
        
        # Clear previous results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.current_results = []
        
        # Update UI
        self.is_processing = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.export_btn.config(state="disabled")
        
        # Start processing in separate thread
        threading.Thread(
            target=self.run_automation,
            args=(materials, selected_plants),
            daemon=True
        ).start()
    
    def run_automation(self, materials: list, selected_plants: list):
        """Run automation in separate thread."""
        self.log_message(f"Starting automation for {len(materials)} materials...")
        
        def progress_callback(current, total, material):
            self.root.after(0, lambda: self.update_progress(current, total, material))
        
        try:
            results = self.scenario_manager.process_batch(
                material_list=materials,
                selected_plants=selected_plants,
                mrp_area=self.mrp_area_var.get(),
                enable_erf_fallback=self.enable_erf_var.get(),
                enable_ko03_fallback=self.enable_ko03_var.get(),
                progress_callback=progress_callback
            )
            
            self.current_results = results
            self.root.after(0, lambda: self.automation_finished(True))
            
        except Exception as e:
            self.logger.error(f"Automation error: {e}", exc_info=True)
            self.root.after(0, lambda: self.automation_finished(False))
    
    def update_progress(self, current, total, material):
        """Update progress display."""
        self.progress_bar.config(maximum=total, value=current)
        self.progress_var.set(f"Processing {current}/{total}...")
        self.current_material_var.set(f"Current: {material}")
    
    def automation_finished(self, success):
        """Called when automation finishes."""
        self.is_processing = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.export_btn.config(state="normal")
        
        if success:
            stats = self.scenario_manager.get_statistics()
            self.log_message("Automation completed successfully!", "SUCCESS")
            self.log_message(f"Statistics: {stats['total_processed']} processed, "
                           f"{stats['total_processed'] - stats['failures']} successful, "
                           f"{stats['failures']} failed")
            
            messagebox.showinfo(
                "Automation Complete",
                f"Processing completed!\n\n"
                f"Total: {stats['total_processed']}\n"
                f"Successful: {stats['total_processed'] - stats['failures']}\n"
                f"Failed: {stats['failures']}\n"
                f"Success Rate: {stats.get('success_rate', 0):.1f}%"
            )
        else:
            self.log_message("Automation failed!", "ERROR")
            messagebox.showerror("Error", "Automation failed. Check log for details.")
    
    def stop_automation(self):
        """Stop automation process."""
        self.is_processing = False
        self.log_message("Automation stopped by user", "WARNING")
    
    def export_results(self):
        """Export results to Excel."""
        if not self.current_results:
            messagebox.showwarning("Warning", "No results to export!")
            return
        
        try:
            output_path = self.excel_manager.write_output_file(self.current_results)
            self.log_message(f"Results exported to: {output_path}", "SUCCESS")
            
            # Ask to open file
            result = messagebox.askyesno(
                "Export Complete",
                f"Results exported successfully!\n\nOpen file?"
            )
            
            if result:
                import os
                os.startfile(output_path)
                
        except Exception as e:
            self.log_message(f"Export failed: {e}", "ERROR")
            messagebox.showerror("Export Error", f"Failed to export results:\n{e}")
    
    def run(self):
        """Run the application."""
        self.log_message("SAP RPA Application Started")
        self.log_message("Please connect to SAP to begin...")
        self.root.mainloop()
        
        # Cleanup on exit
        if self.sap_connector.is_connected:
            self.sap_connector.disconnect()
