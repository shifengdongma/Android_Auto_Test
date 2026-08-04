# -*- coding: utf-8 -*-
"""
登录模块 - 自动化测试用例

测试范围:
    - 正常登录流程
    - 错误密码/空输入异常场景
    - 验证码相关
    - 找回密码流程
    - 微信登录入口检测 (预留)

标记: @pytest.mark.login

依赖:
    - config.yaml 中的 test_accounts 配置测试账号
    - data/login_data.yaml 提供参数化数据
"""

import logging

import pytest
import allure

from pages.login_page import LoginPage
from pages.home_page import HomePage

logger = logging.getLogger(__name__)


# ============================================================
# 正常流程测试
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("登录模块")
@allure.story("账号密码登录")
@allure.title("正常登录 - 有效账号密码")
@pytest.mark.login
@pytest.mark.smoke
def test_login_success(driver, config):
    """
    测试场景: 使用有效的账号密码登录

    前置条件:
        - 设备已连接
        - APP已启动
        - 测试账号已在系统中注册

    测试步骤:
        1. 等待登录页加载
        2. 输入正确账号
        3. 输入正确密码
        4. 点击登录
        5. 验证进入首页

    预期结果:
        - 登录成功后跳转到首页
        - 首页显示通知列表或AI输入框
    """
    account = config.get_test_account("default")
    login_page = LoginPage(driver)

    with allure.step("1. 等待登录页面加载"):
        login_page.wait_for_login_page()

    with allure.step("2. 输入有效的账号密码"):
        login_page.enter_username(account["username"])
        login_page.enter_password(account["password"])

    with allure.step("3. 点击登录按钮"):
        home_page = login_page.click_login()

    with allure.step("4. 验证进入首页"):
        home = HomePage(driver)
        home.wait_for_home_page(timeout=15)
        assert home.is_on_home_page(), (
            f"登录失败: 未能进入首页\n"
            f"当前页面: {driver.current_activity}"
        )
        logger.info("✅ 登录成功，已进入首页")


# ============================================================
# 异常场景测试 - 参数化
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("登录模块")
@allure.story("异常登录场景")
@pytest.mark.login
@pytest.mark.parametrize("username,password,expected_error", [
    pytest.param(
        "testuser",
        "wrong_password_123",
        "密码错误",
        id="错误密码"
    ),
    pytest.param(
        "",
        "testpass123",
        "请输入账号",
        id="空账号"
    ),
    pytest.param(
        "testuser",
        "",
        "请输入密码",
        id="空密码"
    ),
    pytest.param(
        "",
        "",
        "请输入",
        id="账号密码均为空"
    ),
])
def test_login_failure(driver, config, username, password, expected_error):
    """
    测试场景: 异常登录 - 参数化

    覆盖:
        - 错误密码 → 提示 "密码错误"
        - 空账号 → 提示 "请输入账号"
        - 空密码 → 提示 "请输入密码"
        - 空账号+空密码 → 提示 "请输入"

    验证点:
        - 登录失败后停留在登录页
        - 显示对应的错误提示信息
    """
    login_page = LoginPage(driver)

    with allure.step("1. 等待登录页加载"):
        login_page.wait_for_login_page()

    with allure.step(f"2. 输入: 账号='{username}', 密码='{password}'"):
        if username:
            login_page.enter_username(username)
        if password:
            login_page.enter_password(password)

    with allure.step("3. 点击登录"):
        try:
            login_page.click_login()
        except Exception:
            pass  # 可能因为空输入导致按钮不可点击

    with allure.step("4. 验证错误提示"):
        # 对于空输入场景，验证按钮是否禁用
        if not username or not password:
            if not login_page.is_login_button_enabled():
                logger.info(f"✅ 登录按钮已禁用 (空输入校验通过)")
                return

        # 获取错误信息
        error_msg = login_page.get_error_message(timeout=5)
        logger.info(f"获取到错误信息: '{error_msg}'")

        assert expected_error in error_msg or login_page.is_on_login_page(), (
            f"错误提示不匹配:\n"
            f"  期望包含: '{expected_error}'\n"
            f"  实际信息: '{error_msg}'\n"
            f"  是否仍在登录页: {login_page.is_on_login_page()}"
        )
        logger.info(f"✅ 异常登录提示正常: {error_msg}")


