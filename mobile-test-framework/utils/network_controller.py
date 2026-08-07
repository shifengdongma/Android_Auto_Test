# -*- coding: utf-8 -*-
"""
网络控制模块

功能:
    - NetworkController: 开关级断网/飞行模式/网络恢复 + 连通性校验
    - ThrottleController: 弱网限速抽象协议 (接口预留，真机限速必须PC侧代理)

弱网测试说明:
    开关级(断网/仅WiFi/仅移动网络/飞行模式)由adb直接实现，双模式(browser/native)可用。
    真正的限速/丢包/延迟模拟在真机上必须通过PC侧代理实现
    (手机WiFi代理指向PC，mitmproxy/Charles限速)，见 docs/弱网测试方案.md。

使用示例:
    from utils.network_controller import NetworkController

    net = NetworkController()
    net.set_mode("offline")   # 断网
    # ... 验证弱网行为 ...
    net.restore_all()         # 恢复网络 (必须恢复，避免污染后续用例)
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

from utils.adb_helper import ADBHelper

try:
    from config.config_manager import ConfigManager
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class NetworkController:
    """
    网络开关控制器

    模式:
        normal:      全部网络开启
        offline:     关闭WiFi+移动数据 (完全断网)
        airplane:    飞行模式
        wifi_only:   仅WiFi
        mobile_only: 仅移动数据
    """

    MODES = {"normal", "offline", "airplane", "wifi_only", "mobile_only"}

    def __init__(self, adb: Optional[ADBHelper] = None):
        """
        初始化网络控制器

        Args:
            adb: ADBHelper实例，默认新建
        """
        self.adb = adb or ADBHelper()

    # ============================================================
    # 模式切换
    # ============================================================

    def set_mode(self, mode: str) -> bool:
        """
        切换到指定网络模式

        Args:
            mode: normal / offline / airplane / wifi_only / mobile_only

        Returns:
            bool: 是否切换成功
        """
        if mode not in self.MODES:
            logger.warning(f"未知网络模式: {mode} (支持: {self.MODES})")
            return False

        if mode == "normal":
            return self.restore_all()
        if mode == "offline":
            return self.disconnect_all()
        if mode == "airplane":
            return self.adb.set_airplane_mode(True)
        if mode == "wifi_only":
            ok1 = self.adb.disable_mobile_data()
            ok2 = self.adb.enable_wifi()
            return ok1 or ok2
        if mode == "mobile_only":
            ok1 = self.adb.disable_wifi()
            ok2 = self.adb.enable_mobile_data()
            return ok1 or ok2
        return False

    def disconnect_all(self) -> bool:
        """
        完全断网 (关闭WiFi + 移动数据)

        Returns:
            bool: 是否成功
        """
        logger.info("断网: 关闭WiFi和移动数据")
        try:
            self.adb.disable_wifi()
        except Exception as e:
            # 部分小米HyperOS版本 svc wifi disable 失效，回退 cmd wifi 命令
            logger.warning(f"svc wifi disable 失效({e})，尝试 cmd wifi set-wifi-enabled")
            self.adb._run_adb(
                ["shell", "cmd", "wifi", "set-wifi-enabled", "disabled"],
                timeout=15,
            )
        try:
            self.adb.disable_mobile_data()
        except Exception as e:
            logger.warning(f"关闭移动数据失败: {e}")
        return True

    def restore_all(self) -> bool:
        """
        恢复全部网络 (关闭飞行模式 + 开启WiFi/移动数据)

        弱网用例teardown必须调用，防止污染后续用例。

        Returns:
            bool: 是否成功
        """
        logger.info("恢复网络: 关闭飞行模式，开启WiFi和移动数据")
        try:
            self.adb.set_airplane_mode(False)
        except Exception as e:
            logger.warning(f"关闭飞行模式失败: {e}")
        try:
            self.adb.enable_wifi()
        except Exception as e:
            logger.warning(f"开启WiFi失败: {e}")
        try:
            self.adb.enable_mobile_data()
        except Exception as e:
            logger.warning(f"开启移动数据失败: {e}")
        return True

    # ============================================================
    # 连通性校验
    # ============================================================

    def is_offline(self) -> bool:
        """
        检查当前是否断网 (ping外网探测)

        Returns:
            bool: True表示无网络
        """
        result = self.adb._run_adb(
            ["shell", "ping", "-c", "1", "-W", "2", "8.8.8.8"],
            timeout=15,
        )
        return result["returncode"] != 0 or "1 received" not in result["stdout"]

    def check_connectivity(self) -> Dict:
        """
        综合网络状态检查

        Returns:
            dict: {
                "offline": bool,
                "wifi": bool,       # WiFi是否启用
                "mobile_data": bool,
                "airplane": bool,
                "detail": str,      # 原始输出摘要
            }
        """
        info = {
            "offline": False,
            "wifi": False,
            "mobile_data": False,
            "airplane": False,
            "detail": "",
        }

        # 飞行模式
        result = self.adb._run_adb(
            ["shell", "settings", "get", "global", "airplane_mode_on"],
            timeout=10,
        )
        info["airplane"] = result["stdout"].strip() == "1"

        # WiFi状态
        result = self.adb._run_adb(
            ["shell", "dumpsys", "wifi"],
            timeout=15,
        )
        info["wifi"] = (
            "Wi-Fi is enabled" in result["stdout"]
            or "mWifiEnabled true" in result["stdout"]
        )

        # 移动数据状态 (connectivity服务)
        result = self.adb._run_adb(
            ["shell", "dumpsys", "connectivity"],
            timeout=15,
        )
        info["mobile_data"] = (
            "Mobile Data State: CONNECTED" in result["stdout"]
            or "ActiveNetwork: TRANSPORT_CELLULAR" in result["stdout"]
        )

        info["offline"] = not (info["wifi"] or info["mobile_data"]) and not info["airplane"]
        # 飞行模式下也是断网的
        if info["airplane"]:
            info["offline"] = True
        info["detail"] = (
            f"airplane={info['airplane']} wifi={info['wifi']} "
            f"mobile={info['mobile_data']} -> offline={info['offline']}"
        )
        return info

    # ============================================================
    # 弱网限速 (接口预留)
    # ============================================================

    def get_throttle_controller(self) -> "ThrottleController":
        """
        获取弱网限速控制器 (按config.network.throttle.backend选择)

        默认返回 NullThrottleController (未配置后端时的占位)。
        实现mitmproxy/Charles后端后在此注册。

        Returns:
            ThrottleController: 限速控制器实例
        """
        try:
            config = ConfigManager()
            backend = config.get("network.throttle.backend", "none")
        except Exception:
            backend = "none"

        if backend in ("mitmproxy", "charles"):
            logger.warning(
                f"配置了 {backend} 限速后端但尚未实现，"
                f"请按 docs/弱网测试方案.md 接入代理限速"
            )
        else:
            logger.info("弱网限速后端未配置(backend=none)，限速能力不可用")
        return NullThrottleController()


class ThrottleController(ABC):
    """
    弱网限速抽象协议 (预留)

    真机弱网限速必须通过PC侧代理: 手机WiFi代理指向PC，
    mitmproxy/Charles在PC侧对流量做限速/丢包/延迟。

    实现新后端时继承此类并注册到 NetworkController.get_throttle_controller()。
    接入步骤见 docs/弱网测试方案.md。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """后端名称: mitmproxy / charles 等"""

    @abstractmethod
    def available(self) -> bool:
        """后端是否可用 (服务是否在运行)"""

    @abstractmethod
    def apply(self, down_kbps: int, up_kbps: int, latency_ms: int) -> bool:
        """
        应用限速参数

        Args:
            down_kbps: 下行带宽(kbps)
            up_kbps: 上行带宽(kbps)
            latency_ms: 网络延迟(毫秒)

        Returns:
            bool: 是否成功
        """

    @abstractmethod
    def remove(self) -> bool:
        """移除限速，恢复正常网络"""


class NullThrottleController(ThrottleController):
    """
    未配置后端时的占位实现

    available()始终返回False，apply()仅WARN提示，
    保证调用方代码路径完整但不会误操作。
    """

    @property
    def name(self) -> str:
        return "none"

    def available(self) -> bool:
        return False

    def apply(self, down_kbps: int, up_kbps: int, latency_ms: int) -> bool:
        logger.warning(
            f"弱网限速不可用: 未配置代理后端。"
            f"请安装mitmproxy或Charles，并按 docs/弱网测试方案.md 接入"
        )
        return False

    def remove(self) -> bool:
        return True
