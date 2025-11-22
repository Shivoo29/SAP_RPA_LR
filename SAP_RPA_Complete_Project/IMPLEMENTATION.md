# SAP RPA - Developer Implementation Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Current State](#current-state)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Development Environment Setup](#development-environment-setup)
5. [How to Run](#how-to-run)
6. [Code Walkthrough](#code-walkthrough)
7. [Known Issues & Bugs](#known-issues--bugs)
8. [Potential Errors](#potential-errors)
9. [Common Pitfalls](#common-pitfalls)
10. [Testing Strategy](#testing-strategy)
11. [Debugging Guide](#debugging-guide)
12. [Contributing](#contributing)

---

## Project Overview

### What is This?
SAP RPA (Robotic Process Automation) system for automating material data extraction from SAP ERP systems. The system searches for material information across multiple SAP plants using a 3-tier fallback strategy.

### Business Problem
- Manual material data extraction from SAP is time-consuming
- Materials may be in different plants (1000, 2000, 1020, 1900)
- Data can exist in different forms: MatRes, OrdRes, or STPord
- Need to check ERF Dashboard and KO03 as fallbacks

### Technical Solution
Automated multi-tier extraction system:
1. **Tier 1**: SAP GUI automation (MD04 transaction)
2. **Tier 2**: Web automation (ERF Dashboard)
3. **Tier 3**: SAP transaction chaining (KO03)

### Tech Stack
```
Backend:     Python 3.8+
SAP Access:  win32com (pywin32) - COM automation
Web Auto:    Selenium WebDriver (Edge)
Data:        Pandas, OpenPyXL
GUI:         Tkinter
Platform:    Windows (SAP GUI required)
```

---

## Current State

### Version: 2.0 (Optimized)

**Last Major Updates:**
- Commit `1fc04b2`: Removed redundancies, 20-40% performance improvement
- Commit `9b24711`: Added OrdRes support (3-tier priority system)
- Commit `624e776`: Added testing and validation tools

### What Works
✅ MatRes extraction from MD04 (PRIORITY 1)
✅ OrdRes extraction from MD04 (PRIORITY 2)
✅ STPord → RPM extraction → ERF workflow (PRIORITY 3)
✅ Multi-plant searching with early termination
✅ Single-pass table scanning
✅ Excel import/export with 3 sheets
✅ Comprehensive logging
✅ Error handling and fallbacks

### What's Experimental
⚠️ **OrdRes extraction** - Field IDs need validation in production environment
⚠️ **WebDriver management** - Opens/closes per material (could be optimized)
⚠️ **VBS script integration** - Depends on external scripts being present

### What's Not Implemented
❌ WebDriver session reuse across materials
❌ Config dependency injection (Config() instantiated everywhere)
❌ Consistent use of data model classes (uses dicts instead)
❌ Unit tests
❌ CI/CD pipeline
❌ Retry logic for network failures

---

## Architecture Deep Dive

### Directory Structure
```
SAP_RPA_Complete_Project/
├── main.py                      # Entry point - initializes GUI
├── config.py                    # Configuration management (CRITICAL)
├── utils.py                     # Shared utilities (VBS execution)
├── requirements.txt             # Python dependencies
│
├── core/                        # Low-level SAP interaction
│   ├── sap_connector.py        # COM automation, session management
│   └── field_manager.py        # Field detection, data extraction
│
├── transactions/                # Transaction-specific handlers
│   ├── md04_handler.py         # MD04 logic (multi-plant, 3-tier priority)
│   └── ko03_handler.py         # KO03 order processing
│
├── workflows/                   # High-level orchestration
│   ├── scenario_manager.py    # Main workflow coordinator
│   └── erf_workflow.py        # Selenium-based ERF automation
│
├── data/                       # Data management
│   ├── data_models.py         # Data structures (ProcessingResult, etc.)
│   └── excel_manager.py       # Excel I/O with formatting
│
├── gui/                        # User interface
│   └── main_window.py         # Tkinter GUI (single-threaded)
│
├── logs/                       # Runtime logs
├── output/                     # Excel exports
│
└── docs/                       # Documentation
    ├── OPTIMIZATION_SUMMARY.md
    ├── ORDRES_INTEGRATION.md
    ├── TESTING_CHECKLIST.md
    └── [8 more .md files]
```

### Data Flow

```
User Input (GUI/Excel)
    ↓
ScenarioManager.process_single_material()
    ↓
MD04Handler.process_material_multiple_plants_optimized()
    ↓
For each plant:
    ├─ Navigate to MD04
    ├─ Execute query
    ├─ FieldManager.scan_md04_table_for_elements()  ← SINGLE SCAN
    │   Returns: {matres_element, has_ordres, ordres_row_index, has_stpord, stpord_row_index}
    │
    ├─ PRIORITY 1: MatRes found?
    │   └─ Yes → extract_data() → Return immediately
    │
    ├─ PRIORITY 2: OrdRes found?
    │   └─ Yes → extract_ordres_from_current_screen() → Return immediately
    │
    ├─ PRIORITY 3: STPord found?
    │   └─ Yes → extract_rpm_from_current_screen() → ERFWorkflow
    │       └─ ERFWorkflow.execute_erf_workflow(rpm_number)
    │           └─ Navigate ERF Dashboard
    │           └─ Extract order data
    │           └─ If order found → KO03Handler.process_order()
    │
    └─ None found → Continue to next plant
    ↓
Return ProcessingResult
    ↓
ExcelManager.write_output_file()
```

### Key Design Patterns

**1. Strategy Pattern** - `scenario_manager.py`
- Different scenarios (MatRes, OrdRes, STPord→ERF, ERF→KO03)
- Fallback chain

**2. Template Method** - Transaction handlers
- Common structure: navigate → fill fields → execute → extract

**3. Facade** - `SAPConnector`
- Hides COM complexity
- Provides clean API for transactions

**4. Observer Pattern** - Logging
- Centralized logging across all modules
- File + console output

---

## Development Environment Setup

### Prerequisites
```bash
# Windows OS (SAP GUI requirement)
Windows 10/11

# Python 3.8 or higher
python --version  # Should show 3.8+

# SAP GUI installed and configured
# Check: Start → SAP Logon → Connection available

# Microsoft Edge (for ERF Dashboard automation)
edge --version
```

### Installation Steps

**1. Clone Repository**
```bash
cd /path/to/work
git clone <repo-url>
cd SAP_RPA_LR/SAP_RPA_Complete_Project
```

**2. Create Virtual Environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Linux (not supported for SAP GUI)
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**Requirements.txt contents:**
```
pywin32>=305           # SAP GUI COM automation
selenium>=4.0.0        # Web automation
pandas>=1.3.0          # Data manipulation
openpyxl>=3.0.9        # Excel read/write
xlsxwriter>=3.0.2      # Excel formatting
```

**4. Verify SAP GUI Scripting Enabled**
```bash
# Run validation
python setup_check.py
```

Should output:
```
✓ SAP GUI found
✓ Scripting engine accessible
✓ Active session detected
```

**5. Configure Field IDs**
```bash
# Discover field IDs for your environment
python sap_field_finder.py
```

Navigate to MD04 manually, then script will show field IDs. Update `config.py` accordingly.

**6. Validate OrdRes Fields** (if using OrdRes)
```bash
python validate_ordres_fields.py
# Enter test material with OrdRes
# Script validates all field IDs
```

---

## How to Run

### Method 1: GUI Mode (Recommended)
```bash
python main.py
```

This launches Tkinter GUI with:
- SAP connection section
- Material input (single or batch)
- Configuration options
- Progress tracking
- Results table

**GUI Workflow:**
1. Click "Connect to SAP"
2. Enter material number OR load Excel file
3. Select plants to search (default: all)
4. Click "Start Processing"
5. Monitor progress
6. Check results in output/

### Method 2: Programmatic Mode
```python
from core.sap_connector import SAPConnector
from workflows.scenario_manager import ScenarioManager
from data.excel_manager import ExcelManager
from config import Config

# Connect
connector = SAPConnector()
connector.connect()

# Initialize
excel_mgr = ExcelManager()
scenario_mgr = ScenarioManager(connector, excel_mgr)

# Process single material
result = scenario_mgr.process_single_material(
    material_number="857-B97453-003",
    selected_plants=['1000', '2000'],
    enable_erf_fallback=True
)

print(f"Success: {result.success}")
print(f"Scenario: {result.scenario.value}")
print(f"Data: {result.data}")

# Cleanup
connector.disconnect()
```

### Method 3: Batch Processing
```python
# Create Excel with material numbers in column A
# Path: input/materials.xlsx

from data.excel_manager import ExcelManager

excel_mgr = ExcelManager()
materials = excel_mgr.read_input_file('input/materials.xlsx')

for material_data in materials:
    result = scenario_mgr.process_single_material(
        material_number=material_data['material_number']
    )
    # Results collected automatically
```

### Environment Variables (Optional)
```bash
# Set log level
export SAP_RPA_LOG_LEVEL=DEBUG

# Set output directory
export SAP_RPA_OUTPUT_DIR=/custom/path

# Disable ERF fallback
export SAP_RPA_DISABLE_ERF=1
```

---

## Code Walkthrough

### Critical Files to Understand

#### 1. `config.py` - Configuration Hub
**Purpose:** All field IDs, plants, timeouts centralized here

**CRITICAL SECTIONS:**
```python
# SAP Field IDs - MUST match your environment
MD04_FIELDS = {
    "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/...",
    # ^^ If this is wrong, NOTHING works
}

# OrdRes field IDs - Validate with validate_ordres_fields.py
ORDRES_FIELDS = {
    "item_display_button": "wnd[1]/tbar[0]/btn[17]",  # May vary
    "grid_shell": "wnd[0]/usr/cntlGRID_1000/...",     # GRID_1000 might be different
}

# Plants to search
AVAILABLE_PLANTS = ['1000', '2000', '1020', '1900']  # Order matters!

# Timing - Adjust if SAP is slow
WAIT_TIME_AFTER_ACTION = 2  # Increase if screens don't load
WAIT_TIME_AFTER_QUERY = 3   # Increase if results are incomplete
```

**Common Mistake:** Copying field IDs from another SAP system without validation

#### 2. `core/field_manager.py` - Table Scanning Engine
**Purpose:** Scans MD04 results table for MatRes/OrdRes/STPord

**Key Method:**
```python
def scan_md04_table_for_elements(self) -> dict:
    """
    CRITICAL: Single-pass scan for all three element types
    Returns: {matres_element, has_ordres, ordres_row_index, has_stpord, stpord_row_index}
    """
    table_id = "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/..."
    table = self.session.findById(table_id)

    for row_idx in range(table.rows.count):
        for col_idx in range(table.columns.count):
            cell_text = table.getCell(row_idx, col_idx).text.strip()

            if cell_text == 'MatRes':      # PRIORITY 1
                result['matres_element'] = cell
            elif cell_text == 'OrdRes':    # PRIORITY 2
                result['has_ordres'] = True
                result['ordres_row_index'] = row_idx
            elif cell_text == 'STPord':    # PRIORITY 3
                result['has_stpord'] = True
                result['stpord_row_index'] = row_idx

    return result
```

**Potential Issue:** If SAP displays text as "ORDRES" (uppercase) or "Ord.Res" (with dot), the exact match fails.

**Fix:** Change to `cell_text.upper().replace('.', '') == 'ORDRES'`

#### 3. `transactions/md04_handler.py` - Multi-Plant Logic
**Purpose:** Orchestrates plant searches with early termination

**Key Method:**
```python
def process_material_multiple_plants_optimized(self, material_number, plant_list):
    for i, plant in enumerate(plant_list):
        # Navigate to MD04
        self.navigate_to_md04()
        self.enter_material(material_number)
        self.set_plant(plant)
        self.execute_query()

        # SINGLE SCAN
        scan_result = self.field_manager.scan_md04_table_for_elements()

        # PRIORITY 1: MatRes
        if scan_result['matres_element']:
            return extract_matres_data()  # STOPS HERE

        # PRIORITY 2: OrdRes
        elif scan_result['has_ordres']:
            return extract_ordres_from_current_screen()  # STOPS HERE

        # PRIORITY 3: STPord
        elif scan_result['has_stpord']:
            return extract_rpm_from_current_screen()  # STOPS HERE

        # None found - continue to next plant
```

**Why Optimized:**
- Old code: Check all 4 plants, then process
- New code: Stop on first match
- Savings: 10-25 seconds per material

#### 4. `workflows/scenario_manager.py` - Orchestration Layer
**Purpose:** Coordinates the entire workflow, handles fallbacks

**Key Method:**
```python
def process_single_material(self, material_number):
    result = ProcessingResult(material_number)

    # Try MD04 (optimized)
    md04_result = self.md04_handler.process_material_multiple_plants_optimized(...)

    if md04_result:
        source = md04_result.get('source')

        if source == 'MatRes':
            result.scenario = ScenarioType.MD04_MATRES_FOUND
            result.data = md04_result
            self.stats['scenario_1_success'] += 1

        elif source == 'OrdRes':
            result.scenario = ScenarioType.MD04_MATRES_FOUND  # Same as MatRes
            result.data = md04_result
            self.stats['scenario_1_success'] += 1

        elif source == 'STPord' and enable_erf_fallback:
            # Go to ERF Dashboard
            erf_data = self.erf_workflow.execute_erf_workflow(
                material_number,
                md04_result['rpm_number']
            )

            if erf_data:
                result.scenario = ScenarioType.ERF_DASHBOARD
                result.data = erf_data
                self.stats['scenario_2_success'] += 1

                # Check for KO03
                if erf_data.get('order_number'):
                    ko03_data = self.ko03_handler.process_order(...)
                    result.scenario = ScenarioType.ERF_TO_KO03
                    self.stats['scenario_3_success'] += 1

    return result
```

**Statistics Tracking:**
- `scenario_1_success`: MatRes + OrdRes count
- `scenario_2_success`: ERF Dashboard count
- `scenario_3_success`: ERF→KO03 count
- `failures`: Total failures

#### 5. `workflows/erf_workflow.py` - Web Automation
**Purpose:** Automate ERF Dashboard when STPord found

**Selenium Flow:**
```python
def execute_erf_workflow(self, material_number, rpm_number):
    # 1. Setup WebDriver (creates new browser instance)
    self.driver = webdriver.Edge(service=Service(driver_path))

    # 2. Navigate to ERF Dashboard
    self.driver.get(ERF_DASHBOARD_URL)

    # 3. Wait for page load
    WebDriverWait(self.driver, 30).until(...)

    # 4. Switch to iframes (nested)
    self.driver.switch_to.frame("contentAreaFrame")
    self.driver.switch_to.frame("isolatedWorkArea")

    # 5. Search by RPM number
    erf_input = self.driver.find_element(By.ID, "aaaa.RpmDashboardView.ERFNumInp")
    erf_input.send_keys(rpm_number)

    # 6. Click search
    search_button.click()

    # 7. Extract data
    order_data = self.extract_erf_data()

    # 8. Cleanup
    self.driver.quit()  # Closes browser

    return order_data
```

**KNOWN ISSUE:** Opens/closes browser for EACH material. For 100 STPord materials = 100 browser launches (~500 seconds wasted).

**Potential Fix:** Reuse driver across materials (not implemented).

---

## Known Issues & Bugs

### 1. OrdRes Field IDs Not Validated
**Severity:** HIGH
**Impact:** OrdRes extraction may fail in production

**Issue:**
Field IDs in `config.py` are based on VBS script, not tested in live environment.

**Example:**
```python
ORDRES_FIELDS = {
    "grid_shell": "wnd[0]/usr/cntlGRID_1000/shellcont/shell/..."
}
# What if it's GRID_0100 in production?
```

**Workaround:**
```bash
python validate_ordres_fields.py
# Update config.py with correct IDs
```

**Status:** Documented in ORDRES_INTEGRATION.md, validation script provided

---

### 2. WebDriver Not Reused
**Severity:** MEDIUM
**Impact:** 5-10 seconds wasted per ERF material

**Issue:**
```python
def execute_erf_workflow(self, material_number, rpm_number):
    self.setup_webdriver()  # Opens browser
    # ... process material ...
    self.cleanup_webdriver()  # Closes browser
```

For 50 materials → 50 browser launches = 250-500 seconds wasted.

**Potential Fix:**
```python
class ERFWorkflow:
    def __init__(self):
        self.driver = None

    def ensure_driver(self):
        if not self.driver:
            self.setup_webdriver()

    def execute_erf_workflow(self, ...):
        self.ensure_driver()  # Reuse if exists
        # ... process ...
        # Don't cleanup

    def cleanup(self):
        # Only called at end
        if self.driver:
            self.driver.quit()
```

**Status:** Not implemented (marked as future enhancement)

---

### 3. Config Instantiated Multiple Times
**Severity:** LOW
**Impact:** Memory overhead (~1KB per instance)

**Issue:**
```python
# In md04_handler.py
self.config = Config()

# In ko03_handler.py
self.config = Config()

# In scenario_manager.py
self.config = Config()

# = 6+ instances of same config
```

**Better Approach:**
```python
# Dependency injection
class MD04Handler:
    def __init__(self, sap_connector, config):
        self.config = config  # Shared instance
```

**Status:** Not implemented (low priority)

---

### 4. Data Models Not Used Consistently
**Severity:** LOW
**Impact:** Lost type safety, harder to maintain

**Issue:**
```python
# data_models.py defines ERFData class
@dataclass
class ERFData:
    erf_number: str
    order_number: str
    # ...

# But code uses plain dicts instead
def extract_erf_data(self):
    return {
        'erf_number': ...,
        'order_number': ...
    }
```

**Better:**
```python
def extract_erf_data(self) -> ERFData:
    data = ERFData()
    data.erf_number = ...
    data.order_number = ...
    return data
```

**Status:** Not implemented (technical debt)

---

### 5. No Retry Logic for Transient Errors
**Severity:** MEDIUM
**Impact:** Failures that could be retried are marked as permanent

**Issue:**
```python
if not self.navigate_to_md04():
    return None  # Gives up immediately
```

If SAP is temporarily slow, entire material fails.

**Better:**
```python
for attempt in range(3):
    if self.navigate_to_md04():
        break
    time.sleep(2 ** attempt)  # Exponential backoff
else:
    return None
```

**Status:** Not implemented

---

### 6. Single-Threaded GUI
**Severity:** LOW
**Impact:** GUI freezes during processing

**Issue:**
```python
# main_window.py
def start_processing(self):
    for material in materials:
        result = scenario_mgr.process_single_material(material)
        # GUI frozen until done
```

**Root Cause:** Tkinter + COM threading issues. COM objects must be accessed from same thread.

**Workaround Used:** `root.after()` loop (already implemented)

**Status:** Acceptable (COM limitation)

---

## Potential Errors

### Runtime Errors

#### 1. COM Exception: "Interface not supported"
```
pywintypes.com_error: (-2147467262, 'No such interface supported', None, None)
```

**Cause:** SAP GUI scripting disabled

**Fix:**
```bash
# Enable in SAP GUI
Options → Accessibility & Scripting → Scripting → Enable scripting
```

#### 2. ElementNotFoundException
```
Exception: Element 'wnd[0]/usr/ctxtRM61R-MATNR' not found
```

**Cause:** Field ID incorrect for your SAP version

**Fix:**
```bash
python sap_field_finder.py
# Navigate to screen, find correct ID
# Update config.py
```

#### 3. TimeoutException (Selenium)
```
selenium.common.exceptions.TimeoutException: Message:
```

**Cause:** ERF Dashboard slow to load, or iframe not found

**Fix:**
```python
# In config.py
WEB_TIMEOUT = 60  # Increase from 30
```

#### 4. AttributeError: 'NoneType' object has no attribute 'text'
```
AttributeError: 'NoneType' object has no attribute 'text'
```

**Cause:** Field not found, `findById()` returned None

**Fix:**
```python
# Add null check
field = session.findById(field_id)
if field and hasattr(field, 'text'):
    value = field.text
```

#### 5. KeyError: 'material'
```
KeyError: 'material'
```

**Cause:** Data extraction failed, expected key missing

**Fix:**
```python
# Use .get() with default
material = data.get('material', '')
```

### Configuration Errors

#### 1. Wrong Plant List
```python
AVAILABLE_PLANTS = ['1000', '2000', '1020', '1900']
# But your SAP only has ['1000', '2000']
```

**Impact:** Wastes time checking non-existent plants

**Fix:** Update to actual plants in your system

#### 2. Field ID Mismatch
```python
MD04_FIELDS = {
    "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/..."
}
# But your SAP has tabs300 (lowercase)
```

**Impact:** Nothing works

**Fix:** Run `sap_field_finder.py`

#### 3. VBS Script Not Found
```
FileNotFoundError: 'vbs_scripts/erf_dashboard_1.vbs' not found
```

**Fix:**
```python
# In config.py
VBS_ERF_SCRIPT_1 = Path(__file__).parent / 'vbs_scripts' / 'erf_dashboard_1.vbs'

# Or disable VBS
# Comment out VBS calls in erf_workflow.py
```

### Logic Errors

#### 1. Infinite Plant Loop
If `process_material_multiple_plants_optimized()` never returns:

**Possible Causes:**
- `execute_query()` hangs
- Table scan loops infinitely
- SAP popup blocks progress

**Debug:**
```python
# Add timeout
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Plant processing timeout")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 second timeout
```

#### 2. Early Termination Too Aggressive
Material has MatRes in plant 2000 with better data, but stops at plant 1000:

**Cause:** By design - stops on first match

**Solution:** If you need to check all plants, modify logic:
```python
# Collect all matches, then pick best
all_matches = []
for plant in plant_list:
    if match_found:
        all_matches.append(match)
return best_match(all_matches)
```

---

## Common Pitfalls

### For New Developers

#### 1. Forgetting to Call `connect()` Before Using Session
```python
connector = SAPConnector()
# connector.connect()  # FORGOT THIS
session = connector.get_session()  # Returns None!
```

**Always:**
```python
connector = SAPConnector()
if not connector.connect():
    raise Exception("SAP connection failed")
```

#### 2. Not Waiting After Screen Actions
```python
field.text = "12345"
button.press()  # Screen hasn't updated yet!
value = other_field.text  # Gets old value
```

**Always:**
```python
field.text = "12345"
time.sleep(0.5)
button.press()
time.sleep(2)  # Wait for screen change
value = other_field.text
```

#### 3. Assuming Field IDs Are Universal
```python
# Copied from another project
field_id = "wnd[0]/usr/ctxtRM61R-MATNR"
```

**Never assume!** Always validate with `sap_field_finder.py`

#### 4. Not Checking Return Values
```python
self.navigate_to_md04()  # What if it returns False?
self.execute_query()     # What if query fails?
data = self.extract_data()  # What if data is empty?
```

**Always:**
```python
if not self.navigate_to_md04():
    return None
if not self.execute_query():
    return None
data = self.extract_data()
if not data:
    return None
```

#### 5. Modifying Config at Runtime
```python
# DON'T DO THIS
config.AVAILABLE_PLANTS.append('3000')  # Mutates shared config
```

**Instead:**
```python
# Pass as parameter
my_plants = config.AVAILABLE_PLANTS + ['3000']
result = handler.process_material_multiple_plants(plants=my_plants)
```

#### 6. Not Disconnecting SAP
```python
connector = SAPConnector()
connector.connect()
# ... do work ...
# Forget to disconnect - leaves sessions open
```

**Always:**
```python
try:
    connector.connect()
    # ... work ...
finally:
    connector.disconnect()

# Or use context manager
with SAPConnector() as connector:
    # ... work ...
```

---

## Testing Strategy

### Current State: ❌ No Unit Tests

**Why:**
- COM objects hard to mock
- SAP GUI dependency
- Selenium state management

**What Should Exist:**

#### 1. Unit Tests (with mocks)
```python
# tests/test_field_manager.py
def test_scan_md04_table_matres_found():
    mock_session = Mock()
    mock_table = Mock()
    mock_table.rows.count = 5
    mock_cell = Mock()
    mock_cell.text = "MatRes"
    mock_table.getCell.return_value = mock_cell

    field_mgr = FieldManager(mock_session)
    result = field_mgr.scan_md04_table_for_elements()

    assert result['matres_element'] is not None
    assert result['has_ordres'] == False
```

#### 2. Integration Tests (with real SAP)
```python
# tests/integration/test_md04_flow.py
@pytest.mark.slow
@pytest.mark.requires_sap
def test_full_md04_flow_matres():
    connector = SAPConnector()
    connector.connect()

    handler = MD04Handler(connector)
    result = handler.process_material_single_plant(
        material_number="TEST-MATERIAL-001",
        plant="1000"
    )

    assert result is not None
    assert result['material'] == "TEST-MATERIAL-001"
```

#### 3. End-to-End Tests
```python
# tests/e2e/test_scenarios.py
def test_scenario_1_matres():
    # Full workflow with known MatRes material
    result = scenario_mgr.process_single_material("MAT-001")
    assert result.scenario == ScenarioType.MD04_MATRES_FOUND
    assert result.success == True
```

### Manual Testing Checklist

Before each release, test:
- [ ] MatRes material in plant 1000
- [ ] MatRes material in plant 2000 (verify early termination)
- [ ] OrdRes material (validate field IDs)
- [ ] STPord material (full ERF flow)
- [ ] Material not in any plant (verify graceful failure)
- [ ] Batch processing 20 materials
- [ ] Excel import/export
- [ ] Statistics tracking

---

## Debugging Guide

### Enable Debug Logging
```python
# In main.py or your script
import logging
logging.basicConfig(
    level=logging.DEBUG,  # Instead of INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### SAP GUI Inspector
```bash
# Record SAP actions
1. Open SAP GUI
2. Right-click in SAP window → Script Recording and Playback
3. Start recording
4. Perform actions manually
5. Stop recording
6. Review generated VBS script for field IDs
```

### Selenium Debug
```python
# Keep browser open after error
from selenium.webdriver.edge.options import Options

options = Options()
options.add_experimental_option("detach", True)  # Don't close on error

driver = webdriver.Edge(options=options)
```

### Breakpoint Debugging
```python
# In code
import pdb; pdb.set_trace()

# Or use IDE debugger (PyCharm, VS Code)
# Set breakpoints in:
# - md04_handler.py:318 (after table scan)
# - scenario_manager.py:103 (after MD04 result)
```

### Common Debug Points

**1. Why didn't MatRes get found?**
```python
# In field_manager.py:270 - After table scan
result = self.scan_md04_table_for_elements()
print(f"DEBUG: MatRes element: {result['matres_element']}")
print(f"DEBUG: Has OrdRes: {result['has_ordres']}")
print(f"DEBUG: Has STPord: {result['has_stpord']}")
```

**2. Why did OrdRes extraction fail?**
```python
# In md04_handler.py:472 - During field extraction
try:
    cost_center_field = self.session.findById(field_id)
    print(f"DEBUG: Cost center field found: {cost_center_field}")
    print(f"DEBUG: Field value: {cost_center_field.text}")
except Exception as e:
    print(f"DEBUG: Exception: {e}")
    print(f"DEBUG: Field ID used: {field_id}")
```

**3. Why is processing so slow?**
```python
# Add timing
import time
start = time.time()
self.navigate_to_md04()
print(f"DEBUG: Navigate took {time.time() - start:.2f}s")

start = time.time()
self.execute_query()
print(f"DEBUG: Query took {time.time() - start:.2f}s")
```

### Log Analysis

**Find failures:**
```bash
grep "✗" logs/sap_rpa_*.log
grep "ERROR" logs/sap_rpa_*.log
```

**Count scenarios:**
```bash
grep "SCENARIO 1 SUCCESS" logs/sap_rpa_*.log | wc -l
grep "SCENARIO 2 SUCCESS" logs/sap_rpa_*.log | wc -l
grep "SCENARIO 3 SUCCESS" logs/sap_rpa_*.log | wc -l
```

**Find slow materials:**
```bash
grep "processing time" logs/sap_rpa_*.log | sort -k10 -n -r | head -10
```

---

## Contributing

### Code Style

**Follow PEP 8:**
```bash
pip install black flake8
black .
flake8 .
```

**Type Hints:**
```python
# Use type hints everywhere
def process_material(self, material_number: str, plant: str) -> Optional[Dict[str, str]]:
    pass
```

**Docstrings:**
```python
def method(self, param1: str) -> bool:
    """
    Short description.

    Longer description if needed.

    Args:
        param1: Description of param1

    Returns:
        Description of return value

    Raises:
        ValueError: When param1 is invalid
    """
```

### Git Workflow

**Branch naming:**
```bash
feature/ordres-validation
bugfix/field-id-mismatch
optimization/webdriver-reuse
```

**Commit messages:**
```
✨ Add OrdRes support
🐛 Fix field ID validation
🚀 Optimize WebDriver reuse
📝 Update documentation
```

**Before committing:**
```bash
# Test
python -m pytest tests/

# Format
black .

# Check
flake8 .

# Commit
git add .
git commit -m "✨ Add feature X"
git push
```

### Pull Request Checklist

- [ ] Code follows style guide
- [ ] Type hints added
- [ ] Docstrings written
- [ ] Tests added (if applicable)
- [ ] Documentation updated
- [ ] TESTING_CHECKLIST.md followed
- [ ] No breaking changes (or documented)
- [ ] Performance impact measured

---

## Quick Reference

### Key Files by Functionality

**SAP Connection:**
- `core/sap_connector.py` - Connect, navigate, press keys
- `core/field_manager.py` - Find elements, extract data

**Business Logic:**
- `workflows/scenario_manager.py` - Main orchestrator
- `transactions/md04_handler.py` - Multi-plant search

**Configuration:**
- `config.py` - ALL field IDs and settings

**Utilities:**
- `utils.py` - VBS execution, parsing
- `sap_field_finder.py` - Field ID discovery
- `validate_ordres_fields.py` - OrdRes validation

**Documentation:**
- `OPTIMIZATION_SUMMARY.md` - Performance improvements
- `ORDRES_INTEGRATION.md` - OrdRes technical details
- `TESTING_CHECKLIST.md` - Pre-deployment testing

### Common Commands

```bash
# Run main application
python main.py

# Validate OrdRes fields
python validate_ordres_fields.py

# Find SAP field IDs
python sap_field_finder.py

# Run setup check
python setup_check.py

# View logs
tail -f logs/sap_rpa_*.log

# Clean output
rm output/*.xlsx

# Install dependencies
pip install -r requirements.txt
```

### Emergency Contacts

**If Production Breaks:**
1. Check logs: `logs/sap_rpa_YYYYMMDD_HHMMSS.log`
2. Review recent commits: `git log --oneline -10`
3. Rollback if needed: `git revert <commit>`
4. Disable OrdRes: Comment out in `scenario_manager.py:115-121`
5. Check SAP connection: Run `setup_check.py`

---

## Final Notes

### Project Maturity: 🟡 Production-Ready with Caveats

**Ready for:**
- MatRes extraction ✅
- STPord → ERF workflow ✅
- Batch processing ✅
- Multi-plant searching ✅

**Needs validation:**
- OrdRes field IDs ⚠️

**Not recommended (yet):**
- High-volume processing without WebDriver optimization
- Unattended 24/7 operation

### Next Steps for New Developer

1. **Day 1:** Setup environment, run `setup_check.py`
2. **Day 2:** Read this doc, understand data flow
3. **Day 3:** Test with 1 material (MatRes, OrdRes, STPord)
4. **Day 4:** Review logs, understand what happened
5. **Week 2:** Modify code, add logging, test changes
6. **Week 3:** Understand optimizations, read OPTIMIZATION_SUMMARY.md
7. **Month 2:** Ready to add features

### Learning Resources

**SAP GUI Scripting:**
- https://help.sap.com/docs/sap_gui_for_windows/scripting

**pywin32 (COM):**
- https://github.com/mhammond/pywin32

**Selenium:**
- https://selenium-python.readthedocs.io/

---

**Last Updated:** 2025-01-19
**Version:** 2.0
**Maintainer:** Development Team
