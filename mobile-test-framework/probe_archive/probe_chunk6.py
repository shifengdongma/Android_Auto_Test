# -*- coding: utf-8 -*-
"""探索脚本 Chunk6: 起飞地搜索完整链路验证 (用后即删)"""
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

def dump(name):
    Path(f"reports/{name}.xml").write_text(d.page_source, encoding="utf-8")

def find_text(txt, timeout=8):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return d.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR, f'new UiSelector().text("{txt}")'
            )
        except Exception:
            time.sleep(1)
    return None

d.tap([(432, 2290)]); time.sleep(3)     # 申报 tab
d.tap([(565, 219)]); time.sleep(2.5)    # 起飞地字段 (a11y坐标), 同时预热a11y树
shot("d1_field_clicked")

el = find_text("请输入起飞地")
if el is None:
    print("NOT FOUND 请输入起飞地")
    dump("d1_dump")
else:
    print("found 请输入起飞地, click + send_keys")
    el.click(); time.sleep(1.5)
    try:
        el.send_keys("新疆")
        print("send_keys 新疆 OK")
    except Exception as e:
        print("send_keys failed:", str(e)[:120])
    time.sleep(2.5)
    shot("d2_searched")
    dump("d2_searched")
    # 点击结果 新疆起降场1
    r = find_text("新疆起降场1", timeout=5)
    if r is None:
        # 尝试 textContains
        try:
            r = d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("新疆起降场1")')
            print("found by contains:", r.text)
        except Exception as e:
            print("result not found:", str(e)[:100])
    if r is not None:
        r.click()
        print("clicked 新疆起降场1")
        time.sleep(2.5)
        shot("d3_selected")
        dump("d3_selected")

m.quit_driver()
print("done")
