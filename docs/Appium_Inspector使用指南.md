# Appium Inspector 完整操作指南

> 适用环境：Windows 10/11 + Android 真机  
> 适用场景：**任意 Android APP 或 H5 页面**的元素定位与交互操作  
> Appium 版本：3.6.0 | UiAutomator2 驱动：8.2.2  
> 更新日期：2026-08-05

---

## 一、概述

Appium Inspector 是一个独立的桌面应用，可**可视化**连接手机并查看屏幕截图和元素树，支持：

| 功能 | 说明 |
|------|------|
| 屏幕镜像 | 实时查看手机屏幕截图（手动刷新） |
| 元素树查看 | 查看页面所有元素的层级结构和属性 |
| 元素定位 | 点击元素获取 `resource-id`、`xpath`、`accessibility-id`、`class` 等 |
| 手势操作 | 点击、滑动、长按、输入文本等手势操作 |
| 录制回放 | 录制操作步骤并生成测试代码（基础功能） |

### 适用场景

- ✅ 测试**项目浏览器 H5 页面**（Chrome 打开 `http://127.0.0.1:8080/`）
- ✅ 测试**项目原生 APP**（APK 已安装到手机）
- ✅ 查看手机**系统设置、桌面等任何界面**
- ✅ 查看**第三方 APP** 的元素结构
- ✅ 调试元素定位器（xpath、id 等）

---

## 二、环境总览

