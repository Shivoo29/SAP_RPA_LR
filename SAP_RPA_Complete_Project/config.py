"""
Configuration Management
========================
Central configuration for SAP RPA system.
"""

from typing import List, Dict
from pathlib import Path


class Config:
    """Central configuration class for SAP RPA."""
    
    # ===== SAP Connection Settings =====
    SAP_CONNECTION_DETAILS = {
        "name": "001. SAP ECC Production (PRD)",
        "system_description": "SAP ERP",
        "sid": "PRD",
        "group_server": "Production PRD",
        "message_server": "pdtcprd01.fermont.lamrc.net"
    }
    
    # ===== Plant Configuration =====
    AVAILABLE_PLANTS = ['1000', '2000', '1020', '1900']
    DEFAULT_PLANT = '1000'
    DEFAULT_MRP_AREA = '1000'
    
    # ===== MD04 Transaction Field IDs =====
    MD04_FIELDS = {
        "material_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-MATNR",
        "mrp_area_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-BERID",
        "plant_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/ctxtRM61R-WERKS",
        "description_field": "/app/con[0]/ses[0]/wnd[0]/usr/tabsTAB300/tabpF01/ssubINCLUDE300:SAPMM61R:0301/txtMT61D-MAKTX",
        "next_part_field": "/app/con[0]/ses[0]/wnd[0]/usr/subINCLUDE8XX:SAPMM61R:0800/ctxtRM61R-MATNR"
    }
    
    # ===== Data Extraction Field IDs =====
    EXTRACTION_FIELDS = {
        "Material": "/app/con[0]/ses[0]/wnd[0]/usr/ctxtRESB-MATNR",
        "Part_Description": "/app/con[0]/ses[0]/wnd[0]/usr/subBLOCK:SAPLKACB:1002/txtTEXT_AUFNR",
        "Recipient": "/app/con[0]/ses[0]/wnd[0]/usr/txtRESB-WEMPF",
        "Order": "/app/con[0]/ses[0]/wnd[0]/usr/subBLOCK:SAPLKACB:1002/ctxtCOBL-AUFNR"
    }

    # ===== OrdRes (Order Reservation) Field IDs =====
    ORDRES_FIELDS = {
        "item_display_button": "wnd[1]/tbar[0]/btn[17]",  # Display button in popup
        "grid_shell": "wnd[0]/usr/cntlGRID_1000/shellcont/shell/shellcont[1]/shell",
        "cost_center_field": "wnd[0]/usr/subBLOCK:SAPLKACB:1002/txtTEXT_KOSTL",
        "part_description_field": "wnd[0]/usr/subBLOCK:SAPLKACB:1002/txtTEXT_AUFNR",
        "order_field": "wnd[0]/usr/subBLOCK:SAPLKACB:1002/ctxtCOBL-AUFNR"
    }
    
    # ===== KO03 Transaction Field IDs =====
    KO03_FIELDS = {
        "order_field": "wnd[0]/usr/ctxtCOAS-AUFNR",
        "order_type_field": "wnd[0]/usr/ctxtCAUFVD-AUART",
        # Add more KO03 fields as needed
    }
    
    # ===== ZERF Transaction Field IDs =====
    ZERF_FIELDS = {
        "start_date_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctextSP$00018-LOW",
        "end_date_field": "/app/con[0]/ses[0]/wnd[0]/usr/ctextSP$00018-HIGH"
    }
    
    # ===== Workflow Settings =====
    MAX_RETRIES = 2  # Reduced from 3 for faster failures
    TIMEOUT_SECONDS = 20  # Reduced from 30
    WAIT_TIME_AFTER_ACTION = 0.5  # Optimized from 2 (70% faster)
    WAIT_TIME_AFTER_QUERY = 1  # Optimized from 3 (66% faster)
    
    # ===== Scenario Settings =====
    ENABLE_MULTI_PLANT_SEARCH = True
    ENABLE_ERF_FALLBACK = True
    ENABLE_KO03_FALLBACK = True
    
    # ===== Output Settings =====
    OUTPUT_DIRECTORY = 'output'
    LOG_DIRECTORY = 'logs'
    OUTPUT_FILE_PREFIX = 'SAP_Export'
    
    # ===== Excel Settings =====
    EXCEL_SHEET_NAMES = {
        'results': 'Part_Data',
        'summary': 'Summary',
        'errors': 'Errors'
    }
    
    # ===== Web Automation Settings =====
    ERF_DASHBOARD_URL = 'https://epp.fremont.lamrc.net/irj/portal?&EPPAP13_0'
    EDGE_DRIVER_PATH = r"c:\Program Files\edgedriver_win64\msedgedriver.exe"
    WEB_TIMEOUT = 30  # Optimized for faster processing
    WEB_RETRY_COUNT = 2  # Reduced from 3 for faster failures

    # ===== Performance Optimization Settings =====
    ENABLE_PARALLEL_PROCESSING = False  # DISABLED: Use sequential mode (50-60% faster with optimizations)
    MAX_PARALLEL_WORKERS = 3  # Number of concurrent SAP sessions (3-5 recommended)
    ENABLE_SMART_PLANT_ORDERING = True  # Reorder plants based on success rate
    ENABLE_AGGRESSIVE_CACHING = True  # Cache plant availability patterns
    
    # ===== VBS Script Paths =====
    VBS_SCRIPT_DIR = Path(__file__).parent / 'vbs_scripts'
    VBS_ERF_SCRIPT_1 = VBS_SCRIPT_DIR / 'erf_dashboard_1.vbs'
    VBS_ERF_SCRIPT_2 = VBS_SCRIPT_DIR / 'erf_dashboard_2.vbs'

    # ===== MD04 RPM Extraction Field IDs =====
    MD04_RPM_EXTRACTION_FIELDS = {
        "item_list_table": "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_1/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ",
        "item_display_button": "wnd[1]/tbar[0]/btn[7]",
        "expand_items_button": "wnd[0]/usr/subSUB0:SAPLMEGUI:0015/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211",
        "rpm_number_field": "wnd[0]/usr/subSUB0:SAPLMEGUI:0015/subSUB2:SAPLMEVIEWS:1100/subSUB2:SAPLMEVIEWS:1200/subSUB1:SAPLMEGUI:1211/tblSAPLMEGUITC_1211/txtMEPO1211-BEDNR[18,0]"
    }

    # ===== MD04 Table ID Alternatives (for robust detection) =====
    # These are known table IDs that may appear in different MD04 screen layouts
    # The system will try these in order, and cache successful ones
    MD04_TABLE_IDS = [
        # Standard layout - Tab 1
        "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_1/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ",

        # Standard layout - Tab 2
        "wnd[0]/usr/subINCLUDE1XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_2/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ",

        # Simplified path (some SAP configurations)
        "wnd[0]/usr/tblSAPMM61RTC_EZ",

        # Grid container layout (alternative rendering)
        "wnd[0]/usr/cntlGRID1/shellcont/shell",

        # Alternative include area
        "wnd[0]/usr/subINCLUDE2XX:SAPMM61R:0780/tabsGL_TAB/tabpGL_1/ssubGL_SUBSCR:SAPMM61R:0750/tblSAPMM61RTC_EZ",

        # Shell control variant
        "wnd[0]/usr/shellcont/shell",
    ]
    
    @classmethod
    def get_plant_list(cls, user_selection: List[str] = None) -> List[str]:
        """
        Get the list of plants to search, based on user selection.
        
        Args:
            user_selection: User-selected plants, or None for all plants
            
        Returns:
            List of plant numbers to search
        """
        if user_selection and len(user_selection) > 0:
            return user_selection
        return cls.AVAILABLE_PLANTS
    
    @classmethod
    def get_field_id(cls, transaction: str, field_name: str) -> str:
        """
        Get field ID for a specific transaction and field name.
        
        Args:
            transaction: Transaction code (MD04, KO03, etc.)
            field_name: Name of the field
            
        Returns:
            Field ID string
        """
        field_map = {
            'MD04': cls.MD04_FIELDS,
            'KO03': cls.KO03_FIELDS,
            'ZERF': cls.ZERF_FIELDS,
            'MD04_RPM': cls.MD04_RPM_EXTRACTION_FIELDS,
            'ORDRES': cls.ORDRES_FIELDS,
        }
        
        fields = field_map.get(transaction.upper(), {})
        return fields.get(field_name, '')
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            True if configuration is valid
        """
        # Check if plant list is not empty
        if not cls.AVAILABLE_PLANTS:
            return False
        
        # Check if essential field IDs exist
        if not cls.MD04_FIELDS.get('material_field'):
            return False
        
        # Check if output directory can be created
        try:
            output_dir = Path(cls.OUTPUT_DIRECTORY)
            output_dir.mkdir(exist_ok=True)
            return True
        except Exception:
            return False
