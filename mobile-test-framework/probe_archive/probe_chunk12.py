# -*- coding: utf-8 -*-
"""探索脚本 Chunk12: 稳健模式打通申报起飞地/降落地搜索选择 (用后即删)"""
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

def find(d, txt, timeout=6, contains=False):
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

def ensure_page(d, tab_xy, marker, timeout=20):
    """点tab并轮询页面标记, 失败重试"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if find(d, marker, timeout=2, contains=True) is not None:
            return True
        try:
            d.hide_keyboard()
        except Exception:
            pass
        d.tap([tab_xy])
        time.sleep(2.5)
    return False

def handle_perm(d):
    if find(d, "是否允许", timeout=2, contains=True) is not None:
        print("  permission dialog -> 允许本次使用")
        d.tap([(576, 2100)]); time.sleep(2)
        return True
    return False

def search_field(d, field_text, keyword, result_text):
    """点击字段 -> 粘贴关键词 -> 点击结果"""
    el = find(d, field_text, timeout=6)
    if el is None:
        print(f"  FIELD {field_text} NOT FOUND")
        return False
    x, y = center(el)
    print(f"  field {field_text} at ({x},{y})")
    el.click(); time.sleep(2)
    handle_perm(d)
    # 重新定位字段(可能位移), 聚焦
    el = find(d, field_text, timeout=6)
    if el is None:
        print("  field lost after click")
        return False
    x, y = center(el)
    el.click(); time.sleep(1.5)
    d.set_clipboard_text(keyword)
    d.execute_script("mobile: longClickGesture", {"x": x, "y": y, "duration": 1500})
    time.sleep(2)
    shot(d, "n_longpress")
    paste = find(d, "粘贴", timeout=5)
    if paste is None:
        print("  PASTE NOT FOUND")
        dump(d, "n_diag")
        return False
    paste.click(); time.sleep(2.5)
    shot(d, "n_pasted")
    dump(d, "n_pasted")
    r = find(d, result_text, timeout=8, contains=True)
    if r is None:
        print(f"  RESULT {result_text} NOT FOUND")
        return False
    print(f"  result {result_text} at {center(r)}")
    r.click(); time.sleep(2.5)
    shot(d, "n_selected")
    return True

ADBHelper().clear_app_data("com.keda.atc")
time.sleep(2)

m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)

from pages.login_page import LoginPage
LoginPage(d).login("liyang", "Liyang@1128")
try:
    d.hide_keyboard()
except Exception:
    pass
time.sleep(1)
print("logged in")
time.sleep(2)

ok = ensure_page(d, (432, 2290), "请输入起飞地")
print("apply page:", ok)
if not ok:
    dump(d, "n_apply_fail")
else:
    shot(d, "n_apply")
    # 起飞地
    if search_field(d, "请输入起飞地", "新疆", "新疆起降场1"):
        print("起飞地 selected")
    # 降落地
    if search_field(d, "请输入降落地", "新疆", "新疆起降场2"):
        print("降落地 selected")
    shot(d, "n_final")
    dump(d, "n_final")

m.quit_driver()
print("done")
