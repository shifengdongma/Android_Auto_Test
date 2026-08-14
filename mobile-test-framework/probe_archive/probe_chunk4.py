# -*- coding: utf-8 -*-
"""探索脚本 Chunk4: 验证 webview a11y 树可交互性 (用后即删)
点击起飞地 -> picker搜索框输入"新疆" -> 查看过滤结果 -> 点击"新疆起降场1"
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from appium.webdriver.common.appiumby import AppiumBy
from drivers.appium_driver import AppiumDriverManager

SHOT = Path("reports/screenshots")

m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)

def shot(name):
    d.save_screenshot(str(SHOT / f"{name}.png"))
    print("shot:", name)

def dump(name):
    Path(f"reports/{name}.xml").write_text(d.page_source, encoding="utf-8")

d.tap([(432, 2290)]); time.sleep(3)   # 申报 tab

# 1. 点击 起飞地 字段 (文本选择器)
try:
    el = d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("起飞地")')
    el.click()
    print("clicked 起飞地")
except Exception as e:
    print("click 起飞地 failed:", str(e)[:100])
time.sleep(2.5)
shot("b1_picker_opened")
dump("b1_picker")

# 2. 搜索框输入
edits = d.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
print("EditTexts:", len(edits))
target = None
for e in edits:
    try:
        if e.is_displayed():
            target = e
    except Exception:
        pass
if target is None:
    print("NO visible EditText!")
else:
    target.click()
    time.sleep(1)
    target.send_keys("新疆")
    print("sent 新疆")
time.sleep(2.5)
shot("b2_search_xinjiang")
dump("b2_search")

# 3. 点击 新疆起降场1
try:
    el = d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("新疆起降场1")')
    print("found:", el.text)
    el.click()
    print("clicked result")
except Exception as e:
    print("click result failed:", str(e)[:100])
time.sleep(2.5)
shot("b3_selected")
dump("b3_selected")

m.quit_driver()
print("done")
