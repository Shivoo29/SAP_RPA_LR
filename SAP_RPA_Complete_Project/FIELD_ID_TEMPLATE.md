# Field ID Configuration Template

This template helps you organize field IDs discovered using `sap_field_finder.py`.

## How to Use This Template

1. Run `sap_field_finder.py`
2. Navigate to each transaction (MD04, KO03, etc.)
3. Click "Scan All Fields"
4. Copy field IDs from output
5. Paste into appropriate sections below
6. Copy completed sections to `config.py`

---

## MD04 Transaction Fields

### Input Fields (for entering data)

```python
MD04_FIELDS = {
    # Material Number Field
    "material_field": "",  # Example: "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-MATNR"
    
    # MRP Area Field
    "mrp_area_field": "",  # Example: "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-BERID"
    
    # Plant Field (for switching plants)
    "plant_field": "",  # Example: "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-WERKS"
}
```

**How to find these:**
1. Navigate to MD04 (transaction code /nMD04)
2. Click in each field
3. Run field finder
4. Copy the "Id" value shown

---

### Data Extraction Fields (after MatRes found)

```python
EXTRACTION_FIELDS = {
    # Material/Part Number
    "Material": "",  # Usually: Grid column or text field with material number
    
    # Part Description
    "Part_Description": "",  # Description of the material
    
    # Recipient
    "Recipient": "",  # Who/what receives the material
    
    # Order Number
    "Order": "",  # Production or purchase order number
    
    # Plant
    "Plant": "",  # Plant code where material is located
    
    # MRP Area
    "MRP_Area": "",  # MRP area code
    
    # Additional fields you want to extract:
    # "Quantity": "",
    # "Date": "",
    # "Storage_Location": "",
    # Add more as needed...
}
```

**How to find these:**
1. Navigate to MD04
2. Enter a material that has MatRes
3. Double-click MatRes
4. Press F7 to maximize
5. Click on each field/column you want to extract
6. Run field finder
7. Copy field IDs

**Tips:**
- For grid columns, field IDs often contain "col[X]" where X is column number
- Text fields have "txt" or "ctxt" in the ID
- Labels might not be extractable - look for the actual data field

---

## KO03 Transaction Fields

```python
KO03_FIELDS = {
    # Order Number Input Field
    "order_field": "",  # Example: "/app/con[0]/ses[0]/wnd[0]/usr/ctxtCAUFVD-AUFNR"
    
    # Order Type Field (display)
    "order_type_field": "",
    
    # Description Field
    "description_field": "",
    
    # Cost Center Field
    "cost_center_field": "",
    
    # Plant Field
    "plant_field": "",
    
    # Status Field
    "status_field": "",
    
    # Add more fields as needed...
}
```

**How to find these:**
1. Navigate to KO03
2. Enter a known order number
3. Click through all tabs/sections you need data from
4. Run field finder on each field
5. Copy field IDs

---

## ERF Dashboard Elements

These are web elements (HTML), not SAP GUI fields.

```python
ERF_ELEMENTS = {
    # Plant Dropdown
    "plant_dropdown_id": "aaaa.RpmDashboardView.PlantsDdbk",
    
    # ERF Number Input
    "erf_input_id": "aaaa.RpmDashboardView.ERFNumInp",
    
    # Search Button
    "search_button_id": "aaaa.RpmDashboardView.SearchBtn",
    
    # Result Link
    "result_link_id": "aaaa.RpmDashboardView.ALL_1Lta-text",
    
    # Update/View Button
    "update_button_id": "aaaa.HeaderView.UpdateBtn",
    
    # Data Fields
    "short_desc_id": "aaaa.CreateOrderView.ShortDescInp",
    "internal_order_id": "aaaa.CreateOrderView.InternalOrderInp",
    "cost_center_id": "aaaa.CreateOrderView.CostCenterInp",
}
```

**How to find these:**
1. Open ERF Dashboard in Edge browser
2. Press F12 (Developer Tools)
3. Click "Select Element" tool (arrow icon)
4. Click on the element you want
5. In HTML panel, find the "id" attribute
6. Copy the ID value

**Update these in:** `workflows/erf_workflow.py`

---

## Common Field ID Patterns

Understanding these patterns helps you find field IDs faster:

### SAP GUI Field ID Structure
```
/app/con[X]/ses[Y]/wnd[Z]/usr/[type][name]

Where:
- X = Connection number (usually 0)
- Y = Session number (usually 0)  
- Z = Window number (0 = main, 1+ = popups)
- type = Field type:
  * txt = Text field (display only)
  * ctxt = Text field (editable)
  * cbo = Combobox/dropdown
  * btn = Button
  * chk = Checkbox
  * tbl = Table
- name = Field technical name
```

### Examples
```python
# Material input field
"/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-MATNR"
#                                ^^^^          = editable text
#                                    ^^^^^^^^^^ = field name

# Plant dropdown
"/app/con[0]/ses[0]/wnd[0]/usr/cboRM61R-WERKS"
#                                ^^^          = combobox

# Grid cell
"/app/con[0]/ses[0]/wnd[0]/usr/tblSAPLMGMMTC_OVERVIEW/txtMDTB-MATNR[1,0]"
#                                ^^^                                     = table
#                                                                [X,Y]   = row, column
```

---

## Field Discovery Workflow

