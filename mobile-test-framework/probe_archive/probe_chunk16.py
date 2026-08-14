# -*- coding: utf-8 -*-
"""探索脚本 Chunk16: 出发时间控件 + 下一步页面探索 (用后即删)"""
import sys
import time
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from appium.webdriver.common.appiumby import AppiumBy
from drivers.appium_driver import AppiumDriverManager
from utils.adb_helper import ADBHelper
from utils import webview_a11y
from pages.login_page import LoginPage
from pages.flight_page import FlightPage

SHOT = Path("reports/screenshots")

def shot(d, name):
    d.save_screenshot(str(SHOT / f"{name}.png"))

def dump(d, name):
    Path(f"reports/{name}.xml").write_text(d.page_source, encoding="utf-8")

def texts_of(d):
    src = d.page_source
    return [mm.group(1) for mm in re.finditer(r'text=\"([^\"]+)\"', src) if mm.group(1) and mm.group(1) != 'None']

ADBHelper().clear_app_data("com.keda.atc")
time.sleep(2)
m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)
LoginPage(d).login("liyang", "Liyang@1128")
try: d.hide_keyboard()
except Exception: pass
time.sleep(2)

webview_a11y.switch_tab(d, "申报", marker="请输入起飞地")
flight = FlightPage(d)
assert flight.select_depart(), "起飞地失败"
assert flight.select_arrive(), "降落地失败"
time.sleep(2)
shot(d, "q1_airports_done")

# 出发时间
el = webview_a11y.find_visible_by_text(d, "出发时间", timeout=8, min_y=500)
if el is None:
    print("出发时间 NOT FOUND")
else:
    print("出发时间 at", el.location)
    el.click(); time.sleep(2.5)
    shot(d, "q2_time_clicked")
    dump(d, "q2_time")
    print("TEXTS:", texts_of(d)[:22])
    # 时间选择器: 若有 确定 按钮则点击 (native picker)
    confirm = webview_a11y.find_text(d, "确定", timeout=4)
    if confirm is not None and confirm.location["y"] > 800:
        print("picker 确定 at", confirm.location)
        confirm.click(); time.sleep(2)
        shot(d, "q3_time_confirmed")
        dump(d, "q3_time")
        print("TEXTS after confirm:", texts_of(d)[:22])
    else:
        print("no 确定 button found")

# 下一步
nxt = webview_a11y.find_visible_by_text(d, "下一步", timeout=8, min_y=1500)
if nxt is None:
    print("下一步 NOT FOUND")
else:
    print("下一步 at", nxt.location)
    nxt.click(); time.sleep(3)
    shot(d, "q4_next_page")
    dump(d, "q4_next")
    print("TEXTS next page:", texts_of(d)[:30])

m.quit_driver()
print("done")
