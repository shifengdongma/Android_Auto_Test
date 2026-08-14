# -*- coding: utf-8 -*-
"""探索脚本 Chunk18: 最小验证 - session创建 + 页面元素抓取是否响应 (已归档)

目的: 验证设备端UiAutomator2仪器在清理重装后是否恢复正常响应。
通过标准: 30秒内抓取到登录页EditText并打印。

归档说明: 当时用于验证设备重启后仪器恢复 (此前仪器进程D状态死锁,
元素查询240s超时)。排查过程见 docs/工作日志.md 2026-08-14 环境问题节。
"""
import sys
import time
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from appium.webdriver.common.appiumby import AppiumBy
from drivers.appium_driver import AppiumDriverManager

m = AppiumDriverManager()
d = m.get_driver()
t0 = time.time()
time.sleep(6)

try:
    els = d.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
    print(f"[chunk18] EditText数量: {len(els)} (耗时{time.time()-t0:.1f}s)")
    for e in els:
        print(f"  EditText at {e.location} size={e.size}")
    src = d.page_source
    texts = [t for t in re.findall(r'text="([^"]+)"', src) if t and t != "None"]
    print(f"[chunk18] page_source_len={len(src)} 文本节点数={len(texts)}")
    print(f"[chunk18] 文本示例: {texts[:12]}")
    d.save_screenshot("reports/screenshots/chunk18_verify.png")
    print("[chunk18] VERIFY-OK")
except Exception as e:
    print(f"[chunk18] VERIFY-FAIL: {type(e).__name__}: {e}")
m.quit_driver()
print("done")
