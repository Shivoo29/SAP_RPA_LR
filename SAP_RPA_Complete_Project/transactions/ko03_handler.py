"""
KO03 Transaction Handler
=========================
Handles KO03 transaction for internal order display.
"""

import time
import logging
from typing import Optional, Dict

from core.field_manager import FieldManager
from config import Config


class KO03Handler:
    """Handles KO03 transaction operations."""
    
    def __init__(self, sap_connector):
        """
        Initialize KO03 handler.
        
        Args:
            sap_connector: SAP connector instance
        """
        self.sap_connector = sap_connector
        self.session = sap_connector.session
        self.field_manager = FieldManager(self.session)
        self.logger = logging.getLogger(__name__)
        self.config = Config()
    
    def navigate_to_ko03(self) -> bool:
        """
        Navigate to KO03 transaction.
        
        Returns:
            True if successful
        """
        return self.sap_connector.navigate_to_transaction('KO03')
    
    def enter_order_number(self, order_number: str) -> bool:
        """
        Enter order number in KO03.
        
        Args:
            order_number: Internal order number
            
        Returns:
            True if successful
        """
        self.logger.info(f"Entering order number: {order_number}")
        
        field_id = self.config.KO03_FIELDS.get('order_field', '')
        if not field_id:
            self.logger.error("Order field ID not configured")
            return False
        
        success = self.field_manager.fill_field(field_id, order_number)
        
        if not success:
            self.logger.error(f"Failed to enter order number: {order_number}")
        
        return success
    
    def execute_query(self) -> bool:
        """
        Execute the KO03 query by pressing Enter.
        
        Returns:
            True if successful
        """
        self.logger.info("Executing KO03 query...")
        
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
    
    def extract_order_details(self) -> Dict[str, str]:
        """
        Extract order details from KO03 screen.
        
        Returns:
            Dictionary with extracted order details
        """
        self.logger.info("Extracting order details from KO03...")
        
        # Define fields to extract (you'll need to add actual field IDs)
        extraction_fields = {
            'order_number': self.config.KO03_FIELDS.get('order_field', ''),
            'order_type': self.config.KO03_FIELDS.get('order_type_field', ''),
            # Add more fields as discovered from VBS scripts
        }
        
        extracted_data = {}
        
        for field_name, field_id in extraction_fields.items():
            if field_id:
                value = self.field_manager.get_field_value(field_id)
                extracted_data[field_name] = value
                self.logger.debug(f"Extracted {field_name}: {value}")
            else:
                self.logger.warning(f"Field ID not configured for {field_name}")
                extracted_data[field_name] = ""
        
        return extracted_data
    
    def process_order(self, order_number: str) -> Optional[Dict[str, str]]:
        """
        Process an order number in KO03.
        
        Args:
            order_number: Internal order number
            
        Returns:
            Extracted order details if successful, None otherwise
        """
        self.logger.info(f"Processing order: {order_number}")
        
        try:
            # Navigate to KO03
            if not self.navigate_to_ko03():
                return None
            
            # Enter order number
            if not self.enter_order_number(order_number):
                return None
            
            # Execute query
            if not self.execute_query():
                return None
            
            # Extract details
            data = self.extract_order_details()
            
            if data:
                self.logger.info(f"Successfully extracted data for order {order_number}")
                return data
            else:
                self.logger.warning(f"No data extracted for order {order_number}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error processing order {order_number}: {e}")
            return None
    
    def extract_using_vbs(self, vbs_script_path: str) -> Optional[Dict[str, str]]:
        """
        Execute VBS script to extract data from KO03.
        
        Args:
            vbs_script_path: Path to VBS script
            
        Returns:
            Extracted data if successful, None otherwise
        """
        self.logger.info(f"Executing VBS script: {vbs_script_path}")
        
        try:
            import subprocess
            
            # Execute VBS script
            result = subprocess.run(
                ['cscript', '//nologo', str(vbs_script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse VBS output
                output = result.stdout.strip()
                self.logger.info(f"VBS script output: {output}")
                
                # TODO: Parse output into structured data
                # This depends on what your VBS script outputs
                
                return {'vbs_output': output}
            else:
                self.logger.error(f"VBS script failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing VBS script: {e}")
            return None
