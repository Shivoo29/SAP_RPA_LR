"""
MD04 Transaction Handler
=========================
Handles MD04 transaction for material stock/requirements list.
Supports multiple plant searches.
"""

import time
import logging
from typing import Optional, Dict, List

from core.field_manager import FieldManager
from config import Config


class MD04Handler:
    """Handles MD04 transaction operations."""
    
    def __init__(self, sap_connector):
        """
        Initialize MD04 handler.
        
        Args:
            sap_connector: SAP connector instance
        """
        self.sap_connector = sap_connector
        self.session = sap_connector.session
        self.field_manager = FieldManager(self.session)
        self.logger = logging.getLogger(__name__)
        self.config = Config()
    
    def navigate_to_md04(self) -> bool:
        """
        Navigate to MD04 transaction.
        
        Returns:
            True if successful
        """
        return self.sap_connector.navigate_to_transaction('MD04')
    
    def ensure_individual_tab(self) -> bool:
        """
        Ensure the 'Individual access' tab is selected.
        
        Returns:
            True if successful
        """
        try:
            individual_tab = self.session.findById("wnd[0]/usr/tabsTAB300/tabpF01")
            if individual_tab:
                individual_tab.select()
                time.sleep(1)
                self.logger.debug("Individual access tab selected")
                return True
        except Exception as e:
            self.logger.warning(f"Could not select Individual tab: {e}")
        return False
    
    def enter_material(self, material_number: str) -> bool:
        """
        Enter material number in MD04.
        
        Args:
            material_number: Material/part number
            
        Returns:
            True if successful
        """
        self.logger.info(f"Entering material number: {material_number}")
        
        field_id = self.config.MD04_FIELDS['material_field']
        success = self.field_manager.fill_field(field_id, material_number)
        
        if not success:
            self.logger.error(f"Failed to enter material number: {material_number}")
        
        return success
    
    def set_plant(self, plant: str) -> bool:
        """
        Set plant number in MD04.
        
        Args:
            plant: Plant number (e.g., '1000', '2000')
            
        Returns:
            True if successful
        """
        self.logger.info(f"Setting plant: {plant}")
        
        field_id = self.config.MD04_FIELDS.get('plant_field', '')
        if not field_id:
            self.logger.warning("Plant field ID not configured, skipping")
            return True
        
        success = self.field_manager.fill_field(field_id, plant)
        
        if not success:
            self.logger.warning(f"Could not set plant: {plant}")
        
        return success
    
    def set_mrp_area(self, mrp_area: str) -> bool:
        """
        Set MRP area in MD04.
        
        Args:
            mrp_area: MRP area (default: '1000')
            
        Returns:
            True if successful
        """
        self.logger.info(f"Setting MRP area: {mrp_area}")
        
        field_id = self.config.MD04_FIELDS.get('mrp_area_field', '')
        if not field_id:
            self.logger.warning("MRP area field ID not configured")
            return True
        
        success = self.field_manager.fill_field(field_id, mrp_area)
        
        if not success:
            self.logger.warning(f"Could not set MRP area: {mrp_area}")
        
        return success
    
    def execute_query(self) -> bool:
        """
        Execute the MD04 query by pressing Enter.
        
        Returns:
            True if successful
        """
        self.logger.info("Executing MD04 query...")
        
        try:
            self.sap_connector.press_enter(wait_time=self.config.WAIT_TIME_AFTER_QUERY)
            
            # Check for errors
            error_msg = self.sap_connector.check_for_sap_errors()
            if error_msg:
                self.logger.warning(f"SAP error after query: {error_msg}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute query: {e}")
            return False
    
    def find_matres(self) -> Optional[object]:
        """
        Find MatRes element in the query results.
        
        Returns:
            MatRes element if found, None otherwise
        """
        return self.field_manager.find_matres_element()
    
    def open_matres_details(self, matres_element) -> bool:
        """
        Open MatRes details by double-clicking.
        
        Args:
            matres_element: MatRes element object
            
        Returns:
            True if successful
        """
        self.logger.info("Opening MatRes details...")
        
        try:
            # Focus on MatRes element
            matres_element.setFocus()
            time.sleep(0.5)
            
            # Press F7 to maximize/open details
            self.sap_connector.press_f7()
            
            # Wait for details to load
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to open MatRes details: {e}")
            return False
    
    def extract_data(self) -> Dict[str, str]:
        """
        Extract data from the current MD04 screen.
        
        Returns:
            Dictionary with extracted field values
        """
        self.logger.info("Extracting data from MD04...")
        
        return self.field_manager.extract_fields(self.config.EXTRACTION_FIELDS)
    
    def process_material_single_plant(
        self, 
        material_number: str, 
        plant: str,
        mrp_area: str = None
    ) -> Optional[Dict[str, str]]:
        """
        Process a material in a specific plant.
        
        Args:
            material_number: Material/part number
            plant: Plant number
            mrp_area: MRP area (optional)
            
        Returns:
            Extracted data if successful, None otherwise
        """
        self.logger.info(f"Processing {material_number} in plant {plant}")
        
        try:
            # Navigate to MD04
            if not self.navigate_to_md04():
                return None
            
            # Ensure correct tab
            self.ensure_individual_tab()
            
            # Enter material number
            if not self.enter_material(material_number):
                return None
            
            # Set plant
            if not self.set_plant(plant):
                return None
            
            # Set MRP area if provided
            if mrp_area:
                self.set_mrp_area(mrp_area)
            
            # Execute query
            if not self.execute_query():
                return None
            
            # Find MatRes
            matres_element = self.find_matres()
            if not matres_element:
                self.logger.warning(f"MatRes not found in plant {plant}")
                return None
            
            # Open MatRes details
            if not self.open_matres_details(matres_element):
                return None
            
            # Extract data
            data = self.extract_data()
            data['plant'] = plant
            data['material'] = material_number
            
            self.logger.info(f"Successfully extracted data from plant {plant}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error processing material in plant {plant}: {e}")
            return None
    
    def process_material_multiple_plants(
        self,
        material_number: str,
        plant_list: List[str] = None,
        mrp_area: str = None
    ) -> Optional[Dict[str, str]]:
        """
        Try to process material across multiple plants until successful.
        This method uses a state-aware back navigation pattern.
        
        Args:
            material_number: Material/part number
            plant_list: List of plants to try (default: all configured plants)
            mrp_area: MRP area (optional)
            
        Returns:
            Extracted data from first successful plant, None if all fail
        """
        if plant_list is None:
            plant_list = self.config.AVAILABLE_PLANTS
        
        self.logger.info(f"Trying multiple plants for {material_number}: {plant_list}")

        for plant in plant_list:
            self.logger.info(f"Attempting plant {plant}...")
            
            # Navigate to MD04 at the start of each loop to ensure a clean state
            if not self.navigate_to_md04():
                self.logger.error("Failed to navigate to MD04, aborting multi-plant search.")
                return None # Abort if we can't even get to the transaction

            try:
                # Ensure we are on the correct tab and fill details
                self.ensure_individual_tab()
                if not self.enter_material(material_number): continue
                if not self.set_plant(plant): continue
                if mrp_area:
                    self.set_mrp_area(mrp_area)
                
                # Execute query
                if not self.execute_query():
                    self.logger.warning(f"Query execution failed for plant {plant}")
                    continue

                # Find MatRes
                matres_element = self.find_matres()
                if matres_element:
                    # SUCCESS PATH
                    self.logger.info(f"✓ Successfully found MatRes in plant {plant}")
                    if self.open_matres_details(matres_element):
                        data = self.extract_data()
                        data['plant'] = plant
                        data['material'] = material_number
                        # No need to press F3, we will re-navigate for the next material
                        return data
                else:
                    # FAILURE PATH
                    self.logger.warning(f"✗ MatRes not found in plant {plant}, trying next...")
                    # No need to press F3, the loop will re-navigate on the next iteration

            except Exception as e:
                self.logger.error(f"An exception occurred while trying plant {plant}: {e}")
                # Continue to the next plant
                continue
        
        self.logger.error(f"MatRes not found in any of the specified plants for {material_number}")
        return None
    
    def process_next_material(self, material_number: str) -> Optional[Dict[str, str]]:
        """
        Process next material using the loop method (after first material).
        
        Args:
            material_number: Material/part number
            
        Returns:
            Extracted data if successful, None otherwise
        """
        self.logger.info(f"Processing next material: {material_number}")
        
        try:
            # Press F3 to go back
            self.sap_connector.press_f3()
            
            # Try multiple possible next part field locations
            possible_fields = [
                self.config.MD04_FIELDS['next_part_field'],
                self.config.MD04_FIELDS['material_field'],
            ]
            
            field_filled = False
            for field_id in possible_fields:
                try:
                    if self.field_manager.fill_field(field_id, material_number):
                        field_filled = True
                        break
                except:
                    continue
            
            if not field_filled:
                self.logger.error("Failed to fill next part field")
                return None
            
            # Execute query
            if not self.execute_query():
                return None
            
            # Find and open MatRes
            matres_element = self.find_matres()
            if not matres_element:
                return None
            
            if not self.open_matres_details(matres_element):
                return None
            
            # Extract data
            data = self.extract_data()
            data['material'] = material_number
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error processing next material: {e}")
            return None
