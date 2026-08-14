# -*- coding: utf-8 -*-
"""
验证码求解器单元测试 (纯逻辑, 无设备依赖)
"""

import base64

from utils.captcha_solver import ArithmeticCaptchaSolver, decode_base64_png

# 1x1 透明 PNG 的 base64
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class TestDecodeBase64Png:
    def test_decode_plain_base64(self):
        assert decode_base64_png(base64.b64encode(PNG_BYTES).decode()) == PNG_BYTES

    def test_decode_data_uri_prefix(self):
        uri = "data:image/png;base64," + base64.b64encode(PNG_BYTES).decode()
        assert decode_base64_png(uri) == PNG_BYTES

    def test_decode_non_png_rejected(self):
        assert decode_base64_png(base64.b64encode(b"hello").decode()) is None

    def test_decode_empty_rejected(self):
        assert decode_base64_png("") is None
        assert decode_base64_png(None) is None


class TestParseExpression:
    def setup_method(self):
        self.solver = ArithmeticCaptchaSolver(recognizer=lambda b: "")

    def test_add(self):
        assert self.solver.parse_expression("3+5=?") == "8"

    def test_sub(self):
        assert self.solver.parse_expression("12-7=?") == "5"

    def test_multiply_chinese_sign(self):
        assert self.solver.parse_expression("3×4=?") == "12"

    def test_divide(self):
        assert self.solver.parse_expression("8÷2=?") == "4"

    def test_multi_digit(self):
        assert self.solver.parse_expression("23+45=?") == "68"

    def test_no_equals_sign(self):
        assert self.solver.parse_expression("3+5") == "8"

    def test_negative_result_rejected(self):
        assert self.solver.parse_expression("3-7=?") is None

    def test_garbage_rejected(self):
        assert self.solver.parse_expression("abc") is None

    def test_empty_rejected(self):
        assert self.solver.parse_expression("") is None

    def test_division_by_zero_rejected(self):
        assert self.solver.parse_expression("8÷0=?") is None


class TestSolve:
    def test_solve_with_fake_recognizer(self):
        solver = ArithmeticCaptchaSolver(recognizer=lambda b: "4×6=?")
        assert solver.solve(b"fake-bytes") == "24"

    def test_solve_recognizer_failure_returns_none(self):
        solver = ArithmeticCaptchaSolver(recognizer=lambda b: "garbage")
        assert solver.solve(b"fake-bytes") is None