| 组件 | 路径/值 | 状态 |
|------|---------|------|
| JDK 21 | `C:\Program Files\Java\jdk-21.0.12` | ✅ |
| Android SDK | `C:\Users\keda\AppData\Local\Android\Sdk` | ✅ |
| ADB | `D:\liyang\code\Android_Auto_Test\platform-tools\adb.exe` | ✅ 37.0.1 |
| Appium Server (CLI) | 通过 npm 全局安装 | ✅ 3.6.0 |
| Appium Server GUI | `C:\Users\keda\AppData\Local\Programs\Appium Server GUI\` | ✅ 可选 |
| Appium Inspector | `D:\Appium-Inspector\Appium Inspector.exe` | ✅ |
| UiAutomator2 驱动 | npm 安装 | ✅ 8.2.2 |
| 测试设备 | 24117RK2CC (Xiaomi Redmi) | ✅ Android 16, 1440×3200 |
| 设备 UDID | `adb devices` 查看 | `24117RK2CC` |
| ChromeDriver | `C:\Users\keda\.appium\chromedriver\150.0.7871.124\` | ✅ 浏览器模式用 |

---

## 三、完整操作流程

### 整体流程图

```
┌─────────────────────────────────────────────────────────────────┐
│  步骤1: 前置检查                                                  │
│  ├─ adb devices          → 确认设备连接                           │
│  └─ appium driver list   → 确认 UiAutomator2 已安装               │
├─────────────────────────────────────────────────────────────────┤
│  步骤2: 启动 Appium Server                                       │
│  └─ appium --relaxed-security --allow-cors                       │
│     → 看到 "listener started on http://0.0.0.0:4723"             │
├─────────────────────────────────────────────────────────────────┤
│  步骤3: 打开 Appium Inspector                                    │
│  └─ D:\Appium-Inspector\Appium Inspector.exe                     │
├─────────────────────────────────────────────────────────────────┤
│  步骤4: 配置连接参数 + Capabilities                               │
│  ├─ Remote Host: 127.0.0.1                                       │
│  ├─ Remote Port: 4723                                            │
│  ├─ Remote Path: /                                               │
│  └─ JSON Capabilities → 见下方各场景配置                           │
├─────────────────────────────────────────────────────────────────┤
│  步骤5: 点击 Start Session                                        │
│  └─ 等待连接 → 手机自动启动目标 APP/Chrome → 显示截图和元素树       │
├─────────────────────────────────────────────────────────────────┤
│  步骤6: 操作与定位元素                                             │
│  └─ 点击/滑动/输入 → 查看属性 → 复制定位器到 Page Object           │
└─────────────────────────────────────────────────────────────────┘
```

---

### 步骤 1：前置检查

在启动 Appium Inspector 之前，必须确保以下条件满足：

#### 1.1 检查设备连接

```powershell
adb devices
```

预期输出：
```
List of devices attached
24117RK2CC    device
```

> 状态必须是 **`device`**（不是 `unauthorized` 或 `offline`）

如果设备未显示：
```powershell
# 重启 ADB 服务
adb kill-server
adb start-server
adb devices
```

#### 1.2 检查 Appium 驱动

```powershell
appium driver list
```

预期输出：
```
✔ Listing available drivers
- uiautomator2 [installed (npm)]
```

#### 1.3 检查 Appium 版本

```powershell
appium --version
# 预期: 3.6.0
```

---

### 步骤 2：启动 Appium Server

> **关键**：`--relaxed-security` 和 `--allow-cors` 两个参数**缺一不可**。

#### 方式 A：命令行启动（推荐）

打开一个**新的 PowerShell 终端**：

```powershell
appium --relaxed-security --allow-cors
```

看到以下输出表示启动成功：
```
[Appium] Welcome to Appium v3.6.0
[Appium] Appium REST http interface listener started on http://0.0.0.0:4723
```

> **保持此终端运行**，不要关闭。

**参数说明：**

| 参数 | 作用 | 不加的后果 |
|------|------|-----------|
| `--relaxed-security` | 允许不安全的 ADB 命令（Android 14+ 必须） | Session 创建失败，权限错误 |
| `--allow-cors` | 允许跨域请求（Inspector 需要） | Inspector 无法连接，或报 CORS 错误 |

#### 方式 B：GUI 启动

双击 `C:\Users\keda\AppData\Local\Programs\Appium Server GUI\Appium Server GUI.exe`：

1. 在 **Advanced** 标签页中，确保勾选：
   - ✅ Relaxed Security
   - ✅ Allow CORS
2. 点击 **Start Server**

---

### 步骤 3：打开 Appium Inspector

双击 `D:\Appium-Inspector\Appium Inspector.exe`

界面布局说明：

```
┌──────────────────────────────────────────────────────────────────┐
│  Appium Inspector                                    [Start Session] │
├────────────────────┬─────────────────────────────────────────────┤
│  Remote Server     │                                             │
│  ────────────────  │                                             │
│  Host: 127.0.0.1   │           📱 手机屏幕截图区域                │
│  Port: 4723        │                                             │
│  Path: /           │           （连接成功后显示）                  │
│                    │                                             │
│  Desired           │                                             │
│  Capabilities      │                                             │
│  ────────────────  │                                             │
│  JSON Rep. tab     │                                             │
│  (粘贴 JSON)       │                                             │
│                    │                                             │
├────────────────────┼─────────────────────────────────────────────┤
│  顶部工具栏:                                                      │
│  [🔍 元素选择] [👆 点击] [👆 滑动] [⌨ 输入] [📷 截图] [🔄 刷新] │
├────────────────────┴─────────────────────────────────────────────┤
│  右侧面板:                                                        │
│  🌳 元素树 (层级结构)                                             │
│  📋 元素属性面板 (Selected Element)                               │
│    - id, class, text, content-desc, xpath, ...                   │
└──────────────────────────────────────────────────────────────────┘
```

---

### 步骤 4：配置连接参数

在 Appium Inspector 的 **Remote Server** 区域填入：

```
Remote Host: 127.0.0.1
Remote Port: 4723
Remote Path: /
```

> ⚠️ **Remote Path 必须是 `/`**，不是 `/wd/hub`！  
> Appium 1.x 使用 `/wd/hub`，Appium 2.x/3.x 使用 `/`。

---

### 步骤 5：编写 Capabilities（按场景选择）

在 **Desired Capabilities** 标签页 → 切换到 **JSON Representation** 选项卡 → 粘贴 JSON。

---

#### 场景 A：浏览器模式 — 测试 H5 页面（项目当前模式）

手机 Chrome 打开指定的 H5 页面，适合测试 Web 页面和本项目 `pages/` 下的 HTML 原型。

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:deviceName": "24117RK2CC",
  "appium:udid": "24117RK2CC",
  "appium:platformVersion": "16",
  "browserName": "Chrome",
  "appium:noReset": true,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 120,
  "appium:skipDeviceInitialization": true,
  "appium:skipServerInstallation": true
}
```

