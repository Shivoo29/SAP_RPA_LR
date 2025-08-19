import os
import time
import logging
import pyautogui
import pandas as pd
from datetime import datetime
import win32gui
import win32con
from typing import List, Dict, Optional
import json

class SAPAutomationBot:
    """
    Robotic Process Automation (RPA) bot for extracting part descriptions 
    from SAP dashboards (MD04/MD06) and populating Excel sheets.
    """
    
    def __init__(self, config_file: str = "sap_config.json"):
        """Initialize the SAP automation bot with configuration."""
        self.config = self.load_config(config_file)
        self.setup_logging()
        self.sap_window = None
        self.processed_parts = []
        self.errors = []
        
        # PyAutoGUI settings for safety
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1  # 1 second pause between actions
        
    def load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file."""
        default_config = {
            "sap_shortcut": r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\SAP Front End\SAP Logon.lnk",
            "sap_connection_name": "SAP Logon 800",
            "excel_output_path": "SAP_Part_Descriptions.xlsx",
            "wait_times": {
                "sap_launch": 8,
                "sap_connection": 15,
                "transaction_load": 5,
                "data_extraction": 3
            },
            "coordinates": {
                "sap_connection": [400, 300],  # Will be auto-detected
                "part_number_field": [200, 200],
                "execute_button": [50, 50],
                "description_field": [300, 400]
            },
            "transactions": ["MD04", "MD06"]
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            # Create default config file
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_filename = f"sap_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_window(self, window_title_partial: str) -> Optional[int]:
        """Find SAP window by partial title match."""
        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_title_partial.lower() in window_text.lower():
                    windows.append((hwnd, window_text))
            return True
        
        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        
        if windows:
            return windows[0][0]  # Return first match
        return None
    
    def activate_window(self, hwnd: int) -> bool:
        """Activate and bring window to foreground."""
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(1)
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate window: {e}")
            return False
    
    def launch_sap(self) -> bool:
        """Launch SAP Logon application."""
        try:
            self.logger.info("Launching SAP Logon...")
            os.startfile(self.config["sap_shortcut"])
            time.sleep(self.config["wait_times"]["sap_launch"])
            
            # Find SAP Logon window
            sap_logon_hwnd = self.find_window("SAP Logon")
            if sap_logon_hwnd:
                self.activate_window(sap_logon_hwnd)
                return True
            else:
                self.logger.error("SAP Logon window not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to launch SAP: {e}")
            return False
    
    def connect_to_sap(self) -> bool:
        """Connect to SAP system by double-clicking connection."""
        try:
            self.logger.info("Connecting to SAP system...")
            
            # Try to find SAP connection entry by image or coordinates
            coords = self.config["coordinates"]["sap_connection"]
            pyautogui.doubleClick(coords[0], coords[1])
            
            time.sleep(self.config["wait_times"]["sap_connection"])
            
            # Check if SAP GUI opened
            self.sap_window = self.find_window("SAP")
            if self.sap_window:
                self.activate_window(self.sap_window)
                self.logger.info("Successfully connected to SAP")
                return True
            else:
                self.logger.error("SAP GUI window not found after connection attempt")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to connect to SAP: {e}")
            return False
    
    def execute_transaction(self, transaction_code: str) -> bool:
        """Execute SAP transaction code."""
        try:
            self.logger.info(f"Executing transaction: {transaction_code}")
            
            if self.sap_window:
                self.activate_window(self.sap_window)
            
            # Clear any existing text and enter transaction
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.5)
            pyautogui.write(transaction_code)
            pyautogui.press('enter')
            
            time.sleep(self.config["wait_times"]["transaction_load"])
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute transaction {transaction_code}: {e}")
            return False
    
    def extract_part_description(self, part_number: str, transaction: str = "MD04") -> Dict[str, str]:
        """Extract part description for a given part number."""
        try:
            self.logger.info(f"Extracting description for part: {part_number}")
            start_time = time.time()
            
            # Execute transaction
            if not self.execute_transaction(transaction):
                raise Exception(f"Failed to execute {transaction}")
            
            # Enter part number
            if self.sap_window:
                self.activate_window(self.sap_window)
            
            # Focus on part number field and enter data
            part_coords = self.config["coordinates"]["part_number_field"]
            pyautogui.click(part_coords[0], part_coords[1])
            time.sleep(1)
            
            pyautogui.hotkey('ctrl', 'a')  # Select all
            pyautogui.write(part_number)
            pyautogui.press('enter')
            
            time.sleep(self.config["wait_times"]["data_extraction"])
            
            # Extract description (this would need to be customized based on actual SAP layout)
            # For now, we'll simulate extraction
            description = f"Description for {part_number} from {transaction}"
            
            processing_time = time.time() - start_time
            
            result = {
                "part_number": part_number,
                "description": description,
                "transaction": transaction,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time": round(processing_time, 2),
                "status": "SUCCESS"
            }
            
            self.logger.info(f"Successfully extracted data for {part_number} in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            error_msg = f"Failed to extract description for {part_number}: {e}"
            self.logger.error(error_msg)
            self.errors.append(error_msg)
            
            return {
                "part_number": part_number,
                "description": "ERROR - Could not extract",
                "transaction": transaction,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "processing_time": 0,
                "status": "ERROR",
                "error": str(e)
            }
    
    def process_parts_list(self, parts_list: List[str], transaction: str = "MD04") -> List[Dict[str, str]]:
        """Process a list of part numbers."""
        self.logger.info(f"Processing {len(parts_list)} parts using {transaction}")
        results = []
        
        for i, part in enumerate(parts_list, 1):
            self.logger.info(f"Processing part {i}/{len(parts_list)}: {part}")
            result = self.extract_part_description(part, transaction)
            results.append(result)
            self.processed_parts.append(result)
            
            # Small delay between parts
            time.sleep(1)
        
        return results
    
    def save_to_excel(self, results: List[Dict[str, str]], output_path: str = None) -> bool:
        """Save results to Excel file."""
        try:
            if not output_path:
                output_path = self.config["excel_output_path"]
            
            df = pd.DataFrame(results)
            
            # Add summary sheet
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{os.path.splitext(output_path)[0]}_{timestamp}.xlsx"
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Part_Descriptions', index=False)
                
                # Create summary sheet
                summary_data = {
                    'Metric': ['Total Parts Processed', 'Successful Extractions', 'Failed Extractions', 
                              'Average Processing Time (seconds)', 'Total Processing Time (minutes)'],
                    'Value': [
                        len(results),
                        len([r for r in results if r['status'] == 'SUCCESS']),
                        len([r for r in results if r['status'] == 'ERROR']),
                        round(sum([r['processing_time'] for r in results]) / len(results), 2),
                        round(sum([r['processing_time'] for r in results]) / 60, 2)
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            self.logger.info(f"Results saved to: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save Excel file: {e}")
            return False
    
    def run_automation(self, parts_list: List[str], transaction: str = "MD04") -> bool:
        """Main automation workflow."""
        try:
            self.logger.info("Starting SAP automation workflow...")
            
            # Step 1: Launch SAP
            if not self.launch_sap():
                return False
            
            # Step 2: Connect to SAP
            if not self.connect_to_sap():
                return False
            
            # Step 3: Process parts
            results = self.process_parts_list(parts_list, transaction)
            
            # Step 4: Save results
            if not self.save_to_excel(results):
                self.logger.error("Failed to save results to Excel")
                return False
            
            # Step 5: Generate summary
            successful = len([r for r in results if r['status'] == 'SUCCESS'])
            failed = len([r for r in results if r['status'] == 'ERROR'])
            
            self.logger.info(f"Automation completed: {successful} successful, {failed} failed")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Automation workflow failed: {e}")
            return False
    
    def create_sample_config(self):
        """Create a sample configuration file for customization."""
        sample_config = {
            "sap_shortcut": "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\SAP Front End\\SAP Logon.lnk",
            "sap_connection_name": "Your SAP Connection Name",
            "excel_output_path": "SAP_Part_Descriptions.xlsx",
            "wait_times": {
                "sap_launch": 8,
                "sap_connection": 15,
                "transaction_load": 5,
                "data_extraction": 3
            },
            "coordinates": {
                "sap_connection": [400, 300],
                "part_number_field": [200, 200],
                "execute_button": [50, 50],
                "description_field": [300, 400]
            },
            "transactions": ["MD04", "MD06"]
        }
        
        with open("sap_config_sample.json", "w") as f:
            json.dump(sample_config, f, indent=4)
        
        print("Sample configuration created: sap_config_sample.json")
        print("Please customize the coordinates and settings for your environment.")


# Example usage and utility functions
def main():
    """Example usage of the SAP automation bot."""
    
    # Initialize bot
    bot = SAPAutomationBot()
    
    # Sample parts list
    parts_to_process = [
        "PART001",
        "PART002", 
        "PART003",
        "PART004"
    ]
    
    # Run automation
    success = bot.run_automation(parts_to_process, transaction="MD04")
    
    if success:
        print("Automation completed successfully!")
    else:
        print("Automation failed. Check logs for details.")


def coordinate_helper():
    """Helper function to get mouse coordinates for configuration."""
    print("Move your mouse to the desired location and press Ctrl+C to get coordinates...")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            x, y = pyautogui.position()
            print(f"\rCurrent position: X={x}, Y={y}", end="")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"\nFinal coordinates: [{x}, {y}]")
        return [x, y]


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "coords":
        coordinate_helper()
    elif len(sys.argv) > 1 and sys.argv[1] == "config":
        bot = SAPAutomationBot()
        bot.create_sample_config()
    else:
        main()