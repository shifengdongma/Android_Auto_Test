# -*- coding: utf-8 -*-
"""
Pytest配置文件 (conftest.py)

职责:
    - 定义全局 Fixtures (driver, login, data)
    - 实现失败自动截图 Hook
    - Allure报告环境信息注入
    - 测试数据加载

Fixture作用域说明:
    - session: 整个测试会话共享一个driver (性能最优)
    - function: 每个测试函数创建独立driver (隔离性最好，适合并行)
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

import pytest

# 确保项目根目录在Python路径中
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from drivers.appium_driver import AppiumDriverManager
from config.config_manager import ConfigManager

try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================
# Session级别 - 全局共享
# ============================================================

@pytest.fixture(scope="session")
def config():
    """
    全局配置Fixture (Session级别)

    整个测试会话只加载一次配置。

    Returns:
        ConfigManager: 配置管理器实例
    """
    cfg = ConfigManager()
    logger.info(f"配置加载完成 | 环境: {cfg.get_active_env()}")
    return cfg


@pytest.fixture(scope="session")
def driver_manager(config):
    """
    Driver管理器Fixture (Session级别)

    注意: driver实例本身是function级别的 (driver fixture),
         此fixture仅提供管理器实例供其他工具使用。

    Returns:
        AppiumDriverManager: Driver管理器实例
    """
    manager = AppiumDriverManager(config_manager=config)
    return manager


# ============================================================
# Function级别 - 每个测试独立
# ============================================================

@pytest.fixture(scope="function")
def driver(request, config):
    """
    WebDriver Fixture (Function级别)

    每个测试函数获取独立的driver实例。
    测试完成后自动关闭driver。

    支持通过命令行参数选择设备:
        pytest --device-index=0

    Returns:
        appium.webdriver.Remote
    """
    # 获取设备索引 (通过命令行参数)
    device_index = request.config.getoption("--device-index", default=0)

    manager = AppiumDriverManager(config_manager=config)

    try:
        driver = manager.get_driver(device_index=device_index)
        logger.info(f"Driver创建成功 (设备索引: {device_index})")
    except Exception as e:
        logger.error(f"Driver创建失败: {e}")
        pytest.exit(f"无法创建Driver: {e}")

    # 将driver附加到request.node，供失败hook使用
    request.node._driver = driver

    yield driver

    # Teardown: 关闭driver
    logger.info("Tearing down driver...")
    try:
        driver.terminate_app(config.get("devices")[device_index]["app_package"])
    except Exception:
        pass
    manager.quit_driver()


@pytest.fixture(scope="function")
def screenshot_manager(driver):
    """
    截图管理器Fixture (Function级别)

    Returns:
        ScreenshotManager
    """
    from utils.screenshot import ScreenshotManager
    return ScreenshotManager(driver)


# ============================================================
# 业务Fixtures
# ============================================================

@pytest.fixture(scope="function")
def logged_in_driver(driver, config):
    """
    预登录Fixture

    自动执行登录操作，返回已登录的driver。
    适用于需要登录态的测试用例。

    Returns:
        appium.webdriver.Remote: 已登录的driver
    """
    from pages.login_page import LoginPage

    account = config.get_test_account("default")
    login_page = LoginPage(driver)

    logger.info(f"执行预登录: {account['username']}")
    login_page.wait_for_login_page(timeout=30)
    home_page = login_page.login(
        username=account["username"],
        password=account["password"],
    )

    # 等待首页加载
    from pages.home_page import HomePage
    home = HomePage(driver)
    assert home.is_on_home_page(), "预登录失败: 未能进入首页"

    return driver


@pytest.fixture(scope="function")
def test_data(request):
    """
    测试数据Fixture

    从YAML文件加载测试数据。
    数据文件路径通过 @pytest.mark.data_file("path/to/data.yaml") 指定。

    用法:
        @pytest.mark.data_file("data/login_data.yaml")
        def test_login(test_data):
            for case in test_data:
                ...
    """
    marker = request.node.get_closest_marker("data_file")
    if marker is None:
        return []

    data_path = PROJECT_ROOT / marker.args[0]
    if not data_path.exists():
        logger.warning(f"测试数据文件不存在: {data_path}")
        return []

    import yaml
    with open(data_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 支持 {"data": [...]} 和直接列表两种格式
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data if isinstance(data, list) else [data]


# ============================================================
# Pytest Hooks
# ============================================================

def pytest_addoption(parser):
    """
    添加自定义命令行参数
    """
    parser.addoption(
        "--device-index",
        action="store",
        type=int,
        default=0,
        help="设备配置索引 (对应config.yaml中devices列表)",
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    测试报告Hook - 失败自动截图

    在测试用例执行后(pytest_runtest_makereport)触发:
        - call.when == "call" 且 call.failed 时自动截图
        - 截图附加到Allure报告
        - 日志也附加到Allure报告
    """
    outcome = yield
    report = outcome.get_result()

    # 只处理测试执行阶段的失败 (非setup/teardown)
    if report.when != "call" or not report.failed:
        return

    # 获取driver
    driver = getattr(item, "_driver", None)
    if driver is None:
        logger.warning("无法获取driver实例，跳过失败截图")
        return

    # 生成截图文件名
    test_name = item.nodeid.replace("::", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_dir = PROJECT_ROOT / "reports" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / f"FAILED_{test_name}_{timestamp}.png"

    # 执行截图
    try:
        driver.save_screenshot(str(screenshot_path))
        logger.info(f"失败截图已保存: {screenshot_path}")

        # 附加到Allure报告
        if ALLURE_AVAILABLE:
            with open(screenshot_path, "rb") as f:
                allure.attach(
                    f.read(),
                    name=f"失败截图 - {test_name}",
                    attachment_type=allure.attachment_type.PNG,
                )

            # 附加页面源码 (用于调试)
            try:
                page_source = driver.page_source
                allure.attach(
                    page_source,
                    name=f"页面源码 - {test_name}",
                    attachment_type=allure.attachment_type.XML,
                )
            except Exception:
                pass

    except Exception as e:
        logger.error(f"失败截图执行失败: {e}")


def pytest_configure(config):
    """
    Pytest启动配置Hook

    用于:
        1. 创建必要目录 (logs, reports)
        2. 注入Allure环境信息
    """
    # 创建必要目录
    for dir_name in ["logs", "reports/screenshots", "reports/allure-results"]:
        (PROJECT_ROOT / dir_name).mkdir(parents=True, exist_ok=True)

    # 注入Allure环境信息
    if ALLURE_AVAILABLE:
        env_props = PROJECT_ROOT / "reports" / "allure-results" / "environment.properties"
        env_props.parent.mkdir(parents=True, exist_ok=True)
        with open(env_props, "w", encoding="utf-8") as f:
            f.write(f"Project=低空空管自动化系统\n")
            f.write(f"Platform=Android\n")
            f.write(f"Framework=Appium2 + Pytest\n")
            f.write(f"Python={sys.version.split()[0]}\n")
            f.write(f"Date={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束Hook

    清理操作:
        - 关闭日志Handler
        - 输出测试摘要
    """
    from utils.logger import TestLogger
    TestLogger.shutdown()

    logger.info(f"测试会话结束 | 退出码: {exitstatus}")
