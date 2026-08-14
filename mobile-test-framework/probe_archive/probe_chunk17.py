# -*- coding: utf-8 -*-
"""探索脚本 Chunk17: 填写飞行计划页 - 航空器/操控员底部弹层 + 提交 (已归档)

流程 (复用已校准的 page 方法):
    清数据 -> 启动 -> 登录 -> 申报tab -> 三个起降场 -> 出发时间 -> 下一步
    -> 填写飞行计划页: 点击航空器 -> 抓取弹层 -> 选首项 -> 点击操控员
    -> 抓取弹层 -> 选首项 -> 点击提交 -> 抓取结果

归档说明: 该脚本当时用于抓取填写飞行计划页弹层元素, 抓取结果已固化为
    pages/flight_page.py 的 select_aircraft/select_operator/submit_plan。
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


def pick_row(d, placeholder, coord_fallback, shot_prefix):
    print(f"\n===== 选择: {placeholder} =====")
    el = webview_a11y.find_visible_by_text(d, placeholder, timeout=8, min_y=200)
    if el is None:
        print(f"[warn] 未找到 {placeholder}, 用坐标点击 {coord_fallback}")
        d.tap([coord_fallback])
    else:
        x, y = webview_a11y.element_center(el)
        print(f"[info] {placeholder} at ({x},{y})")
        d.tap([(x, y)])
    time.sleep(2)
    shot(d, f"{shot_prefix}_picker_open")
    dump(d, f"{shot_prefix}_picker_open")
    print(f"[dump] 弹层文本节点:")
    for t, x1, y1, x2, y2 in visible_texts(d):
        if y1 > 600:
            print(f"    ({x1},{y1})-({x2},{y2})  {t}")

    item = webview_a11y.find_first_list_item(d, y_min=800, y_max=1700)
    if item is not None:
        print(f"[info] a11y列表首项: {item}")
        d.tap([(item[0], item[1])])
    else:
        print("[warn] a11y无列表项, 坐标兜底 (576,1080)")
        d.tap([(576, 1080)])
    time.sleep(1.5)
    shot(d, f"{shot_prefix}_after_select")
    dump(d, f"{shot_prefix}_after_select")

    still = webview_a11y.find_visible_by_text(
        d, placeholder, timeout=3, min_y=200
    )
    ok = still is None
    print(f"[result] {placeholder} 选择: {'成功' if ok else '失败(占位文本仍在)'}")
    return ok


# ---- 主流程 ----
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
assert flight.modify_departure_time("04:00"), "出发时间修改失败"
assert flight.click_next_step(), "未进入填写飞行计划页"
time.sleep(2)
shot(d, "w1_plan_page")
dump(d, "w1_plan_page")
print("\n===== 填写飞行计划页 文本节点 =====")
for t, x1, y1, x2, y2 in visible_texts(d):
    print(f"    ({x1},{y1})-({x2},{y2})  {t}")

ok1 = pick_row(d, "请选择航空器", (724, 366), "w2_aircraft")
ok2 = pick_row(d, "请选择操控员", (724, 523), "w3_operator")

# ---- 提交 ----
print("\n===== 点击提交 =====")
sub = webview_a11y.find_visible_by_text(d, "提交", timeout=8, min_y=2000)
if sub is None:
    print("[warn] a11y未找到提交按钮, 坐标兜底 (721,2265)")
    d.tap([(721, 2265)])
else:
    x, y = webview_a11y.element_center(sub)
    print(f"[info] 提交 at ({x},{y})")
    d.tap([(x, y)])
time.sleep(3)
shot(d, "w4_submitted")
dump(d, "w4_submitted")
print("[dump] 提交后文本节点:")
for t, x1, y1, x2, y2 in visible_texts(d):
    print(f"    ({x1},{y1})-({x2},{y2})  {t}")

print(f"\n总结: 航空器={'OK' if ok1 else 'FAIL'} 操控员={'OK' if ok2 else 'FAIL'}")
m.quit_driver()
print("done")
