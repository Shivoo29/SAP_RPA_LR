#!/usr/bin/env python3
"""
OrdRes Field Validation Script
================================
Use this script to validate OrdRes field IDs in your SAP environment
before running the full automation.

This script will:
1. Connect to SAP
2. Navigate to MD04 with a test material
3. Try to find OrdRes
4. Attempt to access all configured fields
5. Report which fields work and which need updating
"""

import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.sap_connector import SAPConnector
from core.field_manager import FieldManager
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_ordres_fields():
    """Validate all OrdRes field IDs."""

    print("="*70)
    print("OrdRes Field Validation Script")
    print("="*70)
    print()

    # Get test material from user
    test_material = input("Enter a test material number that has OrdRes: ").strip()
    if not test_material:
        print("❌ No material entered. Exiting.")
        return

    test_plant = input("Enter plant number (default: 1000): ").strip() or "1000"

    print(f"\n📋 Testing with material: {test_material}, plant: {test_plant}")
    print("="*70)

    # Connect to SAP
    print("\n1️⃣  Connecting to SAP...")
    connector = SAPConnector()

    if not connector.connect():
        print("❌ Failed to connect to SAP. Make sure SAP is running.")
        return

    print("✅ Connected to SAP")

    try:
        session = connector.session
        field_mgr = FieldManager(session)
        config = Config()

        # Navigate to MD04
        print("\n2️⃣  Navigating to MD04...")
        connector.navigate_to_transaction('MD04')

        # Enter material and plant
        print(f"3️⃣  Entering material {test_material} and plant {test_plant}...")

        mat_field = session.findById(config.MD04_FIELDS['material_field'])
        mat_field.text = test_material

        plant_field = session.findById(config.MD04_FIELDS['plant_field'])
        plant_field.text = test_plant

        connector.press_enter(wait_time=3)

        # Scan for OrdRes
        print("\n4️⃣  Scanning table for OrdRes...")
        scan_result = field_mgr.scan_md04_table_for_elements()

        if not scan_result['has_ordres']:
            print("❌ OrdRes not found in table!")
            print("   Possible reasons:")
            print("   - Material doesn't have OrdRes in this plant")
            print("   - OrdRes text is different (check SAP screen)")
            print("   - Try a different material/plant")
            return

        print(f"✅ OrdRes found at row {scan_result['ordres_row_index']}")

        # Navigate to OrdRes details
        print("\n5️⃣  Navigating to OrdRes details...")
        table_id = config.get_field_id('MD04_RPM', 'item_list_table')
        table = session.findById(table_id)
        table.getCell(scan_result['ordres_row_index'], 0).setFocus()
        session.findById("wnd[0]").sendVKey(2)  # F2

        import time
        time.sleep(2)

        # Test field IDs
        print("\n6️⃣  Testing OrdRes field IDs...")
        print("-" * 70)

        results = {}

        # Test display button
        print("\n📍 Testing: item_display_button")
        field_id = config.get_field_id('ORDRES', 'item_display_button')
        print(f"   Field ID: {field_id}")
        try:
            button = session.findById(field_id)
            button.press()
            time.sleep(2)
            print("   ✅ Display button found and pressed")
            results['item_display_button'] = True
        except Exception as e:
            print(f"   ⚠️  Display button not found: {e}")
            print("   This is OK if popup doesn't appear")
            results['item_display_button'] = False

        # Test grid shell
        print("\n📍 Testing: grid_shell")
        field_id = config.get_field_id('ORDRES', 'grid_shell')
        print(f"   Field ID: {field_id}")
        try:
            grid = session.findById(field_id)
            grid.pressToolbarButton("SHOW")
            time.sleep(2)
            print("   ✅ Grid shell found and SHOW pressed")
            results['grid_shell'] = True
        except Exception as e:
            print(f"   ❌ Grid shell error: {e}")
            print("   ⚠️  This field ID likely needs updating!")
            results['grid_shell'] = False

        # Test cost center field
        print("\n📍 Testing: cost_center_field")
        field_id = config.get_field_id('ORDRES', 'cost_center_field')
        print(f"   Field ID: {field_id}")
        try:
            field = session.findById(field_id)
            value = field.text.strip()
            print(f"   ✅ Cost center field found: '{value}'")
            results['cost_center_field'] = True
        except Exception as e:
            print(f"   ❌ Cost center field error: {e}")
            print("   ⚠️  This field ID likely needs updating!")
            results['cost_center_field'] = False

        # Test part description field
        print("\n📍 Testing: part_description_field")
        field_id = config.get_field_id('ORDRES', 'part_description_field')
        print(f"   Field ID: {field_id}")
        try:
            field = session.findById(field_id)
            value = field.text.strip()
            print(f"   ✅ Part description field found: '{value}'")
            results['part_description_field'] = True
        except Exception as e:
            print(f"   ❌ Part description field error: {e}")
            print("   ⚠️  This field ID likely needs updating!")
            results['part_description_field'] = False

        # Test order field
        print("\n📍 Testing: order_field")
        field_id = config.get_field_id('ORDRES', 'order_field')
        print(f"   Field ID: {field_id}")
        try:
            field = session.findById(field_id)
            value = field.text.strip()
            print(f"   ✅ Order field found: '{value}'")
            results['order_field'] = True
        except Exception as e:
            print(f"   ❌ Order field error: {e}")
            print("   ⚠️  This field ID likely needs updating!")
            results['order_field'] = False

        # Summary
        print("\n" + "="*70)
        print("VALIDATION SUMMARY")
        print("="*70)

        total = len(results)
        passed = sum(results.values())

        print(f"\n✅ Passed: {passed}/{total}")
        print(f"❌ Failed: {total - passed}/{total}")

        if passed == total:
            print("\n🎉 All fields validated successfully!")
            print("   OrdRes integration should work in production.")
        elif passed >= 3:
            print("\n⚠️  Most fields work, but some need attention.")
            print("   Review the failed fields above and update config.py")
        else:
            print("\n❌ Many fields failed validation.")
            print("   You need to use sap_field_finder.py to discover correct field IDs")

        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)

        if passed < total:
            print("\n1. Use sap_field_finder.py to find correct field IDs:")
            print("   - Navigate to OrdRes screen manually")
            print("   - Run sap_field_finder.py")
            print("   - Record the correct field IDs")
            print("\n2. Update config.py ORDRES_FIELDS with correct IDs")
            print("\n3. Run this validation script again")
        else:
            print("\n✅ Validation complete! You can proceed with production testing.")
            print("\nRecommended next steps:")
            print("1. Test with 1-2 OrdRes materials manually")
            print("2. Check logs for any warnings")
            print("3. Verify extracted data quality")
            print("4. Roll out to larger dataset")

    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        print(f"\n❌ Validation failed with error: {e}")

    finally:
        connector.disconnect()
        print("\n✅ Disconnected from SAP")


if __name__ == "__main__":
    try:
        validate_ordres_fields()
    except KeyboardInterrupt:
        print("\n\n⚠️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
