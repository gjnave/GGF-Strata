@echo off
setlocal EnableExtensions DisableDelayedExpansion
title GetGoingFast - Run Strata
cd /d "%~dp0"

set "GGF_ROOT=%~dp0Strata"
set "STRATA_HOME=%GGF_ROOT%\state"
set "STRATA_INSTALL_DIR=%GGF_ROOT%\runtime"
set "STRATA_COMPONENTS_DIR=%GGF_ROOT%\components"
set "STRATA_PROFILE_DIR=%GGF_ROOT%\profiles"
set "STRATA_RUNTIME_DIR=%GGF_ROOT%\sessions"
set "STRATA_WORKSPACE=%GGF_ROOT%\Workspace"
set "STRATA_MODELS_DIR=%GGF_ROOT%\models"
set "STRATA_CONTROL_DIR=%GGF_ROOT%\app\control"
set "STRATA_HARNESS_DIR=%GGF_ROOT%\app\harness"
set "STRATA_REAL_ENGINE=1"
set "STRATA_NO_REPAIR_ACCESS=1"
set "STRATA_NO_BUNDLED_ENGINE=1"
set "STRATA_BIND=127.0.0.1"
if not defined STRATA_PORT set "STRATA_PORT=8798"
set "PYTHONDONTWRITEBYTECODE=1"
set "PY=%STRATA_CONTROL_DIR%\python\python.exe"

if not exist "%PY%" goto not_installed
if not exist "%GGF_ROOT%\app\node\node.exe" goto not_installed
if not exist "%GGF_ROOT%\member.py" goto not_installed

"%PY%" "%GGF_ROOT%\member.py" start
if errorlevel 1 goto failed
echo Strata is ready at http://127.0.0.1:%STRATA_PORT%/
start "" "http://127.0.0.1:%STRATA_PORT%/"
echo If the browser did not open, enter the address above in your browser.
echo Strata keeps running when you close this window.
pause
exit /b 0

:not_installed
echo Strata is not installed in "%GGF_ROOT%".
echo Run 1-install-strata.bat from this folder first.
goto failed

:failed
echo Strata could not start. Check "%GGF_ROOT%\logs\agent-host.log" for details.
pause
exit /b 1
