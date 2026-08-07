# Appium Android 自动化测试框架 — 环境配置完整指南

> 适用平台：Windows 10/11  
> 目标：从零搭建 Appium Android 自动化测试环境  
> 更新日期：2026-08-04

---

## 一、软件清单总览

| 序号 | 软件 | 推荐版本 | 本项目实际版本 | 用途 |
|------|------|---------|---------------|------|
| 1 | JDK (Java Development Kit) | 11 / 17 / 21 | 21.0.12 | Appium 与 Android SDK 运行时依赖 |
| 2 | Node.js | 18 LTS+ | - | Appium Server 运行环境 (npm) |
| 3 | Android SDK (Platform Tools) | 34+ | 37.0.1 | 提供 adb、aapt 等 Android 调试工具 |
| 4 | Appium Server (CLI) | 2.x / 3.x | 3.6.0 | 移动端自动化测试服务端 |
| 5 | Appium UiAutomator2 Driver | latest | 8.2.2 | Android 自动化引擎驱动 |
| 6 | Appium Server GUI (可选) | latest | - | Appium 图形化管理界面 |
| 7 | Appium Inspector | latest | - | 元素定位可视化工具 |
| 8 | Python | 3.9 - 3.13 | 3.13 | 测试脚本语言 |
| 9 | Appium-Python-Client | 4.0+ | - | Python 调用 Appium 的客户端库 |
| 10 | Pytest + Allure | 8.0+ / 2.x | - | 测试框架 + 报告 |
| 11 | ChromeDriver (浏览器模式) | 与手机 Chrome 匹配 | 150.0.7871.124 | Chrome 浏览器自动化驱动 |

---

## 二、各软件安装与配置详解

### 2.1 JDK — Java Development Kit

**作用**：Android SDK 和 Appium 部分组件依赖 Java 运行时。

#### 下载

- 官网：https://www.oracle.com/java/technologies/downloads/
- 推荐 OpenJDK：https://adoptium.net/

#### 安装

安装到无中文、无空格的路径：
```
C:\Program Files\Java\jdk-21.0.12
```

#### 环境变量配置

1. `Win + R` → 输入 `sysdm.cpl` → 回车
2. 高级 → 环境变量
3. **系统变量 → 新建**：
   - 变量名：`JAVA_HOME`
   - 变量值：`C:\Program Files\Java\jdk-21.0.12`
4. **系统变量 → Path → 新建**：
   ```
   %JAVA_HOME%\bin
   ```

#### 验证

```powershell
java -version
# 预期输出：
# java version "21.0.12" 2025-07-15 LTS
# Java(TM) SE Runtime Environment (build 21.0.12+8-LTS-291)
```

---

### 2.2 Node.js

**作用**：Appium Server 基于 Node.js 运行，通过 npm 安装。

#### 下载

- 官网：https://nodejs.org/
- 推荐 **LTS 版本**（长期支持版）

#### 安装

一路 Next 即可，安装程序会自动添加到 PATH。

#### 验证

```powershell
node -v
# 预期输出：v18.x.x 或 v20.x.x 或 v22.x.x

npm -v
# 预期输出：10.x.x
```

---

### 2.3 Android SDK (Platform Tools)

**作用**：提供 adb（Android Debug Bridge）等命令行工具，用于 PC 与 Android 设备通信。

#### 下载

- 官方：https://developer.android.com/tools/releases/platform-tools
- 只需下载 **SDK Platform Tools**（约 15MB），无需安装完整 Android Studio

#### 安装

解压到目标目录：
```
C:\Users\keda\AppData\Local\Android\Sdk
```

目录结构应为：
```
Android\Sdk\
├── platform-tools\
│   ├── adb.exe
│   ├── fastboot.exe
│   └── ...
├── build-tools\
├── cmdline-tools\
└── ...
```

#### 环境变量配置

1. **系统变量 → 新建**：
   - 变量名：`ANDROID_HOME`
   - 变量值：`C:\Users\keda\AppData\Local\Android\Sdk`

2. **系统变量 → Path → 新建**，添加以下 4 条：
   ```
   %ANDROID_HOME%\platform-tools
   %ANDROID_HOME%\tools
   %ANDROID_HOME%\build-tools
   %ANDROID_HOME%\emulator
   ```

