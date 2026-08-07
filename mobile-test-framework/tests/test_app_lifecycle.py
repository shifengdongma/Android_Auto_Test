# -*- coding: utf-8 -*-
"""
App生命周期 - 自动化测试用例

测试范围:
    - 冷启动 (耗时测量 + 进程存活)
    - 关闭应用
    - 后台运行 / 回前台
    - 冷/热启动耗时统计

说明:
    - 目标App未安装时自动回退到Chrome(com.android.chrome)验证机制，
      APK就绪后自动切换为目标App，无需改代码
    - 全部基于ADB，不依赖driver

标记: @pytest.mark.lifecycle
"""

import logging
from datetime import datetime

import pytest
import allure

logger = logging.getLogger(__name__)


# ============================================================
# Fixture: 目标App解析
# ============================================================

@pytest.fixture(scope="module")
def target_app(config, adb):
    """
    解析目标App

    优先使用config配置的包名(需已安装)，未安装时回退Chrome验证机制，
    两者都不可用时skip。

    Returns:
        dict: {"package", "activity", "mode": "target"|"chrome-fallback"}
    """
    cfg_pkg = config.get("devices")[0].get("app_package", "com.dolphin.atc")
    for pkg, mode in [(cfg_pkg, "target"), ("com.android.chrome", "chrome-fallback")]:
        if adb.is_app_installed(pkg):
            info = adb.get_app_info(pkg)
            activity = info.get("main_activity")
            if activity in (None, "unknown", ""):
                activity = ".MainActivity"
            logger.info(f"生命周期测试目标: {pkg} ({mode}, activity={activity})")
            return {"package": pkg, "activity": activity, "mode": mode}

    pytest.skip("目标App未安装且无Chrome可用于机制验证")
    return {}


# ============================================================
# 启动与关闭
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("冷启动")
@allure.title("冷启动应用并测量耗时")
@pytest.mark.lifecycle
def test_cold_start_app(app_lifecycle, adb, target_app):
    """
    验证点:
        - 冷启动成功且耗时>0
        - 启动后进程存活
    """
    pkg, act = target_app["package"], target_app["activity"]

    with allure.step("1. 强制停止应用 (模拟冷启动)"):
        adb.force_stop_app(pkg)

    with allure.step("2. 启动并测量耗时"):
        result = app_lifecycle.launch(pkg, act, measure=True)

    with allure.step("3. 验证启动结果"):
        assert result["success"], f"启动失败: {result}"
        assert result["total_time_ms"] is not None and result["total_time_ms"] > 0, (
            f"未获取到启动耗时: {result}"
        )

    with allure.step("4. 验证进程存活"):
        assert adb.is_process_alive(pkg), f"启动后进程未存活: {pkg}"

    allure.attach(
        f"包名: {pkg}\nTotalTime: {result['total_time_ms']}ms\n"
        f"ThisTime: {result['this_time_ms']}ms\nLaunchState: {result['launch_state']}",
        name="冷启动耗时",
        attachment_type=allure.attachment_type.TEXT,
    )
    logger.info(f"冷启动耗时: {result['total_time_ms']}ms state={result['launch_state']}")


@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("启动状态")
@allure.title("启动状态自动识别 (COLD/WARM)")
@pytest.mark.lifecycle
def test_launch_state_detected(app_lifecycle, target_app):
    """
    验证点: am start -W 的LaunchState字段能正常解析
    (Android 12+有该字段，不硬断言具体值)
    """
    pkg, act = target_app["package"], target_app["activity"]
    result = app_lifecycle.launch(pkg, act, measure=True)
    assert result["launch_state"] in ("COLD", "WARM", "UNKNOWN"), (
        f"异常LaunchState: {result['launch_state']}"
    )
    logger.info(f"LaunchState: {result['launch_state']}")


@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("关闭应用")
@allure.title("关闭应用后进程结束")
@pytest.mark.lifecycle
def test_close_app(app_lifecycle, adb, target_app):
    """
    验证点:
        - close后进程不存在
        - 前台不再是目标包
    """
    pkg = target_app["package"]

    with allure.step("1. 先启动应用"):
        app_lifecycle.launch(pkg, target_app["activity"], measure=False)

    with allure.step("2. 关闭应用"):
        assert app_lifecycle.close(pkg), "关闭应用失败"

    with allure.step("3. 验证进程已结束"):
        assert not adb.is_process_alive(pkg), f"关闭后进程仍存活: {pkg}"

    with allure.step("4. 验证不在前台"):
        assert adb.get_current_app_package() != pkg, "关闭后应用仍在前台"


