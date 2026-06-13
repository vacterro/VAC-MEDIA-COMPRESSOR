@echo off
echo Building SMART VAC MEDIA COMPRESSOR...

:: Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo PyInstaller is not installed. Installing it now...
    pip install pyinstaller
)

echo Running PyInstaller...
pyinstaller --noconfirm --onedir --windowed --name "SmartVacMediaCompressor" "main.py"

echo Build complete. Check the 'dist' folder.
pause
