# 登录算术验证码支持 — 设计文档

日期: 2026-08-14
状态: 已批准 (方案A)

---

## 1. 背景与问题

新 APK `atc-app-v1.0.2-sit.apk` (包名 `com.keda.atc`, uni-app 应用, 启动入口 `io.dcloud.PandoraEntry`) 的登录页新增了**图片型算术验证码**：

- 验证码为图片渲染（`android.widget.Image`），算式文本在 UI 层不可读
- 现有 `LoginPage.login()` 流程完全没有验证码步骤 → 点击登录后停留在登录页 → 等"首页"超时，表象为 `NoSuchElementError`
- 旧 `com.dolphin.atc:id/et_*` 定位器全部失效（包名已变，且新 UI 输入框无 resource-id）
- 本机无任何 OCR 环境

## 2. 探索证据（真机 Appium 抓取）

| 项 | 证据 |
|---|---|
| 输入框 | 3 个原生 EditText：账号 instance(0)、密码 instance(1, password=true)、验证码 instance(2)，`UiSelector().className("android.widget.EditText").instance(N)` 可稳定定位 |
| 验证码图片 | `android.widget.Image`，bounds `[750,1215][1062,1317]`，`clickable=false`，**`text` 属性直接携带 base64 PNG**（uni-app 渲染 data URI 泄漏到属性） |
| 上下文 | 单一 `NATIVE_APP`，text 定位器可用（"登录"、"请输入验证码"等文本节点存在） |
| 版本 | 页面底部显示 `V1.0.2-sit.20260814.1352` |
| 账号 | 已更新: `liyang` / `Liyang@1128`（config.yaml + data/test_accounts.yaml） |

## 3. 方案决策

- **方案A（选定）**: ddddocr 识别 + 元素 `text` 属性直取 base64 PNG（零裁剪误差），属性取不到时回退整页截图 + PIL 按 bounds 裁剪
- 方案B（截图裁剪为主）: 更通用但多一层像素比换算，仅作为 A 的兜底
- 方案C（pytesseract）: 需装 Tesseract 二进制、算式符号识别差，排除

## 4. 组件设计

### 4.1 `utils/captcha_solver.py` — ArithmeticCaptchaSolver

纯逻辑组件（不依赖页面对象，可单测）：

```
solve(image_element, driver) -> Optional[str]
    1. _extract_image(): element.get_attribute("text") 为 base64 PNG → 解码为字节
       失败 → driver 整页截图 + bounds 裁剪 (PIL, 设备像素比换算)
    2. _ocr(image_bytes): ddddocr 识别字符序列
    3. _parse_expression(raw): 白名单正则 [0-9+\-×÷x*] 提取算式;
       归一化 ×/x→*  ÷→/; 安全求值 (拒绝一切白名单外字符)
    4. 校验: 结果为非负整数 → 返回 str; 否则 None (触发刷新重试)
```

- 常量: 最大识别重试次数 3（模块内常量，不进 config，YAGNI）
- 日志: 识别原始串、解析结果、命中步骤均 DEBUG 记录

### 4.2 `pages/login_page.py` 改造

- **定位器重写**:
  - `USERNAME_INPUT` / `PASSWORD_INPUT` / `CAPTCHA_INPUT` = `UiSelector().className("android.widget.EditText").instance(0/1/2)`
  - `CAPTCHA_IMAGE` = className `android.widget.Image` + 代码过滤（`find_elements` 后取 text 为 base64 者）
  - 删除 `ALT_*`（dolphin resource-id）及 `enter_*` 中每次 2 秒的死路探测
  - `LOGIN_BUTTON`(text 登录)、`PAGE_TITLE`、`FORGOT_PASSWORD_LINK` 保留
- **`login(username, password, captcha_override=None)` 升级**（自动求解，`captcha_override` 供负例测试注入错误答案）:
  1. 输入账号、密码
  2. `captcha_override` 为空时: `solve_captcha()`: 取图 → solver 求解；`None` 则刷新重试（≤3 次）
  3. 输入答案（求解结果或 override）→ 点击登录
  4. 仍停留在登录页且错误提示含"验证码" → 刷新验证码重试（≤3 次）
  5. 全部失败 → 抛 TimeoutException（附失败截图）
- **新增 `solve_captcha() -> str`**: 公开方法，返回当前验证码正确答案（供测试构造错误答案与断言）
- **`refresh_captcha()`**: 图片 `clickable=false`，改用 `tap_coordinates` 点图片中心；返回刷新前后 base64 是否变化
- **新增 `get_captcha_image_base64()`**: 供刷新判定与测试断言

### 4.3 数据流

```
login() → 定位 CAPTCHA_IMAGE → ArithmeticCaptchaSolver.solve()
       → (取图: base64 直取 | 截图裁剪) → ddddocr → 算式解析 → 安全求值
       → enter_captcha(答案) → click_login() → 错误提示校验
       → 验证码错误? → refresh_captcha() → 重试 (≤3)
```

### 4.4 错误处理

| 场景 | 处理 |
|---|---|
| 取图失败（属性无 base64 且截图失败） | 刷新重试，3 次后 TimeoutException + 截图 |
| OCR 结果非合法算式 | 视为识别失败，刷新重试 |
| 登录后提示验证码错误 | 刷新验证码重试（不重输账号密码，EditText 内容保留） |
| 账号/密码错误 | 直接透出错误提示，不重试（业务错误非验证码问题） |

## 5. 测试更新

| 用例 | 变更 |
|---|---|
| `test_login_success` | 改走 `login()`（自动验证码）；登录成功判定 = 登录按钮消失 + 出现首页特征元素（实现时抓取真机首页 page source，以实际特征为准校准，替换原型时代的"首页/计划审批"文本定位器） |
| `test_login_failure` (参数化) | 账号 `testuser` → `liyang`（login_data.yaml 同步）；期望错误文案按新 APP 实测校准 |
| `test_login_wrong_captcha` | 流程: `answer = login_page.solve_captcha()` → `login(captcha_override=str(int(answer)+1))`（原 "AAAA" 对数字验证码无意义）；期望提示按实测校准 |
| `test_refresh_captcha` | 断言刷新前后验证码图片 base64 变化 |
| `test_forgot_password_flow` | 依赖真实邮箱验证码，无法自动化时标注 skip（现状，不在本次强制范围） |

`conftest.py` 的 `logged_in_driver` fixture 调用 `login()`，自动受益，无需修改。

## 6. 依赖与配置

- `requirements.txt` 增加: `ddddocr`（自带 onnxruntime）、`Pillow`
- 删除临时探针脚本 `probe_login.py`
- config.yaml 无需新增配置段

## 7. 验证标准

1. `pytest tests/test_login.py -v -m "login and not slow"` 全绿
2. 登录成功判定经真机首页抓取校准（见 5）
3. 失败时 Allure 附失败截图与识别过程日志

## 8. 范围外（下一步另行处理）

- 首页/资讯/我的等页面定位器校准（README "APK 工作流" 第 4 步）
- 注册模块激活（README 标记 🔜）
