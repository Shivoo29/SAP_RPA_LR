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
        Uses shared SAP connector method to avoid duplication.

        Returns:
            True if successful
        """
        self.logger.info("Executing MD04 query...")
        return self.sap_connector.execute_sap_query(wait_time=self.config.WAIT_TIME_AFTER_QUERY)
    
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
    
    def process_material_multiple_plants_optimized(
        self,
        material_number: str,
        plant_list: List[str] = None,
        mrp_area: str = None
    ) -> Optional[Dict[str, str]]:
        """
        OPTIMIZED multi-plant search with smart early termination and 3-tier priority system.

        Logic:
        1. Check plants one by one
        2. Single table scan looks for MatRes, OrdRes, and STPord
        3. Priority handling:
           - PRIORITY 1: MatRes found → STOP immediately, extract data, return
           - PRIORITY 2: OrdRes found → STOP immediately, extract data, return
           - PRIORITY 3: STPord found → extract RPM immediately, return with RPM data
        4. No wasted time checking remaining plants once we have what we need

        Args:
            material_number: Material/part number
            plant_list: List of plants to try (default: all configured plants)
            mrp_area: MRP area (optional)

        Returns:
            Dictionary with extracted data and metadata, or None if all plants failed
        """
        if plant_list is None:
            plant_list = self.config.AVAILABLE_PLANTS

        self.logger.info(f"🚀 OPTIMIZED multi-plant search for {material_number}: {plant_list}")

        for i, plant in enumerate(plant_list):
            self.logger.info(f"Checking plant {plant} ({i+1}/{len(plant_list)})...")

            try:
                # Navigate to MD04
                if not self.navigate_to_md04():
                    self.logger.error(f"Navigation to MD04 failed for plant {plant}. Skipping.")
                    continue
                time.sleep(2)

                # Enter material and plant details
                if not self.ensure_individual_tab(): continue
                if not self.enter_material(material_number): continue
                if not self.set_plant(plant): continue
                if mrp_area:
                    self.set_mrp_area(mrp_area)
                else:
                    self.set_mrp_area(plant)

                if not self.execute_query():
                    self.logger.warning(f"Query execution failed for plant {plant}")
                    continue

                # SINGLE TABLE SCAN for both MatRes and STPord
                scan_result = self.field_manager.scan_md04_table_for_elements()

                # PRIORITY 1: MatRes found - STOP IMMEDIATELY
                if scan_result['matres_element']:
                    self.logger.info(f"✓✓✓ MatRes found in plant {plant} - STOPPING search here!")
                    if self.open_matres_details(scan_result['matres_element']):
                        data = self.extract_data()
                        data['plant'] = plant
                        data['material'] = material_number
                        data['source'] = 'MatRes'
                        data['plants_checked'] = i + 1
                        return data
                    else:
                        self.logger.warning(f"Failed to open MatRes details in plant {plant}")
                        continue

                # PRIORITY 2: OrdRes found and no MatRes - Extract data immediately
                elif scan_result['has_ordres']:
                    self.logger.info(f"✓✓ OrdRes found in plant {plant} - Extracting data immediately!")
                    ordres_data = self.extract_ordres_from_current_screen(
                        material_number,
                        plant,
                        scan_result['ordres_row_index']
                    )

                    if ordres_data:
                        self.logger.info(f"✓ OrdRes data extracted - STOPPING search here!")
                        ordres_data['plants_checked'] = i + 1
                        return ordres_data
                    else:
                        self.logger.warning(f"OrdRes found but data extraction failed in plant {plant}")
                        continue

                # PRIORITY 3: STPord found (no MatRes or OrdRes) - Extract RPM immediately
                elif scan_result['has_stpord']:
                    self.logger.info(f"✓ STPord found in plant {plant} - Extracting RPM immediately!")
                    rpm_number = self.extract_rpm_from_current_screen(
                        material_number,
                        plant,
                        scan_result['stpord_row_index']
                    )

                    if rpm_number:
                        self.logger.info(f"✓ RPM extracted: {rpm_number} - STOPPING search here!")
                        return {
                            'material': material_number,
                            'plant': plant,
                            'rpm_number': rpm_number,
                            'source': 'STPord',
                            'plants_checked': i + 1,
                            'needs_erf_lookup': True
                        }
                    else:
                        self.logger.warning(f"STPord found but RPM extraction failed in plant {plant}")
                        continue

                else:
                    self.logger.info(f"No MatRes, OrdRes, or STPord found in plant {plant}")

            except Exception as e:
                self.logger.error(f"Error processing plant {plant}: {e}", exc_info=True)
                continue

        self.logger.warning(f"All {len(plant_list)} plants checked - no MatRes, OrdRes, or STPord found")
        return None

    def process_material_multiple_plants(
        self,
        material_number: str,
        plant_list: List[str] = None,
        mrp_area: str = None
    ) -> (Optional[Dict[str, str]], Optional[str]):
        """
        LEGACY METHOD - Kept for backward compatibility.
        Consider using process_material_multiple_plants_optimized() instead.

        Try to process material across multiple plants using a robust /nMD04 navigation loop.
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

        self.logger.info(f"Starting robust /nMD04-based multi-plant search for {material_number}: {plant_list}")
        first_stpord_plant: Optional[str] = None

        for i, plant in enumerate(plant_list):
            self.logger.info(f"Attempting plant {plant} ({i+1}/{len(plant_list)})...")

            try:
                # Navigate to /nMD04 at the start of each loop for maximum stability.
                if not self.navigate_to_md04():
                    self.logger.error(f"Navigation to MD04 failed for plant {plant}. Skipping.")
                    continue
                time.sleep(3) # INCREASED DELAY for screen rendering

                # Enter details for the current plant
                if not self.ensure_individual_tab(): continue
                if not self.enter_material(material_number): continue
                if not self.set_plant(plant): continue
                self.set_mrp_area(plant)

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
                        return data, None

                # PRIORITY 2: If no MatRes, check for STPord
                if first_stpord_plant is None:
                    try:
                        table_id = self.config.get_field_id('MD04_RPM', 'item_list_table')
                        table = self.session.findById(table_id)
                        for row_idx in range(table.rows.count):
                            for col_idx in range(table.columns.count):
                                try:
                                    cell_text = table.getCell(row_idx, col_idx).text.strip()
                                    if cell_text == "STPord":
                                        self.logger.info(f"✓ PRIORITY 2: Noted 'STPord' found in plant {plant}.")
                                        first_stpord_plant = plant
                                        break
                                except:
                                    continue
                            if first_stpord_plant:
                                break
                    except Exception as e:
                        self.logger.warning(f"Could not scan for STPord in plant {plant}: {e}")

            except Exception as e:
                self.logger.error(f"An unexpected exception occurred while processing plant {plant}: {e}", exc_info=True)
                continue

        self.logger.info(f"Finished all plants. Returning STPord plant: {first_stpord_plant}")
        return None, first_stpord_plant

    def extract_rpm_from_current_screen(self, material_number: str, plant: str, stpord_row_index: int) -> Optional[str]:
        """
        OPTIMIZED: Extract RPM from the CURRENT screen without re-navigating.
        We already know the STPord row index from the table scan.

        Args:
            material_number: Material number
            plant: Plant number
            stpord_row_index: Row index where STPord was found

        Returns:
            RPM number if found, None otherwise
        """
        self.logger.info(f"Extracting RPM from current screen for material {material_number} at row {stpord_row_index}")

        try:
            # We're already on the MD04 results screen with STPord visible
            table_id = self.config.get_field_id('MD04_RPM', 'item_list_table')
            table = self.session.findById(table_id)

            # Navigate to STPord details
            table.getCell(stpord_row_index, 0).setFocus()
            time.sleep(0.5)
            self.session.findById("wnd[0]").sendVKey(2)  # F2 to enter edit mode
            time.sleep(self.config.WAIT_TIME_AFTER_ACTION)

            # Press item display button if available
            try:
                self.session.findById(self.config.get_field_id('MD04_RPM', 'item_display_button')).press()
                time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
            except:
                self.logger.debug("Item display button not found or not needed")

            # Check if requirements table is visible, if not expand it
            req_table_id = "wnd[0]/usr/subSUB0:SAPLMEGUI:0015/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211"
            try:
                req_table = self.session.findById(req_table_id)
                self.logger.info("Requirements table is already visible")
            except:
                self.logger.info("Expanding requirements table...")
                expand_button_id = "wnd[0]/usr/subSUB0:SAPLMEGUI:0015/subSUB2:SAPLMEVIEWS:1100/subSUB1:SAPLMEVIEWS:4001/btnDYN_4000-BUTTON"
                try:
                    self.session.findById(expand_button_id).press()
                    time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
                except:
                    self.logger.warning("Could not find expand button")

            # Read RPM number from the table
            req_table = self.session.findById(req_table_id)
            base_cell_id = f"{req_table_id}/txtMEPO1211-BEDNR[18,"

            for i in range(req_table.rows.count):
                try:
                    cell_id = f"{base_cell_id}{i}]"
                    rpm_full_text = self.field_manager.get_field_value(cell_id)

                    if rpm_full_text and rpm_full_text.upper().startswith("RPM"):
                        self.logger.info(f"Found raw RPM text: '{rpm_full_text}' in row {i}")
                        match = re.search(r'\d+', rpm_full_text)
                        if match:
                            rpm_number = match.group(0).lstrip('0')
                            self.logger.info(f"✓ Successfully extracted RPM number: {rpm_number}")
                            return rpm_number
                except:
                    continue

            self.logger.warning("Requirements table found but no RPM number detected")
            return None

        except Exception as e:
            self.logger.error(f"Error extracting RPM from current screen: {e}", exc_info=True)
            return None

    def extract_ordres_from_current_screen(self, material_number: str, plant: str, ordres_row_index: int) -> Optional[Dict[str, str]]:
        """
        OPTIMIZED: Extract OrdRes (Order Reservation) data from the CURRENT screen without re-navigating.
        We already know the OrdRes row index from the table scan.

        Args:
            material_number: Material number
            plant: Plant number
            ordres_row_index: Row index where OrdRes was found

        Returns:
            Dictionary with extracted data if successful, None otherwise
        """
        self.logger.info(f"Extracting OrdRes data from current screen for material {material_number} at row {ordres_row_index}")

        try:
            # We're already on the MD04 results screen with OrdRes visible
            table_id = self.config.get_field_id('MD04_RPM', 'item_list_table')  # Same table as STPord
            table = self.session.findById(table_id)

            # Navigate to OrdRes details
            table.getCell(ordres_row_index, 0).setFocus()
            time.sleep(0.5)
            self.session.findById("wnd[0]").sendVKey(2)  # F2 to enter details
            time.sleep(self.config.WAIT_TIME_AFTER_ACTION)

            # Press item display button if popup appears
            try:
                display_button = self.session.findById(self.config.get_field_id('ORDRES', 'item_display_button'))
                display_button.press()
                time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
                self.logger.info("Pressed item display button")
            except:
                self.logger.debug("Item display button not found or not needed")

            # Press SHOW button on grid shell
            try:
                grid_shell = self.session.findById(self.config.get_field_id('ORDRES', 'grid_shell'))
                grid_shell.pressToolbarButton("SHOW")
                time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
                self.logger.info("Pressed SHOW toolbar button")
            except Exception as e:
                self.logger.warning(f"Could not press SHOW button: {e}")

            # Extract data from OrdRes screen
            extracted_data = {}

            # Extract Cost Center
            try:
                cost_center_field = self.session.findById(self.config.get_field_id('ORDRES', 'cost_center_field'))
                extracted_data['cost_center'] = cost_center_field.text.strip()
                self.logger.info(f"Extracted Cost Center: {extracted_data['cost_center']}")
            except Exception as e:
                self.logger.warning(f"Could not extract cost center: {e}")
                extracted_data['cost_center'] = ""

            # Extract Part Description
            try:
                desc_field = self.session.findById(self.config.get_field_id('ORDRES', 'part_description_field'))
                extracted_data['part_description'] = desc_field.text.strip()
                self.logger.info(f"Extracted Part Description: {extracted_data['part_description']}")
            except Exception as e:
                self.logger.warning(f"Could not extract part description: {e}")
                extracted_data['part_description'] = ""

            # Extract Order Number
            try:
                order_field = self.session.findById(self.config.get_field_id('ORDRES', 'order_field'))
                extracted_data['order'] = order_field.text.strip()
                self.logger.info(f"Extracted Order: {extracted_data['order']}")
            except Exception as e:
                self.logger.warning(f"Could not extract order: {e}")
                extracted_data['order'] = ""

            # Add metadata
            extracted_data['material'] = material_number
            extracted_data['plant'] = plant
            extracted_data['source'] = 'OrdRes'

            self.logger.info(f"✓ Successfully extracted OrdRes data for {material_number}")
            return extracted_data

        except Exception as e:
            self.logger.error(f"Error extracting OrdRes from current screen: {e}", exc_info=True)
            return None

    def find_and_extract_rpm_number(self, material_number: str, plant: str) -> Optional[str]:
        """
        LEGACY METHOD - Re-navigates to MD04 which wastes time.
        Use extract_rpm_from_current_screen() instead when possible.

        Finds the STPord row, navigates to details, and extracts the RPM number
        by directly accessing the cell ID, exactly like the VBScript.
        """
        self.logger.info(f"Attempting to find RPM number for material {material_number} in plant {plant} using VBS-style direct access.")
        try:
            # 1. Navigate and execute query
            if not self.navigate_to_md04(): return None
            time.sleep(3)
            if not self.ensure_individual_tab(): return None
            if not self.enter_material(material_number): return None
            if not self.set_plant(plant): return None
            if not self.set_mrp_area(plant): return None
            if not self.execute_query(): return None

            # 2. Find and select the 'STPord' row
            table_id = self.config.get_field_id('MD04_RPM', 'item_list_table')
            table = self.session.findById(table_id)
            stpord_row_index = -1
            for i in range(table.rows.count):
                for j in range(table.columns.count):
                    try:
                        if table.getCell(i, j).text.strip() == "STPord":
                            stpord_row_index = i
                            break
                    except: continue
                if stpord_row_index != -1: break
            
            if stpord_row_index == -1:
                self.logger.warning(f"'STPord' row not found in plant {plant}.")
                return None

            # 3. Navigate to details screen
            table.getCell(stpord_row_index, 0).setFocus()
            self.session.findById("wnd[0]").sendVKey(2)
            time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
            try:
                self.session.findById(self.config.get_field_id('MD04_RPM', 'item_display_button')).press()
                time.sleep(self.config.WAIT_TIME_AFTER_ACTION)
            except: pass

            # 4. Expand items to show the requirements table, only if it's not already expanded.
            req_table_id = "wnd[0]/usr/subSUB0:SAPLMEGUI:0015/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211"
            try:
                # Check if table is already visible. If this fails, it means it's not visible.
                req_table = self.session.findById(req_table_id)
                self.logger.info("Requirements table is already visible. Proceeding to read.")
            except:
                # If table is not visible, press the expand button to show it.
                self.logger.info("Requirements table is not visible. Pressing 'Expand items' button...")
                expand_button_id = "wnd[0]/usr/subSUB0:SAPLMEGUI:0015/subSUB2:SAPLMEVIEWS:1100/subSUB1:SAPLMEVIEWS:4001/btnDYN_4000-BUTTON"
                self.session.findById(expand_button_id).press()
                time.sleep(self.config.WAIT_TIME_AFTER_ACTION)

            # 5. Read the RPM number from the now-visible table
            req_table = self.session.findById(req_table_id)
            base_cell_id = f"{req_table_id}/txtMEPO1211-BEDNR[18,"

            for i in range(req_table.rows.count):
                try:
                    cell_id = f"{base_cell_id}{i}]"
                    rpm_full_text = self.field_manager.get_field_value(cell_id)
                    
                    if rpm_full_text and rpm_full_text.upper().startswith("RPM"):
                        self.logger.info(f"Found raw RPM text: '{rpm_full_text}' in row {i}")
                        match = re.search(r'\d+', rpm_full_text)
                        if match:
                            rpm_number = match.group(0).lstrip('0')
                            self.logger.info(f"✓ Successfully extracted RPM number: {rpm_number}")
                            return rpm_number
                except:
                    continue
            
            self.logger.error("Found the requirements table, but no RPM number was found within it.")
            return None

        except Exception as e:
            self.logger.error(f"An unexpected error occurred during RPM number extraction: {e}", exc_info=True)
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
