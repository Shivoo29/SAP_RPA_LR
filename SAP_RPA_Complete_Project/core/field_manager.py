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
    
    def scan_element_for_matres(self, element, depth: int = 0) -> Optional[object]:
        """
        Recursively scan element tree for MatRes text.
        
        Args:
            element: SAP element to scan
            depth: Current depth in element tree
            
        Returns:
            MatRes element if found, None otherwise
        """
        if depth > 10:  # Prevent infinite recursion
            return None
        
        try:
            # Check if this element has 'MatRes' text
            if hasattr(element, 'text'):
                text = str(element.text).strip()
                if text == 'MatRes':
                    return element
            
            # Scan children
            try:
                children_count = element.Children.Count
                for i in range(children_count):
                    try:
                        child = element.Children(i)
                        result = self.scan_element_for_matres(child, depth + 1)
                        if result:
                            return result
                    except:
                        continue
            except:
                pass
                
        except:
            pass
        
        return None
    
    def find_matres_element(self) -> Optional[object]:
        """
        Find the MatRes element in the current SAP window.
        
        Returns:
            MatRes element if found, None otherwise
        """
        try:
            self.logger.info("Scanning for MatRes element...")
            main_window = self.session.findById("wnd[0]")
            matres_element = self.scan_element_for_matres(main_window, 0)
            
            if matres_element:
                self.logger.info("MatRes element found!")
                return matres_element
            else:
                self.logger.warning("MatRes element not found")
                return None
                
        except Exception as e:
            self.logger.error(f"Error finding MatRes: {e}")
            return None
    
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
