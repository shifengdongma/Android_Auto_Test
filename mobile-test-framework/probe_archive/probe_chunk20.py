# -*- coding: utf-8 -*-
"""探索脚本 Chunk20: 降落地选择失败现场诊断 (已归档)

聚焦: 起飞地选择成功后, 降落地字段点击->粘贴->点击结果 各子步骤的a11y树状态,
定位"点击结果后字段未更新"的真实原因 (树缺失? 点击未生效? 值节点延迟?)。

归档说明: 定位到根因为 pick_result 的 textContains 子串匹配命中后台首页卡片
"新疆起降场1 → 新疆起降场2" (中心(594,753)即卡片中心), 实际点中了列表第一项。
修复见 utils/webview_a11y.py pick_result (exact=True)。
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
flight = FlightPage(d)
assert flight.select_depart(), "起飞地失败"
time.sleep(2)
show(d, "起飞地完成后")

# ---- 降落地 手动分步 ----
print("\n===== 降落地: 点击字段 =====")
el = webview_a11y.find_text(d, "请输入降落地", timeout=10)
assert el is not None, "未找到降落地字段"
x, y = webview_a11y.element_center(el)
d.tap([(x, y)])
time.sleep(2)
show(d, "字段点击后")

print("\n===== 降落地: 粘贴关键词 =====")
webview_a11y.type_chinese(d, "新疆")
shot(d, "y1_pasted")
dump(d, "y1_pasted")
show(d, "粘贴后")

print("\n===== 降落地: 点击结果项 =====")
r = webview_a11y.pick_result(d, "新疆起降场2", timeout=20)
assert r is not None, "未找到结果项"
rx, ry = webview_a11y.element_center(r)
print(f"[info] 结果项 at ({rx},{ry})")
d.tap([(rx, ry)])
start = time.time()
for target, tag in [(1, "y2_click+1s"), (5, "y3_click+5s"), (10, "y4_click+10s")]:
    while time.time() - start < target:
        time.sleep(0.5)
    shot(d, tag)
    dump(d, tag)
    show(d, tag)

m.quit_driver()
print("done")
