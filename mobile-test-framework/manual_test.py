#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
手动/交互式测试辅助模块

功能:
    提供交互式Python会话，用于:
        - 手动操作APP并实时验证
        - 调试元素定位器
        - 逐步骤探索页面
        - 开发新Page Object时快速验证
        - 配合 Appium Inspector 使用

使用方式:
    # 方式1: 交互模式 (推荐)
    python -i manual_test.py

    # 方式2: 先启动Appium，再运行
    # 终端1: appium
    # 终端2: python -i manual_test.py

    # 方式3: 不需要自动化，仅启动APP到设备
    python manual_test.py --launch-only

交互式会话中可用的变量:
    driver    - Appium WebDriver实例
    config    - 配置管理器
    adb       - ADB工具
    bp        - BasePage快捷引用
    login_pg  - LoginPage实例
    home_pg   - HomePage实例
    flight_pg - FlightPage实例
    news_pg   - NewsPage实例
    mine_pg   - MinePage实例

    help()    - 显示帮助
    launch()  - 启动/重启APP
    info()    - 显示设备和会话信息
"""

import sys
import os
from pathlib import Path

# 确保项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def _print_banner():
    """Print welcome banner"""
    test_mode = "(native)"  # default
    try:
        test_mode = config.get("test_mode", "native")
    except Exception:
        pass

    print(f"""
╔══════════════════════════════════════════════════════════╗
║          Manual Test Console  (mode: {test_mode})
║          LATM - Low-Altitude Airspace Management         ║
╚══════════════════════════════════════════════════════════╝

  Loaded variables:
    driver     - WebDriver instance
    config     - ConfigManager
    adb        - ADBHelper

  Quick functions:
    help()       - Show this help
    launch()     - Navigate to test URL / launch APP
    info()       - Device & session info
    screenshot("name") - Take screenshot
    navigate("url")    - Navigate to URL (browser mode)

  App discovery (when APK is ready):
    find_app("keyword")  - Search installed apps
    inspect_app("pkg")   - Get appPackage/appActivity
    current_app()        - Get foreground app package
    install_apk("path")  - Install APK to device

  Browser mode - Web locators:
    >>> from selenium.webdriver.common.by import By
    >>> driver.find_element(By.CSS_SELECTOR, ".btn-primary")
    >>> driver.find_element(By.XPATH, "//input[@placeholder]")
    >>> driver.page_source[:200]     # View page HTML
    >>> driver.title                 # Page title
    >>> driver.current_url           # Current URL
    >>> driver.swipe(500,1500,500,500) # Swipe up
""")


def help():
    """Show help"""
    test_mode = config.get("test_mode", "native")
    if test_mode == "browser":
        print("""
==================== Browser Mode Help ====================

[Navigation]
  launch()                    - Go to test URL
  navigate("https://...")     - Go to any URL
  driver.get("https://...")   - Selenium standard navigate
  driver.back()               - Browser back
  driver.refresh()            - Refresh page

[Web Elements]  (from selenium.webdriver.common.by import By)
  driver.find_element(By.CSS_SELECTOR, ".btn-primary")
  driver.find_element(By.CSS_SELECTOR, "input[placeholder*='user']")
  driver.find_element(By.CSS_SELECTOR, "button")
  driver.find_element(By.XPATH, "//input[@type='password']")
  driver.find_element(By.XPATH, "//button[contains(text(),'Login')]")
  driver.find_elements(By.CSS_SELECTOR, ".notify-card")

[Page Info]
  driver.title                - Page title
  driver.current_url          - Current URL
  driver.page_source[:500]    - Page HTML
  info()                      - Device & session info

[Screenshots & Swipe]
  screenshot("name")          - Save screenshot to reports/screenshots/
  driver.swipe(500,1500,500,500,500)  - Swipe up (adjust coords)

