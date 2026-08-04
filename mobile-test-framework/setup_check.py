#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Environment Setup Checker

Validates all prerequisites before running tests.
Run this on any new machine to verify the environment is correctly configured.

Usage:
    python setup_check.py
    python setup_check.py --fix    # Attempt automatic fixes
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FRAMEWORK_ROOT = Path(__file__).parent


class Colors:
    """Terminal colors"""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"
    OK = "\033[92m[OK]\033[0m"
    FAIL = "\033[91m[FAIL]\033[0m"
    WARN = "\033[93m[WARN]\033[0m"
    FIX = "\033[93m[FIXED]\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  {text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")


def check_python() -> bool:
    """Check Python version"""
    print(f"\n  Python version: {sys.version}")
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 9):
        print(f"  {Colors.OK} Python {major}.{minor} meets minimum (3.9+)")
        return True
    print(f"  {Colors.FAIL} Python {major}.{minor} too old, need 3.9+")
    return False


def check_venv() -> bool:
    """Check virtual environment"""
    venv_path = FRAMEWORK_ROOT / ".venv"
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    if venv_path.exists():
        print(f"  {Colors.OK} Virtual environment found: .venv")
        if in_venv:
            print(f"  {Colors.OK} Currently running inside .venv")
        else:
            print(f"  {Colors.WARN} .venv exists but not activated")
            print(f"    Activate: .venv\\Scripts\\Activate.ps1  (PowerShell)")
            print(f"    Activate: .venv\\Scripts\\activate.bat   (CMD)")
        return True
    else:
        print(f"  {Colors.FAIL} Virtual environment not found")
        print(f"    Create: python -m venv .venv")
        print(f"    Install: .venv\\Scripts\\pip install -r requirements.txt")
        return False


def check_adb() -> bool:
    """Check ADB availability"""
    # Check project built-in platform-tools
    local_adb = PROJECT_ROOT / "platform-tools" / "adb.exe"
    system_adb = shutil.which("adb")

    if local_adb.exists():
        print(f"  {Colors.OK} Project ADB found: {local_adb}")
        return True
    elif system_adb:
        print(f"  {Colors.OK} System ADB found: {system_adb}")
        return True
    else:
        print(f"  {Colors.FAIL} ADB not found")
        print(f"    Expected at: {local_adb}")
        print(f"    Download: https://developer.android.com/tools/releases/platform-tools")
        return False


def check_android_home(fix: bool = False) -> bool:
    """Check ANDROID_HOME environment variable"""
    android_home = os.environ.get("ANDROID_HOME")
    android_sdk_root = os.environ.get("ANDROID_SDK_ROOT")
    local_platform_tools = PROJECT_ROOT / "platform-tools" / "adb.exe"

    if android_home:
        adb_path = Path(android_home) / "platform-tools" / "adb.exe"
        if adb_path.exists():
            print(f"  {Colors.OK} ANDROID_HOME={android_home}")
            print(f"  {Colors.OK} ADB found at: {adb_path}")
            return True
        else:
            print(f"  {Colors.WARN} ANDROID_HOME={android_home} BUT adb.exe not found")
            print(f"    Expected: {adb_path}")
            return False
    elif android_sdk_root:
        print(f"  {Colors.OK} ANDROID_SDK_ROOT={android_sdk_root}")
        return True
    else:
        print(f"  {Colors.FAIL} ANDROID_HOME not set")
        print(f"  {Colors.FAIL} ANDROID_SDK_ROOT not set")

        if local_platform_tools.exists():
            print(f"\n  {Colors.YELLOW}Auto-detected project platform-tools:{Colors.RESET}")
            print(f"    {local_platform_tools}")
            print(f"\n  {Colors.BOLD}Recommended fix (permanent):{Colors.RESET}")
            print(f"    1. Press Win+R, type: sysdm.cpl")
            print(f"    2. Advanced -> Environment Variables")
            print(f"    3. Add User variable:")
            print(f"       Name:  ANDROID_HOME")
            print(f"       Value: {PROJECT_ROOT}")
            print(f"    4. Click OK, restart terminals")

            if fix:
                os.environ["ANDROID_HOME"] = str(PROJECT_ROOT)
                os.environ["ANDROID_SDK_ROOT"] = str(PROJECT_ROOT)
                print(f"\n  {Colors.FIX} Temporarily set ANDROID_HOME={PROJECT_ROOT}")
                print(f"    (Note: this only affects this session)")
            return fix  # return True if we fixed it
        else:
            print(f"\n  {Colors.FAIL} Project platform-tools not found either")
            print(f"    Expected: {local_platform_tools}")
            return False


def check_node() -> bool:
    """Check Node.js"""
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=10
        )
        version = result.stdout.strip()
        print(f"  {Colors.OK} Node.js {version}")
        return True
    except FileNotFoundError:
        print(f"  {Colors.FAIL} Node.js not found")
        print(f"    Install: https://nodejs.org/")
        return False


