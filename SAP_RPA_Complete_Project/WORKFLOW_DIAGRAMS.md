# SAP RPA - Workflow Diagrams

## Main Automation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      START AUTOMATION                            │
│                                                                  │
│  User Input: Material Number(s) + Plant Selection               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Connect to SAP GUI   │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  For Each Material:   │
         └───────────┬───────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │         SCENARIO 1: MD04 Search        │
    │                                        │
    │  1. Navigate to MD04                  │
    │  2. Enter Material Number             │
    │  3. Try Plant 1000                    │
    │     ├─ MatRes Found? ──→ YES ──┐     │
    │     └─ NO → Try Plant 2000      │     │
    │         ├─ MatRes Found? ─→ YES ┘     │
    │         └─ NO → Try Plant 1020        │
    │             ├─ MatRes Found? → YES ┐  │
    │             └─ NO → Try Plant 1900  │  │
    │                 ├─ Found? → YES ────┘  │
    │                 └─ NO → SCENARIO 2    │
    └────────────────┬───────────────────────┘
                     │
         ┌───────────┴─────────────┐
         │ MatRes Found?           │
         └─────┬──────────┬────────┘
               │          │
           YES │          │ NO
               │          │
               ▼          ▼
    ┌──────────────┐  ┌──────────────────────────┐
    │ Extract Data │  │   SCENARIO 2: ERF        │
    │ from MD04    │  │   Dashboard Fallback     │
    │              │  │                          │
    │ • Material   │  │ 1. Launch Edge Browser   │
    │ • Desc       │  │ 2. Navigate to ERF       │
    │ • Recipient  │  │ 3. Search Material       │
    │ • Order      │  │ 4. Extract ERF Data      │
    │ • Plant      │  │ 5. Get Order Number      │
    └──────┬───────┘  └────────┬─────────────────┘
           │                   │
           │                   ▼
           │         ┌────────────────────┐
           │         │  Order Found?      │
           │         └───────┬────────────┘
           │                 │
           │            YES  │  NO
           │                 │  │
           │                 ▼  ▼
           │    ┌────────────────┐  ┌──────────┐
           │    │  SCENARIO 3:   │  │  FAILED  │
           │    │  ERF → KO03    │  └──────────┘
           │    │                │
           │    │ 1. Navigate    │
           │    │    to KO03     │
           │    │ 2. Enter Order │
           │    │ 3. Extract     │
           │    │    Details     │
           │    └────────┬───────┘
           │             │
           └─────────────┴──────────┐
                                    │
                                    ▼
                     ┌──────────────────────────┐
                     │  Combine All Data        │
                     │  • MD04 Data             │
                     │  • ERF Data              │
                     │  • KO03 Data             │
                     │  • Processing Stats      │
                     └──────────┬───────────────┘
                                │
                                ▼
                     ┌──────────────────────────┐
                     │  Add to Results List     │
                     └──────────┬───────────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │  More Materials?        │
                  └───────┬─────────────────┘
                          │
                    YES   │   NO
                          │   │
                  ┌───────┘   └──────┐
                  │                  │
                  ▼                  ▼
         ┌────────────────┐  ┌──────────────────────┐
         │  Next Material │  │  Generate Excel      │
         │  (loop back)   │  │  Output              │
         └────────────────┘  │                      │
                             │  • Part_Data Sheet   │
                             │  • Summary Sheet     │
                             │  • Errors Sheet      │
                             └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │  COMPLETE ✓          │
                             │                      │
                             │  Display Results     │
                             │  Show Statistics     │
                             └──────────────────────┘
```

## Scenario 1: MD04 Multi-Plant Search

```
                    ┌────────────────────┐
                    │   Start MD04       │
                    │   Transaction      │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Enter Material    │
                    │  Number            │
                    └──────────┬─────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │         Multi-Plant Search Loop              │
        │                                              │
        │  Plants = [1000, 2000, 1020, 1900]          │
        └──────────────────────┬──────────────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Set Plant = Next  │
                    │  in List           │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Execute Query     │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Scan for MatRes   │
                    │  Element           │
                    └──────────┬─────────┘
                               │
                ┌──────────────┴───────────────┐
                │                              │
              FOUND                        NOT FOUND
                │                              │
                ▼                              ▼
     ┌──────────────────┐        ┌─────────────────────┐
     │  Double-Click    │        │  More Plants?       │
     │  MatRes          │        └──────┬──────────────┘
     └────────┬─────────┘               │
              │                     YES  │  NO
              ▼                          │  │
     ┌──────────────────┐       ┌───────┘  └────────┐
     │  Press F7 to     │       │                   │
     │  Maximize        │       ▼                   ▼
     └────────┬─────────┘  ┌─────────────┐  ┌──────────────┐
              │            │  Try Next   │  │  Fallback to │
              ▼            │  Plant      │  │  Scenario 2  │
     ┌──────────────────┐ └─────────────┘  └──────────────┘
     │  Extract Data:   │
     │  • Material      │
     │  • Description   │
     │  • Recipient     │
     │  • Order         │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │  SUCCESS ✓       │
     │  Return Data     │
     └──────────────────┘
