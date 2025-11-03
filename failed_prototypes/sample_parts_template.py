#!/usr/bin/env python3
"""
Sample Part Numbers Template Creator
===================================
Creates sample Excel templates that users can use to input their part numbers
for batch processing in the Enhanced SAP Automation tool.
"""

import pandas as pd
from datetime import datetime
import os

def create_sample_template():
    """Create a sample Excel template with example part numbers."""
    
    # Sample data with various part number formats
    sample_data = [
        {"Part Number": "857-A65473-106", "MRP Area": "1000"},
        {"Part Number": "ABC123XYZ", "MRP Area": "1000"},
        {"Part Number": "PART-001-REV-A", "MRP Area": "2000"},
        {"Part Number": "1234567890", "MRP Area": "1000"},
        {"Part Number": "COMP-WIDGET-789", "MRP Area": "3000"},
        {"Part Number": "ASSY-TOP-LEVEL-001", "MRP Area": "1000"},
        {"Part Number": "SUB-COMPONENT-456", "MRP Area": "1000"},
        {"Part Number": "RAW-MATERIAL-123", "MRP Area": "2000"},
        {"Part Number": "FINISHED-GOODS-999", "MRP Area": "1000"},
        {"Part Number": "SPARE-PART-555", "MRP Area": "1000"},
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SAP_Parts_Template_{timestamp}.xlsx"
    
    # Create Excel file with multiple sheets
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Sheet 1: Sample Data
        df.to_excel(writer, sheet_name='Sample Parts', index=False)
        
        # Sheet 2: Empty Template
        empty_template = pd.DataFrame(columns=['Part Number', 'MRP Area'])
        # Add 50 empty rows for user input
        for i in range(50):
            empty_template.loc[i] = ['', '1000']
        empty_template.to_excel(writer, sheet_name='Empty Template', index=False)
        
        # Sheet 3: Instructions
        instructions = pd.DataFrame({
            'Instructions': [
                "HOW TO USE THIS TEMPLATE",
                "",
                "1. Use the 'Empty Template' sheet to add your part numbers",
                "2. Fill in the 'Part Number' column with your material codes",
                "3. Fill in the 'MRP Area' column (default is 1000 if left blank)",
                "4. Save the file when done",
                "5. Load this file in the Enhanced SAP Automation tool",
                "",
                "COLUMN DESCRIPTIONS:",
                "• Part Number: The material/component code from SAP",
                "• MRP Area: The MRP planning area (optional, defaults to 1000)",
                "",
                "SUPPORTED FORMATS:",
                "• Excel files (.xlsx, .xls)",
                "• CSV files (.csv)",
                "",
                "TIPS:",
                "• You can have up to 1000 part numbers in one file",
                "• Make sure part numbers are exactly as they appear in SAP",
                "• Remove any empty rows to avoid processing errors",
                "• The tool will skip invalid/empty part numbers automatically",
                "",
                "SAMPLE DATA:",
                "Check the 'Sample Parts' sheet for examples of valid part numbers"
            ]
        })
        instructions.to_excel(writer, sheet_name='Instructions', index=False)
    
    print(f"✅ Created sample template: {filename}")
    print(f"📁 File location: {os.path.abspath(filename)}")
    print("\n📋 Template contains:")
    print("   • Sample Parts sheet: Example part numbers")
    print("   • Empty Template sheet: Ready for your data")
    print("   • Instructions sheet: Detailed usage guide")
    
    return filename

def create_csv_template():
    """Create a simple CSV template."""
    
    sample_data = [
        {"Part Number": "857-A65473-106", "MRP Area": "1000"},
        {"Part Number": "ABC123XYZ", "MRP Area": "1000"},
        {"Part Number": "PART-001-REV-A", "MRP Area": "2000"},
    ]
    
    df = pd.DataFrame(sample_data)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SAP_Parts_Template_{timestamp}.csv"
    
    df.to_csv(filename, index=False)
    
    print(f"✅ Created CSV template: {filename}")
    print(f"📁 File location: {os.path.abspath(filename)}")
    
    return filename

def create_large_sample_template(num_parts=100):
    """Create a large sample template for testing batch processing."""
    
    print(f"🔄 Creating large sample template with {num_parts} parts...")
    
    # Generate sample part numbers
    sample_data = []
    mrp_areas = ["1000", "2000", "3000", "1000"]  # Cycle through MRP areas
    
    for i in range(1, num_parts + 1):
        part_formats = [
            f"PART-{i:06d}",
            f"COMP-{i:04d}-REV-A",
            f"ASSY-TOP-{i:03d}",
            f"{i:09d}",
            f"MAT-{i:05d}-{chr(65 + (i % 26))}"
        ]
        
        part_number = part_formats[i % len(part_formats)]
        mrp_area = mrp_areas[i % len(mrp_areas)]
        
        sample_data.append({
            "Part Number": part_number,
            "MRP Area": mrp_area
        })
    
    df = pd.DataFrame(sample_data)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"SAP_Large_Sample_{num_parts}parts_{timestamp}.xlsx"
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Large Sample', index=False)
        
        # Add summary sheet
        summary = pd.DataFrame({
            'Summary': [
                f"LARGE SAMPLE TEMPLATE - {num_parts} PARTS",
                "",
                f"Total Parts: {num_parts}",
                f"Unique MRP Areas: {len(set(mrp_areas))}",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "USE FOR TESTING:",
                "• Batch processing capabilities",
                "• Error handling and recovery",
                "• Excel export functionality",
                "• Progress tracking",
                "",
                "CAUTION:",
                "• This will process many parts in SAP",
                "• Ensure you have proper SAP access",
                "• Monitor the process closely",
                "• Stop if any issues occur"
            ]
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"✅ Created large sample template: {filename}")
    print(f"📊 Contains {num_parts} sample part numbers")
    print(f"📁 File location: {os.path.abspath(filename)}")
    
    return filename

def main():
    """Main function to create templates."""
    print("="*70)
    print("📋 SAP AUTOMATION - TEMPLATE CREATOR")
    print("="*70)
    print("This tool creates Excel/CSV templates for the Enhanced SAP Automation")
    print()
    
    while True:
        print("Choose template type:")
        print("1. 📊 Standard Excel Template (recommended)")
        print("2. 📄 Simple CSV Template")
        print("3. 🔢 Large Sample Template (for testing)")
        print("4. ❌ Exit")
        
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                print("\n🔄 Creating standard Excel template...")
                filename = create_sample_template()
                print(f"\n🎉 Template created successfully!")
                print(f"Next steps:")
                print(f"1. Open {filename} in Excel")
                print(f"2. Use the 'Empty Template' sheet to add your part numbers")
                print(f"3. Save the file")
                print(f"4. Load it in the Enhanced SAP Automation tool")
                
            elif choice == '2':
                print("\n🔄 Creating CSV template...")
                filename = create_csv_template()
                print(f"\n🎉 CSV template created successfully!")
                print(f"Next steps:")
                print(f"1. Open {filename} in Excel or any text editor")
                print(f"2. Add your part numbers following the sample format")
                print(f"3. Save the file")
                print(f"4. Load it in the Enhanced SAP Automation tool")
                
            elif choice == '3':
                try:
                    num_parts = int(input("Enter number of sample parts (10-1000): ").strip())
                    if 10 <= num_parts <= 1000:
                        print(f"\n🔄 Creating large template with {num_parts} parts...")
                        filename = create_large_sample_template(num_parts)
                        print(f"\n🎉 Large template created successfully!")
                        print(f"⚠️  WARNING: This template contains {num_parts} parts")
                        print(f"Use this ONLY for testing the automation tool!")
                    else:
                        print("❌ Please enter a number between 10 and 1000")
                        continue
                except ValueError:
                    print("❌ Please enter a valid number")
                    continue
                    
            elif choice == '4':
                print("\n👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4")
                continue
            
            # Ask if user wants to create another template
            print("\n" + "="*50)
            another = input("Create another template? (y/n): ").strip().lower()
            if another not in ['y', 'yes']:
                print("\n👋 All done! Templates created successfully.")
                break
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

if __name__ == "__main__":
    main()