### Step 1: Prepare
```
1. Open SAP Logon
2. Log into your SAP system
3. Have sap_field_finder.py ready
4. Have this template open
```

### Step 2: MD04 Input Fields
```
1. Run: python sap_field_finder.py
2. Click "Connect to SAP"
3. In SAP, navigate to: /nMD04
4. In field finder, click "Scan All Fields"
5. Find "Material" field in list
6. Copy its ID to MD04_FIELDS["material_field"] above
7. Repeat for plant_field and mrp_area_field
```

### Step 3: MD04 Extraction Fields
```
1. In MD04, enter a test material: 857-A65473-106
2. Enter plant: 1000
3. Press Enter
4. Double-click MatRes
5. Press F7
6. Now the data screen is maximized
7. In field finder, click "Scan All Fields"
8. For each column/field you want:
   - Click the field in SAP
   - Find it in field finder list
   - Copy ID to EXTRACTION_FIELDS above
```

### Step 4: KO03 Fields
```
1. In SAP, navigate to: /nKO03
2. In field finder, scan for order_field
3. Enter a test order number
4. Press Enter
5. Scan all display fields
6. Copy IDs to KO03_FIELDS above
```

### Step 5: ERF Dashboard Elements
```
1. Open Edge browser
2. Navigate to ERF Dashboard URL
3. Press F12 (Developer Tools)
4. Click each element and find its ID
5. Update ERF_ELEMENTS above
6. Then update workflows/erf_workflow.py
```

---

## Testing Your Field IDs

After updating config.py, test each field:

### Test Input Fields
```python
from core.sap_connector import SAPConnector
from core.field_manager import FieldManager

connector = SAPConnector()
connector.connect()
connector.navigate_to_transaction('MD04')

field_manager = FieldManager(connector.session)

# Test material field
success = field_manager.fill_field(
    "YOUR_MATERIAL_FIELD_ID",
    "857-A65473-106"
)
print(f"Material field: {'✓ Works' if success else '✗ Failed'}")

# Test plant field  
success = field_manager.fill_field(
    "YOUR_PLANT_FIELD_ID",
    "1000"
)
print(f"Plant field: {'✓ Works' if success else '✗ Failed'}")
```

### Test Extraction Fields
```python
# After navigating to data screen
for field_name, field_id in EXTRACTION_FIELDS.items():
    if field_id:  # Only test if ID is set
        value = field_manager.get_field_value(field_id)
        print(f"{field_name}: {value}")
```

---

## Quick Reference

### Most Important Field IDs to Find

**Priority 1 (Critical):**
- [ ] MD04_FIELDS["material_field"] - Can't enter materials without this
- [ ] MD04_FIELDS["plant_field"] - Can't switch plants without this
- [ ] EXTRACTION_FIELDS["Material"] - Need to verify what was extracted

**Priority 2 (Important):**
- [ ] EXTRACTION_FIELDS["Part_Description"] - Good to have
- [ ] EXTRACTION_FIELDS["Recipient"] - Useful data
- [ ] EXTRACTION_FIELDS["Order"] - Needed for KO03 fallback
- [ ] KO03_FIELDS["order_field"] - Needed for Scenario 3

**Priority 3 (Nice to Have):**
- [ ] MD04_FIELDS["mrp_area_field"] - Optional, has default
- [ ] Other extraction fields - Add as needed

---

## Example: Completed Configuration

Here's what a completed section looks like:

```python
MD04_FIELDS = {
    "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-MATNR",
    "mrp_area_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-BERID",
    "plant_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRM61R-WERKS",
}

EXTRACTION_FIELDS = {
    "Material": "/app/con[0]/ses[0]/wnd[0]/usr/tblMDTB/txtMDTB-MATNR[1,0]",
    "Part_Description": "/app/con[0]/ses[0]/wnd[0]/usr/tblMDTB/txtMAKT-MAKTX[2,0]",
    "Recipient": "/app/con[0]/ses[0]/wnd[0]/usr/tblMDTB/txtMDTB-KZLPN[5,0]",
    "Order": "/app/con[0]/ses[0]/wnd[0]/usr/tblMDTB/txtMDTB-DELKZ[8,0]",
    "Plant": "/app/con[0]/ses[0]/wnd[0]/usr/tblMDTB/txtMDTB-WERKS[10,0]",
}

KO03_FIELDS = {
    "order_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctxtCAUFVD-AUFNR",
    "order_type_field": "/app/con[0]/ses[0]/wnd[0]/usr/txtCAUFVD-AUART",
    "description_field": "/app/con[0]/ses[0]/wnd[0]/usr/txtCAUFVD-KTEXT",
}
```

---

## Tips for Success

1. **Be Patient** - Finding all field IDs takes time
2. **Test as You Go** - Don't wait until all fields are done
3. **Document** - Note which fields work and which don't
4. **Screen Position** - Field IDs can change based on screen position
5. **SAP Version** - IDs may differ between SAP versions
6. **Start Simple** - Get basic fields working first
7. **One at a Time** - Test each field individually

---

## Validation Checklist

Before running full automation:

```
□ Found all Priority 1 field IDs
□ Tested material_field - can enter material number
□ Tested plant_field - can switch plants
□ Tested at least one extraction field - can read data
□ Updated config.py with all found IDs
□ Ran setup_check.py
□ Tested single material successfully
□ Ready for batch processing!
```

---

**Next Step:** Copy your completed field IDs to `config.py` and test!
