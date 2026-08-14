# -*- coding: utf-8 -*-
"""探索脚本 Chunk1: 首页三模块/AI助手/卡片详情 (坐标初探, 用后即删)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from drivers.appium_driver import AppiumDriverManager

SHOT = Path("reports/screenshots")

m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)

def tap(x, y, name, wait=2.5):
    d.tap([(x, y)])
    time.sleep(wait)
    d.save_screenshot(str(SHOT / f"{name}.png"))
    print(f"tap({x},{y}) -> {name}.png")

tap(0, 0, "h1_home_initial", wait=0.5)
# 顶部三个通知模块tab (y≈370)
tap(583, 370, "h2_gaojing")      # 告警通知
tap(1012, 370, "h3_guanzhi")     # 管制员通知
tap(143, 370, "h4_huifu_jihua")  # 计划审批
# 第一张通知卡片
tap(500, 700, "h5_card_detail")
d.back(); time.sleep(2); d.save_screenshot(str(SHOT / "h6_after_back.png"))
# 右下角知识助手悬浮按钮
tap(1038, 2100, "h7_ai_assistant", wait=3.5)
d.back(); time.sleep(2); d.save_screenshot(str(SHOT / "h8_after_ai_back.png"))
m.quit_driver()
print("done")
