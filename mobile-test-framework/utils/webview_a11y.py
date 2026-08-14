# -*- coding: utf-8 -*-
"""
WebView内容区自动化工具 (uni-app a11y树交互)

背景: 被测应用 (com.keda.atc, uni-app) 页面内容渲染在 WebView 中,
原生层仅暴露底部Tab。本模块封装真机实测总结的交互规则。

实测规则 (设备 NOH-AN01, 1152x2376, 2026-08-14):
  1. 内容区a11y树在页面被单次点击后约4秒内构建完成; 反复点击会打断构建
  2. 底部原生tab点击坐标 y=2290 (更靠下会被手势导航区拦截)
  3. a11y树包含后台堆叠页面的节点, 选节点必须用 is_displayed + 位置过滤
  4. webview输入框无法 send_keys, 中文输入用 剪贴板 + keyevent 279 (原生粘贴)
  5. 数据清空(pm clear)后首次进入申报页弹系统位置权限, EMUI按钮为"允许本次使用"
"""

import logging
import time
from typing import Optional, Tuple

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement

from utils.adb_helper import ADBHelper

logger = logging.getLogger(__name__)

# ---- 底部原生tab坐标 (y=2290 避开手势导航区) ----
TAB_X = {"首页": 144, "申报": 432, "资讯": 720, "我的": 1008}
TAB_Y = 2290

# ---- EMUI权限弹窗 ----
PERM_DIALOG_TEXT = "是否允许"
PERM_ALLOW_THIS_TIME = (576, 2100)

# ---- Android原生粘贴按键 ----
KEYCODE_PASTE = 279

_adb = None


def _get_adb() -> ADBHelper:
    global _adb
    if _adb is None:
        _adb = ADBHelper()
    return _adb


def find_text(
    driver, text: str, timeout: float = 8, contains: bool = False
) -> Optional[WebElement]:
    """轮询查找文本节点 (a11y树可能延迟构建)"""
    sel = f'new UiSelector().{"textContains" if contains else "text"}("{text}")'
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, sel)
        except Exception:
            time.sleep(0.8)
    return None


def find_visible_by_text(
    driver, text: str, timeout: float = 8, min_y: int = 0, max_y: int = 0,
    exact: bool = False,
) -> Optional[WebElement]:
    """查找可见文本节点 (排除后台堆叠页面的同文案节点; 可选按y区间过滤)

    Args:
        min_y: y下界 (0=不限)
        max_y: y上界 (0=不限, 如650=仅表单区, 排除下方列表项)
        exact: True=精确匹配 (默认textContains; 用于排除同文案子串节点,
               如首页卡片"新疆起降场1 → 新疆起降场2"包含两个场名)
    """
    sel = f'new UiSelector().{"text" if exact else "textContains"}("{text}")'
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            els = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, sel)
            for el in els:
                if el.is_displayed() and el.location["y"] >= min_y:
                    if max_y and el.location["y"] >= max_y:
                        continue
                    return el
        except Exception:
            pass
        time.sleep(0.8)
    return None


def element_center(el: WebElement) -> Tuple[int, int]:
    """元素中心坐标"""
    loc = el.location
    size = el.size
    return loc["x"] + size["width"] // 2, loc["y"] + size["height"] // 2


def switch_tab(driver, tab_name: str, marker: str = None, timeout: float = 25) -> bool:
    """
    切换底部原生tab: 单次点击+等待a11y构建, 用marker文本验证切换成功

    Args:
        driver: Appium driver
        tab_name: 首页/申报/资讯/我的
        marker: 目标页面特征文本 (None则只点击不验证)

    Returns:
        bool: 是否切换成功
    """
    x = TAB_X[tab_name]
    logger.info(f"切换tab: {tab_name}")
    try:
        driver.hide_keyboard()
    except Exception:
        pass
    deadline = time.time() + timeout
    while time.time() < deadline:
        driver.tap([(x, TAB_Y)])
        if marker is None:
            time.sleep(4)
            return True
        if find_text(driver, marker, timeout=6, contains=True) is not None:
            return True
        time.sleep(2)
    logger.warning(f"切换tab {tab_name} 后未出现标记: {marker}")
    return False


