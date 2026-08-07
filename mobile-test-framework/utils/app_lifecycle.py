# -*- coding: utf-8 -*-
"""
App生命周期管理模块

功能:
    - 启动/关闭/后台运行/回前台
    - 启动耗时测量 (冷启动/热启动, am start -W)
    - 前台状态与进程状态查询

实现说明:
    - 后台切换用 adb input keyevent 3 (HOME)，不依赖driver
    - 回前台优先 driver.activate_app (uiautomator2经由instrumentation拉起，
      绕开MIUI"后台弹出界面"权限限制)，回退 am start -n
    - 启动耗时走 am start -W，Android 12+ 提供 LaunchState 自动区分冷/热启动

使用示例:
    from utils.app_lifecycle import AppLifecycleManager

    lc = AppLifecycleManager()
    result = lc.launch("com.dolphin.atc", ".MainActivity")
    lc.background()
    lc.resume()
    stats = lc.cold_start_time(rounds=3)
"""

import logging
import statistics
import time
from typing import Any, Dict, Optional, Tuple

from utils.adb_helper import ADBHelper

try:
    from config.config_manager import ConfigManager
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class AppLifecycleManager:
    """
    App生命周期管理器

    adb为主，driver可选增强。所有adb失败只WARN返回空值/False，不抛异常。
    """

    def __init__(
        self,
        adb: Optional[ADBHelper] = None,
        config: Optional[ConfigManager] = None,
        driver=None,
    ):
        """
        初始化生命周期管理器

        Args:
            adb: ADBHelper实例，默认新建
            config: ConfigManager实例，默认加载单例
            driver: Appium driver (可选，resume时优先activate_app)
        """
        self.adb = adb or ADBHelper()
        self.config = config or ConfigManager()
        self.driver = driver

    def set_driver(self, driver) -> None:
        """设置Appium driver (功能级fixture可在用例内调用)"""
        self.driver = driver

    # ============================================================
    # 包名/Activity解析
    # ============================================================

    def _pkg_activity(
        self,
        package: Optional[str],
        activity: Optional[str],
    ) -> Tuple[str, str]:
        """
        解析目标包名与Activity

        缺省取 config 设备配置的 app_package/app_activity，
        其次取 environments[active_env]。
        """
        if package and activity:
            return package, activity

        pkg = package
        act = activity
        if not pkg:
            try:
                pkg = self.config.get("devices")[0].get("app_package")
            except (IndexError, TypeError):
                pass
        if not pkg:
            env = self.config.get_active_env()
            pkg = self.config.get(f"environments.{env}.app_package")
        if not act:
            try:
                act = self.config.get("devices")[0].get("app_activity")
            except (IndexError, TypeError):
                pass
        if not act:
            env = self.config.get_active_env()
            act = self.config.get(f"environments.{env}.app_activity")

        if not pkg or not act:
            logger.warning("无法解析包名/Activity，请通过参数或config指定")
            return pkg or "unknown", act or "unknown"
        return pkg, act

    # ============================================================
    # 核心生命周期操作
    # ============================================================

    def launch(
        self,
        package: Optional[str] = None,
        activity: Optional[str] = None,
        measure: bool = True,
    ) -> Dict[str, Any]:
        """
        启动应用 (可选测量启动耗时)

        Args:
            package: 包名，默认config
            activity: Activity，默认config
            measure: True使用 am start -W 测量耗时

        Returns:
            dict: {"success", "total_time_ms", "this_time_ms", "wait_time_ms",
                   "launch_state"(COLD/WARM/UNKNOWN)}
        """
        pkg, act = self._pkg_activity(package, activity)
        if measure:
            info = self.adb.start_app_measured(pkg, act)
        else:
            ok = self.adb.start_app(pkg, act)
            info = {"success": ok, "total_time_ms": None, "this_time_ms": None,
                    "wait_time_ms": None, "launch_state": "UNKNOWN"}
        return info

    def close(self, package: Optional[str] = None) -> bool:
        """
        关闭应用 (force-stop，彻底结束进程)

        Args:
            package: 包名，默认config

        Returns:
            bool: 是否成功
        """
        pkg, _ = self._pkg_activity(package, None)
        try:
            if self.driver is not None:
                try:
                    self.driver.terminate_app(pkg)
                    return True
                except Exception:
                    pass  # driver不可用时回退adb
            return self.adb.force_stop_app(pkg)
        except Exception as e:
            logger.warning(f"关闭应用失败: {e}")
            return False

    def background(self, package: Optional[str] = None) -> bool:
        """
        应用切后台 (HOME键)

        Args:
            package: 包名，默认config

        Returns:
            bool: 是否成功切后台 (前台不再是目标包)
        """
        pkg, _ = self._pkg_activity(package, None)
        try:
            self.adb.press_key(3)  # KEYCODE_HOME
            # 等待动画结束
            time.sleep(1)
            foreground = self.adb.get_current_app_package()
            moved = foreground != pkg
            if not moved:
                logger.warning(f"切后台失败: 前台仍是 {foreground}")
            else:
                logger.info(f"应用已切后台: {pkg}")
            return moved
        except Exception as e:
            logger.warning(f"切后台失败: {e}")
            return False

    def resume(
        self,
        package: Optional[str] = None,
        activity: Optional[str] = None,
    ) -> bool:
        """
        应用回前台

        优先 driver.activate_app (绕开MIUI后台弹出限制)，回退 adb am start。

        Args:
            package: 包名，默认config
            activity: Activity，默认config

        Returns:
            bool: 是否成功 (前台已是目标包)
        """
        pkg, act = self._pkg_activity(package, activity)
        try:
            if self.driver is not None:
                try:
                    self.driver.activate_app(pkg)
                except Exception as e:
                    logger.warning(f"driver.activate_app失败({e})，回退adb")
                    self.adb.start_app(pkg, act)
            else:
                self.adb.start_app(pkg, act)
            time.sleep(1)
            foreground = self.adb.get_current_app_package()
            back = foreground == pkg
            if not back:
                logger.warning(f"回前台验证失败: 前台={foreground}, 期望={pkg}")
            return back
        except Exception as e:
            logger.warning(f"回前台失败: {e}")
            return False

    def is_foreground(self, package: Optional[str] = None) -> bool:
        """检查目标应用是否在前台"""
        pkg, _ = self._pkg_activity(package, None)
        try:
            return self.adb.get_current_app_package() == pkg
        except Exception:
            return False

    # ============================================================
    # 启动耗时测量
    # ============================================================

    def cold_start_time(
        self,
        package: Optional[str] = None,
        activity: Optional[str] = None,
        rounds: int = 3,
    ) -> Dict[str, Any]:
        """
        冷启动耗时测量 (force-stop后 am start -W 多轮取统计)

        Args:
            package: 包名，默认config
            activity: Activity，默认config
            rounds: 测量轮次

        Returns:
            dict: {"values": [...], "avg", "median", "min", "max", "launch_states": [...]}
        """
        pkg, act = self._pkg_activity(package, activity)
        values = []
        states = []
        for i in range(rounds):
            try:
                self.adb.force_stop_app(pkg)
                time.sleep(0.5)
                info = self.adb.start_app_measured(pkg, act)
                if info["total_time_ms"] is not None:
                    values.append(info["total_time_ms"])
                    states.append(info["launch_state"])
                else:
                    logger.warning(f"第{i + 1}轮冷启动测量无耗时数据")
            except Exception as e:
                logger.warning(f"第{i + 1}轮冷启动测量失败: {e}")
            time.sleep(1)  # 轮次间隔

        return self._stats(values, states)

    def warm_start_time(
        self,
        package: Optional[str] = None,
        activity: Optional[str] = None,
        rounds: int = 3,
    ) -> Dict[str, Any]:
        """
        热启动耗时测量 (HOME切后台后 am start -W 多轮取统计)

        Args:
            package: 包名，默认config
            activity: Activity，默认config
            rounds: 测量轮次

        Returns:
            dict: {"values": [...], "avg", "median", "min", "max", "launch_states": [...]}
        """
        pkg, act = self._pkg_activity(package, activity)
        values = []
        states = []
        for i in range(rounds):
            try:
                # 先确保应用在运行，切后台，再测量
                if not self.adb.is_process_alive(pkg):
                    self.adb.start_app(pkg, act)
                    time.sleep(1)
                self.adb.press_key(3)
                time.sleep(0.5)
                info = self.adb.start_app_measured(pkg, act)
                if info["total_time_ms"] is not None:
                    values.append(info["total_time_ms"])
                    states.append(info["launch_state"])
                else:
                    logger.warning(f"第{i + 1}轮热启动测量无耗时数据")
            except Exception as e:
                logger.warning(f"第{i + 1}轮热启动测量失败: {e}")
            time.sleep(1)

        return self._stats(values, states)

    @staticmethod
    def _stats(values: list, states: list) -> Dict[str, Any]:
        """计算统计值"""
        if not values:
            return {"values": [], "avg": None, "median": None,
                    "min": None, "max": None, "launch_states": states}
        return {
            "values": values,
            "avg": round(statistics.mean(values), 1),
            "median": round(statistics.median(values), 1),
            "min": min(values),
            "max": max(values),
            "launch_states": states,
        }

    # ============================================================
    # 状态报告
    # ============================================================

    def state_report(self, package: Optional[str] = None) -> Dict[str, Any]:
        """
        应用状态摘要 (供Allure attach/manual_test打印)

        Returns:
            dict: {"package", "foreground", "process_alive", "pid", "current_activity"}
        """
        pkg, _ = self._pkg_activity(package, None)
        try:
            pid = self.adb.get_pid(pkg)
            return {
                "package": pkg,
                "foreground": self.is_foreground(pkg),
                "process_alive": pid is not None,
                "pid": pid,
                "current_activity": self.adb.get_current_activity(),
            }
        except Exception as e:
            logger.warning(f"状态报告获取失败: {e}")
            return {"package": pkg, "error": str(e)}
