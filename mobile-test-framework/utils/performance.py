# -*- coding: utf-8 -*-
"""
性能采集模块

功能:
    - CPU/内存/电量快照采集 (dumpsys/top)
    - 启动耗时测量 (am start -W, 委托AppLifecycleManager)
    - 页面操作响应时间 (timer上下文管理器)
    - 定时采样线程 (长场景性能监控)
    - 阈值校验 (warn_only默认 / strict)
    - CSV输出 (utf-8-sig, Excel可直接打开) + Allure展示

性能指标全部走ADB层采集，不依赖driver，browser/native双模式可用。
uiautomator2 driver不提供电量API，电量必须用 dumpsys battery 读取。

使用示例:
    from utils.performance import PerformanceCollector

    pc = PerformanceCollector()
    snap = pc.snapshot_all("com.dolphin.atc")       # 三合一快照
    with pc.timer("登录流程"):                       # 响应时间计时
        login_page.login(...)
    pc.start_sampling("com.dolphin.atc")            # 定时采样
    pc.stop_sampling()                              # 停止+Allure展示
"""

import csv
import logging
import re
import statistics
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.adb_helper import ADBHelper

try:
    from config.config_manager import ConfigManager
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config.config_manager import ConfigManager

try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False

logger = logging.getLogger(__name__)

# 性能指标的中文名与单位 (CSV展示用)
METRIC_META = {
    "cold_start_ms": ("冷启动耗时", "ms"),
    "warm_start_ms": ("热启动耗时", "ms"),
    "operation_response_ms": ("操作响应时间", "ms"),
    "memory_mb": ("内存(TOTAL PSS)", "MB"),
    "cpu_percent": ("CPU占用", "%"),
    "battery_drop_percent": ("电量下降", "%"),
}


