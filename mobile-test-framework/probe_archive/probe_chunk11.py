# -*- coding: utf-8 -*-
"""探索脚本 Chunk11: 权限处理 -> 起飞地搜索选择全链路 (用后即删)"""
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

ADBHelper().clear_app_data("com.keda.atc")
time.sleep(2)

m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)

from pages.login_page import LoginPage
LoginPage(d).login("liyang", "Liyang@1128")
print("logged in")
time.sleep(2)

d.tap([(432, 2332)]); time.sleep(3.5)     # 申报 tab
d.tap([(565, 219)]); time.sleep(3)        # 起飞地 -> 触发权限弹窗
shot(d, "m1_perm")

# 权限弹窗: EMUI按钮
if find(d, "是否允许", timeout=3, contains=True) is not None:
    print("permission dialog shown, tap 允许本次使用")
    d.tap([(576, 2100)]); time.sleep(2.5)
    shot(d, "m2_perm_allow")
else:
    print("no permission dialog")

# 再次点击起飞地打开picker
d.tap([(565, 219)]); time.sleep(3)
shot(d, "m3_picker")
dump(d, "m3_picker")

# picker中的搜索框: 找EditText或搜索占位文本
edits = d.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
vis = []
for e in edits:
    try:
        if e.is_displayed():
            vis.append(e)
            print("visible EditText:", e.location, e.size)
    except Exception:
        pass
print("visible EditTexts:", len(vis))

# 无论是否找到EditText, 尝试剪贴板粘贴到搜索框 (picker顶部)
search_el = vis[0] if vis else None
if search_el is not None:
    x = search_el.location["x"] + search_el.size["width"] // 2
    y = search_el.location["y"] + search_el.size["height"] // 2
else:
    # 猜picker搜索框位置: 面板顶部 (默认在起飞地字段上方)
    x, y = 565, 219
search_el.click() if search_el is not None else d.tap([(x, y)])
time.sleep(1.5)
d.set_clipboard_text("新疆")
d.execute_script("mobile: longClickGesture", {"x": x, "y": y, "duration": 1500})
time.sleep(2)
shot(d, "m4_longpress")
paste = find(d, "粘贴", timeout=5)
if paste is None:
    print("PASTE NOT FOUND")
    dump(d, "m4_diag")
else:
    print("paste clicked")
    paste.click(); time.sleep(2.5)
    shot(d, "m5_pasted")
    dump(d, "m5_pasted")
    r = find(d, "新疆起降场1", timeout=8, contains=True)
    if r is None:
        print("RESULT NOT FOUND")
    else:
        print("result:", r.text, "at", r.location, r.size)
        r.click(); time.sleep(2.5)
        shot(d, "m6_selected")
        dump(d, "m6_selected")
        print("SELECTED")

m.quit_driver()
print("done")