[ADB Commands]
  adb.get_connected_devices()
  adb.set_gps_location(22.5431, 114.0579)  # Simulate GPS
  adb.disable_wifi() / adb.enable_wifi()
  adb.take_screenshot_adb("test.png")

[App Discovery] (when APK is ready)
  find_app("dolphin")         - Search for installed apps
  inspect_app("com.xxx.yyy")  - Get appPackage/appActivity/activities
  current_app()               - Show current foreground app
  install_apk("path.apk")     - Install APK to device

[Tips]
  - Use chrome://inspect on PC for Chrome Remote Debugging
  - Prototype testing: start serve_pages.py first, then use launch()
  - Ctrl+C to exit, then type exit() or Ctrl+D
""")
    else:
        print("""
==================== Native Mode Help ====================

[Page Objects]
  login_pg.enter_username("user")    # Type username
  login_pg.click_login()             # Click login
  home_pg.switch_notify_tab("alert") # Switch tab
  flight_pg.search_airport("name")   # Search airport

[BasePage]
  bp.find_element((AppiumBy.ID, "xxx"))
  bp.click(locator) / bp.input_text(locator, text)
  bp.swipe_up() / bp.swipe_down()

[Tips]
  - Use Appium Inspector for element inspection
  - driver.page_source shows XML view hierarchy
""")


def info():
    """显示设备和当前会话信息"""
    print("\n════════════ 设备和会话信息 ════════════")
    try:
        caps = driver.capabilities
        print(f"  平台:       {caps.get('platformName', 'N/A')}")
        print(f"  系统版本:   {caps.get('platformVersion', 'N/A')}")
        print(f"  设备名称:   {caps.get('deviceName', 'N/A')}")
        print(f"  自动化引擎: {caps.get('automationName', 'N/A')}")
        print(f"  应用包名:   {caps.get('appPackage', 'N/A')}")
        print(f"  UDID:       {caps.get('udid', 'auto')}")
    except Exception:
        print("  (无法获取caps信息)")

    try:
        size = driver.get_window_size()
        print(f"  屏幕尺寸:   {size['width']}x{size['height']}")
    except Exception:
        pass

    try:
        activity = driver.current_activity
        print(f"  当前Activity: {activity}")
    except Exception:
        pass

    print(f"  配置环境:   {config.get_active_env()}")
    print(f"  设备数量:   {len(config.get_all_devices())}")
    test_mode = config.get("test_mode", "native")
    print(f"  测试模式:   {test_mode}")
    if test_mode == "browser":
        print(f"  测试URL:    {config.get('test_url', 'N/A')}")
    print("════════════════════════════════════════════\n")


def screenshot(name="manual"):
    """快捷截图函数"""
    import datetime
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"manual_{name}_{ts}"
    # Ensure screenshot dir exists
    import os
    os.makedirs("reports/screenshots", exist_ok=True)
    path = driver.save_screenshot(f"reports/screenshots/{filename}.png")
    print(f"Screenshot saved: {path}")
    return path


def launch():
    """启动APP 或 导航到测试URL"""
    test_mode = config.get("test_mode", "native")
    if test_mode == "browser":
        url = config.get("test_url", "https://dkkgsit-test.testdolphin.com/atc/dashboard")
        print(f"Navigating to: {url}")
        driver.get(url)
        print(f"Page title: {driver.title}")
    else:
        device_config = config.get_device_config(0)
        package = device_config.get("app_package", "")
        activity = device_config.get("app_activity", "")
        print(f"Starting: {package}/{activity}")
        try:
            driver.start_activity(package, activity)
            print("App launched")
        except Exception as e:
            print(f"Launch failed: {e}")


def navigate(url=None):
    """浏览器模式: 导航到指定URL"""
    if url is None:
        url = config.get("test_url", "about:blank")
    print(f"Navigating to: {url}")
    driver.get(url)
    print(f"Done. Title: {driver.title}")
    print(f"URL: {driver.current_url}")


def find_app(keyword=None):
    """查找已安装的应用 — 用于确定 appPackage"""
    if keyword is None:
        keyword = input("Enter keyword to search (e.g. 'dolphin', 'atc'): ").strip()
    print(f"\nSearching installed apps matching '{keyword}'...")
    apps = adb.get_installed_apps(keyword) if keyword else adb.get_installed_apps()
    if apps:
        print(f"\nFound {len(apps)} app(s):")
        for a in apps:
            print(f"  📦 {a['package_name']}  (v{a['version']})")
    else:
        print(f"\nNo apps found matching '{keyword}'")
        print("  Try without keyword to see all third-party apps:")
        print("  >>> adb.get_installed_apps()")
    return apps


def inspect_app(package_name=None):
    """检查应用详细信息 — 用于确定 appActivity"""
    if package_name is None:
        package_name = input("Enter package name: ").strip()
    if not package_name:
        print("[ERROR] Package name required")
        return

    print(f"\nInspecting {package_name}...")
    info = adb.get_app_info(package_name)
    print(f"""
