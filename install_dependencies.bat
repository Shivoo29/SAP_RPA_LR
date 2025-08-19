"""
@echo off
echo Installing SAP MD04 RPA Dependencies...
echo.

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo.
echo Installing required packages...
pip install pandas>=1.3.0
pip install pyautogui>=0.9.54
pip install opencv-python>=4.5.0
pip install Pillow>=8.0.0
pip install pytesseract>=0.3.8
pip install pywin32>=227
pip install openpyxl>=3.0.7
pip install keyboard>=0.13.5
pip install pyinstaller>=4.5.1

echo.
echo Installation complete!
echo.
echo Next steps:
echo 1. Run initial setup: python main.py setup
echo 2. Start the application: python main.py
echo.
pause
"""