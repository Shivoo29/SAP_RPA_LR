# SAP RPA Project Restructure Plan

## New Project Structure

```
sap_rpa_project/
│
├── main.py                          # Main entry point
├── config.py                        # Configuration management
├── requirements.txt                 # Dependencies
├── README.md                        # Project documentation
│
├── core/                            # Core SAP automation modules
│   ├── __init__.py
│   ├── sap_connector.py            # SAP GUI connection handler
│   ├── field_manager.py            # Field detection and interaction
│   ├── transaction_base.py         # Base class for all transactions
│   └── exceptions.py               # Custom exceptions
│
├── transactions/                    # Transaction-specific modules
│   ├── __init__.py
│   ├── md04_handler.py             # MD04 transaction handler
│   ├── ko03_handler.py             # KO03 transaction handler
│   ├── zerf_handler.py             # ZERF transaction handler
│   └── transaction_factory.py      # Factory for transaction handlers
│
├── workflows/                       # Multi-step workflow orchestration
│   ├── __init__.py
│   ├── scenario_manager.py         # Manages different scenarios
│   ├── matres_workflow.py          # MatRes finding workflow
│   ├── erf_workflow.py             # ERF dashboard workflow
│   └── fallback_handler.py         # Handles fallback scenarios
│
├── data/                            # Data processing and export
│   ├── __init__.py
│   ├── excel_manager.py            # Excel import/export
│   ├── data_validator.py           # Data validation
│   └── data_models.py              # Data structures
│
├── gui/                             # GUI components
│   ├── __init__.py
│   ├── main_window.py              # Main GUI window
│   ├── config_dialog.py            # Configuration dialog
│   └── progress_tracker.py         # Progress tracking UI
│
├── web_automation/                  # Selenium-based web automation
│   ├── __init__.py
│   ├── erf_dashboard.py            # ERF dashboard automation
│   └── web_scraper.py              # Web scraping utilities
│
├── vbs_scripts/                     # VBS scripts integration
│   ├── erf_dashboard_1.vbs         # First ERF scenario
│   ├── erf_dashboard_2.vbs         # Second ERF scenario
│   └── vbs_executor.py             # Python wrapper for VBS execution
│
├── logs/                            # Log files (gitignored)
│   └── .gitkeep
│
├── output/                          # Output files (gitignored)
│   └── .gitkeep
│
├── tests/                           # Unit tests
│   ├── __init__.py
│   ├── test_md04.py
│   └── test_workflows.py
│
└── docs/                            # Documentation
    ├── BRD_Placeholder_HandOff.md  # Converted from .docx
    ├── WORKFLOW_SCENARIOS.md       # All scenario documentation
    └── API_REFERENCE.md            # Code documentation
```

## Module Breakdown

### 1. Core Modules

#### `core/sap_connector.py`
```python
class SAPConnector:
    - connect_to_sap()
    - verify_connection()
    - get_session()
    - disconnect()
```

#### `core/field_manager.py`
```python
class FieldManager:
    - find_field(field_id)
    - fill_field(field_id, value)
    - get_field_value(field_id)
    - scan_fields()
    - make_field_editable()
```

#### `core/transaction_base.py`
```python
class TransactionBase:
    - navigate_to_transaction(tcode)
    - execute_query()
    - check_for_errors()
    - extract_data()
```

### 2. Transaction Handlers

#### `transactions/md04_handler.py`
```python
class MD04Handler(TransactionBase):
    - set_plant(plant_number)
    - enter_material(material_number)
    - find_matres()
    - get_matres_details()
    - try_multiple_plants(plant_list)
```

#### `transactions/ko03_handler.py`
```python
class KO03Handler(TransactionBase):
    - enter_order_number(order_no)
    - extract_order_details()
```

#### `transactions/zerf_handler.py`
```python
class ZERFHandler(TransactionBase):
    - set_date_range(start, end)
    - execute_report()
    - extract_results()
```

### 3. Workflow Orchestration

#### `workflows/scenario_manager.py`
```python
class ScenarioManager:
    - execute_scenario_1()  # Standard MatRes found
    - execute_scenario_2()  # MatRes not found → ERF Dashboard
    - execute_scenario_3()  # ERF → KO03 workflow
    - handle_exceptions()
```

