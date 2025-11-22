"""
Field Manager
=============
Manages SAP field detection, interaction, and data extraction.
"""

import time
import logging
from typing import Optional, Dict, List
from core.table_id_cache import TableIDCache


class FieldManager:
    """Manages interactions with SAP fields."""

    def __init__(self, session, cache_manager: Optional[TableIDCache] = None):
        """
        Initialize field manager.

        Args:
            session: SAP session object
            cache_manager: Optional table ID cache manager
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
        self.cache_manager = cache_manager or TableIDCache()

        # Runtime session cache for table IDs
        self.session_table_cache = {}
        self.current_plant = None
        self.current_material = None
    
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

    def scan_md04_table_for_elements(self, plant: Optional[str] = None,
                                     material: Optional[str] = None) -> dict:
        """
        Scans the MD04 results table ONCE for MatRes, OrdRes, DepReq, and STPord elements.
        Uses 3-tier detection strategy with caching.

        Priority order:
        1. MatRes (Material Reservation) - highest priority
        2. OrdRes (Order Reservation) - second priority
        2.5 DepReq (Dependent Requirement) - same workflow as OrdRes
        3. STPord (Stock Transfer Purchase Order) - third priority

        Args:
            plant: Current plant number (for cache context)
            material: Current material number (for cache context)

        Returns:
            Dictionary with keys:
            - 'matres_element': MatRes cell element if found
            - 'has_ordres': True if OrdRes found
            - 'ordres_row_index': Row index of OrdRes
            - 'has_depreq': True if DepReq found
            - 'depreq_row_index': Row index of DepReq
            - 'has_stpord': True if STPord found
            - 'stpord_row_index': Row index of STPord
            - 'table_id_used': The table ID that worked (for debugging)
        """
        self.current_plant = plant
        self.current_material = material

        self.logger.info("🔍 Starting robust MD04 table scan (3-tier detection)...")

        result = {
            'matres_element': None,
            'has_ordres': False,
            'ordres_row_index': -1,
            'has_stpord': False,
            'stpord_row_index': -1,
            'table_id_used': None
        }

        # TIER 1: Try cached table IDs (fastest)
        table_id = self._try_cached_table_ids()

        if table_id:
            self.logger.info(f"✓ TIER 1 SUCCESS: Using cached table ID")
            result = self._scan_table(table_id)
            result['table_id_used'] = table_id

            if result['matres_element'] or result['has_ordres'] or result['has_stpord']:
                # Record success in cache
                self.cache_manager.record_success(table_id, plant, material)
                return result

        # TIER 2: Try known alternative table IDs
        self.logger.info("⚠ TIER 1 failed - trying known alternative table IDs...")
        table_id = self._try_known_table_ids()

        if table_id:
            self.logger.info(f"✓ TIER 2 SUCCESS: Found working table ID")
            result = self._scan_table(table_id)
            result['table_id_used'] = table_id

            if result['matres_element'] or result['has_ordres'] or result['has_stpord']:
                # Record success and cache this discovery
                self.cache_manager.record_success(table_id, plant, material)
                return result

        # TIER 3: Dynamic table discovery (slowest but most robust)
        self.logger.warning("⚠ TIER 2 failed - starting dynamic table discovery...")
        table_id = self._discover_md04_table()

        if table_id:
            self.logger.info(f"✓ TIER 3 SUCCESS: Discovered new table ID dynamically!")
            result = self._scan_table(table_id)
            result['table_id_used'] = table_id

            if result['matres_element'] or result['has_ordres'] or result['has_stpord']:
                # Record this new discovery
                self.cache_manager.record_success(table_id, plant, material)
                self.logger.info(f"💾 New table ID cached for future use")
                return result

        # All tiers failed
        self.logger.error("✗ ALL TIERS FAILED: Could not find MD04 results table")
        self.logger.error("This might indicate: (1) No data in MD04, (2) Screen layout error, (3) Different SAP version")

        return result

    def _try_cached_table_ids(self) -> Optional[str]:
        """
        Try table IDs from cache.

        Returns:
            Working table ID if found, None otherwise
        """
        cached_ids = self.cache_manager.get_cached_table_ids()

        if not cached_ids:
            self.logger.debug("No cached table IDs available")
            return None

        self.logger.info(f"Trying {len(cached_ids)} cached table ID(s)...")

        for table_id in cached_ids:
            try:
                table = self.session.findById(table_id)
                if self._is_valid_md04_table(table):
                    self.logger.debug(f"✓ Cached table ID valid: {table_id[:50]}...")
                    return table_id
            except Exception as e:
                self.logger.debug(f"Cached ID failed: {str(e)[:50]}...")
                self.cache_manager.record_failure(table_id)
                continue

        return None

    def _try_known_table_ids(self) -> Optional[str]:
        """
        Try known alternative table IDs from config.

        Returns:
            Working table ID if found, None otherwise
        """
        # Import config here to avoid circular dependency
        from config import Config
        import re

        known_ids = Config.MD04_TABLE_IDS if hasattr(Config, 'MD04_TABLE_IDS') else []

        if not known_ids:
            # Fallback to hardcoded common patterns
            known_ids = [
                "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_1/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ",
                "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_2/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ",
                "wnd[0]/usr/tblSAPMM61RTC_EZ",
                "wnd[0]/usr/cntlGRID1/shellcont/shell",
            ]

        self.logger.info(f"Trying {len(known_ids)} known table ID pattern(s)...")

        for table_id in known_ids:
            # Try both original and cell-stripped versions
            ids_to_try = [table_id]

            # Strip cell position if present (e.g., [3,2] or /cell[3,2])
            stripped_id = re.sub(r'\[?\d+,\d+\]?$', '', table_id)
            stripped_id = re.sub(r'/cell\[\d+,\d+\]$', '', stripped_id)
            if stripped_id != table_id:
                ids_to_try.append(stripped_id)
                self.logger.debug(f"Detected cell position in ID, trying stripped: {stripped_id[:50]}...")

            for try_id in ids_to_try:
                try:
                    table = self.session.findById(try_id)
                    if self._is_valid_md04_table(table):
                        self.logger.debug(f"✓ Known table ID valid: {try_id[:50]}...")
                        # Add to cache for future use
                        self.cache_manager.add_known_table_id(try_id, source="config")
                        return try_id
                except Exception as e:
                    self.logger.debug(f"ID failed: {str(e)[:50]}...")
                    continue

        return None

    def _discover_md04_table(self) -> Optional[str]:
        """
        Dynamically discover MD04 table by recursively scanning ALL screen elements.

        Returns:
            Discovered table ID if found, None otherwise
        """
        self.logger.info("🔎 Scanning screen for table controls...")

        try:
            # Get main window
            main_window = self.session.findById("wnd[0]")

            # Strategy 1: Enumerate ALL children recursively
            candidate_ids = []
            self._enumerate_all_tables(main_window, candidate_ids, max_depth=5)

            self.logger.info(f"Found {len(candidate_ids)} potential table control(s) via enumeration")

            # Validate each candidate
            for table_id in candidate_ids:
                try:
                    table = self.session.findById(table_id)
                    if self._is_valid_md04_table(table):
                        self.logger.info(f"✓ Discovered valid MD04 table: {table_id}")
                        return table_id
                except Exception:
                    continue

            # Strategy 2: Try common patterns as fallback
            if not candidate_ids:
                self.logger.info("Enumeration failed, trying pattern-based discovery...")
                patterns = [
                    "wnd[0]/usr/tbl",
                    "wnd[0]/usr/subINCLUDE",
                    "wnd[0]/usr/cntl",
                    "wnd[0]/shell",
                ]

                for pattern in patterns:
                    discovered = self._find_controls_by_pattern(main_window, pattern)
                    candidate_ids.extend(discovered)

                self.logger.info(f"Found {len(candidate_ids)} potential table(s) via patterns")

                # Validate pattern-based candidates
                for table_id in candidate_ids:
                    try:
                        table = self.session.findById(table_id)
                        if self._is_valid_md04_table(table):
                            self.logger.info(f"✓ Discovered valid MD04 table: {table_id}")
                            return table_id
                    except Exception:
                        continue

        except Exception as e:
            self.logger.error(f"Error during table discovery: {e}")

        return None

    def _enumerate_all_tables(self, element, table_list: List[str],
                             current_depth: int = 0, max_depth: int = 5):
        """
        Recursively enumerate ALL SAP elements and find table controls.

        Args:
            element: Current SAP element
            table_list: List to append discovered table IDs
            current_depth: Current recursion depth
            max_depth: Maximum recursion depth
        """
        if current_depth >= max_depth:
            return

        try:
            # Get element ID
            element_id = element.id if hasattr(element, 'id') else None

            if not element_id:
                return

            # Check if this element is a table
            element_type = element.Type if hasattr(element, 'Type') else ''

            # Check for table-like types
            if any(indicator in element_type.lower() for indicator in ['grid', 'table', 'tree']) or \
               any(indicator in element_id.lower() for indicator in ['tbl', 'grid', 'tree']):
                # Verify it has table properties
                if hasattr(element, 'rows') or hasattr(element, 'RowCount'):
                    if element_id not in table_list:
                        table_list.append(element_id)
                        self.logger.debug(f"Found table candidate: {element_id}")

            # Recursively check children
            if hasattr(element, 'Children'):
                try:
                    children_count = element.Children.Count
                    for i in range(children_count):
                        try:
                            child = element.Children(i)
                            self._enumerate_all_tables(child, table_list, current_depth + 1, max_depth)
                        except Exception:
                            continue
                except Exception:
                    pass

        except Exception:
            pass

    def _find_controls_by_pattern(self, parent, pattern: str) -> List[str]:
        """
        Find controls matching a pattern.

        Args:
            parent: Parent SAP element
            pattern: Pattern to match

        Returns:
            List of control IDs
        """
        found_ids = []

        try:
            # This is a simplified approach - in real SAP scripting,
            # you'd need to recursively traverse the element tree
            # For now, we'll try common numbered variations

            if "tbl" in pattern:
                # Try table patterns
                for i in range(10):
                    test_id = f"{pattern}SAPMM61RTC_EZ"
                    try:
                        self.session.findById(test_id)
                        found_ids.append(test_id)
                    except:
                        pass

            elif "shell" in pattern or "cntl" in pattern:
                # Try grid/shell patterns
                test_patterns = [
                    f"{pattern}/shellcont/shell",
                    f"{pattern}GRID1/shellcont/shell",
                    pattern
                ]
                for test_id in test_patterns:
                    try:
                        self.session.findById(test_id)
                        found_ids.append(test_id)
                    except:
                        pass

        except Exception as e:
            self.logger.debug(f"Pattern search error: {e}")

        return found_ids

    def _is_valid_md04_table(self, table) -> bool:
        """
        Validate if a table element is the MD04 results table.

        Args:
            table: Table element to validate

        Returns:
            True if valid MD04 table
        """
        try:
            # Check if it has table-like properties
            if not hasattr(table, 'rows') and not hasattr(table, 'RowCount'):
                return False

            # Try to get row count
            row_count = 0
            if hasattr(table, 'rows'):
                row_count = table.rows.count if hasattr(table.rows, 'count') else len(table.rows)
            elif hasattr(table, 'RowCount'):
                row_count = table.RowCount

            # Valid tables should have at least 0 rows (can be empty)
            if row_count < 0:
                return False

            # Additional validation: try to access first cell if rows exist
            if row_count > 0:
                if hasattr(table, 'getCell'):
                    try:
                        table.getCell(0, 0)
                        return True
                    except:
                        pass
                elif hasattr(table, 'GetCellValue'):
                    try:
                        table.GetCellValue(0, 0)
                        return True
                    except:
                        pass

            # Empty table is still valid
            return True

        except Exception as e:
            self.logger.debug(f"Table validation failed: {e}")
            return False

    def _check_row_for_1a_demand(self, table, row_idx: int, col_count: int) -> bool:
        """
        Check if a row contains "1A-" pattern in MRP element data column.

        Args:
            table: SAP table object
            row_idx: Row index to check
            col_count: Number of columns in table

        Returns:
            True if "1A-" pattern found in row
        """
        try:
            # Scan all columns in the row for "1A-" pattern
            for col_idx in range(col_count):
                try:
                    cell = table.getCell(row_idx, col_idx)
                    if hasattr(cell, 'text'):
                        cell_text = cell.text.strip()
                        if cell_text.startswith('1A-'):
                            self.logger.info(f"Found 1A demand indicator: '{cell_text}' at row {row_idx}, col {col_idx}")
                            return True
                except:
                    continue
            return False
        except Exception as e:
            self.logger.debug(f"Error checking row for 1A demand: {e}")
            return False

    def _scan_table(self, table_id: str) -> dict:
        """
        Scan a table for MatRes, OrdRes, DepReq, and STPord elements.

        Args:
            table_id: ID of table to scan

        Returns:
            Scan results dictionary
        """
        result = {
            'matres_element': None,
            'has_ordres': False,
            'ordres_row_index': -1,
            'has_depreq': False,
            'depreq_row_index': -1,
            'has_stpord': False,
            'stpord_row_index': -1,
            'is_1a_demand': False,
            'mrp_element_type': None
        }

        try:
            table = self.session.findById(table_id)

            # Get row count
            row_count = table.rows.count if hasattr(table.rows, 'count') else len(table.rows)
            col_count = table.columns.count if hasattr(table, 'columns') else 0

            self.logger.debug(f"Scanning table with {row_count} rows, {col_count} columns")

            # Single pass through the table
            for row_idx in range(row_count):
                for col_idx in range(col_count):
                    try:
                        cell = table.getCell(row_idx, col_idx)
                        if not hasattr(cell, 'text'):
                            continue

                        cell_text = cell.text.strip()

                        # Check for MatRes - PRIORITY 1
                        if cell_text == 'MatRes':
                            self.logger.info(f"✓ MatRes found at row {row_idx}, col {col_idx}")
                            result['matres_element'] = cell
                            # Check if this row has 1A demand
                            if self._check_row_for_1a_demand(table, row_idx, col_count):
                                result['is_1a_demand'] = True
                                result['mrp_element_type'] = 'MatRes'

                        # Check for OrdRes - PRIORITY 2
                        elif cell_text == 'OrdRes' and not result['has_ordres']:
                            self.logger.info(f"✓ OrdRes found at row {row_idx}, col {col_idx}")
                            result['has_ordres'] = True
                            result['ordres_row_index'] = row_idx
                            # Check if this row has 1A demand
                            if self._check_row_for_1a_demand(table, row_idx, col_count):
                                result['is_1a_demand'] = True
                                result['mrp_element_type'] = 'OrdRes'

                        # Check for DepReq - PRIORITY 2.5 (same workflow as OrdRes)
                        elif cell_text == 'DepReq' and not result['has_depreq']:
                            self.logger.info(f"✓ DepReq found at row {row_idx}, col {col_idx}")
                            result['has_depreq'] = True
                            result['depreq_row_index'] = row_idx
                            # Check if this row has 1A demand
                            if self._check_row_for_1a_demand(table, row_idx, col_count):
                                result['is_1a_demand'] = True
                                result['mrp_element_type'] = 'DepReq'

                        # Check for STPord - PRIORITY 3
                        elif cell_text == 'STPord' and not result['has_stpord']:
                            self.logger.info(f"✓ STPord found at row {row_idx}, col {col_idx}")
                            result['has_stpord'] = True
                            result['stpord_row_index'] = row_idx
                            # Check if this row has 1A demand
                            if self._check_row_for_1a_demand(table, row_idx, col_count):
                                result['is_1a_demand'] = True
                                result['mrp_element_type'] = 'STPord'

                    except Exception:
                        continue

            # Log results
            if result['matres_element']:
                self.logger.info("✓ Scan complete: MatRes found (PRIORITY 1)")
            elif result['has_ordres']:
                self.logger.info("✓ Scan complete: OrdRes found (PRIORITY 2)")
            elif result['has_depreq']:
                self.logger.info("✓ Scan complete: DepReq found (PRIORITY 2.5)")
            elif result['has_stpord']:
                self.logger.info("✓ Scan complete: STPord found (PRIORITY 3)")
            else:
                self.logger.warning("Scan complete: No MatRes, OrdRes, DepReq, or STPord found")

        except Exception as e:
            self.logger.error(f"Error during table scan: {e}", exc_info=True)

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