```

## Scenario 2: ERF Dashboard Workflow

```
                    ┌────────────────────┐
                    │  MatRes Not Found  │
                    │  in Any Plant      │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Launch Edge       │
                    │  WebDriver         │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Navigate to ERF   │
                    │  Dashboard URL     │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Switch to iFrame  │
                    │  (2 levels deep)   │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Select "ALL"      │
                    │  from Plant        │
                    │  Dropdown          │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Enter Material    │
                    │  in ERF Number     │
                    │  Field             │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Click Search      │
                    │  Button            │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Results Found?    │
                    └──────┬─────────────┘
                           │
                      YES  │  NO
                           │  │
              ┌────────────┘  └────────────┐
              │                            │
              ▼                            ▼
   ┌──────────────────┐         ┌──────────────────┐
   │  Click Result    │         │  FAILED          │
   │  Link ("1")      │         │  No Data Found   │
   └────────┬─────────┘         └──────────────────┘
            │
            ▼
   ┌──────────────────┐
   │  Click           │
   │  "Update/View    │
   │  ERF" Button     │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Extract:        │
   │  • Short Desc    │
   │  • Internal      │
   │    Order         │
   │  • Cost Center   │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Execute VBS     │
   │  Script 1        │
   │  (Additional     │
   │  Data)           │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Order Number    │
   │  Available?      │
   └────────┬─────────┘
            │
       YES  │  NO
            │  │
    ┌───────┘  └──────────────┐
    │                         │
    ▼                         ▼
┌────────────┐    ┌─────────────────────┐
│ Go to      │    │  SUCCESS ✓          │
│ Scenario 3 │    │  Return ERF Data    │
│ (KO03)     │    └─────────────────────┘
└────────────┘
```

## Scenario 3: KO03 Processing

```
                    ┌────────────────────┐
                    │  Order Number      │
                    │  from ERF          │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Navigate to KO03  │
                    │  Transaction       │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Enter Order       │
                    │  Number            │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Press Enter       │
                    │  (Execute Query)   │
                    └──────────┬─────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │  Order Found?      │
                    └──────┬─────────────┘
                           │
                      YES  │  NO
                           │  │
              ┌────────────┘  └────────────┐
              │                            │
              ▼                            ▼
   ┌──────────────────┐         ┌──────────────────┐
   │  Extract Order   │         │  FAILED          │
   │  Details:        │         │  Order Not Found │
   │  • Order Type    │         └──────────────────┘
   │  • Description   │
   │  • Cost Center   │
   │  • Plant         │
   │  • Status        │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Execute VBS     │
   │  Script 2        │
   │  (Additional     │
   │  Order Data)     │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  Combine:        │
   │  • ERF Data      │
   │  • KO03 Data     │
   │  • VBS Data      │
   └────────┬─────────┘
            │
            ▼
   ┌──────────────────┐
   │  SUCCESS ✓       │
   │  Complete Data   │
   │  Package         │
   └──────────────────┘
```

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE (GUI)                      │
│                                                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐ │
│  │  Material  │  │   Plant    │  │  Fallback  │  │ Progress │ │
│  │   Input    │  │ Selection  │  │  Options   │  │ Tracking │ │
│  └────────────┘  └────────────┘  └────────────┘  └──────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SCENARIO MANAGER                             │
│                                                                  │
│  • Orchestrates workflow                                        │
│  • Manages fallback logic                                       │
│  • Tracks statistics                                            │
└──────────┬──────────────────┬───────────────────┬──────────────┘
           │                  │                   │
           ▼                  ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│  MD04 Handler    │ │  ERF Workflow    │ │  KO03 Handler    │
│                  │ │                  │ │                  │
│ • Multi-plant    │ │ • Web automation │ │ • Order query    │
│ • MatRes search  │ │ • Selenium       │ │ • Data extract   │
│ • Data extract   │ │ • VBS Script 1   │ │ • VBS Script 2   │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                     │
         └────────────────────┼─────────────────────┘
                              │
                              ▼
         ┌────────────────────────────────────────┐
         │         SAP CONNECTOR                  │
         │                                        │
         │  • Connection management               │
         │  • Session handling                    │
         │  • Error checking                      │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │         FIELD MANAGER                  │
         │                                        │
         │  • Field detection                     │
         │  • Data extraction                     │
         │  • MatRes scanning                     │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │        DATA MODELS                     │
         │                                        │
         │  • ProcessingResult                    │
         │  • MD04Data, ERFData, KO03Data        │
         │  • BatchProcessingReport               │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │        EXCEL MANAGER                   │
         │                                        │
         │  • Read input files                    │
         │  • Format output                       │
         │  • Generate reports                    │
         └────────────┬───────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────────────────┐
         │         OUTPUT FILES                   │
         │                                        │
         │  📊 Part_Data.xlsx                     │
         │  📈 Summary Statistics                 │
         │  ❌ Error Reports                       │
         └────────────────────────────────────────┘
```

## Module Interaction Map

```
main.py
  │
  ├─ config.py ────────────────────── (All modules read config)
  │
  ├─ gui/main_window.py
  │    │
  │    ├─ core/sap_connector.py
  │    │    └─ pythoncom, win32com
  │    │
  │    ├─ workflows/scenario_manager.py
  │    │    │
  │    │    ├─ transactions/md04_handler.py
  │    │    │    └─ core/field_manager.py
  │    │    │
  │    │    ├─ workflows/erf_workflow.py
  │    │    │    └─ selenium, subprocess (VBS)
  │    │    │
  │    │    └─ transactions/ko03_handler.py
  │    │         └─ core/field_manager.py
  │    │
  │    └─ data/excel_manager.py
  │         └─ pandas, openpyxl
  │
  └─ data/data_models.py
       └─ dataclasses, enum
```

---

**Legend:**
- `─►` : Data flow
- `─┐` : Decision point  
- `┌─┘` : Branch merge
- `✓` : Success point
- `❌` : Failure point