#### 验证

```powershell
adb version
# 预期输出：
# Android Debug Bridge version 1.0.41
# Version 37.0.1
```

---

### 2.4 Appium Server（命令行版）

**作用**：Appium 核心服务端，接收测试脚本指令并转发到手机执行。

#### 安装

```powershell
npm install -g appium
```

> 国内网络慢可切换镜像源：
> ```powershell
> npm config set registry https://registry.npmmirror.com
> ```

#### 安装 Android 驱动

```powershell
appium driver install uiautomator2
```

#### 验证

```powershell
appium --version
# 预期输出：3.6.0

appium driver list
# 预期输出：
# ✔ Listing available drivers
# - uiautomator2 [installed (npm)]
```

---

### 2.5 Appium Server GUI（可选）

**作用**：Appium 桌面版，提供图形化启动/停止服务和日志查看。

- 路径：`C:\Users\keda\AppData\Local\Programs\Appium Server GUI\Appium Server GUI.exe`
- 功能等同于命令行 `appium`，两者选其一运行即可

---

### 2.6 Appium Inspector

**作用**：可视化查看手机屏幕和 APP 元素树，获取元素定位器（resource-id、xpath、class 等）。

- 路径：`D:\Appium-Inspector\Appium Inspector.exe`
- 下载地址：https://github.com/appium/appium-inspector/releases

#### 连接配置

| 配置项 | 值 |
|--------|-----|
| Remote Host | `127.0.0.1` |
| Remote Port | `4723` |
| Remote Path | `/` （**注意**：Appium 3.x 是 `/`，不是 `/wd/hub`） |

#### JSON Capabilities 配置

