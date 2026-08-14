# -*- coding: utf-8 -*-
"""探索脚本 Chunk5: 坐标点击起飞地 -> a11y树构建 -> 选择器搜索输入 (用后即删)"""
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
    print("dump:", name)

d.tap([(432, 2290)]); time.sleep(3)    # 申报 tab
d.tap([(800, 440)]); time.sleep(3)     # 起飞地字段 (坐标, chunk3已实测可打开picker)
dump("c1_picker_open")
shot("c1_picker_open")

# 找可见EditText (picker搜索框)
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
    print("NO visible EditText")
else:
    target.click(); time.sleep(1)
    target.send_keys("新疆")
    print("sent 新疆")
    time.sleep(2.5)
    dump("c2_search")
    shot("c2_search")
    # 点结果
    try:
        el = d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("新疆起降场1")')
        print("found:", el.text)
        el.click()
        print("clicked 新疆起降场1")
    except Exception as e:
        print("click failed:", str(e)[:120])
    time.sleep(2.5)
    dump("c3_selected")
    shot("c3_selected")

m.quit_driver()
print("done")
