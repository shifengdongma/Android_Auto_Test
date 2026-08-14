# -*- coding: utf-8 -*-
"""探索脚本 Chunk22: 留空飞行三种空域绘制手势验证 + 命名/时间/下一步 (已归档)

流程: 清数据 -> 登录 -> 申报 -> 留空飞行
    1. 多边形: 3点三角形 (单击×3 + 双击结束)
    2. 圆形: 长按拖动 (mobile: dragGesture duration=1500)
    3. 线缓冲区: 2点线 (单击×2 + 双击结束)
    4. 回到多边形画三角形 -> 输入名称"测试" -> 修改出发时间 -> 下一步

归档说明: 三种绘制手势全部验证通过, 已固化为 pages/flight_page.py 的
LoiterPage.draw_polygon/draw_circle/draw_buffer。注意点: 输入空域名称后
必须关闭输入法键盘, 否则底部"修改/下一步"按钮被键盘遮挡不可见。
"""
import sys
import time
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions import interaction

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


def tap(d, x, y):
    d.tap([(x, y)])


def double_click(d, x, y):
    """双击结束绘制: mobile手势优先, 失败回退两次快速tap"""
    try:
        d.execute_script("mobile: doubleClickGesture", {"x": x, "y": y})
        print(f"[gesture] doubleClickGesture ({x},{y})")
        return
    except Exception as e:
        print(f"[warn] doubleClickGesture失败({type(e).__name__}), 回退两次tap")
    d.tap([(x, y)])
    time.sleep(0.08)
    d.tap([(x, y)])


def long_press_drag(d, x1, y1, x2, y2):
    """长按后向外拖动 (圆形绘制): dragGesture慢速拖动模拟长按, 失败回退W3C actions"""
    try:
        d.execute_script(
            "mobile: dragGesture",
            {"startX": x1, "startY": y1, "endX": x2, "endY": y2, "duration": 1500},
        )
        print(f"[gesture] dragGesture ({x1},{y1})->({x2},{y2}) dur=1500")
        return
    except Exception as e:
        print(f"[warn] dragGesture失败({type(e).__name__}), 回退W3C actions")
    actions = ActionBuilder(d, mouse=PointerInput(interaction.POINTER_TOUCH, "touch"))
    actions.pointer_action.move_to_location(x1, y1)
    actions.pointer_action.pointer_down()
    actions.pointer_action.pause(1.0)
    actions.pointer_action.move_to_location(x2, y2)
    actions.pointer_action.pause(0.5)
    actions.pointer_action.pointer_up()
    actions.perform()
    print(f"[gesture] w3c long_press_drag ({x1},{y1})->({x2},{y2})")


def draw_polygon(d, points, tag):
    for i, (x, y) in enumerate(points, 1):
        tap(d, x, y)
        time.sleep(0.8)
        print(f"[draw] 多边形顶点{i}: ({x},{y})")
    double_click(d, points[-1][0], points[-1][1])
    time.sleep(1.5)
    shot(d, tag)
    print(f"[shot] {tag}.png")


def draw_buffer(d, points, tag):
    for i, (x, y) in enumerate(points, 1):
        tap(d, x, y)
        time.sleep(0.8)
        print(f"[draw] 线缓冲点{i}: ({x},{y})")
    double_click(d, points[-1][0], points[-1][1])
    time.sleep(1.5)
    shot(d, tag)
    print(f"[shot] {tag}.png")


def draw_circle(d, center, edge, tag):
    long_press_drag(d, center[0], center[1], edge[0], edge[1])
    time.sleep(1.5)
    shot(d, tag)
    print(f"[shot] {tag}.png")


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
time.sleep(1)
loiter = webview_a11y.find_visible_by_text(d, "留空飞行", timeout=8, min_y=2000)
assert loiter is not None, "未找到留空飞行"
x, y = webview_a11y.element_center(loiter)
d.tap([(x, y)])
time.sleep(2.5)
shot(d, "m1_loiter_page")
print("[info] 已进入留空飞行空域绘制页")

# ---- 1. 多边形 (三角形) ----
poly = webview_a11y.find_visible_by_text(d, "多边形", timeout=5, min_y=1400)
assert poly is not None
d.tap([webview_a11y.element_center(poly)])
time.sleep(1)
draw_polygon(d, [(400, 750), (750, 750), (575, 550)], "m2_polygon_done")

# ---- 2. 圆形 ----
circle = webview_a11y.find_visible_by_text(d, "圆形", timeout=5, min_y=1400)
d.tap([webview_a11y.element_center(circle)])
time.sleep(1)
draw_circle(d, (550, 750), (780, 750), "m3_circle_done")

# ---- 3. 线缓冲区 ----
buf = webview_a11y.find_visible_by_text(d, "线缓冲区", timeout=5, min_y=1400)
d.tap([webview_a11y.element_center(buf)])
time.sleep(1)
draw_buffer(d, [(350, 900), (800, 900)], "m4_buffer_done")

# ---- 4. 回到多边形画最终三角形 ----
d.tap([webview_a11y.element_center(
    webview_a11y.find_visible_by_text(d, "多边形", timeout=5, min_y=1400)
)])
time.sleep(1)
draw_polygon(d, [(400, 750), (750, 750), (575, 550)], "m5_final_polygon")

# ---- 5. 输入空域名称 ----
name_field = webview_a11y.find_visible_by_text(d, "请输入空域名称", timeout=5, min_y=1500)
assert name_field is not None, "未找到空域名称输入框"
d.tap([webview_a11y.element_center(name_field)])
time.sleep(1.2)
webview_a11y.type_chinese(d, "测试")
# 关闭输入法键盘 (否则底部修改/下一步按钮被键盘遮挡)
try:
    d.hide_keyboard()
except Exception:
    ADBHelper().press_key(4)
time.sleep(1.5)
shot(d, "m6_name_input")
print("[info] 空域名称已输入: 测试")

# ---- 6. 修改出发时间 ----
modify = webview_a11y.find_visible_by_text(d, "修改", timeout=5, min_y=1700)
assert modify is not None, "未找到修改按钮"
modify.click()
time.sleep(2)
assert webview_a11y.find_text(d, "选择出发时间", timeout=8) is not None, "时间选择器未打开"
slot = webview_a11y.find_visible_by_text(d, "04:00", timeout=8, min_y=1400)
if slot is not None:
    slot.click()
    time.sleep(1)
confirm = webview_a11y.find_text(d, "确定", timeout=8)
assert confirm is not None, "时间选择器无确定按钮"
confirm.click()
time.sleep(1)
shot(d, "m7_time_modified")
print("[info] 出发时间已修改")

# ---- 7. 下一步 ----
nxt = webview_a11y.find_visible_by_text(d, "下一步", timeout=8, min_y=1900)
assert nxt is not None, "未找到下一步按钮"
x, y = webview_a11y.element_center(nxt)
d.tap([(x, y)])
time.sleep(3)
shot(d, "m8_next_page")
dump(d, "m8_next_page")
src = d.page_source
print("[result] 填写飞行计划:", "OK" if "填写飞行计划" in src else "NOT FOUND")
print("[result] 请选择航空器:", "OK" if "请选择航空器" in src else "NOT FOUND")

m.quit_driver()
print("done")