#### `workflows/matres_workflow.py`
```python
class MatResWorkflow:
    - search_in_plants(material, plant_list)
    - fallback_to_erf()
    - collect_data()
```

### 4. Data Management

#### `data/excel_manager.py`
```python
class ExcelManager:
    - read_input_file(file_path)
    - validate_input_data()
    - write_output_file(data)
    - format_excel_output()
```

### 5. GUI Components

#### `gui/main_window.py`
```python
class MainWindow:
    - setup_ui()
    - plant_selection_dropdown()
    - scenario_selection()
    - progress_tracking()
    - results_display()
```

## Implementation Plan

### Phase 1: Core Restructure (Priority 1)
1. Extract `endgame_SAP.py` into modular components
2. Create base classes and interfaces
3. Implement SAP connector and field manager

### Phase 2: Multiple Plant Support (Priority 1)
1. Extend MD04Handler with plant selection
2. Implement plant iteration logic
3. Add GUI controls for plant selection

### Phase 3: Scenario Handling (Priority 2)
1. Implement ScenarioManager
2. Create fallback workflows
3. Integrate VBS scripts

### Phase 4: Web Automation (Priority 2)
1. Clean up selenium_try.py
2. Create ERF dashboard automation
3. Integrate with main workflow

### Phase 5: Data & Output (Priority 3)
1. Standardize data models
2. Create comprehensive Excel output
3. Implement error reporting

### Phase 6: Polish & Testing (Priority 3)
1. Add unit tests
2. Error handling improvements
3. Documentation
4. GUI enhancements

## Configuration Structure

### `config.py`
```python
class Config:
    # SAP Connection
    SAP_CONNECTION_DETAILS = {...}
    
    # Plant Numbers
    AVAILABLE_PLANTS = ['1000', '2000', '1020', '1900']
    DEFAULT_PLANT = '1000'
    
    # Field IDs by Transaction
    MD04_FIELDS = {...}
    KO03_FIELDS = {...}
    ZERF_FIELDS = {...}
    
    # Workflow Settings
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 30
    
    # Output Settings
    OUTPUT_DIRECTORY = './output'
    LOG_DIRECTORY = './logs'
```

## Next Steps

1. **Immediate**: Create the new folder structure
2. **Day 1**: Extract and modularize MD04 logic from endgame_SAP.py
3. **Day 2**: Implement multi-plant support
4. **Day 3**: Create scenario manager and fallback logic
5. **Day 4**: Integrate web automation
6. **Day 5**: Testing and refinement

## Scenarios to Handle

### Scenario 1: MatRes Found in Plant 1000
- MD04 → Enter Material → Select Plant 1000 → Find MatRes → Extract Data

### Scenario 2: MatRes Not Found in 1000, Try Other Plants
- MD04 → Enter Material → Try Plant 1000 (fail) → Try 2000 → Try 1020 → Try 1900
- If found in any plant → Extract Data
- If not found in any plant → Go to Scenario 3

### Scenario 3: MatRes Not Found Anywhere → ERF Dashboard
- Cannot find MatRes in any plant
- Switch to ERF Dashboard (Web automation)
- Get ERF number
- Use VBS Script 1 to extract initial data
- Go to Scenario 4

### Scenario 4: ERF Dashboard → KO03
- From ERF Dashboard, get Order Number
- Navigate to KO03
- Enter Order Number
- Extract order details using VBS Script 2

## Files to Keep/Modify/Archive

### Keep & Refactor:
- endgame_SAP.py → Break into modules
- sap_field_finder.py → Integrate into field_manager.py
- selenium_try.py → Integrate into erf_dashboard.py

### Keep As-Is:
- Script_ERF_dash_board_1.vbs
- Script_ERF_dash_board_2.vbs
- BRD_Placeholder_HandOff.docx

### Archive:
- Move all files in failed_prototypes/ to archive/
- Move test Excel files to archive/
- Keep requirements.txt but update it

### Remove:
- .bat files (for now)
- Numbered files (0.13.5, 0.3.8, etc.)
- ~$ temporary files
- HTML iframe files