# ============================================================
# 后台运行
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("后台运行")
@allure.title("应用切后台后回前台")
@pytest.mark.lifecycle
def test_background_and_resume(app_lifecycle, target_app):
    """
    验证点:
        - background后前台不再是目标包
        - resume后前台恢复为目标包
    """
    pkg, act = target_app["package"], target_app["activity"]

    with allure.step("1. 启动应用"):
        app_lifecycle.launch(pkg, act, measure=False)

    with allure.step("2. 切后台"):
        assert app_lifecycle.background(pkg), "切后台失败"

    with allure.step("3. 回前台"):
        assert app_lifecycle.resume(pkg, act), "回前台失败"


@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("后台运行")
@allure.title("切后台后位于桌面")
@pytest.mark.lifecycle
def test_background_state_after_home_key(app_lifecycle, adb, target_app):
    """
    验证点: 按HOME切后台后当前Activity为桌面(launcher)或非目标包
    """
    pkg = target_app["package"]

    with allure.step("1. 启动应用"):
        app_lifecycle.launch(pkg, target_app["activity"], measure=False)

    with allure.step("2. 切后台"):
        assert app_lifecycle.background(pkg), "切后台失败"

    with allure.step("3. 验证前台状态"):
        foreground = adb.get_current_app_package()
        assert foreground != pkg, f"切后台后前台仍是目标包: {foreground}"
        logger.info(f"切后台后前台: {foreground}")


# ============================================================
# 启动耗时统计
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("启动耗时统计")
@allure.title("冷启动耗时统计 (3轮)")
@pytest.mark.lifecycle
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)  # 性能数据不可重跑
def test_cold_start_time(app_lifecycle, performance_collector, target_app):
    """
    验证点:
        - 3轮测量统计齐全 (avg/median/min/max)
        - 阈值校验 (默认warn_only不失败)
    """
    pkg, act = target_app["package"], target_app["activity"]

    with allure.step("1. 测量3轮冷启动"):
        stats = app_lifecycle.cold_start_time(pkg, act, rounds=3)

    with allure.step("2. 验证统计完整性"):
        assert stats["values"], f"无有效测量数据: {stats}"
        assert len(stats["values"]) >= 1, "至少1轮有效"
        assert stats["median"] is not None, "缺少中位数"

    with allure.step("3. 阈值校验 (warn_only默认不失败)"):
        result = performance_collector.check_threshold("cold_start_ms", stats["median"])
        assert result in ("ok", "warn"), f"strict模式下超阈值: {stats['median']}ms"
        # 记录到CSV
        performance_collector.write_csv(
            [{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "test_name": "test_cold_start_time",
                "metric": "cold_start_ms",
                "value": stats["median"],
                "result": result,
                "package": pkg,
            }]
        )

    allure.attach(str(stats), name="冷启动统计", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"冷启动统计: {stats}")


@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("启动耗时统计")
@allure.title("热启动耗时统计 (3轮)")
@pytest.mark.lifecycle
@pytest.mark.perf
@pytest.mark.flaky(reruns=0)
def test_warm_start_time(app_lifecycle, target_app):
    """
    验证点: 热启动(后台->前台)3轮测量统计齐全
    """
    pkg, act = target_app["package"], target_app["activity"]

    with allure.step("1. 测量3轮热启动"):
        stats = app_lifecycle.warm_start_time(pkg, act, rounds=3)

    with allure.step("2. 验证统计完整性"):
        assert stats["values"], f"无有效测量数据: {stats}"
        assert stats["avg"] is not None and stats["avg"] >= 0, "平均耗时异常"

    allure.attach(str(stats), name="热启动统计", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"热启动统计: {stats}")


@allure.epic("低空空管系统")
@allure.feature("App生命周期")
@allure.story("状态报告")
@allure.title("应用状态报告")
@pytest.mark.lifecycle
def test_state_report(app_lifecycle, target_app):
    """
    验证点: 状态报告包含前台/进程/Activity信息
    """
    pkg = target_app["package"]

    with allure.step("1. 生成状态报告"):
        report = app_lifecycle.state_report(pkg)

    with allure.step("2. 验证报告结构"):
        assert "foreground" in report, "缺少前台状态"
        assert "process_alive" in report, "缺少进程状态"
        assert "current_activity" in report, "缺少当前Activity"

    allure.attach(str(report), name="状态报告", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"状态报告: {report}")
