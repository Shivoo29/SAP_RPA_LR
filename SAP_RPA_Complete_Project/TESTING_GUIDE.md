# 🧪 SAP RPA - Testing Guide

Complete testing procedures to validate your automation system.

---

## Pre-Testing Checklist

Before starting tests, ensure:

```
□ All files copied to project folder
□ Dependencies installed (pip install -r requirements.txt)
□ Field IDs updated in config.py
□ SAP Logon is open and logged in
□ VBS scripts in vbs_scripts/ folder (if using)
□ Edge WebDriver downloaded (if using ERF)
□ setup_check.py passed all checks
```

---

## Test Levels

### Level 1: Component Tests (Individual Parts)
Test each module independently

### Level 2: Integration Tests (Combined Parts)
Test modules working together

### Level 3: End-to-End Tests (Full Scenarios)
Test complete workflows

### Level 4: Stress Tests (Performance)
Test with large batches

---

## Level 1: Component Tests

### Test 1.1: SAP Connection

**Purpose:** Verify SAP connection works

**Steps:**
```
1. Run: python main.py
2. Click "Connect to SAP"
3. Observe connection status
```

**Expected Result:**
```
✓ Status shows: "✅ Connected: PRD Client XXX User YourName"
✓ Log shows: "Successfully connected to SAP"
```

**If Failed:**
- Check SAP Logon is running
- Verify you're logged into SAP
- Enable SAP GUI Scripting
- See TROUBLESHOOTING.md

---

### Test 1.2: Transaction Navigation

**Purpose:** Verify can navigate to transactions

**Test Script:**
```python
# test_navigation.py
from core.sap_connector import SAPConnector

connector = SAPConnector()
if connector.connect():
    print("✓ Connected")
    
    # Test MD04
    if connector.navigate_to_transaction('MD04'):
        print("✓ Navigated to MD04")
    else:
        print("✗ Failed to navigate to MD04")
    
    # Test KO03
    if connector.navigate_to_transaction('KO03'):
        print("✓ Navigated to KO03")
    else:
        print("✗ Failed to navigate to KO03")
else:
    print("✗ Connection failed")
```

**Expected Result:**
```
✓ Connected
✓ Navigated to MD04
✓ Navigated to KO03
```

---

### Test 1.3: Field Manager - Fill Fields

**Purpose:** Verify can fill fields

**Test Script:**
```python
# test_field_fill.py
from core.sap_connector import SAPConnector
from core.field_manager import FieldManager
from config import Config

config = Config()
connector = SAPConnector()

if connector.connect():
    connector.navigate_to_transaction('MD04')
    field_manager = FieldManager(connector.session)
    
    # Test material field
    material_id = config.MD04_FIELDS['material_field']
    if field_manager.fill_field(material_id, "857-A65473-106"):
        print("✓ Filled material field")
    else:
        print("✗ Failed to fill material field")
    
    # Test plant field
    plant_id = config.MD04_FIELDS['plant_field']
    if field_manager.fill_field(plant_id, "1000"):
        print("✓ Filled plant field")
    else:
        print("✗ Failed to fill plant field")
```

**Expected Result:**
```
✓ Filled material field
✓ Filled plant field
```

---

### Test 1.4: Field Manager - Read Fields

**Purpose:** Verify can read field values

**Test Script:**
```python
# test_field_read.py
from core.sap_connector import SAPConnector
from core.field_manager import FieldManager
from config import Config

config = Config()
connector = SAPConnector()

if connector.connect():
    connector.navigate_to_transaction('MD04')
    field_manager = FieldManager(connector.session)
    
    # Fill and read back
    material_id = config.MD04_FIELDS['material_field']
    field_manager.fill_field(material_id, "TEST123")
    
    value = field_manager.get_field_value(material_id)
    if value == "TEST123":
        print("✓ Successfully read field value")
    else:
        print(f"✗ Read incorrect value: {value}")
```

**Expected Result:**
```
✓ Successfully read field value
```

