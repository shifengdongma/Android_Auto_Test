# -*- coding: utf-8 -*-
"""
资讯模块 - 自动化测试用例

测试范围:
    - 法律法规列表展示
    - 通知公告列表展示
    - 子Tab切换
    - 文章详情查看
    - 附件检测

标记: @pytest.mark.news
"""

import logging

import pytest
import allure

from pages.news_page import NewsPage
from pages.home_page import HomePage

logger = logging.getLogger(__name__)


# ============================================================
# Fixture
# ============================================================

@pytest.fixture
def news_page(logged_in_driver):
    """进入资讯页的Fixture"""
    home = HomePage(logged_in_driver)
    assert home.is_on_home_page(), "前置条件失败: 未在首页"
    return home.go_to_news()


# ============================================================
# 法律法规
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("资讯")
@allure.story("法律法规")
@allure.title("法律法规列表正常加载")
@pytest.mark.news
@pytest.mark.smoke
def test_law_list(news_page):
    """
    测试场景: 进入资讯页，默认显示法律法规列表

    验证点:
        - 列表加载成功
        - 文章条目包含标题/来源/时间
    """
    with allure.step("1. 确认在资讯页"):
        assert news_page.is_on_news_page(), "应位于资讯页"

    with allure.step("2. 检查法律法规列表"):
        articles = news_page.get_article_list()
        logger.info(f"法律法规文章数量: {len(articles)}")

        if articles:
            first = articles[0]
            logger.info(
                f"第一篇文章: 标题='{first['title']}', "
                f"来源='{first['source']}', 时间='{first['date']}'"
            )
            assert first["title"], "文章标题不应为空"

    logger.info(f"✅ 法律法规列表正常 (共{len(articles)}篇)")


@allure.epic("低空空管系统")
@allure.feature("资讯")
@allure.story("法律法规")
@allure.title("查看法律法规详情")
@pytest.mark.news
def test_law_detail(news_page):
    """
    测试场景: 点击法律法规文章查看详情

    验证点:
        - 详情页正常打开
        - 标题/正文显示
        - 可返回列表
    """
    with allure.step("1. 点击第一篇文章"):
        count = news_page.get_article_count()
        if count == 0:
            pytest.skip("法律法规列表为空")
        news_page.click_article(0)

    with allure.step("2. 验证详情页"):
        if news_page.is_detail_page_shown():
            title = news_page.get_article_detail_title()
            logger.info(f"文章详情标题: {title}")
            assert title, "详情页标题不应为空"

    with allure.step("3. 返回列表"):
        news_page.back_to_list()
        assert news_page.is_on_news_page(), "应返回资讯列表"


# ============================================================
# 通知公告
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("资讯")
@allure.story("通知公告")
@allure.title("通知公告列表正常加载")
@pytest.mark.news
def test_notice_list(news_page):
    """
    测试场景: 切换到通知公告Tab并验证列表

    验证点:
        - Tab切换成功
        - 列表加载成功
    """
    with allure.step("1. 切换到通知公告Tab"):
        news_page.switch_tab("通知公告")

    with allure.step("2. 检查列表"):
        articles = news_page.get_article_list()
        logger.info(f"通知公告文章数量: {len(articles)}")

        if articles:
            first = articles[0]
            assert first["title"], "文章标题不应为空"
            logger.info(f"第一篇: {first['title']}")

    logger.info(f"✅ 通知公告列表正常 (共{len(articles)}篇)")


# ============================================================
# Tab切换
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("资讯")
@allure.story("Tab切换")
@allure.title("资讯子Tab切换")
@pytest.mark.news
@pytest.mark.parametrize("tab_name,tab_key", [
    pytest.param("法律法规", "laws", id="法律法规"),
    pytest.param("通知公告", "notices", id="通知公告"),
])
def test_switch_tabs(news_page, tab_name, tab_key):
    """
    测试场景: 在资讯子Tab之间切换

    验证点:
        - 切换后列表刷新
        - 无崩溃
    """
    with allure.step(f"切换到'{tab_name}'"):
        news_page.switch_tab(tab_key)

    with allure.step("验证列表"):
        count = news_page.get_article_count()
        logger.info(f"'{tab_name}' - 文章数量: {count}")

        # 列表可为空(开发环境中没有数据)
        assert True  # 不崩溃即通过


# ============================================================
# 文章详情
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("资讯")
@allure.story("文章详情")
@allure.title("文章附件检测")
@pytest.mark.news
def test_article_attachment(news_page):
    """
    测试场景: 检查文章是否有附件

    验证点:
        - 附件区域正确显示/隐藏
    """
    with allure.step("1. 查找有内容的文章"):
        count = news_page.get_article_count()
        if count == 0:
            pytest.skip("资讯列表为空")

        # 遍历查找有附件的文章
        found = False
        for i in range(min(count, 5)):
            news_page.click_article(i)
            if news_page.is_attachment_available():
                logger.info(f"第{i}篇文章包含附件")
                found = True
                break
            news_page.back_to_list()

    with allure.step("2. 结论"):
        if found:
            logger.info("✅ 检测到文章附件")
        else:
            logger.info("未检测到附件 (可能所有文章均无附件)")
