@echo off
rem Builds a single-file Windows executable: dist\DrudeLorentz.exe
rem Run from anywhere: double-click or "build_exe.bat" in a terminal.

cd /d "%~dp0"

.venv\Scripts\pyinstaller ^
    --noconfirm --clean ^
    --onefile --windowed ^
    --name DrudeLorentz ^
    --exclude-module tkinter ^
    --exclude-module pytest ^
    main.py

echo.
echo Done: dist\DrudeLorentz.exe
