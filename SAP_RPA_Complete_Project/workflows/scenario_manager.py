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
from config import Config


class ScenarioManager:
    """Manages different automation scenarios and fallback logic."""
    
    def __init__(self, sap_connector, excel_manager):
        """
        Initialize scenario manager.
        
        Args:
            sap_connector: SAP connector instance
            excel_manager: Excel manager for data operations
        """
        self.sap_connector = sap_connector
        self.excel_manager = excel_manager
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        
        # Initialize handlers
        self.md04_handler = MD04Handler(self.sap_connector)
        self.ko03_handler = KO03Handler(self.sap_connector)
        self.erf_workflow = ERFWorkflow(self.sap_connector)
        
        # Statistics
        self.stats = self.get_initial_stats()
    
    def get_initial_stats(self) -> Dict:
        """Returns a clean dictionary for statistics."""
        return {
            'total_processed': 0,
            'scenario_1_success': 0,  # MatRes found
            'scenario_2_success': 0,  # ERF fallback
            'scenario_3_success': 0,  # KO03 fallback
            'failures': 0
        }

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = self.get_initial_stats()
        self.logger.info("Statistics reset")

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
            
            md04_data, stpord_plant = self.md04_handler.process_material_multiple_plants(
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
                
            # ===== SCENARIO 1.5: MatRes not found, but STPord was found → Extract RPM and go to ERF =====
            elif enable_erf_fallback and stpord_plant:
                self.logger.info(f"SCENARIO 1.5: MatRes not found, but STPord was found in plant {stpord_plant}. Extracting RPM number...")
                
                rpm_number = self.md04_handler.find_and_extract_rpm_number(
                    material_number=material_number,
                    plant=stpord_plant
                )

                if rpm_number:
                    self.logger.info(f"Found RPM number: {rpm_number}. Proceeding to ERF Dashboard...")
                    
                    erf_data = self.erf_workflow.execute_erf_workflow(
                        material_number=material_number, 
                        erf_search_term=rpm_number
                    )
                    
                    if erf_data:
                        self.logger.info("✓ SCENARIO 2 SUCCESS: Data extracted from ERF Dashboard!")
                        result.scenario = ScenarioType.ERF_DASHBOARD
                        result.success = True
                        result.data = erf_data
                        self.stats['scenario_2_success'] += 1
                        
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
                else:
                    self.logger.warning(f"STPord was found in {stpord_plant}, but failed to extract RPM number.")
            
            if not result.success:
                # ===== ALL SCENARIOS FAILED =====
                self.logger.error("✗ ALL SCENARIOS FAILED: Could not extract data")
                result.scenario = ScenarioType.ALL_FAILED
                result.success = False
                result.error_message = "MatRes not found in any plant, ERF fallback also failed"
                self.stats['failures'] += 1

        except Exception as e:
            self.logger.error(f"Error processing material {material_number}: {e}", exc_info=True)
            result.success = False
            result.error_message = str(e)
            self.stats['failures'] += 1
        
        finally:
            self.stats['total_processed'] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            if result.success:
                self.logger.info(f"✓ Success: {material_number} - Scenario: {result.scenario.value}")
            else:
                self.logger.error(f"✗ Failed: {material_number} - Error: {result.error_message}")

        return result

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
