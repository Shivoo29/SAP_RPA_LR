# 🔧 SAP RPA - Troubleshooting Guide

## Common Issues & Solutions

### 1. SAP Connection Issues

#### Issue: "Failed to connect to SAP"
**Symptoms:**
- Connection button shows error
- Status remains "❌ Not Connected"

**Solutions:**
```
✓ Check 1: Is SAP Logon running?
  → Open SAP Logon application
  → Log in to your SAP system

✓ Check 2: Is SAP GUI Scripting enabled?
  → In SAP: Settings → Options → Accessibility & Scripting
  → Enable "Enable scripting"
  → Restart SAP

✓ Check 3: Python COM libraries installed?
  → Run: pip install pywin32
  → If still fails, run: python -m win32com.client.makepy

✓ Check 4: Run as Administrator?
  → Right-click python.exe → Run as Administrator
  → Or run Command Prompt as Admin
```

#### Issue: "No active SAP session found"
**Symptoms:**
- Connection works initially
- Later shows "session not found"

**Solutions:**
```
✓ Don't close SAP window
✓ Don't log out of SAP
✓ Keep SAP window in background (minimized is OK)
✓ Reconnect if SAP session times out
```

---

### 2. Field ID Issues

#### Issue: "Field not found: wnd[0]/usr/..."
**Symptoms:**
- Automation stops with field error
- Log shows "Field ID not found"

**Solutions:**
```
Step 1: Verify field ID
  → Run sap_field_finder.py
  → Navigate to the transaction
  → Click "Scan All Fields"
  → Find the correct field ID

Step 2: Update config.py
  → Open config.py
  → Find the field section (MD04_FIELDS, etc.)
  → Replace with correct field ID from step 1

Step 3: Test again
  → Restart application
  → Try single material first
```

**Example Fix:**
```python
# BEFORE (incorrect)
MD04_FIELDS = {
    "material_field": "wnd[0]/usr/ctxtRM61R-MATNR",  # ❌ Wrong
}

# AFTER (corrected with field finder)
MD04_FIELDS = {
    "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-MATNR",  # ✓ Correct
}
```

#### Issue: "Data extraction returns empty values"
**Symptoms:**
- Automation completes successfully
- But extracted data is blank

**Solutions:**
```
✓ Verify extraction field IDs
  → Use field finder on the data screen
  → Update EXTRACTION_FIELDS in config.py

✓ Check timing
  → Increase WAIT_TIME_AFTER_QUERY in config.py
  → Default is 2 seconds, try 3-4 seconds

✓ Verify screen elements
  → Check if MatRes is actually present
  → Check if F7 press maximizes correctly
```

---

### 3. Multi-Plant Search Issues

#### Issue: "Not found in any plant" but material exists
**Symptoms:**
- Search tries all plants
- Says "not found" but you know it exists

**Solutions:**
```
✓ Check 1: Correct plants configured?
  → Open config.py
  → Verify AVAILABLE_PLANTS = ['1000', '2000', '1020', '1900']
  → Make sure plant where material exists is in list

✓ Check 2: Plant field ID correct?
  → Verify plant_field in MD04_FIELDS
  → Use field finder to get correct ID

✓ Check 3: MRP Area correct?
  → Try different MRP Area
  → Default is '1000', try others

✓ Check 4: Manual test
  → Manually open MD04 in SAP
  → Enter material and plant
  → Verify MatRes actually appears
  → If not, material may not exist in that plant
```

#### Issue: "Stuck on plant 1000, doesn't try other plants"
**Symptoms:**
- Always tries only plant 1000
- Never moves to next plant

**Solutions:**
```
✓ Check multi-plant flag
  → In config.py: ENABLE_MULTI_PLANT_SEARCH = True

✓ Verify plant selection in GUI
  → All desired plants should be checked
  → At least 2 plants should be selected

✓ Check plant switching logic
  → Look at logs/
  → Should see: "Trying plant 2000..." after 1000 fails
  → If not, field ID for plant field may be wrong
```

---

### 4. ERF Dashboard Issues

#### Issue: "ERF Dashboard not loading"
**Symptoms:**
- Browser launches but doesn't navigate
- Timeout errors

**Solutions:**
```
✓ Check 1: Edge WebDriver installed?
  → Download from: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
  → Extract to: C:\Program Files\edgedriver_win64\
  → Update EDGE_DRIVER_PATH in config.py

✓ Check 2: Correct URL?
  → Verify ERF_DASHBOARD_URL in config.py
  → Test URL manually in browser
  → Make sure you can log in

✓ Check 3: Network/VPN?
  → ERF Dashboard may require VPN
  → Ensure VPN is connected
  → Try accessing URL manually first

✓ Check 4: Timeout too short?
  → Increase WEB_TIMEOUT in config.py
  → Default is 30, try 60 seconds
```

#### Issue: "Cannot find element on ERF Dashboard"
**Symptoms:**
- Page loads but can't find buttons/fields
- Element not found errors

