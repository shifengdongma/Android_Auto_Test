# -*- coding: utf-8 -*-
"""
告警详情页面 (AlertDetailPage)

页面路径: 首页 → 告警通知列表 → 点击告警卡片 → 告警详情
页面功能:
    - 告警基本信息展示 (告警ID/类别/时间/级别/状态)
    - 告警对象信息展示 (识别码/类型/计划名称/运营人/位置)
    - 协调反馈时间线
    - 底部操作: 签收 / 忽略

对应原型: pages/小程序_告警详情.html
"""

import logging
from typing import Dict, List, Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class AlertDetailPage(BasePage):
    """
    告警详情页面对象

    封装告警详情的元素定位和操作方法。
    """

    # ============================================================
    # 元素定位器 - Native (resource-id, 待APK校准)
    # ============================================================

    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("告警详情")')
    BACK_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("返回")')

    # 基本信息区域
    ALERT_ID = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("AL_")')
    ALERT_CATEGORY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("告警类别")')
    ALERT_TIME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("发生时间")')
    ALERT_LEVEL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("告警级别")')
    ALERT_STATUS = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("处理状态")')
    ALERT_BASIS = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("告警依据")')

    # 告警对象
    OBJECT_CARD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.view.View").descriptionContains("巡检")')

    # 协调反馈时间线
    TIMELINE = (AppiumBy.CLASS_NAME, "android.widget.ListView")
    TIMELINE_ITEM = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("管制员")')

    # 操作按钮
    BTN_IGNORE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("忽略")')
    BTN_SIGN = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("签收")')

    # ============================================================
    # 元素定位器 - Browser模式 (CSS Selectors)
    # ============================================================

    ALT_PAGE_TITLE = (AppiumBy.CSS_SELECTOR, ".page-header .title")
    ALT_BACK_BUTTON = (AppiumBy.CSS_SELECTOR, ".page-header .back")

    # 基本信息区域
    ALT_SECTION_TITLE = (AppiumBy.CSS_SELECTOR, ".section-title")
    ALT_INFO_ROWS = (AppiumBy.CSS_SELECTOR, ".info-row")
    ALT_INFO_KEY = (AppiumBy.CSS_SELECTOR, ".info-row .k")
    ALT_INFO_VALUE = (AppiumBy.CSS_SELECTOR, ".info-row .v")

    # 标签
    ALT_TAG_RED = (AppiumBy.CSS_SELECTOR, ".tag-red")
    ALT_TAG_MUTED = (AppiumBy.CSS_SELECTOR, ".tag-muted")

    # 告警对象卡片
    ALT_OBJECT_CARDS = (AppiumBy.CSS_SELECTOR, ".obj-card")
    ALT_OBJECT_NAME = (AppiumBy.CSS_SELECTOR, ".obj-card .obj-name")
    ALT_OBJECT_GRID_ITEMS = (AppiumBy.CSS_SELECTOR, ".obj-grid .og-item")

    # 协调反馈时间线
    ALT_TIMELINE = (AppiumBy.CSS_SELECTOR, ".timeline")
    ALT_TIMELINE_ITEMS = (AppiumBy.CSS_SELECTOR, ".tl-item")
    ALT_TIMELINE_TIME = (AppiumBy.CSS_SELECTOR, ".tl-item .tl-time")
    ALT_TIMELINE_CONTENT = (AppiumBy.CSS_SELECTOR, ".tl-item .tl-content")

    # 操作按钮
    ALT_BTN_IGNORE = (AppiumBy.CSS_SELECTOR, ".action-bar .btn-ignore")
    ALT_BTN_SIGN = (AppiumBy.CSS_SELECTOR, ".tl-tag")

    # ============================================================
    # 页面状态判断
    # ============================================================

    def is_on_alert_detail_page(self, timeout: int = 10) -> bool:
        """
        判断是否在告警详情页面

        Returns:
            bool: 是否在告警详情页
        """
        return (
            self.is_element_present(self.ALT_PAGE_TITLE, timeout) or
            self.is_element_present(self.PAGE_TITLE, timeout)
        )

    def wait_for_alert_detail_page(self, timeout: int = 15):
        """
        等待告警详情页面加载完成

        Returns:
            self
        """
        self.wait_for_element_visible(self.ALT_PAGE_TITLE, timeout)
        logger.info("告警详情页面已加载")
        return self

    # ============================================================
    # 信息获取
    # ============================================================

    def get_alert_basic_info(self) -> Dict[str, str]:
        """
        获取告警基本信息

        遍历 .info-row 元素，提取所有的 key-value 对。

        Returns:
            dict: 告警基本信息字典，包含告警ID/类别/时间/级别/状态/依据等
        """
        info = {}

        try:
            rows = self.find_elements(self.ALT_INFO_ROWS, timeout=5)
            for row in rows:
                try:
                    key_el = row.find_element(*self.ALT_INFO_KEY) if hasattr(row, 'find_element') else None
                    val_el = row.find_element(*self.ALT_INFO_VALUE) if hasattr(row, 'find_element') else None
                    if key_el and val_el:
                        key = key_el.text.strip()
                        val = val_el.text.strip()
                        if key:
                            info[key] = val
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"获取告警基本信息失败: {e}")

        return info

    def get_alert_category(self) -> str:
        """获取告警类别"""
        text = self.get_text(self.ALT_INFO_ROWS, timeout=5)
        return text

    def get_alert_level(self) -> str:
        """获取告警级别 (重要/紧急/一般)"""
        try:
            tag = self.find_element(self.ALT_TAG_RED, timeout=3)
            return tag.text.strip()
        except Exception:
            try:
                tag = self.find_element(self.ALT_TAG_MUTED, timeout=3)
                return tag.text.strip()
            except Exception:
                return ""

    def get_alert_status(self) -> str:
        """获取告警处理状态 (已关闭/部分签收/待处理)"""
        try:
            tags = self.find_elements(self.ALT_TAG_MUTED, timeout=3)
            for tag in tags:
                text = tag.text.strip()
                if text in ("已关闭", "部分签收", "待处理", "已签收"):
                    return text
        except Exception:
            pass
        return ""

    def get_alert_objects(self) -> List[Dict[str, str]]:
        """
        获取告警对象列表

        Returns:
            list[dict]: 每个对象的属性字典
        """
        objects = []

        try:
            cards = self.find_elements(self.ALT_OBJECT_CARDS, timeout=5)
            for card in cards:
                obj_info = {}
                try:
                    name_el = card.find_element(*self.ALT_OBJECT_NAME) if hasattr(card, 'find_element') else None
                    if name_el:
                        obj_info["name"] = name_el.text.strip()
                except Exception:
                    pass

                try:
                    grid_items = card.find_elements(*self.ALT_OBJECT_GRID_ITEMS) if hasattr(card, 'find_elements') else []
                    for item in grid_items:
                        try:
                            k = item.find_element(By.CSS_SELECTOR, ".k") if hasattr(item, 'find_element') else None
                            v = item.find_element(By.CSS_SELECTOR, ".v") if hasattr(item, 'find_element') else None
                            if k and v:
                                obj_info[k.text.strip()] = v.text.strip()
                        except Exception:
                            continue
                except Exception:
                    pass

                if obj_info:
                    objects.append(obj_info)
        except Exception as e:
            logger.warning(f"获取告警对象信息失败: {e}")

        return objects

    def get_coordination_timeline(self) -> List[Dict[str, str]]:
        """
        获取协调反馈时间线

        Returns:
            list[dict]: 每条时间线条目 {time, role, tag, message}
        """
        timeline = []

        try:
            items = self.find_elements(self.ALT_TIMELINE_ITEMS, timeout=5)
            for item in items:
                entry = {}
                try:
                    time_el = item.find_element(*self.ALT_TIMELINE_TIME) if hasattr(item, 'find_element') else None
                    if time_el:
                        entry["time"] = time_el.text.strip()
                except Exception:
                    pass
                try:
                    content = item.find_element(*self.ALT_TIMELINE_CONTENT) if hasattr(item, 'find_element') else None
                    if content:
                        entry["content"] = content.text.strip()
                except Exception:
                    pass
                if entry:
                    timeline.append(entry)
        except Exception as e:
            logger.warning(f"获取协调反馈失败: {e}")

        return timeline

    # ============================================================
    # 操作
    # ============================================================

    def click_sign(self):
        """
        点击签收按钮

        Returns:
            self
        """
        try:
            # 优先使用 CSS selector
            sign_btns = self.find_elements(self.ALT_BTN_SIGN, timeout=3)
            for btn in sign_btns:
                if btn.text.strip() == "签收":
                    btn.click()
                    logger.info("已签收告警")
                    return self
        except Exception:
            pass

        # 回退到 UiAutomator
        try:
            self.click(self.BTN_SIGN)
            logger.info("已签收告警")
        except Exception as e:
            logger.error(f"签收操作失败: {e}")
            raise

        return self

    def click_ignore(self):
        """
        点击忽略按钮

        Returns:
            self
        """
        try:
            self.click(self.ALT_BTN_IGNORE)
            logger.info("已忽略告警")
        except Exception:
            try:
                self.click(self.BTN_IGNORE)
                logger.info("已忽略告警")
            except Exception as e:
                logger.error(f"忽略操作失败: {e}")
                raise
        return self

    def verify_alert_status(self, expected_status: str) -> bool:
        """
        验证告警处理状态

        Args:
            expected_status: 期望的状态文本 (如 "已关闭", "部分签收")

        Returns:
            bool: 状态是否匹配
        """
        actual = self.get_alert_status()
        match = expected_status in actual
        if match:
            logger.info(f"告警状态验证通过: {actual}")
        else:
            logger.warning(f"告警状态不匹配: 期望={expected_status}, 实际={actual}")
        return match

    # ============================================================
    # 导航
    # ============================================================

    def go_back_to_home(self):
        """
        返回到首页

        Returns:
            HomePage
        """
        from pages.home_page import HomePage
        try:
            self.click(self.ALT_BACK_BUTTON)
        except Exception:
            self.click(self.BACK_BUTTON)
        logger.info("从告警详情返回首页")
        return HomePage(self.driver)


# 解决循环导入的延迟导入
from selenium.webdriver.common.by import By
