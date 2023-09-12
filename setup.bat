@echo off
if "%~1"=="" (
    curl -o epic_pkg.zip "https://smarslab-files.s3.amazonaws.com/epic-utils/epic_pkg.zip"
) else (
    mkdir "%~1" 2>nul
    curl -o "%~1\epic_pkg.zip" "https://smarslab-files.s3.amazonaws.com/epic-utils/epic_pkg.zip"
    cd "%~1"
)

curl -o epic_pkg.zip "https://github.com/smarsGroup/EPIC-pkg/archive/master.zip"

curl -o GDAL-3.4.3-cp38-cp38-win_amd64.whl "https://smarslab-files.s3.amazonaws.com/epic-utils/GDAL-3.4.3-cp38-cp38-win_amd64.whl"

pip install GDAL-3.4.3-cp38-cp38-win_amd64.whl

tar -xf epic_pkg.zip


:: Detect the path to the default Python interpreter
for /f %%i in ('where python') do set "interpreter_path=%%i"

if "%interpreter_path%"=="" (
    echo Error: Python interpreter not found.
    exit /b 1
)

:: Update the shebang line of scripts in the scripts directory
cd .\epic_pkg
set "script=%cd%\epic_lib\dispatcher.py"
echo #!%interpreter_path% > temp
type "%script%" >> temp
move /y temp "%script%"
@REM chmod +x "%script%"

set "wrapper_script=%cd%\epic_lib\scripts\epic_pkg.bat"
echo @echo off > "%wrapper_script%"
echo "%script%" %%* >> "%wrapper_script%"
@REM chmod +x "%wrapper_script%"

:: Install Python dependencies
pip install -r requirements.txt

:: Determine if the terminal is Windows Command Prompt
if "%ComSpec%" == "cmd.exe" (
    setx PATH "%PATH%;%cd%\epic_lib\scripts"
    echo Setup for Command Prompt complete!
) else (
    echo You are using a different shell. Please add the path %cd%\epic_lib\scripts to your PATH.
)

echo Restart your terminal or open a new Command Prompt for the changes to take effect!
