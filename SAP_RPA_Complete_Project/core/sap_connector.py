"""
SAP Connector
=============
Handles SAP GUI connection and session management.
"""

import win32com.client
import pythoncom
import time
import logging
from typing import Optional


class SAPConnector:
    """Manages SAP GUI connection and session."""
    
    def __init__(self):
        """Initialize SAP connector."""
        self.logger = logging.getLogger(__name__)
        self.sap_gui_auto = None
        self.application = None
        self.connection = None
        self.session = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        Connect to SAP GUI and establish session.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info("Connecting to SAP GUI...")
            
            # Get SAP GUI Automation object
            self.sap_gui_auto = win32com.client.GetObject("SAPGUI")
            if not self.sap_gui_auto:
                raise Exception("SAP GUI not found. Please start SAP Logon.")
            
            # Get Application object
            self.application = self.sap_gui_auto.GetScriptingEngine
            if not self.application:
                raise Exception("SAP GUI Scripting not enabled.")
            
            # Get Connection
            if self.application.Children.Count > 0:
                self.connection = self.application.Children(0)
            else:
                raise Exception("No SAP connections available.")
            
            # Get Session
            if self.connection.Children.Count > 0:
                self.session = self.connection.Children(0)
            else:
                raise Exception("No active SAP session found.")
            
            # Verify connection
            session_info = self.session.Info
            system_name = session_info.SystemName
            client = session_info.Client
            user = session_info.User
            
            self.is_connected = True
            self.logger.info(f"Connected to SAP: {system_name} Client {client} User {user}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to SAP: {e}")
            self.is_connected = False
            return False
    
    def verify_connection(self) -> bool:
        """
        Verify that SAP session is still active.
        
        Returns:
            True if session is active, False otherwise
        """
        try:
            if not self.session:
                return False
            
            # Try to access session info
            info = self.session.Info
            system_name = info.SystemName
            return True
            
        except Exception as e:
            self.logger.error(f"Session verification failed: {e}")
            self.is_connected = False
            return False
    
    def get_session(self):
        """
        Get the current SAP session object.
        
        Returns:
            SAP session object or None
        """
        if self.verify_connection():
            return self.session
        return None
    
    def get_session_info(self) -> dict:
        """
        Get information about the current session.
        
        Returns:
            Dictionary with session information
        """
        if not self.verify_connection():
            return {}
        
        try:
            info = self.session.Info
            return {
                'system_name': info.SystemName,
                'client': info.Client,
                'user': info.User,
                'transaction': info.Transaction,
                'screen_number': info.ScreenNumber,
                'program': info.Program
            }
        except Exception as e:
            self.logger.error(f"Failed to get session info: {e}")
            return {}
    
    def disconnect(self):
        """Disconnect from SAP and cleanup resources."""
        try:
            self.logger.info("Disconnecting from SAP...")
            
            # Cleanup session objects
            self.session = None
            self.connection = None
            self.application = None
            self.sap_gui_auto = None
            
            self.is_connected = False
            self.logger.info("Disconnected from SAP")
            
        except Exception as e:
            self.logger.error(f"Error during disconnect: {e}")
    
    def navigate_to_transaction(self, tcode: str, wait_time: int = 3) -> bool:
        """
        Navigate to a specific SAP transaction.
        
        Args:
            tcode: Transaction code (e.g., 'MD04', 'KO03')
            wait_time: Time to wait after navigation (seconds)
            
        Returns:
            True if navigation successful
        """
        if not self.verify_connection():
            self.logger.error("Cannot navigate: Not connected to SAP")
            return False
        
        try:
            self.logger.info(f"Navigating to transaction {tcode}...")
            
            # Clear transaction field
            self.session.findById("wnd[0]/tbar[0]/okcd").text = ""
            time.sleep(0.5)
            
            # Enter transaction code
            self.session.findById("wnd[0]/tbar[0]/okcd").text = tcode
            self.session.findById("wnd[0]").sendVKey(0)  # Press Enter
            
            # Wait for transaction to load
            time.sleep(wait_time)
            
            # Verify transaction loaded
            current_tcode = self.session.Info.Transaction
            if current_tcode.upper() == tcode.upper():
                self.logger.info(f"Successfully navigated to {tcode}")
                return True
            else:
                self.logger.warning(f"Navigation uncertain. Current transaction: {current_tcode}")
                return True  # Continue anyway
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to {tcode}: {e}")
            return False
    
    def press_enter(self, wait_time: int = 2):
        """
        Press Enter key in SAP.
        
        Args:
            wait_time: Time to wait after pressing Enter
        """
        try:
            self.session.findById("wnd[0]").sendVKey(0)
            time.sleep(wait_time)
        except Exception as e:
            self.logger.error(f"Failed to press Enter: {e}")
    
    def press_f3(self, wait_time: int = 2):
        """
        Press F3 key (Back) in SAP.
        
        Args:
            wait_time: Time to wait after pressing F3
        """
        try:
            self.session.findById("wnd[0]").sendVKey(15)  # F3 key
            time.sleep(wait_time)
        except Exception as e:
            self.logger.error(f"Failed to press F3: {e}")
    
    def press_f7(self, wait_time: int = 2):
        """
        Press F7 key (Maximize) in SAP.
        
        Args:
            wait_time: Time to wait after pressing F7
        """
        try:
            self.session.findById("wnd[0]").sendVKey(7)  # F7 key
            time.sleep(wait_time)
        except Exception as e:
            self.logger.error(f"Failed to press F7: {e}")
    
    def check_for_sap_errors(self) -> Optional[str]:
        """
        Check for SAP error messages.
        
        Returns:
            Error message if found, None otherwise
        """
        try:
            # Check status bar
            try:
                status_bar = self.session.findById("wnd[0]/sbar")
                if status_bar and hasattr(status_bar, 'text'):
                    status_text = status_bar.text.strip()
                    if status_text and any(keyword in status_text.lower() 
                                          for keyword in ['error', 'not found', 'does not exist']):
                        return status_text
            except:
                pass
            
            # Check for error popup windows
            for window_id in ["wnd[1]", "wnd[2]"]:
                try:
                    window = self.session.findById(window_id)
                    if window and hasattr(window, 'text'):
                        window_text = window.text
                        if any(keyword in window_text.lower() 
                              for keyword in ['error', 'fehler', 'warning']):
                            # Try to close the error window
                            try:
                                window.sendVKey(0)  # Press Enter to close
                            except:
                                pass
                            return window_text
                except:
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Error checking for SAP errors: {e}")
        
        return None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