**浏览器模式**（手机 Chrome 打开 H5 页面）：

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:deviceName": "24117RK2CC",
  "appium:udid": "438014b9",
  "appium:platformVersion": "16",
  "browserName": "Chrome",
  "appium:noReset": true,
  "appium:autoGrantPermissions": true,
  "appium:newCommandTimeout": 120,
  "appium:skipDeviceInitialization": true,
  "appium:skipServerInstallation": true
}
```

**原生 APP 模式**（APK 就绪后）：

```json
{
  "platformName": "Android",
  "appium:automationName": "UiAutomator2",
  "appium:deviceName": "24117RK2CC",
  "appium:udid": "438014b9",
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

---

### 2.7 Python 环境

**作用**：编写和执行自动化测试脚本。

#### 安装

- 官网：https://www.python.org/downloads/
- 推荐 **Python 3.11**（Appium-Python-Client 兼容性最佳）
- 本项目使用 Python 3.13
- 安装时勾选 **Add Python to PATH**

#### 创建虚拟环境

```powershell
cd D:\liyang\code\Android_Auto_Test\mobile-test-framework
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### 安装 Python 依赖

```powershell
pip install -r requirements.txt
```

`requirements.txt` 内容：

```
Appium-Python-Client>=4.0.0
selenium>=4.15.0
pytest>=8.0.0
pytest-xdist>=3.5.0
pytest-rerunfailures>=13.0
allure-pytest>=2.13.0
PyYAML>=6.0
colorlog>=6.8.0
python-dateutil>=2.8.0
Pillow>=10.0.0
```

#### 验证

```powershell
python -c "from appium import webdriver; print('OK')"
# 预期输出：OK
```

---

### 2.8 ChromeDriver（浏览器模式专用）

**作用**：浏览器模式下，Appium 通过 ChromeDriver 控制手机 Chrome。

#### 版本匹配规则

手机 Chrome 版本 **必须** 与 ChromeDriver 版本完全一致。

#### 查看手机 Chrome 版本

```powershell
adb shell dumpsys package com.android.chrome | findstr versionName
```

#### 下载 ChromeDriver

- 地址：https://storage.googleapis.com/chrome-for-testing-public/

#### 安装位置

将 `chromedriver.exe` 放到：

```
C:\Users\keda\.appium\chromedriver\<版本号>\chromedriver.exe
```

例如 Chrome 150.0.7871：

```
C:\Users\keda\.appium\chromedriver\150.0.7871.124\chromedriver.exe
```

---

## 三、环境变量配置总结

配置完成后，系统应包含以下环境变量：

### 系统变量（新建）

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `JAVA_HOME` | `C:\Program Files\Java\jdk-21.0.12` | JDK 安装目录 |
| `ANDROID_HOME` | `C:\Users\keda\AppData\Local\Android\Sdk` | Android SDK 目录 |

### 系统变量 Path（新增条目）

| 路径 | 说明 |
|------|------|
| `%JAVA_HOME%\bin` | java、javac 命令 |
| `%ANDROID_HOME%\platform-tools` | adb、fastboot 命令 |
| `%ANDROID_HOME%\tools` | Android 工具集 |
| `%ANDROID_HOME%\build-tools` | 构建工具 |
| `%ANDROID_HOME%\emulator` | 模拟器命令 |

> ⚠️ 每次修改环境变量后，需要**重新打开终端**才能生效。

---

## 四、手机端配置

### 4.1 开启开发者模式

1. 设置 → 关于手机
2. 连续点击 **版本号** 7 次
3. 提示"您已处于开发者模式"

### 4.2 开启 USB 调试

1. 设置 → 系统 → 开发人员选项
2. 开启 **USB 调试**
3. 开启 **安装 via USB**（部分手机需要）
4. 开启 **USB 调试（安全设置）**（部分手机需要）

### 4.3 连接电脑

1. USB 数据线连接手机和电脑
2. 手机上弹出"允许 USB 调试"对话框 → 勾选 **一律允许** → 点击 **允许**
3. 验证连接：

```powershell
adb devices
# 预期输出：
# List of devices attached
# 438014b9    device
```

---

## 五、完整验证流程

按顺序执行以下 6 项验证，全部通过即表示环境搭建完成。

### ✅ 验证 1：Java 环境

```powershell
java -version
```

### ✅ 验证 2：Node.js 环境

```powershell
node -v
npm -v
```

### ✅ 验证 3：ADB 与设备连接

```powershell
adb version
adb devices
```

### ✅ 验证 4：Appium 环境

```powershell
appium --version
appium driver list  # 确认 uiautomator2 已安装
```

### ✅ 验证 5：Python 环境

```powershell
cd D:\liyang\code\Android_Auto_Test\mobile-test-framework
.venv\Scripts\Activate.ps1
python setup_check.py --fix
# 10 项检查全部 PASS
```

### ✅ 验证 6：Appium Inspector 连接

1. 启动 Appium Server：
   ```powershell
   appium --relaxed-security --allow-cors
   ```
2. 打开 Appium Inspector
3. 填入连接配置和 JSON Capabilities
4. 点击 Start Session → 成功加载手机截图和元素树

---

## 六、Capabilities 参数详解

| 参数 | 必填 | 说明 | 示例值 |
|------|------|------|--------|
| `platformName` | ✅ | 平台名称 | `Android` |
| `appium:automationName` | ✅ | 自动化引擎 | `UiAutomator2` |
| `appium:deviceName` | ✅ | 设备名称（可自定义） | `24117RK2CC` |
| `appium:udid` | ✅ | 设备序列号（`adb devices` 获取） | `438014b9` |
| `appium:platformVersion` | ✅ | Android 版本号 | `16` |
| `browserName` | ⚡ | 浏览器模式时填 `Chrome`；原生模式时**删除此项** | `Chrome` |
| `appium:appPackage` | ⚡ | 原生模式：APP 包名 | `com.dolphin.atc` |
| `appium:appActivity` | ⚡ | 原生模式：启动 Activity | `.MainActivity` |
| `appium:noReset` | 推荐 | `true` = 不重置 APP 数据 | `true` |
| `appium:autoGrantPermissions` | 推荐 | 自动授予权限 | `true` |
| `appium:newCommandTimeout` | 推荐 | 命令超时（秒） | `120` |
| `appium:skipDeviceInitialization` | ⚠️ | Android 14+ 必须设为 `true` | `true` |
| `appium:skipServerInstallation` | ⚠️ | 跳过重复安装 Appium 设置 | `true` |

> ⚡ = 浏览器模式和原生模式二选一，不可同时存在  
> ⚠️ = Android 14 (API 34) 及以上必须配置

---

## 七、关键注意事项

### 7.1 版本兼容性

| 组合 | 说明 |
|------|------|
| Appium 3.x + UiAutomator2 8.x | ✅ 推荐 |
| Appium 3.x → Remote Path | `/`（不是 `/wd/hub`） |
| Appium 2.x → Remote Path | `/` |
| Appium 1.x → Remote Path | `/wd/hub` |

### 7.2 Android 14+ 特殊配置

Android 14/15/16 必须加这两个参数：
```json
"appium:skipDeviceInitialization": true,
"appium:skipServerInstallation": true
```

同时启动 Appium 时必须加：
```powershell
appium --relaxed-security --allow-cors
```

### 7.3 常见坑点

| 问题 | 原因 | 解决 |
|------|------|------|
| `Device not in list` | UDID 填了型号名而非序列号 | 用 `adb devices` 查真实序列号 |
| `unknown command` on GET /status | CORS 未开 | 加 `--allow-cors` 参数 |
| `context` 报错 | 浏览器模式无 NATIVE context | 忽略，不影响使用 |
| 端口占用 | 4723 被其他进程使用 | `taskkill /PID <pid> /F` |
| ChromeDriver 不匹配 | 版本与手机 Chrome 不一致 | 下载匹配版本 |

### 7.4 安装路径规范

- ❌ 避免中文路径
- ❌ 避免空格路径（部分工具不兼容）
- ✅ 推荐全英文、无空格路径

---

## 八、环境架构图

```
┌─────────────────────────────────────────────────────────┐
│                     测试 PC (Windows)                     │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │   JDK 21  │  │ Node.js  │  │   Python 3.13 (.venv)│   │
│  │           │  │  + npm   │  │   + Appium-Client     │   │
│  └────┬─────┘  └────┬─────┘  │   + Pytest + Allure   │   │
│       │             │        └───────────┬───────────┘   │
│       │             │                    │               │
│       │      ┌──────▼──────────┐         │               │
│       │      │  Appium Server  │◄────────┘               │
│       │      │  (port 4723)    │  W3C WebDriver Protocol │
│       │      │  version 3.6.0  │                         │
│       │      └──────┬──────────┘                         │
│       │             │                                    │
│       │      ┌──────▼──────────┐                         │
│       │      │ UiAutomator2    │  --allow-cors           │
│       │      │ Driver 8.2.2    │  --relaxed-security     │
│       │      └──────┬──────────┘                         │
│       │             │                                    │
│  ┌────▼─────────────▼──────────────────────────────┐     │
│  │              Android SDK                          │     │
│  │  platform-tools/ (adb.exe, fastboot.exe...)      │     │
│  │  ANDROID_HOME = C:\Users\keda\...\Android\Sdk   │     │
│  └──────────────────────┬──────────────────────────┘     │
│                         │ USB / TCP                       │
└─────────────────────────┼────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │   Android 真机 / 模拟器  │
              │   model: 24117RK2CC     │
              │   udid: 438014b9        │
              │   Android 16            │
              │   Chrome 150.0.7871     │
              │   (或被测 APP)           │
              └─────────────────────────┘
```

---

## 九、启动命令速查

### 日常启动（3 个终端）

```powershell
# 终端 1：Appium Server
appium --relaxed-security --allow-cors

# 终端 2：页面服务器（浏览器模式）
cd D:\liyang\code\Android_Auto_Test\mobile-test-framework
.venv\Scripts\Activate.ps1
python serve_pages.py

# 终端 3：运行测试
cd D:\liyang\code\Android_Auto_Test\mobile-test-framework
.venv\Scripts\Activate.ps1
python run_tests.py --smoke
```

### 后台启动 Appium

```powershell
start /B appium --relaxed-security --allow-cors > nul 2>&1
```

### 关闭 Appium

```powershell
# 查找占用 4723 端口的进程
netstat -ano | findstr ":4723"
# 强制终止（替换为实际的 PID）
taskkill /PID <PID> /F
```

---

## 十、扩展参考

- Appium 官方文档：https://appium.io/docs/en/latest/
- Appium Inspector Releases：https://github.com/appium/appium-inspector/releases
- Android SDK Platform Tools：https://developer.android.com/tools/releases/platform-tools
- ChromeDriver 下载：https://storage.googleapis.com/chrome-for-testing-public/
- Adoptium JDK：https://adoptium.net/

---

*文档版本：v1.0*  
*最后更新：2026-08-04*