def check_appium() -> bool:
    """Check Appium installation"""
    import platform
    # On Windows, npm global packages use .cmd wrappers that need shell=True
    use_shell = platform.system() == "Windows"
    try:
        result = subprocess.run(
            "appium --version" if use_shell else ["appium", "--version"],
            capture_output=True, text=True, timeout=10,
            shell=use_shell,
        )
        version = result.stdout.strip()
        if version:
            print(f"  {Colors.OK} Appium {version}")
            return True
        # Try stderr for version info
        if result.stderr and "appium" in result.stderr.lower():
            print(f"  {Colors.OK} Appium installed")
            return True
        raise FileNotFoundError("Appium not found")
    except FileNotFoundError:
        print(f"  {Colors.FAIL} Appium not installed")
        print(f"    Install: npm install -g appium")
        print(f"    Driver:  appium driver install uiautomator2")
        return False


def check_appium_drivers() -> bool:
    """Check Appium UiAutomator2 driver"""
    # Check by looking for the driver in Appium's home directory
    appium_home = os.environ.get("APPIUM_HOME", os.path.expanduser("~/.appium"))
    driver_path = Path(appium_home) / "node_modules" / "appium-uiautomator2-driver"
    if driver_path.exists():
        print(f"  {Colors.OK} UiAutomator2 driver found: {driver_path}")
        return True

    import platform
    use_shell = platform.system() == "Windows"
    try:
        result = subprocess.run(
            "appium driver list --installed" if use_shell else ["appium", "driver", "list", "--installed"],
            capture_output=True, text=True, timeout=15,
            shell=use_shell,
        )
        combined = result.stdout + result.stderr
        if "uiautomator2" in combined:
            print(f"  {Colors.OK} UiAutomator2 driver installed")
            return True

        print(f"  {Colors.FAIL} UiAutomator2 driver not installed")
        print(f"    Install: appium driver install uiautomator2")
        return False
    except Exception:
        print(f"  {Colors.FAIL} Failed to check driver")
        print(f"    Install: appium driver install uiautomator2")
        return False
        return False


def check_devices() -> bool:
    """Check connected Android devices"""
    local_adb = PROJECT_ROOT / "platform-tools" / "adb.exe"
    adb = str(local_adb) if local_adb.exists() else "adb"

    try:
        result = subprocess.run(
            [adb, "devices"], capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split("\n")[1:]  # Skip header
        devices = [l for l in lines if l.strip() and "device" in l]
        online = [d for d in devices if d.endswith("\tdevice")]

        if online:
            for d in online:
                device_id = d.split("\t")[0]
                print(f"  {Colors.OK} Device connected: {device_id}")
            return True
        else:
            print(f"  {Colors.WARN} No Android devices connected")
            print(f"    Real device: Enable USB Debugging, connect via USB")
            print(f"    Emulator:    Start AVD from Android Studio")
            return False
    except Exception as e:
        print(f"  {Colors.FAIL} Failed to check devices: {e}")
        return False


def check_config() -> bool:
    """Check config.yaml"""
    config_path = FRAMEWORK_ROOT / "config" / "config.yaml"
    if config_path.exists():
        print(f"  {Colors.OK} config.yaml found: {config_path}")
        return True
    else:
        print(f"  {Colors.FAIL} config.yaml not found: {config_path}")
        return False


def check_python_deps() -> bool:
    """Check Python dependencies"""
    required = ["appium", "selenium", "pytest", "allure", "yaml"]
    missing = []
    for mod in required:
        try:
            if mod == "appium":
                import appium.webdriver
            elif mod == "allure":
                import allure
            elif mod == "yaml":
                import yaml
            else:
                __import__(mod)
        except ImportError:
            missing.append(mod)

    if not missing:
        print(f"  {Colors.OK} All Python dependencies installed")
        return True
    else:
        print(f"  {Colors.FAIL} Missing packages: {', '.join(missing)}")
        print(f"    Install: pip install -r requirements.txt")
        return False


def print_summary(results: dict):
    """Print check summary"""
    print_header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, ok in results.items():
        status = Colors.OK if ok else Colors.FAIL
        print(f"  {status} {name}")

    print(f"\n  Result: {passed}/{total} checks passed")
    if passed == total:
        print(f"  {Colors.GREEN}{Colors.BOLD}Environment is ready!{Colors.RESET}")
        print(f"\n  Quick start:")
        print(f"    Terminal 1: appium")
        print(f"    Terminal 2: python run_tests.py --smoke")
    else:
        print(f"\n  {Colors.YELLOW}Fix the FAIL items above, then re-run:{Colors.RESET}")
        print(f"    python setup_check.py")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="LATM Test Framework - Environment Setup Checker"
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Attempt automatic fixes for detected issues"
    )
    args = parser.parse_args()

    print_header("LATM Test Framework - Environment Check")

    results = {}
    checks = [
        ("Python 3.9+", check_python),
        ("Virtual Environment", check_venv),
        ("Python Dependencies", check_python_deps),
        ("Config File", check_config),
        ("ADB (Android Debug Bridge)", check_adb),
        ("ANDROID_HOME", lambda: check_android_home(fix=args.fix)),
        ("Node.js", check_node),
        ("Appium Server", check_appium),
        ("Appium UiAutomator2 Driver", check_appium_drivers),
        ("Android Device Connection", check_devices),
    ]

    for name, check_fn in checks:
        print(f"\n--- {name} ---")
        try:
            results[name] = check_fn()
        except Exception as e:
            print(f"  {Colors.FAIL} Check error: {e}")
            results[name] = False

    print_summary(results)
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
