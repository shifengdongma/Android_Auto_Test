# -*- coding: utf-8 -*-
"""
Logcat抓取与异常分析模块

功能:
    - LogcatCapture: 测试期间按包名抓取日志，测试结束attach到Allure
    - LogcatAnalyzer: 扫描日志中的ANR/崩溃/被杀事件

使用示例:
    from utils.logcat import LogcatCapture, LogcatAnalyzer

    capture = LogcatCapture()
    capture.start("com.dolphin.atc")
    # ... 执行测试 ...
    log_file = capture.stop()
    capture.attach("测试日志")

    analyzer = LogcatAnalyzer("com.dolphin.atc")
    hits = analyzer.scan(open(log_file).read())
"""

import logging
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.adb_helper import ADBHelper

logger = logging.getLogger(__name__)

try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False


class LogcatCapture:
    """
    Logcat日志抓取

    抓取策略: 启动时清空缓冲并抓全量(不按包名过滤，保证ANR/系统级事件不丢失)，
    停止时用 pidof 过滤目标包日志，保真度更高。
    """

    def __init__(
        self,
        adb: Optional[ADBHelper] = None,
        log_dir: str = "logs/logcat",
    ):
        """
        初始化抓取器

        Args:
            adb: ADBHelper实例，默认新建
            log_dir: 日志保存目录 (相对mobile-test-framework/根目录)
        """
        self.adb = adb or ADBHelper()
        self._log_dir = Path(__file__).parent.parent / log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._process: Optional[subprocess.Popen] = None
        self._log_file: Optional[Path] = None

    def start(
        self,
        package: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> None:
        """
        开始抓取日志 (非阻塞)

        Args:
            package: 目标包名 (仅用于日志命名)
            device_id: 设备ID
        """
        if self._process:
            logger.warning("Logcat抓取已在进行中，先停止旧抓取")
            self.stop()

        # 清空缓冲，确保只抓取本次测试的日志
        self.adb.clear_logcat(device_id=device_id)

        pkg_part = package or "all"
        self._log_file = self._log_dir / (
            f"logcat_{pkg_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        self._process = self.adb.start_logcat(str(self._log_file), device_id=device_id)
        logger.info(f"开始logcat抓取: {self._log_file}")

    def stop(self) -> str:
        """
        停止抓取

        Returns:
            str: 日志文件路径，未启动返回""
        """
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=10)
            except Exception as e:
                logger.warning(f"停止logcat进程异常: {e}")
            self._process = None
            logger.info(f"logcat抓取结束: {self._log_file}")
        return str(self._log_file) if self._log_file else ""

    def tail(
        self,
        lines: int = 200,
        package: Optional[str] = None,
        device_id: Optional[str] = None,
    ) -> str:
        """
        读取设备logcat末尾N行 (不启动抓取，用于失败现场)

        Args:
            lines: 取最后N行
            package: 按包名过滤 (grep -E)
            device_id: 设备ID

        Returns:
            str: 日志内容，失败返回""
        """
        try:
            cmd = [self.adb._adb]
            if device_id:
                cmd += ["-s", device_id]
            cmd += ["logcat", "-d", "-v", "threadtime"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
            output = result.stdout
            if package:
                output = "\n".join(
                    line for line in output.split("\n") if package in line
                )
            tail_lines = output.strip().split("\n")[-lines:]
            return "\n".join(tail_lines)
        except Exception as e:
            logger.warning(f"读取logcat尾部失败: {e}")
            return ""

    def attach(self, name: str = "测试日志", max_bytes: int = 50 * 1024) -> None:
        """
        将抓取的日志文件attach到Allure报告

        Args:
            name: Allure附件名称
            max_bytes: 截断大小(默认50KB，控制报告体积)
        """
        if not ALLURE_AVAILABLE:
            return
        if not self._log_file or not self._log_file.exists():
            logger.debug("日志文件不存在，跳过attach")
            return

        try:
            content = self._log_file.read_text(encoding="utf-8", errors="replace")
            if len(content) > max_bytes:
                # 保留尾部(最新日志更有价值)
                content = content[-max_bytes:]
                content = f"...(截断, 完整日志: {self._log_file})\n" + content
            allure.attach(
                content,
                name=name,
                attachment_type=allure.attachment_type.TEXT,
            )
        except Exception as e:
            logger.warning(f"日志attach失败: {e}")


class LogcatAnalyzer:
    """
    Logcat异常分析器: ANR / 崩溃 / 进程被杀检测
    """

    # ANR模式 (Android 16上仍以 "ANR in <pkg>" 出现)
    _ANR_PATTERNS = [
        r"ANR in {pkg}",
        r"Input dispatching timed out",
        r"am_anr",
        r"Application Not Responding",
    ]
    # 崩溃模式
    _CRASH_PATTERNS = [
        r"FATAL EXCEPTION",
        r"Process: {pkg}, PID: \d+",
        r"AndroidRuntime:.*{pkg}",
    ]
    # 进程被杀模式 (低内存/系统杀进程，压测关注)
    _KILL_PATTERNS = [
        r"lowmemorykiller",
        r"Killing \d+:{pkg}",
        r"has died",
    ]

    def __init__(self, package: str):
        """
        初始化分析器

        Args:
            package: 目标包名 (注入到各匹配模式)
        """
        self.package = package
        # 编译各模式
        self._patterns = [
            (kind, re.compile(p.format(pkg=re.escape(package))))
            for kind, patterns in [
                ("ANR", self._ANR_PATTERNS),
                ("CRASH", self._CRASH_PATTERNS),
                ("KILL", self._KILL_PATTERNS),
            ]
            for p in patterns
        ]

    def scan(self, text: str) -> List[Dict]:
        """
        扫描日志文本

        Args:
            text: 日志内容

        Returns:
            list[dict]: [{"kind": "ANR|CRASH|KILL", "pattern": str, "line": str, "line_no": int}]
        """
        hits = []
        lines = text.split("\n")
        for idx, line in enumerate(lines, start=1):
            for kind, pattern in self._patterns:
                if pattern.search(line):
                    hits.append(
                        {
                            "kind": kind,
                            "pattern": pattern.pattern,
                            "line": line.strip(),
                            "line_no": idx,
                        }
                    )
        return hits

    def has_anr(self, text: str) -> bool:
        """日志中是否出现ANR"""
        return any(h["kind"] == "ANR" for h in self.scan(text))

    def has_crash(self, text: str) -> bool:
        """日志中是否出现崩溃"""
        return any(h["kind"] == "CRASH" for h in self.scan(text))

    def assert_clean(
        self,
        text: str,
        attach_name: str = "ANR/崩溃日志",
        attach_context_lines: int = 3,
    ) -> None:
        """
        断言日志无ANR/崩溃/被杀事件；有命中则attach上下文并pytest.fail

        Args:
            text: 日志内容
            attach_name: Allure附件名称
            attach_context_lines: 命中行前后各取几行作为上下文
        """
        import pytest

        hits = self.scan(text)
        if not hits:
            return

        lines = text.split("\n")
        context_lines = []
        for h in hits:
            start = max(0, h["line_no"] - 1 - attach_context_lines)
            end = min(len(lines), h["line_no"] + attach_context_lines)
            context_lines.append(
                f"--- {h['kind']} @第{h['line_no']}行 (匹配: {h['pattern']}) ---"
            )
            context_lines.extend(lines[start:end])
            context_lines.append("")

        if ALLURE_AVAILABLE:
            allure.attach(
                "\n".join(context_lines),
                name=attach_name,
                attachment_type=allure.attachment_type.TEXT,
            )
        pytest.fail(f"检测到异常事件: {[h['kind'] for h in hits]}")