def type_chinese(driver, text: str) -> bool:
    """
    向当前已聚焦的webview输入框输入中文 (剪贴板 + 原生粘贴键)

    前置: 输入框必须已获得焦点 (点击后约1秒)。
    """
    driver.set_clipboard_text(text)
    time.sleep(0.3)
    _get_adb().press_key(KEYCODE_PASTE)
    # 实测: 粘贴后列表过滤需要约2秒, 等待过短会漏列表
    time.sleep(2.5)
    return True


def handle_emui_permission(driver, timeout: float = 3) -> bool:
    """处理EMUI系统权限弹窗 (华为定制文案, 点击"允许本次使用")"""
    if find_text(driver, PERM_DIALOG_TEXT, timeout=timeout, contains=True) is not None:
        logger.info("检测到EMUI权限弹窗, 点击'允许本次使用'")
        try:
            driver.tap([PERM_ALLOW_THIS_TIME])
        except Exception as e:
            # W3C action链偶发失败时回退ADB直接点击
            logger.warning(f"W3C点击权限按钮失败({e}), 回退ADB点击")
            _get_adb().tap(*PERM_ALLOW_THIS_TIME)
        time.sleep(1.2)
        return True
    return False


def pick_result(
    driver, result_text: str, timeout: float = 10, min_y: int = 650
) -> Optional[WebElement]:
    """
    选择列表中可见的结果项

    min_y=650: 排除表单字段 (y<500) 的同文案节点; picker列表项实测 y>=693。
    exact=True: 排除后台首页通知卡片的子串误判 (卡片文本为
    "新疆起降场1 → 新疆起降场2", textContains会命中, 实测导致点错列表项)。
    """
    return find_visible_by_text(
        driver, result_text, timeout=timeout, min_y=min_y, exact=True
    )


def find_first_list_item(
    driver, y_min: int = 650, y_max: int = 1350, timeout: float = 15
):
    """
    查找列表第一项文本节点的中心坐标 (用于未知文案的picker列表)

    Args:
        y_min/y_max: 列表区域y范围 (表单行在500内, 首页卡片~510, 列表项693起)

    Returns:
        tuple(x, y, text)|None
    """
    import re

    deadline = time.time() + timeout
    while time.time() < deadline:
        src = driver.page_source
        for m in re.finditer(
            r'text="([^"]+)"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', src
        ):
            text, x1, y1, x2, y2 = m.groups()
            # x1<400: 列表项起点x≈84, 表单值文本x≈402 (排除表单行)
            if text and int(x1) < 400 and int(y1) >= y_min and int(y2) <= y_max:
                return (int(x1) + int(x2)) // 2, (int(y1) + int(y2)) // 2, text
        time.sleep(1)
    return None


# ---- 弹层静态按钮文案 (列表项过滤用) ----
SHEET_STATIC_TEXTS = {"取消", "确定", "提交"}


def find_top_sheet_item(
    driver, y_min: int = 2050, y_max: int = 2360, timeout: float = 10
):
    """
    查找底部弹层列表首项的 y1 坐标 (填写飞行计划页的航空器/操控员弹层)

    实测结构 (NOH-AN01, 2026-08-14):
        弹层头部: 取消 | 选择航空器/选择操控员 | 确定 (y≈1930-2090)
        列表项: y≈2100-2360 (单选行); 页面底部 取消/提交 与首页AI助手条
        也落在该区间, 按文案排除后取最靠上节点即为列表首行。

    Returns:
        int|None: 首行文本节点的 y1 (tap时 y = y1+33 落入首行)
    """
    import re

    deadline = time.time() + timeout
    while time.time() < deadline:
        src = driver.page_source
        best = None
        for m in re.finditer(
            r'text="([^"]+)"[^>]*?bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', src
        ):
            text, x1, y1, x2, y2 = m.groups()
            if not text or text == "None" or text in SHEET_STATIC_TEXTS:
                continue
            if not (y_min <= int(y1) <= y_max):
                continue
            if best is None or int(y1) < best:
                best = int(y1)
        if best is not None:
            return best
        time.sleep(0.8)
    return None


def ensure_fresh_state(config) -> None:
    """清空应用数据 (测试前置: a11y树构建依赖干净状态)"""
    pkg = config.get("devices")[0]["app_package"]
    _get_adb().clear_app_data(pkg)
    time.sleep(2)
