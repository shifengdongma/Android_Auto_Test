# -*- coding: utf-8 -*-
"""
资讯 (NewsPage)

页面功能 (真机实测):
    - 顶部三个功能模块: 法律法规 / 通知公告 / 系统公告
    - 各模块内容列表 (无数据时显示"暂无数据")

交互方式: uni-app WebView内容, 经 utils.webview_a11y 定位。
"""

import logging
import time

from pages.base_page import BasePage
from utils import webview_a11y

logger = logging.getLogger(__name__)


class NewsPage(BasePage):
    """资讯Page Object"""

    TAB_LAW = "法律法规"
    TAB_NOTICE = "通知公告"
    TAB_SYSTEM = "系统公告"
    TABS = [TAB_LAW, TAB_NOTICE, TAB_SYSTEM]

    EMPTY_MARKER = "暂无数据"

    def switch_tab(self, tab: str):
        """点击顶部功能模块tab"""
        logger.info(f"切换资讯模块: {tab}")
        el = webview_a11y.find_visible_by_text(self.driver, tab, timeout=8, min_y=200)
        assert el is not None, f"未找到资讯模块tab: {tab}"
        el.click()
        time.sleep(2)
        return self

    def is_tab_present(self, tab: str) -> bool:
        """判断模块tab是否仍在页面 (切换未崩溃/未跳走)"""
        return webview_a11y.find_visible_by_text(
            self.driver, tab, timeout=5, min_y=200
        ) is not None

    def has_empty_state(self) -> bool:
        """当前模块是否显示暂无数据"""
        return webview_a11y.find_visible_by_text(
            self.driver, self.EMPTY_MARKER, timeout=3, min_y=450
        ) is not None
