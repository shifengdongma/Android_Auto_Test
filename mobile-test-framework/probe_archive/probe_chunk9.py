# -*- coding: utf-8 -*-
"""探索脚本 Chunk9: 实时bounds定位 + 剪贴板粘贴 (用后即删)"""
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

def find(txt, timeout=6, contains=False):
    sel = f'new UiSelector().{"textContains" if contains else "text"}("{txt}")'
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, sel)
        except Exception:
            time.sleep(0.8)
    return None

def center(el):
    loc = el.location
    size = el.size
    return loc["x"] + size["width"] // 2, loc["y"] + size["height"] // 2

def scroll_to_top():
    d.swipe(576, 500, 576, 1200, 400)
    time.sleep(1.5)

d.tap([(432, 2290)]); time.sleep(3.5)

# 找起飞地字段, 找不到就上滑后重试
el = None
for i in range(4):
    el = find("请输入起飞地", timeout=5)
    if el is not None:
        break
    print(f"retry {i+1}: scroll to top")
    scroll_to_top()
if el is None:
    print("FIELD NOT FOUND after scrolls")
    dump("j_diag")
else:
    x, y = center(el)
    print(f"field found at ({x},{y})")
    el.click(); time.sleep(1.5)
    # 长按 → 粘贴
    d.execute_script("mobile: longClickGesture", {"x": x, "y": y, "duration": 1500})
    time.sleep(2)
    shot("j1_longpress")
    paste = find("粘贴", timeout=5)
    if paste is None:
        print("PASTE NOT FOUND")
        dump("j1_diag")
    else:
        print("paste found, click")
        paste.click(); time.sleep(2.5)
        shot("j2_pasted")
        dump("j2_pasted")
        r = find("新疆起降场1", timeout=8, contains=True)
        if r is None:
            print("RESULT NOT FOUND after paste")
        else:
            print("result found:", r.text)
            rx, ry = center(r)
            print(f"result at ({rx},{ry})")
            r.click(); time.sleep(2.5)
            shot("j3_selected")
            dump("j3_selected")
            print("SELECTED 新疆起降场1")

m.quit_driver()
print("done")
