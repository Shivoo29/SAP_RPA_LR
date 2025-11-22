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
        
    def connect(self, session_index: int = 0, create_new: bool = False) -> bool:
        """
        Connect to SAP GUI and establish session.

        Args:
            session_index: Index of session to use (0-5). Used for parallel processing.
            create_new: If True, creates a new session instead of using existing one

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to SAP GUI (session_index={session_index}, create_new={create_new})...")

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

            # Get or Create Session
            if create_new:
                # NOTE: Parallel processing with multiprocessing is disabled due to COM limitations
                # CreateSession() doesn't work reliably across process boundaries
                raise Exception("Parallel processing is currently disabled. Use sequential mode instead.")
            elif session_index < self.connection.Children.Count:
                # Use existing session at specified index
                self.session = self.connection.Children(session_index)
                self.logger.info(f"✓ Using existing session {session_index}")
            else:
                # Session doesn't exist
                raise Exception(f"Session {session_index} not found!")

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
        Navigate to a specific SAP transaction using the most robust method.
        This method mimics a user by setting focus, clearing the field,
        and attempting to press the dedicated Enter button before falling back.
        
        Args:
            tcode: Transaction code (e.g., 'MD04', 'KO03'). Should NOT include /n.
            
        Returns:
            True if navigation is successful.
        """
        if not self.verify_connection():
            self.logger.error("Cannot navigate: Not connected to SAP")
            return False
        
        command_to_run = f"/n{tcode}"
        self.logger.info(f"Navigating to transaction using robust method: '{command_to_run}'...")
        
        try:
            ok_code_field = self.session.findById("wnd[0]/tbar[0]/okcd")
            
            # 1. Set focus and clear the field to ensure a clean state
            ok_code_field.setFocus()
            ok_code_field.text = ""
            
            # 2. Set the command text
            ok_code_field.text = command_to_run
            
            # 3. Try to press the dedicated 'Enter' button first (more reliable)
            try:
                enter_button = self.session.findById("wnd[0]/tbar[0]/btn[0]")
                enter_button.press()
            except:
                # 4. Fallback to sending VKey 0 if the button isn't found
                self.logger.debug("Enter button (btn[0]) not found, falling back to VKey 0.")
                self.session.findById("wnd[0]").sendVKey(0)

            # 5. Wait for the screen to change. This is critical.
            self.logger.debug(f"Waiting {wait_time} seconds for screen to render...")
            time.sleep(wait_time)
            
            # 6. Verify that the navigation was successful
            current_tcode = self.session.Info.Transaction
            if current_tcode.upper() == tcode.upper():
                self.logger.info(f"✓ Successfully navigated to {tcode}")
                return True
            else:
                # This can happen if a popup appeared and was dismissed.
                # The command might still be pending. We send one more Enter.
                self.logger.warning(f"Navigation to {tcode} resulted in a different screen ({current_tcode}). Sending one more Enter to proceed.")
                self.press_enter(wait_time=2)
                current_tcode = self.session.Info.Transaction
                if current_tcode.upper() == tcode.upper():
                    self.logger.info(f"✓ Successfully navigated to {tcode} after second Enter.")
                    return True
                else:
                    self.logger.error(f"✗ Failed to navigate to {tcode}. Final screen is {current_tcode}.")
                    return False
                
        except Exception as e:
            self.logger.error(f"Fatal error during robust navigation to {tcode}: {e}", exc_info=True)
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

    def execute_sap_query(self, wait_time: int = 3) -> bool:
        """
        Execute a SAP query by pressing Enter and checking for errors.
        This is a shared method to avoid duplication across transaction handlers.

        Args:
            wait_time: Time to wait after pressing Enter (default: 3)

        Returns:
            True if successful, False if errors were detected
        """
        try:
            self.press_enter(wait_time=wait_time)

            # Check for SAP errors
            error_msg = self.check_for_sap_errors()
            if error_msg:
                self.logger.warning(f"SAP error after query: {error_msg}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to execute SAP query: {e}")
            return False
    
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

    def get_status_bar_info(self) -> dict:
        """
        Get comprehensive status bar information.

        Returns:
            Dictionary with status bar details:
            - 'text': Status bar message text
            - 'type': Message type (error, warning, info, success, none)
            - 'message_id': SAP message ID if available
        """
        result = {
            'text': '',
            'type': 'none',
            'message_id': ''
        }

        try:
            status_bar = self.session.findById("wnd[0]/sbar")
            if not status_bar:
                return result

            # Get status bar text
            if hasattr(status_bar, 'text'):
                result['text'] = status_bar.text.strip()

            # Get message type
            if hasattr(status_bar, 'MessageType'):
                msg_type = status_bar.MessageType
                type_mapping = {
                    'E': 'error',
                    'W': 'warning',
                    'I': 'info',
                    'S': 'success',
                    'A': 'abort'
                }
                result['type'] = type_mapping.get(msg_type, 'unknown')

            # Get message ID
            if hasattr(status_bar, 'MessageId'):
                result['message_id'] = status_bar.MessageId

            # Fallback: detect type from text if MessageType not available
            if result['type'] == 'none' and result['text']:
                text_lower = result['text'].lower()
                if any(kw in text_lower for kw in ['error', 'fehler', 'not found', 'does not exist']):
                    result['type'] = 'error'
                elif any(kw in text_lower for kw in ['warning', 'warnung']):
                    result['type'] = 'warning'
                elif any(kw in text_lower for kw in ['success', 'erfolgreich']):
                    result['type'] = 'success'
                elif result['text']:
                    result['type'] = 'info'

        except Exception as e:
            self.logger.debug(f"Error getting status bar info: {e}")

        return result

    def has_data_in_screen(self) -> bool:
        """
        Check if the current screen has data (not empty result).

        Returns:
            True if screen appears to have data, False if empty/error
        """
        try:
            # Check status bar for "no data" messages
            status_info = self.get_status_bar_info()

            if status_info['type'] == 'error':
                self.logger.debug(f"Screen has error: {status_info['text']}")
                return False

            text_lower = status_info['text'].lower()
            no_data_keywords = [
                'no data',
                'keine daten',
                'not found',
                'nicht gefunden',
                'does not exist',
                'existiert nicht',
                'no items',
                'keine einträge'
            ]

            if any(kw in text_lower for kw in no_data_keywords):
                self.logger.debug(f"Screen indicates no data: {status_info['text']}")
                return False

            # If we get here, assume data exists
            return True

        except Exception as e:
            self.logger.debug(f"Error checking for screen data: {e}")
            # Default to True to avoid false negatives
            return True

    def get_screen_info(self) -> dict:
        """
        Get information about the current SAP screen state.

        Returns:
            Dictionary with screen information:
            - 'transaction': Current transaction code
            - 'screen_number': Screen number
            - 'program': Program name
            - 'status_bar': Status bar info dict
        """
        info = {
            'transaction': '',
            'screen_number': '',
            'program': '',
            'status_bar': {}
        }

        try:
            # Get transaction code
            if hasattr(self.session.Info, 'Transaction'):
                info['transaction'] = self.session.Info.Transaction

            # Get screen number
            if hasattr(self.session.Info, 'ScreenNumber'):
                info['screen_number'] = str(self.session.Info.ScreenNumber)

            # Get program name
            if hasattr(self.session.Info, 'Program'):
                info['program'] = self.session.Info.Program

            # Get status bar info
            info['status_bar'] = self.get_status_bar_info()

        except Exception as e:
            self.logger.debug(f"Error getting screen info: {e}")

        return info
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
