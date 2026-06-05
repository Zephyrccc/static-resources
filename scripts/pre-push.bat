@echo off
REM
REM Git pre-push hook to convert images to WebP (Windows Batch)
REM Calls the Node.js conversion script
REM

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set REPO_DIR=%SCRIPT_DIR%..

REM Change to repository directory
cd /d "%REPO_DIR%"

REM Run the Node.js conversion script
echo Running pre-push image conversion...
node "%REPO_DIR%\scripts\convert-to-webp.js"

if %ERRORLEVEL% equ 0 (
    echo Image conversion completed successfully.
    exit /b 0
) else (
    echo Warning: Image conversion encountered errors, but continuing with push.
    exit /b 0
)