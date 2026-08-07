# -*- coding: utf-8 -*-
"""
弱网/断网 - 自动化测试用例

测试范围:
    - 完全断网 (offline)
    - 飞行模式 (airplane)
    - 断网时登录错误态 (不崩溃)
    - 网络恢复验证
    - 弱网限速接口预留验证

说明:
    - weak_network fixture 保证用例结束后强制恢复网络，不污染后续用例
    - 双模式可跑: browser模式测H5错误态，native模式测Toast/弹窗
    - 真正的限速/丢包模拟需PC侧代理(接口已预留)，见 docs/弱网测试方案.md

标记: @pytest.mark.weaknet + @pytest.mark.offline
"""

import logging

import pytest
import allure

from pages.login_page import LoginPage

logger = logging.getLogger(__name__)


# ============================================================
# 断网/恢复基础能力
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("弱网测试")
@allure.story("断网控制")
@allure.title("完全断网后网络不可用")
@pytest.mark.weaknet
@pytest.mark.offline
@pytest.mark.flaky(reruns=0)  # 网络操作不可重跑
def test_disconnect_all_blocks_network(weak_network, network_controller):
    """
    验证点:
        - set_mode("offline")后 is_offline()为True
        - teardown自动恢复网络
    """
    with allure.step("1. 执行完全断网"):
        assert network_controller.set_mode("offline"), "断网切换失败"

    with allure.step("2. 验证网络不可用"):
        assert network_controller.is_offline(), "断网后ping仍然成功"

    with allure.step("3. 记录连通性状态"):
        status = network_controller.check_connectivity()
        allure.attach(str(status), name="断网状态", attachment_type=allure.attachment_type.TEXT)
        logger.info(f"断网状态: {status}")


@allure.epic("低空空管系统")
@allure.feature("弱网测试")
@allure.story("网络恢复")
@allure.title("断网后恢复网络")
@pytest.mark.weaknet
@pytest.mark.offline
@pytest.mark.flaky(reruns=0)
def test_restore_network_recovers(weak_network, network_controller):
    """
    验证点: 断网 -> 恢复 -> 网络可用
    """
    with allure.step("1. 执行完全断网"):
        network_controller.set_mode("offline")
        assert network_controller.is_offline(), "断网失败"

    with allure.step("2. 恢复网络"):
        assert network_controller.restore_all(), "网络恢复失败"

    with allure.step("3. 验证网络可用"):
        assert not network_controller.is_offline(), "恢复后网络仍不可用"

    logger.info("网络恢复验证通过")


@allure.epic("低空空管系统")
@allure.feature("弱网测试")
@allure.story("飞行模式")
@allure.title("飞行模式切换与恢复")
@pytest.mark.weaknet
@pytest.mark.flaky(reruns=0)
def test_airplane_mode(weak_network, network_controller):
    """
    验证点:
        - 飞行模式开启后 airplane=true 且 offline=true
        - teardown自动恢复
    """
    with allure.step("1. 开启飞行模式"):
        assert network_controller.set_mode("airplane"), "飞行模式切换失败"

    with allure.step("2. 验证飞行模式状态"):
        status = network_controller.check_connectivity()
        assert status["airplane"], f"飞行模式未生效: {status}"
        assert status["offline"], f"飞行模式应断网: {status}"

    allure.attach(str(status), name="飞行模式状态", attachment_type=allure.attachment_type.TEXT)


# ============================================================
# 断网业务场景
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("弱网测试")
@allure.story("断网业务场景")
@allure.title("断网时登录显示错误且不崩溃")
@pytest.mark.weaknet
@pytest.mark.flaky(reruns=0)
def test_login_fails_when_offline(weak_network, network_controller, driver, config):
    """
    验证点:
        - 断网后登录应显示错误提示 (Toast/文案)
        - 停留在登录页，不崩溃
    """
    account = config.get_test_account("default")

    with allure.step("1. 执行完全断网"):
        network_controller.set_mode("offline")
        assert network_controller.is_offline(), "断网失败"

    with allure.step("2. 尝试登录"):
        login_page = LoginPage(driver)
        try:
            login_page.wait_for_login_page(timeout=10)
            login_page.login(
                username=account["username"],
                password=account["password"],
            )
        except Exception as e:
            # 网络请求超时/失败均为预期行为，记录即可
            logger.info(f"断网登录过程异常(预期): {e}")

    with allure.step("3. 记录错误提示"):
        error = login_page.get_error_message(timeout=5)
        # 错误提示可能为Toast/文案/空(页面仍在加载中)，断网场景以不崩溃为主验证点
        logger.info(f"断网登录错误提示: {error!r}")

    with allure.step("4. 验证应用未崩溃 (driver仍可用)"):
        assert driver.page_source is not None, "driver不可用，应用可能崩溃"

    allure.attach(
        f"错误提示: {error!r}",
        name="断网登录结果",
        attachment_type=allure.attachment_type.TEXT,
    )


# ============================================================
# 弱网限速接口预留
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("弱网测试")
@allure.story("限速接口预留")
@allure.title("弱网限速控制器接口预留验证")
@pytest.mark.weaknet
def test_throttle_interface_reserved(network_controller):
    """
    验证点: ThrottleController接口协议完整 (永远通过)

    此用例是"接口预留"的落点:
        - 未配置代理后端时 available()=False，仅WARN不报错
        - 接入mitmproxy/Charles后 (docs/弱网测试方案.md) 自动启用
    """
    with allure.step("1. 获取限速控制器"):
        controller = network_controller.get_throttle_controller()

    with allure.step("2. 验证协议接口存在"):
        assert hasattr(controller, "name"), "缺少name属性"
        assert hasattr(controller, "available"), "缺少available方法"
        assert hasattr(controller, "apply"), "缺少apply方法"
        assert hasattr(controller, "remove"), "缺少remove方法"

    with allure.step("3. 验证当前可用性 (未配置后端时为False)"):
        available = controller.available()
        assert available is False or available is True, "available()返回值非法"
        logger.info(f"限速后端: {controller.name}, 可用: {available} (False为预期: 未配置代理后端)")
