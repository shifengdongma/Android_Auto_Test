# -*- coding: utf-8 -*-
"""
登录页面 (LoginPage)

页面路径: 登录页是APP启动后的第一个页面
页面功能:
    - 账号密码登录
    - 图片验证码输入及刷新
    - 忘记密码/找回密码流程 (邮箱验证)
    - 微信登录入口 (预留)
    - 错误提示信息展示

对应原型: pages/小程序_登录.html
"""

import logging
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """
    登录页面对象

    封装登录页面的所有元素定位和操作方法。
    """

    # ============================================================
    # 元素定位器 (Locators)
    # ============================================================

    # --- 登录表单 ---
    USERNAME_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)')
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)')
    CAPTCHA_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(2)')
    CAPTCHA_IMAGE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("验证码")')

    LOGIN_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("登录")')
    FORGOT_PASSWORD_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("忘记密码")')

    # --- 微信登录 (预留) ---
    WECHAT_LOGIN_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("微信登录")')

    # --- 找回密码 ---
    RECOVER_EMAIL_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("邮箱")')
    RECOVER_CODE_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("验证码")')
    SEND_CODE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("获取验证码")')
    RESEND_CODE_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("重新获取")')

    NEW_PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("新密码")')
    CONFIRM_PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("确认密码")')
    RESET_SUBMIT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("提交")')

    # --- 通用 ---
    BACK_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "返回")
    ERROR_MESSAGE = (AppiumBy.ID, "android:id/message")
    TOAST_TEXT = (AppiumBy.XPATH, "//android.widget.Toast")
    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("低空")')

    # --- 备用定位 (根据实际APP调整resource-id) ---
    ALT_USERNAME_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_username")
    ALT_PASSWORD_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_password")
    ALT_CAPTCHA_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_captcha")
    ALT_LOGIN_BUTTON = (AppiumBy.ID, "com.dolphin.atc:id/btn_login")

    # ============================================================
    # 页面操作方法
    # ============================================================

    def enter_username(self, username: str):
        """
        输入账号

        Args:
            username: 账号

        Returns:
            self: 支持链式调用
        """
        logger.info(f"输入账号: {username}")
        # 优先尝试resource-id定位，回退到通用定位
        locator = self.ALT_USERNAME_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.USERNAME_INPUT
        self.input_text(locator, username)
        return self

    def enter_password(self, password: str):
        """
        输入密码

        Args:
            password: 密码

        Returns:
            self
        """
        logger.info(f"输入密码: {'*' * len(password)}")
        locator = self.ALT_PASSWORD_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.PASSWORD_INPUT
        self.input_text(locator, password)
        return self

    def enter_captcha(self, captcha: str):
        """
        输入图片验证码

        Args:
            captcha: 4位验证码

        Returns:
            self
        """
        logger.info(f"输入验证码: {captcha}")
        locator = self.ALT_CAPTCHA_INPUT
        if not self.is_element_present(locator, timeout=2):
            locator = self.CAPTCHA_INPUT
        self.input_text(locator, captcha)
        return self

    def click_login(self):
        """
        点击登录按钮

        Returns:
            HomePage: 登录成功后跳转到首页
        """
        logger.info("点击登录按钮")
        locator = self.ALT_LOGIN_BUTTON
        if not self.is_element_present(locator, timeout=2):
            locator = self.LOGIN_BUTTON
        self.click(locator)
        # 登录成功后可能跳转到首页
        from pages.home_page import HomePage
        return HomePage(self.driver)

    def login(
        self,
        username: str,
        password: str,
        captcha: str = "",
    ):
        """
        完整登录流程 (组合操作)

        Args:
            username: 账号
            password: 密码
            captcha: 验证码 (测试环境可能不需要)

        Returns:
            HomePage: 登录成功后的首页对象

        Raises:
            TimeoutException: 登录失败 (停留在登录页或弹出错误)
        """
        logger.info(f"执行登录操作: username={username}")
        (
            self.enter_username(username)
            .enter_password(password)
        )
        if captcha:
            self.enter_captcha(captcha)
        return self.click_login()

    def click_forgot_password(self):
        """
        点击"忘记密码"链接

        Returns:
            self: 进入找回密码页面
        """
        logger.info("点击'忘记密码'")
        self.click(self.FORGOT_PASSWORD_LINK)
        # 等待找回密码页面加载
        self.wait_for_element(self.RECOVER_EMAIL_INPUT, timeout=10)
        return self

    # ============================================================
    # 找回密码流程
    # ============================================================

    def enter_recover_email(self, email: str):
        """输入找回密码的邮箱"""
        logger.info(f"输入邮箱: {email}")
        self.input_text(self.RECOVER_EMAIL_INPUT, email)
        return self

    def click_send_code(self):
        """
        点击"获取验证码"按钮

        Note:
            点击后按钮变为"重新获取"，并有60秒倒计时。
        """
        logger.info("点击'获取验证码'")
        if self.is_element_present(self.SEND_CODE_BUTTON, timeout=2):
            self.click(self.SEND_CODE_BUTTON)
        else:
            self.click(self.RESEND_CODE_BUTTON)
        return self

    def enter_recover_code(self, code: str):
        """输入邮箱收到的验证码"""
        logger.info(f"输入验证码: {code}")
        self.input_text(self.RECOVER_CODE_INPUT, code)
        return self

    def enter_new_password(self, password: str):
        """输入新密码 (找回密码第二步)"""
        logger.info(f"输入新密码: {'*' * len(password)}")
        self.input_text(self.NEW_PASSWORD_INPUT, password)
        return self

    def confirm_new_password(self, password: str):
        """确认新密码"""
        logger.info(f"确认新密码: {'*' * len(password)}")
        self.input_text(self.CONFIRM_PASSWORD_INPUT, password)
        return self

    def click_reset_submit(self):
        """点击找回密码的提交按钮"""
        logger.info("点击提交(重置密码)")
        self.click(self.RESET_SUBMIT_BUTTON)
        return self

    def recover_password(
        self,
        email: str,
        code: str,
        new_password: str,
    ):
        """
        完整找回密码流程 (组合操作)

        Args:
            email: 注册邮箱
            code: 验证码
            new_password: 新密码

        Returns:
            self
        """
        logger.info(f"执行找回密码流程: email={email}")
        (
            self.enter_recover_email(email)
            .click_send_code()
            .enter_recover_code(code)
            .enter_new_password(new_password)
            .confirm_new_password(new_password)
            .click_reset_submit()
        )
        return self

    # ============================================================
    # 状态/验证方法
    # ============================================================

    def is_on_login_page(self) -> bool:
        """
        判断当前是否在登录页

        Returns:
            bool
        """
        return (
            self.is_element_present(self.PAGE_TITLE, timeout=5)
            or self.is_element_present(self.LOGIN_BUTTON, timeout=3)
        )

    def get_error_message(self, timeout: int = 5) -> str:
        """
        获取错误提示信息

        优先级:
            1. Toast消息
            2. 弹窗错误消息
            3. 页面内错误文本

        Returns:
            str: 错误信息文本
        """
        # 先检查Toast
        toast = self.get_toast_text(timeout)
        if toast:
            return toast

        # 再检查弹窗
        try:
            error = self.get_text(self.ERROR_MESSAGE, timeout=3)
            if error:
                return error
        except Exception:
            pass

        # 最后检查页面内错误文本
        error_locator = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("错误")')
        if self.is_element_present(error_locator, timeout=2):
            return self.get_text(error_locator)

        return ""

    def is_login_button_enabled(self) -> bool:
        """判断登录按钮是否可点击"""
        locator = self.ALT_LOGIN_BUTTON
        if not self.is_element_present(locator, timeout=2):
            locator = self.LOGIN_BUTTON
        return self.is_element_enabled(locator, timeout=3)

    def is_wechat_login_available(self) -> bool:
        """检测微信登录入口是否显示 (预留)"""
        return self.is_element_present(self.WECHAT_LOGIN_BUTTON, timeout=3)

    def refresh_captcha(self):
        """刷新图片验证码 (点击验证码图片)"""
        logger.info("刷新验证码")
        self.click(self.CAPTCHA_IMAGE)
        self.wait_seconds(0.5)
        return self

    def wait_for_login_page(self, timeout: int = 30):
        """
        等待登录页面完全加载

        Args:
            timeout: 超时时间
        """
        logger.info("等待登录页面加载...")
        self.wait_for_element_visible(self.LOGIN_BUTTON, timeout)
        return self

    def wait_for_recover_page(self, timeout: int = 15):
        """等待找回密码页面加载"""
        logger.info("等待找回密码页面加载...")
        self.wait_for_element_visible(self.RECOVER_EMAIL_INPUT, timeout)
        return self
