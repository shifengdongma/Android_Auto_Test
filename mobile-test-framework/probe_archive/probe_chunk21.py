# -*- coding: utf-8 -*-
"""探索脚本 Chunk21: 留空飞行入口 + 空域类型选择 + 我的计划入口 (已归档)

流程: 清数据 -> 登录 -> 申报tab
    1. 点击"留空飞行" -> 抓取类型选择UI
    2. 若有"多边形"选项则点击 -> 抓取绘制页
    3. 点击"我的计划" -> 抓取计划列表页

归档说明: 抓取到留空飞行空域绘制页结构 (三种空域类型选项 y≈1485-1539,
空域名称输入框 y≈1653, 出发时间区 y≈1827+), 已固化为 pages/flight_page.py
的 LoiterPage。
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

SHOT = Path("reports/screenshots")


def shot(d, name):
    d.save_screenshot(str(SHOT / f"{name}.png"))
    print(f"[shot] {name}.png")


def dump(d, name):
    Path(f"reports/{name}.xml").write_text(d.page_source, encoding="utf-8")
    print(f"[dump] {name}.xml")


def show(d, label):
    src = d.page_source
    print(f"----- {label} -----")
    for m in re.finditer(
        r'text="([^"]+)"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', src
    ):
        t, x1, y1, x2, y2 = m.groups()
        if t and t != "None":
            print(f"    ({x1},{y1})-({x2},{y2})  {t}")


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
time.sleep(1)
show(d, "申报页初始")

# ---- 1. 留空飞行 ----
print("\n===== 点击留空飞行 =====")
loiter = webview_a11y.find_visible_by_text(d, "留空飞行", timeout=8, min_y=2000)
assert loiter is not None, "未找到留空飞行"
x, y = webview_a11y.element_center(loiter)
print(f"[info] 留空飞行 at ({x},{y})")
d.tap([(x, y)])
time.sleep(2.5)
shot(d, "l1_loiter_entered")
dump(d, "l1_loiter_entered")
show(d, "留空飞行页面")

# ---- 2. 多边形 (若有) ----
print("\n===== 尝试点击多边形 =====")
poly = webview_a11y.find_visible_by_text(d, "多边形", timeout=3, min_y=300)
if poly is None:
    print("[warn] 未找到多边形选项")
else:
    x, y = webview_a11y.element_center(poly)
    print(f"[info] 多边形 at ({x},{y})")
    d.tap([(x, y)])
    time.sleep(2.5)
    shot(d, "l2_polygon_mode")
    dump(d, "l2_polygon_mode")
    show(d, "多边形绘制模式")

# ---- 3. 返回申报页再进我的计划 ----
print("\n===== 我的计划 =====")
try:
    d.back()
except Exception:
    pass
time.sleep(2)
webview_a11y.switch_tab(d, "申报", marker="请输入起飞地")
time.sleep(1)
plans = webview_a11y.find_visible_by_text(d, "我的计划", timeout=8, min_y=2000)
assert plans is not None, "未找到我的计划"
x, y = webview_a11y.element_center(plans)
print(f"[info] 我的计划 at ({x},{y})")
d.tap([(x, y)])
time.sleep(2.5)
shot(d, "l3_my_plans")
dump(d, "l3_my_plans")
show(d, "我的计划页")

m.quit_driver()
print("done")
