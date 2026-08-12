# -*- coding: utf-8 -*-
"""
飞行计划详情页面 (PlanDetailPage)

页面路径: 首页审批通知 → 点击计划卡片 → 计划详情
         或 申报 → 我的计划 → 点击计划 → 计划详情
页面功能:
    - 计划状态横幅 (编号 + 状态标签)
    - 航路信息展示 (出发/到达)
    - 基础信息 (执飞时段/航空器/操控员/计划性质)
    - 更多信息折叠 (计划名称/观测员/计划类型)
    - 文件资料列表
    - 驳回原因展示 (驳回状态时)
    - 计划操作 (编辑/推延/取消/撤回)

对应原型: pages/小程序_计划详情.html, pages/小程序_计划详情_留空.html
"""

import logging
from typing import Dict, List, Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class PlanDetailPage(BasePage):
    """
    飞行计划详情页面对象

    封装计划详情的元素定位和操作方法。
    支持航线飞行和留空飞行两种模式。
    """

    # ============================================================
    # 元素定位器 - Native (resource-id, 待APK校准)
    # ============================================================

    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("计划详情")')
    BACK_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("返回")')

    # 状态横幅
    PLAN_NO = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("计划编号")')
    STATUS_TAG = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").instance(2)')

    # 航路
    ROUTE_DEPARTURE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("出发")')
    ROUTE_ARRIVAL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("到达")')

    # 驳回原因
    REJECT_BOX = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").instance(10)')

    # 更多折叠
    MORE_TOGGLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("更多")')

    # 操作按钮
    BTN_EDIT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("编辑")')
    BTN_DELAY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("推延")')
    BTN_CANCEL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("取消")')
    BTN_RECALL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("撤回")')

    # ============================================================
    # 元素定位器 - Browser模式 (CSS Selectors)
    # ============================================================

    ALT_PAGE_TITLE = (AppiumBy.CSS_SELECTOR, ".page-header .title")
    ALT_BACK_BUTTON = (AppiumBy.CSS_SELECTOR, ".page-header .back")

    # 状态横幅
    ALT_STATUS_BANNER = (AppiumBy.CSS_SELECTOR, ".status-banner")
    ALT_PLAN_NO = (AppiumBy.CSS_SELECTOR, ".status-banner .sb-no")
    ALT_STATUS_TAG = (AppiumBy.CSS_SELECTOR, ".status-tag")
    ALT_STATUS_PENDING = (AppiumBy.CSS_SELECTOR, ".status-pending")
    ALT_STATUS_REJECTED = (AppiumBy.CSS_SELECTOR, ".status-rejected")
    ALT_STATUS_DONE = (AppiumBy.CSS_SELECTOR, ".status-done")

    # 航路
    ALT_ROUTE_LINE = (AppiumBy.CSS_SELECTOR, ".route-line")
    ALT_ROUTE_DEPARTURE = (AppiumBy.CSS_SELECTOR, ".pt-label + .pt")
    ALT_ROUTE_POINTS = (AppiumBy.CSS_SELECTOR, ".rl-points .pt")
    ALT_ROUTE_LABELS = (AppiumBy.CSS_SELECTOR, ".rl-points .pt-label")
    ALT_ROUTE_META = (AppiumBy.CSS_SELECTOR, ".route-meta")
    ALT_CHIP = (AppiumBy.CSS_SELECTOR, ".route-meta .chip")

    # 基础信息
    ALT_SECTION = (AppiumBy.CSS_SELECTOR, ".section")
    ALT_SECTION_TITLE = (AppiumBy.CSS_SELECTOR, ".section-title")
    ALT_INFO_ROWS = (AppiumBy.CSS_SELECTOR, ".info-row")
    ALT_INFO_KEY = (AppiumBy.CSS_SELECTOR, ".info-row .k")
    ALT_INFO_VALUE = (AppiumBy.CSS_SELECTOR, ".info-row .v")

    # 文件资料
    ALT_FILE_ROWS = (AppiumBy.CSS_SELECTOR, ".file-row")
    ALT_FILE_NAME = (AppiumBy.CSS_SELECTOR, ".file-row .f-name")
    ALT_FILE_VIEW = (AppiumBy.CSS_SELECTOR, ".file-row .f-view")

    # 驳回原因
    ALT_REJECT_BOX = (AppiumBy.CSS_SELECTOR, ".reject-box")

    # 更多折叠
    ALT_MORE_TOGGLE = (AppiumBy.CSS_SELECTOR, ".more-toggle")
    ALT_MORE_BODY = (AppiumBy.CSS_SELECTOR, ".more-body")

    # 操作按钮 (在底部或更多区域)
    ALT_BTN_EDIT = (AppiumBy.CSS_SELECTOR, "a[href*='编辑']")
    ALT_BTN_DELAY = (AppiumBy.CSS_SELECTOR, ".action-btn.outline")
    ALT_BTN_CANCEL = (AppiumBy.CSS_SELECTOR, ".action-btn.warn")

    # 留空飞行特有元素
    ALT_LOITER_AREA = (AppiumBy.CSS_SELECTOR, ".area-info")
    ALT_LOITER_POLYGON = (AppiumBy.CSS_SELECTOR, ".polygon-preview")

    # ============================================================
    # 页面状态判断
    # ============================================================

    def is_on_plan_detail_page(self, timeout: int = 10) -> bool:
        """判断是否在计划详情页面"""
        return (
            self.is_element_present(self.ALT_PAGE_TITLE, timeout) or
            self.is_element_present(self.PAGE_TITLE, timeout)
        )

    def wait_for_plan_detail_page(self, timeout: int = 15):
        """等待计划详情页面加载完成"""
        self.wait_for_element_visible(self.ALT_PAGE_TITLE, timeout)
        logger.info("计划详情页面已加载")
        return self

    # ============================================================
    # 信息获取
    # ============================================================

    def get_plan_number(self) -> str:
        """获取计划编号"""
        try:
            el = self.find_element(self.ALT_PLAN_NO, timeout=5)
            text = el.text.strip()
            return text.replace("计划编号：", "").strip()
        except Exception:
            return ""

    def get_plan_status(self) -> str:
        """
        获取计划状态

        Returns:
            str: 审批中 / 审批通过 / 审批驳回 / 待飞行 / 执飞中 / 已完成 / 取消
        """
        try:
            tag = self.find_element(self.ALT_STATUS_TAG, timeout=5)
            return tag.text.strip()
        except Exception:
            return ""

    def get_status_css_class(self) -> str:
        """
        获取状态标签的CSS类 (用于判断状态类型)

        Returns:
            str: status-pending / status-rejected / status-done 等
        """
        try:
            tag = self.find_element(self.ALT_STATUS_TAG, timeout=5)
            classes = tag.get_attribute("class") or ""
            for cls in classes.split():
                if cls.startswith("status-"):
                    return cls
        except Exception:
            pass
        return ""

    def get_route_info(self) -> Dict[str, str]:
        """获取航路信息 (出发/到达)"""
        route = {"departure": "", "arrival": ""}
        try:
            points = self.find_elements(self.ALT_ROUTE_POINTS, timeout=5)
            labels = self.find_elements(self.ALT_ROUTE_LABELS, timeout=5)
            for i, label in enumerate(labels):
                label_text = label.text.strip()
                if "出发" in label_text and i < len(points):
                    route["departure"] = points[i].text.strip()
                elif "到达" in label_text and i < len(points):
                    route["arrival"] = points[i].text.strip()
        except Exception as e:
            logger.warning(f"获取航路信息失败: {e}")
        return route

    def get_basic_info(self) -> Dict[str, str]:
        """
        获取基础信息区域的所有字段

        Returns:
            dict: {字段名: 字段值}
        """
        info = {}
        try:
            rows = self.find_elements(self.ALT_INFO_ROWS, timeout=5)
            for row in rows:
                try:
                    key_el = row.find_element(*(self.ALT_INFO_KEY))
                    val_el = row.find_element(*(self.ALT_INFO_VALUE))
                    key = key_el.text.strip()
                    val = val_el.text.strip()
                    if key:
                        info[key] = val
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"获取基础信息失败: {e}")
        return info

    def get_reject_reason(self) -> str:
        """
        获取驳回原因 (仅驳回状态时有效)

        Returns:
            str: 驳回原因文本
        """
        try:
            el = self.find_element(self.ALT_REJECT_BOX, timeout=3)
            return el.text.strip()
        except Exception:
            return ""

    def get_file_attachments(self) -> List[Dict[str, str]]:
        """
        获取文件资料列表

        Returns:
            list[dict]: [{name, view_link}]
        """
        files = []
        try:
            rows = self.find_elements(self.ALT_FILE_ROWS, timeout=5)
            for row in rows:
                try:
                    name_el = row.find_element(*(self.ALT_FILE_NAME))
                    files.append({"name": name_el.text.strip()})
                except Exception:
                    continue
        except Exception:
            pass
        return files

    def is_loiter_flight(self) -> bool:
        """
        判断是否为留空飞行计划

        Returns:
            bool: 是否为留空飞行
        """
        return (
            self.is_element_present(self.ALT_LOITER_AREA, timeout=2) or
            self.is_element_present(self.ALT_LOITER_POLYGON, timeout=2)
        )

    # ============================================================
    # 页面操作
    # ============================================================

    def toggle_more_info(self):
        """
        展开/折叠"更多"信息区域

        显示: 计划名称、观测员、计划类型

        Returns:
            self
        """
        try:
            self.click(self.ALT_MORE_TOGGLE, timeout=5)
            logger.info("已切换更多信息区域")
        except Exception as e:
            logger.warning(f"切换更多信息失败: {e}")
        return self

    def is_more_expanded(self) -> bool:
        """判断"更多"是否已展开"""
        try:
            el = self.find_element(self.ALT_MORE_BODY, timeout=3)
            classes = el.get_attribute("class") or ""
            return "open" in classes
        except Exception:
            return False

    def get_all_info(self) -> Dict:
        """
        获取计划详情全部信息 (含展开的隐藏字段)

        Returns:
            dict: 完整信息
        """
        info = {
            "plan_number": self.get_plan_number(),
            "status": self.get_plan_status(),
            "route": self.get_route_info(),
            "basic_info": self.get_basic_info(),
            "files": self.get_file_attachments(),
            "reject_reason": self.get_reject_reason(),
            "is_loiter": self.is_loiter_flight(),
        }

        # 展开更多信息
        if not self.is_more_expanded():
            self.toggle_more_info()
            self.wait_seconds(0.5)

        # 合并展开后的字段
        more_info = self.get_basic_info()
        if more_info:
            info["basic_info"].update(more_info)

        return info

    # ============================================================
    # 计划操作
    # ============================================================

    def click_edit(self):
        """
        点击编辑按钮

        适用于: 审批驳回状态、审批通过状态

        Returns:
            PlanEditPage
        """
        from pages.plan_edit_page import PlanEditPage
        try:
            self.click(self.ALT_BTN_EDIT)
        except Exception:
            self.click(self.BTN_EDIT)
        logger.info("进入计划编辑页面")
        return PlanEditPage(self.driver)

    def click_delay(self):
        """
        点击推延按钮

        适用于: 审批通过后、执飞前
        最多允许推延2次。

        Returns:
            self
        """
        try:
            self.click(self.ALT_BTN_DELAY)
        except Exception:
            try:
                self.click(self.BTN_DELAY)
            except Exception:
                # 可能需要在底部弹窗中操作
                pass
        logger.info("已点击推延按钮")
        return self

    def click_cancel(self):
        """
        点击取消按钮

        适用于: 审批中(撤回)、审批通过、待飞行、执飞中

        Returns:
            self
        """
        try:
            self.click(self.ALT_BTN_CANCEL)
        except Exception:
            self.click(self.BTN_CANCEL)
        logger.info("已点击取消按钮")
        return self

    def click_recall(self):
        """
        点击撤回按钮

        适用于: 审批中状态

        Returns:
            self
        """
        try:
            self.click(self.BTN_RECALL)
            logger.info("已撤回飞行计划")
        except Exception as e:
            logger.error(f"撤回操作失败: {e}")
            raise
        return self

    def verify_status_transition(
        self,
        from_status: str,
        after_action: str,
    ) -> bool:
        """
        验证状态流转

        执行操作后验证状态是否正确转换。

        Args:
            from_status: 操作前状态
            after_action: 执行的操作描述

        Returns:
            bool: 状态流转正确
        """
        # 等待页面刷新
        self.wait_seconds(1.0)

        new_status = self.get_plan_status()
        if not new_status:
            logger.warning("未能获取新状态")
            return False

        logger.info(f"状态流转: {from_status} → ({after_action}) → {new_status}")
        return new_status != from_status

    # ============================================================
    # 导航
    # ============================================================

    def go_back(self):
        """返回到上一页 (审批进度列表)"""
        try:
            self.click(self.ALT_BACK_BUTTON)
        except Exception:
            self.click(self.BACK_BUTTON)
        logger.info("从计划详情返回上一页")
        return self


# 延迟导入，解决循环依赖
try:
    from pages.plan_edit_page import PlanEditPage
except ImportError:
    # PlanEditPage可能尚未创建，回退到通用BasePage
    PlanEditPage = None
