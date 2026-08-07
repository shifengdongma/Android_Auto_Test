# -*- coding: utf-8 -*-
"""
性能采集 - 自动化测试用例

测试范围:
    - CPU/内存/电量快照
    - 冷启动阈值校验
    - 页面操作响应时间
    - 定时采样场景
    - 阈值策略与CSV编码

说明:
    - 默认warn_only策略(超阈值仅提示不失败)，--perf-strict可切换严格模式
    - 目标App未安装时自动回退Chrome验证机制
    - 性能数据不可重跑，全部使用 @pytest.mark.flaky(reruns=0)

标记: @pytest.mark.perf
"""

import glob
import logging
import time
from datetime import datetime
from pathlib import Path

import pytest
import allure

from pages.home_page import HomePage

logger = logging.getLogger(__name__)


# ============================================================
# Fixture
# ============================================================

@pytest.fixture(scope="module")
def perf_target(config, adb):
    """
    性能测试目标包解析: 优先config包名(已安装)，回退Chrome

    Returns:
        str: 包名
    """
    cfg_pkg = config.get("devices")[0].get("app_package", "com.dolphin.atc")
    for pkg in (cfg_pkg, "com.android.chrome"):
        if adb.is_app_installed(pkg):
            logger.info(f"性能测试目标: {pkg}")
            return pkg
    pytest.skip("目标App未安装且无Chrome可用于机制验证")


# ============================================================
# 快照采集
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("CPU采集")
@allure.title("CPU占用快照")
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
def test_cpu_snapshot(performance_collector, perf_target):
    """
    验证点: CPU快照返回合法数值 (可能为0/None，不抛异常)
    """
    with allure.step("1. 采集CPU快照"):
        snap = performance_collector.snapshot_cpu(perf_target)

    with allure.step("2. 验证快照结构"):
        assert "cpu_percent" in snap, "缺少cpu_percent字段"
        if snap["cpu_percent"] is not None:
            assert 0 <= snap["cpu_percent"] <= 100, f"CPU占比异常: {snap['cpu_percent']}"

    allure.attach(str(snap), name="CPU快照", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"CPU快照: {snap}")


@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("内存采集")
@allure.title("内存占用快照")
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
def test_memory_snapshot(performance_collector, perf_target):
    """
    验证点: 内存快照返回TOTAL PSS (Android 8+)
    """
    with allure.step("1. 采集内存快照"):
        snap = performance_collector.snapshot_memory(perf_target)

    with allure.step("2. 验证快照结构"):
        assert "total_pss_kb" in snap, "缺少total_pss_kb字段"
        if snap["total_pss_kb"] is not None:
            assert snap["total_pss_kb"] > 0, f"内存异常: {snap['total_pss_kb']}"

    allure.attach(str(snap), name="内存快照", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"内存快照: {snap}")


@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("电量采集")
@allure.title("电量快照")
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
def test_battery_snapshot(performance_collector):
    """
    验证点: 电量level在0-100，状态可读
    """
    with allure.step("1. 采集电量快照"):
        snap = performance_collector.snapshot_battery()

    with allure.step("2. 验证快照结构"):
        assert snap["level"] is not None, "未获取到电量"
        assert 0 <= snap["level"] <= 100, f"电量异常: {snap['level']}"
        assert snap["status_text"] != "unknown", "电量状态未知"

    allure.attach(str(snap), name="电量快照", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"电量快照: {snap}")


# ============================================================
# 启动耗时与阈值
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("启动耗时")
@allure.title("冷启动耗时阈值校验")
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
def test_startup_cold_with_threshold(app_lifecycle, performance_collector, config, adb, perf_target):
    """
    验证点:
        - 3轮冷启动测量有数据
        - 阈值校验结果合法 (ok/warn，默认不失败)
    """
    # 解析Activity
    info = adb.get_app_info(perf_target)
    activity = info.get("main_activity") if info.get("main_activity") not in (None, "unknown") else ".MainActivity"

    with allure.step("1. 测量3轮冷启动"):
        stats = app_lifecycle.cold_start_time(perf_target, activity, rounds=3)

    with allure.step("2. 验证有有效数据"):
        assert stats["values"], f"无有效启动数据: {stats}"

    with allure.step("3. 阈值校验"):
        result = performance_collector.check_threshold("cold_start_ms", stats["median"])
        assert result in ("ok", "warn"), f"strict模式超阈值: {stats['median']}ms"

    with allure.step("4. 写入CSV"):
        path = performance_collector.write_csv(
            [{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "test_name": "test_startup_cold_with_threshold",
                "metric": "cold_start_ms",
                "value": stats["median"],
                "result": result,
                "package": perf_target,
            }]
        )
        assert path, "CSV写入失败"

    allure.attach(str(stats), name="冷启动耗时统计", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"冷启动: median={stats['median']}ms result={result}")


