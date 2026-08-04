# -*- coding: utf-8 -*-
"""
ADB辅助工具

功能:
    - 检测ADB设备连接状态
    - 获取设备信息 (型号、系统版本、分辨率等)
    - 执行ADB命令
    - 模拟GPS位置 (用于地图/GPS定位测试)
    - 网络状态控制 (WiFi/移动数据/飞行模式)
    - 应用安装/卸载
    - 日志抓取 (logcat)

使用示例:
    from utils.adb_helper import ADBHelper

    adb = ADBHelper()
    devices = adb.get_connected_devices()
    adb.set_gps_location(22.5431, 114.0579)  # 模拟深圳坐标
"""

import logging
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ADBHelper:
    """
    ADB命令封装工具类

    封装常用ADB命令，提供统一接口操作Android设备。
    所有命令在 platform-tools/ 目录下的 adb.exe 中执行。
    如果该目录不可用，则回退到系统PATH中的adb。

    支持操作:
        - 设备检测与信息获取
        - GPS位置模拟
        - 网络状态控制
        - 应用管理
        - 日志抓取
        - 权限管理
    """

    def __init__(self, adb_path: Optional[str] = None):
        """
        初始化ADB助手

        Args:
            adb_path: adb可执行文件路径，默认自动查找
        """
        if adb_path:
            self._adb = adb_path
        else:
            # 优先使用项目内的 platform-tools
            local_adb = (
                Path(__file__).parent.parent.parent / "platform-tools" / "adb.exe"
            )
            if local_adb.exists():
                self._adb = str(local_adb)
            else:
                # 回退到系统PATH
                self._adb = "adb"

        self._verify_adb()

    def _verify_adb(self) -> None:
        """验证ADB是否可用"""
        try:
            result = self._run_adb(["version"], timeout=10)
            if result["returncode"] != 0:
                raise RuntimeError(f"ADB版本检查失败: {result['stderr']}")
            version_line = result["stdout"].split("\n")[0]
            logger.info(f"ADB工具就绪: {version_line}")
        except FileNotFoundError:
            raise RuntimeError(
                f"未找到ADB工具 (路径: {self._adb})\n"
                f"请确认:\n"
                f"  1. platform-tools/ 目录存在且包含 adb.exe\n"
                f"  2. 或 ADB已添加到系统PATH环境变量"
            )
        except Exception as e:
            raise RuntimeError(f"ADB初始化失败: {e}")

    def _run_adb(
        self,
        args: List[str],
        device_id: Optional[str] = None,
        timeout: int = 30,
    ) -> Dict[str, any]:
        """
        执行ADB命令

        Args:
            args: ADB命令参数列表 (不含adb本身)
            device_id: 指定设备ID (多设备时必须指定)
            timeout: 命令超时时间(秒)

        Returns:
            dict: {"returncode": int, "stdout": str, "stderr": str}
        """
        cmd = [self._adb]
        if device_id:
            cmd += ["-s", device_id]
        cmd += args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
            }
        except subprocess.TimeoutExpired:
            logger.warning(f"ADB命令超时({timeout}s): {' '.join(cmd)}")
            return {"returncode": -1, "stdout": "", "stderr": "Command timeout"}

    # ============================================================
    # 设备检测
    # ============================================================

    def get_connected_devices(self) -> List[Dict[str, str]]:
        """
        获取已连接的Android设备列表

        Returns:
            list[dict]: 设备列表，每个设备包含:
                - id: 设备序列号
                - status: 连接状态 (device / offline / unauthorized)
                - model: 设备型号
                - android_version: Android版本

        Examples:
            >>> adb.get_connected_devices()
            [
                {"id": "abc123", "status": "device",
                 "model": "Mi 14", "android_version": "14"}
            ]
        """
        result = self._run_adb(["devices", "-l"])
        if result["returncode"] != 0:
            logger.error(f"获取设备列表失败: {result['stderr']}")
            return []

        devices = []
        lines = result["stdout"].split("\n")[1:]  # 跳过首行 "List of devices..."

        for line in lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                device_id = parts[0]
                status = parts[1]

                device_info = {
                    "id": device_id,
                    "status": status,
                    "model": self._get_device_property(device_id, "ro.product.model"),
                    "android_version": self._get_device_property(
                        device_id, "ro.build.version.release"
                    ),
                }
                devices.append(device_info)

        logger.info(f"检测到 {len(devices)} 台已连接设备")
        return devices

    def get_first_device_id(self) -> Optional[str]:
        """
        获取第一台已连接设备的ID

        Returns:
            str: 设备ID，无设备在线返回None
        """
        devices = self.get_connected_devices()
        online = [d for d in devices if d["status"] == "device"]
        return online[0]["id"] if online else None

    def is_device_connected(self, device_id: Optional[str] = None) -> bool:
        """
        检查设备是否已连接且在线

        Args:
            device_id: 设备ID，不传则检查是否有任意设备在线

        Returns:
            bool: 设备是否在线
        """
        if device_id:
            result = self._run_adb(
                ["-s", device_id, "shell", "echo", "ok"], device_id=device_id
            )
            return result["returncode"] == 0 and "ok" in result["stdout"]
        else:
            devices = self.get_connected_devices()
            return any(d["status"] == "device" for d in devices)

    def _get_device_property(self, device_id: str, prop: str) -> str:
        """获取设备系统属性"""
        result = self._run_adb(
            ["shell", "getprop", prop],
            device_id=device_id,
        )
        return result["stdout"] if result["returncode"] == 0 else "unknown"

    # ============================================================
    # 设备信息
    # ============================================================

    def get_device_info(self, device_id: Optional[str] = None) -> Dict[str, str]:
        """
        获取设备详细信息

        Returns:
            dict: 包含型号、品牌、SDK版本、分辨率、屏幕密度等
        """
        if device_id is None:
            device_id = self.get_first_device_id()
        if device_id is None:
            raise RuntimeError("没有可用的Android设备")

        return {
            "model": self._get_device_property(device_id, "ro.product.model"),
            "brand": self._get_device_property(device_id, "ro.product.brand"),
            "manufacturer": self._get_device_property(
                device_id, "ro.product.manufacturer"
            ),
            "sdk_version": self._get_device_property(
                device_id, "ro.build.version.sdk"
            ),
            "android_version": self._get_device_property(
                device_id, "ro.build.version.release"
            ),
            "resolution": self._get_screen_resolution(device_id),
            "density": self._get_screen_density(device_id),
        }

    def _get_screen_resolution(self, device_id: str) -> str:
        """获取屏幕分辨率 (如 1080x2400)"""
        result = self._run_adb(
            ["shell", "wm", "size"], device_id=device_id
        )
        if result["returncode"] == 0:
            # 输出格式: "Physical size: 1080x2400"
            match = re.search(r"(\d+x\d+)", result["stdout"])
            return match.group(1) if match else "unknown"
        return "unknown"

    def _get_screen_density(self, device_id: str) -> str:
        """获取屏幕密度 (dpi)"""
        result = self._run_adb(
            ["shell", "wm", "density"], device_id=device_id
        )
        if result["returncode"] == 0:
            match = re.search(r"(\d+)", result["stdout"])
            return match.group(1) if match else "unknown"
        return "unknown"

    # ============================================================
    # GPS位置模拟 (用于地图/GPS定位测试)
    # ============================================================

    def set_gps_location(
        self,
        latitude: float,
        longitude: float,
        altitude: float = 0.0,
        device_id: Optional[str] = None,
    ) -> bool:
        """
        模拟GPS位置

        用于测试:
            - GPS定位功能
            - 附近起降场搜索
            - 地图定位显示

        Args:
            latitude: 纬度 (如 22.5431)
            longitude: 经度 (如 114.0579)
            altitude: 海拔高度(米)，默认0
            device_id: 设备ID

        Returns:
            bool: 是否设置成功

        Note:
            - 需要在开发者选项中开启"允许模拟位置"
            - 部分模拟器(如Android Emulator)通过 telnet 设置，
              此方法适用于真机(已root或使用mock location app)
        """
        logger.info(
            f"设置模拟GPS位置: lat={latitude}, lng={longitude}, alt={altitude}"
        )

        # 方式1: 使用 app_process (需要mock-location权限)
        cmd = [
            "shell",
            "am", "broadcast",
            "-a", "android.intent.action.LOCATION",
            "--es", "latitude", str(latitude),
            "--es", "longitude", str(longitude),
            "--es", "altitude", str(altitude),
        ]
        result = self._run_adb(cmd, device_id=device_id)

        if result["returncode"] != 0:
            # 方式2: 使用 geo fix (仅模拟器支持)
            logger.info("方式1失败，尝试模拟器方式...")
            result = self._run_adb(
                ["emu", "geo", "fix", str(longitude), str(latitude), str(altitude)],
                device_id=device_id,
            )

        success = result["returncode"] == 0
        if success:
            logger.info("GPS位置设置成功")
        else:
            logger.warning(f"GPS位置设置失败: {result['stderr']}")

        return success

    # ============================================================
    # 网络控制 (用于断网/弱网测试)
    # ============================================================

    def enable_wifi(self, device_id: Optional[str] = None) -> bool:
        """开启WiFi"""
        result = self._run_adb(
            ["shell", "svc", "wifi", "enable"], device_id=device_id
        )
        return result["returncode"] == 0

    def disable_wifi(self, device_id: Optional[str] = None) -> bool:
        """关闭WiFi"""
        result = self._run_adb(
            ["shell", "svc", "wifi", "disable"], device_id=device_id
        )
        return result["returncode"] == 0

    def enable_mobile_data(self, device_id: Optional[str] = None) -> bool:
        """开启移动数据"""
        result = self._run_adb(
            ["shell", "svc", "data", "enable"], device_id=device_id
        )
        return result["returncode"] == 0

    def disable_mobile_data(self, device_id: Optional[str] = None) -> bool:
        """关闭移动数据"""
        result = self._run_adb(
            ["shell", "svc", "data", "disable"], device_id=device_id
        )
        return result["returncode"] == 0

    def set_airplane_mode(
        self, enable: bool, device_id: Optional[str] = None
    ) -> bool:
        """
        设置飞行模式

        Args:
            enable: True=开启飞行模式, False=关闭

        Note:
            Android 4.2+ 需要通过 settings 命令控制
        """
        value = "1" if enable else "0"
        result = self._run_adb(
            [
                "shell", "settings", "put", "global",
                "airplane_mode_on", value,
            ],
            device_id=device_id,
        )
        # 广播飞行模式变更
        self._run_adb(
            [
                "shell", "am", "broadcast",
                "-a", "android.intent.action.AIRPLANE_MODE",
            ],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def disable_all_network(self, device_id: Optional[str] = None) -> None:
        """
        断开所有网络连接 (用于断网测试)

        同时关闭WiFi和移动数据。
        """
        logger.info("断开所有网络连接...")
        self.disable_wifi(device_id)
        self.disable_mobile_data(device_id)

    def enable_all_network(self, device_id: Optional[str] = None) -> None:
        """恢复所有网络连接"""
        logger.info("恢复网络连接...")
        self.enable_wifi(device_id)
        self.enable_mobile_data(device_id)

    # ============================================================
    # 应用管理
    # ============================================================

    def install_app(self, apk_path: str, device_id: Optional[str] = None) -> bool:
        """
        安装APK

        Args:
            apk_path: APK文件路径
            device_id: 设备ID

        Returns:
            bool: 安装是否成功
        """
        logger.info(f"安装APK: {apk_path}")
        result = self._run_adb(
            ["install", "-r", "-d", apk_path],
            device_id=device_id,
            timeout=120,
        )
        success = "Success" in result["stdout"]
        if success:
            logger.info("APK安装成功")
        else:
            logger.error(f"APK安装失败: {result['stdout']}")
        return success

    def uninstall_app(
        self, package_name: str, device_id: Optional[str] = None
    ) -> bool:
        """
        卸载应用

        Args:
            package_name: 应用包名
            device_id: 设备ID

        Returns:
            bool: 卸载是否成功
        """
        logger.info(f"卸载应用: {package_name}")
        result = self._run_adb(
            ["uninstall", package_name], device_id=device_id
        )
        return "Success" in result["stdout"]

    def clear_app_data(
        self, package_name: str, device_id: Optional[str] = None
    ) -> bool:
        """
        清除应用数据 (相当于重新安装)

        Args:
            package_name: 应用包名
            device_id: 设备ID
        """
        logger.info(f"清除应用数据: {package_name}")
        result = self._run_adb(
            ["shell", "pm", "clear", package_name], device_id=device_id
        )
        return result["returncode"] == 0

    def is_app_installed(
        self, package_name: str, device_id: Optional[str] = None
    ) -> bool:
        """检查应用是否已安装"""
        result = self._run_adb(
            ["shell", "pm", "list", "packages", package_name],
            device_id=device_id,
        )
        return package_name in result["stdout"]

    def get_current_activity(self, device_id: Optional[str] = None) -> str:
        """获取当前前台Activity"""
        # Android 10+ 方式
        result = self._run_adb(
            ["shell", "dumpsys", "window", "windows"],
            device_id=device_id,
        )
        match = re.search(r"mCurrentFocus=.*?\{[^}]*\s+(\S+)\}", result["stdout"])
        if match:
            return match.group(1)
        return "unknown"

    # ============================================================
    # 日志抓取
    # ============================================================

    def start_logcat(
        self,
        output_file: str,
        filters: Optional[List[str]] = None,
        device_id: Optional[str] = None,
    ) -> subprocess.Popen:
        """
        启动logcat日志抓取 (非阻塞)

        Args:
            output_file: 输出文件路径
            filters: 日志过滤标签列表，如 ["ActivityManager:*", "*:E"]
            device_id: 设备ID

        Returns:
            subprocess.Popen: 子进程对象，可调用 terminate() 停止

        Examples:
            >>> proc = adb.start_logcat("crash.log", ["*:E"])  # 只抓错误日志
            >>> # ... 执行测试 ...
            >>> proc.terminate()  # 停止抓取
        """
        cmd = [self._adb]
        if device_id:
            cmd += ["-s", device_id]
        cmd += ["logcat", "-v", "threadtime"]

        if filters:
            for f in filters:
                cmd += ["-s", f]

        logger.info(f"开始logcat抓取 -> {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            return subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
            )

    def clear_logcat(self, device_id: Optional[str] = None) -> bool:
        """清空logcat缓冲区"""
        result = self._run_adb(
            ["logcat", "-c"], device_id=device_id
        )
        return result["returncode"] == 0

    # ============================================================
    # 应用交互
    # ============================================================

    def start_app(
        self,
        package_name: str,
        activity: str,
        device_id: Optional[str] = None,
    ) -> bool:
        """
        启动应用

        Args:
            package_name: 应用包名
            activity: Activity全名
            device_id: 设备ID
        """
        component = f"{package_name}/{activity}"
        result = self._run_adb(
            ["shell", "am", "start", "-n", component],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def force_stop_app(
        self, package_name: str, device_id: Optional[str] = None
    ) -> bool:
        """强制停止应用"""
        result = self._run_adb(
            ["shell", "am", "force-stop", package_name],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def grant_permission(
        self,
        package_name: str,
        permission: str,
        device_id: Optional[str] = None,
    ) -> bool:
        """
        授予应用权限

        Args:
            package_name: 应用包名
            permission: 权限名 (如 android.permission.ACCESS_FINE_LOCATION)

        常用权限:
            - android.permission.ACCESS_FINE_LOCATION (GPS精确定位)
            - android.permission.ACCESS_COARSE_LOCATION (网络定位)
            - android.permission.CAMERA
            - android.permission.READ_EXTERNAL_STORAGE
        """
        result = self._run_adb(
            ["shell", "pm", "grant", package_name, permission],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def press_key(self, keycode: int, device_id: Optional[str] = None) -> bool:
        """
        模拟按键

        常用按键码:
            - 3: HOME
            - 4: BACK
            - 24: VOLUME_UP
            - 25: VOLUME_DOWN
            - 26: POWER
            - 82: MENU
            - 187: RECENT_APPS
        """
        result = self._run_adb(
            ["shell", "input", "keyevent", str(keycode)],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def tap(self, x: int, y: int, device_id: Optional[str] = None) -> bool:
        """模拟屏幕点击"""
        result = self._run_adb(
            ["shell", "input", "tap", str(x), str(y)],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def swipe(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration_ms: int = 300,
        device_id: Optional[str] = None,
    ) -> bool:
        """模拟屏幕滑动"""
        result = self._run_adb(
            [
                "shell", "input", "swipe",
                str(x1), str(y1), str(x2), str(y2), str(duration_ms),
            ],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def input_text(self, text: str, device_id: Optional[str] = None) -> bool:
        """
        模拟文本输入 (仅支持ASCII字符)

        注意: 中文输入请使用Appium的send_keys方法
        """
        # 转义特殊字符
        escaped = text.replace(" ", "%s").replace("&", "\\&")
        result = self._run_adb(
            ["shell", "input", "text", escaped],
            device_id=device_id,
        )
        return result["returncode"] == 0

    def reboot(self, device_id: Optional[str] = None) -> bool:
        """重启设备"""
        logger.info("正在重启设备...")
        result = self._run_adb(["reboot"], device_id=device_id, timeout=10)
        return result["returncode"] == 0

    def take_screenshot_adb(
        self,
        output_path: str,
        device_id: Optional[str] = None,
    ) -> bool:
        """
        通过ADB截图 (不依赖Appium)

        Args:
            output_path: 输出文件路径 (.png)
            device_id: 设备ID

        Returns:
            bool: 截图是否成功
        """
        remote_path = "/sdcard/screenshot_temp.png"
        # 设备端截图
        result = self._run_adb(
            ["shell", "screencap", "-p", remote_path],
            device_id=device_id,
        )
        if result["returncode"] != 0:
            return False

        # 拉取到本地
        result = self._run_adb(
            ["pull", remote_path, output_path],
            device_id=device_id,
        )
        # 清理远程文件
        self._run_adb(
            ["shell", "rm", remote_path],
            device_id=device_id,
        )
        return result["returncode"] == 0
