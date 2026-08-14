# -*- coding: utf-8 -*-
"""
单实例执行器 (single_run)

背景: 本机环境偶发同一命令被拉起两个进程, 两个Appium session抢占同一设备
导致所有UI操作无限阻塞。本执行器用原子锁文件保证同一时刻只有一个实例运行,
第二个实例检测到锁后立即退出。

用法: .venv/Scripts/python.exe single_run.py <命令...>
      例: .venv/Scripts/python.exe single_run.py .venv/Scripts/python.exe -m pytest -v
"""

import os
import subprocess
import sys
from pathlib import Path

LOCK = Path(__file__).parent / ".single_run.lock"


def _pid_alive(pid: int) -> bool:
    """检查Windows进程是否存活"""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            capture_output=True, text=True, shell=True, timeout=10,
        ).stdout
        return str(pid) in out
    except Exception:
        return False


def acquire() -> bool:
    """尝试获取锁 (O_CREAT|O_EXCL 原子创建)"""
    while True:
        try:
            fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            print(f"[single_run] 获取锁成功 (pid={os.getpid()})", flush=True)
            return True
        except FileExistsError:
            try:
                holder = int(LOCK.read_text().strip())
            except Exception:
                holder = 0
            if holder and _pid_alive(holder):
                print(f"[single_run] 已有实例运行中 (pid={holder}), 本次退出", flush=True)
                return False
            # 残留锁 (持有者已死), 清理后重试
            try:
                LOCK.unlink()
            except Exception:
                pass


def release():
    try:
        LOCK.unlink()
    except Exception:
        pass
    print("[single_run] 锁已释放", flush=True)


def main():
    if len(sys.argv) < 2:
        print("用法: single_run.py <命令...>")
        return 2
    if not acquire():
        return 0
    try:
        return subprocess.call(sys.argv[1:])
    finally:
        release()


if __name__ == "__main__":
    sys.exit(main())
