# -*- coding: utf-8 -*-
"""
Appium Driver管理器

功能:
    - 封装Appium WebDriver的创建和销毁
    - 支持Android真机和模拟器自动识别
    - 支持多设备配置切换
    - 连接重试机制
    - Session生命周期管理
    - 预留iOS扩展接口

使用示例:
    from drivers.appium_driver import AppiumDriverManager

    manager = AppiumDriverManager()
    driver = manager.get_driver()
    # ... 执行测试 ...
    manager.quit_driver()
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

from appium import webdriver
from appium.options.android import UiAutomator2Options
# iOS扩展预留 (后续导入)
# from appium.options.ios import XCUITestOptions

from config.config_manager import ConfigManager


def _ensure_android_sdk():
    """
    确保 ANDROID_HOME 环境变量已设置

    自动检测项目内置的 platform-tools 目录，
    如果 ANDROID_HOME 未设置则自动指向项目根目录。
    """
    if os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT"):
        return  # 已设置，无需处理

    # 查找项目根目录 (mobile-test-framework 的上一级)
    project_root = Path(__file__).parent.parent.parent
    platform_tools = project_root / "platform-tools" / "adb.exe"

    if platform_tools.exists():
        os.environ["ANDROID_HOME"] = str(project_root)
        os.environ["ANDROID_SDK_ROOT"] = str(project_root)
        logging.debug(f"自动设置 ANDROID_HOME={project_root}")


# 模块加载时自动检测
_ensure_android_sdk()

logger = logging.getLogger(__name__)


class AppiumDriverManager:
    """
    Appium Driver管理类

    职责:
        1. 根据配置创建Appium WebDriver实例
        2. 管理Session的创建/销毁生命周期
        3. 提供连接重试和异常恢复机制
        4. 支持多设备/多平台切换

    设计原则:
        - 单例模式管理driver实例，避免重复创建
        - 所有平台相关配置通过ConfigManager注入
        - 方法不含平台硬编码，为iOS扩展留接口
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化Driver管理器

        Args:
            config_manager: 配置管理器实例，默认创建新实例
        """
        self._config = config_manager or ConfigManager()
        self._driver: Optional[webdriver.Remote] = None
        self._device_config: Dict[str, Any] = {}
        self._platform: str = "Android"  # 支持后续切换为 iOS

    # ============================================================
    # 公共API - Driver生命周期
    # ============================================================

    def get_driver(
        self,
        device_index: int = 0,
        platform: str = "Android",
        restart: bool = False,
    ):
        """
        获取或创建Appium WebDriver实例

        Args:
            device_index: 设备配置索引 (对应config.yaml中devices列表)
            platform: 平台类型 (Android / iOS，预留扩展)
            restart: 是否强制重新创建session

        Returns:
            appium.webdriver.Remote: Appium WebDriver实例

        Raises:
            ConnectionError: 连接Appium服务失败
            RuntimeError: 创建Session失败
        """
        self._platform = platform

        # 如果已有driver且不需要重启，直接返回
        if self._driver is not None and not restart:
            try:
                # 验证session是否仍然有效
                self._driver.current_activity
                return self._driver
            except Exception:
                logger.warning("现有Session已失效，将重新创建")
                self._driver = None

        # 加载设备配置
        if platform == "Android":
            self._device_config = self._config.get_device_config(device_index)
            self._auto_fix_platform_version()  # 自动适配实际设备版本
        elif platform == "iOS":
            self._device_config = self._config.get_ios_device_config(device_index)
        else:
            raise ValueError(f"不支持的平台类型: {platform}，仅支持 Android / iOS")

        # 创建driver (带重试)
        self._driver = self._create_driver_with_retry()

        return self._driver

    def quit_driver(self) -> None:
        """安全关闭driver并释放资源"""
        if self._driver is not None:
            try:
                self._driver.quit()
                logger.info("Appium Driver已成功关闭")
            except Exception as e:
                logger.warning(f"关闭Driver时出现异常 (可忽略): {e}")
            finally:
                self._driver = None

    def restart_driver(self, device_index: int = 0):
        """
        重启driver (先关闭再创建)

        Args:
            device_index: 设备配置索引

        Returns:
            appium.webdriver.Remote: 新的WebDriver实例
        """
        self.quit_driver()
        return self.get_driver(device_index=device_index, restart=True)

    def _auto_fix_platform_version(self):
        """
        自动修正 platformVersion 以匹配实际设备

        通过 ADB 获取实际设备的 Android 版本，
        如果与配置不符则自动覆盖，避免 "Unable to find device with OS X" 错误。
        """
        udid = self._device_config.get("udid", "")
        try:
            from utils.adb_helper import ADBHelper
            adb = ADBHelper()
            devices = adb.get_connected_devices()
            online = [d for d in devices if d["status"] == "device"]

            if not online:
                return  # 没有设备连接，跳过检测

            # 找到匹配的设备
            actual_version = None
            if udid:
                for d in online:
                    if d["id"] == udid:
                        actual_version = d["android_version"]
                        break
            else:
                actual_version = online[0]["android_version"]

            if actual_version:
                configured = self._device_config.get("platform_version", "")
                if configured != actual_version:
                    logger.info(
                        f"自动修正 platformVersion: '{configured}' -> '{actual_version}'"
                        f" (设备 {online[0]['model']})"
                    )
                    self._device_config["platform_version"] = actual_version
        except Exception as e:
            logger.debug(f"自动检测设备版本失败 (不影响流程): {e}")

    # ============================================================
    # 内部方法 - Driver创建
    # ============================================================

    def _create_driver_with_retry(self):
        """
        带重试机制的Driver创建

        重试次数和间隔从配置文件读取:
            config.yaml -> retry.max_attempts / retry.interval_ms

        Returns:
            appium.webdriver.Remote

        Raises:
            ConnectionError: 所有重试均失败
        """
        retry_config = self._config.get("retry", {})
        max_attempts = retry_config.get("max_attempts", 3)
        interval_ms = retry_config.get("interval_ms", 1000)

        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"正在创建Appium Session (第{attempt}/{max_attempts}次)...\n"
                    f"  平台: {self._platform}\n"
                    f"  设备: {self._device_config.get('name', 'Unknown')}\n"
                    f"  UDID: {self._device_config.get('udid', '自动检测')}"
                )
                return self._build_driver()
            except Exception as e:
                last_error = e
                logger.warning(
                    f"第{attempt}次创建Session失败: {e}"
                )
                if attempt < max_attempts:
                    wait_time = interval_ms / 1000.0
                    logger.info(f"等待 {wait_time}s 后重试...")
                    time.sleep(wait_time)

        raise ConnectionError(
            f"创建Appium Session失败 (已重试{max_attempts}次)\n"
            f"请检查:\n"
            f"  1. Appium Server是否已启动: appium\n"
            f"  2. 设备是否正确连接: adb devices\n"
            f"  3. appPackage/appActivity是否正确\n"
            f"最终错误: {last_error}"
        )

    def _build_driver(self):
        """
        根据平台构建对应的WebDriver实例

        支持:
            - Android: UiAutomator2
            - iOS: XCUITest (预留扩展)

        Returns:
            appium.webdriver.Remote
        """
        server_url = self._config.get("appium.server_url", "http://127.0.0.1:4723")

        if self._platform == "Android":
            return self._build_android_driver(server_url)
        elif self._platform == "iOS":
            return self._build_ios_driver(server_url)
        else:
            raise ValueError(f"不支持的平台: {self._platform}")

    def _build_android_driver(self, server_url: str):
        """
        构建Android WebDriver

        支持两种模式:
            - native: 测试原生APP (使用 appPackage/appActivity)
            - browser: 测试移动端H5 (使用手机Chrome浏览器)

        Args:
            server_url: Appium Server地址

        Returns:
            appium.webdriver.Remote
        """
        # 检查测试模式
        test_mode = self._config.get("test_mode", "native")
        options = UiAutomator2Options()

        if test_mode == "browser":
            # ---- 浏览器模式: 通过手机Chrome访问H5页面 ----
            options.platform_name = self._device_config.get("platform", "Android")
            options.automation_name = self._device_config.get(
                "automation_name", "UiAutomator2"
            )
            options.device_name = self._device_config.get("device_name", "Android")
            options.platform_version = self._device_config.get("platform_version", "")

            # Chrome 浏览器模式
            options.browser_name = "Chrome"
            options.no_reset = True  # Chrome is preinstalled, don't reset

            # UDID
            udid = self._device_config.get("udid", "")
            if udid:
                options.udid = udid

            # 兼容 Android 14+
            options.set_capability("skipDeviceInitialization", True)
            options.set_capability("skipServerInstallation", True)

            options.new_command_timeout = self._device_config.get(
                "new_command_timeout",
                self._config.get("timeout.new_command", 120)
            )
            options.auto_grant_permissions = True

            logger.info("Browser mode: launching Chrome on device")

        else:
            # ---- 原生APP模式 (原有逻辑) ----
            options.platform_name = self._device_config.get("platform", "Android")
            options.automation_name = self._device_config.get(
                "automation_name", "UiAutomator2"
            )
            options.device_name = self._device_config.get("device_name", "Android")
            options.platform_version = self._device_config.get("platform_version", "")

            # UDID
            udid = self._device_config.get("udid", "")
            if udid:
                options.udid = udid

            # 应用包名和Activity
            app_package = self._device_config.get("app_package", "")
            app_activity = self._device_config.get("app_activity", "")
            if app_package:
                options.app_package = app_package
            if app_activity:
                options.app_activity = app_activity

            options.no_reset = self._device_config.get("no_reset", True)
            options.full_reset = self._device_config.get("full_reset", False)
            options.auto_grant_permissions = self._device_config.get(
                "auto_grant_permissions", True
            )
            # Android 14+: 如果 app 未安装，不强制等待
            options.set_capability("enforceAppInstall", False)

            # Android 14+ 兼容: 跳过 hidden_api_policy 设置
            if self._device_config.get("skip_device_initialization"):
                options.set_capability("skipDeviceInitialization", True)
            if self._device_config.get("skip_server_installation"):
                options.set_capability("skipServerInstallation", True)

            # 超时设置
            options.new_command_timeout = self._device_config.get(
                "new_command_timeout",
                self._config.get("timeout.new_command", 120)
            )

            # 语言
            if self._device_config.get("language"):
                options.language = self._device_config["language"]
            if self._device_config.get("locale"):
                options.locale = self._device_config["locale"]

            logger.info("Native mode: launching app on device")

        logger.info(f"Android Driver配置完成，正在连接: {server_url} mode={test_mode}")
        driver = webdriver.Remote(server_url, options=options)

        # 设置隐式等待
        implicit_wait = self._config.get("timeout.implicit_wait", 10)
        driver.implicitly_wait(implicit_wait)

        # 浏览器模式: 先打开空白页，测试URL由用户/PageObject手动导航
        if test_mode == "browser":
            driver.get("about:blank")
            logger.info("浏览器Session已创建，Chrome已启动 (空白页)")
            logger.info(f"测试URL请手动导航: {self._config.get('test_url', '')}")

        logger.info(f"Android Session创建成功 (隐式等待: {implicit_wait}s, 模式: {test_mode})")
        return driver

    def _build_ios_driver(self, server_url: str):
        """
        构建iOS WebDriver (XCUITest) - 预留扩展接口

        当项目扩展至iOS时启用此方法。
        需要先安装: appium driver install xcuitest

        Args:
            server_url: Appium Server地址

        Returns:
            appium.webdriver.Remote
        """
        from appium.options.ios import XCUITestOptions

        options = XCUITestOptions()

        options.platform_name = self._device_config.get("platform", "iOS")
        options.automation_name = self._device_config.get(
            "automation_name", "XCUITest"
        )
        options.device_name = self._device_config.get("device_name", "iPhone 15")
        options.platform_version = self._device_config.get("platform_version", "")

        udid = self._device_config.get("udid", "")
        if udid:
            options.udid = udid

        bundle_id = self._device_config.get("bundle_id", "")
        if bundle_id:
            options.bundle_id = bundle_id

        options.no_reset = self._device_config.get("no_reset", True)
        options.auto_accept_alerts = self._device_config.get(
            "auto_accept_alerts", True
        )

        options.new_command_timeout = self._device_config.get(
            "new_command_timeout", 120
        )

        logger.info(f"iOS Driver配置完成，正在连接: {server_url}")
        driver = webdriver.Remote(server_url, options=options)

        implicit_wait = self._config.get("timeout.implicit_wait", 10)
        driver.implicitly_wait(implicit_wait)

        logger.info(f"iOS Session创建成功 (隐式等待: {implicit_wait}s)")
        return driver

    # ============================================================
    # 属性
    # ============================================================

    @property
    def driver(self):
        """获取当前driver实例 (便捷属性)"""
        if self._driver is None:
            raise RuntimeError(
                "Driver尚未初始化，请先调用 get_driver() 创建Session"
            )
        return self._driver

    @property
    def is_connected(self) -> bool:
        """检查Driver是否已连接且可用"""
        if self._driver is None:
            return False
        try:
            self._driver.current_activity
            return True
        except Exception:
            return False

    @property
    def platform(self) -> str:
        """获取当前平台类型"""
        return self._platform

    @property
    def device_info(self) -> Dict[str, Any]:
        """获取当前设备配置信息"""
        return self._device_config.copy()
