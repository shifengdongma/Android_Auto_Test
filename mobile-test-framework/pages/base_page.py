# -*- coding: utf-8 -*-
"""
基础页面类 (BasePage)

功能:
    提供所有Page Object的通用操作方法:
        - 元素查找 (单个/多个)
        - 点击、输入、清除
        - 滑动操作 (上下左右)
        - 显式等待 (存在/可见/可点击/消失)
        - 截图
        - Toast消息获取
        - 系统权限弹窗处理

设计原则:
    - 所有方法包含异常处理和日志记录
    - 使用显式等待(WebDriverWait)替代隐式等待
    - 不包含业务断言 (断言保留在测试用例层)
    - 平台无关设计，支持后续iOS扩展

使用示例:
    from pages.base_page import BasePage
    from appium.webdriver.common.appiumby import AppiumBy

    class LoginPage(BasePage):
        USERNAME_INPUT = (AppiumBy.ID, "username")
        def enter_username(self, text):
            self.input_text(self.USERNAME_INPUT, text)
            return self
"""

import logging
import time
from typing import Tuple, List, Optional, Any

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)
from appium.webdriver.common.appiumby import AppiumBy

try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False

logger = logging.getLogger(__name__)


class BasePage:
    """
    Page Object基类

    封装所有页面的通用操作，具体页面继承此类。
    每个方法返回 self 支持链式调用。
    """

    def __init__(self, driver):
        """
        初始化基础页面

        Args:
            driver: Appium WebDriver实例
        """
        self.driver = driver
        # 从driver中获取当前平台类型 (用于处理平台差异)
        self._platform = self._detect_platform()

    def _detect_platform(self) -> str:
        """自动检测当前平台类型"""
        try:
            caps = self.driver.capabilities
            platform = caps.get("platformName", "").lower()
            return platform if platform else "android"
        except Exception:
            return "android"

    # ============================================================
    # 元素查找
    # ============================================================

    def find_element(
        self,
        locator: Tuple[str, str],
        timeout: int = 15,
    ):
        """
        查找单个元素 (带显式等待)

        Args:
            locator: 元素定位器，格式 (By.XXX, "value")
                    例如: (AppiumBy.ID, "login_btn")
            timeout: 等待超时时间(秒)

        Returns:
            WebElement: 找到的元素

        Raises:
            TimeoutException: 元素在超时时间内未找到
        """
        by, value = locator
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value)),
                message=f"元素未找到: {by}='{value}' (超时{timeout}s)",
            )
            logger.debug(f"找到元素: {by}='{value}'")
            return element
        except TimeoutException:
            logger.error(f"元素查找超时: {by}='{value}'")
            raise

    def find_elements(
        self,
        locator: Tuple[str, str],
        timeout: int = 10,
    ) -> List:
        """
        查找多个元素

        Args:
            locator: 元素定位器
            timeout: 等待至少一个元素出现的时间

        Returns:
            list[WebElement]: 匹配的元素列表 (可能为空)
        """
        by, value = locator
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value)),
            )
        except TimeoutException:
            logger.debug(f"未找到匹配元素: {by}='{value}'")
            return []

        return self.driver.find_elements(by, value)

    def find_element_by_text(
        self,
        text: str,
        partial: bool = False,
        timeout: int = 15,
    ):
        """
        通过文本内容查找元素

        Args:
            text: 要查找的文本
            partial: True=模糊匹配, False=精确匹配
            timeout: 超时时间

        Returns:
            WebElement
        """
        if partial:
            locator = (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().textContains("{text}")',
            )
        else:
            locator = (
                AppiumBy.ANDROID_UIAUTOMATOR,
                f'new UiSelector().text("{text}")',
            )
        return self.find_element(locator, timeout)

    # ============================================================
    # 元素交互
    # ============================================================

    def click(
        self,
        locator: Tuple[str, str],
        timeout: int = 15,
        retry: int = 2,
    ):
        """
        点击元素 (带重试机制)

        自动等待元素可点击后执行点击。
        如果点击被拦截(如被弹窗遮挡)，会进行重试。

        Args:
            locator: 元素定位器
            timeout: 等待超时
            retry: 失败重试次数

        Returns:
            self: 支持链式调用
        """
        by, value = locator
        for attempt in range(retry + 1):
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value)),
                    message=f"元素不可点击: {by}='{value}'",
                )
                element.click()
                logger.debug(f"点击成功: {by}='{value}'")
                return self
            except ElementClickInterceptedException:
                if attempt < retry:
                    logger.warning(
                        f"点击被拦截 ({attempt + 1}/{retry + 1}): {by}='{value}'，重试中..."
                    )
                    time.sleep(0.5)
                else:
                    raise
            except TimeoutException:
                logger.error(f"元素不可点击(超时): {by}='{value}'")
                raise
        return self

    def input_text(
        self,
        locator: Tuple[str, str],
        text: str,
        clear_first: bool = True,
        timeout: int = 15,
    ):
        """
        在输入框中输入文本

        Args:
            locator: 元素定位器
            text: 要输入的文本
            clear_first: 是否先清空已有内容
            timeout: 等待超时

        Returns:
            self: 支持链式调用
        """
        element = self.find_element(locator, timeout)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.debug(f"输入文本: '{text[:20]}{'...' if len(text) > 20 else ''}'")
        return self

    def clear_input(self, locator: Tuple[str, str], timeout: int = 10):
        """清空输入框"""
        element = self.find_element(locator, timeout)
        element.clear()
        return self

    # ============================================================
    # 元素状态判断
    # ============================================================

    def is_element_present(
        self,
        locator: Tuple[str, str],
        timeout: int = 5,
    ) -> bool:
        """
        判断元素是否存在于DOM中

        Args:
            locator: 元素定位器
            timeout: 最大等待时间

        Returns:
            bool: 元素是否存在
        """
        try:
            self.find_element(locator, timeout)
            return True
        except TimeoutException:
            return False

    def is_element_visible(
        self,
        locator: Tuple[str, str],
        timeout: int = 5,
    ) -> bool:
        """
        判断元素是否可见

        Args:
            locator: 元素定位器
            timeout: 最大等待时间

        Returns:
            bool: 元素是否可见
        """
        try:
            by, value = locator
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value)),
            )
            return True
        except TimeoutException:
            return False

    def is_element_enabled(
        self,
        locator: Tuple[str, str],
        timeout: int = 5,
    ) -> bool:
        """判断元素是否可交互(enabled)"""
        element = self.find_element(locator, timeout)
        return element.is_enabled()

    def get_text(
        self,
        locator: Tuple[str, str],
        timeout: int = 10,
    ) -> str:
        """
        获取元素的文本内容

        Args:
            locator: 元素定位器
            timeout: 等待超时

        Returns:
            str: 元素文本 (不存在返回空字符串)
        """
        try:
            element = self.find_element(locator, timeout)
            return element.text or ""
        except TimeoutException:
            return ""

    def get_attribute(
        self,
        locator: Tuple[str, str],
        attribute: str,
        timeout: int = 10,
    ) -> Optional[str]:
        """
        获取元素属性值

        Args:
            locator: 元素定位器
            attribute: 属性名 (如 'content-desc', 'resource-id', 'checked')
            timeout: 等待超时

        Returns:
            str: 属性值 (不存在返回None)
        """
        try:
            element = self.find_element(locator, timeout)
            return element.get_attribute(attribute)
        except TimeoutException:
            return None

    # ============================================================
    # 等待方法
    # ============================================================

    def wait_for_element(
        self,
        locator: Tuple[str, str],
        timeout: int = 15,
    ):
        """等待元素出现 (presence)"""
        return self.find_element(locator, timeout)

    def wait_for_element_visible(
        self,
        locator: Tuple[str, str],
        timeout: int = 15,
    ):
        """等待元素可见"""
        by, value = locator
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value)),
            message=f"元素未变为可见: {by}='{value}'",
        )

    def wait_for_element_clickable(
        self,
        locator: Tuple[str, str],
        timeout: int = 15,
    ):
        """等待元素可点击"""
        by, value = locator
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value)),
            message=f"元素不可点击: {by}='{value}'",
        )

    def wait_for_element_disappear(
        self,
        locator: Tuple[str, str],
        timeout: int = 30,
    ) -> bool:
        """
        等待元素从页面消失

        Args:
            locator: 元素定位器
            timeout: 最大等待时间

        Returns:
            bool: 是否成功消失
        """
        try:
            by, value = locator
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((by, value)),
            )
            return True
        except TimeoutException:
            logger.warning(f"元素在{timeout}s内未消失: {by}='{value}'")
            return False

    def wait_for_text_present(
        self,
        text: str,
        timeout: int = 10,
    ) -> bool:
        """
        等待指定文本出现在页面上

        Args:
            text: 待匹配文本
            timeout: 超时时间

        Returns:
            bool: 文本是否出现
        """
        locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("{text}")',
        )
        return self.is_element_present(locator, timeout)

    def wait_seconds(self, seconds: float = 1.0):
        """
        强制等待 (仅用于特殊场景)

        注意: 尽量使用显式等待，仅在以下场景使用:
            - 动画过渡
            - 网络请求完成后UI刷新
            - 第三方SDK无元素可定位

        Args:
            seconds: 等待秒数
        """
        time.sleep(seconds)
        return self

    # ============================================================
    # 滑动操作
    # ============================================================

    def _get_window_size(self) -> dict:
        """获取屏幕尺寸"""
        size = self.driver.get_window_size()
        return {"width": size["width"], "height": size["height"]}

    def swipe_up(self, duration_ms: int = 500):
        """
        向上滑动 (手指从下往上)

        适用于大多数需要向下滚动的场景。
        """
        size = self._get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.8)
        end_y = int(size["height"] * 0.2)

        self.driver.swipe(start_x, start_y, start_x, end_y, duration_ms)
        logger.debug(f"向上滑动: ({start_x},{start_y}) -> ({start_x},{end_y})")
        return self

    def swipe_down(self, duration_ms: int = 500):
        """
        向下滑动 (手指从上往下)

        适用于刷新或回到顶部。
        """
        size = self._get_window_size()
        start_x = size["width"] // 2
        start_y = int(size["height"] * 0.2)
        end_y = int(size["height"] * 0.8)

        self.driver.swipe(start_x, start_y, start_x, end_y, duration_ms)
        logger.debug(f"向下滑动: ({start_x},{start_y}) -> ({start_x},{end_y})")
        return self

    def swipe_left(self, duration_ms: int = 300):
        """
        向左滑动

        适用于Tab切换、图片轮播等场景。
        """
        size = self._get_window_size()
        start_x = int(size["width"] * 0.8)
        end_x = int(size["width"] * 0.2)
        y = size["height"] // 2

        self.driver.swipe(start_x, y, end_x, y, duration_ms)
        logger.debug(f"向左滑动: ({start_x},{y}) -> ({end_x},{y})")
        return self

    def swipe_right(self, duration_ms: int = 300):
        """
        向右滑动

        适用于返回上一页等场景。
        """
        size = self._get_window_size()
        start_x = int(size["width"] * 0.2)
        end_x = int(size["width"] * 0.8)
        y = size["height"] // 2

        self.driver.swipe(start_x, y, end_x, y, duration_ms)
        logger.debug(f"向右滑动: ({start_x},{y}) -> ({end_x},{y})")
        return self

    def scroll_to_element(self, locator: Tuple[str, str], max_swipes: int = 5):
        """
        滚动到指定元素 (通过向上滑动直到元素可见)

        Args:
            locator: 目标元素定位器
            max_swipes: 最大滑动次数

        Returns:
            self: 如果找到元素
            None: 超过最大滑动次数仍未找到
        """
        for i in range(max_swipes):
            if self.is_element_visible(locator, timeout=3):
                logger.debug(f"滚动到元素成功 (第{i + 1}次)")
                return self
            self.swipe_up()
        logger.warning(f"滚动{max_swipes}次后仍未找到元素")
        return self

    def scroll_to_text(self, text: str, max_swipes: int = 5):
        """
        滚动到包含指定文本的元素

        Args:
            text: 目标文本
            max_swipes: 最大滑动次数

        Returns:
            self 或 None
        """
        locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("{text}")',
        )
        return self.scroll_to_element(locator, max_swipes)

    # ============================================================
    # 截图
    # ============================================================

    def take_screenshot(self, name: str = "screenshot") -> str:
        """
        执行页面截图

        Args:
            name: 截图描述名称

        Returns:
            str: 截图文件路径
        """
        from utils.screenshot import ScreenshotManager

        screenshot_mgr = ScreenshotManager(self.driver)
        path = screenshot_mgr.capture(name)
        logger.info(f"截图已保存: {path}")
        return path

    # ============================================================
    # 坐标操作 (用于地图、图表等无确定选择器的元素)
    # ============================================================

    def tap_coordinates(self, x: int, y: int):
        """
        按坐标点击

        适用于:
            - 地图上的Marker
            - 图表数据点
            - 无法通过选择器定位的自定义View

        Args:
            x: X坐标(像素)
            y: Y坐标(像素)
        """
        self.driver.tap([(x, y)])
        logger.debug(f"坐标点击: ({x}, {y})")
        return self

    # ============================================================
    # 系统交互
    # ============================================================

    def go_back(self):
        """点击系统返回键"""
        self.driver.back()
        logger.debug("点击系统返回键")
        return self

    def hide_keyboard(self):
        """隐藏软键盘"""
        try:
            if self.driver.is_keyboard_shown():
                self.driver.hide_keyboard()
                logger.debug("软键盘已隐藏")
        except Exception:
            pass  # 键盘未显示时直接忽略
        return self

    def accept_alert(self):
        """接受系统弹窗 (如权限请求)"""
        try:
            self.driver.switch_to.alert.accept()
            logger.debug("已接受系统弹窗")
        except Exception:
            pass
        return self

    def dismiss_alert(self):
        """取消系统弹窗"""
        try:
            self.driver.switch_to.alert.dismiss()
            logger.debug("已取消系统弹窗")
        except Exception:
            pass
        return self

    # ============================================================
    # Toast消息
    # ============================================================

    def get_toast_text(self, timeout: int = 5) -> str:
        """
        获取Android Toast消息文本

        Args:
            timeout: 等待Toast出现的最大时间

        Returns:
            str: Toast消息文本 (未获取到返回空字符串)

        Note:
            此方法仅支持Android (UiAutomator2)
        """
        try:
            locator = (
                AppiumBy.XPATH,
                "//android.widget.Toast",
            )
            element = self.find_element(locator, timeout)
            return element.get_attribute("name") or element.text or ""
        except TimeoutException:
            logger.debug("未检测到Toast消息")
            return ""

    def is_toast_displayed(self, expected_text: str, timeout: int = 5) -> bool:
        """
        验证Toast消息内容

        Args:
            expected_text: 期望的Toast文本
            timeout: 等待时间

        Returns:
            bool: Toast内容是否匹配
        """
        actual = self.get_toast_text(timeout)
        return expected_text in actual

    # ============================================================
    # 应用状态
    # ============================================================

    def get_current_activity(self) -> str:
        """获取当前Activity名称 (仅Android)"""
        try:
            return self.driver.current_activity or "unknown"
        except Exception:
            return "unknown"

    def get_page_source(self) -> str:
        """获取当前页面XML源码 (用于调试)"""
        return self.driver.page_source

    # ============================================================
    # 权限弹窗处理 (通用)
    # ============================================================

    def handle_permission_popup(
        self,
        allow: bool = True,
        timeout: int = 5,
    ):
        """
        处理系统权限弹窗

        Android常见权限弹窗:
            - "允许 [APP] 访问此设备的位置信息?"
            - "允许 [APP] 拍摄照片和录制视频?"
            - "允许 [APP] 访问您设备上的文件?"

        Args:
            allow: True=允许, False=拒绝
            timeout: 等待弹窗出现的时间
        """
        try:
            if allow:
                # 尝试点击"允许"按钮
                allow_locators = [
                    (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_button"),
                    (AppiumBy.ID, "android:id/button1"),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("允许")'),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("始终允许")'),
                    (AppiumBy.XPATH, '//*[@text="允许"]'),
                ]
                for loc in allow_locators:
                    if self.is_element_present(loc, timeout=2):
                        self.click(loc)
                        logger.info("已允许系统权限")
                        return self
            else:
                deny_locators = [
                    (AppiumBy.ID, "com.android.permissioncontroller:id/permission_deny_button"),
                    (AppiumBy.ID, "android:id/button2"),
                    (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("拒绝")'),
                    (AppiumBy.XPATH, '//*[@text="拒绝"]'),
                ]
                for loc in deny_locators:
                    if self.is_element_present(loc, timeout=2):
                        self.click(loc)
                        logger.info("已拒绝系统权限")
                        return self
        except Exception:
            pass
        return self

    # ============================================================
    # Allure步骤装饰 (可选)
    # ============================================================

    @staticmethod
    def allure_step(step_name: str):
        """
        创建Allure测试步骤上下文

        用法:
            with BasePage.allure_step("用户登录"):
                login_page.login("user", "pass")

        Args:
            step_name: 步骤名称
        """
        if ALLURE_AVAILABLE:
            return allure.step(step_name)
        else:
            # 如果没有Allure，返回一个空的上下文管理器
            from contextlib import contextmanager

            @contextmanager
            def null_context():
                yield

            return null_context()