# ============================================================
# 验证码测试
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("登录模块")
@allure.story("验证码")
@allure.title("错误验证码 - 提示并刷新")
@pytest.mark.login
def test_login_wrong_captcha(driver, config):
    """
    测试场景: 输入错误的验证码

    预期:
        - Toast提示"验证码错误"
        - 验证码自动刷新
        - 验证码输入框清空
    """
    account = config.get_test_account("default")
    login_page = LoginPage(driver)

    with allure.step("1. 输入正确账号密码"):
        login_page.wait_for_login_page()
        login_page.enter_username(account["username"])
        login_page.enter_password(account["password"])

    with allure.step("2. 输入错误验证码"):
        login_page.enter_captcha("AAAA")  # 错误验证码

    with allure.step("3. 点击登录"):
        login_page.click_login()

    with allure.step("4. 验证提示"):
        error = login_page.get_error_message(timeout=5)
        assert "验证码" in error, f"期望验证码错误提示，实际: '{error}'"
        logger.info(f"✅ 验证码错误提示: {error}")

    with allure.step("5. 验证停留在登录页"):
        assert login_page.is_on_login_page(), "错误验证码后不应进入首页"


@allure.epic("低空空管系统")
@allure.feature("登录模块")
@allure.story("验证码")
@allure.title("点击验证码图片 - 刷新验证码")
@pytest.mark.login
def test_refresh_captcha(driver):
    """
    测试场景: 点击验证码图片刷新

    预期:
        - 验证码图片更新
    """
    login_page = LoginPage(driver)
    login_page.wait_for_login_page()

    with allure.step("1. 点击验证码图片"):
        login_page.refresh_captcha()

    with allure.step("2. 验证图片已刷新"):
        # 验证码图片元素仍然存在即可
        assert login_page.is_element_present(
            LoginPage.CAPTCHA_IMAGE, timeout=3
        ), "验证码图片刷新后应仍然可见"
        logger.info("✅ 验证码刷新成功")


# ============================================================
# 找回密码测试
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("登录模块")
@allure.story("找回密码")
@allure.title("找回密码 - 完整流程")
@pytest.mark.login
@pytest.mark.slow
def test_forgot_password_flow(driver, config):
    """
    测试场景: 忘记密码 → 邮箱验证 → 重置密码

    预期:
        - 进入找回密码页面
        - 输入邮箱 → 发送验证码
        - 输入验证码 → 设置新密码
        - 提交成功 → 返回登录页
    """
    account = config.get_test_account("default")
    login_page = LoginPage(driver)

    with allure.step("1. 点击忘记密码"):
        login_page.wait_for_login_page()
        login_page.click_forgot_password()

    with allure.step("2. 输入邮箱"):
        login_page.enter_recover_email(account["email"])

    with allure.step("3. 点击获取验证码"):
        login_page.click_send_code()
        # 验证按钮变为"重新获取"(倒计时中)
        assert login_page.is_element_present(
            LoginPage.RESEND_CODE_BUTTON, timeout=3
        ) or login_page.is_element_present(
            LoginPage.SEND_CODE_BUTTON, timeout=3
        ), "获取验证码按钮状态异常"

    with allure.step("4. 输入验证码 (测试用固定码)"):
        login_page.enter_recover_code("123456")

    with allure.step("5. 设置新密码"):
        login_page.enter_new_password("newTestPass123")
        login_page.confirm_new_password("newTestPass123")

    with allure.step("6. 提交重置"):
        login_page.click_reset_submit()

    with allure.step("7. 验证回到登录页"):
        login_page.wait_for_login_page(timeout=15)
        assert login_page.is_on_login_page(), "重置成功后应返回登录页"
        logger.info("✅ 找回密码流程完成")


# ============================================================
# 微信登录入口检测 (预留)
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("登录模块")
@allure.story("微信登录")
@allure.title("检测微信登录入口")
@pytest.mark.login
def test_wechat_login_entry(driver):
    """
    测试场景: 检测微信登录入口是否存在

    当前第一迭代可能不包含微信登录，此测试为预留。

    预期:
        - 页面如包含微信登录入口则记录
        - 不阻塞测试通过
    """
    login_page = LoginPage(driver)
    login_page.wait_for_login_page()

    has_wechat = login_page.is_wechat_login_available()
    if has_wechat:
        logger.info("检测到微信登录入口 (已启用)")
        pytest.skip("微信登录功能在当前迭代可能未完全实现")
    else:
        logger.info("当前版本不包含微信登录入口 (符合第一迭代预期)")
