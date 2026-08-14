# 登录算术验证码支持 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让登录模块自动求解新 APK (com.keda.atc v1.0.2-sit) 的图片型算术验证码并跑通 test_login 全部用例。

**Architecture:** 新建纯逻辑组件 `ArithmeticCaptchaSolver`（取图→OCR→白名单算式解析→安全求值），LoginPage 集成求解器并在 `login()` 中实现"识别→输入→校验→验证码错误刷新重试"闭环；识别引擎 ddddocr 可注入以便单测。

**Tech Stack:** Python 3.13 (venv), Appium-Python-Client, ddddocr (OCR), pytest

**规格:** `docs/superpowers/specs/2026-08-14-login-arithmetic-captcha-design.md`

## Global Constraints

- Python 版本: venv 为 3.13.13，所有命令用 `.venv/Scripts/python.exe`
- 工作目录: 所有命令在 `D:\liyang\code\Android_Auto_Test\mobile-test-framework` 下执行（简称 `$FW`）
- 依赖约束: `ddddocr>=1.5.6`（py3.13 需 onnxruntime>=1.20，由 pip 自动解析；如 import 失败则 `pip install -U onnxruntime`）
- 代码风格: 与现有代码一致——中文 docstring、`logger = logging.getLogger(__name__)`、`# ==== 分节注释 ====`
- 验证码重试上限: `MAX_CAPTCHA_RETRIES = 3`（模块内常量，不进 config.yaml）
- 不修改 config.yaml 结构、不动其它页面对象（HomePage 等校准属于下一步范围）
- 提交信息前缀: `feat:` / `test:` / `chore:`，结尾附 `Co-Authored-By: Claude <noreply@anthropic.com>`
- 真机验证前置: Appium 服务已运行于 127.0.0.1:4723，设备 NOH-AN01 已连接（框架自动按型号匹配 devices[1]）

---

### Task 1: 验证码求解器 `ArithmeticCaptchaSolver`（TDD）

**Files:**
- Create: `utils/captcha_solver.py`
- Create: `tests/test_captcha_solver.py`
- Modify: `requirements.txt`

**Interfaces:**
- Consumes: 无
- Produces:
  - `ArithmeticCaptchaSolver(recognizer=None)` — recognizer 为可调用对象 `(bytes) -> str`，默认延迟导入 ddddocr
  - `ArithmeticCaptchaSolver.solve(image_bytes: bytes) -> Optional[str]` — 答案字符串，失败返回 None
  - `ArithmeticCaptchaSolver.parse_expression(raw: str) -> Optional[str]` — 纯函数：OCR 原始串 → 答案
  - 模块函数 `decode_base64_png(text: str) -> Optional[bytes]` — 解码元素 text 属性中的 base64 PNG（兼容 data URI 前缀；非 PNG 数据返回 None）

- [ ] **Step 1: 安装 ddddocr 并更新 requirements.txt**

```bash
cd $FW && .venv/Scripts/python.exe -m pip install "ddddocr>=1.5.6"
```

requirements.txt 在 "工具库" 分节（`Pillow>=10.0.0` 行之前）插入：

```
ddddocr>=1.5.6              # 算术验证码OCR识别
```

- [ ] **Step 2: 验证 ddddocr 可导入（py3.13/onnxruntime 兼容性检查）**

```bash
cd $FW && .venv/Scripts/python.exe -c "import ddddocr; ddddocr.DdddOcr(show_ad=False); print('OCR OK')"
```

Expected: 输出 `OCR OK`。若报 onnxruntime 相关 ImportError/AttributeError：`pip install -U onnxruntime` 后重试。

- [ ] **Step 3: 写失败的单测 `tests/test_captcha_solver.py`**

```python
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
```

- [ ] **Step 4: 运行测试确认失败**

```bash
cd $FW && .venv/Scripts/python.exe -m pytest tests/test_captcha_solver.py -v
```

Expected: 全部 FAIL（`ModuleNotFoundError: No module named 'utils.captcha_solver'`）

- [ ] **Step 5: 实现 `utils/captcha_solver.py`**

```python
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
```

- [ ] **Step 6: 运行测试确认通过**

```bash
cd $FW && .venv/Scripts/python.exe -m pytest tests/test_captcha_solver.py -v
```

Expected: 16 passed

- [ ] **Step 7: Commit**

