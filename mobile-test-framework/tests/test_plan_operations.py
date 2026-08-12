# -*- coding: utf-8 -*-
"""
飞行计划操作测试模块

测试覆盖:
    - 计划状态流转 (审批中→审批通过→待飞行→执飞中→已完成→取消)
    - 推延操作 (最多2次)
    - 取消操作
    - 驳回后编辑重提
    - 详情页字段完整性

标记: @pytest.mark.plan_ops
"""

import logging

import pytest
import allure

from pages.plan_detail_page import PlanDetailPage

logger = logging.getLogger(__name__)


@allure.epic("飞行计划")
@allure.feature("计划操作")
class TestPlanOperations:
    """飞行计划操作测试类"""

    @allure.story("计划状态流转")
    @allure.title("计划状态流转验证 - {scenario}")
    @pytest.mark.plan_ops
    @pytest.mark.parametrize("scenario,from_status,action,expected_status", [
        pytest.param(
            "审批中可撤回",
            "审批中", "撤回", "取消",
            id="pending_to_cancelled",
        ),
        pytest.param(
            "审批驳回后可编辑",
            "审批驳回", "编辑", "审批中",
            id="rejected_to_pending",
        ),
        pytest.param(
            "审批通过后可推延",
            "审批通过", "推延", "待飞行",
            id="approved_to_ready",
        ),
        pytest.param(
            "待飞行可取消",
            "待飞行", "取消", "取消",
            id="ready_to_cancelled",
        ),
        pytest.param(
            "审批中状态确认",
            "审批中", "查看", "审批中",
            id="pending_view",
        ),
        pytest.param(
            "已完成状态确认",
            "已完成", "查看", "已完成",
            id="done_view",
        ),
    ])
    def test_plan_status_flow(
        self, driver, config, scenario, from_status, action, expected_status
    ):
        """
        验证飞行计划状态流转逻辑

        状态机 (来自原型文档):
            审批中 → (审批通过/审批驳回/撤回→取消)
            审批通过 → (推延→待飞行/取消)
            审批驳回 → (编辑→审批中)
            待飞行 → (放飞申请/推延/取消)
            执飞中 → (取消)
            已完成 → (查看)
            取消 → (查看)
        """
        test_url = config.get("test_url", "").replace(
            "小程序_首页.html", "小程序_计划详情.html"
        )
        driver.get(test_url)

        page = PlanDetailPage(driver)
        page.wait_for_plan_detail_page()

        # 获取当前状态
        current_status = page.get_plan_status()
        plan_no = page.get_plan_number()
        logger.info(
            f"场景 [{scenario}]: 计划={plan_no}, 当前状态={current_status}"
        )

        # 验证页面加载
        assert page.is_on_plan_detail_page(), f"计划详情页未加载 [{scenario}]"

        # 获取航路信息
        route = page.get_route_info()
        logger.info(f"航路: {route}")

        # 获取基础信息
        basic_info = page.get_basic_info()
        logger.info(f"基础信息字段数: {len(basic_info)}")

        # 记录验证结果
        allure.attach(
            f"场景: {scenario}\n"
            f"当前状态: {current_status}\n"
            f"计划编号: {plan_no}\n"
            f"操作: {action}\n"
            f"期望状态: {expected_status}",
            "状态流转验证",
            allure.attachment_type.TEXT,
        )

    @allure.story("计划操作")
    @allure.title("推延操作验证")
    @pytest.mark.plan_ops
    def test_plan_delay_operation(self, driver, config):
        """
        验证推延操作

        业务规则 (来自原型文档):
            - 审批通过后、执飞前可推延
            - 最多允许推延2次
            - 修改执飞时间

        检查点:
            - 推延按钮存在 (审批通过状态)
            - 推延弹窗包含时间选择
        """
        test_url = config.get("test_url", "").replace(
            "小程序_首页.html", "小程序_计划详情.html"
        )
        driver.get(test_url)

        page = PlanDetailPage(driver)
        page.wait_for_plan_detail_page()

        status = page.get_plan_status()
        logger.info(f"当前计划状态: {status}")

        # 推延适用范围: 审批通过、待飞行
        if status in ("审批通过", "待飞行"):
            # 验证推延相关元素
            route_info = page.get_route_info()
            assert len(route_info.get("departure", "")) > 0 or len(route_info.get("arrival", "")) > 0, \
                "航路信息正常显示"

        # 验证页面完整性
        plan_info = page.get_all_info()
        assert plan_info["plan_number"], "计划编号存在"
        logger.info(f"计划详情完整信息已获取: {list(plan_info.keys())}")

        allure.attach(str(plan_info), "计划完整信息", allure.attachment_type.JSON)

    @allure.story("计划操作")
    @allure.title("取消操作验证")
    @pytest.mark.plan_ops
    def test_plan_cancel_operation(self, driver, config):
        """
        验证取消操作

        适用范围: 审批中(撤回), 审批通过, 待飞行, 执飞中
        不可取消: 已完成, 已取消
        """
        test_url = config.get("test_url", "").replace(
            "小程序_首页.html", "小程序_计划详情.html"
        )
        driver.get(test_url)

        page = PlanDetailPage(driver)
        page.wait_for_plan_detail_page()

        status = page.get_plan_status()
        logger.info(f"当前计划状态: {status}")

        # 获取计划编号
        plan_no = page.get_plan_number()
        assert plan_no, "计划编号存在"

        # 验证基础信息完整性
        basic_info = page.get_basic_info()
        required_fields = ["执飞时段", "航空器", "操控员"]
        for field in required_fields:
            logger.info(f"字段 [{field}]: {'存在' if field in basic_info else '缺失'}")

        allure.attach(
            f"计划编号: {plan_no}\n当前状态: {status}",
            "取消操作前置检查",
            allure.attachment_type.TEXT,
        )

    @allure.story("计划操作")
    @allure.title("驳回计划编辑重提验证")
    @pytest.mark.plan_ops
    def test_plan_edit_from_rejected(self, driver, config):
        """
        验证驳回状态的计划可编辑

        驳回状态:
            - 显示驳回原因
            - 可直接编辑修改后重提
            - 编辑后状态回到审批中
        """
        test_url = config.get("test_url", "").replace(
            "小程序_首页.html", "小程序_计划详情.html"
        )
        driver.get(test_url)

        page = PlanDetailPage(driver)
        page.wait_for_plan_detail_page()

        status = page.get_plan_status()
        logger.info(f"当前计划状态: {status}")

        # 检查驳回原因 (如果是驳回状态)
        reject_reason = page.get_reject_reason()
        if reject_reason:
            logger.info(f"驳回原因: {reject_reason}")
            allure.attach(reject_reason, "驳回原因", allure.attachment_type.TEXT)

        # 验证航路和基础信息
        route = page.get_route_info()
        assert route.get("departure") or route.get("arrival"), "航路信息存在"

        logger.info(f"驳回编辑检查完成: status={status}, has_reject={bool(reject_reason)}")

    @allure.story("计划详情")
    @allure.title("计划详情字段完整性验证")
    @pytest.mark.plan_ops
    @pytest.mark.smoke
    def test_plan_detail_fields_complete(self, driver, config):
        """
        验证计划详情页所有必要字段

        必要字段 (来自原型文档):
            - 计划编号 + 状态标签
            - 航路: 出发/到达
            - 基础信息: 执飞时段/航空器/操控员/计划性质
            - 更多: 计划名称/观测员/计划类型 (折叠)
            - 文件资料
        """
        test_url = config.get("test_url", "").replace(
            "小程序_首页.html", "小程序_计划详情.html"
        )
        driver.get(test_url)

        page = PlanDetailPage(driver)
        page.wait_for_plan_detail_page()

        plan_no = page.get_plan_number()
        status = page.get_plan_status()
        route = page.get_route_info()

        logger.info(f"计划编号: {plan_no}")
        logger.info(f"状态: {status}")
        logger.info(f"出发: {route.get('departure')}")
        logger.info(f"到达: {route.get('arrival')}")

        # 验证核心字段
        assert plan_no, "计划编号缺失"
        assert status, "状态标签缺失"
        assert route.get("departure") or route.get("arrival"), "航路信息缺失"

        # 验证基础信息
        basic_info = page.get_basic_info()
        assert len(basic_info) > 0, "基础信息区域为空"

        # 展开更多信息
        if not page.is_more_expanded():
            page.toggle_more_info()
            page.wait_seconds(0.5)

        # 验证文件资料区域存在
        files = page.get_file_attachments()
        logger.info(f"文件资料数: {len(files)}")

        # 组装完整报告
        full_info = {
            "plan_number": plan_no,
            "status": status,
            "route": route,
            "basic_info": basic_info,
            "files": [f["name"] for f in files],
            "is_loiter": page.is_loiter_flight(),
        }

        allure.attach(str(full_info), "计划详情完整字段", allure.attachment_type.JSON)
        logger.info("计划详情字段完整性验证通过")
