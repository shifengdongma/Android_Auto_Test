#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化测试运行入口

功能:
    - 统一管理测试运行命令
    - 支持不同粒度的测试执行
    - 自动生成Allure报告
    - 支持并行执行

使用示例:
    python run_tests.py                    # 运行所有测试
    python run_tests.py --smoke            # 仅运行冒烟测试
    python run_tests.py --module login     # 运行指定模块
    python run_tests.py --parallel 2       # 2个worker并行执行
    python run_tests.py --report           # 运行后自动打开Allure报告
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 测试模块名 -> 测试文件映射
MODULE_FILES = {
    "login": "tests/test_login.py",
    "home": "tests/test_home.py",
    "flight": "tests/test_flight.py",
    "news": "tests/test_news.py",
    "mine": "tests/test_mine.py",
    "install": "tests/test_app_install.py",
    "lifecycle": "tests/test_app_lifecycle.py",
    "performance": "tests/test_performance.py",
    "network": "tests/test_network.py",
    "stability": "tests/test_stability.py",
    "register": "tests/test_register.py",
    "alert": "tests/test_alert_detail.py",
    "plan-ops": "tests/test_plan_operations.py",
}


def run_command(cmd: list, description: str = "") -> int:
    """
    执行命令并返回退出码

    Args:
        cmd: 命令列表
        description: 描述信息

    Returns:
        int: 退出码 (0=成功)
    """
    print(f"\n{'=' * 60}")
    print(f"  {description}")
    print(f"  命令: {' '.join(cmd)}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="低空空管自动化系统 - 移动端测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有测试
  python run_tests.py

  # 仅运行冒烟测试
  python run_tests.py --smoke

  # 运行登录模块测试
  python run_tests.py --module login

  # 并行执行 (2个worker)
  python run_tests.py --parallel 2

  # 运行测试并自动打开Allure报告
  python run_tests.py --report

  # 运行但不生成报告 (仅控制台输出)
  python run_tests.py --no-allure

  # 指定设备索引
  python run_tests.py --device 0

  # 调试模式 (单用例，显示详细输出)
  python run_tests.py --debug tests/test_login.py::test_login_success

  # APK安装/升级测试 (需将APK放入 apk/ 目录)
  python run_tests.py --module install

  # App生命周期测试 (启动/关闭/后台)
  python run_tests.py --module lifecycle

  # 性能采集 (基线模式: 只采集不告警)
  python run_tests.py --module performance --perf-baseline

  # 性能严格模式 (超阈值判失败)
  python run_tests.py --module performance --perf-strict

  # 弱网/断网测试
  python run_tests.py --module network

  # Monkey压力测试
  python run_tests.py --module stability
        """,
    )

    # 测试选择
    parser.add_argument(
        "--smoke", action="store_true",
        help="仅运行冒烟测试 (带 @pytest.mark.smoke 标记)"
    )
    parser.add_argument(
        "--module", type=str, default=None,
        choices=list(MODULE_FILES.keys()),
        help="指定运行的测试模块: login/home/flight/news/mine/install/lifecycle/"
             "performance/network/stability/register"
    )
    parser.add_argument(
        "--debug", type=str, default=None,
        help="调试模式: 指定具体测试路径 (如 tests/test_login.py::test_login_success)"
    )

    # 执行配置
    parser.add_argument(
        "--parallel", "-n", type=int, default=0,
        help="并行执行worker数量 (0=单线程)"
    )
    parser.add_argument(
        "--device", type=int, default=0,
        help="设备配置索引 (对应config.yaml中devices列表)"
    )
    parser.add_argument(
        "--reruns", type=int, default=2,
        help="失败重试次数 (默认2)"
    )

    # 报告配置
    parser.add_argument(
        "--report", "-r", action="store_true",
        help="测试结束后自动生成并打开Allure报告"
    )
    parser.add_argument(
        "--no-allure", action="store_true",
        help="不生成Allure报告 (仅控制台输出)"
    )
    parser.add_argument(
        "--allure-dir", type=str, default="reports/allure-results",
        help="Allure结果输出目录"
    )

    # 性能测试配置
    parser.add_argument(
        "--perf-baseline", action="store_true",
        help="性能基线模式: 只采集记录不按阈值告警 (建基线用)"
    )
    parser.add_argument(
        "--perf-strict", action="store_true",
        help="性能阈值严格模式: 超阈值判失败(覆盖warn_only)"
    )
    parser.add_argument(
        "--apk-path", type=str, default=None,
        help="指定本地APK路径(覆盖 config.apk.dir 自动扫描)"
    )

    # 其他
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=True,
        help="详细输出 (默认开启)"
    )
    parser.add_argument(
        "--env", type=str, default=None,
        help="测试环境 (dev/test/staging)，覆盖配置文件"
    )

    args = parser.parse_args()

    # 设置环境变量
    if args.env:
        os.environ["TEST_ENV"] = args.env
    os.environ["DEVICE_INDEX"] = str(args.device)

    # 构建pytest命令
    cmd = ["pytest"]

    # 选择测试范围
    if args.debug:
        cmd.append(args.debug)
    elif args.module:
        cmd.append(MODULE_FILES[args.module])
    else:
        cmd.append("tests/")

    # 标记筛选
    if args.smoke:
        cmd.extend(["-m", "smoke"])

    # 输出配置
    if args.verbose:
        cmd.append("-v")

    # 失败重试
    if args.reruns > 0:
        cmd.extend(["--reruns", str(args.reruns), "--reruns-delay", "3"])

    # 并行执行
    if args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])

    # Allure报告
    if not args.no_allure:
        cmd.extend(["--alluredir", args.allure_dir])

    # 设备索引
    cmd.extend(["--device-index", str(args.device)])

    # 性能测试参数透传
    if args.perf_baseline:
        cmd.append("--perf-baseline")
    if args.perf_strict:
        cmd.append("--perf-strict")
    if args.apk_path:
        cmd.extend(["--apk-path", args.apk_path])

    # 执行测试
    exit_code = run_command(cmd, "执行自动化测试")

    # 生成Allure报告
    if args.report and not args.no_allure:
        allure_cmd = ["allure", "serve", args.allure_dir]
        run_command(allure_cmd, "生成并打开Allure报告")

    # 输出结果摘要
    print(f"\n{'=' * 60}")
    if exit_code == 0:
        print("  ✅ 所有测试通过!")
    else:
        print(f"  ❌ 测试失败 (退出码: {exit_code})")
    print(f"  Allure结果: {PROJECT_ROOT / args.allure_dir}")
    print(f"  日志目录: {PROJECT_ROOT / 'logs'}")
    print(f"  截图目录: {PROJECT_ROOT / 'reports' / 'screenshots'}")
    print(f"{'=' * 60}\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
