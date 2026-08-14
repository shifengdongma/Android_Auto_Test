# -*- coding: utf-8 -*-
"""探索脚本 Chunk2: 申报/资讯/我的 三页入口截图 (用后即删)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from drivers.appium_driver import AppiumDriverManager

SHOT = Path("reports/screenshots")

m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)

# 底部原生tab: 首页(144,2290) 申报(432,2290) 资讯(720,2290) 我的(1008,2290)
d.tap([(432, 2290)]); time.sleep(3)
d.save_screenshot(str(SHOT / "f1_shenbao.png"))
d.tap([(720, 2290)]); time.sleep(3)
d.save_screenshot(str(SHOT / "n1_zixun.png"))
d.tap([(1008, 2290)]); time.sleep(3)
d.save_screenshot(str(SHOT / "m1_mine.png"))
m.quit_driver()
print("done")
