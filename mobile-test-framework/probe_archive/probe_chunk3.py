# -*- coding: utf-8 -*-
"""探索脚本 Chunk3: 申报页-点击起飞地字段 (用后即删)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from drivers.appium_driver import AppiumDriverManager

SHOT = Path("reports/screenshots")

m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)

d.tap([(432, 2290)]); time.sleep(3)   # 底部tab -> 申报
d.save_screenshot(str(SHOT / "a0_shenbao_reentry.png"))
d.tap([(800, 440)]); time.sleep(3)    # 起飞地字段 (估值)
d.save_screenshot(str(SHOT / "a1_qifeidi_clicked.png"))
m.quit_driver()
print("done")
