"""
Scenario Manager
================
Orchestrates different automation scenarios and fallback mechanisms.

Scenarios:
1. MatRes found in any plant → Extract data
2. MatRes not found → Fallback to ERF Dashboard
3. ERF Dashboard → KO03 workflow
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from transactions.md04_handler import MD04Handler
from transactions.ko03_handler import KO03Handler
from workflows.erf_workflow import ERFWorkflow
from data.data_models import ProcessingResult, ScenarioType
from core.sap_connector import SAPConnector
from config import Config


class ScenarioManager:
    """Manages different automation scenarios and fallback logic."""
    
    def __init__(self, sap_connector, excel_manager):
        """
        Initialize scenario manager.
        
        Args:
            sap_connector: SAP connector instance (can be None if created later)
            excel_manager: Excel manager for data operations
        """
        self.sap_connector = sap_connector
        self.excel_manager = excel_manager
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Handlers are initialized later if sap_connector is None
        self.md04_handler = None
        self.ko03_handler = None
        self.erf_workflow = None
        
        if sap_connector:
            self._initialize_handlers()

        # Statistics
        self.stats = {
            'total_processed': 0,
            'scenario_1_success': 0,  # MatRes found
            'scenario_2_success': 0,  # ERF fallback
            'scenario_3_success': 0,  # KO03 fallback
            'failures': 0
        }
    
    def _initialize_handlers(self):
        """Initializes all handlers with the current SAP connector."""
        if not self.sap_connector:
            self.logger.error("Cannot initialize handlers without a SAP connector.")
            return
        self.md04_handler = MD04Handler(self.sap_connector)
        self.ko03_handler = KO03Handler(self.sap_connector)
        self.erf_workflow = ERFWorkflow(self.sap_connector)
        self.logger.info("All handlers initialized.")

    def process_single_material(
        self,
        material_number: str,
        selected_plants: List[str] = None,
        mrp_area: str = None,
        enable_erf_fallback: bool = True,
        enable_ko03_fallback: bool = True
    ) -> ProcessingResult:
        """
        Process a single material through all scenarios.
        
        Args:
            material_number: Material/part number
            selected_plants: List of plants to search (None = all)
            mrp_area: MRP area
            enable_erf_fallback: Enable ERF dashboard fallback
            enable_ko03_fallback: Enable KO03 fallback
            
        Returns:
            ProcessingResult object with extracted data
        """
        self.logger.info("="*60)
        self.logger.info(f"Processing material: {material_number}")
        self.logger.info("="*60)
        
        start_time = datetime.now()
        result = ProcessingResult(material_number=material_number)
        
        try:
            # ===== SCENARIO 1: Try MD04 with multiple plants =====
            self.logger.info("SCENARIO 1: Attempting MD04 with multiple plants...")
            
            plant_list = selected_plants if selected_plants else self.config.AVAILABLE_PLANTS
            
            md04_data = self.md04_handler.process_material_multiple_plants(
                material_number=material_number,
                plant_list=plant_list,
                mrp_area=mrp_area
            )
            
            if md04_data:
                # Success! MatRes found
                self.logger.info("✓ SCENARIO 1 SUCCESS: MatRes found!")
                result.scenario = ScenarioType.MD04_MATRES_FOUND
                result.success = True
                result.data = md04_data
                result.plant_found = md04_data.get('plant', '')
                self.stats['scenario_1_success'] += 1
                
                processing_time = (datetime.now() - start_time).total_seconds()
                result.processing_time = processing_time
                
                return result
            
            # ===== SCENARIO 2: MatRes not found → ERF Dashboard =====
            if enable_erf_fallback:
                self.logger.info("SCENARIO 2: MatRes not found, trying ERF Dashboard...")
                
                erf_data = self.erf_workflow.execute_erf_workflow(material_number)
                
                if erf_data:
                    self.logger.info("✓ SCENARIO 2 SUCCESS: Data extracted from ERF Dashboard!")
                    result.scenario = ScenarioType.ERF_DASHBOARD
                    result.success = True
                    result.data = erf_data
                    self.stats['scenario_2_success'] += 1
                    
                    processing_time = (datetime.now() - start_time).total_seconds()
                    result.processing_time = processing_time
                    
                    # Check if we need to go to KO03
                    order_number = erf_data.get('order_number', '')
                    if order_number and enable_ko03_fallback:
                        # ===== SCENARIO 3: ERF → KO03 =====
                        self.logger.info("SCENARIO 3: Going to KO03 with order number...")
                        
                        ko03_data = self.ko03_handler.process_order(order_number)
                        
                        if ko03_data:
                            self.logger.info("✓ SCENARIO 3 SUCCESS: Data extracted from KO03!")
                            result.scenario = ScenarioType.ERF_TO_KO03
                            result.data.update(ko03_data)
                            self.stats['scenario_3_success'] += 1
                    
                    return result
            
            # ===== ALL SCENARIOS FAILED =====
            self.logger.error("✗ ALL SCENARIOS FAILED: Could not extract data")
            result.scenario = ScenarioType.ALL_FAILED
            result.success = False
            result.error_message = "MatRes not found in any plant, ERF fallback also failed"
            self.stats['failures'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing material {material_number}: {e}", exc_info=True)
            result.success = False
            result.error_message = str(e)
            self.stats['failures'] += 1
            
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            return result
        finally:
            self.stats['total_processed'] += 1
    
    def process_batch(
        self,
        material_list: List[str],
        selected_plants: List[str] = None,
        mrp_area: str = None,
        enable_erf_fallback: bool = True,
        enable_ko03_fallback: bool = True,
        progress_callback=None
    ) -> List[ProcessingResult]:
        """
        Process multiple materials in batch. This method is thread-safe.
        
        Args:
            material_list: List of material numbers
            selected_plants: List of plants to search
            mrp_area: MRP area
            enable_erf_fallback: Enable ERF dashboard fallback
            enable_ko03_fallback: Enable KO03 fallback
            progress_callback: Callback function for progress updates
            
        Returns:
            List of ProcessingResult objects
        """
        # Thread-local SAP connection handling
        is_local_connector = False
        if self.sap_connector is None:
            self.logger.info("Creating a new thread-local SAP connection...")
            self.sap_connector = SAPConnector()
            if not self.sap_connector.connect():
                self.logger.error("Failed to create thread-local SAP connection. Aborting batch.")
                # Optionally, communicate this failure back to the GUI
                return []
            self._initialize_handlers()
            is_local_connector = True

        try:
            self.logger.info(f"Starting batch processing of {len(material_list)} materials")
            
            results = []
            total = len(material_list)
            
            for idx, material in enumerate(material_list, 1):
                self.logger.info(f"Processing {idx}/{total}: {material}")
                
                # Update progress
                if progress_callback:
                    progress_callback(idx, total, material)
                
                # Process material
                result = self.process_single_material(
                    material_number=material,
                    selected_plants=selected_plants,
                    mrp_area=mrp_area,
                    enable_erf_fallback=enable_erf_fallback,
                    enable_ko03_fallback=enable_ko03_fallback
                )
                
                results.append(result)
                
                # Log result
                if result.success:
                    self.logger.info(f"✓ Success: {material} - Scenario: {result.scenario.value}")
                else:
                    self.logger.error(f"✗ Failed: {material} - Error: {result.error_message}")
            
            # Log final statistics
            self.log_statistics()
            
            return results
        finally:
            # Clean up the thread-local connection if it was created here
            if is_local_connector and self.sap_connector:
                self.sap_connector.disconnect()
                self.sap_connector = None # Important to reset for next run
                self.logger.info("Thread-local SAP connection closed.")
    
    def log_statistics(self):
        """Log processing statistics."""
        self.logger.info("="*60)
        self.logger.info("PROCESSING STATISTICS")
        self.logger.info("="*60)
        self.logger.info(f"Total Processed: {self.stats['total_processed']}")
        self.logger.info(f"Scenario 1 (MatRes Found): {self.stats['scenario_1_success']}")
        self.logger.info(f"Scenario 2 (ERF Dashboard): {self.stats['scenario_2_success']}")
        self.logger.info(f"Scenario 3 (ERF→KO03): {self.stats['scenario_3_success']}")
        self.logger.info(f"Failures: {self.stats['failures']}")
        
        if self.stats['total_processed'] > 0:
            success_rate = ((self.stats['total_processed'] - self.stats['failures']) / 
                          self.stats['total_processed']) * 100
            self.logger.info(f"Success Rate: {success_rate:.1f}%")
        
        self.logger.info("="*60)
    
    def get_statistics(self) -> Dict:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = self.stats.copy()
        
        if stats['total_processed'] > 0:
            stats['success_rate'] = ((stats['total_processed'] - stats['failures']) / 
                                   stats['total_processed']) * 100
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'total_processed': 0,
            'scenario_1_success': 0,
            'scenario_2_success': 0,
            'scenario_3_success': 0,
            'failures': 0
        }
        self.logger.info("Statistics reset")
