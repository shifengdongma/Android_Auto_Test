#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地原型页面服务器

功能:
    在 PC 上启动 HTTP 服务器，将 pages/ 目录下的 HTML 原型提供给手机 Chrome 访问。
    自动执行 adb reverse 端口转发，手机可直接通过 http://127.0.0.1:8080/ 访问。

使用方式:
    # 方式1: 直接运行
    python serve_pages.py

    # 方式2: 指定端口
    python serve_pages.py --port 9090

    # 方式3: 指定页码目录
    python serve_pages.py --dir ../pages

工作流程:
    PC (port 8080)  ←→  adb reverse  ←→  Phone (127.0.0.1:8080)
                                               │
                                        Chrome 浏览器打开
                                        127.0.0.1:8080/小程序_首页.html
"""

import sys
import os
import socket
import subprocess
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

PROJECT_ROOT = Path(__file__).parent


def get_local_ip():
    """获取本机局域网IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_adb_reverse(port):
    """执行 adb reverse 端口转发，手机可通过 127.0.0.1 访问 PC 端口"""
    try:
        # 先清除旧的反向代理
        subprocess.run(
            ["adb", "reverse", "--remove", f"tcp:{port}"],
            capture_output=True,
            timeout=5,
        )
        # 建立新的反向代理
        result = subprocess.run(
            ["adb", "reverse", f"tcp:{port}", f"tcp:{port}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print(f"[OK] adb reverse tcp:{port} -> tcp:{port} 已建立")
            return True
        else:
            print(f"[WARN] adb reverse 失败 (code={result.returncode})")
            if result.stderr:
                print(f"  stderr: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("[WARN] 未找到 adb 命令，跳过端口转发")
        print("  手机需通过局域网IP访问: http://{}:{}/".format(get_local_ip(), port))
        return False
    except Exception as e:
        print(f"[WARN] adb reverse 异常: {e}")
        return False


class IndexHandler(SimpleHTTPRequestHandler):
    """自定义请求处理器，目录列表显示中文文件名"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT.parent / "pages"), **kwargs)

    def log_message(self, format, *args):
        # 简化日志输出
        print(f"  [{self.client_address[0]}] {args[0]}")

    def end_headers(self):
        # 允许跨域访问
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def list_pages():
    """列出所有可用页面"""
    pages_dir = PROJECT_ROOT.parent / "pages"
    html_files = sorted(pages_dir.glob("*.html"))
    print("\n  Available pages:")
    print(f"  {'─' * 48}")
    for f in html_files:
        name = f.stem.replace("小程序_", "")
        print(f"  📄 {name:20s}  →  http://127.0.0.1:PORT/{f.name}")
    print(f"  {'─' * 48}")
    print(f"  Total: {len(html_files)} pages\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="本地原型页面服务器 — 手机 Chrome 测试辅助"
    )
    parser.add_argument("--port", type=int, default=8080, help="HTTP 服务端口 (默认: 8080)")
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="页码目录 (默认: ../pages)",
    )
    parser.add_argument(
        "--no-adb",
        action="store_true",
        help="跳过 adb reverse (手机手动输入局域网IP)",
    )
    args = parser.parse_args()

    port = args.port
    local_ip = get_local_ip()

    print()
    print("=" * 55)
    print("   Low-Altitude Airspace Management — Page Server")
    print("=" * 55)
    print(f"   PC IP:   {local_ip}")
    print(f"   Port:    {port}")
    print(f"   Root:    {PROJECT_ROOT.parent / 'pages'}")
    print("=" * 55)

    # ADB 端口转发
    if not args.no_adb:
        run_adb_reverse(port)

    # 列出可用页面
    list_pages()

    # 启动服务器
    print(f"  HTTP server starting on http://0.0.0.0:{port}/")
    print(f"  Press Ctrl+C to stop\n")
    print(f"  On your phone Chrome, open:")
    print(f"  → http://127.0.0.1:{port}/小程序_首页.html")
    if not args.no_adb:
        print(f"  (or http://{local_ip}:{port}/  if adb reverse fails)")
    print()

    httpd = HTTPServer(("0.0.0.0", port), IndexHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[OK] Server stopped.")
        # 清理 adb reverse
        if not args.no_adb:
            subprocess.run(
                ["adb", "reverse", "--remove", f"tcp:{port}"],
                capture_output=True,
            )
            print(f"[OK] adb reverse tcp:{port} removed.")


if __name__ == "__main__":
    main()
