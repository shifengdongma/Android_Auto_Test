# -*- coding: utf-8 -*-
"""
算术验证码求解器 (ArithmeticCaptchaSolver)

功能:
    - 从验证码图片字节中识别算术表达式并计算答案
    - 识别引擎可注入 (默认 ddddocr)，便于单元测试

流程: 图片字节 -> OCR字符序列 -> 白名单算式解析 -> 安全求值 -> 答案

使用示例:
    from utils.captcha_solver import ArithmeticCaptchaSolver

    solver = ArithmeticCaptchaSolver()
    answer = solver.solve(image_bytes)  # "3+5=?" -> "8"
"""

import base64
import binascii
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class ArithmeticCaptchaSolver:
    """
    算术验证码求解器

    职责:
        1. OCR识别验证码图片中的字符序列
        2. 解析为算术表达式 (仅允许 数字 + - × ÷ = ?)
        3. 安全求值并返回非负整数答案
    """

    # 白名单: 数字与算术符号 (含OCR常见误读形态 ×/x/X/÷)
    _EXPR_CHARS = re.compile(r"[^0-9+\-*×xX÷/=?]")

    def __init__(self, recognizer=None):
        """
        Args:
            recognizer: 可调用对象 (bytes) -> str，OCR字符序列。
                        默认使用 ddddocr (延迟导入, 无OCR环境仍可单测纯逻辑)。
        """
        self._recognizer = recognizer

    def solve(self, image_bytes: bytes) -> Optional[str]:
        """
        识别并求解验证码图片

        Args:
            image_bytes: 验证码图片字节 (PNG/JPEG)

        Returns:
            str|None: 答案字符串 (如 "8")；识别/解析失败返回 None
        """
        raw = self.recognize(image_bytes)
        if not raw:
            return None
        return self.parse_expression(raw)

    def recognize(self, image_bytes: bytes) -> str:
        """OCR识别图片 -> 字符序列"""
        if self._recognizer is not None:
            return self._recognizer(image_bytes)
        import ddddocr  # 延迟导入
        return ddddocr.DdddOcr(show_ad=False).classification(image_bytes)

    def parse_expression(self, raw: str) -> Optional[str]:
        """
        从OCR原始串解析算式并求值

        Args:
            raw: OCR输出, 如 "3+5=?" / "3十5二?" / "12-7=?"

        Returns:
            str|None: 非负整数答案；无法解析返回 None
        """
        cleaned = self._EXPR_CHARS.sub("", raw)
        # 去掉等号及之后的内容, 仅保留算式部分
        expr = cleaned.split("=")[0].rstrip("?")
        if not expr:
            logger.warning(f"验证码识别结果无算式: {raw!r} -> {cleaned!r}")
            return None

        # 归一化乘除符号
        expr = expr.replace("×", "*").replace("x", "*").replace("X", "*").replace("÷", "/")

        # 校验: 仅剩数字与 +-*/ 且至少含一个运算符
        if not re.fullmatch(r"[\d+\-*/]+", expr) or not re.search(r"[+\-*/]", expr):
            logger.warning(f"验证码算式非法: {raw!r} -> {expr!r}")
            return None

        try:
            # 白名单字符过滤后求值, 禁用内建
            result = eval(expr, {"__builtins__": {}}, {})
        except (SyntaxError, ZeroDivisionError, TypeError) as e:
            logger.warning(f"算式求值失败: {expr!r} ({e})")
            return None

        if isinstance(result, float) and result.is_integer():
            result = int(result)
        if not isinstance(result, int) or result < 0:
            logger.warning(f"验证码结果非法(非非负整数): {expr!r} = {result!r}")
            return None

        logger.info(f"验证码求解: {raw!r} -> {expr!r} = {result}")
        return str(result)


def decode_base64_png(text: str) -> Optional[bytes]:
    """
    解码图片元素 text 属性中的 base64 PNG 数据

    uni-app 将 data URI 泄漏到 Image 元素 text 属性 (已实测)。
    兼容带/不带 "data:image/png;base64," 前缀；非 PNG 数据返回 None。

    Returns:
        bytes|None: PNG字节
    """
    if not text:
        return None
    if text.startswith("data:image"):
        try:
            text = text.split(",", 1)[1]
        except IndexError:
            return None
    try:
        data = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        return None
    if not data.startswith(b"\x89PNG"):
        return None
    return data
