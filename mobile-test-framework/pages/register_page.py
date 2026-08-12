# -*- coding: utf-8 -*-
"""
注册页面 (RegisterPage) - 预留框架能力

设计决策:
    根据《06-手机端-第一迭代.md》原型文档，第一迭代不提供注册入口，
    仅支持PC端已有账号登录移动端。后续迭代考虑手机号快捷登录、微信授权登录扩展。

    本页面为框架预留。APK就绪后，使用Appium Inspector校准下方"待校准"定位器
    即可自动激活，无需改动测试代码逻辑。

    当前行为: 所有注册相关测试通过 require_native_mode guard 自动 skip。

页面功能 (预留):
    - 用户名/密码/确认密码/邮箱注册
    - 邮箱验证码获取 (60s倒计时)
    - 注册校验错误提示

对应原型: pages/小程序_登录.html (第一迭代无注册入口)
"""

import logging
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class RegisterPage(BasePage):
    """
    注册页面对象 (预留)

    定位器全部带"待校准"注释，结构参照 login_page 的 ALT_ 优先 + 通用回退模式。
    """

    # ============================================================
    # 元素定位器 (Locators) — 全部待校准
    # ============================================================

    # --- 登录页"注册"入口 (从登录页跳转) ---
    REGISTER_ENTRY = (AppiumBy.ID, "com.dolphin.atc:id/btn_register")  # 待校准

    # --- 注册表单 ---
    USERNAME_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)')  # 待校准
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)')  # 待校准
    CONFIRM_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(2)')  # 待校准
    EMAIL_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("邮箱")')  # 待校准
    VERIFY_CODE_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("验证码")')  # 待校准

    SEND_CODE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("获取验证码")')  # 待校准
    SUBMIT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("注册")')  # 待校准

    # --- 通用 ---
    ERROR_MESSAGE = (AppiumBy.ID, "android:id/message")
    TOAST_TEXT = (AppiumBy.XPATH, "//android.widget.Toast")
    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("注册")')  # 待校准

    # --- 备用定位 (根据实际APP调整resource-id) ---
    ALT_USERNAME_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_register_user")  # 待校准
    ALT_PASSWORD_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_register_pass")  # 待校准
    ALT_CONFIRM_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_register_confirm")  # 待校准
    ALT_EMAIL_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_register_email")  # 待校准
    ALT_VERIFY_CODE_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_register_code")  # 待校准
    ALT_SUBMIT_BUTTON = (AppiumBy.ID, "com.dolphin.atc:id/btn_register_submit")  # 待校准

    # ============================================================
    # 页面操作方法 (链式)
    # ============================================================

    def enter_username(self, username: str):
        """
        输入注册用户名

        Returns:
            self
        """
        logger.info(f"输入注册用户名: {username}")
        locator = self.ALT_USERNAME_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.USERNAME_INPUT
        self.input_text(locator, username)
        return self

    def enter_password(self, password: str):
        """
        输入注册密码 (日志打码)

        Returns:
            self
        """
        logger.info(f"输入注册密码: {'*' * len(password)}")
        locator = self.ALT_PASSWORD_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.PASSWORD_INPUT
        self.input_text(locator, password)
        return self

    def enter_confirm_password(self, password: str):
        """
        输入确认密码

        Returns:
            self
        """
        logger.info(f"输入确认密码: {'*' * len(password)}")
        locator = self.ALT_CONFIRM_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.CONFIRM_INPUT
        self.input_text(locator, password)
        return self

    def enter_email(self, email: str):
        """
        输入注册邮箱

        Returns:
            self
        """
        logger.info(f"输入注册邮箱: {email}")
        locator = self.ALT_EMAIL_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.EMAIL_INPUT
        self.input_text(locator, email)
        return self

    def enter_verify_code(self, code: str):
        """
        输入邮箱验证码

        Returns:
            self
        """
        logger.info(f"输入验证码: {code}")
        locator = self.ALT_VERIFY_CODE_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.VERIFY_CODE_INPUT
        self.input_text(locator, code)
        return self

    def click_send_code(self):
        """
        点击"获取验证码"按钮 (处理60s倒计时切换)

        Returns:
            self
        """
        logger.info("点击获取验证码")
        self.click(self.SEND_CODE_BUTTON)
        return self

    def click_submit(self):
        """
        点击"注册"提交按钮

        Returns:
            self
        """
        logger.info("点击注册提交")
        locator = self.ALT_SUBMIT_BUTTON
        if not self.is_element_present(locator, timeout=2):
            locator = self.SUBMIT_BUTTON
        self.click(locator)
        return self

    def register(
        self,
        username: str,
        password: str,
        confirm: Optional[str] = None,
        email: str = "",
        code: str = "",
    ):
        """
        组合注册流程 (链式)

        Args:
            username: 用户名
            password: 密码
            confirm: 确认密码 (默认同password)
            email: 邮箱
            code: 验证码

        Returns:
            self (注册成功后跳转目标页待APK确认)
        """
        confirm = confirm if confirm is not None else password
        return (
            self.enter_username(username)
            .enter_password(password)
            .enter_confirm_password(confirm)
            .enter_email(email)
            .enter_verify_code(code)
            .click_submit()
        )

    # ============================================================
    # 状态与校验
    # ============================================================

    def is_on_register_page(self) -> bool:
        """
        判断是否在注册页

        定位器未校准(APK未就绪)时探测失败返回False，
        测试层据此自动skip。
        """
        return self.is_element_present(self.PAGE_TITLE, timeout=3) or \
            self.is_element_present(self.SUBMIT_BUTTON, timeout=3)

    def get_error_message(self, timeout: int = 5) -> str:
        """
        获取注册错误提示 (Toast → 弹窗 → 页面文本 三级)

        Returns:
            str: 错误信息文本
        """
        # 1. Toast
        toast = self.get_toast_text(timeout=timeout)
        if toast:
            return toast
        # 2. 弹窗
        if self.is_element_present(self.ERROR_MESSAGE, timeout=2):
            return self.get_text(self.ERROR_MESSAGE)
        # 3. 页面内错误文本 (待校准: 根据实际APP补充错误文案定位器)
        return ""

    def wait_for_register_page(self, timeout: int = 30):
        """
        等待注册页加载

        Returns:
            self
        """
        self.wait_for_element(self.PAGE_TITLE, timeout=timeout)
        return self