**连接成功后**：
- 手机自动打开 Chrome 浏览器（空白页 `about:blank`）
- 在 Inspector 顶部的地址栏输入目标 URL，例如：
  - 本地原型：`http://127.0.0.1:8080/小程序_首页.html`
  - 远程 H5：`https://dkkgsit-test.testdolphin.com/atc/dashboard`
  - 任意网站：`https://www.baidu.com`
- 按回车 → 点击 **刷新按钮** 🔄 → 即可看到页面截图和元素树

> **前提**：访问本地 `127.0.0.1:8080` 前，需要先在另一个终端执行 `adb reverse tcp:8080 tcp:8080` 并启动页面服务器 `python serve_pages.py`。

---

#### 场景 B：原生 APP 模式 — 测试项目 APK

启动指定的原生 Android APP。APK 必须已安装到手机。

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:deviceName": "24117RK2CC",
  "appium:udid": "24117RK2CC",
  "appium:platformVersion": "16",
  "appium:appPackage": "com.dolphin.atc",
  "appium:appActivity": ".MainActivity",
  "appium:noReset": true,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 120,
  "appium:skipDeviceInitialization": true,
  "appium:skipServerInstallation": true
}
```

**连接成功后**：手机自动启动 `com.dolphin.atc` APP，Inspector 显示 APP 首页截图和元素树。

---

#### 场景 C：查看任意已安装 APP — 通用原生模式

如果你不知道目标 APP 的 `appPackage` 和 `appActivity`，先通过 ADB 查出来，再填入配置。

**第 1 步：查找 APP 的包名**

```powershell
# 列出所有第三方应用包名
adb shell pm list packages -3

# 按关键字过滤（例如找微信）
adb shell pm list packages | findstr wechat
# 输出: package:com.tencent.mm
```

**第 2 步：查找 APP 的启动 Activity**

```powershell
# 方法1: 用 dumpsys 查找 LAUNCHER Activity（推荐）
adb shell dumpsys package com.tencent.mm | findstr "android.intent.action.MAIN" -A 5

# 方法2: 用 cmd 命令（Android 10+）
adb shell cmd package resolve-activity --brief com.tencent.mm
# 输出: com.tencent.mm/.ui.LauncherUI
#       包名=com.tencent.mm, Activity=.ui.LauncherUI

# 方法3: 使用项目内置工具（推荐，在项目目录下）
cd D:\liyang\code\Android_Auto_Test\mobile-test-framework
.venv\Scripts\Activate.ps1
python -i manual_test.py
>>> find_app("wechat")           # 搜索微信
>>> inspect_app("com.tencent.mm")  # 查看详情 → 获取 main_activity
```

**第 3 步：将查到的值填入 Capabilities**

例如，查看微信：
```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:deviceName": "24117RK2CC",
  "appium:udid": "24117RK2CC",
  "appium:platformVersion": "16",
  "appium:appPackage": "com.tencent.mm",
  "appium:appActivity": ".ui.LauncherUI",
  "appium:noReset": true,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 120,
  "appium:skipDeviceInitialization": true,
  "appium:skipServerInstallation": true
}
```

---

#### 场景 D：仅查看手机当前界面（不启动特定 APP）

使用 `appium:app` 为空或不指定 `appPackage`，Appium 不会启动任何 APP，而是直接查看手机当前正在显示的界面。

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:deviceName": "24117RK2CC",
  "appium:udid": "24117RK2CC",
  "appium:platformVersion": "16",
  "appium:noReset": true,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 120,
  "appium:skipDeviceInitialization": true,
  "appium:skipServerInstallation": true
}
```

**使用场景**：
- 查看手机桌面/系统设置的元素
- 查看某个已打开 APP 的当前页面
- 不想让 Appium 重启 APP

> 注意：不指定 `appPackage` 时，Appium 可能仍会启动其自带的设置 APP。如需保留当前页面，先手动打开目标 APP，再用此配置连接。

---

### 步骤 6：启动 Session

1. 确认 **Remote Server** 配置正确
2. 在 **JSON Representation** 中粘贴对应场景的 Capabilities JSON
3. 点击 **Start Session** 按钮

**预期效果**：
- 手机屏幕会自动亮起
- 如果配置了 `appPackage`，目标 APP 会自动启动
- 如果配置了 `browserName: "Chrome"`，Chrome 浏览器会自动打开
- Appium Inspector 左侧显示手机截图，右侧显示元素树