class PerformanceCollector:
    """
    性能采集器

    提供快照/采样/计时/阈值/CSV/Allure一站式能力。
    所有adb失败只WARN返回空值，不抛异常破坏测试。
    """

    def __init__(
        self,
        adb: Optional[ADBHelper] = None,
        config: Optional[ConfigManager] = None,
    ):
        """
        初始化性能采集器

        Args:
            adb: ADBHelper实例，默认新建
            config: ConfigManager实例，默认加载单例
        """
        self.adb = adb or ADBHelper()
        self.config = config or ConfigManager()
        self._thresholds = self.config.get("performance.thresholds", {}) or {}
        self._policy = self.config.get("performance.threshold_policy", "warn_only")
        self._sample_interval = self.config.get("performance.sample_interval", 2)
        self._samples: List[Dict] = []
        self._sampling_thread: Optional[threading.Thread] = None
        self._sampling_active = threading.Event()
        self._csv_lock = threading.Lock()

    # ============================================================
    # 进程状态
    # ============================================================

    def get_pid(self, package: str) -> Optional[int]:
        """获取应用主进程PID，未运行返回None"""
        return self.adb.get_pid(package)

    # ============================================================
    # 单指标快照
    # ============================================================

    def snapshot_cpu(self, package: str) -> Dict[str, Any]:
        """
        CPU占用快照

        优先 top -b -n 1 -p <pid> (按表头定位%CPU列, 兼容toybox)，
        回退 dumpsys cpuinfo 正则。

        Returns:
            dict: {"cpu_percent": float|None, "user_percent": float|None,
                   "kernel_percent": float|None, "ts": str}
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pid = self.get_pid(package)
        result = {"cpu_percent": None, "user_percent": None, "kernel_percent": None, "ts": ts}

        try:
            if pid:
                # 方式1: top按进程 (表头含%CPU)
                output = self.adb.top_snapshot(pid=pid)
                lines = output.split("\n")
                header_idx = None
                cpu_col = None
                for i, line in enumerate(lines):
                    if "%CPU" in line:
                        header_idx = i
                        parts = line.split()
                        cpu_col = next(
                            (j for j, p in enumerate(parts) if "%CPU" in p), None
                        )
                        break
                if header_idx is not None and cpu_col is not None:
                    for line in lines[header_idx + 1:]:
                        parts = line.split()
                        if parts and parts[0] == str(pid):
                            try:
                                result["cpu_percent"] = float(parts[cpu_col])
                            except (ValueError, IndexError):
                                pass
                            break

            # 方式2: dumpsys cpuinfo回退
            if result["cpu_percent"] is None:
                output = self.adb.cpuinfo_snapshot(package)
                m = re.search(r"^(\d+(?:\.\d+)?)%\s+\d+/" + re.escape(package),
                              output, re.MULTILINE)
                if m:
                    result["cpu_percent"] = float(m.group(1))
        except Exception as e:
            logger.warning(f"CPU快照失败: {e}")

        return result

    def snapshot_memory(self, package: str) -> Dict[str, Any]:
        """
        内存占用快照 (dumpsys meminfo)

        Android 8+ 使用 "TOTAL PSS:" 行，旧系统回退 "TOTAL:" 行。

        Returns:
            dict: {"total_pss_kb": int|None, "java_heap_kb": int|None,
                   "total_kb": int|None, "ts": str}
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {"total_pss_kb": None, "java_heap_kb": None, "total_kb": None, "ts": ts}

        try:
            output = self.adb.meminfo_snapshot(package)
            # Android 8+: TOTAL PSS (总PSS, 最接近真实占用)
            m = re.search(r"TOTAL PSS:\s+([\d,]+)", output)
            if m:
                result["total_pss_kb"] = int(m.group(1).replace(",", ""))
            else:
                # 旧格式: App Summary段的 TOTAL
                m = re.search(r"^\s*TOTAL:\s+([\d,]+)", output, re.MULTILINE)
                if m:
                    result["total_kb"] = int(m.group(1).replace(",", ""))
            # Java堆大小 (App Summary段)
            m = re.search(r"Java Heap:\s+([\d,]+)", output)
            if m:
                result["java_heap_kb"] = int(m.group(1).replace(",", ""))
        except Exception as e:
            logger.warning(f"内存快照失败: {e}")

        return result

    def snapshot_battery(self) -> Dict[str, Any]:
        """
        电量快照 (dumpsys battery)

        注意: battery服务只读；若其他工具曾执行 dumpsys battery set level N
              (测试态)，必须先 dumpsys battery reset 恢复真实电量。

        Returns:
            dict: {"level": int|None, "status_text": str,
                   "temperature_c": float|None, "voltage_mv": int|None, "ts": str}
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = {"level": None, "status_text": "unknown", "temperature_c": None,
                  "voltage_mv": None, "ts": ts}

        try:
            output = self.adb.battery_snapshot()

            # 电量百分比: level / scale
            m = re.search(r"level:\s+(\d+)", output)
            m2 = re.search(r"scale:\s+(\d+)", output)
            if m and m2:
                scale = int(m2.group(1)) or 100
                result["level"] = int(round(int(m.group(1)) * 100 / scale))

            # 状态: 2充电 3放电 4未充 5满
            status_map = {2: "charging", 3: "discharging", 4: "not_charging", 5: "full"}
            m = re.search(r"status:\s+(\d+)", output)
            if m:
                result["status_text"] = status_map.get(int(m.group(1)), "unknown")

            # 温度 (0.1°C)
            m = re.search(r"temperature:\s+(\d+)", output)
            if m:
                result["temperature_c"] = float(m.group(1)) / 10.0

            # 电压 (mV)
            m = re.search(r"voltage:\s+(\d+)", output)
            if m:
                result["voltage_mv"] = int(m.group(1))
        except Exception as e:
            logger.warning(f"电量快照失败: {e}")

        return result

    def snapshot_all(self, package: str) -> Dict[str, Any]:
        """
        三合一快照 (CPU + 内存 + 电量) 并打阈值标

        Returns:
            dict: {"cpu": ..., "memory": ..., "battery": ..., "ts": str}
        """
        snap = {
            "cpu": self.snapshot_cpu(package),
            "memory": self.snapshot_memory(package),
            "battery": self.snapshot_battery(),
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        # 阈值打标 (warn/fail/ok，不抛异常)
        snap["cpu"]["threshold_result"] = self.check_threshold(
            "cpu_percent", snap["cpu"].get("cpu_percent") or 0
        )
        pss_kb = snap["memory"].get("total_pss_kb") or snap["memory"].get("total_kb") or 0
        snap["memory"]["threshold_result"] = self.check_threshold("memory_mb", pss_kb / 1024)
        return snap

    # ============================================================
    # 启动耗时
    # ============================================================

    def measure_startup(
        self,
        package: Optional[str] = None,
        activity: Optional[str] = None,
        cold: bool = True,
        rounds: int = 3,
    ) -> Dict[str, Any]:
        """
        测量启动耗时 (委托AppLifecycleManager)

        Args:
            package: 包名，默认config设备配置
            activity: Activity，默认config设备配置
            cold: True冷启动(force-stop后) / False热启动(后台回前台)
            rounds: 测量轮次

        Returns:
            dict: {"values": [...], "avg", "median", "min", "max", "threshold_result"}
        """
        # lazy import避免循环依赖
        from utils.app_lifecycle import AppLifecycleManager

        lifecycle = AppLifecycleManager(adb=self.adb, config=self.config)
        if cold:
            stats = lifecycle.cold_start_time(package=package, activity=activity, rounds=rounds)
        else:
            stats = lifecycle.warm_start_time(package=package, activity=activity, rounds=rounds)

        values = stats.get("values", [])
        median = stats.get("median", 0)
        metric = "cold_start_ms" if cold else "warm_start_ms"
        stats["metric"] = metric
        stats["threshold_result"] = self.check_threshold(metric, median) if values else "ok"
        return stats

    # ============================================================
    # 操作响应时间计时
    # ============================================================

    class _Timer:
        """timer上下文管理器的内部实现"""

        def __init__(self, collector: "PerformanceCollector", name: str):
            self.collector = collector
            self.name = name
            self.elapsed_ms: Optional[float] = None
            self._start = 0.0

        def __enter__(self):
            self._start = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.elapsed_ms = round((time.perf_counter() - self._start) * 1000, 1)
            result = self.collector.check_threshold(
                "operation_response_ms", self.elapsed_ms
            )
            logger.info(f"操作响应时间 [{self.name}]: {self.elapsed_ms}ms -> {result}")
            # 记录到采样列表供CSV输出
            self.collector._samples.append(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "test_name": self.name,
                    "metric": "operation_response_ms",
                    "value": self.elapsed_ms,
                    "result": result,
                }
            )
            return False  # 不吞异常

    def timer(self, name: str) -> "_Timer":
        """
        页面操作响应时间计时器

        Usage:
            with pc.timer("登录流程"):
                login_page.login(...)
        """
        return self._Timer(self, name)

    # ============================================================
    # 定时采样线程
    # ============================================================

    def start_sampling(
        self,
        package: str,
        interval: Optional[float] = None,
        duration: Optional[float] = None,
    ) -> None:
        """
        启动定时采样线程 (daemon)

        Args:
            package: 目标包名
            interval: 采样间隔(秒)，默认config.performance.sample_interval
            duration: 最长采样时长(秒)，None则需手动stop_sampling
        """
        if self._sampling_active.is_set():
            logger.warning("采样已在进行中，忽略重复启动")
            return

        interval = interval or self._sample_interval
        self._samples = []
        self._sampling_active.set()

        def _worker():
            while self._sampling_active.is_set():
                try:
                    snap = self.snapshot_all(package)
                    self._samples.append(
                        {
                            "timestamp": snap["ts"],
                            "test_name": "sampling",
                            "package": package,
                            "cpu_percent": snap["cpu"].get("cpu_percent"),
                            "memory_kb": snap["memory"].get("total_pss_kb")
                            or snap["memory"].get("total_kb"),
                            "battery_level": snap["battery"].get("level"),
                        }
                    )
                except Exception as e:
                    logger.warning(f"采样线程异常: {e}")
                time.sleep(interval)

        self._sampling_thread = threading.Thread(
            target=_worker, name="perf-sampling", daemon=True
        )
        self._sampling_thread.start()
        logger.info(f"开始定时采样: {package} interval={interval}s")

        if duration:
            # 定时自动停止
            def _auto_stop():
                time.sleep(duration)
                self.stop_sampling()

            threading.Thread(target=_auto_stop, name="perf-auto-stop", daemon=True).start()

    def stop_sampling(self) -> List[Dict]:
        """
        停止采样并返回样本列表

        计算均值/峰值，attach到Allure (CSV+摘要文本)。

        Returns:
            list[dict]: 采样样本
        """
        self._sampling_active.clear()
        if self._sampling_thread:
            self._sampling_thread.join(timeout=5)
            self._sampling_thread = None

        samples = list(self._samples)
        if not samples:
            logger.warning("无采样数据")
            return samples

        # 统计摘要
        cpus = [s["cpu_percent"] for s in samples if s.get("cpu_percent") is not None]
        mems = [s["memory_kb"] for s in samples if s.get("memory_kb") is not None]
        summary = {
            "samples": len(samples),
            "cpu_avg": round(statistics.mean(cpus), 2) if cpus else None,
            "cpu_max": round(max(cpus), 2) if cpus else None,
            "memory_avg_mb": round(statistics.mean(mems) / 1024, 1) if mems else None,
            "memory_max_mb": round(max(mems) / 1024, 1) if mems else None,
        }
        logger.info(f"采样完成: {summary}")

        # Allure展示
        if ALLURE_AVAILABLE:
            lines = ["采样统计摘要", "-" * 40]
            for k, v in summary.items():
                lines.append(f"{k}: {v}")
            lines += ["", "原始样本 (csv):"]
            for s in samples[-20:]:  # 最多展示20行原始
                lines.append(
                    f"{s['timestamp']} cpu={s.get('cpu_percent')}% "
                    f"mem={s.get('memory_kb')}KB bat={s.get('battery_level')}%"
                )
            allure.attach("\n".join(lines), name="性能采样摘要", attachment_type=allure.attachment_type.TEXT)

        # 写CSV
        rows = [
            {
                "timestamp": s["timestamp"],
                "test_name": s.get("test_name", "sampling"),
                "metric": metric_name,
                "value": s.get(key),
                "package": s.get("package"),
            }
            for s in samples
            for metric_name, key in [
                ("cpu_percent", "cpu_percent"),
                ("memory_kb", "memory_kb"),
                ("battery_level", "battery_level"),
            ]
        ]
        self.write_csv(rows)
        return samples

    # ============================================================
    # 阈值校验
    # ============================================================

    def check_threshold(self, metric: str, value: float) -> str:
        """
        阈值校验 (永不抛异常)

        Args:
            metric: 指标名 (cold_start_ms/warm_start_ms/operation_response_ms/
                    memory_mb/cpu_percent/battery_drop_percent)
            value: 实际值

        Returns:
            str: "ok" (未超限) / "warn" (超限但warn_only) / "fail" (strict模式超限)
        """
        threshold = self._thresholds.get(metric)
        if threshold is None:
            return "ok"

        # 电量下降指标: 数值本身是下降量，阈值语义一致
        over = value > threshold
        if not over:
            return "ok"

        # strict模式由 --perf-strict 参数或 config 控制
        strict = self._policy == "strict"
        if strict:
            logger.warning(f"阈值超限(strict): {metric}={value} > {threshold}")
            return "fail"
        logger.warning(f"阈值超限(warn): {metric}={value} > {threshold} (仅提示)")
        return "warn"

    def assert_within_threshold(self, metric: str, value: float, hard: bool = False) -> None:
        """
        断言指标在阈值内

        Args:
            metric: 指标名
            value: 实际值
            hard: True则超限时pytest.fail (覆盖warn_only)；False仅记录
        """
        import pytest

        result = self.check_threshold(metric, value)
        if result == "fail" or (result == "warn" and hard):
            pytest.fail(
                f"性能指标超限: {metric}={value} (阈值: {self._thresholds.get(metric)})"
            )

    # ============================================================
    # CSV输出与报告
    # ============================================================

    def write_csv(
        self,
        rows: Optional[List[Dict]] = None,
        path: Optional[str] = None,
    ) -> str:
        """
        写性能CSV (utf-8-sig带BOM, Excel可直接打开)

        Args:
            rows: 数据行列表，None则输出采样数据
            path: 输出路径，默认 reports/performance/perf_YYYYMMDD_HHMMSS.csv

        Returns:
            str: CSV文件路径
        """
        rows = rows or self._samples
        if not rows:
            return ""

        csv_dir = Path(__file__).parent.parent / self.config.get(
            "performance.csv_dir", "reports/performance"
        )
        csv_dir.mkdir(parents=True, exist_ok=True)
        path = path or str(
            csv_dir / f"perf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )

        fieldnames = [
            "timestamp", "test_name", "metric", "value", "unit",
            "threshold", "result", "package", "device_id", "extra",
        ]
        with self._csv_lock:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in rows:
                    metric = row.get("metric", "")
                    meta = METRIC_META.get(metric, ("", ""))
                    writer.writerow(
                        {
                            "timestamp": row.get("timestamp", ""),
                            "test_name": row.get("test_name", ""),
                            "metric": metric,
                            "value": row.get("value", ""),
                            "unit": meta[1],
                            "threshold": self._thresholds.get(metric, ""),
                            "result": row.get("result", ""),
                            "package": row.get("package", ""),
                            "device_id": row.get("device_id", ""),
                            "extra": row.get("extra", ""),
                        }
                    )
        logger.info(f"性能CSV已写入: {path}")
        return path

    def save_report(self, data: Dict, name: str = "性能报告") -> str:
        """
        保存性能报告 (JSON + Allure attach)

        Args:
            data: 报告数据
            name: Allure附件名称

        Returns:
            str: CSV文件路径 (空表示无数据)
        """
        import json

        csv_path = self.write_csv()
        if ALLURE_AVAILABLE:
            allure.attach(
                json.dumps(data, ensure_ascii=False, indent=2),
                name=name,
                attachment_type=allure.attachment_type.JSON,
            )
        return csv_path

    def attach_to_allure(self, data: Dict, name: str = "性能数据") -> None:
        """将性能数据格式化为文本attach到Allure"""
        if not ALLURE_AVAILABLE:
            return
        lines = [f"{name}:", "-" * 40]
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f"{k}:")
                for k2, v2 in v.items():
                    lines.append(f"  {k2}: {v2}")
            else:
                lines.append(f"{k}: {v}")
        allure.attach("\n".join(lines), name=name, attachment_type=allure.attachment_type.TEXT)
