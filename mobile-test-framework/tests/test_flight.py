# -*- coding: utf-8 -*-
"""
飞行计划(申报)模块 - 自动化测试用例 (真机校准版)

测试范围 (按真实应用流程):
    - 起飞地/降落地/备降地 搜索选择 (关键词过滤 + 列表选择)
    - 出发时间修改 (选完机场后出现的表单步骤)
    - 下一步 -> 航空器/操作员选择 -> 完成计划
    - 留空飞行: 三种空域绘制 (多边形/圆形/线缓冲区) -> 命名 -> 下一步 -> 完成计划
    - 我的计划入口与列表展示

标记: @pytest.mark.flight

前置: fresh_logged_in_driver (清数据+登录, 保证a11y树确定性)
"""

import logging

import pytest
import allure

from pages.flight_page import FlightPage
from utils import webview_a11y

logger = logging.getLogger(__name__)


def _goto_flight(driver) -> FlightPage:
    ok = webview_a11y.switch_tab(
        driver, "申报", marker=FlightPage.FIELD_DEPART
    )
    assert ok, "未能切换到申报页"
    return FlightPage(driver)


@allure.epic("低空空管系统")
@allure.feature("申报模块")
@allure.story("起降场搜索选择")
@allure.title("起降场关键词搜索并选择")
@pytest.mark.flight
@pytest.mark.smoke
def test_airport_search_select(fresh_logged_in_driver):
    """
    起飞地: 搜索"新疆" -> 选择"新疆起降场1"
    降落地: 搜索"新疆" -> 选择"新疆起降场2"

    预期: 两个字段值均更新为所选起降场。
    """
    flight = _goto_flight(fresh_logged_in_driver)

    with allure.step("1. 起飞地搜索选择 新疆起降场1"):
        assert flight.select_depart(), "起飞地选择失败"
        logger.info("✅ 起飞地 = 新疆起降场1")

    with allure.step("2. 降落地搜索选择 新疆起降场2"):
        assert flight.select_arrive(), "降落地选择失败"
        logger.info("✅ 降落地 = 新疆起降场2")

    flight.take_screenshot("flight_airports_selected")


@allure.epic("低空空管系统")
@allure.feature("申报模块")
@allure.story("完整计划流程")
@allure.title("飞行计划完整创建流程")
@pytest.mark.flight
def test_full_plan_creation(fresh_logged_in_driver):
    """
    完整计划创建 (真机实测流程):
        1. 起飞地=新疆起降场1 / 降落地=新疆起降场2 / 备降地=新疆起降场2
        2. 修改出发时间 -> 04:00
        3. 下一步 -> 填写飞行计划 (航空器/操控员/任务性质)
        4. 选择航空器/操控员 (底部弹层首项)
        5. 提交 -> 确认弹窗点确定 -> 我的计划页

    预期: 每步表单状态正确推进, 提交无异常。
    """
    flight = _goto_flight(fresh_logged_in_driver)

    with allure.step("1. 选择起降场 (起飞地/降落地/备降地)"):
        assert flight.select_depart(), "起飞地选择失败"
        assert flight.select_arrive(), "降落地选择失败"
        assert flight.select_alternate(), "备降地选择失败"
        logger.info("✅ 三个起降场选择完成")

    with allure.step("2. 修改出发时间为 04:00"):
        assert flight.modify_departure_time("04:00"), "出发时间修改失败"
        logger.info("✅ 出发时间已修改")

    with allure.step("3. 下一步 -> 填写飞行计划页"):
        assert flight.click_next_step(), "未进入填写飞行计划页"
        logger.info("✅ 已进入填写飞行计划页")

    with allure.step("4. 选择航空器与操控员"):
        assert flight.select_aircraft(), "航空器选择失败"
        assert flight.select_operator(), "操控员选择失败"
        logger.info("✅ 航空器/操控员已选择")

    with allure.step("5. 提交计划 (含确认弹窗点确定)"):
        assert flight.submit_plan(), "提交失败"
        flight.take_screenshot("flight_submitted")
        logger.info("✅ 提交完成, 已进入我的计划")