**等待时间**：首次连接约 10-30 秒（取决于手机性能和 APP 大小）。

---

## 四、在 Inspector 中操作手机

Session 启动成功后，Inspector 提供以下交互能力：

### 4.1 顶部工具栏

| 按钮 | 功能 | 快捷键 | 说明 |
|------|------|--------|------|
| 🔍 **Select Element** | 选择元素 | — | 点击截图上任意位置 → 自动定位到该元素 |
| 👆 **Tap** | 点击 | — | 模拟手指点击，等同于 `driver.click()` |
| 👆↔ **Swipe** | 滑动 | — | 在截图上拖动，模拟手指滑动 |
| ⌨ **Send Keys** | 文本输入 | — | 向当前选中元素输入文本 |
| 📷 **Screenshot** | 截图 | — | 刷新当前屏幕截图 |
| 🔄 **Refresh** | 刷新 | — | 刷新截图和元素树 |
| ⏪ **Back** | 返回 | — | 按 Android 返回键 |
| 🔍 **Search** | 搜索元素 | — | 按 xpath/id/class 搜索元素 |

### 4.2 元素树查看

右侧面板显示页面元素的层级树：

```
🌳 元素树
├── android.widget.FrameLayout
│   ├── android.widget.LinearLayout
│   │   ├── android.widget.TextView  [text="首页"]
│   │   └── android.widget.Button    [resource-id="btn_login"]
│   └── android.widget.EditText      [hint="请输入用户名"]
└── ...
```

- **点击元素树中任意节点** → 左侧截图高亮该元素位置
- **点击截图上任意位置（Select Element 模式）** → 右侧自动展开对应节点

### 4.3 元素属性面板

点击某个元素后，**Selected Element** 面板显示该元素的所有属性：

| 属性 | 示例值 | Page Object 定位方式 |
|------|--------|---------------------|
| `resource-id` | `com.dolphin.atc:id/btn_login` | `(AppiumBy.ID, "com.dolphin.atc:id/btn_login")` |
| `content-desc` | `登录按钮` | `(AppiumBy.ACCESSIBILITY_ID, "登录按钮")` |
| `text` | `登录` | `(AppiumBy.XPATH, "//*[@text='登录']")` |
| `class` | `android.widget.Button` | `(AppiumBy.CLASS_NAME, "android.widget.Button")` |
| `xpath` | `//android.widget.Button[@text='登录']` | `(AppiumBy.XPATH, "...")` |
| `bounds` | `[0,100][1080,250]` | 用于计算坐标点击 |
| `clickable` | `true` | 判断可点击性 |
| `enabled` | `true` | 判断可用性 |
| `displayed` | `true` | 判断可见性 |

### 4.4 定位策略优先级

将属性值写入 Page Object 时，遵循以下优先级（可靠性从高到低）：

```
1. accessibility-id (content-desc)    → AppiumBy.ACCESSIBILITY_ID
2. resource-id                        → AppiumBy.ID
3. xpath (带明确属性的)               → AppiumBy.XPATH
4. class_name                         → AppiumBy.CLASS_NAME
```

**Page Object 写入示例：**

```python
# pages/login_page.py
from appium.webdriver.common.appiumby import AppiumBy

class LoginPage(BasePage):
    # 优先使用 accessibility-id（最稳定）
    USERNAME_INPUT = (AppiumBy.ACCESSIBILITY_ID, "用户名输入框")

    # 其次使用 resource-id
    PASSWORD_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_password")

    # 再次使用 xpath
    LOGIN_BUTTON = (AppiumBy.XPATH, "//android.widget.Button[@text='登录']")

    # 最低优先级 class_name（容易重复）
    ALL_BUTTONS = (AppiumBy.CLASS_NAME, "android.widget.Button")
```

---

## 五、常用操作速查

### 5.1 浏览器模式 — 本地页面测试完整命令序列

