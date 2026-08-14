# -*- coding: utf-8 -*-
"""
资讯模块 - 自动化测试用例 (真机校准版)

测试范围 (按真实应用流程):
    - 顶部三个功能模块切换: 法律法规 / 通知公告 / 系统公告

标记: @pytest.mark.news

前置: fresh_logged_in_driver (清数据+登录, 保证a11y树确定性)
"""

import logging

import pytest
import allure

from pages.news_page import NewsPage
from utils import webview_a11y

logger = logging.getLogger(__name__)


@allure.epic("低空空管系统")
@allure.feature("资讯模块")
@allure.story("功能模块切换")
@allure.title("法律法规/通知公告/系统公告依次切换")
@pytest.mark.news
@pytest.mark.smoke
def test_news_tabs_switch(fresh_logged_in_driver):
    """
    依次点击 法律法规 / 通知公告 / 系统公告 三个功能模块

    预期: 每次切换后模块tab仍在页面 (无崩溃/无跳走), 截图留证。
    """
    ok = webview_a11y.switch_tab(
        fresh_logged_in_driver, "资讯", marker=NewsPage.TAB_LAW
    )
    assert ok, "未能切换到资讯页"

    news = NewsPage(fresh_logged_in_driver)
    for tab in NewsPage.TABS:
        with allure.step(f"切换模块: {tab}"):
            news.switch_tab(tab)
            assert news.is_tab_present(tab), f"切换 {tab} 后tab不在页面"
            if news.has_empty_state():
                logger.info(f"✅ {tab} 切换成功 (当前暂无数据)")
            else:
                logger.info(f"✅ {tab} 切换成功 (有内容)")
    news.take_screenshot("news_tabs_switch")
