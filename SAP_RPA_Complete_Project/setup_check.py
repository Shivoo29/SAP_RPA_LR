"""
Setup Helper Script
===================
Helps with initial project setup and validation.
"""

import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories."""
    directories = ['logs', 'output', 'vbs_scripts']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}/")


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'pandas',
        'openpyxl',
        'win32com',
        'selenium',
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True


def check_sap_connection():
    """Check if SAP GUI is available."""
    try:
        import win32com.client
        import pythoncom
        
        pythoncom.CoInitialize()
        sap_gui = win32com.client.GetObject("SAPGUI")
        
        if sap_gui:
            print("✓ SAP GUI is available")
            return True
        else:
            print("✗ SAP GUI not found")
            return False
            
    except Exception as e:
        print(f"✗ SAP GUI check failed: {e}")
        return False


def check_edge_driver():
    """Check if Edge WebDriver exists."""
    from config import Config
    
    driver_path = Path(Config.EDGE_DRIVER_PATH)
    
    if driver_path.exists():
        print(f"✓ Edge WebDriver found at: {driver_path}")
        return True
    else:
        print(f"✗ Edge WebDriver NOT found at: {driver_path}")
        print("  Download from: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
        return False


def check_vbs_scripts():
    """Check if VBS scripts exist."""
    from config import Config
    
    scripts = [
        Config.VBS_ERF_SCRIPT_1,
        Config.VBS_ERF_SCRIPT_2
    ]
    
    all_found = True
    
    for script in scripts:
        if script.exists():
            print(f"✓ VBS script found: {script.name}")
        else:
            print(f"✗ VBS script NOT found: {script.name}")
            all_found = False
    
    return all_found


def check_config():
    """Check if config is properly set up."""
    from config import Config
    
    issues = []
    
    # Check field IDs
    if not Config.MD04_FIELDS.get('material_field'):
        issues.append("MD04 material_field not configured")
    
    # Check plants
    if not Config.AVAILABLE_PLANTS:
        issues.append("No plants configured")
    
    if issues:
        print("✗ Configuration issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ Configuration looks good")
        return True


def main():
    """Run setup checks."""
    print("="*60)
    print("SAP RPA - Setup Helper")
    print("="*60)
    print()
    
    print("1. Creating directories...")
    create_directories()
    print()
    
    print("2. Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("3. Checking SAP GUI...")
    sap_ok = check_sap_connection()
    print()
    
    print("4. Checking Edge WebDriver...")
    edge_ok = check_edge_driver()
    print()
    
    print("5. Checking VBS scripts...")
    vbs_ok = check_vbs_scripts()
    print()
    
    print("6. Checking configuration...")
    config_ok = check_config()
    print()
    
    print("="*60)
    print("SETUP SUMMARY")
    print("="*60)
    
    all_checks = [
        ("Dependencies", deps_ok),
        ("SAP GUI", sap_ok),
        ("Edge WebDriver", edge_ok),
        ("VBS Scripts", vbs_ok),
        ("Configuration", config_ok)
    ]
    
    passed = sum(1 for _, ok in all_checks if ok)
    total = len(all_checks)
    
    for check_name, ok in all_checks:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"{check_name:20s} {status}")
    
    print()
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("🎉 All checks passed! You're ready to run the application.")
        print()
        print("Next steps:")
        print("1. Run: python main.py")
        print("2. Click 'Connect to SAP'")
        print("3. Start automation!")
    else:
        print()
        print("⚠️ Some checks failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Start SAP Logon and log in")
        print("3. Download Edge WebDriver if missing")
        print("4. Copy your VBS scripts to vbs_scripts/ folder")
        print("5. Update field IDs in config.py using sap_field_finder.py")


if __name__ == "__main__":
    main()