---

### Test 1.5: MatRes Detection

**Purpose:** Verify MatRes element detection

**Test Materials:**
- Has MatRes: `857-A65473-106` in plant `1000`
- No MatRes: `DUMMY-12345` (doesn't exist)

**Test Script:**
```python
# test_matres.py
from core.sap_connector import SAPConnector
from core.field_manager import FieldManager
from transactions.md04_handler import MD04Handler

connector = SAPConnector()
if connector.connect():
    handler = MD04Handler(connector)
    
    # Test 1: Material with MatRes
    print("Test 1: Material with MatRes")
    handler.navigate_to_md04()
    handler.enter_material_details("857-A65473-106", "1000")
    handler.execute_md04_query()
    
    if handler.field_manager.find_matres_element():
        print("✓ MatRes detected correctly")
    else:
        print("✗ MatRes not detected")
    
    # Test 2: Material without MatRes
    print("\nTest 2: Material without MatRes")
    handler.navigate_to_md04()
    handler.enter_material_details("DUMMY-12345", "1000")
    handler.execute_md04_query()
    
    if not handler.field_manager.find_matres_element():
        print("✓ Correctly detected no MatRes")
    else:
        print("✗ False positive - detected MatRes where none exists")
```

**Expected Result:**
```
Test 1: Material with MatRes
✓ MatRes detected correctly

Test 2: Material without MatRes
✓ Correctly detected no MatRes
```

---

### Test 1.6: Excel Reading

**Purpose:** Verify can read Excel input files

**Preparation:**
Create `test_input.xlsx` with:
```
| Part Number       |
|-------------------|
| 857-A65473-106    |
| 684-B20512-006    |
| 813-B97886-001    |
```

**Test Script:**
```python
# test_excel_read.py
from data.excel_manager import ExcelManager

manager = ExcelManager()
materials = manager.read_input_file("test_input.xlsx")

print(f"Read {len(materials)} materials:")
for material in materials:
    print(f"  - {material['material_number']}")

if len(materials) == 3:
    print("✓ Correctly read all materials")
else:
    print(f"✗ Expected 3 materials, got {len(materials)}")
```

**Expected Result:**
```
Read 3 materials:
  - 857-A65473-106
  - 684-B20512-006
  - 813-B97886-001
✓ Correctly read all materials
```

---

### Test 1.7: Excel Writing

**Purpose:** Verify can write Excel output files

**Test Script:**
```python
# test_excel_write.py
from data.excel_manager import ExcelManager
from data.data_models import ProcessingResult, ScenarioType

manager = ExcelManager()

# Create test results
results = [
    ProcessingResult(
        material_number="TEST-001",
        success=True,
        scenario=ScenarioType.MD04_MATRES_FOUND,
        plant_found="1000",
        data={"description": "Test part"}
    )
]

# Write to Excel
output_file = manager.write_output_file(results)
print(f"✓ Created output file: {output_file}")

# Verify file exists
import os
if os.path.exists(output_file):
    print("✓ File exists")
else:
    print("✗ File not created")
```

**Expected Result:**
```
✓ Created output file: output/SAP_RPA_Results_20250115_143022.xlsx
✓ File exists
```

---

## Level 2: Integration Tests

### Test 2.1: MD04 Handler - Single Plant

**Purpose:** Test complete MD04 workflow for one plant

**Test Material:** `857-A65473-106` (known to exist in plant 1000)

**Test Script:**
```python
# test_md04_single_plant.py
from core.sap_connector import SAPConnector
from transactions.md04_handler import MD04Handler

connector = SAPConnector()
if connector.connect():
    handler = MD04Handler(connector)
    
    print("Testing MD04 with single plant...")
    data = handler.process_material("857-A65473-106", "1000")
    
    if data:
        print("✓ Successfully extracted data:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    else:
        print("✗ Failed to extract data")
```

**Expected Result:**
```
Testing MD04 with single plant...
✓ Successfully extracted data:
  material: 857-A65473-106
  part_description: [some description]
  recipient: [recipient value]
  order: [order number]
  plant: 1000
```

---

### Test 2.2: MD04 Handler - Multi-Plant

**Purpose:** Test multi-plant search logic

**Test Materials:**
- In plant 1000: `857-A65473-106`
- In plant 2000: `[material in 2000]`
- Nowhere: `DUMMY-12345`

**Test Script:**
```python
# test_md04_multi_plant.py
from core.sap_connector import SAPConnector
from transactions.md04_handler import MD04Handler

connector = SAPConnector()
if connector.connect():
    handler = MD04Handler(connector)
    
    plants = ['1000', '2000', '1020']
    
    print("Test 1: Material in plant 1000")
    data = handler.process_material_multiple_plants("857-A65473-106", plants)
    if data and data.get('plant') == '1000':
        print("✓ Found in correct plant")
    else:
        print("✗ Not found or wrong plant")
    
    print("\nTest 2: Material not in any plant")
    data = handler.process_material_multiple_plants("DUMMY-12345", plants)
    if not data:
        print("✓ Correctly returned None")
    else:
        print("✗ Should not have found data")
```

**Expected Result:**
```
Test 1: Material in plant 1000
✓ Found in correct plant

Test 2: Material not in any plant
✓ Correctly returned None
```

---

### Test 2.3: Scenario Manager - Scenario 1

**Purpose:** Test Scenario Manager with MD04 success

**Test Script:**
```python
# test_scenario_1.py
from core.sap_connector import SAPConnector
from data.excel_manager import ExcelManager
from workflows.scenario_manager import ScenarioManager

connector = SAPConnector()
excel_manager = ExcelManager()

if connector.connect():
    manager = ScenarioManager(connector, excel_manager)
    
    result = manager.process_single_material(
        material_number="857-A65473-106",
        selected_plants=['1000', '2000']
    )
    
    if result.success and result.scenario.value == "MD04_MatRes_Found":
        print("✓ Scenario 1 executed successfully")
        print(f"  Plant found: {result.plant_found}")
        print(f"  Processing time: {result.processing_time:.2f}s")
    else:
        print(f"✗ Scenario 1 failed: {result.error_message}")
```

**Expected Result:**
```
✓ Scenario 1 executed successfully
  Plant found: 1000
  Processing time: 18.23s
```

---

### Test 2.4: ERF Workflow (If Configured)

**Purpose:** Test ERF Dashboard automation

**Prerequisites:**
- Edge WebDriver installed
- ERF Dashboard accessible
- Test material that's in ERF but not MD04

**Test Script:**
```python
# test_erf_workflow.py
from core.sap_connector import SAPConnector
from workflows.erf_workflow import ERFWorkflow

connector = SAPConnector()
if connector.connect():
    workflow = ERFWorkflow(connector)
    
    print("Testing ERF workflow...")
    data = workflow.execute_erf_workflow("YOUR_TEST_MATERIAL")
    
    if data:
        print("✓ ERF workflow successful:")
        for key, value in data.items():
            print(f"  {key}: {value}")
    else:
        print("✗ ERF workflow failed")
```

**Expected Result:**
```
Testing ERF workflow...
✓ ERF workflow successful:
  erf_number: [ERF number]
  short_order_desc: [description]
  internal_order: [order]
  cost_center: [cost center]
```

---

## Level 3: End-to-End Tests

### Test 3.1: Complete Workflow - Scenario 1

**Purpose:** Test full workflow from GUI to Excel export

**Steps:**
```
1. Launch application: python main.py
2. Click "Connect to SAP"
3. Enter material: 857-A65473-106
4. Select plants: 1000
5. Click "Start Automation"
6. Wait for completion
7. Click "Export to Excel"
8. Open generated Excel file
```

**Expected Result:**
```
✓ Connection successful
✓ Material processed
✓ Results show in table with:
  - Material: 857-A65473-106
  - Status: True
  - Scenario: MD04_MatRes_Found
  - Plant: 1000
✓ Excel file created
✓ Excel has 3 sheets: Part_Data, Summary, Errors
✓ Part_Data contains extracted fields
✓ Summary shows 1 processed, 1 successful
✓ Errors sheet is empty or says "No errors"
```

---

### Test 3.2: Complete Workflow - Scenario 2

**Purpose:** Test full workflow with ERF fallback

**Prerequisites:**
- Material that doesn't exist in MD04 but exists in ERF

**Steps:**
```
1. Launch application
2. Connect to SAP
3. Enter material without MatRes: [your test material]
4. Select all plants
5. Enable ERF fallback
6. Click "Start Automation"
7. Wait for completion
8. Export to Excel
```

**Expected Result:**
```
✓ Tries all plants in MD04 - not found
✓ Falls back to ERF Dashboard
✓ Browser launches automatically
✓ ERF data extracted
✓ Results show Scenario: ERF_Dashboard
✓ Excel export successful
```

---

### Test 3.3: Batch Processing - Small Batch

**Purpose:** Test batch processing with multiple materials

**Preparation:**
Create `test_batch.xlsx` with 5 materials:
```
| Part Number       |
|-------------------|
| 857-A65473-106    | ← Has MatRes
| 684-B20512-006    | ← Has MatRes  
| 813-B97886-001    | ← Has MatRes
| DUMMY-TEST-001    | ← No MatRes
| DUMMY-TEST-002    | ← No MatRes
```

**Steps:**
```
1. Launch application
2. Connect to SAP
3. Browse and select test_batch.xlsx
4. Select plants: 1000, 2000
5. Disable fallbacks (faster testing)
6. Click "Start Automation"
7. Watch progress bar
8. Wait for completion
9. Export results
```

**Expected Result:**
```
✓ Progress shows: "Processing 1/5", "2/5", etc.
✓ Results table shows all 5 materials
✓ 3 materials successful (those with MatRes)
✓ 2 materials failed (dummy materials)
✓ Summary statistics:
  - Total: 5
  - Successful: 3
  - Failed: 2
  - Success Rate: 60%
✓ Excel export has errors sheet with 2 failures listed
```

---

### Test 3.4: Batch Processing - Mixed Scenarios

**Purpose:** Test batch with multiple scenario types

**Preparation:**
Create `test_mixed.xlsx` with materials for each scenario:
```
| Part Number       | Notes                  |
|-------------------|------------------------|
| [MD04 material]   | Will use Scenario 1    |
| [ERF material]    | Will use Scenario 2    |
| [Order material]  | Will use Scenario 3    |
```

**Expected Result:**
```
✓ Material 1 → Scenario 1 (MD04)
✓ Material 2 → Scenario 2 (ERF)
✓ Material 3 → Scenario 3 (KO03)
✓ Statistics show breakdown:
  - Scenario 1: 1
  - Scenario 2: 1
  - Scenario 3: 1
✓ All data extracted correctly
```

---

## Level 4: Stress Tests

### Test 4.1: Large Batch Processing

**Purpose:** Test performance with larger batch

**Preparation:**
Create batch file with 25-50 materials

**Metrics to Track:**
```
- Start time
- End time
- Total processing time
- Average time per material
- Memory usage
- Success rate
```

**Test Script:**
```python
# test_large_batch.py
import time
import psutil
from core.sap_connector import SAPConnector
from data.excel_manager import ExcelManager
from workflows.scenario_manager import ScenarioManager

# Track metrics
start_time = time.time()
start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

# Read materials
excel_manager = ExcelManager()
materials_data = excel_manager.read_input_file("large_batch.xlsx")
materials = [m['material_number'] for m in materials_data]

print(f"Processing {len(materials)} materials...")

# Process
connector = SAPConnector()
if connector.connect():
    manager = ScenarioManager(connector, excel_manager)
    
    results = manager.process_batch(
        material_list=materials,
        selected_plants=['1000', '2000']
    )
    
    # Calculate metrics
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024
    
    total_time = end_time - start_time
    avg_time = total_time / len(materials)
    memory_used = end_memory - start_memory
    
    success_count = len([r for r in results if r.success])
    success_rate = (success_count / len(materials)) * 100
    
    print("\n" + "="*60)
    print("PERFORMANCE METRICS")
    print("="*60)
    print(f"Total materials: {len(materials)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(materials) - success_count}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Average per material: {avg_time:.2f} seconds")
    print(f"Memory used: {memory_used:.2f} MB")
```

**Acceptable Performance:**
```
✓ Average time < 30 seconds per material
✓ Success rate > 90% (for valid materials)
✓ Memory usage < 500 MB
✓ No crashes or hangs
✓ All results exported correctly
```

---

### Test 4.2: Concurrent Session Handling

**Purpose:** Test SAP connection stability over time

**Test Script:**
```python
# test_stability.py
from core.sap_connector import SAPConnector
import time

connector = SAPConnector()

for i in range(10):
    print(f"\nIteration {i+1}/10")
    
    if connector.connect():
        print("✓ Connected")
        
        # Do some work
        connector.navigate_to_transaction('MD04')
        time.sleep(2)
        connector.navigate_to_transaction('KO03')
        time.sleep(2)
        
        # Check still connected
        if connector.is_connected:
            print("✓ Still connected")
        else:
            print("✗ Connection lost")
            break
    else:
        print("✗ Connection failed")
        break
    
    time.sleep(5)

print("\n✓ Stability test complete")
```

**Expected Result:**
```
All 10 iterations pass
No connection losses
No memory leaks
```

---

## Test Results Template

Use this template to document your test results:

```
================================
SAP RPA TEST RESULTS
================================
Date: __________
Tester: __________
SAP System: __________

COMPONENT TESTS
---------------
[ ] 1.1 SAP Connection
[ ] 1.2 Transaction Navigation
[ ] 1.3 Field Fill
[ ] 1.4 Field Read
[ ] 1.5 MatRes Detection
[ ] 1.6 Excel Reading
[ ] 1.7 Excel Writing

INTEGRATION TESTS
----------------
[ ] 2.1 MD04 Single Plant
[ ] 2.2 MD04 Multi-Plant
[ ] 2.3 Scenario Manager
[ ] 2.4 ERF Workflow

END-TO-END TESTS
----------------
[ ] 3.1 Complete Workflow - Scenario 1
[ ] 3.2 Complete Workflow - Scenario 2
[ ] 3.3 Batch Processing - Small
[ ] 3.4 Batch Processing - Mixed

STRESS TESTS
------------
[ ] 4.1 Large Batch (___materials)
    Time: ___ min, Success Rate: ___%
[ ] 4.2 Stability Test

ISSUES FOUND
------------
1. ____________________
2. ____________________
3. ____________________

OVERALL STATUS
--------------
[ ] PASS - Ready for production
[ ] PASS WITH ISSUES - Works but has minor issues
[ ] FAIL - Major issues, not ready

NOTES
-----
_______________________
_______________________
```

---

## Regression Testing

After making changes, rerun these critical tests:

```
□ Test 1.1 - SAP Connection
□ Test 1.3 - Field Fill  
□ Test 2.1 - MD04 Single Plant
□ Test 3.1 - Complete Workflow
□ Test 3.3 - Batch Processing
```

---

## Continuous Monitoring

In production, monitor:

```
✓ Success rate per day
✓ Average processing time
✓ Error patterns
✓ Field ID changes (SAP updates)
✓ Performance degradation
```

---

**Testing is complete when:**
- ✅ All Level 1 tests pass
- ✅ At least Test 2.1, 2.2, 2.3 pass
- ✅ At least Test 3.1, 3.3 pass
- ✅ No critical issues found
- ✅ Performance is acceptable

**Then you're ready for production use! 🚀**
