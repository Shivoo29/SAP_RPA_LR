"""
ERF Workflow
============
Handles ERF Dashboard automation using Selenium WebDriver.
Integrates with VBS scripts for additional data extraction.
"""

import time
import logging
from typing import Optional, Dict
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from config import Config
from data.data_models import ERFData
from utils import execute_vbs_script, parse_vbs_output_to_dict


class ERFWorkflow:
    """Handles ERF Dashboard automation workflow."""
    
    def __init__(self, sap_connector):
        """
        Initialize ERF workflow.
        
        Args:
            sap_connector: SAP connector instance
        """
        self.sap_connector = sap_connector
        self.logger = logging.getLogger(__name__)
        self.config = Config()
        self.driver = None
    
    def setup_webdriver(self) -> bool:
        """
        Setup Selenium WebDriver for Edge.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("Setting up Edge WebDriver...")
            
            # Check if driver path exists
            driver_path = Path(self.config.EDGE_DRIVER_PATH)
            if not driver_path.exists():
                self.logger.error(f"Edge driver not found at: {driver_path}")
                return False
            
            # Setup Edge options
            options = webdriver.EdgeOptions()
            options.use_chromium = True
            # options.add_argument('--headless')  # Uncomment for headless mode
            
            # Create service and driver
            service = Service(executable_path=str(driver_path))
            self.driver = webdriver.Edge(service=service, options=options)
            
            self.logger.info("WebDriver setup successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False
    
    def navigate_to_erf_dashboard(self) -> bool:
        """
        Navigate to ERF Dashboard.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("Navigating to ERF Dashboard...")
            
            self.driver.get(self.config.ERF_DASHBOARD_URL)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.config.WEB_TIMEOUT)
            
            # Wait for ERF Dashboard tab to be clickable
            erf_dashboard = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@class='TabText' and text()='ERF Dashboard']")
                )
            )
            
            erf_dashboard.click()
            self.logger.info("Clicked ERF Dashboard tab")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to navigate to ERF Dashboard: {e}")
            return False
    
    def switch_to_erf_iframe(self) -> bool:
        """
        Switch to the ERF Dashboard iframe.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("Switching to ERF iframe...")
            
            wait = WebDriverWait(self.driver, self.config.WEB_TIMEOUT)
            
            # Wait for page to fully load
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(5)
            
            # Switch to content area frame
            iframe_1 = wait.until(EC.presence_of_element_located((By.ID, "contentAreaFrame")))
            self.driver.switch_to.frame(iframe_1)
            self.logger.info("Switched to iframe 1")
            
            # Switch to nested iframe
            nested_iframe = wait.until(EC.presence_of_element_located((By.ID, "isolatedWorkArea")))
            self.driver.switch_to.frame(nested_iframe)
            self.logger.info("Switched to nested iframe")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to switch to iframe: {e}")
            return False
    
    def search_erf_by_term(self, erf_search_term: str) -> Optional[str]:
        """
        Search for ERF by a given search term (material or RPM number).
        
        Args:
            erf_search_term: The term to search for in the ERF input.
            
        Returns:
            ERF number if found, None otherwise
        """
        try:
            self.logger.info(f"Searching ERF for term: {erf_search_term}")
            
            wait = WebDriverWait(self.driver, self.config.WEB_TIMEOUT)
            
            # Select "ALL" from plant dropdown
            plant_input = wait.until(
                EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.PlantsDdbk"))
            )
            plant_input.click()
            
            all_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(),'ALL')]"))
            )
            all_option.click()
            self.logger.info("Selected 'ALL' from plant dropdown")
            
            # Enter material number (ERF number in this context)
            erf_input = wait.until(
                EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.ERFNumInp"))
            )
            erf_input.clear()
            erf_input.send_keys(erf_search_term)
            self.logger.info(f"Entered search term: {erf_search_term}")
            
            # Click search button
            search_button = wait.until(
                EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.SearchBtn"))
            )
            search_button.click()
            self.logger.info("Clicked search button")
            
            time.sleep(2)
            
            # Check for results - click on the "1" link
            try:
                one_link = wait.until(
                    EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.ALL_1Lta-text"))
                )
                one_link.click()
                self.logger.info("Found and clicked result link")
                
                return erf_search_term  # Return as ERF number
                
            except Exception:
                self.logger.warning(f"No results found for term '{erf_search_term}'")
                return None
            
        except Exception as e:
            self.logger.error(f"Error searching ERF: {e}")
            return None
    
    def extract_erf_data(self) -> Optional[ERFData]:
        """
        Extract data from ERF Dashboard screen.
        
        Returns:
            ERFData object if successful, None otherwise
        """
        self.logger.info("Extracting ERF data...")
        wait = WebDriverWait(self.driver, self.config.WEB_TIMEOUT)
        erf_data = ERFData()

        try:
            # Click "Update/View ERF" button and wait for a known element on the next page
            update_button = wait.until(
                EC.element_to_be_clickable((By.ID, "aaaa.HeaderView.UpdateBtn"))
            )
            update_button.click()
            self.logger.info("Clicked Update/View ERF button")

            # Wait for the first input field to be visible as a confirmation the page has loaded
            short_desc_element = wait.until(
                EC.visibility_of_element_located((By.ID, "aaaa.CreateOrderView.ShortDescInp"))
            )
            
            # Extract data fields using the now-visible elements
            erf_data.short_order_desc = short_desc_element.get_attribute("value")
            self.logger.info(f"Short Order Description: {erf_data.short_order_desc}")

            internal_order_element = self.driver.find_element(By.ID, "aaaa.CreateOrderView.InternalOrderInp")
            erf_data.internal_order = internal_order_element.get_attribute("value")
            erf_data.order_number = erf_data.internal_order
            self.logger.info(f"Internal Order: {erf_data.internal_order}")

            cost_center_element = self.driver.find_element(By.ID, "aaaa.CreateOrderView.CostCenterInp")
            erf_data.cost_center = cost_center_element.get_attribute("value")
            self.logger.info(f"Cost Center: {erf_data.cost_center}")
            
            return erf_data

        except TimeoutException:
            self.logger.error("Error extracting ERF data: Timed out waiting for 'Update/View' page elements to load.")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during ERF data extraction: {e}")
            return None
    
    def execute_vbs_script_1(self) -> Optional[Dict]:
        """
        Execute VBS Script 1 for additional ERF data extraction.
        Uses shared utility function to avoid code duplication.

        Returns:
            Extracted data if successful, None otherwise
        """
        vbs_script_path = self.config.VBS_ERF_SCRIPT_1
        self.logger.info("Executing VBS Script 1 for ERF data...")

        result = execute_vbs_script(vbs_script_path, timeout=30)

        if result and result['success']:
            # Parse the output into structured data
            parsed_data = parse_vbs_output_to_dict(result['output'])
            self.logger.info(f"VBS Script 1 extracted {len(parsed_data)} fields")
            return parsed_data
        else:
            self.logger.warning("VBS Script 1 execution failed or returned no data")
            return None
    
    def execute_erf_workflow(self, material_number: str, erf_search_term: str) -> Optional[Dict]:
        """
        Execute complete ERF workflow for a material.
        
        Args:
            material_number: The original material/part number for data association.
            erf_search_term: The term to use in the ERF search (could be RPM number).
            
        Returns:
            Extracted data if successful, None otherwise
        """
        self.logger.info(f"Starting ERF workflow for material '{material_number}' using search term '{erf_search_term}'")
        
        try:
            if not self.setup_webdriver(): return None
            if not self.navigate_to_erf_dashboard(): return None
            if not self.switch_to_erf_iframe(): return None
            
            erf_number = self.search_erf_by_term(erf_search_term)
            if not erf_number:
                return None
            
            erf_data = self.extract_erf_data()
            if not erf_data:
                return None
            
            erf_data.erf_number = erf_number
            erf_data.material = material_number
            
            vbs_data = self.execute_vbs_script_1()
            result_data = erf_data.to_dict()
            if vbs_data:
                result_data.update(vbs_data)
            
            self.logger.info("ERF workflow completed successfully")
            return result_data
            
        except Exception as e:
            self.logger.error(f"ERF workflow failed: {e}", exc_info=True)
            return None
        finally:
            self.cleanup_webdriver()
    
    def cleanup_webdriver(self):
        """Cleanup WebDriver resources."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("WebDriver cleaned up")
        except Exception as e:
            self.logger.warning(f"Error during WebDriver cleanup: {e}")