```bash
git add utils/captcha_solver.py tests/test_captcha_solver.py requirements.txt
git commit -m "feat: add arithmetic captcha solver with ddddocr

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: LoginPage 改造（定位器重写 + 验证码集成）

**Files:**
- Modify: `pages/login_page.py`

**Interfaces:**
- Consumes: `ArithmeticCaptchaSolver` / `decode_base64_png`（Task 1）
- Produces（Task 3/4 依赖）:
  - `LoginPage.MAX_CAPTCHA_RETRIES = 3`（类常量）
  - `LoginPage.login(username: str, password: str, captcha_override: Optional[str] = None) -> HomePage` — 自动求解验证码；`captcha_override` 非 None 时**单发不重试**（供负例测试）
  - `LoginPage.solve_captcha() -> str` — 公开方法，返回当前验证码正确答案
  - `LoginPage.get_captcha_image_base64() -> str` — 供刷新前后对比
  - `LoginPage.refresh_captcha() -> self` — tap 图片中心刷新
  - `LoginPage._find_captcha_image()` — 过滤出验证码 Image 元素
  - `LoginPage._get_captcha_image_bytes(image_element) -> bytes`
  - `LoginPage._get_login_error() -> Optional[str]` — 登录后校验：None=成功离开登录页
  - 原有 `enter_username/enter_password/enter_captcha/click_login/wait_for_login_page` 签名不变

- [ ] **Step 1: 更新 imports（`pages/login_page.py` 顶部）**

将原 imports 区（`import logging` 之后）改为：

```python
import base64
import logging
from typing import Optional

from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage
from utils.captcha_solver import ArithmeticCaptchaSolver, decode_base64_png
```

（原文件已有 `WebDriverWait`/`EC` 导入，保留；新增 `base64`、`TimeoutException`、求解器导入。）

- [ ] **Step 2: 重写定位器区（原 39-71 行）**

删除 `ALT_USERNAME_INPUT` / `ALT_PASSWORD_INPUT` / `ALT_CAPTCHA_INPUT` / `ALT_LOGIN_BUTTON`，将表单定位器区替换为：

```python
    # --- 登录表单 ---
    # 新APK (com.keda.atc) 输入框无 resource-id, 按出现顺序定位 (真机实测可用)
    USERNAME_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(0)')
    PASSWORD_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(1)')
    CAPTCHA_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText").instance(2)')
    # 验证码图片: Image 元素中 text 属性携带 base64 数据者 (由 _find_captcha_image 过滤)
    CAPTCHA_IMAGE = (AppiumBy.CLASS_NAME, "android.widget.Image")

    LOGIN_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("登录")')
    FORGOT_PASSWORD_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("忘记密码")')
```

（`WECHAT_LOGIN_BUTTON`、找回密码区、`BACK_BUTTON`/`ERROR_MESSAGE`/`TOAST_TEXT`/`PAGE_TITLE` 保持不变。）

- [ ] **Step 3: 简化 `enter_username` / `enter_password` / `enter_captcha`（删除 2 秒死路探测）**

三个方法体分别替换为：

```python
    def enter_username(self, username: str):
        """输入账号"""
        logger.info(f"输入账号: {username}")
        self.input_text(self.USERNAME_INPUT, username)
        return self
```

```python
    def enter_password(self, password: str):
        """输入密码"""
        logger.info(f"输入密码: {'*' * len(password)}")
        self.input_text(self.PASSWORD_INPUT, password)
        return self
```

```python
    def enter_captcha(self, captcha: str):
        """输入验证码答案"""
        logger.info(f"输入验证码: {captcha}")
        self.input_text(self.CAPTCHA_INPUT, captcha)
        return self
```

- [ ] **Step 4: 简化 `click_login`（删除 ALT 探测）**

方法体替换为：

```python
    def click_login(self):
        """
        点击登录按钮

        Returns:
            HomePage: 登录成功后跳转到首页
        """
        logger.info("点击登录按钮")
        self.click(self.LOGIN_BUTTON)
        from pages.home_page import HomePage
        return HomePage(self.driver)
