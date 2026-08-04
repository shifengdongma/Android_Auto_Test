# -*- coding: utf-8 -*-
"""
首页 (HomePage)

页面路径: 登录成功后的默认Tab页
页面功能 (双态设计):
    默认态:
        - 消息通知列表 (三个Tab: 计划审批/告警通知/管制员通知)
        - 底部AI输入框
    对话态:
        - AI智能问答对话区域
        - "返回首页"按钮
        - "对话历史"按钮
        - 快捷对话入口

对应原型: pages/小程序_首页.html
"""

import logging
from typing import List, Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class HomePage(BasePage):
    """
    首页Page Object

    封装首页通知列表和AI对话的操作。
    """

    # ============================================================
    # 元素定位器
    # ============================================================

    # --- 页面标识 ---
    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("首页")')
    TAB_BAR_HOME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("首页")')

    # --- 通知Tab切换 ---
    NOTIFY_TAB_APPROVAL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("计划审批")')
    NOTIFY_TAB_ALERT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("告警通知")')
    NOTIFY_TAB_COORD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("管制员通知")')

    # --- 通知列表 ---
    NOTIFICATION_LIST = (AppiumBy.ID, "com.dolphin.atc:id/rv_notifications")
    NOTIFY_CARD = (AppiumBy.ID, "com.dolphin.atc:id/notify_card")
    NOTIFY_CARD_TITLE = (AppiumBy.ID, "com.dolphin.atc:id/notify_title")
    NOTIFY_CARD_TIME = (AppiumBy.ID, "com.dolphin.atc:id/notify_time")
    NOTIFY_BADGE = (AppiumBy.ID, "com.dolphin.atc:id/notify_badge")

    # --- 告警子筛选 ---
    ALERT_FILTER_UNREAD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("未读")')
    ALERT_FILTER_READ = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("已读")')

    # --- 管制员通知操作 ---
    COORD_ACK_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("已知晓")')
    COORD_DONE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("已处理")')

    # --- AI对话态 ---
    AI_INPUT_FIELD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)')
    AI_SEND_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("发送")')
    AI_BACK_HOME_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("返回首页")')
    AI_HISTORY_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("对话历史")')
    AI_CHAT_AREA = (AppiumBy.ID, "com.dolphin.atc:id/chat_area")
    AI_MESSAGE_BUBBLE = (AppiumBy.ID, "com.dolphin.atc:id/msg_bubble")

    # --- 对话历史 ---
    HISTORY_LIST = (AppiumBy.ID, "com.dolphin.atc:id/history_list")
    HISTORY_ITEM_TITLE = (AppiumBy.ID, "com.dolphin.atc:id/history_title")

    # --- 空状态 ---
    EMPTY_STATE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("暂无")')

    # --- 底部Tab栏 ---
    TAB_HOME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("首页")')
    TAB_FLIGHT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("申报")')
    TAB_NEWS = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("资讯")')
    TAB_MINE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的")')

    # --- 备用resource-id定位 ---
    ALT_AI_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_chat_input")
    ALT_AI_SEND = (AppiumBy.ID, "com.dolphin.atc:id/btn_send")
    ALT_NOTIFY_LIST = (AppiumBy.ID, "com.dolphin.atc:id/recycler_view")
    ALT_BACK_HOME = (AppiumBy.ID, "com.dolphin.atc:id/btn_back_home")
    ALT_HISTORY_BTN = (AppiumBy.ID, "com.dolphin.atc:id/btn_history")

    # ============================================================
    # 页面操作方法 - 通知列表
    # ============================================================

    def is_on_home_page(self) -> bool:
        """判断当前是否在首页"""
        return (
            self.is_element_present(self.PAGE_TITLE, timeout=5)
            or self.is_element_present(self.TAB_BAR_HOME, timeout=5)
            or self.is_element_present(self.NOTIFY_TAB_APPROVAL, timeout=3)
        )

    def wait_for_home_page(self, timeout: int = 30):
        """等待首页加载完成"""
        logger.info("等待首页加载...")
        self.wait_for_element_visible(self.PAGE_TITLE, timeout)
        return self

    def switch_notify_tab(self, tab: str):
        """
        切换通知Tab

        Args:
            tab: 通知Tab名称
                 - "审批" / "approval": 计划审批
                 - "告警" / "alert": 告警通知
                 - "协调" / "coord": 管制员通知

        Returns:
            self
        """
        tab_map = {
            "审批": self.NOTIFY_TAB_APPROVAL,
            "approval": self.NOTIFY_TAB_APPROVAL,
            "告警": self.NOTIFY_TAB_ALERT,
            "alert": self.NOTIFY_TAB_ALERT,
            "协调": self.NOTIFY_TAB_COORD,
            "coord": self.NOTIFY_TAB_COORD,
        }

        locator = tab_map.get(tab)
        if locator is None:
            raise ValueError(f"未知的通知Tab: '{tab}'，可选: 审批/告警/协调")

        logger.info(f"切换到通知Tab: {tab}")
        self.click(locator)
        return self

    def get_notification_count(self) -> int:
        """
        获取当前通知列表中的通知数量

        Returns:
            int: 通知卡片数量
        """
        cards = self.find_elements(self.NOTIFY_CARD)
        return len(cards)

    def get_notification_list(self) -> List[dict]:
        """
        获取通知列表内容

        Returns:
            list[dict]: 每项包含 title(标题), time(时间)
        """
        notifications = []
        cards = self.find_elements(self.NOTIFY_CARD)
        for card in cards:
            try:
                title = card.find_element(*self.NOTIFY_CARD_TITLE).text
                time_text = card.find_element(*self.NOTIFY_CARD_TIME).text
                notifications.append({"title": title, "time": time_text})
            except Exception:
                continue
        logger.info(f"获取到 {len(notifications)} 条通知")
        return notifications

    def click_first_notification(self):
        """
        点击第一条通知

        Returns:
            self: 页面可能跳转到详情页
        """
        logger.info("点击第一条通知")
        cards = self.find_elements(self.NOTIFY_CARD)
        if cards:
            cards[0].click()
        else:
            raise ValueError("通知列表为空，无法点击")
        return self

    def is_notification_list_empty(self) -> bool:
        """判断通知列表是否为空"""
        return self.is_element_present(self.EMPTY_STATE, timeout=3)

    # --- 告警子筛选 ---

    def filter_unread_alerts(self):
        """筛选未读告警"""
        logger.info("筛选未读告警")
        self.click(self.ALERT_FILTER_UNREAD)
        return self

    def filter_read_alerts(self):
        """筛选已读告警"""
        logger.info("筛选已读告警")
        self.click(self.ALERT_FILTER_READ)
        return self

    # --- 管制员通知操作 ---

    def acknowledge_coordination(self):
        """
        点击管制员通知的"已知晓"按钮

        Returns:
            self
        """
        logger.info("点击'已知晓'")
        self.click(self.COORD_ACK_BUTTON)
        return self

    def mark_coordination_done(self):
        """
        点击管制员通知的"已处理"按钮

        Returns:
            self
        """
        logger.info("点击'已处理'")
        self.click(self.COORD_DONE_BUTTON)
        return self

    # ============================================================
    # 页面操作方法 - AI智能问答
    # ============================================================

    def enter_chat_mode(self):
        """
        进入对话态 (点击底部输入框)

        Returns:
            self
        """
        logger.info("进入AI对话模式")
        locator = self.ALT_AI_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.AI_INPUT_FIELD
        self.click(locator)
        # 等待对话界面加载
        self.wait_for_element_visible(self.AI_CHAT_AREA, timeout=10)
        return self

    def input_ai_question(self, question: str):
        """
        在AI输入框中输入问题

        Args:
            question: 问题文本

        Returns:
            self
        """
        logger.info(f"AI提问: {question[:30]}...")
        locator = self.ALT_AI_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.AI_INPUT_FIELD
        self.input_text(locator, question)
        return self

    def click_send_question(self):
        """
        点击发送按钮提交AI问题

        Returns:
            self
        """
        logger.info("点击发送AI问题")
        locator = self.ALT_AI_SEND
        if not self.is_element_present(locator, timeout=2):
            locator = self.AI_SEND_BUTTON
        self.click(locator)
        # 等待AI回复
        self.wait_seconds(2)
        return self

    def ask_question(self, question: str):
        """
        完整的AI提问流程 (组合操作)

        Args:
            question: 问题文本

        Returns:
            self
        """
        self.input_ai_question(question).click_send_question()
        return self

    def back_to_home_from_chat(self):
        """
        从对话态返回默认态

        点击"返回首页"按钮。

        Returns:
            self
        """
        logger.info("返回首页(退出对话态)")
        locator = self.ALT_BACK_HOME
        if not self.is_element_present(locator, timeout=2):
            locator = self.AI_BACK_HOME_BUTTON
        self.click(locator)
        # 等待通知列表重新出现
        self.wait_for_element_visible(self.NOTIFICATION_LIST, timeout=10)
        return self

    def open_chat_history(self):
        """
        打开对话历史列表

        Returns:
            self
        """
        logger.info("打开对话历史")
        locator = self.ALT_HISTORY_BTN
        if not self.is_element_present(locator, timeout=2):
            locator = self.AI_HISTORY_BUTTON
        self.click(locator)
        self.wait_for_element_visible(self.HISTORY_LIST, timeout=10)
        return self

    def get_chat_history_count(self) -> int:
        """
        获取对话历史数量

        Returns:
            int
        """
        items = self.find_elements(self.HISTORY_ITEM_TITLE)
        return len(items)

    def get_ai_response_text(self, timeout: int = 15) -> str:
        """
        获取AI最新回复的文本

        Args:
            timeout: 等待AI回复的最大时间

        Returns:
            str: AI回复文本
        """
        # 等待最后一条消息气泡出现
        bubbles = self.find_elements(self.AI_MESSAGE_BUBBLE)
        if bubbles:
            return bubbles[-1].text
        return ""

    def is_chat_mode_active(self) -> bool:
        """判断当前是否处于对话态"""
        return self.is_element_present(
            self.AI_BACK_HOME_BUTTON, timeout=3
        ) or self.is_element_present(self.ALT_BACK_HOME, timeout=3)

    # ============================================================
    # 底部Tab导航
    # ============================================================

    def go_to_flight(self):
        """跳转到申报Tab"""
        logger.info("跳转到申报Tab")
        self.click(self.TAB_FLIGHT)
        from pages.flight_page import FlightPage
        return FlightPage(self.driver)

    def go_to_news(self):
        """跳转到资讯Tab"""
        logger.info("跳转到资讯Tab")
        self.click(self.TAB_NEWS)
        from pages.news_page import NewsPage
        return NewsPage(self.driver)

    def go_to_mine(self):
        """跳转到我的Tab"""
        logger.info("跳转到我的Tab")
        self.click(self.TAB_MINE)
        from pages.mine_page import MinePage
        return MinePage(self.driver)
