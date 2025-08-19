from setuptools import setup, find_packages

setup(
    name="SAP-MD04-RPA",
    version="1.0.0",
    description="Robotic Process Automation for SAP MD04 Part Description Extraction",
    author="Shivam Kumar Jha",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.3.0",
        "pyautogui>=0.9.54",
        "opencv-python>=4.5.0",
        "Pillow>=8.0.0",
        "pytesseract>=0.3.8",
        "pywin32>=227",
        "openpyxl>=3.0.7",
        "keyboard>=0.13.5",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "sap-rpa=main:main",
        ],
    },
)