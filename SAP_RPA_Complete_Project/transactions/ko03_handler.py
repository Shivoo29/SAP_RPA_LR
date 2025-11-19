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
from utils import execute_vbs_script, parse_vbs_output_to_dict


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
        Uses shared SAP connector method to avoid duplication.

        Returns:
            True if successful
        """
        self.logger.info("Executing KO03 query...")
        return self.sap_connector.execute_sap_query(wait_time=self.config.WAIT_TIME_AFTER_QUERY)
    
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
        Uses shared utility function to avoid code duplication.

        Args:
            vbs_script_path: Path to VBS script

        Returns:
            Extracted data if successful, None otherwise
        """
        from pathlib import Path

        self.logger.info(f"Executing VBS script for KO03 data extraction...")

        vbs_path = Path(vbs_script_path) if isinstance(vbs_script_path, str) else vbs_script_path
        result = execute_vbs_script(vbs_path, timeout=30)

        if result and result['success']:
            # Parse the output into structured data
            parsed_data = parse_vbs_output_to_dict(result['output'])
            self.logger.info(f"VBS script extracted {len(parsed_data)} fields")
            return parsed_data
        else:
            self.logger.warning("VBS script execution failed or returned no data")
            return None