```

- [ ] **Step 5: 重写 `login()` 为自动验证码版本**

替换原 `login` 方法为：

```python
    MAX_CAPTCHA_RETRIES = 3

    def login(
        self,
        username: str,
        password: str,
        captcha_override: Optional[str] = None,
    ):
        """
        完整登录流程 (自动求解算术验证码)

        Args:
            username: 账号
            password: 密码
            captcha_override: 指定验证码答案 (供负例测试)。
                              非 None 时单发不重试: 失败直接抛出。

        Returns:
            HomePage: 登录成功后的首页对象

        Raises:
            TimeoutException: 登录失败 (账号/密码错误, 或验证码重试耗尽)
        """
        logger.info(f"执行登录操作: username={username}")
        self.enter_username(username).enter_password(password)

        if captcha_override is not None:
            self.enter_captcha(captcha_override)
            self.click_login()
            error = self._get_login_error()
            if error is None:
                from pages.home_page import HomePage
                return HomePage(self.driver)
            raise TimeoutException(f"登录失败: {error}")

        for attempt in range(1, self.MAX_CAPTCHA_RETRIES + 1):
            answer = self.solve_captcha()
            self.enter_captcha(answer)
            self.click_login()
            error = self._get_login_error()
            if error is None:
                from pages.home_page import HomePage
                return HomePage(self.driver)
            if "验证码" not in error:
                # 账号/密码类业务错误, 不重试
                self.take_screenshot("login_failed")
                raise TimeoutException(f"登录失败: {error}")
            logger.warning(
                f"验证码错误, 刷新重试 ({attempt}/{self.MAX_CAPTCHA_RETRIES}): {error}"
            )
            self.refresh_captcha()

        self.take_screenshot("login_failed")
        raise TimeoutException(
            f"登录失败: 验证码识别/校验重试{self.MAX_CAPTCHA_RETRIES}次仍未成功"
        )
```

- [ ] **Step 6: 新增验证码相关方法（放在 `refresh_captcha` 原位置）**

替换原 `refresh_captcha` 方法为以下一组方法：

```python
    def solve_captcha(self) -> str:
        """
        求解当前验证码 (识别失败自动刷新重试, 最多 MAX_CAPTCHA_RETRIES 次)

        Returns:
            str: 算术验证码答案 (如 "8")

        Raises:
            TimeoutException: 连续重试后仍无法求解
        """
        solver = ArithmeticCaptchaSolver()
        image = self._find_captcha_image()
        for attempt in range(1, self.MAX_CAPTCHA_RETRIES + 1):
            try:
                answer = solver.solve(self._get_captcha_image_bytes(image))
            except Exception as e:
                logger.warning(f"验证码求解异常: {e}")
                answer = None
            if answer:
                logger.info(f"验证码答案: {answer} (第{attempt}次)")
                return answer
            if attempt < self.MAX_CAPTCHA_RETRIES:
                logger.warning(f"验证码识别失败(第{attempt}次), 刷新重试")
                self.refresh_captcha()
                image = self._find_captcha_image()
        raise TimeoutException(f"验证码识别失败: 连续{self.MAX_CAPTCHA_RETRIES}次无法求解")

    def refresh_captcha(self):
        """刷新验证码 (图片 clickable=false, 改用坐标点击图片中心)"""
        logger.info("刷新验证码")
        image = self._find_captcha_image()
        self.tap_coordinates(*self._element_center(image))
        self.wait_seconds(1.0)
        return self

    def get_captcha_image_base64(self) -> str:
        """获取当前验证码图片内容 (base64), 供刷新前后对比"""
        image = self._find_captcha_image()
        text = image.get_attribute("text") or ""
        if len(text) > 50:
            return text
        return image.screenshot_as_base64

    def _find_captcha_image(self):
        """
        定位验证码 Image 元素

        策略: 1) text 属性携带 base64 数据 (len>50) 的 Image
              2) 兜底: 验证码行位置 (x>=700 且 y>=1150) 的 Image

        Raises:
            TimeoutException: 未找到
        """
        images = self.find_elements(self.CAPTCHA_IMAGE, timeout=10)
        for img in images:
            try:
                if len(img.get_attribute("text") or "") > 50:
                    return img
            except Exception:
                continue
        for img in images:
            loc = img.location or {}
            if loc.get("x", 0) >= 700 and loc.get("y", 0) >= 1150:
                return img
        raise TimeoutException("未找到验证码图片元素")

    def _get_captcha_image_bytes(self, image_element) -> bytes:
        """
        提取验证码图片字节: 优先 text 属性 base64, 回退元素截图

        Args:
            image_element: _find_captcha_image() 返回的元素

        Returns:
            bytes: PNG 图片字节
        """
        text = image_element.get_attribute("text") or ""
        data = decode_base64_png(text)
        if data:
            return data
        return base64.b64decode(image_element.screenshot_as_base64)

    def _get_login_error(self) -> Optional[str]:
        """
        登录点击后的结果校验

        Returns:
            str|None: 错误信息 (仍停留在登录页)；None 表示已离开登录页 (成功)
        """
        self.wait_seconds(2.0)  # 等待登录请求返回 (get_error_message 内部另有等待, 容忍慢跳转)
        if not self.is_on_login_page():
            return None
        return self.get_error_message(timeout=5)

    @staticmethod
    def _element_center(element):
        """元素中心坐标 (tap 用)"""
        loc = element.location
        size = element.size
        return loc["x"] + size["width"] // 2, loc["y"] + size["height"] // 2
