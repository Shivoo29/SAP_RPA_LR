import win32com.client
import win32api
import win32con
import win32gui
import time
import threading
from datetime import datetime
import os

class SAPClickTracker:
    def __init__(self):
        self.sap_gui_auto = None
        self.application = None
        self.connection = None
        self.session = None
        self.tracking = False
        self.click_log = []
        self.sap_window_handle = None
        self.last_click_time = 0
        
    def connect_to_sap(self):
        """Connect to SAP GUI application"""
        try:
            # Connect to SAP GUI
            self.sap_gui_auto = win32com.client.GetObject("SAPGUI")
            self.application = self.sap_gui_auto.GetScriptingEngine
            
            if self.application.Children.Count == 0:
                print("No SAP GUI connections found. Please open SAP GUI first.")
                return False
                
            # Get the first connection
            self.connection = self.application.Children(0)
            
            if self.connection.Children.Count == 0:
                print("No active SAP sessions found. Please log in to SAP.")
                return False
                
            # Get the first session
            self.session = self.connection.Children(0)
            
            # Find SAP GUI window handle
            self.find_sap_window()
            
            print(f"Connected to SAP session: {self.session.Info.Transaction}")
            return True
            
        except Exception as e:
            print(f"Error connecting to SAP: {str(e)}")
            print("Make sure SAP GUI is running and scripting is enabled.")
            return False
    
    def find_sap_window(self):
        """Find the SAP GUI window handle"""
        def enum_windows_proc(hwnd, lParam):
            window_text = win32gui.GetWindowText(hwnd)
            if "SAP" in window_text and "Logon" not in window_text:
                self.sap_window_handle = hwnd
                return False
            return True
        
        win32gui.EnumWindows(enum_windows_proc, 0)
    
    def get_element_at_position(self, x, y):
        """Get SAP element at specific screen coordinates"""
        try:
            if not self.session or not self.session.ActiveWindow:
                return None
            
            # Convert screen coordinates to SAP window coordinates
            window_rect = win32gui.GetWindowRect(self.sap_window_handle)
            relative_x = x - window_rect[0]
            relative_y = y - window_rect[1]
            
            # Try to find element at position using SAP GUI scripting
            try:
                element = self.session.ActiveWindow.FindByPosition(relative_x, relative_y)
                return element
            except:
                # Alternative method: check all elements for position match
                return self.find_element_by_coordinates(relative_x, relative_y)
                
        except Exception as e:
            return None
    
    def find_element_by_coordinates(self, x, y):
        """Find element by checking coordinates of all elements"""
        try:
            def search_children(parent):
                try:
                    for i in range(parent.Children.Count):
                        child = parent.Children(i)
                        try:
                            if hasattr(child, 'ScreenLeft') and hasattr(child, 'ScreenTop'):
                                if (child.ScreenLeft <= x <= child.ScreenLeft + getattr(child, 'Width', 0) and
                                    child.ScreenTop <= y <= child.ScreenTop + getattr(child, 'Height', 0)):
                                    return child
                        except:
                            pass
                        
                        # Recursively search children
                        result = search_children(child)
                        if result:
                            return result
                except:
                    pass
                return None
            
            return search_children(self.session.ActiveWindow)
        except:
            return None
    
    def get_element_info(self, element, click_x, click_y):
        """Extract information from a SAP GUI element"""
        try:
            info = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'click_x': click_x,
                'click_y': click_y,
                'id': getattr(element, 'Id', 'N/A'),
                'name': getattr(element, 'Name', 'N/A'),
                'type': getattr(element, 'Type', 'N/A'),
                'text': getattr(element, 'Text', 'N/A'),
                'tooltip': getattr(element, 'Tooltip', 'N/A'),
                'screen_left': getattr(element, 'ScreenLeft', 'N/A'),
                'screen_top': getattr(element, 'ScreenTop', 'N/A'),
                'width': getattr(element, 'Width', 'N/A'),
                'height': getattr(element, 'Height', 'N/A')
            }
            
            # Try to get additional properties if available
            try:
                info['changeable'] = getattr(element, 'Changeable', 'N/A')
                info['modified'] = getattr(element, 'Modified', 'N/A')
                info['value'] = getattr(element, 'Value', 'N/A')
                info['key'] = getattr(element, 'Key', 'N/A')
            except:
                pass
                
            return info
        except Exception as e:
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'click_x': click_x,
                'click_y': click_y,
                'error': f"Could not extract element info: {str(e)}"
            }
    
    def mouse_click_handler(self):
        """Handle mouse click events"""
        last_click_state = False
        
        while self.tracking:
            try:
                # Check for left mouse button click
                current_click_state = win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000
                current_time = time.time()
                
                # Detect click (button pressed and wasn't pressed before)
                if current_click_state and not last_click_state:
                    # Avoid duplicate clicks (debounce)
                    if current_time - self.last_click_time > 0.2:  # 200ms debounce
                        self.last_click_time = current_time
                        
                        # Get current mouse position
                        x, y = win32gui.GetCursorPos()
                        
                        # Check if click is within SAP window
                        if self.sap_window_handle and self.is_click_in_sap_window(x, y):
                            self.handle_sap_click(x, y)
                
                last_click_state = current_click_state
                time.sleep(0.01)  # Check every 10ms for responsiveness
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                time.sleep(0.1)
    
    def is_click_in_sap_window(self, x, y):
        """Check if click coordinates are within SAP window"""
        try:
            window_rect = win32gui.GetWindowRect(self.sap_window_handle)
            return (window_rect[0] <= x <= window_rect[2] and 
                    window_rect[1] <= y <= window_rect[3])
        except:
            return False
    
    def handle_sap_click(self, x, y):
        """Handle a click within SAP window"""
        try:
            # Get element at click position
            element = self.get_element_at_position(x, y)
            
            if element:
                element_info = self.get_element_info(element, x, y)
                element_info['action'] = 'CLICKED'
                
                self.click_log.append(element_info)
                
                # Print real-time feedback
                print(f"Clicked: {element_info['id']} | Type: {element_info['type']} | Name: {element_info['name']} | Position: ({x}, {y})")
            else:
                # Log click even if no element found
                click_info = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    'action': 'CLICKED',
                    'click_x': x,
                    'click_y': y,
                    'id': 'UNKNOWN_ELEMENT',
                    'type': 'Unknown',
                    'name': 'No element found at this position'
                }
                self.click_log.append(click_info)
                print(f"Clicked at position ({x}, {y}) - No SAP element identified")
                
        except Exception as e:
            print(f"Error handling click: {str(e)}")
    
    def start_tracking(self):
        """Start the click tracking process"""
        if not self.connect_to_sap():
            return False
            
        self.tracking = True
        
        # Start click tracking in a separate thread
        tracking_thread = threading.Thread(target=self.mouse_click_handler)
        tracking_thread.daemon = True
        tracking_thread.start()
        
        return True
    
    def stop_tracking(self):
        """Stop the click tracking process"""
        self.tracking = False
        print("Stopping click tracking...")
    
    def save_log_to_file(self, filename=None):
        """Save the click interaction log to a text file"""
        if filename is None:
            filename = f"sap_click_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("SAP Click Interaction Log\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total clicks recorded: {len(self.click_log)}\n\n")
                
                for i, entry in enumerate(self.click_log, 1):
                    f.write(f"Click #{i}:\n")
                    f.write("-" * 30 + "\n")
                    
                    for key, value in entry.items():
                        f.write(f"{key.capitalize().replace('_', ' ')}: {value}\n")
                    f.write("\n")
            
            print(f"Log saved to: {os.path.abspath(filename)}")
            return filename
            
        except Exception as e:
            print(f"Error saving log: {str(e)}")
            return None
    
    def print_summary(self):
        """Print a summary of recorded clicks"""
        if not self.click_log:
            print("No clicks recorded.")
            return
            
        print(f"\nSummary: {len(self.click_log)} clicks recorded")
        print("-" * 50)
        
        # Group by field ID
        field_counts = {}
        for entry in self.click_log:
            field_id = entry.get('id', 'Unknown')
            field_counts[field_id] = field_counts.get(field_id, 0) + 1
        
        print("Most clicked fields:")
        for field_id, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {field_id}: {count} times")

def main():
    """Main function to run the SAP click tracker"""
    tracker = SAPClickTracker()
    
    try:
        print("SAP Click Tracker")
        print("=================")
        print("This tool will track your mouse clicks on SAP GUI fields.")
        print("Make sure SAP GUI is open and you're logged in before starting.\n")
        
        if tracker.start_tracking():
            print("Click tracking started! Click on SAP GUI elements...")
            print("Press Enter to stop tracking and save the log.\n")
            
            # Wait for user to press Enter
            input()
            
            tracker.stop_tracking()
            tracker.print_summary()
            
            # Save the log
            filename = tracker.save_log_to_file()
            if filename:
                print(f"Click interaction log saved to: {filename}")
            
        else:
            print("Failed to start tracking. Please check SAP GUI connection.")
            
    except KeyboardInterrupt:
        print("\nTracking interrupted by user.")
        tracker.stop_tracking()
        tracker.save_log_to_file()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        tracker.stop_tracking()

if __name__ == "__main__":
    main()