```powershell
# ===== 终端1: 启动页面服务器 =====
cd D:\liyang\code\Android_Auto_Test\mobile-test-framework
.venv\Scripts\Activate.ps1
adb reverse tcp:8080 tcp:8080   # 建立端口转发
python serve_pages.py           # 启动 HTTP 服务器（端口 8080）

# ===== 终端2: 启动 Appium Server =====
appium --relaxed-security --allow-cors

# ===== 打开 Appium Inspector =====
# 双击 D:\Appium-Inspector\Appium Inspector.exe
# 填入:
#   Remote Host: 127.0.0.1
#   Remote Port: 4723
#   Remote Path: /
# JSON Capabilities: 场景A 的浏览器模式 JSON
# 点击 Start Session

# ===== 在 Inspector 中操作 =====
# 顶部地址栏输入: http://127.0.0.1:8080/小程序_首页.html
# 点击刷新按钮 → 查看页面元素
```

### 5.2 原生模式 — 项目 APK 测试

```powershell
# ===== 终端1: 启动 Appium Server =====
appium --relaxed-security --allow-cors

# ===== 打开 Appium Inspector =====
# 填入场景B 的原生模式 JSON Capabilities
# 点击 Start Session → APP 自动启动

# ===== 页面切换（在 Inspector 中无法直接切换 Activity） =====
# 需要配合代码或 ADB:
>>> driver.start_activity("com.dolphin.atc", ".LoginActivity")
```

### 5.3 查看任意 APP 的完整流程

```powershell
# Step 1: 找到目标 APP 包名和启动 Activity
adb shell pm list packages -3 | findstr "关键字"
adb shell cmd package resolve-activity --brief "com.example.app"

# Step 2: 填入场景C 的 JSON Capabilities（修改 appPackage 和 appActivity）
# Step 3: Start Session → 目标 APP 自动打开 → 查看元素
```

### 5.4 在 Inspector 中手动导航（浏览器模式）

Session 启动后，如果需要在手机 Chrome 中访问不同页面：

1. 在 Inspector 顶部的地址栏输入新 URL
2. 按回车
3. 点击 🔄 **Refresh** 按钮刷新截图和元素树
4. 即可看到新页面的元素

### 5.5 Session 断开与重连

- **断开**：点击 Inspector 右上角的 **X（Close Session）** 或直接关闭 Inspector
- **重连**：重新填入 Capabilities → 点击 **Start Session**
- **注意**：重连时如果手机上 Chrome/APP 还在运行，`noReset: true` 会保留页面状态

---

## 六、Capabilities 参数完整参考

| 参数 | 必填 | 类型 | 说明 | 示例 |
|------|------|------|------|------|
| `platformName` | ✅ | string | 平台名称，固定 `Android` | `"Android"` |
| `appium:automationName` | ✅ | string | 自动化引擎 | `"UiAutomator2"` |
| `appium:deviceName` | ✅ | string | 设备名称（可任意填） | `"24117RK2CC"` |
| `appium:udid` | ✅ | string | 设备序列号，`adb devices` 第一列 | `"24117RK2CC"` |
| `appium:platformVersion` | ✅ | string | Android 版本号 | `"16"` |
| `browserName` | ⚡ | string | 浏览器模式填 `"Chrome"`，原生模式**删除此行** | `"Chrome"` |
| `appium:appPackage` | ⚡ | string | 原生模式：APP 包名 | `"com.dolphin.atc"` |
| `appium:appActivity` | ⚡ | string | 原生模式：启动 Activity | `".MainActivity"` |
| `appium:noReset` | 推荐 | bool | `true`=不重置 APP 数据 | `true` |
| `appium:fullReset` | 可选 | bool | `true`=卸载重装 APP | `false` |
| `appium:autoGrantPermissions` | 推荐 | bool | 自动授予运行时权限 | `true` |
| `appium:newCommandTimeout` | 推荐 | number | 无操作自动断开秒数 | `120` |
| `appium:skipDeviceInitialization` | ⚠️ | bool | Android 14+ **必须为 true** | `true` |
| `appium:skipServerInstallation` | ⚠️ | bool | Android 14+ **必须为 true** | `true` |
| `appium:language` | 可选 | string | 设备语言 | `"zh"` |
| `appium:locale` | 可选 | string | 设备区域 | `"CN"` |

> ⚡ = 浏览器模式和原生模式**二选一**，不可同时存在  
> ⚠️ = Android 14 (API 34) 及以上**必须配置**

---

## 七、通过 ADB 获取任意 APP 的配置信息

以下命令帮助你快速找到任意 APP 的 `appPackage` 和 `appActivity`：

### 7.1 列出已安装 APP