**Solutions:**
```
✓ Element IDs may have changed
  → Open ERF Dashboard in browser
  → Press F12 (Developer Tools)
  → Inspect the element
  → Find the correct ID
  → Update in workflows/erf_workflow.py

✓ Check iframe switching
  → ERF may use different iframe structure
  → Verify iframe IDs in erf_workflow.py:
    - contentAreaFrame
    - isolatedWorkArea
  → Update if different in your system

✓ Increase wait times
  → Add more time.sleep() calls
  → Page may load slowly
```

**Example Fix:**
```python
# workflows/erf_workflow.py

# BEFORE
plant_input = wait.until(
    EC.element_to_be_clickable((By.ID, "aaaa.RpmDashboardView.PlantsDdbk"))
)

# AFTER (if ID changed)
plant_input = wait.until(
    EC.element_to_be_clickable((By.ID, "YOUR_NEW_ELEMENT_ID"))
)
```

---

### 5. VBS Script Issues

#### Issue: "VBS Script failed to execute"
**Symptoms:**
- Error when trying to run VBS
- Empty VBS output

**Solutions:**
```
✓ Check 1: VBS file exists?
  → Verify files in vbs_scripts/ folder
  → Check file names match config.py:
    - VBS_ERF_SCRIPT_1
    - VBS_ERF_SCRIPT_2

✓ Check 2: Test VBS manually
  → Open Command Prompt
  → cd vbs_scripts
  → cscript //nologo script_name.vbs
  → Check for errors

✓ Check 3: VBS outputs parseable data
  → VBS should output JSON or text
  → Add at end of VBS:
    WScript.Echo "Success"
  → Python captures this output

✓ Check 4: Path separators
  → Use Path object in config.py
  → Example: Path("vbs_scripts/script.vbs")
  → Not: "vbs_scripts\script.vbs"
```

#### Issue: "Cannot parse VBS output"
**Symptoms:**
- VBS runs but data not extracted
- Parsing errors in log

**Solutions:**
```
✓ Modify VBS to output JSON
  → At end of your VBS script:

' VBS Script
Dim field1, field2
field1 = "value1"
field2 = "value2"

' Output as JSON
Dim jsonOutput
jsonOutput = "{""field1"":""" & field1 & """,""field2"":""" & field2 & """}"
WScript.Echo jsonOutput

✓ Parse in Python
  → In erf_workflow.py or ko03_handler.py:
  
import json
result = subprocess.run([...])
output = result.stdout.strip()
data = json.loads(output)  # Now you have dictionary
```

---

### 6. Excel Issues

#### Issue: "Failed to read input Excel file"
**Symptoms:**
- Error when loading Excel
- No materials detected

**Solutions:**
```
✓ Check file format
  → Must be .xlsx or .xls
  → Not .xlsm or .csv (though .csv should work)

✓ Check file structure
  → First column should have material numbers
  → Column header doesn't matter
  → No blank rows at top

✓ Correct format:
  | Part Number    | Plant | MRP |
  |----------------|-------|-----|
  | 857-A65473-106 | 1000  | 1000|
  | 684-B20512-006 |       |     |

✓ File not open elsewhere
  → Close Excel if file is open
  → Excel locks files when open
```

#### Issue: "Failed to export results to Excel"
**Symptoms:**
- Processing completes
- But export fails

**Solutions:**
```
✓ Check output directory exists
  → Should auto-create 'output/' folder
  → Manually create if needed

✓ Check permissions
  → Run as Administrator if needed
  → Check folder isn't read-only

✓ File not already open
  → Close any previously exported files
  → Excel can't overwrite open files

✓ Check disk space
  → Ensure sufficient disk space
  → Large batches create large files
```

---

### 7. GUI Issues

#### Issue: "GUI doesn't open" or "Window blank"
**Symptoms:**
- Application starts but no window
- Window appears but controls missing

**Solutions:**
```
✓ Check tkinter installed
  → Usually comes with Python
  → Try: python -m tkinter
  → Should open small window

✓ Try different Python version
  → Python 3.8+ recommended
  → Some versions have tkinter issues

✓ Update display settings
  → Windows: Settings → Display → Scale to 100%
  → High DPI can cause GUI issues
```

#### Issue: "Progress bar stuck" or "Not updating"
**Symptoms:**
- Automation running but progress not showing
- GUI frozen

**Solutions:**
```
✓ This is normal during processing
  → Progress updates between materials
  → Not during material processing
  → GUI may appear frozen but is working

✓ Check logs
  → Open logs/ folder
  → Watch latest log file
  → Shows real-time progress

✓ Force update (for developers)
  → In code, add: self.root.update_idletasks()
  → After each major operation
```

---

### 8. Performance Issues

#### Issue: "Automation very slow"
**Symptoms:**
- Each material takes >60 seconds
- Batch processing takes hours

