# -*- coding: utf-8 -*-
"""
我的模块 - 自动化测试用例 (真机校准版)

测试范围 (按真实应用流程):
    - 信誉明细入口
    - 关于我们入口
    - 退出登录 (回到登录页)

标记: @pytest.mark.mine

前置: fresh_logged_in_driver (清数据+登录, 保证a11y树确定性)
"""

import logging

import pytest
import allure

from pages.mine_page import MinePage
from utils import webview_a11y

logger = logging.getLogger(__name__)


def _goto_mine(driver) -> MinePage:
    ok = webview_a11y.switch_tab(
        driver, "我的", marker=MinePage.ENTRY_LOGOUT
    )
    assert ok, "未能切换到我的页"
    mine = MinePage(driver)
    mine.wait_for_mine_page()
    return mine


@allure.epic("低空空管系统")
@allure.feature("我的模块")
@allure.story("功能入口")
@allure.title("信誉明细/关于我们入口可点击进入")
@pytest.mark.mine
def test_mine_entries(fresh_logged_in_driver):
    """
    依次点击 信誉明细 / 关于我们 入口, 返回后仍在我的页

    预期: 入口可点击进入子页面, 返回正常。
    """
    mine = _goto_mine(fresh_logged_in_driver)

    for entry in [MinePage.ENTRY_CREDIT_DETAIL, MinePage.ENTRY_ABOUT_US]:
        with allure.step(f"进入: {entry}"):
            mine.open_entry(entry)
            logger.info(f"✅ {entry} 已点击 (截图留证)")
            mine.take_screenshot(f"mine_entry_{entry}")
            mine.go_back()
            mine.wait_for_mine_page()
            logger.info(f"✅ {entry} 返回正常")


@allure.epic("低空空管系统")
@allure.feature("我的模块")
@allure.story("退出登录")
@allure.title("退出登录回到登录页")
@pytest.mark.mine
@pytest.mark.smoke
def test_logout(fresh_logged_in_driver):
    """
    点击退出登录 (如有确认弹窗则确认)

    预期: 回到登录页 (登录按钮出现)。
    """
    mine = _goto_mine(fresh_logged_in_driver)

    with allure.step("1. 点击退出登录"):
        mine.open_entry(MinePage.ENTRY_LOGOUT)
        mine.confirm_logout_if_needed()

    with allure.step("2. 验证回到登录页"):
        assert mine.is_back_on_login_page(), "退出登录后未回到登录页"
        logger.info("✅ 退出登录成功, 已回到登录页")
