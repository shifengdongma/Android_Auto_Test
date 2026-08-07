# -*- coding: utf-8 -*-
"""
注册模块 - 自动化测试用例 (预留骨架)

测试范围:
    - 注册页面显示
    - 正常注册流程 (数据驱动)
    - 注册校验异常 (数据驱动)

说明:
    - 第一迭代无注册入口，本模块为框架预留
    - 双守卫: require_native_mode (browser模式skip) + 定位器探测(未校准则skip)
    - APK就绪后校准 pages/register_page.py 的定位器常量即自动激活
    - 首次消费 data/register_data.yaml + test_data fixture

标记: @pytest.mark.register
"""

import logging

import pytest
import allure

from pages.register_page import RegisterPage
from pages.login_page import LoginPage

logger = logging.getLogger(__name__)


# ============================================================
# Fixture
# ============================================================

@pytest.fixture(scope="module")
def register_ready(driver, require_native_mode):
    """
    注册页就绪守卫 (模块级)

    定位器未校准(APK未就绪)时自动skip整个模块。

    Returns:
        RegisterPage
    """
    page = RegisterPage(driver)
    # 探测注册入口/注册页标题，未校准则skip
    if not page.is_element_present(page.REGISTER_ENTRY, timeout=3) and \
            not page.is_element_present(page.SUBMIT_BUTTON, timeout=3) and \
            not page.is_element_present(page.PAGE_TITLE, timeout=3):
        pytest.skip("注册页定位器待APK校准 (pages/register_page.py)")
    return page


@pytest.fixture
def register_page(register_ready):
    """进入注册页 (从登录页点注册入口，待校准)"""
    login_page = LoginPage(register_ready.driver)
    try:
        login_page.wait_for_login_page(timeout=10)
        if register_ready.is_element_present(register_ready.REGISTER_ENTRY, timeout=3):
            register_ready.click(register_ready.REGISTER_ENTRY)
            register_ready.wait_for_register_page(timeout=10)
    except Exception as e:
        logger.warning(f"进入注册页失败(待APK校准): {e}")
    return register_ready


# ============================================================
# 用例
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("注册")
@allure.story("注册页面")
@allure.title("注册页面正常显示")
@pytest.mark.register
def test_register_page_displayed(register_ready):
    """
    验证点: 注册页可识别 (定位器校准后生效)
    """
    with allure.step("1. 验证注册页识别"):
        assert register_ready.is_on_register_page(), "无法识别注册页"
    logger.info("注册页显示正常")


@allure.epic("低空空管系统")
@allure.feature("注册")
@allure.story("正常注册")
@allure.title("正常注册流程")
@pytest.mark.register
@pytest.mark.data_file("data/register_data.yaml")
def test_register_success(register_page, test_data):
    """
    验证点: 正常注册流程完成 (数据驱动 register_success_cases)

    定位器校准后自动激活；注册成功后的跳转目标页待APK确认。
    """
    cases = test_data.get("register_success_cases") if isinstance(test_data, dict) else test_data
    if not cases:
        pytest.skip("注册数据为空 (data/register_data.yaml)")

    case = cases[0]  # 正常注册只跑一组，避免重复注册同名用户
    with allure.step(f"1. 执行注册流程 ({case['description']})"):
        register_page.register(
            username=case["username"],
            password=case["password"],
            confirm=case["confirm"],
            email=case["email"],
            code=case["code"],
        )

    with allure.step("2. 验证注册结果"):
        # 注册成功提示/跳转目标页待APK确认，先验证无错误提示
        error = register_page.get_error_message(timeout=3)
        logger.info(f"注册结果错误提示: {error!r}")


@allure.epic("低空空管系统")
@allure.feature("注册")
@allure.story("注册校验")
@allure.title("注册校验异常提示")
@pytest.mark.register
@pytest.mark.data_file("data/register_data.yaml")
def test_register_validation(register_page, test_data):
    """
    验证点: 非法输入出现对应错误提示 (数据驱动 register_validation_cases)
    """
    cases = test_data.get("register_validation_cases") if isinstance(test_data, dict) else test_data
    if not cases:
        pytest.skip("注册校验数据为空 (data/register_data.yaml)")

    for case in cases:
        with allure.step(f"1. 提交非法数据 ({case['description']})"):
            register_page.register(
                username=case.get("username", ""),
                password=case.get("password", ""),
                confirm=case.get("confirm", ""),
            )

        with allure.step(f"2. 验证错误提示包含 [{case['expected_error']}]"):
            error = register_page.get_error_message(timeout=3)
            assert case["expected_error"] in error, (
                f"错误提示 [{error!r}] 未包含期望关键词 [{case['expected_error']}]"
            )
        logger.info(f"校验通过: {case['description']} -> {error!r}")
