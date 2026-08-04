# -*- coding: utf-8 -*-
"""
资讯页 (NewsPage)

页面路径: 底部Tab "资讯"
页面功能:
    - 子Tab切换: 法律法规 / 通知公告 / 系统公告
    - 文章列表展示
    - 文章详情查看
    - 附件下载

对应原型: pages/小程序_查询.html
"""

import logging
from typing import Dict, List, Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class NewsPage(BasePage):
    """
    资讯Page Object

    封装法律法规、通知公告、系统公告的浏览操作。
    """

    # ============================================================
    # 元素定位器
    # ============================================================

    # --- 页面标识 ---
    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("资讯")')

    # --- 子Tab ---
    TAB_LAWS = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("法律法规")')
    TAB_NOTICES = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("通知公告")')
    TAB_SYSTEM = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("系统公告")')

    # --- 文章列表 ---
    ARTICLE_LIST = (AppiumBy.ID, "com.dolphin.atc:id/rv_articles")
    ARTICLE_CARD = (AppiumBy.ID, "com.dolphin.atc:id/article_card")
    ARTICLE_TITLE = (AppiumBy.ID, "com.dolphin.atc:id/article_title")
    ARTICLE_SOURCE = (AppiumBy.ID, "com.dolphin.atc:id/article_source")
    ARTICLE_DATE = (AppiumBy.ID, "com.dolphin.atc:id/article_date")
    ARTICLE_TAG = (AppiumBy.ID, "com.dolphin.atc:id/article_tag")

    # --- 文章详情 ---
    DETAIL_TITLE = (AppiumBy.ID, "com.dolphin.atc:id/detail_title")
    DETAIL_META = (AppiumBy.ID, "com.dolphin.atc:id/detail_meta")
    DETAIL_CONTENT = (AppiumBy.ID, "com.dolphin.atc:id/detail_content")
    DETAIL_BACK = (AppiumBy.ACCESSIBILITY_ID, "返回")
    DETAIL_ATTACHMENT = (AppiumBy.ID, "com.dolphin.atc:id/detail_attachment")
    DETAIL_SHARE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("分享")')

    # --- 空状态 ---
    EMPTY_STATE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("暂无")')

    # --- 底部Tab ---
    TAB_HOME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("首页")')
    TAB_FLIGHT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("申报")')
    TAB_MINE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的")')

    # ============================================================
    # 页面状态
    # ============================================================

    def is_on_news_page(self) -> bool:
        """判断当前是否在资讯页"""
        return (
            self.is_element_present(self.PAGE_TITLE, timeout=5)
            or self.is_element_present(self.TAB_LAWS, timeout=3)
        )

    def wait_for_news_page(self, timeout: int = 20):
        """等待资讯页加载完成"""
        logger.info("等待资讯页加载...")
        self.wait_for_element_visible(self.PAGE_TITLE, timeout)
        return self

    # ============================================================
    # Tab切换
    # ============================================================

    def switch_tab(self, tab: str):
        """
        切换资讯子Tab

        Args:
            tab: Tab名称
                - "法律法规" / "laws"
                - "通知公告" / "notices"
                - "系统公告" / "system"

        Returns:
            self
        """
        tab_map = {
            "法律法规": self.TAB_LAWS,
            "laws": self.TAB_LAWS,
            "通知公告": self.TAB_NOTICES,
            "notices": self.TAB_NOTICES,
            "系统公告": self.TAB_SYSTEM,
            "system": self.TAB_SYSTEM,
        }

        locator = tab_map.get(tab)
        if locator is None:
            raise ValueError(
                f"未知的资讯Tab: '{tab}'，可选: 法律法规/通知公告/系统公告"
            )

        logger.info(f"切换到资讯Tab: {tab}")
        self.click(locator)
        # 等待列表刷新
        self.wait_for_element_visible(self.ARTICLE_LIST, timeout=10)
        return self

    # ============================================================
    # 文章列表
    # ============================================================

    def get_article_count(self) -> int:
        """
        获取当前Tab下的文章数量

        Returns:
            int
        """
        return len(self.find_elements(self.ARTICLE_CARD))

    def get_article_list(self) -> List[Dict[str, str]]:
        """
        获取文章列表内容

        Returns:
            list[dict]: 每项包含:
                - title: 标题
                - source: 发布单位
                - date: 发布时间
                - tag: 标签 (如有)
        """
        articles = []
        cards = self.find_elements(self.ARTICLE_CARD)
        for card in cards:
            try:
                article = {
                    "title": card.find_element(*self.ARTICLE_TITLE).text,
                    "source": card.find_element(*self.ARTICLE_SOURCE).text,
                    "date": card.find_element(*self.ARTICLE_DATE).text,
                }
                # tag可能不存在
                try:
                    article["tag"] = card.find_element(*self.ARTICLE_TAG).text
                except Exception:
                    article["tag"] = ""
                articles.append(article)
            except Exception:
                continue

        logger.info(f"获取到 {len(articles)} 篇文章")
        return articles

    def click_article(self, index: int = 0):
        """
        点击文章进入详情

        Args:
            index: 文章索引 (0=第一篇)

        Returns:
            self
        """
        logger.info(f"点击第{index}篇文章")
        cards = self.find_elements(self.ARTICLE_CARD)
        if index >= len(cards):
            raise IndexError(f"文章索引 {index} 超出范围 (共{len(cards)}篇)")
        cards[index].click()

        # 等待详情页加载
        self.wait_for_element_visible(self.DETAIL_TITLE, timeout=10)
        return self

    def is_article_list_empty(self) -> bool:
        """判断文章列表是否为空"""
        return self.is_element_present(self.EMPTY_STATE, timeout=3)

    # ============================================================
    # 文章详情
    # ============================================================

    def get_article_detail_title(self) -> str:
        """获取文章详情标题"""
        return self.get_text(self.DETAIL_TITLE)

    def get_article_detail_content(self) -> str:
        """获取文章正文内容"""
        return self.get_text(self.DETAIL_CONTENT)

    def get_article_detail_meta(self) -> str:
        """
        获取文章元信息

        通常包含: 通知类型、发布单位、发布时间等
        """
        return self.get_text(self.DETAIL_META)

    def is_attachment_available(self) -> bool:
        """判断文章是否有附件"""
        return self.is_element_present(self.DETAIL_ATTACHMENT, timeout=3)

    def click_attachment(self):
        """
        点击附件下载/查看

        Returns:
            self
        """
        logger.info("点击附件")
        self.click(self.DETAIL_ATTACHMENT)
        return self

    def click_share(self):
        """点击分享按钮"""
        logger.info("点击分享")
        self.click(self.DETAIL_SHARE)
        return self

    def back_to_list(self):
        """从详情页返回文章列表"""
        logger.info("返回文章列表")
        self.click(self.DETAIL_BACK)
        self.wait_for_element_visible(self.ARTICLE_LIST, timeout=10)
        return self

    def is_detail_page_shown(self) -> bool:
        """判断是否显示文章详情页"""
        return self.is_element_present(self.DETAIL_TITLE, timeout=3)

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

    def go_to_mine(self):
        """跳转到我的"""
        logger.info("跳转到我的")
        self.click(self.TAB_MINE)
        from pages.mine_page import MinePage
        return MinePage(self.driver)
