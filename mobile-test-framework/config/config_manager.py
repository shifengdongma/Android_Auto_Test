# -*- coding: utf-8 -*-
"""
配置管理器

功能:
    - 加载和解析YAML配置文件
    - 支持多环境切换 (dev/test/staging)
    - 支持多设备选择
    - 提供统一的配置访问接口
    - 为后续iOS扩展预留接口

使用示例:
    from config.config_manager import ConfigManager

    cfg = ConfigManager()
    device_cfg = cfg.get_device_config(0)
    timeout = cfg.get("timeout.explicit_wait")
"""

import os
import logging
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    配置管理单例类

    负责加载YAML配置文件并提供统一的配置访问接口。
    支持:
        - 多环境切换 (通过环境变量 TEST_ENV)
        - 多设备选择 (通过环境变量 DEVICE_INDEX 或索引参数)
        - 点号路径访问 (如 "timeout.explicit_wait")
        - 为iOS扩展预留配置段
    """

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls, config_path: Optional[str] = None):
        """单例模式: 确保全局只有一个配置实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: YAML配置文件路径，默认使用 config/config.yaml
        """
        if self._initialized:
            return

        if config_path is None:
            # 默认配置路径: 当前文件所在目录下的 config.yaml
            config_path = Path(__file__).parent / "config.yaml"

        self._config_path = Path(config_path)
        self._load_config()
        self._apply_env_overrides()
        self._initialized = True

    def _load_config(self) -> None:
        """从YAML文件加载配置"""
        if not self._config_path.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self._config_path}\n"
                f"请确保 config.yaml 文件存在于 config/ 目录下"
            )

        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"配置文件解析失败: {self._config_path}\n错误: {e}")

    def _apply_env_overrides(self) -> None:
        """
        应用环境变量覆盖

        支持的环境变量:
            TEST_ENV: 切换环境 (dev/test/staging)
            DEVICE_INDEX: 选择设备索引 (0, 1, 2...)
            APPIUM_SERVER_URL: 覆盖Appium服务地址
        """
        # 环境切换
        env = os.environ.get("TEST_ENV")
        if env and env in self._config.get("environments", {}):
            self._config["active_env"] = env
            env_config = self._config["environments"][env]
            # 将环境特定配置合并到默认设备配置
            for device in self._config.get("devices", []):
                for key, value in env_config.items():
                    if key not in device:
                        device[key] = value

        # Appium服务地址覆盖
        server_url = os.environ.get("APPIUM_SERVER_URL")
        if server_url:
            self._config.setdefault("appium", {})["server_url"] = server_url

    # ============================================================
    # 公共API
    # ============================================================

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        通过点号路径获取配置值

        Args:
            key_path: 配置路径，如 "timeout.explicit_wait", "appium.server_url"
            default: 默认值

        Returns:
            配置值，不存在时返回 default

        Examples:
            >>> cfg.get("timeout.explicit_wait")
            15
            >>> cfg.get("nonexistent.key", "fallback")
            'fallback'
        """
        keys = key_path.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def get_active_env(self) -> str:
        """获取当前激活的环境名称"""
        return self._config.get("active_env", "test")

    def get_device_config(self, index: int = 0) -> Dict[str, Any]:
        """
        获取指定索引的设备配置

        Args:
            index: 设备索引，0为第一个设备。
                   支持通过环境变量 DEVICE_INDEX 覆盖

        Returns:
            设备配置字典

        Raises:
            IndexError: 设备索引超出范围
        """
        # 环境变量覆盖
        env_index = os.environ.get("DEVICE_INDEX")
        if env_index is not None:
            index = int(env_index)

        devices = self._config.get("devices", [])
        if not devices:
            raise ValueError("配置文件中未定义任何设备 (devices 段为空)")

        if index < 0 or index >= len(devices):
            raise IndexError(
                f"设备索引 {index} 超出范围 (可用设备: 0~{len(devices) - 1})"
            )

        return devices[index].copy()

    def get_device_config_by_model(self, model: str) -> Optional[Dict[str, Any]]:
        """
        根据设备型号名称查找匹配的设备配置

        通过 ADB 获取的 ro.product.model 与 devices[].name 进行匹配。
        支持子串匹配：配置中的 name 是设备 model 的子串，或反过来。

        Args:
            model: 设备型号名称 (adb shell getprop ro.product.model)

        Returns:
            匹配的设备配置字典，未找到返回 None

        Examples:
            >>> cfg.get_device_config_by_model("NOH-AN01")
            {"name": "NOH-AN01", "platform_version": "12", ...}
            >>> cfg.get_device_config_by_model("unknown_device")
            None
        """
        if not model:
            return None
        devices = self._config.get("devices", [])
        for idx, device in enumerate(devices):
            name = device.get("name", "")
            if name and (name in model or model in name):
                logger.debug(
                    f"设备型号匹配: model='{model}' -> devices[{idx}].name='{name}'"
                )
                return device.copy()
        return None

    def get_device_config_by_udid(self, udid: str) -> Optional[Dict[str, Any]]:
        """
        根据设备 UDID/序列号 查找匹配的设备配置

        Args:
            udid: 设备序列号 (adb devices 输出的 ID)

        Returns:
            匹配的设备配置字典，未找到返回 None
        """
        if not udid:
            return None
        devices = self._config.get("devices", [])
        for idx, device in enumerate(devices):
            cfg_udid = device.get("udid", "")
            if cfg_udid and cfg_udid == udid:
                logger.debug(
                    f"设备UDID匹配: udid='{udid}' -> devices[{idx}]"
                )
                return device.copy()
        return None

    def get_all_devices(self) -> List[Dict[str, Any]]:
        """获取所有Android设备配置列表"""
        return self._config.get("devices", [])

    def get_ios_device_config(self, index: int = 0) -> Dict[str, Any]:
        """
        获取iOS设备配置 (预留扩展接口)

        Args:
            index: iOS设备索引

        Returns:
            iOS设备配置字典
        """
        ios_devices = self._config.get("ios_devices", [])
        if not ios_devices:
            raise ValueError("配置文件中未定义iOS设备")
        if index < 0 or index >= len(ios_devices):
            raise IndexError(f"iOS设备索引 {index} 超出范围")
        return ios_devices[index].copy()

    def get_test_account(self, role: str = "default") -> Dict[str, str]:
        """
        获取测试账号

        Args:
            role: 账号角色 (default / admin)

        Returns:
            包含 username, password, email 的字典
        """
        accounts = self._config.get("test_accounts", {})
        return accounts.get(role, accounts.get("default", {}))

    def reload(self) -> None:
        """重新加载配置文件 (用于热更新场景)"""
        self._load_config()
        self._apply_env_overrides()

    @property
    def config_data(self) -> Dict[str, Any]:
        """获取完整配置字典 (只读)"""
        return self._config.copy()
