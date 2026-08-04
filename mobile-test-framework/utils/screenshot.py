# -*- coding: utf-8 -*-
"""
截图机制

功能:
    - 测试执行过程中手动/自动截图
    - 失败自动截图 (通过Pytest hook)
    - 截图自动附加到Allure报告
    - 支持自定义截图保存路径和命名规范
    - 支持截图压缩 (可选，减少磁盘占用)

使用示例:
    from utils.screenshot import ScreenshotManager

    screenshot_mgr = ScreenshotManager(driver)
    screenshot_mgr.capture("登录成功")
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False


class ScreenshotManager:
    """
    截图管理器

    职责:
        - 调用Appium Driver执行截图
        - 按规范命名和保存截图文件
        - 自动附加截图到Allure报告
        - 管理截图文件生命周期

    截图命名规范:
        {test_name}_{description}_{timestamp}.png
        例如: test_login_success_登录成功页_20260804_143052.png
    """

    def __init__(self, driver, save_dir: str = "reports/screenshots"):
        """
        初始化截图管理器

        Args:
            driver: Appium WebDriver实例
            save_dir: 截图保存目录 (相对于项目根目录)
        """
        self._driver = driver
        self._save_dir = Path(save_dir)
        self._save_dir.mkdir(parents=True, exist_ok=True)
        self._current_test_name = "unknown"

    # ============================================================
    # 公共API
    # ============================================================

    def capture(
        self,
        description: str = "",
        test_name: Optional[str] = None,
        attach_to_allure: bool = True,
    ) -> str:
        """
        执行截图并保存

        Args:
            description: 截图描述 (会出现在文件名中)
            test_name: 测试用例名称，默认使用当前设置的名称
            attach_to_allure: 是否附加到Allure报告

        Returns:
            str: 截图文件的绝对路径

        Raises:
            RuntimeError: Driver不可用时执行截图
        """
        if self._driver is None:
            raise RuntimeError("Driver未初始化，无法执行截图")

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = test_name or self._current_test_name
        safe_desc = self._sanitize_filename(description) if description else "screenshot"
        filename = f"{name}_{safe_desc}_{timestamp}.png"
        filepath = self._save_dir / filename

        # 执行截图
        try:
            self._driver.save_screenshot(str(filepath))
        except Exception as e:
            raise RuntimeError(f"截图失败: {e}")

        # 附加到Allure报告
        if attach_to_allure and ALLURE_AVAILABLE:
            self._attach_to_allure(str(filepath), description or "截图")

        return str(filepath)

    def capture_on_failure(
        self,
        test_name: str,
        exception_info: Optional[str] = None,
    ) -> Optional[str]:
        """
        失败时自动截图 (由Pytest hook调用)

        与 capture() 的区别:
            - 文件命名包含 "FAILED" 标记
            - 自动附加异常信息到Allure

        Args:
            test_name: 失败的测试用例名称
            exception_info: 异常描述信息

        Returns:
            str: 截图文件路径，失败返回None
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = self._sanitize_filename(test_name)
            filename = f"FAILED_{safe_name}_{timestamp}.png"
            filepath = self._save_dir / filename

            self._driver.save_screenshot(str(filepath))

            if ALLURE_AVAILABLE:
                self._attach_to_allure(
                    str(filepath),
                    f"失败截图 - {exception_info or '未知错误'}",
                )

            return str(filepath)
        except Exception:
            return None

    def set_test_name(self, name: str) -> None:
        """
        设置当前测试名称 (用于截图文件命名)

        Args:
            name: 测试用例名称，如 test_login_success
        """
        self._current_test_name = name

    # ============================================================
    # 内部方法
    # ============================================================

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        清理文件名中的非法字符

        替换Windows/Linux文件名不允许的字符为下划线。
        """
        illegal_chars = r'<>:"/\|?*'
        for char in illegal_chars:
            name = name.replace(char, "_")
        # 限制长度
        return name[:100]

    @staticmethod
    def _attach_to_allure(filepath: str, description: str) -> None:
        """
        将截图附加到Allure报告

        Args:
            filepath: 截图文件路径
            description: Allure附件描述
        """
        try:
            with open(filepath, "rb") as f:
                allure.attach(
                    f.read(),
                    name=description,
                    attachment_type=allure.attachment_type.PNG,
                )
        except Exception:
            pass  # Allure附加失败不影响主流程

    # ============================================================
    # 工具方法
    # ============================================================

    def get_screenshots(self, test_name: Optional[str] = None) -> list:
        """
        获取指定测试的截图文件列表

        Args:
            test_name: 测试名称 (None则返回全部)

        Returns:
            list[Path]: 截图文件路径列表
        """
        pattern = f"*{test_name}*.png" if test_name else "*.png"
        return sorted(
            self._save_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    def clean_old_screenshots(self, keep_days: int = 7) -> int:
        """
        清理过期截图

        Args:
            keep_days: 保留最近N天的截图

        Returns:
            int: 清理的文件数量
        """
        import time

        if not self._save_dir.exists():
            return 0

        cutoff = time.time() - keep_days * 86400
        deleted = 0

        for screenshot in self._save_dir.glob("*.png"):
            if screenshot.stat().st_mtime < cutoff:
                try:
                    screenshot.unlink()
                    deleted += 1
                except OSError:
                    pass

        return deleted

    @property
    def save_dir(self) -> str:
        """获取截图保存目录"""
        return str(self._save_dir)
