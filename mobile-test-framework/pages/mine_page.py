# -*- coding: utf-8 -*-
"""
我的 (MinePage)

页面功能 (真机实测):
    - 用户信息 (昵称/公司/信誉分)
    - 功能入口: 信誉明细 / 关于我们
    - 退出登录 (退出后回登录页)

交互方式: uni-app WebView内容, 经 utils.webview_a11y 定位。
"""

import logging
import time

from pages.base_page import BasePage
from utils import webview_a11y

logger = logging.getLogger(__name__)


class MinePage(BasePage):
    """我的Page Object"""

    ENTRY_CREDIT_DETAIL = "信誉明细"
    ENTRY_ABOUT_US = "关于我们"
    ENTRY_LOGOUT = "退出登录"

    LOGOUT_CONFIRM = "确定"

    def wait_for_mine_page(self, timeout: int = 20):
        """等待我的页面加载"""
        logger.info("等待我的页面加载...")
        assert webview_a11y.find_text(
            self.driver, self.ENTRY_LOGOUT, timeout=timeout
        ) is not None, "我的页面未加载: 未发现'退出登录'入口"
        return self

    def open_entry(self, entry_text: str):
        """点击功能入口 (信誉明细/关于我们/退出登录)"""
        logger.info(f"点击入口: {entry_text}")
        el = webview_a11y.find_visible_by_text(
            self.driver, entry_text, timeout=8, min_y=300
        )
        assert el is not None, f"未找到入口: {entry_text}"
        el.click()
        time.sleep(2.5)
        return self

    def confirm_logout_if_needed(self):
        """
        退出登录如有确认弹窗则点击确定

        注意: 必须精确匹配"确定" (contains会误中弹窗消息"确定退出登录吗？")。
        """
        for attempt in range(3):
            confirm = webview_a11y.find_text(
                self.driver, self.LOGOUT_CONFIRM, timeout=3
            )
            if confirm is not None and confirm.location["y"] > 1000:
                logger.info("点击退出确定")
                confirm.click()
                time.sleep(2)
                return self
            # 预热: 点击弹窗区域触发a11y树构建
            self.driver.tap([(576, 1400)])
            time.sleep(2)
        logger.warning("未发现退出确认弹窗")
        return self

    def is_back_on_login_page(self) -> bool:
        """判断是否回到登录页 (登录按钮出现; 登录页a11y树可能延迟构建, 预热重试)"""
        el = webview_a11y.find_text(self.driver, "登录", timeout=10)
        if el is None:
            # 预热: 点击页面中部触发a11y树构建
            self.driver.tap([(576, 1300)])
            time.sleep(3)
            el = webview_a11y.find_text(self.driver, "登录", timeout=10)
        return el is not None

    def go_back(self):
        """返回上一页"""
        self.driver.back()
        time.sleep(2)
        return self
