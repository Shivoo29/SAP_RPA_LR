import win32com.client
import time
import threading
from datetime import datetime
import os

class SAPFieldTracker:
    def __init__(self):
        self.sap_gui_auto = None
        self.application = None
        self.connection = None
        self.session = None
        self.tracking = False
        self.field_log = []
        self.last_focused_element = None
        
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
            print(f"Connected to SAP session: {self.session.Info.Transaction}")
            return True
            
        except Exception as e:
            print(f"Error connecting to SAP: {str(e)}")
            print("Make sure SAP GUI is running and scripting is enabled.")
            return False
    
    def get_element_info(self, element):
        """Extract information from a SAP GUI element"""
        try:
            info = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
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
            except:
                pass
                
            return info
        except Exception as e:
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                'error': f"Could not extract element info: {str(e)}"
            }
    
    def track_focus_changes(self):
        """Monitor focus changes in SAP GUI"""
        print("Starting focus tracking... Press Ctrl+C to stop.")
        
        while self.tracking:
            try:
                if self.session and self.session.ActiveWindow:
                    # Get the currently focused element
                    try:
                        current_element = self.session.ActiveWindow.ActiveControl
                        
                        if current_element and current_element != self.last_focused_element:
                            element_info = self.get_element_info(current_element)
                            element_info['action'] = 'FOCUS_CHANGED'
                            
                            self.field_log.append(element_info)
                            self.last_focused_element = current_element
                            
                            # Print real-time feedback
                            print(f"Focus: {element_info['id']} | Type: {element_info['type']} | Name: {element_info['name']}")
                            
                    except Exception as e:
                        # Silently continue if we can't get the active control
                        pass
                        
                time.sleep(0.1)  # Check every 100ms
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Tracking error: {str(e)}")
                time.sleep(1)
    
    def start_tracking(self):
        """Start the field tracking process"""
        if not self.connect_to_sap():
            return False
            
        self.tracking = True
        
        # Start tracking in a separate thread
        tracking_thread = threading.Thread(target=self.track_focus_changes)
        tracking_thread.daemon = True
        tracking_thread.start()
        
        return True
    
    def stop_tracking(self):
        """Stop the field tracking process"""
        self.tracking = False
        print("Stopping field tracking...")
    
    def save_log_to_file(self, filename=None):
        """Save the field interaction log to a text file"""
        if filename is None:
            filename = f"sap_field_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("SAP Field Interaction Log\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total interactions recorded: {len(self.field_log)}\n\n")
                
                for i, entry in enumerate(self.field_log, 1):
                    f.write(f"Entry #{i}:\n")
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
        """Print a summary of recorded interactions"""
        if not self.field_log:
            print("No field interactions recorded.")
            return
            
        print(f"\nSummary: {len(self.field_log)} field interactions recorded")
        print("-" * 50)
        
        # Group by field ID
        field_counts = {}
        for entry in self.field_log:
            field_id = entry.get('id', 'Unknown')
            field_counts[field_id] = field_counts.get(field_id, 0) + 1
        
        print("Most accessed fields:")
        for field_id, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {field_id}: {count} times")

def main():
    """Main function to run the SAP field tracker"""
    tracker = SAPFieldTracker()
    
    try:
        print("SAP Field Tracker")
        print("================")
        print("This tool will track your field interactions in SAP GUI.")
        print("Make sure SAP GUI is open and you're logged in before starting.\n")
        
        if tracker.start_tracking():
            print("Tracking started! Interact with SAP GUI fields...")
            print("Press Enter to stop tracking and save the log.\n")
            
            # Wait for user to press Enter
            input()
            
            tracker.stop_tracking()
            tracker.print_summary()
            
            # Save the log
            filename = tracker.save_log_to_file()
            if filename:
                print(f"Field interaction log saved to: {filename}")
            
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