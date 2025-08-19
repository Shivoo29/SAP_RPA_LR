"""
@echo off
echo Creating SAP MD04 RPA Executable...
echo.

echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist SAP_MD04_RPA.spec del SAP_MD04_RPA.spec

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "SAP_MD04_RPA" ^
    --hidden-import=tkinter ^
    --hidden-import=pandas ^
    --hidden-import=pyautogui ^
    --hidden-import=cv2 ^
    --hidden-import=PIL ^
    --hidden-import=win32gui ^
    --hidden-import=win32con ^
    --icon=sap_icon.ico ^
    main.py

echo.
echo Copying configuration files...
if exist dist (
    copy sap_rpa_config.json dist\
    if not exist dist\logs mkdir dist\logs
    if not exist dist\templates mkdir dist\templates
)

echo.
echo Executable created in dist\ folder
echo.
pause
"""
