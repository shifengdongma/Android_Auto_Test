# -*- coding: utf-8 -*-
"""
稳定性测试 - 自动化测试用例

测试范围:
    - Monkey压力测试 (随机事件注入)
    - Monkey + 性能采样组合
    - ANR检测器
    - Logcat抓取与Allure attach

说明:
    - monkey为破坏性/长耗时测试，全部 @pytest.mark.flaky(reruns=0) 防重跑放大压力
    - 目标App未安装时回退Chrome验证机制
    - 带 slow 标记

标记: @pytest.mark.stability / @pytest.mark.monkey
"""

import logging
import os
import time

import pytest
import allure

from utils.logcat import LogcatAnalyzer, LogcatCapture
from pages.login_page import LoginPage

logger = logging.getLogger(__name__)


# ============================================================
# Fixture
# ============================================================

@pytest.fixture(scope="module")
def stability_target(config, adb):
    """稳定性测试目标包解析 (优先config包名，回退Chrome)"""
    cfg_pkg = config.get("devices")[0].get("app_package", "com.dolphin.atc")
    for pkg in (cfg_pkg, "com.android.chrome"):
        if adb.is_app_installed(pkg):
            logger.info(f"稳定性测试目标: {pkg}")
            return pkg
    pytest.skip("目标App未安装且无Chrome可用于机制验证")


# ============================================================
# Monkey压力测试
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("稳定性测试")
@allure.story("Monkey压力")
@allure.title("Monkey冒烟 (200事件)")
@pytest.mark.stability
@pytest.mark.monkey
@pytest.mark.flaky(reruns=0)
@pytest.mark.slow
def test_monkey_smoke(adb, config, stability_target):
    """
    验证点:
        - monkey正常跑完 (Monkey finished)
        - 无CRASH/ANR
    """
    with allure.step("1. 运行monkey (200事件, 固定seed)"):
        result = adb.run_monkey(
            stability_target,
            events=200,
            seed=config.get("stability.monkey_seed", 42),
            throttle_ms=config.get("stability.monkey_throttle_ms", 300),
            timeout=300,
        )

    with allure.step("2. 验证无崩溃/ANR"):
        assert result["finished"], f"Monkey未正常结束: {result['raw_tail']}"
        assert not result["crashed"], f"Monkey出现崩溃: {result['raw_tail']}"
        assert not result["anr"], f"Monkey出现ANR: {result['raw_tail']}"

    allure.attach(result["raw_tail"], name="Monkey输出尾部", attachment_type=allure.attachment_type.TEXT)


@allure.epic("低空空管系统")
@allure.feature("稳定性测试")
@allure.story("Monkey压力")
@allure.title("Monkey压测 + 性能采样 (500事件)")
@pytest.mark.stability
@pytest.mark.monkey
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
@pytest.mark.slow
def test_monkey_with_perf_sampling(performance_collector, adb, config, stability_target):
    """
    验证点:
        - monkey运行期间持续采样性能
        - 无ANR/崩溃
        - 采样CSV生成
    """
    with allure.step("1. 启动性能采样"):
        performance_collector.start_sampling(stability_target, interval=2)

    with allure.step("2. 运行monkey (500事件)"):
        result = adb.run_monkey(
            stability_target,
            events=500,
            seed=config.get("stability.monkey_seed", 42),
            throttle_ms=config.get("stability.monkey_throttle_ms", 300),
            timeout=600,
        )

    with allure.step("3. 停止采样"):
        samples = performance_collector.stop_sampling()

    with allure.step("4. 验证压测结果"):
        assert not result["crashed"], f"Monkey出现崩溃: {result['raw_tail']}"
        assert not result["anr"], f"Monkey出现ANR: {result['raw_tail']}"
        assert len(samples) >= 1, "压测期间无采样数据"

    allure.attach(result["raw_tail"], name="Monkey输出尾部", attachment_type=allure.attachment_type.TEXT)


@allure.epic("低空空管系统")
@allure.feature("稳定性测试")
@allure.story("Monkey压力")
@allure.title("Monkey对不存在包容错")
@pytest.mark.stability
@pytest.mark.monkey
@pytest.mark.flaky(reruns=0)
def test_monkey_abort_on_wrong_package(adb):
    """
    验证点: 对不存在的包运行monkey不阻塞不报错 (容错路径)
    """
    with allure.step("1. 对不存在的包运行monkey"):
        result = adb.run_monkey("com.nonexistent.app.test", events=50, timeout=60)

    with allure.step("2. 验证容错行为"):
        # 包不存在时monkey可能aborted或finished，但不允许抛异常
        assert isinstance(result, dict), "monkey返回异常"
        logger.info(f"容错验证: finished={result['finished']} aborted={result['aborted']} crashed={result['crashed']}")


# ============================================================
# ANR检测与Logcat
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("稳定性测试")
@allure.story("ANR检测")
@allure.title("ANR检测器扫描正常场景无异常")
@pytest.mark.stability
@pytest.mark.flaky(reruns=0)
def test_anr_detector_scan(adb, config, stability_target):
    """
    验证点: 正常场景后扫描logcat，LogcatAnalyzer不应误报
    """
    analyzer = LogcatAnalyzer(stability_target)

    with allure.step("1. 清空logcat缓冲"):
        adb.clear_logcat()

    with allure.step("2. 快速启动/关闭应用几次"):
        for _ in range(3):
            adb.start_app(stability_target, ".MainActivity")
            time.sleep(0.5)
            adb.force_stop_app(stability_target)

    with allure.step("3. 扫描logcat"):
        capture = LogcatCapture(adb=adb)
        log_tail = capture.tail(lines=500, package=stability_target)
        hits = analyzer.scan(log_tail)
        assert not hits, f"正常场景误报异常: {hits}"

    logger.info("ANR检测器扫描通过: 无异常事件")


@allure.epic("低空空管系统")
@allure.feature("稳定性测试")
@allure.story("日志抓取")
@allure.title("Logcat抓取与Allure attach")
@pytest.mark.stability
def test_logcat_capture_and_attach(adb, config, driver):
    """
    验证点:
        - 抓取文件生成
        - 日志包含目标包名
        - Allure attach成功
    """
    pkg = config.get("devices")[0].get("app_package", "com.dolphin.atc")

    with allure.step("1. 启动logcat抓取"):
        capture = LogcatCapture(adb=adb)
        capture.start(pkg)

    with allure.step("2. 执行简单业务操作 (登录页加载)"):
        try:
            login_page = LoginPage(driver)
            login_page.wait_for_login_page(timeout=10)
        except Exception as e:
            logger.info(f"登录页加载(用于产生日志): {e}")

    with allure.step("3. 停止抓取并attach"):
        log_file = capture.stop()
        assert log_file, "日志文件未生成"
        assert os.path.exists(log_file), f"日志文件不存在: {log_file}"
        capture.attach("稳定性测试日志")

    with allure.step("4. 验证日志包含目标包"):
        content = open(log_file, encoding="utf-8", errors="replace").read()
        assert pkg in content, f"日志中未找到目标包 {pkg} 的日志"

    logger.info(f"Logcat抓取验证通过: {log_file}")
