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

import base64
import logging
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from utils.captcha_solver import ArithmeticCaptchaSolver, decode_base64_png

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
    # 新APK (com.keda.atc) 输入框无 resource-id, 按出现顺序定位 (真机实测可用)
    USERNAME_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)')
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)')
    CAPTCHA_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(2)')
    # 验证码图片: Image 元素中 text 属性携带 base64 数据者 (由 _find_captcha_image 过滤)
    CAPTCHA_IMAGE = (AppiumBy.CLASS_NAME, "android.widget.Image")

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

    # ============================================================
    # 页面操作方法
    # ============================================================

    def enter_username(self, username: str):
        """输入账号"""
        logger.info(f"输入账号: {username}")
        self.input_text(self.USERNAME_INPUT, username)
        return self

    def enter_password(self, password: str):
        """输入密码"""
        logger.info(f"输入密码: {'*' * len(password)}")
        self.input_text(self.PASSWORD_INPUT, password)
        return self

    def enter_captcha(self, captcha: str):
        """输入验证码答案"""
        logger.info(f"输入验证码: {captcha}")
        self.input_text(self.CAPTCHA_INPUT, captcha)
        return self

    def click_login(self):
        """
        点击登录按钮

        Returns:
            HomePage: 登录成功后跳转到首页
        """
        logger.info("点击登录按钮")
        self.click(self.LOGIN_BUTTON)
        from pages.home_page import HomePage
        return HomePage(self.driver)

    MAX_CAPTCHA_RETRIES = 3

    def login(
        self,
        username: str,
        password: str,
        captcha_override: Optional[str] = None,
    ):
        """
        完整登录流程 (自动求解算术验证码)

        Args:
            username: 账号
            password: 密码
            captcha_override: 指定验证码答案 (供负例测试)。
                              非 None 时单发不重试: 失败直接抛出。

        Returns:
            HomePage: 登录成功后的首页对象

        Raises:
            TimeoutException: 登录失败 (账号/密码错误, 或验证码重试耗尽)
        """
        logger.info(f"执行登录操作: username={username}")
        self.enter_username(username).enter_password(password)

        if captcha_override is not None:
            self.enter_captcha(captcha_override)
            self.click_login()
            error = self._get_login_error()
            if error is None:
                from pages.home_page import HomePage
                return HomePage(self.driver)
            raise TimeoutException(f"登录失败: {error}")

        for attempt in range(1, self.MAX_CAPTCHA_RETRIES + 1):
            answer = self.solve_captcha()
            self.enter_captcha(answer)
            self.click_login()
            error = self._get_login_error()
            if error is None:
                from pages.home_page import HomePage
                return HomePage(self.driver)
            if "验证码" not in error:
                # 账号/密码类业务错误, 不重试
                self.take_screenshot("login_failed")
                raise TimeoutException(f"登录失败: {error}")
            logger.warning(
                f"验证码错误, 刷新重试 ({attempt}/{self.MAX_CAPTCHA_RETRIES}): {error}"
            )
            self.refresh_captcha()

        self.take_screenshot("login_failed")
        raise TimeoutException(
            f"登录失败: 验证码识别/校验重试{self.MAX_CAPTCHA_RETRIES}次仍未成功"
        )

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
        return self.is_element_enabled(self.LOGIN_BUTTON, timeout=3)

    def is_wechat_login_available(self) -> bool:
        """检测微信登录入口是否显示 (预留)"""
        return self.is_element_present(self.WECHAT_LOGIN_BUTTON, timeout=3)

    def solve_captcha(self) -> str:
        """
        求解当前验证码 (识别失败自动刷新重试, 最多 MAX_CAPTCHA_RETRIES 次)

        Returns:
            str: 算术验证码答案 (如 "8")

        Raises:
            TimeoutException: 连续重试后仍无法求解
        """
        solver = ArithmeticCaptchaSolver()
        image = self._find_captcha_image()
        for attempt in range(1, self.MAX_CAPTCHA_RETRIES + 1):
            try:
                answer = solver.solve(self._get_captcha_image_bytes(image))
            except Exception as e:
                logger.warning(f"验证码求解异常: {e}")
                answer = None
            if answer:
                logger.info(f"验证码答案: {answer} (第{attempt}次)")
                return answer
            if attempt < self.MAX_CAPTCHA_RETRIES:
                logger.warning(f"验证码识别失败(第{attempt}次), 刷新重试")
                self.refresh_captcha()
                image = self._find_captcha_image()
        raise TimeoutException(f"验证码识别失败: 连续{self.MAX_CAPTCHA_RETRIES}次无法求解")

    def refresh_captcha(self):
        """刷新验证码 (图片 clickable=false, 改用坐标点击图片中心)"""
        logger.info("刷新验证码")
        image = self._find_captcha_image()
        self.tap_coordinates(*self._element_center(image))
        self.wait_seconds(1.0)
        return self

    def get_captcha_image_base64(self) -> str:
        """获取当前验证码图片内容 (base64), 供刷新前后对比"""
        image = self._find_captcha_image()
        text = image.get_attribute("text") or ""
        if len(text) > 50:
            return text
        return image.screenshot_as_base64

    def _find_captcha_image(self):
        """
        定位验证码 Image 元素

        策略: 1) text 属性携带 base64 数据 (len>50) 的 Image
              2) 兜底: 验证码行位置 (x>=700 且 y>=1150) 的 Image

        Raises:
            TimeoutException: 未找到
        """
        images = self.find_elements(self.CAPTCHA_IMAGE, timeout=10)
        for img in images:
            try:
                if len(img.get_attribute("text") or "") > 50:
                    return img
            except Exception:
                continue
        for img in images:
            loc = img.location or {}
            if loc.get("x", 0) >= 700 and loc.get("y", 0) >= 1150:
                return img
        raise TimeoutException("未找到验证码图片元素")

    def _get_captcha_image_bytes(self, image_element) -> bytes:
        """
        提取验证码图片字节: 优先 text 属性 base64, 回退元素截图

        Args:
            image_element: _find_captcha_image() 返回的元素

        Returns:
            bytes: PNG 图片字节
        """
        text = image_element.get_attribute("text") or ""
        data = decode_base64_png(text)
        if data:
            return data
        return base64.b64decode(image_element.screenshot_as_base64)

    def _get_login_error(self) -> Optional[str]:
        """
        登录点击后的结果校验

        Returns:
            str|None: 错误信息 (仍停留在登录页)；None 表示已离开登录页 (成功)
        """
        self.wait_seconds(2.0)  # 等待登录请求返回 (get_error_message 内部另有等待, 容忍慢跳转)
        if not self.is_on_login_page():
            return None
        return self.get_error_message(timeout=5)

    @staticmethod
    def _element_center(element):
        """元素中心坐标 (tap 用)"""
        loc = element.location
        size = element.size
        return loc["x"] + size["width"] // 2, loc["y"] + size["height"] // 2

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
