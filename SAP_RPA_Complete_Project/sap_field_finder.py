
SAP Field Finder
================
A helper script to identify the IDs of SAP GUI elements for configuration.

Instructions:
1. Run this script in a terminal.
2. It will connect to your active SAP session.
3. In the SAP window, navigate to the screen containing the element you want to identify.
4. Double-click on the specific field (e.g., an input box, a button, a table cell).
5. The script will print the unique ID of that element to the console.
6. Copy the ID and paste it into your config.py file.
7. The script will ask if you want to find another ID. Type 'y' to continue or 'n' to exit.
"""

import win32com.client
import time
import sys

# --- Event Handler Class ---
class SAPFEEventHandler:
    def __init__(self, session):
        self.session = session
        self.last_event_id = None
        self.event_fired = False

    def OnDoubleClick(self, component, item, col):
        """Handles the DoubleClick event from the SAP GUI Scripting API."""
        try:
            # Get the component that was double-clicked
            element = self.session.FindById(component.id)
            print("\n" + "="*60)
            print("EVENT: DoubleClick Detected!")
            print(f"Element ID: {element.id}")
            print("="*60)
            print("--> Copy the Element ID above and paste it into your config.py file.\n")
            self.last_event_id = element.id
            self.event_fired = True
        except Exception as e:
            print(f"\nError getting element ID: {e}")
            self.event_fired = True # Stop waiting even if there's an error

    def OnError(self, component, item, col):
        pass

    def OnAction(self, component, item, col):
        pass

def main():
    """Main function to run the field finder."""
    print("--- SAP Field Finder ---")
    
    try:
        print("1. Connecting to SAP GUI...")
        sap_gui_auto = win32com.client.GetObject("SAPGUI")
        if not sap_gui_auto:
            print("   ERROR: SAP Logon is not running.")
            sys.exit(1)

        application = sap_gui_auto.GetScriptingEngine
        if not application:
            print("   ERROR: SAP GUI Scripting is not enabled.")
            sys.exit(1)

        connection = application.Children(0)
        if not connection:
            print("   ERROR: No active SAP connection found.")
            sys.exit(1)
            
        session = connection.Children(0)
        if not session:
            print("   ERROR: No active SAP session found.")
            sys.exit(1)
            
        print("   ✓ Successfully connected to SAP session.")
        print("2. Attaching event listener...")

        # Create and attach the event handler
        handler = SAPFEEventHandler(session)
        win32com.client.WithEvents(session, handler)
        
        print("   ✓ Event listener attached.")
        print("\n" + "="*60)
        print("SAP Field Finder is now ACTIVE.")
        print("Navigate in your SAP window and DOUBLE-CLICK on any field to get its ID.")
        print("="*60)

        while True:
            handler.event_fired = False
            print("\nWaiting for you to double-click on a field in SAP...")
            
            # Wait for the event to fire. This loop just keeps the script alive.
            while not handler.event_fired:
                time.sleep(0.5)

            while True:
                another = input("Find another field? (y/n): ").lower().strip()
                if another in ['y', 'n']:
                    break
            
            if another == 'n':
                print("Exiting SAP Field Finder.")
                break

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure SAP Logon is running and you are logged into a session.")
    finally:
        input("Press Enter to exit.")

if __name__ == "__main__":
    main()
