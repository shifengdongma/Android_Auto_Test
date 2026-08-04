# -*- coding: utf-8 -*-
"""
日志系统

功能:
    - 统一管理测试框架日志
    - 支持控制台彩色输出 + 文件持久化
    - 按日期/大小自动轮转日志文件
    - 分级日志 (DEBUG / INFO / WARNING / ERROR)
    - 支持附加到Allure报告
    - 异常日志单独记录

使用示例:
    from utils.logger import TestLogger

    logger = TestLogger.get_logger(__name__)
    logger.info("测试开始")
    logger.error("发生异常", exc_info=True)
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class TestLogger:
    """
    测试日志管理器

    特性:
        - 双通道输出: 控制台(INFO级别) + 文件(DEBUG级别)
        - 文件按日期轮转: 每天一个日志文件
        - 文件按大小限制: 超过配置大小自动轮转
        - 异常日志单独文件: 记录ERROR级别及以上的日志
        - 彩色控制台输出: 通过colorlog实现(可选依赖)
    """

    _loggers = {}
    _initialized = False
    _log_dir: Optional[Path] = None

    @classmethod
    def get_logger(
        cls,
        name: str,
        log_dir: Optional[str] = None,
        level: str = "DEBUG",
        console_output: bool = True,
        file_output: bool = True,
    ) -> logging.Logger:
        """
        获取指定名称的Logger实例 (工厂方法)

        同一个name的Logger只会创建一次，重复调用返回已有实例。

        Args:
            name: Logger名称 (通常使用 __name__)
            log_dir: 日志目录路径，默认 "logs/"
            level: 文件输出最低级别 (DEBUG / INFO / WARNING / ERROR)
            console_output: 是否启用控制台输出
            file_output: 是否启用文件输出

        Returns:
            logging.Logger: 配置好的Logger实例

        Examples:
            >>> logger = TestLogger.get_logger(__name__)
            >>> logger.info("这是一条信息日志")
            >>> logger.error("异常发生", exc_info=True)
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Logger自身设为最低级别
        logger.propagate = False  # 避免重复输出到根Logger

        # 避免重复添加Handler
        if not logger.handlers:
            # 确定日志目录
            if log_dir is None:
                log_dir = str(Path(__file__).parent.parent / "logs")
            cls._log_dir = Path(log_dir)
            cls._log_dir.mkdir(parents=True, exist_ok=True)

            # 控制台输出
            if console_output:
                cls._add_console_handler(logger)

            # 文件输出
            if file_output:
                cls._add_file_handler(logger, level)
                cls._add_error_file_handler(logger)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def _add_console_handler(cls, logger: logging.Logger) -> None:
        """
        添加控制台输出Handler

        尝试使用colorlog实现彩色输出，失败则降级为普通输出。
        """
        try:
            import colorlog

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # 彩色格式
            color_formatter = colorlog.ColoredFormatter(
                fmt=(
                    "%(log_color)s%(asctime)s"
                    " [%(levelname)-7s]"
                    " %(name)s: %(message)s"
                ),
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            )
            console_handler.setFormatter(color_formatter)
        except ImportError:
            # 降级为普通控制台输出
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    @classmethod
    def _add_file_handler(
        cls, logger: logging.Logger, level: str = "DEBUG"
    ) -> None:
        """
        添加文件输出Handler (按日期轮转)

        日志文件命名: logs/test_20260804.log
        """
        today = datetime.now().strftime("%Y%m%d")
        log_file = cls._log_dir / f"test_{today}.log"

        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, level.upper(), logging.DEBUG))

        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s [%(levelname)-7s]"
                " %(name)s(%(filename)s:%(lineno)d): %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    @classmethod
    def _add_error_file_handler(cls, logger: logging.Logger) -> None:
        """
        添加异常日志单独输出Handler

        只记录ERROR及以上级别的日志到单独文件。
        文件命名: logs/error_20260804.log
        """
        today = datetime.now().strftime("%Y%m%d")
        error_file = cls._log_dir / f"error_{today}.log"

        error_handler = logging.handlers.RotatingFileHandler(
            filename=str(error_file),
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)

        formatter = logging.Formatter(
            fmt=(
                "%(asctime)s [%(levelname)s]"
                " %(name)s(%(filename)s:%(lineno)d):\n"
                "  Message: %(message)s\n"
                "  ----"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    @classmethod
    def get_log_file_path(cls) -> Optional[str]:
        """获取当前日志文件路径"""
        if cls._log_dir is None:
            return None
        today = datetime.now().strftime("%Y%m%d")
        return str(cls._log_dir / f"test_{today}.log")

    @classmethod
    def get_error_log_path(cls) -> Optional[str]:
        """获取当前异常日志文件路径"""
        if cls._log_dir is None:
            return None
        today = datetime.now().strftime("%Y%m%d")
        return str(cls._log_dir / f"error_{today}.log")

    @classmethod
    def shutdown(cls) -> None:
        """关闭所有Logger的Handler，释放文件资源"""
        for logger in cls._loggers.values():
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
        cls._loggers.clear()

    @classmethod
    def clear_old_logs(cls, keep_days: int = 30) -> int:
        """
        清理指定天数之前的日志文件

        Args:
            keep_days: 保留最近N天的日志

        Returns:
            int: 清理的文件数量
        """
        import time

        if cls._log_dir is None or not cls._log_dir.exists():
            return 0

        cutoff = time.time() - keep_days * 86400
        deleted = 0

        for log_file in cls._log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff:
                try:
                    log_file.unlink()
                    deleted += 1
                except OSError:
                    pass

        return deleted
