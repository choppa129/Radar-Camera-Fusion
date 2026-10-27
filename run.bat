@echo off
setlocal
cd /d "%~dp0"

REM Run from Anaconda Prompt (Windows x64); no machine-specific F:\ paths.
where conda >nul 2>nul
if errorlevel 1 (
    echo Conda was not found. Open Anaconda Prompt and retry.
    exit /b 1
)
call conda activate fusion
if errorlevel 1 (
    echo Could not activate environment "fusion".
    echo See env\README.md for the installation steps.
    exit /b 1
)
python "src\detect.py"
set "status=%errorlevel%"
if not "%status%"=="0" (
    echo The application exited with an error. Try: python tools\check_env.py
    pause
)
exit /b %status%
