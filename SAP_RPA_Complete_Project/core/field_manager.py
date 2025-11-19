"""
Field Manager
=============
Manages SAP field detection, interaction, and data extraction.
"""

import time
import logging
from typing import Optional, Dict, List


class FieldManager:
    """Manages interactions with SAP fields."""
    
    def __init__(self, session):
        """
        Initialize field manager.
        
        Args:
            session: SAP session object
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    def find_field(self, field_id: str) -> Optional[object]:
        """
        Find a SAP field by ID.
        
        Args:
            field_id: SAP field ID
            
        Returns:
            Field object if found, None otherwise
        """
        try:
            field = self.session.findById(field_id)
            return field
        except Exception as e:
            self.logger.debug(f"Field {field_id} not found: {e}")
            return None
    
    def get_field_value(self, field_id: str) -> str:
        """
        Get the value of a field.
        
        Args:
            field_id: SAP field ID
            
        Returns:
            Field value as string, empty string if not found
        """
        try:
            field = self.find_field(field_id)
            if field and hasattr(field, 'text'):
                return str(field.text).strip()
            return ""
        except Exception as e:
            self.logger.error(f"Error getting field value {field_id}: {e}")
            return ""
    
    def fill_field(self, field_id: str, value: str, method: str = 'auto') -> bool:
        """
        Fill a field with a value using specified or automatic method.
        
        Args:
            field_id: SAP field ID
            value: Value to enter
            method: Method to use ('auto', 'direct', 'focus', 'keyboard')
            
        Returns:
            True if successful, False otherwise
        """
        field = self.find_field(field_id)
        if not field:
            self.logger.error(f"Cannot fill field {field_id}: Field not found")
            return False
        
        # Make field editable if needed
        self.make_field_editable(field_id)
        
        # Try different methods based on preference
        methods = {
            'direct': self._fill_direct,
            'focus': self._fill_with_focus,
            'keyboard': self._fill_with_keyboard,
        }
        
        if method == 'auto':
            # Try all methods in order
            for method_name, method_func in methods.items():
                try:
                    if method_func(field, value):
                        current_value = self.get_field_value(field_id)
                        if current_value == value:
                            self.logger.debug(f"Field filled successfully with {method_name} method")
                            return True
                except Exception as e:
                    self.logger.debug(f"Method {method_name} failed: {e}")
                    continue
        else:
            # Use specific method
            method_func = methods.get(method)
            if method_func:
                try:
                    return method_func(field, value)
                except Exception as e:
                    self.logger.error(f"Failed to fill field with {method} method: {e}")
                    return False
        
        return False
    
    def _fill_direct(self, field, value: str) -> bool:
        """Direct assignment method."""
        field.text = value
        time.sleep(0.5)
        return True
    
    def _fill_with_focus(self, field, value: str) -> bool:
        """Fill with focus method."""
        field.setFocus()
        time.sleep(0.3)
        field.text = value
        time.sleep(0.5)
        return True
    
    def _fill_with_keyboard(self, field, value: str) -> bool:
        """Fill using keyboard simulation."""
        field.setFocus()
        time.sleep(0.3)
        
        # Clear field
        field.text = ""
        time.sleep(0.2)
        
        # Type value
        field.text = value
        time.sleep(0.3)
        
        # Press Tab to confirm
        try:
            self.session.findById("wnd[0]").sendVKey(1)  # Tab key
            time.sleep(0.2)
        except:
            pass
        
        return True
    
    def make_field_editable(self, field_id: str) -> bool:
        """
        Try to make a field editable.
        
        Args:
            field_id: SAP field ID
            
        Returns:
            True if field is now editable
        """
        try:
            field = self.find_field(field_id)
            if not field:
                return False
            
            # Check if already editable
            if getattr(field, 'Modifiable', False):
                return True
            
            # Try to make editable
            field.setFocus()
            time.sleep(0.5)
            
            # Try pressing F2 (Edit mode)
            try:
                self.session.findById("wnd[0]").sendVKey(2)
                time.sleep(0.5)
            except:
                pass
            
            # Check again
            return getattr(field, 'Modifiable', False)
            
        except Exception as e:
            self.logger.debug(f"Could not make field editable: {e}")
            return False
    
    def extract_fields(self, field_map: Dict[str, str]) -> Dict[str, str]:
        """
        Extract values from multiple fields.
        
        Args:
            field_map: Dictionary mapping field names to field IDs
            
        Returns:
            Dictionary with field names and extracted values
        """
        extracted_data = {}
        
        for field_name, field_id in field_map.items():
            try:
                value = self.get_field_value(field_id)
                extracted_data[field_name] = value
                self.logger.debug(f"Extracted {field_name}: {value}")
            except Exception as e:
                self.logger.warning(f"Failed to extract {field_name}: {e}")
                extracted_data[field_name] = ""
        
        return extracted_data
    
    def find_matres_element(self) -> Optional[object]:
        """
        Finds the MatRes element by specifically searching the MD04 results table
        across all rows and columns.

        Returns:
            MatRes element (the table cell) if found, None otherwise.
        """
        self.logger.info("Scanning MD04 results table for 'MatRes'...")
        try:
            # This ID is from the new config, assuming it's the same table for both searches
            table_id = "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_1/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ"
            table = self.session.findById(table_id)

            # Iterate through all rows and all columns to find 'MatRes'
            for row_idx in range(table.rows.count):
                for col_idx in range(table.columns.count):
                    try:
                        cell = table.getCell(row_idx, col_idx)
                        if hasattr(cell, 'text') and cell.text.strip() == 'MatRes':
                            self.logger.info(f"✓ MatRes element found in table at row {row_idx}, col {col_idx}.")
                            return cell
                    except Exception:
                        # This cell might not have a 'text' property, continue to the next
                        continue

            self.logger.warning("MatRes element not found in the results table.")
            return None

        except Exception as e:
            self.logger.error(f"Error finding MatRes in table: {e}", exc_info=True)
            return None

    def scan_md04_table_for_elements(self) -> dict:
        """
        Scans the MD04 results table ONCE for MatRes, OrdRes, and STPord elements.
        This is more efficient than scanning multiple times.

        Priority order:
        1. MatRes (Material Reservation) - highest priority
        2. OrdRes (Order Reservation) - second priority
        3. STPord (Stock Transfer Purchase Order) - third priority

        Returns:
            Dictionary with keys:
            - 'matres_element': MatRes cell element if found
            - 'has_ordres': True if OrdRes found
            - 'ordres_row_index': Row index of OrdRes
            - 'has_stpord': True if STPord found
            - 'stpord_row_index': Row index of STPord
        """
        self.logger.info("Scanning MD04 results table for MatRes, OrdRes, and STPord in single pass...")
        result = {
            'matres_element': None,
            'has_ordres': False,
            'ordres_row_index': -1,
            'has_stpord': False,
            'stpord_row_index': -1
        }

        try:
            table_id = "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_1/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ"
            table = self.session.findById(table_id)

            # Single pass through the table
            for row_idx in range(table.rows.count):
                for col_idx in range(table.columns.count):
                    try:
                        cell = table.getCell(row_idx, col_idx)
                        if not hasattr(cell, 'text'):
                            continue

                        cell_text = cell.text.strip()

                        # Check for MatRes - PRIORITY 1
                        if cell_text == 'MatRes':
                            self.logger.info(f"✓ MatRes found at row {row_idx}, col {col_idx}")
                            result['matres_element'] = cell
                            # Continue scanning to log all available options

                        # Check for OrdRes - PRIORITY 2
                        elif cell_text == 'OrdRes' and not result['has_ordres']:
                            self.logger.info(f"✓ OrdRes found at row {row_idx}, col {col_idx}")
                            result['has_ordres'] = True
                            result['ordres_row_index'] = row_idx

                        # Check for STPord - PRIORITY 3
                        elif cell_text == 'STPord' and not result['has_stpord']:
                            self.logger.info(f"✓ STPord found at row {row_idx}, col {col_idx}")
                            result['has_stpord'] = True
                            result['stpord_row_index'] = row_idx

                    except Exception:
                        continue

            # Log results with priority indication
            if result['matres_element']:
                self.logger.info("Scan complete: MatRes found (PRIORITY 1 - will use this)")
            elif result['has_ordres']:
                self.logger.info("Scan complete: OrdRes found (PRIORITY 2 - will use this)")
            elif result['has_stpord']:
                self.logger.info("Scan complete: STPord found (PRIORITY 3 - will extract RPM)")
            else:
                self.logger.warning("Scan complete: No MatRes, OrdRes, or STPord found")

            return result

        except Exception as e:
            self.logger.error(f"Error scanning MD04 table: {e}", exc_info=True)
            return result
    
    def click_element(self, element_or_id) -> bool:
        """
        Click on an element.
        
        Args:
            element_or_id: SAP element object or field ID
            
        Returns:
            True if successful
        """
        try:
            # Get element if ID was provided
            if isinstance(element_or_id, str):
                element = self.find_field(element_or_id)
            else:
                element = element_or_id
            
            if not element:
                return False
            
            # Try to click
            element.setFocus()
            time.sleep(0.3)
            
            # Try double-click if available
            try:
                element.doubleClick()
                time.sleep(1)
                return True
            except:
                # Single click fallback
                try:
                    element.press()
                    time.sleep(1)
                    return True
                except:
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error clicking element: {e}")
            return False
