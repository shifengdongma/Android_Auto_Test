# -*- coding: utf-8 -*-
"""探索脚本 Chunk10: 状态归零(清数据+登录) -> 申报页确定性探索 (用后即删)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from appium.webdriver.common.appiumby import AppiumBy
from drivers.appium_driver import AppiumDriverManager
from utils.adb_helper import ADBHelper

SHOT = Path("reports/screenshots")

# 1. 状态归零: 清数据
ADBHelper().clear_app_data("com.keda.atc")
print("data cleared")
time.sleep(2)

# 2. 全新会话 + 登录
m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)

from pages.login_page import LoginPage
page = LoginPage(d)
page.wait_for_login_page(timeout=20)
page.login("liyang", "Liyang@1128")
print("logged in")
time.sleep(2)
d.save_screenshot(str(SHOT / "k0_logged_in.png"))

# 3. 申报 tab (fresh state)
d.tap([(432, 2290)]); time.sleep(3.5)
d.save_screenshot(str(SHOT / "k1_fresh_apply.png"))
Path("reports/k1_dump.xml").write_text(d.page_source, encoding="utf-8")

# 4. 点击起飞地 (fresh坐标估值 700,440)
d.tap([(700, 440)]); time.sleep(3)
d.save_screenshot(str(SHOT / "k2_picker.png"))
Path("reports/k2_dump.xml").write_text(d.page_source, encoding="utf-8")

# 5. a11y找搜索输入框/字段
for txt in ["请输入起飞地", "起飞地"]:
    try:
        el = d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{txt}")')
        print(f"found {txt!r} at {el.location}, size={el.size}")
    except Exception as e:
        print(f"not found {txt!r}")
edits = d.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
print("EditTexts:", len(edits))
for e in edits:
    try:
        print("  EditText:", e.location, e.size, "displayed:", e.is_displayed(), "text:", repr((e.text or "")[:20]))
    except Exception as ex:
        print("  EditText err:", str(ex)[:60])

m.quit_driver()
print("done")
