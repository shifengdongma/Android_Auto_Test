# -*- coding: utf-8 -*-
"""探索脚本 Chunk13: 机场选择后的表单状态 (出发时间/下一步) (用后即删)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from appium.webdriver.common.appiumby import AppiumBy
from drivers.appium_driver import AppiumDriverManager
from utils.adb_helper import ADBHelper

SHOT = Path("reports/screenshots")

def shot(d, name):
    d.save_screenshot(str(SHOT / f"{name}.png"))

def dump(d, name):
    Path(f"reports/{name}.xml").write_text(d.page_source, encoding="utf-8")

def find(d, txt, timeout=8, contains=False):
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
    s = el.size
    return loc["x"] + s["width"] // 2, loc["y"] + s["height"] // 2

def search_field(d, field_text, keyword, result_text):
    el = find(d, field_text, timeout=8)
    if el is None:
        print(f"FIELD {field_text} NOT FOUND")
        return False
    el.click(); time.sleep(2)
    if find(d, "是否允许", timeout=2, contains=True) is not None:
        d.tap([(576, 2100)]); time.sleep(2)
    el = find(d, field_text, timeout=8)
    if el is None:
        print("field lost")
        return False
    x, y = center(el)
    el.click(); time.sleep(1.5)
    d.set_clipboard_text(keyword)
    d.execute_script("mobile: longClickGesture", {"x": x, "y": y, "duration": 1500})
    time.sleep(2)
    paste = find(d, "粘贴", timeout=5)
    if paste is None:
        print("PASTE NOT FOUND")
        return False
    paste.click(); time.sleep(2.5)
    r = find(d, result_text, timeout=8, contains=True)
    if r is None:
        print(f"RESULT {result_text} NOT FOUND")
        shot(d, "o_noresult")
        return False
    r.click(); time.sleep(2.5)
    return True

ADBHelper().clear_app_data("com.keda.atc")
time.sleep(2)
m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)
from pages.login_page import LoginPage
LoginPage(d).login("liyang", "Liyang@1128")
try: d.hide_keyboard()
except Exception: pass
time.sleep(2)

# 单次tab点击 + 等待
d.tap([(432, 2290)]); time.sleep(4)
print("apply page entered")
ok1 = search_field(d, "请输入起飞地", "新疆", "新疆起降场1")
print("起飞地:", ok1)
time.sleep(1.5)
ok2 = search_field(d, "请输入降落地", "新疆", "新疆起降场2")
print("降落地:", ok2)
time.sleep(2)
shot(d, "o_after_airports")
dump(d, "o_after_airports")

# 看看有没有出发时间/下一步
for t in ["出发时间", "下一步"]:
    e = find(d, t, timeout=3, contains=True)
    print(f"{t}:", "FOUND" if e else "not found")

m.quit_driver()
print("done")