@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("操作响应时间")
@allure.title("页面操作响应时间 (timer)")
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
def test_page_operation_response(performance_collector, logged_in_driver):
    """
    验证点: timer上下文管理器能记录页面操作耗时

    场景: 登录后等待首页加载
    """
    with allure.step("1. 使用timer计时首页加载"):
        with performance_collector.timer("首页加载"):
            home = HomePage(logged_in_driver)
            home.is_on_home_page()

    elapsed = performance_collector._samples[-1]
    with allure.step("2. 验证计时结果"):
        assert elapsed["value"] >= 0, "计时结果为负"
        assert elapsed["metric"] == "operation_response_ms"

    allure.attach(str(elapsed), name="操作响应时间", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"首页加载耗时: {elapsed['value']}ms")


# ============================================================
# 定时采样
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("定时采样")
@allure.title("场景期间定时采样 (CPU/内存/电量)")
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
def test_sampling_during_scenario(performance_collector, perf_target):
    """
    验证点:
        - 采样期间样本数>=3
        - 生成CSV文件
    """
    with allure.step("1. 启动定时采样 (interval=1s, duration=5s)"):
        performance_collector.start_sampling(perf_target, interval=1, duration=5)

    with allure.step("2. 执行场景动作 (等待5秒模拟操作)"):
        time.sleep(5)

    with allure.step("3. 停止采样"):
        samples = performance_collector.stop_sampling()

    with allure.step("4. 验证采样结果"):
        assert len(samples) >= 3, f"采样样本过少: {len(samples)}"
        # 校验CSV文件已生成
        csv_files = glob.glob(
            str(Path(__file__).parent.parent / "reports" / "performance" / "perf_*.csv")
        )
        assert csv_files, "未生成性能CSV"

    logger.info(f"采样完成: {len(samples)}个样本")


# ============================================================
# 阈值策略与CSV
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("阈值策略")
@allure.title("阈值策略: warn_only默认不失败")
@pytest.mark.perf
def test_threshold_policy_warn_only(performance_collector, request):
    """
    验证点:
        - 默认warn_only: 超阈值返回warn
        - --perf-strict: 超阈值返回fail
    """
    # 构造必然超限的值
    huge_value = performance_collector._thresholds.get("memory_mb", 500) * 100

    with allure.step("1. 检查策略配置"):
        strict = request.config.getoption("--perf-strict", default=False)

    with allure.step("2. 执行阈值校验"):
        result = performance_collector.check_threshold("memory_mb", huge_value)

    if strict:
        assert result == "fail", f"strict模式应返回fail，实际: {result}"
    else:
        assert result == "warn", f"warn_only模式应返回warn，实际: {result}"


@allure.epic("低空空管系统")
@allure.feature("性能测试")
@allure.story("CSV输出")
@allure.title("CSV编码为utf-8-sig (Excel兼容)")
@pytest.mark.perf
def test_csv_encoding_utf8_sig(performance_collector):
    """
    验证点: CSV文件带BOM头 (0xEF 0xBB 0xBF)，Excel可直接打开不乱码
    """
    path = performance_collector.write_csv(
        [{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "test_name": "test_csv_encoding",
            "metric": "cpu_percent",
            "value": 10,
            "result": "ok",
        }]
    )
    assert path, "CSV写入失败"

    with open(path, "rb") as f:
        head = f.read(3)
    assert head == b"\xef\xbb\xbf", f"CSV缺少BOM头: {head.hex()}"
    logger.info(f"CSV编码验证通过: {path}")
