# -*- coding: utf-8 -*-
"""
首页模块 - 自动化测试用例 (真机校准版)

测试范围 (按真实应用流程):
    - 顶部三个通知模块切换: 计划审批 / 告警通知 / 管制员通知
    - 有消息内容时点击首条通知进入详情
    - 知识助手入口可点击进入 (功能开发中, 仅验证入口)

标记: @pytest.mark.home

前置: fresh_logged_in_driver (清数据+登录, 保证a11y树确定性)
"""

import logging

import pytest
import allure

from pages.home_page import HomePage
from utils import webview_a11y

logger = logging.getLogger(__name__)


@allure.epic("低空空管系统")
@allure.feature("首页模块")
@allure.story("通知模块切换")
@allure.title("顶部三个通知模块依次切换")
@pytest.mark.home
@pytest.mark.smoke
def test_notification_tabs_switch(fresh_logged_in_driver):
    """
    依次点击 计划审批 / 告警通知 / 管制员通知 三个模块

    预期: 每次切换后模块tab仍在页面 (无崩溃/无跳走), 截图留证。
    """
    home = HomePage(fresh_logged_in_driver)
    home.wait_for_home_page()

    for tab in [
        HomePage.NOTIFY_TAB_APPROVAL,
        HomePage.NOTIFY_TAB_ALERT,
        HomePage.NOTIFY_TAB_COORD,
    ]:
        with allure.step(f"切换模块: {tab}"):
            home.switch_notify_tab(tab)
            assert home.is_on_home_page(), f"切换 {tab} 后页面异常"
            logger.info(f"✅ {tab} 切换成功")
    home.take_screenshot("home_tabs_switch")


@allure.epic("低空空管系统")
@allure.feature("首页模块")
@allure.story("通知详情")
@allure.title("有消息内容时进入首条通知详情")
@pytest.mark.home
def test_notification_detail(fresh_logged_in_driver):
    """
    计划审批模块: 若存在消息卡片则点击进入详情, 返回后仍在首页

    预期: 无消息时跳过 (数据驱动的条件测试)。
    """
    home = HomePage(fresh_logged_in_driver)
    home.wait_for_home_page()

    with allure.step("1. 检查计划审批是否有消息"):
        if not home.has_notifications():
            logger.info("当前计划审批无消息内容, 跳过详情测试")
            pytest.skip("当前计划审批无消息内容")

    with allure.step("2. 点击首条通知进入详情"):
        home.open_first_notification()
        assert home.is_on_notification_detail(), "未进入通知详情页"
        logger.info("✅ 已进入通知详情")

    with allure.step("3. 返回首页"):
        home.go_back()
        assert home.is_on_home_page(), "返回后未回到首页"
        logger.info("✅ 返回首页成功")


@allure.epic("低空空管系统")
@allure.feature("首页模块")
@allure.story("知识助手")
@allure.title("知识助手入口可点击进入")
@pytest.mark.home
def test_ai_assistant_entry(fresh_logged_in_driver):
    """
    点击底部知识助手悬浮入口

    预期: 进入AI问答页 (功能开发中, 仅验证入口可进)。
    """
    home = HomePage(fresh_logged_in_driver)
    home.wait_for_home_page()

    with allure.step("1. 点击知识助手入口"):
        home.open_ai_assistant()

    with allure.step("2. 验证进入问答页"):
        assert home.is_on_ai_assistant(), "未进入知识助手问答页"
        logger.info("✅ 知识助手入口可用, 已进入问答页")
