# -*- coding: utf-8 -*-
"""探索脚本 Chunk7: 剪贴板粘贴输入中文关键词 (用后即删)"""
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

def find_text(txt, timeout=8, contains=False):
    sel = f'new UiSelector().{"textContains" if contains else "text"}("{txt}")'
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, sel)
        except Exception:
            time.sleep(1)
    return None

# 剪贴板自检
d.set_clipboard_text("新疆")
print("clipboard:", d.get_clipboard_text())

d.tap([(432, 2290)]); time.sleep(3)     # 申报 tab
d.tap([(565, 219)]); time.sleep(2.5)    # 起飞地字段 + 预热a11y

el = find_text("请输入起飞地")
if el is None:
    print("NOT FOUND field")
else:
    el.click(); time.sleep(1.5)
    # 长按弹出粘贴菜单
    d.execute_script("mobile: longClickGesture", {"x": 565, "y": 219, "duration": 1500})
    time.sleep(2)
    shot("e1_longpress")
    dump("e1_longpress")
    paste = find_text("粘贴", timeout=5)
    if paste is None:
        paste = find_text("Paste", timeout=3)
    if paste is None:
        print("paste menu NOT FOUND")
    else:
        print("found paste:", paste.text)
        paste.click()
        time.sleep(2.5)
        shot("e2_pasted")
        dump("e2_pasted")
        r = find_text("新疆起降场1", timeout=6, contains=True)
        if r is None:
            print("result 新疆起降场1 NOT FOUND after paste")
        else:
            print("found result:", r.text)
            r.click()
            time.sleep(2.5)
            shot("e3_selected")
            dump("e3_selected")
            print("clicked 新疆起降场1")

m.quit_driver()
print("done")
