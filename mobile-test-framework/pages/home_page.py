# -*- coding: utf-8 -*-
"""
首页 (HomePage)

页面路径: 登录后首页
页面功能 (真机实测):
    - 顶部三个通知模块: 计划审批 / 告警通知 / 管制员通知
    - 通知卡片列表 (有消息时首卡可点进详情)
    - 底部知识助手悬浮入口 (AI问答)

交互方式: 内容为uni-app WebView, 通过 utils.webview_a11y 的
a11y文本节点定位 (见该模块实测规则注释)。
"""

import logging
import time

from pages.base_page import BasePage
from utils import webview_a11y

logger = logging.getLogger(__name__)


class HomePage(BasePage):
    """首页Page Object"""

    # --- 顶部通知模块tab ---
    NOTIFY_TAB_APPROVAL = "计划审批"
    NOTIFY_TAB_ALERT = "告警通知"
    NOTIFY_TAB_COORD = "管制员通知"

    # --- 知识助手入口 (悬浮输入框占位文本) ---
    AI_INPUT_HINT = "输入问题，向知识助手提问..."
    AI_CHAT_MARKER = "智能问答"

    # --- 通知卡片标记 (卡片时间图标的a11y text) ---
    CARD_TIME_ICON = "icon-time"

    def wait_for_home_page(self, timeout: int = 20):
        """等待首页加载 (顶部通知tab出现)"""
        logger.info("等待首页加载...")
        assert webview_a11y.find_text(
            self.driver, self.NOTIFY_TAB_APPROVAL, timeout=timeout
        ) is not None, "首页未加载: 未发现'计划审批'模块tab"
        return self

    def is_on_home_page(self) -> bool:
        """判断当前是否在首页"""
        return webview_a11y.find_text(
            self.driver, self.NOTIFY_TAB_APPROVAL, timeout=3
        ) is not None

    def switch_notify_tab(self, tab: str):
        """
        点击顶部通知模块tab

        Args:
            tab: 计划审批 / 告警通知 / 管制员通知

        Returns:
            self
        """
        logger.info(f"切换通知模块: {tab}")
        el = webview_a11y.find_visible_by_text(self.driver, tab, timeout=8, min_y=200)
        assert el is not None, f"未找到通知模块tab: {tab}"
        el.click()
        time.sleep(2)
        return self

    def has_notifications(self) -> bool:
        """当前通知模块是否存在消息卡片"""
        return webview_a11y.find_visible_by_text(
            self.driver, self.CARD_TIME_ICON, timeout=5, min_y=450
        ) is not None

    def open_first_notification(self):
        """点击第一条通知卡片进入详情"""
        logger.info("点击第一条通知卡片")
        el = webview_a11y.find_visible_by_text(
            self.driver, self.CARD_TIME_ICON, timeout=8, min_y=450
        )
        assert el is not None, "未找到通知卡片"
        el.click()
        time.sleep(2.5)
        return self

    def is_on_notification_detail(self) -> bool:
        """判断是否在通知详情页 (标题含'详情')"""
        return webview_a11y.find_visible_by_text(
            self.driver, "详情", timeout=5, min_y=100
        ) is not None

    def go_back(self):
        """返回上一页"""
        self.driver.back()
        time.sleep(2)
        return self

    def open_ai_assistant(self):
        """
        点击知识助手入口 (底部悬浮输入框)

        Returns:
            self (进入AI问答页后可用 is_on_ai_assistant 验证)
        """
        logger.info("点击知识助手入口")
        el = webview_a11y.find_visible_by_text(
            self.driver, self.AI_INPUT_HINT, timeout=8, min_y=1500
        )
        assert el is not None, "未找到知识助手入口"
        el.click()
        time.sleep(3)
        return self

    def is_on_ai_assistant(self) -> bool:
        """判断是否进入知识助手问答页"""
        return webview_a11y.find_text(
            self.driver, self.AI_CHAT_MARKER, timeout=8
        ) is not None
