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
# 工具类Fixtures (APK管理/生命周期/性能/网络)
# ============================================================

@pytest.fixture(scope="session")
def adb():
    """
    ADB工具单例 (Session级别)

    Returns:
        ADBHelper
    """
    from utils.adb_helper import ADBHelper
    return ADBHelper()


@pytest.fixture(scope="session")
def apk_manager(adb, config, request):
    """
    APK管理器 (Session级别)

    支持 --apk-path 指定APK路径。

    Returns:
        APKManager
    """
    from utils.apk_manager import APKManager
    mgr = APKManager(adb=adb, config=config)
    # 命令行指定APK时临时覆盖目录
    apk_path = request.config.getoption("--apk-path", default=None)
    if apk_path:
        mgr._override_apk_path = apk_path
    else:
        mgr._override_apk_path = None
    return mgr


@pytest.fixture(scope="session")
def app_lifecycle(adb, config):
    """
    App生命周期管理器 (Session级别)

    注意: driver是function级别，此fixture以adb模式运行；
          用例内如需driver增强可调用 lifecycle.set_driver(driver)。

    Returns:
        AppLifecycleManager
    """
    from utils.app_lifecycle import AppLifecycleManager
    return AppLifecycleManager(adb=adb, config=config)


@pytest.fixture(scope="session")
def performance_collector(adb, config, request):
    """
    性能采集器 (Session级别)

    支持 --perf-baseline (只采集不告警) / --perf-strict (超阈值判失败)。

    Returns:
        PerformanceCollector
    """
    from utils.performance import PerformanceCollector
    pc = PerformanceCollector(adb=adb, config=config)
    # 命令行参数覆盖阈值策略
    if request.config.getoption("--perf-baseline", default=False):
        pc._policy = "warn_only"
        logger.info("性能基线模式: 只采集记录，不按阈值告警")
    elif request.config.getoption("--perf-strict", default=False):
        pc._policy = "strict"
        logger.info("性能严格模式: 超阈值将判失败")
    return pc


@pytest.fixture(scope="session")
def network_controller(adb, config):
    """
    网络控制器 (Session级别)

    Returns:
        NetworkController
    """
    from utils.network_controller import NetworkController
    return NetworkController(adb=adb)


# ============================================================
# 守卫Fixtures (条件跳过)
# ============================================================

@pytest.fixture(scope="session")
def require_native_mode(config):
    """
    native模式守卫: browser模式下跳过

    APK就绪后切换 config.yaml 的 test_mode: native 即自动生效。
    """
    if config.get("test_mode") != "native":
        pytest.skip("当前为browser模式，该用例需要native模式(test_mode: native)")
    return True


@pytest.fixture(scope="session")
def require_apk(apk_manager):
    """
    APK存在守卫: 无本地APK文件时跳过

    返回最新APK路径。
    """
    if getattr(apk_manager, "_override_apk_path", None):
        return apk_manager._override_apk_path
    apk = apk_manager.get_latest_apk()
    if not apk:
        pytest.skip("未找到本地APK文件，请放置到 config.apk.dir 目录")
    return str(apk)


# ============================================================
# 业务Fixtures
# ============================================================

@pytest.fixture(scope="function")
def weak_network(network_controller):
    """
    弱网用例Fixture (Function级别)

    setup后交给用例控制网络，teardown强制恢复网络，
    防止断网状态污染后续用例。
    """
    yield network_controller
    # Teardown: 无论用例成败都恢复网络
    try:
        network_controller.restore_all()
        logger.info("弱网用例结束，网络已恢复")
    except Exception as e:
        logger.error(f"网络恢复失败: {e}")

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
    parser.addoption(
        "--perf-baseline",
        action="store_true",
        default=False,
        help="性能基线模式: 只采集记录不按阈值告警",
    )
    parser.addoption(
        "--perf-strict",
        action="store_true",
        default=False,
        help="性能阈值严格模式: 超阈值判失败(覆盖 warn_only)",
    )
    parser.addoption(
        "--apk-path",
        type=str,
        default=None,
        help="指定本地APK路径(覆盖 config.apk.dir 自动扫描)",
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

    # 生成截图文件名 (清理Windows非法字符: 参数化id转义产生的反斜杠与方括号)
    test_name = (
        item.nodeid.replace("::", "_").replace("/", "_")
        .replace("\\", "_").replace("[", "_").replace("]", "_")
    )
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

    # 失败时附加logcat尾部 (驱动挂掉也可用, 独立于driver)
    try:
        from utils.logcat import LogcatCapture

        capture = LogcatCapture()
        package = None
        try:
            cfg = ConfigManager()
            package = cfg.get("devices")[0].get("app_package")
        except Exception:
            pass
        log_tail = capture.tail(lines=100, package=package)
        if log_tail and ALLURE_AVAILABLE:
            # 截断50KB控制报告体积
            if len(log_tail) > 50 * 1024:
                log_tail = log_tail[-50 * 1024:]
                log_tail = "...(截断, 完整日志见logs/logcat)\n" + log_tail
            allure.attach(
                log_tail,
                name=f"logcat现场 - {test_name}",
                attachment_type=allure.attachment_type.TEXT,
            )
    except Exception as e:
        logger.warning(f"失败logcat获取失败: {e}")


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
        # 追加设备型号/模式信息 (不依赖driver)
        device_model = "unknown"
        test_mode = "browser"
        try:
            from utils.adb_helper import ADBHelper
            _adb = ADBHelper()
            device_id = _adb.get_first_device_id()
            if device_id:
                device_model = _adb.get_device_info(device_id).get("model", "unknown")
        except Exception:
            pass
        try:
            from config.config_manager import ConfigManager
            test_mode = ConfigManager().get("test_mode", "browser")
        except Exception:
            pass
        with open(env_props, "w", encoding="utf-8") as f:
            f.write(f"Project=低空空管自动化系统\n")
            f.write(f"Platform=Android\n")
            f.write(f"Framework=Appium2 + Pytest\n")
            f.write(f"Python={sys.version.split()[0]}\n")
            f.write(f"Date={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"TestMode={test_mode}\n")
            f.write(f"DeviceModel={device_model}\n")
            f.write(f"PerfPolicy={config.getoption('--perf-strict', default=False) and 'strict' or 'warn_only'}\n")


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