@allure.epic("低空空管系统")
@allure.feature("申报模块")
@allure.story("留空飞行")
@allure.title("留空飞行空域绘制与计划创建")
@pytest.mark.flight
def test_loiter_flight_creation(fresh_logged_in_driver):
    """
    留空飞行完整流程 (真机实测):
        1. 申报页点击"留空飞行" -> 空域绘制页
        2. 三种空域各绘制一次:
           多边形 (单击加点/双击结束) -> 圆形 (长按拖动) -> 线缓冲区 (单击/双击)
        3. 最终用多边形画三角形空域
        4. 输入空域名称"测试" (输入后关闭输入法键盘)
        5. 修改出发时间 -> 04:30
        6. 下一步 -> 填写飞行计划 (与普通申报流程一致)
        7. 航空器/操控员选择 -> 提交 (确认弹窗点确定)

    预期: 各步表单正确推进, 提交后进入我的计划页。
    """
    flight = _goto_flight(fresh_logged_in_driver)
    loiter = flight.enter_loiter_flight()

    with allure.step("1. 三种空域各绘制一次"):
        assert loiter.select_type("多边形"), "多边形类型选择失败"
        assert loiter.draw_polygon(), "多边形绘制失败"
        assert loiter.select_type("圆形"), "圆形类型选择失败"
        assert loiter.draw_circle(), "圆形绘制失败"
        assert loiter.select_type("线缓冲区"), "线缓冲区类型选择失败"
        assert loiter.draw_buffer(), "线缓冲区绘制失败"
        logger.info("✅ 三种空域绘制尝试完成")

    with allure.step("2. 最终用多边形(三角形)绘制空域"):
        assert loiter.select_type("多边形"), "回到多边形类型失败"
        assert loiter.draw_polygon(), "最终三角形绘制失败"
        logger.info("✅ 三角形空域绘制完成")

    with allure.step("3. 输入空域名称: 测试"):
        assert loiter.input_airspace_name("测试"), "空域名称输入失败"
        logger.info("✅ 空域名称已输入 (键盘已关闭)")

    with allure.step("4. 修改出发时间为 04:30"):
        assert loiter.modify_departure_time("04:30"), "出发时间修改失败"
        logger.info("✅ 出发时间已修改")

    with allure.step("5. 下一步 -> 填写飞行计划页"):
        assert loiter.click_next_step(), "未进入填写飞行计划页"
        logger.info("✅ 已进入填写飞行计划页")

    with allure.step("6. 选择航空器与操控员"):
        assert loiter.select_aircraft(), "航空器选择失败"
        assert loiter.select_operator(), "操控员选择失败"
        logger.info("✅ 航空器/操控员已选择")

    with allure.step("7. 提交计划 (含确认弹窗点确定)"):
        assert loiter.submit_plan(), "提交失败"
        loiter.take_screenshot("loiter_submitted")
        logger.info("✅ 留空飞行计划提交完成")


@allure.epic("低空空管系统")
@allure.feature("申报模块")
@allure.story("我的计划")
@allure.title("我的计划入口与列表展示")
@pytest.mark.flight
@pytest.mark.smoke
def test_my_plans_entry(fresh_logged_in_driver):
    """
    申报页底部"我的计划"入口:
        点击后进入计划列表页, 列表含状态筛选器与计划卡片。

    预期: 页面标题"我的计划" + 顶部"全部状态"筛选器出现。
    """
    flight = _goto_flight(fresh_logged_in_driver)

    with allure.step("1. 点击我的计划"):
        assert flight.open_my_plans(), "未进入我的计划页"
        logger.info("✅ 已进入我的计划页")

    with allure.step("2. 验证列表页特征"):
        assert flight.has_text("全部状态", timeout=5), "未找到状态筛选器"
        flight.take_screenshot("my_plans_list")
        logger.info("✅ 我的计划列表展示正常")