**Solutions:**
```
✓ Reduce wait times
  → In config.py:
  → WAIT_TIME_AFTER_QUERY = 1  # Try lower
  → WAIT_TIME_AFTER_F7 = 1

✓ Disable unnecessary fallbacks
  → If ERF not needed, disable it
  → Saves 30-40 seconds per material

✓ Select specific plants only
  → Don't select all plants if not needed
  → Each plant adds 15-20 seconds

✓ Optimize VBS scripts
  → Remove unnecessary operations
  → Minimize SAP interactions
```

#### Issue: "High CPU/Memory usage"
**Symptoms:**
- Computer slows down
- High resource usage

**Solutions:**
```
✓ Process in smaller batches
  → Instead of 100, do 25 at a time
  → Close and restart between batches

✓ Close unnecessary programs
  → Close other browser tabs
  → Close unused applications

✓ Enable headless browser (advanced)
  → In erf_workflow.py:
  → options.add_argument('--headless')
  → Browser runs invisibly
```

---

### 9. Data Quality Issues

#### Issue: "Extracted data is incorrect"
**Symptoms:**
- Data extracted but wrong values
- Fields mixed up

**Solutions:**
```
✓ Verify field IDs match field names
  → In EXTRACTION_FIELDS:
  → "Material" should map to material field ID
  → "Description" should map to description field ID
  → Use field finder to verify each one

✓ Check field positions
  → Fields may appear in different positions
  → on different screens
  → Verify on actual screen

✓ Data type mismatches
  → Some fields need special handling
  → Dates, numbers, etc.
```

#### Issue: "Some fields always empty"
**Symptoms:**
- Most data extracted correctly
- But specific fields always blank

**Solutions:**
```
✓ Field may not always be populated
  → Not an error, just no data in SAP
  → Normal for optional fields

✓ Field ID may be wrong
  → Use field finder to get correct ID
  → Field may have similar name but different ID

✓ Timing issue
  → Field may load slowly
  → Increase wait time before extraction
```

---

## 🔍 Debugging Techniques

### 1. Enable Debug Logging
```python
# In main.py
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
```

### 2. Test Components Individually

**Test SAP Connection:**
```python
from core.sap_connector import SAPConnector

connector = SAPConnector()
if connector.connect():
    print("✓ Connection works")
    print(connector.get_session_info())
else:
    print("✗ Connection failed")
```

**Test Field Manager:**
```python
from core.field_manager import FieldManager

# After connecting to SAP and navigating to screen
field_manager = FieldManager(session)
value = field_manager.get_field_value("your_field_id")
print(f"Field value: {value}")
```

**Test MD04 Handler:**
```python
from transactions.md04_handler import MD04Handler

handler = MD04Handler(sap_connector)
data = handler.process_material("857-A65473-106", "1000")
print(f"Extracted: {data}")
```

### 3. Use Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use Visual Studio Code debugger
# Set breakpoints in VS Code and run in debug mode
```

### 4. Watch Log Files in Real-Time

**Windows:**
```cmd
# Open Command Prompt
cd logs
powershell Get-Content -Path .\sap_rpa_*.log -Wait
```

**This shows logs as they're written**

### 5. Test with Single Material First

Always test with one material before batch processing:
```
1. Enter one material number
2. Select one plant
3. Disable all fallbacks
4. Start automation
5. Watch logs
6. Fix any issues
7. Then try multiple materials
```

---

## 📊 Diagnostic Checklist

Run through this checklist when troubleshooting:

```
□ SAP Logon is running
□ Logged into SAP
□ SAP GUI Scripting is enabled
□ Python dependencies installed (pip list)
□ Field IDs updated in config.py
□ VBS scripts in vbs_scripts/ folder
□ Edge WebDriver downloaded and path configured
□ Logs folder exists and is writable
□ Output folder exists and is writable
□ No Excel files open from previous runs
□ Sufficient disk space
□ Not running other SAP automation simultaneously
□ setup_check.py passes all checks
```

---

## 🆘 Getting More Help

### 1. Check Log Files
```
logs/sap_rpa_YYYYMMDD_HHMMSS.log
```
Look for:
- ERROR messages
- Exception tracebacks
- "Failed to..." messages

### 2. Run Setup Check
```bash
python setup_check.py
```
Shows all configuration issues

### 3. Test Each Component
Follow "Test Components Individually" section above

### 4. Compare with Working System
If it worked before:
- Check what changed
- Compare config.py
- Check SAP system updates
- Check network/VPN changes

---

## 💡 Pro Tips

1. **Always test manually first** - Before automating, do it manually in SAP to verify it works

2. **Start simple** - Test with one material, one plant, no fallbacks

3. **Read the logs** - Logs contain detailed information about what's happening

4. **Use field finder** - Don't guess field IDs, use the field finder tool

5. **Keep SAP open** - Don't close SAP while automation is running

6. **Version control** - Keep working config.py backed up before making changes

7. **Document changes** - Note what works and what doesn't for future reference

---

**Need more help? Check the other documentation files!**
- README.md - Feature overview
- IMPLEMENTATION_GUIDE.md - Setup instructions  
- WORKFLOW_DIAGRAMS.md - Visual flowcharts
