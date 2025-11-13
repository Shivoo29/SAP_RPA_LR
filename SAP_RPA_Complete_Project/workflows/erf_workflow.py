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

from config import Config
from data.data_models import ERFData


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
    
    def search_erf_by_material(self, material_number: str) -> Optional[str]:
        """
        Search for ERF by material number.
        
        Args:
            material_number: Material/part number
            
        Returns:
            ERF number if found, None otherwise
        """
        try:
            self.logger.info(f"Searching ERF for material: {material_number}")
            
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
            erf_input.send_keys(material_number)
            self.logger.info(f"Entered material number: {material_number}")
            
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
                
                return material_number  # Return as ERF number
                
            except Exception:
                self.logger.warning("No results found for material")
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
        try:
            self.logger.info("Extracting ERF data...")
            
            wait = WebDriverWait(self.driver, self.config.WEB_TIMEOUT)
            
            # Click "Update/View ERF" button
            update_button = wait.until(
                EC.element_to_be_clickable((By.ID, "aaaa.HeaderView.UpdateBtn"))
            )
            update_button.click()
            self.logger.info("Clicked Update/View ERF button")
            
            time.sleep(2)
            
            # Extract data fields
            erf_data = ERFData()
            
            try:
                short_order_desc = self.driver.find_element(
                    By.ID, "aaaa.CreateOrderView.ShortDescInp"
                ).get_attribute("value")
                erf_data.short_order_desc = short_order_desc
                self.logger.info(f"Short Order Description: {short_order_desc}")
            except:
                self.logger.warning("Could not extract Short Order Description")
            
            try:
                internal_order = self.driver.find_element(
                    By.ID, "aaaa.CreateOrderView.InternalOrderInp"
                ).get_attribute("value")
                erf_data.internal_order = internal_order
                erf_data.order_number = internal_order  # Use for KO03
                self.logger.info(f"Internal Order: {internal_order}")
            except:
                self.logger.warning("Could not extract Internal Order")
            
            try:
                cost_center = self.driver.find_element(
                    By.ID, "aaaa.CreateOrderView.CostCenterInp"
                ).get_attribute("value")
                erf_data.cost_center = cost_center
                self.logger.info(f"Cost Center: {cost_center}")
            except:
                self.logger.warning("Could not extract Cost Center")
            
            return erf_data
            
        except Exception as e:
            self.logger.error(f"Error extracting ERF data: {e}")
            return None
    
    def execute_vbs_script_1(self) -> Optional[Dict]:
        """
        Execute VBS Script 1 for additional ERF data extraction.
        
        Returns:
            Extracted data if successful, None otherwise
        """
        try:
            vbs_script_path = self.config.VBS_ERF_SCRIPT_1
            
            if not vbs_script_path.exists():
                self.logger.warning(f"VBS script not found: {vbs_script_path}")
                return None
            
            self.logger.info("Executing VBS Script 1...")
            
            import subprocess
            
            result = subprocess.run(
                ['cscript', '//nologo', str(vbs_script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                self.logger.info(f"VBS Script 1 output: {output}")
                
                # TODO: Parse VBS output into structured data
                return {'vbs_1_output': output}
            else:
                self.logger.error(f"VBS Script 1 failed: {result.stderr}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing VBS Script 1: {e}")
            return None
    
    def execute_erf_workflow(self, material_number: str) -> Optional[Dict]:
        """
        Execute complete ERF workflow for a material.
        
        Args:
            material_number: Material/part number
            
        Returns:
            Extracted data if successful, None otherwise
        """
        self.logger.info("="*60)
        self.logger.info(f"Starting ERF workflow for: {material_number}")
        self.logger.info("="*60)
        
        try:
            # Setup WebDriver
            if not self.setup_webdriver():
                return None
            
            # Navigate to ERF Dashboard
            if not self.navigate_to_erf_dashboard():
                return None
            
            # Switch to iframe
            if not self.switch_to_erf_iframe():
                return None
            
            # Search for material
            erf_number = self.search_erf_by_material(material_number)
            if not erf_number:
                return None
            
            # Extract data
            erf_data = self.extract_erf_data()
            if not erf_data:
                return None
            
            # Set ERF and material numbers
            erf_data.erf_number = erf_number
            erf_data.material = material_number
            
            # Execute VBS Script 1 for additional data
            vbs_data = self.execute_vbs_script_1()
            if vbs_data:
                result_data = erf_data.to_dict()
                result_data.update(vbs_data)
            else:
                result_data = erf_data.to_dict()
            
            self.logger.info("ERF workflow completed successfully")
            return result_data
            
        except Exception as e:
            self.logger.error(f"ERF workflow failed: {e}")
            return None
        finally:
            # Cleanup
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
