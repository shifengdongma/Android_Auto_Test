# -*- coding: utf-8 -*-
"""
我的页面 (MinePage)

页面路径: 底部Tab "我的"
页面功能:
    - 个人信息展示 (头像/姓名/公司)
    - 信誉积分统计 (积分/等级)
    - 信誉明细查看
    - 关于我们
    - 退出登录

对应原型: pages/小程序_我的.html
"""

import logging
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class MinePage(BasePage):
    """
    我的Page Object

    封装个人中心的所有操作。
    """

    # ============================================================
    # 元素定位器
    # ============================================================

    # --- 页面标识 ---
    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的")')

    # --- 个人信息 ---
    AVATAR = (AppiumBy.ID, "com.dolphin.atc:id/iv_avatar")
    USER_NAME = (AppiumBy.ID, "com.dolphin.atc:id/tv_username")
    COMPANY_NAME = (AppiumBy.ID, "com.dolphin.atc:id/tv_company")

    # --- 信誉积分 ---
    CREDIT_SCORE_CARD = (AppiumBy.ID, "com.dolphin.atc:id/credit_score_card")
    CREDIT_SCORE_VALUE = (AppiumBy.ID, "com.dolphin.atc:id/tv_score")
    CREDIT_SCORE_LABEL = (AppiumBy.ID, "com.dolphin.atc:id/tv_score_label")
    CREDIT_LEVEL = (AppiumBy.ID, "com.dolphin.atc:id/tv_level")

    # --- 菜单项 ---
    MENU_ABOUT_US = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("关于我们")')
    MENU_LOGOUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("退出登录")')
    MENU_ITEM = (AppiumBy.ID, "com.dolphin.atc:id/menu_item")

    # --- 关于我们 ---
    ABOUT_TITLE = (AppiumBy.ID, "com.dolphin.atc:id/about_title")
    ABOUT_COMPANY_NAME = (AppiumBy.ID, "com.dolphin.atc:id/about_company")
    ABOUT_CONTACT = (AppiumBy.ID, "com.dolphin.atc:id/about_contact")
    ABOUT_VERSION = (AppiumBy.ID, "com.dolphin.atc:id/about_version")
    ABOUT_BACK = (AppiumBy.ACCESSIBILITY_ID, "返回")

    # --- 退出登录确认 ---
    LOGOUT_CONFIRM_DIALOG = (AppiumBy.ID, "android:id/parentPanel")
    LOGOUT_CONFIRM_YES = (AppiumBy.ID, "android:id/button1")
    LOGOUT_CONFIRM_NO = (AppiumBy.ID, "android:id/button2")

    # --- 底部Tab ---
    TAB_HOME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("首页")')
    TAB_FLIGHT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("申报")')
    TAB_NEWS = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("资讯")')

    # --- 备用定位 ---
    ALT_SCORE_CARD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("信誉")')
    ALT_LOGOUT = (AppiumBy.ID, "com.dolphin.atc:id/btn_logout")
    ALT_ABOUT = (AppiumBy.ID, "com.dolphin.atc:id/menu_about")

    # ============================================================
    # 页面状态
    # ============================================================

    def is_on_mine_page(self) -> bool:
        """判断当前是否在我的页面"""
        return (
            self.is_element_present(self.PAGE_TITLE, timeout=5)
            or self.is_element_present(self.CREDIT_SCORE_CARD, timeout=3)
        )

    def wait_for_mine_page(self, timeout: int = 20):
        """等待我的页面加载完成"""
        logger.info("等待'我的'页面加载...")
        self.wait_for_element_visible(self.PAGE_TITLE, timeout)
        return self

    # ============================================================
    # 个人信息
    # ============================================================

    def get_user_name(self) -> str:
        """
        获取用户名

        Returns:
            str: 用户名称
        """
        return self.get_text(self.USER_NAME)

    def get_company_name(self) -> str:
        """
        获取公司名称

        Returns:
            str: 公司名称
        """
        return self.get_text(self.COMPANY_NAME)

    def click_avatar(self):
        """点击头像"""
        logger.info("点击头像")
        self.click(self.AVATAR)
        return self

    # ============================================================
    # 信誉积分
    # ============================================================

    def get_credit_score(self) -> int:
        """
        获取信誉积分

        Returns:
            int: 信誉分数 (解析失败返回-1)
        """
        score_text = self.get_text(self.CREDIT_SCORE_VALUE)
        try:
            return int(score_text)
        except (ValueError, TypeError):
            logger.warning(f"无法解析信誉分: '{score_text}'")
            return -1

    def get_credit_level(self) -> str:
        """
        获取信誉等级

        Returns:
            str: 等级 (优秀/良好/告警/限制)
        """
        return self.get_text(self.CREDIT_LEVEL)

    def get_credit_label(self) -> str:
        """
        获取信誉积分标签

        Returns:
            str: 如 "信誉积分"
        """
        return self.get_text(self.CREDIT_SCORE_LABEL)

    def click_credit_score_card(self):
        """
        点击信誉积分卡片 → 进入信誉明细

        Returns:
            self
        """
        logger.info("点击信誉积分卡片")
        locator = self.ALT_SCORE_CARD
        if not self.is_element_present(locator, timeout=2):
            locator = self.CREDIT_SCORE_CARD
        self.click(locator)
        return self

    def verify_score_range(self, expected_min: int, expected_max: int) -> bool:
        """
        验证信誉分是否在预期范围内

        Args:
            expected_min: 最小期望值
            expected_max: 最大期望值

        Returns:
            bool
        """
        score = self.get_credit_score()
        return expected_min <= score <= expected_max

    def verify_score_level(self, score: Optional[int] = None) -> str:
        """
        根据积分判断等级

        积分规则:
            - 800+ : 优秀
            - 600-799: 良好
            - 400-599: 告警
            - <400: 限制

        Args:
            score: 积分，不传则从页面获取

        Returns:
            str: 等级名称
        """
        if score is None:
            score = self.get_credit_score()

        if score >= 800:
            expected = "优秀"
        elif score >= 600:
            expected = "良好"
        elif score >= 400:
            expected = "告警"
        else:
            expected = "限制"

        actual = self.get_credit_level()
        if actual != expected:
            logger.warning(f"信誉等级不匹配: 期望={expected}, 实际={actual}")
        return actual

    # ============================================================
    # 关于我们
    # ============================================================

    def click_about_us(self):
        """
        点击"关于我们"菜单

        Returns:
            self
        """
        logger.info("点击'关于我们'")
        locator = self.ALT_ABOUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.MENU_ABOUT_US
        self.click(locator)

        # 等待关于我们页面加载
        self.wait_for_element_visible(self.ABOUT_TITLE, timeout=10)
        return self

    def get_about_company_name(self) -> str:
        """获取关于我们-公司名称"""
        return self.get_text(self.ABOUT_COMPANY_NAME)

    def get_about_contact(self) -> str:
        """获取关于我们-联系方式"""
        return self.get_text(self.ABOUT_CONTACT)

    def get_about_version(self) -> str:
        """获取关于我们-版本信息"""
        return self.get_text(self.ABOUT_VERSION)

    def is_about_page_shown(self) -> bool:
        """判断是否显示关于我们页面"""
        return self.is_element_present(self.ABOUT_TITLE, timeout=3)

    def close_about_page(self):
        """关闭关于我们页面 (点击返回)"""
        logger.info("关闭关于我们页面")
        self.click(self.ABOUT_BACK)
        self.wait_for_element_visible(self.PAGE_TITLE, timeout=10)
        return self

    # ============================================================
    # 退出登录
    # ============================================================

    def click_logout(self, confirm: bool = True):
        """
        点击"退出登录"并处理确认弹窗

        Args:
            confirm: True=确认退出, False=取消退出

        Returns:
            LoginPage: 确认退出后跳转到登录页
            MinePage: 取消退出则停留在当前页
        """
        logger.info(f"点击'退出登录' (确认={confirm})")

        locator = self.ALT_LOGOUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.MENU_LOGOUT
        self.click(locator)

        # 等待确认弹窗
        self.wait_seconds(0.5)

        if self.is_element_present(self.LOGOUT_CONFIRM_DIALOG, timeout=3):
            if confirm:
                self.click(self.LOGOUT_CONFIRM_YES)
                logger.info("已确认退出登录")
                from pages.login_page import LoginPage
                return LoginPage(self.driver)
            else:
                self.click(self.LOGOUT_CONFIRM_NO)
                logger.info("已取消退出登录")
                return self

        # 没有弹窗则直接退出
        if confirm:
            from pages.login_page import LoginPage
            return LoginPage(self.driver)
        return self

    def is_logged_out(self) -> bool:
        """
        判断是否已退出登录 (是否已返回登录页)

        Returns:
            bool
        """
        from pages.login_page import LoginPage
        login_page = LoginPage(self.driver)
        return login_page.is_on_login_page()

    # ============================================================
    # 菜单项通用操作
    # ============================================================

    def get_menu_items(self) -> list:
        """
        获取我的页面的所有菜单项文本

        Returns:
            list[str]: 菜单项文本列表
        """
        items = self.find_elements(self.MENU_ITEM)
        return [item.text for item in items]

    def click_menu_by_text(self, text: str):
        """
        通过文本点击任意菜单项

        Args:
            text: 菜单文本

        Returns:
            self
        """
        logger.info(f"点击菜单: {text}")
        self.find_element_by_text(text).click()
        return self

    # ============================================================
    # 底部Tab导航
    # ============================================================

    def go_to_home(self):
        """跳转到首页"""
        logger.info("跳转到首页")
        self.click(self.TAB_HOME)
        from pages.home_page import HomePage
        return HomePage(self.driver)

    def go_to_flight(self):
        """跳转到申报"""
        logger.info("跳转到申报")
        self.click(self.TAB_FLIGHT)
        from pages.flight_page import FlightPage
        return FlightPage(self.driver)

    def go_to_news(self):
        """跳转到资讯"""
        logger.info("跳转到资讯")
        self.click(self.TAB_NEWS)
        from pages.news_page import NewsPage
        return NewsPage(self.driver)
