import os
import pyautogui
import time

# Step 1: Launch SAP Logon using the shortcut
sap_shortcut = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\SAP Front End\SAP Logon.lnk"
os.startfile(sap_shortcut)

# Step 2: Wait for SAP Logon to open
time.sleep(5)

# Step 3: Double-click on SAP Logon 800 entry (adjust coordinates)
pyautogui.doubleClick(x=300, y=400)

# Step 4: Wait for SAP GUI to load
time.sleep(10)

# Step 5: Type transaction code
pyautogui.write('md04')
pyautogui.press('enter')