════════════ App Info ════════════
  Package:      {info['package_name']}
  Version:      {info['version_name']} ({info['version_code']})
  Target SDK:   {info['target_sdk']}
  Main Activity:{info['main_activity']}
  Activities:   {len(info['activities'])} total
  Permissions:  {len(info['permissions'])} total
""")

    if info['activities']:
        print("  All Activities:")
        for act in info['activities'][:20]:
            marker = " ← LAUNCHER" if act == info['main_activity'] else ""
            print(f"    - {act}{marker}")
        if len(info['activities']) > 20:
            print(f"    ... and {len(info['activities']) - 20} more")

    print("\n  For config.yaml:")
    print(f"    app_package: \"{info['package_name']}\"")
    print(f"    app_activity: \"{info['main_activity']}\"")
    print("════════════════════════════════\n")
    return info


def current_app():
    """获取当前前台应用包名"""
    pkg = adb.get_current_app_package()
    if pkg:
        print(f"\n  Current foreground app: {pkg}")
        print(f"  For more details: inspect_app('{pkg}')\n")
    else:
        print("\n  Cannot determine current app. Is screen on and unlocked?\n")
    return pkg


def install_apk(path=None):
    """安装APK到设备，安装成功后自动获取应用信息"""
    if path is None:
        path = input("APK file path: ").strip().strip('"').strip("'")
    if not path or not os.path.exists(path):
        print(f"[ERROR] File not found: {path}")
        return False

    print(f"\nInstalling: {path}")
    success = adb.install_app(path)
    if success:
        print("[OK] APK installed!")
        # 尝试从APK文件名推测包名
        import re
        # 或让用户搜索
        print("\n  Finding installed apps (searching 'dolphin'/'atc')...")
        for kw in ["dolphin", "atc", "test"]:
            apps = adb.get_installed_apps(kw)
            if apps:
                for a in apps:
                    print(f"  Found: {a['package_name']} v{a['version']}")
                    print(f"  Run: inspect_app('{a['package_name']}')")
                break
    else:
        print("[ERROR] APK installation failed. Check:")
        print("  1. USB debugging is enabled on the device")
        print("  2. Install from unknown sources is allowed")
        print("  3. The APK file is not corrupted")
    return success


# ============================================================
# 初始化 (模块导入时执行)
# ============================================================

driver = None
config = None
adb = None
bp = None
login_pg = None
home_pg = None
flight_pg = None
news_pg = None
mine_pg = None

try:
    from config.config_manager import ConfigManager
    from utils.adb_helper import ADBHelper
    from pages.base_page import BasePage
    from pages.login_page import LoginPage
    from pages.home_page import HomePage
    from pages.flight_page import FlightPage
    from pages.news_page import NewsPage
    from pages.mine_page import MinePage

    # 加载配置
    config = ConfigManager()
    print(f"[OK] 配置已加载 (环境: {config.get_active_env()})")

    # 初始化ADB
    try:
        adb = ADBHelper()
        devices = adb.get_connected_devices()
        if devices:
            print(f"[OK] ADB已就绪 (在线设备: {len(devices)})")
            for d in devices:
                print(f"     - {d['model']} | Android {d['android_version']} | {d['status']}")
        else:
            print("[WARN] 没有检测到连接的Android设备")
    except Exception as e:
        print(f"[WARN] ADB初始化失败: {e}")

    # 尝试创建driver (手动模式只重试1次，快速失败)
    try:
        from drivers.appium_driver import AppiumDriverManager
        dm = AppiumDriverManager(config_manager=config)
        # Override retry for manual mode: only 1 attempt, fail fast
        retry_cfg = config.get("retry", {})
        retry_cfg["max_attempts"] = 1
        retry_cfg["interval_ms"] = 500
        driver = dm.get_driver()
        print("[OK] Appium Session已建立")

        test_mode = config.get("test_mode", "native")
        if test_mode == "browser":
            test_url = config.get("test_url", "")
            print(f"[OK] Chrome已启动")
            print(f"[INFO] 测试URL: {test_url}")
            print(f"[INFO] 在交互模式中使用 launch() 导航到测试页面")
            print(f"[INFO] 或手动: driver.get('{test_url}')")

        # 初始化辅助对象
        bp = BasePage(driver)
        login_pg = LoginPage(driver)
        home_pg = HomePage(driver)
        flight_pg = FlightPage(driver)
        news_pg = NewsPage(driver)
        mine_pg = MinePage(driver)

        print("[OK] 所有Page Object已就绪")
    except Exception as e:
        test_mode = config.get("test_mode", "native")
        if test_mode == "browser":
            print(f"\n[ERROR] Chrome浏览器Session创建失败!")
            print(f"[ERROR] 原因: {e}")
            print(f"\n[ACTIONS] 请按以下步骤修复:")
            print(f"  1. 确认手机已安装 Chrome 浏览器")
            print(f"     手机上打开 Play Store → 搜索 Google Chrome → 安装")
            print(f"  2. 验证安装: adb shell pm list packages | grep chrome")
            print(f"     预期输出: package:com.android.chrome")
            print(f"  3. 重新运行: python -i manual_test.py")
            print(f"\n[ALTERNATIVE] 不使用Appium的手动测试方式:")
            print(f"  1. 手机上用浏览器打开: https://dkkgsit-test.testdolphin.com/atc/dashboard")
            print(f"  2. PC Chrome 打开: chrome://inspect")
            print(f"  3. 在 Remote Target 中找到手机页面 → inspect")
            print(f"\n[OR] 切换到native模式 (测试已安装的APP):")
            print(f"  修改 config/config.yaml: test_mode: native")
        else:
            print(f"\n[ERROR] Driver创建失败: {e}")
            print(f"[HINT] 请确认:")
            print(f"  1. Appium Server 已启动: appium --relaxed-security")
            print(f"  2. 设备已连接: adb devices")
            print(f"  3. config.yaml 中 appPackage/appActivity 正确")
        print(f"\n你仍可以使用 adb 和 config 工具")

except Exception as e:
    print(f"[ERROR] 初始化失败: {e}")

# 打印横幅和帮助
_print_banner()
print("  输入 help() 查看详细帮助，info() 查看设备和会话信息")
print("  输入 exit() 或 Ctrl+D 退出\n")


# ============================================================
# 直接运行 (非交互模式) 时的行为
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="手动测试辅助")
    parser.add_argument("--launch-only", action="store_true", help="仅启动APP不进入交互")
    args = parser.parse_args()

    if args.launch_only and driver:
        launch()
    elif not driver:
        print("\n[提示] Driver未创建。请确保:")
        print("  1. Appium Server已启动: appium")
        print("  2. Android设备已连接: adb devices")
        print("  3. config.yaml中设备配置正确")