```powershell
# 列出所有第三方应用
adb shell pm list packages -3

# 按关键字搜索
adb shell pm list packages | findstr <关键字>

# 示例：搜索所有 dolphin 相关应用
adb shell pm list packages | findstr dolphin
# 输出: package:com.dolphin.atc
```

### 7.2 查看 APP 的启动 Activity

```powershell
# 方法1（推荐）: cmd package resolve-activity
adb shell cmd package resolve-activity --brief com.dolphin.atc
# 输出: com.dolphin.atc/.MainActivity
#       → appPackage = "com.dolphin.atc"
#       → appActivity = ".MainActivity"

# 方法2: 查看 AndroidManifest 中的 LAUNCHER
adb shell dumpsys package com.dolphin.atc | findstr "android.intent.action.MAIN" -A 3

# 方法3: 使用项目内置 Python 工具
cd D:\liyang\code\Android_Auto_Test\mobile-test-framework
.venv\Scripts\Activate.ps1
python -i manual_test.py
>>> find_app("dolphin")            # 搜索
>>> inspect_app("com.dolphin.atc")  # 查看详情
# 输出:
#   Main Activity: .MainActivity
#   For config.yaml:
#     app_package: "com.dolphin.atc"
#     app_activity: ".MainActivity"
```

### 7.3 查看当前前台 APP

```powershell
# Android 10+
adb shell dumpsys window windows | findstr "mCurrentFocus"
# 输出: mCurrentFocus=Window{a1b2c3 ... com.dolphin.atc/com.dolphin.atc.MainActivity}
#                                 ↑ 包名                ↑ Activity

# 或使用项目工具
python -i manual_test.py
>>> info()  # 显示当前 APP 和设备信息
```

---

## 八、快捷启动脚本

将以下内容保存为 `start_appium.bat`，双击即可一键启动 Appium Server + 打开 Inspector：

```bat
@echo off
echo ============================================
echo   启动 Appium Server + Inspector
echo ============================================
echo.

echo [1/3] 检查设备连接...
adb devices | findstr "device" >nul
if %errorlevel% neq 0 (
    echo [FAIL] 未检测到设备！请检查 USB 连接。
    pause
    exit /b 1
)
echo [OK] 设备已连接

echo [2/3] 启动 Appium Server...
start "Appium-Server" cmd /c "appium --relaxed-security --allow-cors"
echo [OK] Appium Server 已启动（后台窗口）

echo [3/3] 打开 Appium Inspector...
start "" "D:\Appium-Inspector\Appium Inspector.exe"
echo [OK] Inspector 已打开

echo.
echo ============================================
echo   请在 Inspector 中:
echo   1. 确认 Remote Host: 127.0.0.1
echo   2. 确认 Remote Port: 4723
echo   3. 确认 Remote Path: /
echo   4. 粘贴 JSON Capabilities
echo   5. 点击 Start Session
echo ============================================
pause
```

---

## 九、故障排查

