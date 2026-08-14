# -*- coding: utf-8 -*-
"""探索脚本 Chunk19: 提交飞行计划后的确认弹窗元素抓取 (已归档)

流程: 清数据 -> 登录 -> 申报 -> 起降场x3 -> 时间 -> 下一步
     -> 航空器/操控员 (复用已校准方法) -> 提交 -> 抓取确认弹窗 -> 点确定 -> 抓结果

归档说明: 抓取确认弹窗 ("进入PC端飞行计划审批流程" + 确定按钮),
结果已固化为 pages/flight_page.py 的 submit_plan()。
"""
import sys
import time
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from drivers.appium_driver import AppiumDriverManager
from utils.adb_helper import ADBHelper
from utils import webview_a11y
from pages.login_page import LoginPage
from pages.flight_page import FlightPage

SHOT = Path("reports/screenshots")


def shot(d, name):
    d.save_screenshot(str(SHOT / f"{name}.png"))
    print(f"[shot] {name}.png")


def dump(d, name):
    Path(f"reports/{name}.xml").write_text(d.page_source, encoding="utf-8")
    print(f"[dump] {name}.xml")


def visible_texts(d):
    src = d.page_source
    out = []
    for m in re.finditer(
        r'text="([^"]+)"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', src
    ):
        t, x1, y1, x2, y2 = m.groups()
        if t and t != "None":
            out.append((t, int(x1), int(y1), int(x2), int(y2)))
    return out


def show(d, label):
    print(f"----- {label} -----")
    for t, x1, y1, x2, y2 in visible_texts(d):
        print(f"    ({x1},{y1})-({x2},{y2})  {t}")


# ---- 主流程 (复用已校准方法) ----
ADBHelper().clear_app_data("com.keda.atc")
time.sleep(2)
m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)
LoginPage(d).login("liyang", "Liyang@1128")
try:
    d.hide_keyboard()
except Exception:
    pass
time.sleep(2)

webview_a11y.switch_tab(d, "申报", marker="请输入起飞地")
flight = FlightPage(d)
assert flight.select_depart(), "起飞地失败"
assert flight.select_arrive(), "降落地失败"
assert flight.select_alternate(), "备降地失败"
time.sleep(2)
shot(d, "z1_three_airports")
dump(d, "z1_three_airports")
show(d, "三个起降场选择后")
try:
    ok = flight.modify_departure_time("04:00")
    assert ok, "出发时间修改失败"
except AssertionError:
    shot(d, "z2_time_fail")
    dump(d, "z2_time_fail")
    show(d, "出发时间失败现场")
    raise
assert flight.click_next_step(), "未进入填写飞行计划页"
time.sleep(2)
assert flight.select_aircraft(), "航空器失败"
assert flight.select_operator(), "操控员失败"
time.sleep(1)
shot(d, "x1_before_submit")

# ---- 提交 ----
print("\n===== 点击提交 =====")
sub = webview_a11y.find_visible_by_text(d, "提交", timeout=8, min_y=2000)
assert sub is not None, "未找到提交按钮"
x, y = webview_a11y.element_center(sub)
print(f"[info] 提交 at ({x},{y})")
d.tap([(x, y)])
time.sleep(2)
shot(d, "x2_after_submit")
dump(d, "x2_after_submit")
show(d, "提交后2秒 弹窗元素")

# ---- 找确定并点击 ----
print("\n===== 点击确定 =====")
confirm = webview_a11y.find_visible_by_text(d, "确定", timeout=5, min_y=1000)
if confirm is None:
    print("[warn] 未找到'确定', 列出全部可见文本:")
    show(d, "全部文本")
else:
    cx, cy = webview_a11y.element_center(confirm)
    print(f"[info] 确定 at ({cx},{cy})")
    d.tap([(cx, cy)])
    time.sleep(3)
    shot(d, "x3_after_confirm")
    dump(d, "x3_after_confirm")
    show(d, "点确定后")

m.quit_driver()
print("done")