```

- [ ] **Step 7: 简化 `is_login_button_enabled`（删除 ALT 探测）**

```python
    def is_login_button_enabled(self) -> bool:
        """判断登录按钮是否可点击"""
        return self.is_element_enabled(self.LOGIN_BUTTON, timeout=3)
```

- [ ] **Step 8: 真机验证求解闭环（临时探针，验证后删除）**

创建临时脚本 `probe_captcha.py`（$FW 根目录，与 login_page.py 同层调用方式一致）：

```python
# -*- coding: utf-8 -*-
"""临时探针: 真机验证 solve_captcha 闭环 (验证后删除)"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from drivers.appium_driver import AppiumDriverManager
from pages.login_page import LoginPage

m = AppiumDriverManager()
d = m.get_driver()
time.sleep(6)

page = LoginPage(d)
page.wait_for_login_page()
for i in range(3):
    answer = page.solve_captcha()
    print(f"第{i + 1}次求解答案: {answer}")
    page.refresh_captcha()

d.save_screenshot(str(Path("reports/screenshots/probe_captcha.png")))
print("截图: reports/screenshots/probe_captcha.png")
m.quit_driver()
```

运行：

```bash
cd $FW && .venv/Scripts/python.exe probe_captcha.py
```

Expected: 输出 3 次求解答案，无异常；人工打开 `reports/screenshots/probe_captcha.png` 核对最后一次刷新的算式与打印的第一次答案规律吻合（前两次答案对应刷新前的算式，可肉眼比对前后截图/算式变化）。若连续失败：检查日志中 `验证码求解` 相关 DEBUG 输出定位是取图还是 OCR 环节。

验证后删除：`rm probe_captcha.py`（git 未跟踪，直接删除）

- [ ] **Step 9: 语法自检 + Commit**

```bash
cd $FW && .venv/Scripts/python.exe -m py_compile pages/login_page.py && echo OK
```

Expected: `OK`

```bash
git add pages/login_page.py
git commit -m "feat: integrate arithmetic captcha solving into LoginPage

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: 登录测试用例更新

**Files:**
- Modify: `tests/test_login.py`
- Modify: `data/login_data.yaml`

**Interfaces:**
- Consumes: Task 2 的 `login(captcha_override=)` / `solve_captcha()` / `get_captcha_image_base64()` / `refresh_captcha()` / `MAX_CAPTCHA_RETRIES`
- Produces: 无新接口（Task 4 直接运行这些用例）

- [ ] **Step 1: test_login.py 增加 imports**

在文件头部 `import logging` 之后追加：

```python
from selenium.common.exceptions import TimeoutException
```

- [ ] **Step 2: 重写 `test_login_success`**

替换原函数体为：

```python
def test_login_success(driver, config):
    """
    测试场景: 使用有效的账号密码登录 (自动求解算术验证码)

    预期结果:
        - 登录成功后离开登录页 (首页特征断言在真机校准后补充)
    """
    account = config.get_test_account("default")
    login_page = LoginPage(driver)

    with allure.step("1. 等待登录页面加载"):
        login_page.wait_for_login_page()

    with allure.step("2. 自动识别验证码并登录"):
        login_page.login(account["username"], account["password"])

    with allure.step("3. 验证已离开登录页"):
        assert not login_page.is_on_login_page(), (
            f"登录失败: 仍停留在登录页\n当前页面: {driver.current_activity}"
        )
        logger.info("✅ 登录成功，已离开登录页")
```

同时删除文件顶部 `from pages.home_page import HomePage` 导入行——重写后全文件不再使用 HomePage。

- [ ] **Step 3: 更新 `test_login_failure` 参数化数据（testuser → liyang）**

将 parametrize 列表替换为：

```python
@pytest.mark.parametrize("username,password,expected_error", [
    pytest.param(
        "liyang",
        "wrong_password_123",
        "密码错误",
        id="错误密码"
    ),
    pytest.param(
        "",
        "Liyang@1128",
        "请输入账号",
        id="空账号"
    ),
    pytest.param(
        "liyang",
        "",
        "请输入密码",
        id="空密码"
    ),
    pytest.param(
        "",
        "",
        "请输入",
        id="账号密码均为空"
    ),
])
```

函数体不变。（期望文案若与真实 APP 不一致，在 Task 4 按实测校准。）

- [ ] **Step 4: 重写 `test_login_wrong_captcha`**

替换原函数体为：

```python
def test_login_wrong_captcha(driver, config):
    """
    测试场景: 输入错误的算术验证码答案

    预期:
        - 抛出包含"验证码"的登录失败
        - 停留在登录页
    """
    account = config.get_test_account("default")
    login_page = LoginPage(driver)

    with allure.step("1. 求解正确答案并构造错误答案"):
        login_page.wait_for_login_page()
        login_page.enter_username(account["username"])
        login_page.enter_password(account["password"])
        correct = login_page.solve_captcha()
        wrong = str(int(correct) + 1)
        logger.info(f"正确答案: {correct}, 故意输入错误答案: {wrong}")

    with allure.step("2. 用错误答案登录 (单发不重试)"):
        with pytest.raises(TimeoutException, match="验证码"):
            login_page.login(
                account["username"],
                account["password"],
                captcha_override=wrong,
            )

    with allure.step("3. 验证停留在登录页"):
        assert login_page.is_on_login_page(), "错误验证码后不应进入首页"
        logger.info("✅ 验证码错误提示正常")
```

- [ ] **Step 5: 重写 `test_refresh_captcha`**

替换原函数体为：

```python
def test_refresh_captcha(driver):
    """
    测试场景: 点击验证码图片刷新

    预期:
        - 刷新前后验证码图片内容变化
    """
    login_page = LoginPage(driver)
    login_page.wait_for_login_page()

    with allure.step("1. 记录当前验证码图片内容"):
        before = login_page.get_captcha_image_base64()
        assert before, "验证码图片内容不应为空"

    with allure.step("2. 点击验证码图片刷新"):
        login_page.refresh_captcha()

    with allure.step("3. 验证图片已变化"):
        after = login_page.get_captcha_image_base64()
        assert after, "刷新后验证码图片内容不应为空"
        assert before != after, "刷新后验证码图片应发生变化"
        logger.info("✅ 验证码刷新成功")
```

- [ ] **Step 6: 同步 `data/login_data.yaml`**

`login_failure_cases` 中 `username: "testuser"` → `"liyang"`，`password: "testpass123"` → `"Liyang@1128"`（共 4 处）。`captcha_cases` 中：

```yaml
  - captcha: "AAAA"
    expected_error: "验证码错误"
    description: "错误验证码"
```

改为：

```yaml
  - captcha: "0"
    expected_error: "验证码错误"
    description: "错误验证码(算术答案错误)"
```

- [ ] **Step 7: 静态校验 + Commit**

```bash
cd $FW && .venv/Scripts/python.exe -m pytest tests/test_captcha_solver.py -v
cd $FW && .venv/Scripts/python.exe -m pytest tests/test_login.py --collect-only -q
```

Expected: 单测 16 passed；collect 8 items（test_login_success / 4×test_login_failure / test_login_wrong_captcha / test_refresh_captcha / test_forgot_password_flow / test_wechat_login_entry）

```bash
git add tests/test_login.py data/login_data.yaml
git commit -m "test: update login tests for arithmetic captcha and new account

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: 真机校准与全量验证

**Files:**
- Modify: `tests/test_login.py`（按实测校准断言）
- 视需要 Modify: `pages/login_page.py`（仅当实测暴露缺陷）

**Interfaces:**
- Consumes: Task 2/3 全部产物
- Produces: 全绿的登录模块用例

- [ ] **Step 1: 全量运行登录用例**

```bash
cd $FW && .venv/Scripts/python.exe -m pytest tests/test_login.py -m "login and not slow" -v --reruns 1 --reruns-delay 2 --alluredir=reports/allure-results --device-index 0
```

Expected 基线: 7 个用例（1 成功 + 4 失败参数 + 错误验证码 + 刷新），通过或失败待实测校准。

- [ ] **Step 2: 校准错误提示文案**

若 `test_login_failure` 断言失败：查看 `logs/pytest.log` 中 `获取到错误信息` 行的实际值，将 `expected_error` 更新为实际文案的关键子串（如 "密码错误" 实为 "账号或密码错误" 则改为 "密码错误" 仍匹配，仅当完全不匹配才改）。若空输入场景 APP 直接禁用登录按钮（走 `is_login_button_enabled` 分支）则无需改。

- [ ] **Step 3: 校准登录成功断言（抓取真实首页特征）**

`test_login_success` 已在 Step 2 跑通并保持登录态（`no_reset: true`）。重新创建 session 直接抓取登录后首页：

```bash
cd $FW && .venv/Scripts/python.exe -c "
import sys, time
sys.path.insert(0, '.')
from drivers.appium_driver import AppiumDriverManager
m = AppiumDriverManager()
d = m.get_driver()
time.sleep(8)
open('reports/home_probe.xml', 'w', encoding='utf-8').write(d.page_source)
d.save_screenshot('reports/screenshots/home_probe.png')
m.quit_driver()
print('done')
"
```

若未保持登录态（仍显示登录页），先运行一次 `test_login_success` 再抓取。

从 `reports/home_probe.xml` 与截图提取一个稳定特征文本（如底部 tab "申报"/"我的"，或页面标题），将 `test_login_success` 第 3 步断言替换为：

```python
    with allure.step("3. 验证进入首页"):
        login_page = LoginPage(driver)
        assert not login_page.is_on_login_page(), (
            f"登录失败: 仍停留在登录页\n当前页面: {driver.current_activity}"
        )
        home_marker = (AppiumBy.ANDROID_UIAUTOMATOR,
                       'new UiSelector().text("<<实测特征文本>>")')
        assert login_page.is_element_present(home_marker, timeout=10), \
            "已离开登录页但未发现首页特征元素"
        logger.info("✅ 登录成功，已进入首页")
```

（`<<实测特征文本>>` 必须替换为 Step 3 抓取到的真实文本；test_login.py 顶部需 import `AppiumBy`。）

- [ ] **Step 4: 重复运行至全绿**

重复 Step 1 命令，直至 7 passed（`test_forgot_password_flow` 为 slow 标记不在本次范围；`test_wechat_login_entry` 视 APP 实际自行跳过）。

- [ ] **Step 5: 失败现场留档检查**

若有失败：`ls reports/screenshots/ | grep FAILED` 确认失败截图已生成，`logs/pytest.log` 中应有 `验证码求解` 日志链。修复后回到 Step 4。

- [ ] **Step 6: Commit 校准结果**

```bash
git add tests/test_login.py pages/login_page.py
git commit -m "test: calibrate login assertions against real app UI

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: 清理

**Files:**
- Delete: `probe_login.py`

**Interfaces:** 无

- [ ] **Step 1: 删除临时探针脚本**

```bash
cd $FW && rm -f probe_login.py && ls probe_login.py 2>&1 | head -1
```

Expected: `No such file or directory`（probe_captcha.py 已在 Task 2 Step 8 删除；reports/ 下探针产物 `login_probe_source.xml` 等为 git 忽略的测试产物，保留无妨）

- [ ] **Step 2: 最终回归**

```bash
cd $FW && .venv/Scripts/python.exe -m pytest tests/test_captcha_solver.py tests/test_login.py -m "login and not slow or not login" -v --reruns 1 --reruns-delay 2 --device-index 0
```

Expected: 单测 16 passed + 登录用例 7 passed（与 Task 4 一致）

- [ ] **Step 3: Commit**

```bash
git add -u probe_login.py
git commit -m "chore: remove temporary login probe script

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 验收标准（对应规格 §7）

1. `tests/test_captcha_solver.py` 16 个单测全绿（Task 1）
2. `pytest tests/test_login.py -m "login and not slow"` 7 个用例全绿（Task 4）
3. 登录成功断言基于真机首页实测特征（Task 4 Step 3）
4. 失败时 Allure 附失败截图（conftest hook 自动，Task 4 Step 5 确认）
