@echo off
:: ============================================================
:: LATM - Mobile Test Framework Startup Script (Windows)
:: ============================================================
:: Features:
::   1. Activate virtual environment
::   2. Set ANDROID_HOME (project built-in platform-tools)
::   3. Interactive command menu
:: ============================================================

title LATM - Mobile Test Framework

:: --- Set Android SDK environment ---
set "ANDROID_HOME=%~dp0.."
set "ANDROID_SDK_ROOT=%~dp0.."
set "PATH=%~dp0..\platform-tools;%PATH%"

echo.
echo ============================================================
echo   LATM - Mobile Test Framework
echo   Low-Altitude Airspace Management System
echo ============================================================
echo.
echo [ENV] ANDROID_HOME=%~dp0..
echo.

:: --- Activate virtual environment ---
call "%~dp0.venv\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate venv. Check .venv directory.
    pause
    exit /b 1
)
echo [OK] Virtual environment activated (.venv)
echo.

:: --- Python info ---
python --version
echo.

:: --- ADB check ---
adb devices 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] ADB not found in PATH, check platform-tools config
) else (
    echo [OK] ADB ready
)
echo.

:: --- Menu ---
:menu
echo ============================================================
echo   Available Commands:
echo ============================================================
echo.
echo   [1] Start Appium Server (new window)
echo   [2] Run smoke tests
echo   [3] Run all tests (with report)
echo   [4] Run login module tests
echo   [5] Run home module tests
echo   [6] Run flight module tests
echo   [7] Run news module tests
echo   [8] Run mine module tests
echo   [9] Show device info
echo   [A] Generate Allure report
echo   [S] Start page server (serve HTML prototypes)
echo   [T] Test with prototypes (server + appium + manual)
echo   [M] Enter manual/interactive test mode
echo   [I] Install APK to device
echo   [Q] Quit
echo.
echo ============================================================
set /p choice="Select [1-9/A/S/T/M/I/Q]: "

if /i "%choice%"=="1" goto start_appium
if /i "%choice%"=="2" goto smoke_test
if /i "%choice%"=="3" goto all_test
if /i "%choice%"=="4" goto login_test
if /i "%choice%"=="5" goto home_test
if /i "%choice%"=="6" goto flight_test
if /i "%choice%"=="7" goto news_test
if /i "%choice%"=="8" goto mine_test
if /i "%choice%"=="9" goto device_info
if /i "%choice%"=="A" goto allure_report
if /i "%choice%"=="S" goto page_server
if /i "%choice%"=="T" goto prototype_test
if /i "%choice%"=="M" goto manual_mode
if /i "%choice%"=="I" goto install_apk
if /i "%choice%"=="Q" goto end
echo Invalid choice, try again
goto menu

:start_appium
    echo.
    echo Starting Appium Server with ANDROID_HOME...
    start "Appium Server" cmd /k "set ANDROID_HOME=%~dp0..&& set ANDROID_SDK_ROOT=%~dp0..&& appium --relaxed-security"
    echo [OK] Appium Server launched in separate window
    echo Waiting 5 seconds...
    timeout /t 5 /nobreak >nul
    goto menu

:smoke_test
    echo.
    python run_tests.py --smoke -v
    goto menu

:all_test
    echo.
    python run_tests.py --report
    goto menu

:login_test
    echo.
    python run_tests.py --module login -v --report
    goto menu

:home_test
    echo.
    python run_tests.py --module home -v
    goto menu

:flight_test
    echo.
    python run_tests.py --module flight -v
    goto menu

:news_test
    echo.
    python run_tests.py --module news -v
    goto menu

:mine_test
    echo.
    python run_tests.py --module mine -v
    goto menu

:device_info
    echo.
    echo === Device Info ===
    adb devices -l
    echo.
    adb shell getprop ro.product.model
    adb shell getprop ro.build.version.release
    goto menu

:allure_report
    echo.
    echo Generating Allure report...
    allure serve reports/allure-results
    goto menu

:page_server
    echo.
    echo ============================================================
    echo   Page Server — Serve HTML Prototypes to Phone
    echo ============================================================
    echo.
    echo   This will:
    echo     1. Start HTTP server on port 8080
    echo     2. Auto-configure adb reverse forwarding
    echo     3. Phone can access via http://127.0.0.1:8080/
    echo.
    start "Page Server" cmd /k "set ANDROID_HOME=%~dp0..&& cd /d %~dp0 && .venv\Scripts\python.exe serve_pages.py"
    echo [OK] Page Server launched in separate window
    echo [OK] It may take 2-3 seconds to start
    timeout /t 2 /nobreak >nul
    goto menu

:prototype_test
    echo.
    echo ============================================================
    echo   Full Prototype Test Workflow
    echo ============================================================
    echo.
    echo   Step 1/3: Starting page server (background)...
    start "Page Server" cmd /k "set ANDROID_HOME=%~dp0..&& cd /d %~dp0 && .venv\Scripts\python.exe serve_pages.py"
    echo   [OK] Page server started on port 8080
    echo.
    echo   Step 2/3: Starting Appium Server (background)...
    start "Appium Server" cmd /k "set ANDROID_HOME=%~dp0..&& set ANDROID_SDK_ROOT=%~dp0..&& appium --relaxed-security"
    echo   [OK] Appium Server starting (wait 5s)...
    timeout /t 5 /nobreak >nul
    echo.
    echo   Step 3/3: Entering manual test mode...
    echo   [OK] Use launch() to navigate to prototype pages
    echo.
    python -i manual_test.py
    goto menu

:install_apk
    echo.
    echo ============================================================
    echo   Install APK to Device
    echo ============================================================
    echo.
    set /p apk_path="Drag APK file here or enter path: "
    if not exist "%apk_path%" (
        echo [ERROR] File not found: %apk_path%
        goto menu
    )
    echo.
    echo Installing: %apk_path%
    adb install -r "%apk_path%"
    if %ERRORLEVEL% EQU 0 (
        echo [OK] APK installed successfully!
        echo.
        echo To get appPackage and appActivity, run:
        echo   adb shell dumpsys package ^| findstr -i "dolphin"
        echo.
        echo Or use: python -c "from utils.adb_helper import ADBHelper; adb=ADBHelper(); print(adb.get_installed_apps())"
    ) else (
        echo [ERROR] APK installation failed
    )
    goto menu

:manual_mode
    echo.
    echo ============================================================
    echo   Manual / Interactive Test Mode
    echo ============================================================
    echo.
    echo   In this mode you can:
    echo     - Use Appium Inspector to inspect elements
    echo     - Run commands step by step in Python REPL
    echo     - Debug element locators
    echo.
    echo   Usage:
    echo     1. Start Appium Server first [select 1]
    echo     2. Then enter interactive mode:
    echo        python -i manual_test.py
    echo.
    python -i manual_test.py
    goto menu

:end
    echo.
    echo Goodbye!
    timeout /t 2 /nobreak >nul
    exit /b 0
