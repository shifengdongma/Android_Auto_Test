# -*- coding: utf-8 -*-
"""
APK管理模块

功能:
    - 本地APK文件解析 (包名/版本/启动Activity)
    - 设备已装版本检测与对比
    - 安装 / 卸载 / 覆盖升级
    - 一键就绪 (ensure_app_ready): 自动判断需要安装还是升级

版本解析优先级:
    1. aapt dump badging (Android SDK build-tools, 信息最全)
    2. pyaxmlparser (纯Python回退, 无build-tools环境可用)
    3. 文件名启发式 (如 app_v1.2.3_4.apk)

使用示例:
    from utils.apk_manager import APKManager

    apk_mgr = APKManager()
    info = apk_mgr.parse_apk_info("apk/app_v1.2.3.apk")
    report = apk_mgr.ensure_app_ready()  # 一键安装/升级
"""

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.adb_helper import ADBHelper

try:
    from config.config_manager import ConfigManager
except ImportError:  # 兜底: 直接运行脚本时使用
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class APKManager:
    """
    APK管理工具类

    提供本地APK解析、设备版本对比、安装/卸载/升级的统一接口。
    所有adb操作委托给 ADBHelper，失败返回空值并WARN，不抛异常。
    """

    # 文件名启发式: 匹配 app_v1.2.3_4.apk / app-1.2.3.apk 等常见命名
    _FILENAME_PATTERN = re.compile(
        r"(?i)(?:v?)(\d+\.\d+(?:\.\d+)?)[_\-]?(\d+)?(?=\.apk)"
    )

    def __init__(
        self,
        adb: Optional[ADBHelper] = None,
        config: Optional[ConfigManager] = None,
    ):
        """
        初始化APK管理器

        Args:
            adb: ADBHelper实例，默认新建
            config: ConfigManager实例，默认加载单例
        """
        self.adb = adb or ADBHelper()
        self.config = config or ConfigManager()
        # 初始化时探测aapt，缓存结果 (None表示未找到)
        self._aapt_path = self._find_aapt()

    # ============================================================
    # aapt探测
    # ============================================================

    def _find_aapt(self) -> Optional[str]:
        """
        探测aapt可执行文件路径

        探测顺序:
            1. config.apk.aapt_path 显式配置
            2. ANDROID_HOME/build-tools/*/aapt.exe
            3. ANDROID_SDK_ROOT/build-tools/*/aapt.exe
            4. %LOCALAPPDATA%/Android/Sdk/build-tools/*/aapt.exe
            5. 系统PATH中的 aapt / aapt.bat

        Returns:
            str|None: aapt路径，未找到返回None
        """
        # 1. 显式配置
        configured = self.config.get("apk.aapt_path", "")
        if configured and Path(configured).exists():
            logger.info(f"使用配置的aapt: {configured}")
            return configured

        # 2-4. 常见SDK安装路径
        candidates = []
        for env_var in ["ANDROID_HOME", "ANDROID_SDK_ROOT"]:
            sdk = os.environ.get(env_var, "")
            if sdk:
                candidates.append(Path(sdk) / "build-tools")
        localappdata = os.environ.get("LOCALAPPDATA", "")
        if localappdata:
            candidates.append(Path(localappdata) / "Android" / "Sdk" / "build-tools")

        for bt_dir in candidates:
            if not bt_dir.exists():
                continue
            # 取版本号最大的build-tools目录
            versions = sorted(
                (d for d in bt_dir.iterdir() if d.is_dir()),
                key=lambda d: self._version_key(d.name),
                reverse=True,
            )
            for v in versions:
                exe = v / "aapt.exe"
                if exe.exists():
                    logger.info(f"探测到aapt: {exe}")
                    return str(exe)

        # 5. 系统PATH
        for path in os.environ.get("PATH", "").split(os.pathsep):
            for name in ("aapt.exe", "aapt.bat", "aapt"):
                candidate = Path(path) / name
                if candidate.exists():
                    logger.info(f"PATH中找到aapt: {candidate}")
                    return str(candidate)

        logger.warning("未找到aapt，将使用pyaxmlparser/文件名启发式解析APK")
        return None

    @staticmethod
    def _version_key(name: str) -> tuple:
        """将版本目录名转为可排序的元组 (如 36.0.0 -> (36,0,0))"""
        parts = []
        for seg in re.findall(r"\d+", name)[:3]:
            parts.append(int(seg))
        return tuple(parts)

    # ============================================================
    # 本地APK解析
    # ============================================================

    def parse_apk_info(self, apk_path: str) -> Dict[str, Any]:
        """
        解析本地APK文件信息

        优先级: aapt > pyaxmlparser > 文件名启发式

        Args:
            apk_path: APK文件路径

        Returns:
            dict: {
                "apk_path": str,
                "package_name": str|None,
                "version_name": str|None,
                "version_code": int|None,
                "main_activity": str|None,
                "parse_method": str,   # aapt / pyaxmlparser / filename / unknown
            }
        """
        path = Path(apk_path)
        info = {
            "apk_path": str(path),
            "package_name": None,
            "version_name": None,
            "version_code": None,
            "main_activity": None,
            "parse_method": "unknown",
        }

        if not path.exists():
            logger.error(f"APK文件不存在: {apk_path}")
            return info

        # 1. aapt优先
        if self._aapt_path:
            info = self._parse_with_aapt(path, info)

        # 2. pyaxmlparser回退
        if not info["package_name"]:
            info = self._parse_with_pyaxmlparser(path, info)

        # 3. 文件名启发式兜底
        if not info["version_name"]:
            info = self._parse_from_filename(path, info)

        logger.info(
            f"APK解析[{info['parse_method']}]: {path.name} "
            f"pkg={info['package_name']} v={info['version_name']} "
            f"code={info['version_code']}"
        )
        return info

    def _parse_with_aapt(self, path: Path, info: Dict) -> Dict:
        """使用aapt dump badging解析APK"""
        try:
            result = subprocess.run(
                [self._aapt_path, "dump", "badging", str(path)],
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8",
                errors="replace",
            )
            output = result.stdout
            if not output:
                return info

            # package: name='com.example' versionCode='10' versionName='1.0.0'
            m = re.search(
                r"package:\s+name='([^']+)' versionCode='(\d+)' versionName='([^']+)'",
                output,
            )
            if m:
                info["package_name"] = m.group(1)
                info["version_code"] = int(m.group(2))
                info["version_name"] = m.group(3)

            # launchable-activity: name='com.example.MainActivity'
            m = re.search(r"launchable-activity:\s+name='([^']+)'", output)
            if m:
                info["main_activity"] = m.group(1)

            info["parse_method"] = "aapt"
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.warning(f"aapt解析失败({e})，尝试回退方案")
        return info

    def _parse_with_pyaxmlparser(self, path: Path, info: Dict) -> Dict:
        """使用pyaxmlparser (纯Python) 解析APK清单"""
        try:
            from pyaxmlparser import APK  # lazy import, 避免硬依赖

            apk = APK(str(path))
            info["package_name"] = info["package_name"] or apk.package
            if apk.version_code:
                info["version_code"] = int(apk.version_code)
            info["version_name"] = info["version_name"] or apk.version_name
            info["parse_method"] = "pyaxmlparser"
        except ImportError:
            logger.debug("未安装pyaxmlparser，跳过")
        except Exception as e:
            logger.warning(f"pyaxmlparser解析失败: {e}")
        return info

    def _parse_from_filename(self, path: Path, info: Dict) -> Dict:
        """从文件名启发式解析版本 (app_v1.2.3_4.apk)"""
        m = self._FILENAME_PATTERN.search(path.name)
        if m:
            info["version_name"] = info["version_name"] or m.group(1)
            if m.group(2):
                info["version_code"] = info["version_code"] or int(m.group(2))
            if info["parse_method"] == "unknown":
                info["parse_method"] = "filename"
        return info

    # ============================================================
    # 本地APK扫描
    # ============================================================

    def get_apk_dir(self) -> Path:
        """
        获取本地APK目录 (config.apk.dir, 相对mobile-test-framework/根目录)

        目录不存在时自动创建。
        """
        apk_dir = self.config.get("apk.dir", "apk")
        path = Path(__file__).parent.parent / apk_dir
        path.mkdir(parents=True, exist_ok=True)
        return path

    def find_apk_files(self, directory: Optional[str] = None) -> List[Path]:
        """
        扫描本地APK文件

        Args:
            directory: 目录路径，默认 config.apk.dir

        Returns:
            list[Path]: APK文件列表 (按修改时间排序)
        """
        path = Path(directory) if directory else self.get_apk_dir()
        if not path.exists():
            logger.warning(f"APK目录不存在: {path}")
            return []
        files = sorted(path.glob("*.apk"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not files:
            logger.warning(f"APK目录为空: {path}")
        return files

    def get_latest_apk(self, directory: Optional[str] = None) -> Optional[Path]:
        """
        获取最新版本APK

        多个APK时按version_code取最大，解析失败者排后并WARN。

        Returns:
            Path|None: 最新APK路径，无APK返回None
        """
        files = self.find_apk_files(directory)
        if not files:
            return None

        parsed = []
        for f in files:
            info = self.parse_apk_info(str(f))
            parsed.append((f, info))

        # 有version_code的按code排序，无的排后面
        parsed.sort(
            key=lambda p: (p[1]["version_code"] is None, p[1]["version_code"] or -1),
            reverse=True,
        )
        return parsed[0][0]

    # ============================================================
    # 设备版本对比
    # ============================================================

    def get_installed_version(
        self, package_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取设备上已安装应用的版本信息

        Args:
            package_name: 包名，默认 config.apk.package_name

        Returns:
            dict: {
                "package_name": str,
                "is_installed": bool,
                "version_name": str|None,
                "version_code": int|None,
            }
        """
        pkg = package_name or self.config.get("apk.package_name", "com.dolphin.atc")
        if not self.adb.is_app_installed(pkg):
            return {
                "package_name": pkg,
                "is_installed": False,
                "version_name": None,
                "version_code": None,
            }

        info = self.adb.get_app_info(pkg)
        version_code = None
        try:
            version_code = int(info.get("version_code", ""))
        except (TypeError, ValueError):
            pass

        return {
            "package_name": pkg,
            "is_installed": True,
            "version_name": info.get("version_name"),
            "version_code": version_code,
        }

    def compare_versions(self, local_info: Dict, installed_info: Dict) -> str:
        """
        对比本地APK与设备已装版本

        Args:
            local_info: parse_apk_info() 的结果
            installed_info: get_installed_version() 的结果

        Returns:
            str: "newer" (本地更新) / "same" / "older" (设备更新) / "not_installed"
        """
        if not installed_info.get("is_installed"):
            return "not_installed"

        local_code = local_info.get("version_code")
        installed_code = installed_info.get("version_code")

        # version_code主判 (两者都有时)
        if local_code is not None and installed_code is not None:
            if local_code > installed_code:
                return "newer"
            if local_code < installed_code:
                return "older"
            return "same"

        # version_code不可比时用version_name字符串
        local_name = local_info.get("version_name") or ""
        installed_name = installed_info.get("version_name") or ""
        if not local_name or not installed_name:
            return "same"  # 均不可比，视为相同避免误升级
        return "newer" if local_name > installed_name else "same"

    # ============================================================
    # 安装/卸载/升级
    # ============================================================

    def install(self, apk_path: str, upgrade: bool = True) -> bool:
        """
        安装APK

        Args:
            apk_path: APK文件路径
            upgrade: True使用覆盖安装(-r -d保留数据)，False先卸载再装(干净安装)

        Returns:
            bool: 是否成功
        """
        info = self.parse_apk_info(apk_path)
        pkg = info.get("package_name")

        if not upgrade and pkg and self.adb.is_app_installed(pkg):
            logger.info(f"干净安装: 先卸载 {pkg}")
            if not self.adb.uninstall_app(pkg):
                logger.warning(f"卸载旧版本失败: {pkg}")

        return self.adb.install_app(apk_path)

    def uninstall(self, package_name: Optional[str] = None) -> bool:
        """
        卸载应用并确认

        Args:
            package_name: 包名，默认 config.apk.package_name

        Returns:
            bool: 卸载是否成功
        """
        pkg = package_name or self.config.get("apk.package_name", "com.dolphin.atc")
        if not self.adb.is_app_installed(pkg):
            logger.info(f"应用未安装，无需卸载: {pkg}")
            return True
        ok = self.adb.uninstall_app(pkg)
        # 确认卸载结果
        if ok and self.adb.is_app_installed(pkg):
            logger.warning(f"卸载命令成功但应用仍存在: {pkg}")
            return False
        return ok

    def ensure_app_ready(
        self,
        apk_path: Optional[str] = None,
        install_if_missing: bool = True,
    ) -> Dict[str, Any]:
        """
        一键就绪: 自动判断安装/升级/跳过

        流程: 扫描本地APK → 解析版本 → 与设备对比 → 按需安装/升级

        Args:
            apk_path: 指定APK路径，None则取最新APK
            install_if_missing: 设备未安装时是否自动安装

        Returns:
            dict: {
                "apk_path": str|None,
                "local_version": str|None,
                "installed_version": str|None,
                "action": "installed"|"upgraded"|"skipped"|"missing_apk"|"install_failed",
                "success": bool,
            }
        """
        # 1. 确定目标APK
        target = Path(apk_path) if apk_path else self.get_latest_apk()
        if not target:
            logger.warning("未找到本地APK，跳过就绪检查")
            return {
                "apk_path": None,
                "local_version": None,
                "installed_version": None,
                "action": "missing_apk",
                "success": False,
            }

        # 2. 解析本地版本
        local_info = self.parse_apk_info(str(target))
        pkg = local_info.get("package_name")
        if not pkg:
            logger.error(f"无法解析APK包名: {target}")
            return {
                "apk_path": str(target),
                "local_version": local_info.get("version_name"),
                "installed_version": None,
                "action": "install_failed",
                "success": False,
            }

        # 3. 设备版本对比
        installed_info = self.get_installed_version(pkg)
        diff = self.compare_versions(local_info, installed_info)

        if diff == "not_installed":
            if not install_if_missing:
                logger.info(f"设备未安装 {pkg}，跳过自动安装")
                return {
                    "apk_path": str(target),
                    "local_version": local_info.get("version_name"),
                    "installed_version": None,
                    "action": "skipped",
                    "success": True,
                }
            ok = self.install(str(target), upgrade=True)
            action = "installed" if ok else "install_failed"
        elif diff == "newer":
            ok = self.install(str(target), upgrade=True)
            action = "upgraded" if ok else "install_failed"
        else:
            ok = True
            action = "skipped"

        return {
            "apk_path": str(target),
            "local_version": local_info.get("version_name"),
            "installed_version": installed_info.get("version_name"),
            "action": action,
            "success": ok,
        }

    def report_status(self, directory: Optional[str] = None) -> Dict[str, Any]:
        """
        汇总报告: 本地APK列表+版本、设备版本、差异、建议动作

        供Allure attach / manual_test打印。

        Returns:
            dict: {
                "local_apks": list[dict],
                "installed": dict,
                "recommendation": str,
            }
        """
        files = self.find_apk_files(directory)
        local_apks = []
        for f in files:
            info = self.parse_apk_info(str(f))
            local_apks.append(
                {
                    "file": f.name,
                    "package_name": info.get("package_name"),
                    "version_name": info.get("version_name"),
                    "version_code": info.get("version_code"),
                }
            )

        installed = self.get_installed_version()
        recommendation = "未找到本地APK"
        if local_apks:
            latest = self.get_latest_apk(directory)
            local_info = self.parse_apk_info(str(latest))
            diff = self.compare_versions(local_info, installed)
            recommendation = {
                "newer": f"建议升级: 本地 {local_info.get('version_name')} > 设备 {installed.get('version_name')}",
                "same": f"版本一致: {installed.get('version_name')}",
                "older": f"设备版本更新: {installed.get('version_name')} > 本地 {local_info.get('version_name')}",
                "not_installed": f"设备未安装 {local_info.get('package_name')}",
            }.get(diff, "")

        return {
            "local_apks": local_apks,
            "installed": installed,
            "recommendation": recommendation,
        }