### 9.1 Session 创建失败

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Could not find a connected Android device` | 设备未连接或 UDID 错误 | `adb devices` 检查，确认 UDID 正确 |
| `Device not in list` | UDID 填了设备型号名而非序列号 | 用 `adb devices` 第一列的值 |
| `unknown command` on GET /status | Appium Server 未启动或端口错误 | 确认 Server 在 4723 端口运行 |
| `Failed to establish a new connection` | 端口 4723 连接被拒绝 | 确认 Appium Server 正在运行 |
| `Activity class does not exist` | `appPackage`/`appActivity` 填错 | 见第七节获取正确值 |
| `An unknown server-side error` / `No Chromedriver` | ChromeDriver 版本不匹配 | 下载匹配手机 Chrome 版本的 ChromeDriver |
| `A new session could not be created` + `original error: 'GET /status'` | Remote Path 填了 `/wd/hub` | 改为 `/`（Appium 3.x 的 base path） |

### 9.2 Appium 端口被占用

```
[HTTP] Could not start REST http interface listener.
EADDRINUSE: address already in use 0.0.0.0:4723
```

**解决**：
```powershell
# PowerShell
Get-NetTCPConnection -LocalPort 4723 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# 或 CMD
netstat -ano | findstr ":4723"
taskkill /PID <PID> /F
```

### 9.3 CORS 错误

```
Access to fetch at 'http://127.0.0.1:4723/...' from origin '...' has been blocked by CORS policy
```

**解决**：确保启动 Appium Server 时带了 `--allow-cors` 参数：
```powershell
appium --relaxed-security --allow-cors
```

### 9.4 元素树为空或不完整

**原因**：
- 页面未完全加载
- 某些动态加载的内容未出现
- 元素在 WebView 中（浏览器模式可能有 context 切换问题）

**解决**：
1. 点击 🔄 Refresh 刷新
2. 在手机上手动滚动/点击让元素出现后再刷新
3. 等待几秒让页面完全加载

### 9.5 截图无法显示 / 黑屏

**原因**：
- 页面包含安全内容（如银行 APP 的支付页面、Chrome 无痕模式）
- 手机锁屏

**解决**：
1. 确保手机屏幕已解锁且处于亮屏状态
2. 某些 APP 的安全页面确实无法截图（系统限制）

### 9.6 Session 意外断开

**原因**：
- 手机 USB 线松动
- `newCommandTimeout` 超时（默认 60 秒）
- Appium Server 崩溃

**解决**：
1. 检查 USB 连接 → 重新插拔
2. 增大 `newCommandTimeout` 值（如 `300` = 5分钟）
3. 重启 Appium Server → 重新 Start Session

---

## 十、环境架构

```
┌──────────────────────────────────────────────────────────────────┐
│                          PC (Windows)                             │
│                                                                   │
│  ┌─────────────────┐     ┌──────────────────┐                    │
│  │  Appium Server   │     │ Appium Inspector │                    │
│  │  (port 4723)     │◄───►│ (GUI 客户端)     │                    │
│  │  v3.6.0          │     │ D:\Appium-Ins... │                    │
│  │  --relaxed-sec   │     └──────────────────┘                    │
│  │  --allow-cors    │                                             │
│  └────────┬─────────┘                                             │
│           │ W3C WebDriver Protocol                                │
│  ┌────────▼─────────┐                                             │
│  │  UiAutomator2    │                                             │
│  │  Driver 8.2.2    │                                             │
│  └────────┬─────────┘                                             │
│           │                                                       │
│  ┌────────▼─────────┐                                             │
│  │  ADB (37.0.1)    │                                             │
│  │  platform-tools/  │                                             │
│  └────────┬─────────┘                                             │
│           │ USB Cable                                             │
└───────────┼──────────────────────────────────────────────────────┘
            │
    ┌───────▼───────────┐
    │  Android 真机      │
    │  24117RK2CC        │
    │  Android 16        │
    │  1440×3200         │
    │                    │
    │  ┌──────────────┐  │
    │  │ 被测 APP      │  │
    │  │ 或 Chrome     │  │
    │  │ 或系统界面    │  │
    │  └──────────────┘  │
    └────────────────────┘
```

---

## 十一、定位器对照速查

| Appium Inspector 属性 | AppiumBy 常量 | Page Object 写法 |
|----------------------|---------------|-----------------|
| `resource-id` | `AppiumBy.ID` | `(AppiumBy.ID, "com.dolphin.atc:id/btn_login")` |
| `content-desc` | `AppiumBy.ACCESSIBILITY_ID` | `(AppiumBy.ACCESSIBILITY_ID, "登录按钮")` |
| `text` | `AppiumBy.XPATH` | `(AppiumBy.XPATH, "//*[@text='登录']")` |
| `class` | `AppiumBy.CLASS_NAME` | `(AppiumBy.CLASS_NAME, "android.widget.Button")` |
| `xpath` | `AppiumBy.XPATH` | `(AppiumBy.XPATH, "//android.widget.Button[@text='登录']")` |
| `hint` | `AppiumBy.XPATH` | `(AppiumBy.XPATH, "//*[@hint='请输入用户名']")` |
| `checkable` | — | 辅助判断，不直接用于定位 |

---

## 十二、停止服务

```powershell
# 方法1: 关闭 Appium Server 终端窗口 (Ctrl+C)

# 方法2: 强制终止占用 4723 端口的进程
netstat -ano | findstr ":4723"
taskkill /PID <PID> /F

# 方法3: 在 Appium Server GUI 中点击 Stop Server
```

---

*文档版本：v2.0*  
*最后更新：2026-08-05*
