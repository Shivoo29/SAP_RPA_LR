"""
MD04 Transaction Handler
=========================
Handles MD04 transaction for material stock/requirements list.
Supports multiple plant searches.
"""

import time
import logging
import re
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
    ) -> (Optional[Dict[str, str]], Optional[str]):
        """
        Try to process material across multiple plants with a robust navigation loop.
        - Priority 1: Find MatRes and return its data immediately.
        - Priority 2: If no MatRes is found, note the first plant where 'STPord' is found.
        
        Args:
            material_number: Material/part number
            plant_list: List of plants to try (default: all configured plants)
            mrp_area: MRP area (optional)
            
        Returns:
            A tuple containing:
            - Extracted data from first successful plant (if MatRes found).
            - The first plant where 'STPord' was found (if no MatRes was found).
        """
        if plant_list is None:
            plant_list = self.config.AVAILABLE_PLANTS
        
        self.logger.info(f"Starting robust multi-plant search for {material_number}: {plant_list}")
        first_stpord_plant: Optional[str] = None

        for i, plant in enumerate(plant_list):
            self.logger.info(f"Attempting plant {plant} ({i+1}/{len(plant_list)})...")
            
            try:
                # Navigation is now INSIDE the loop for maximum stability
                if not self.navigate_to_md04():
                    self.logger.error(f"Navigation to MD04 failed for plant {plant}. Skipping.")
                    continue

                # Enter details for the current plant
                if not self.ensure_individual_tab(): continue
                if not self.enter_material(material_number): continue
                if not self.set_plant(plant): continue
                self.set_mrp_area(plant) # Use plant as MRP area
                
                if not self.execute_query():
                    self.logger.warning(f"Query execution failed for plant {plant}")
                    continue

                # PRIORITY 1: Check for MatRes
                matres_element = self.find_matres()
                if matres_element:
                    self.logger.info(f"✓ PRIORITY 1: Successfully found MatRes in plant {plant}")
                    if self.open_matres_details(matres_element):
                        data = self.extract_data()
                        data['plant'] = plant
                        data['material'] = material_number
                        return data, None  # MatRes found, workflow is complete for this material

                # PRIORITY 2: If no MatRes, check for STPord across the entire table
                if first_stpord_plant is None:
                    try:
                        table_id = self.config.get_field_id('MD04_RPM', 'item_list_table')
                        table = self.session.findById(table_id)
                        
                        # Search through all rows and columns for 'STPord'
                        for row_idx in range(table.rows.count):
                            for col_idx in range(table.columns.count):
                                try:
                                    cell_text = table.getCell(row_idx, col_idx).text.strip()
                                    if cell_text == "STPord":
                                        self.logger.info(f"✓ PRIORITY 2: Noted 'STPord' found in plant {plant} at row {row_idx}, col {col_idx}.")
                                        first_stpord_plant = plant
                                        break  # Found in this row, break column loop
                                except Exception:
                                    # This cell might not have a 'text' property, continue
                                    continue
                            if first_stpord_plant:
                                break  # Found in the table, break row loop
                    except Exception as e:
                        self.logger.warning(f"Could not scan for STPord in plant {plant}: {e}")

            except Exception as e:
                self.logger.error(f"An unexpected exception occurred while processing plant {plant}: {e}", exc_info=True)
                continue # Move to the next plant
        
        if first_stpord_plant:
            self.logger.info(f"Finished all plants. No MatRes found, but returning first plant with 'STPord': {first_stpord_plant}.")
        else:
            self.logger.error(f"Finished all plants. MatRes and STPord not found in any specified plant for {material_number}")

        return None, first_stpord_plant

    def find_and_extract_rpm_number(self, material_number: str, plant: str) -> Optional[str]:
        """
        Finds the STPord row in MD04 for a *specific plant* and extracts the RPM number.
        This is the fallback when MatRes is not found.

        Args:
            material_number: The material number to search for.
            plant: The specific plant to search in.

        Returns:
            The extracted RPM number (digits only) if found, otherwise None.
        """
        self.logger.info(f"Attempting to find RPM number for material {material_number} in specific plant {plant}")
        try:
            # 1. Navigate to MD04 and execute query for the specific plant
            if not self.navigate_to_md04(): return None
            if not self.ensure_individual_tab(): return None
            if not self.enter_material(material_number): return None
            if not self.set_plant(plant): return None
            if not self.set_mrp_area(plant): return None # Use plant as MRP area as per previous logic
            if not self.execute_query(): return None

            # 2. Find the 'STPord' row in the results table
            table_id = self.config.get_field_id('MD04_RPM', 'item_list_table')
            table = self.session.findById(table_id)
            
            stpord_row_index = -1
            for i in range(table.rows.count):
                for j in range(table.columns.count):
                    try:
                        element_text = table.getCell(i, j).text.strip()
                        if element_text == "STPord":
                            stpord_row_index = i
                            self.logger.info(f"Found 'STPord' at row {i}")
                            break
                    except:
                        continue
                if stpord_row_index != -1:
                    break
            
            if stpord_row_index == -1:
                self.logger.warning(f"'STPord' row not found in plant {plant}.")
                return None

            # 3. Select the row and press "Display" (VKey 2)
            # We need to select the cell we found, not just the row.
            stpord_cell = table.getCell(stpord_row_index, 0) # Select the first cell of the found row
            stpord_cell.setFocus()
            self.session.findById("wnd[0]").sendVKey(2)
            time.sleep(self.config.WAIT_TIME_AFTER_ACTION)

            # 4. Press "Display element" button in the new window/view
            try:
                display_button_id = self.config.get_field_id('MD04_RPM', 'item_display_button')
                self.session.findById(display_button_id).press()
                time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
                self.logger.info("Pressed 'Display element' button.")
            except Exception as e:
                self.logger.warning(f"Could not press 'Display element' button (this might be optional): {e}")

            # 5. Press "Expand items" button
            try:
                expand_button_id = "wnd[0]/usr/subSUB0:SAPLMEGUI:0015/subSUB2:SAPLMEVIEWS:1100/subSUB1:SAPLMEVIEWS:4001/btnDYN_4000-BUTTON"
                self.session.findById(expand_button_id).press()
                time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
                self.logger.info("Pressed 'Expand items' button.")
            except Exception as e:
                self.logger.error(f"Failed to press 'Expand items' button: {e}", exc_info=True)
                return None

            # 6. Extract the RPM number from the table
            rpm_field_id = self.config.get_field_id('MD04_RPM', 'rpm_number_field')
            rpm_full_text = self.field_manager.get_field_value(rpm_field_id)
            
            if not rpm_full_text:
                self.logger.error("Could not read RPM number field.")
                return None
            
            self.logger.info(f"Found raw RPM text: '{rpm_full_text}'")

            # 7. Parse the number from the text
            match = re.search(r'\d+', rpm_full_text)
            if match:
                rpm_number = match.group(0)
                self.logger.info(f"✓ Successfully extracted RPM number: {rpm_number}")
                return rpm_number
            else:
                self.logger.error(f"Could not parse digits from RPM text: '{rpm_full_text}'")
                return None

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during RPM number extraction in plant {plant}: {e}", exc_info=True)
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
