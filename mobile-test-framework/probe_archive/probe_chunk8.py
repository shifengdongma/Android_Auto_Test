# -*- coding: utf-8 -*-
"""探索脚本 Chunk8: 剪贴板粘贴输入完整验证+诊断 (用后即删)"""
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
    last = None
    while time.time() < deadline:
        try:
            el = d.find_element(AppiumBy.ANDROID_UIAUTOMATOR, sel)
            return el
        except Exception as e:
            last = str(e)[:80]
            time.sleep(1)
    print(f"find failed ({txt}): {last}")
    return None

# --- 申报页 + 起飞地 ---
d.tap([(432, 2290)]); time.sleep(3.5)
shot("i1_shenbao")
d.tap([(565, 219)]); time.sleep(2.5)
shot("i2_field_tap")

el = find_text("请输入起飞地", timeout=10)
if el is None:
    # 二次预热: 再点一次字段
    d.tap([(565, 219)]); time.sleep(2)
    el = find_text("请输入起飞地", timeout=10)
if el is None:
    print("FIELD NOT FOUND - dump for diagnosis")
    dump("i2_diag")
else:
    print("field found, click")
    el.click(); time.sleep(1.5)
    # 长按 → 粘贴
    d.execute_script("mobile: longClickGesture", {"x": 565, "y": 219, "duration": 1500})
    time.sleep(2)
    shot("i3_longpress")
    paste = find_text("粘贴", timeout=5)
    if paste is None:
        dump("i3_diag")
        print("PASTE MENU NOT FOUND")
    else:
        print("paste clicked")
        paste.click(); time.sleep(2.5)
        shot("i4_pasted")
        dump("i4_pasted")
        r = find_text("新疆起降场1", timeout=10, contains=True)
        if r is None:
            print("RESULT NOT FOUND after paste")
        else:
            print("result found:", r.text)
            r.click(); time.sleep(2.5)
            shot("i5_selected")
            dump("i5_selected")
            print("SELECTED 新疆起降场1")

m.quit_driver()
print("done")
