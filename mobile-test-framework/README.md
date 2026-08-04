# 低空空管自动化系统 — 移动端自动化测试框架

> **Low-Altitude Airspace Management System — Mobile Automation Test Framework**

基于 **Python + Appium2 + Pytest + Allure + Page Object Model** 的企业级Android自动化测试框架。

---

## 目录

- [项目概述](#项目概述)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
  - [1. 安装Python依赖](#1-安装python依赖)
  - [2. 安装Appium2](#2-安装appium2)
  - [3. 配置ADB](#3-配置adb)
  - [4. 连接Android设备](#4-连接android设备)
  - [5. 配置测试参数](#5-配置测试参数)
- [运行测试](#运行测试)
  - [命令行方式](#命令行方式)
  - [运行脚本方式](#运行脚本方式)
  - [运行特定模块](#运行特定模块)
  - [并行执行](#并行执行)
- [生成测试报告](#生成测试报告)
- [测试模块说明](#测试模块说明)
- [框架设计](#框架设计)
- [扩展指南](#扩展指南)
- [常见问题](#常见问题)

---

## 项目概述

本框架为**低空空管自动化系统**移动端Android APP提供全面的自动化测试能力。

### 测试覆盖范围

| 模块 | 测试内容 | 状态 |
|------|---------|------|
| **登录** | 账号密码登录、异常输入、验证码、找回密码 | ✅ |
| **首页** | 消息通知列表、Tab切换、AI智能问答、对话态切换 | ✅ |
| **申报(飞行计划)** | GPS定位、起降场搜索、计划创建、审批进度、离线条存 | ✅ |
| **资讯** | 法律法规、通知公告、文章详情 | ✅ |
| **我的** | 信誉积分、关于我们、退出登录 | ✅ |

---

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 编程语言 |
| Appium | 2.x | 移动端自动化驱动 |
| Appium UiAutomator2 | latest | Android自动化引擎 |
| Pytest | 8.0+ | 测试框架 |
| Allure | 2.x | 测试报告 |
| PyYAML | 6.0+ | 配置和数据管理 |
| Appium-Python-Client | 4.0+ | Python Appium客户端 |

---

## 项目结构

```
mobile-test-framework/
├── config/                         # 配置管理
│   ├── __init__.py
│   ├── config.yaml                 # 主配置文件 (设备/超时/日志/账号)
│   └── config_manager.py           # 配置加载器 (环境切换/多设备)
│
├── drivers/                        # 驱动层
│   ├── __init__.py
│   └── appium_driver.py            # Appium Driver封装 (真机/模拟器/iOS扩展)
│
├── pages/                          # Page Object层
│   ├── __init__.py
│   ├── base_page.py                # 基础页面 (查找/点击/滑动/等待/截图)
│   ├── login_page.py               # 登录页
│   ├── home_page.py                # 首页 (双态: 通知+AI对话)
│   ├── flight_page.py              # 申报页 (地图/GPS/计划创建/审批进度)
│   ├── news_page.py                # 资讯页 (法律法/通知公告)
│   └── mine_page.py                # 我的页 (信誉积分/退出)
│
├── tests/                          # 测试用例层
│   ├── __init__.py
│   ├── conftest.py                 # Pytest配置 (Fixtures/Hooks/Allure)
│   ├── test_login.py               # 登录测试 (8个用例)
│   ├── test_home.py                # 首页测试 (8个用例)
│   ├── test_flight.py              # 飞行计划测试 (8个用例)
│   ├── test_news.py                # 资讯测试 (5个用例)
│   └── test_mine.py                # 我的测试 (7个用例)
│
├── utils/                          # 工具层
│   ├── __init__.py
│   ├── logger.py                   # 日志系统 (双通道/滚动/彩色)
│   ├── screenshot.py               # 截图管理 (失败自动截图/Allure集成)
│   └── adb_helper.py              # ADB工具 (GPS模拟/网络控制/应用管理)
│
├── data/                           # 测试数据
│   ├── login_data.yaml             # 登录参数化数据
│   ├── flight_data.yaml            # 飞行计划参数化数据
│   └── test_accounts.yaml          # 测试账号
│
├── reports/                        # 测试报告输出
│   ├── allure-results/             # Allure原始数据
│   └── screenshots/                # 失败截图
│
├── logs/                           # 执行日志
├── requirements.txt                # Python依赖
├── pytest.ini                      # Pytest配置
├── run_tests.py                    # 一键运行脚本
└── README.md                       # 本文档
```

---

## 环境要求

### 硬件

| 项目 | 要求 |
|------|------|
| PC系统 | Windows 10/11 或 macOS 或 Linux |
| 内存 | 8GB以上 |
| USB接口 | 正常可用 |
| Android设备 | Android 10+ (真机或模拟器) |

### 软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.9 - 3.12 | 推荐3.11 |
| Node.js | 16+ | Appium2运行时 |
| Java JDK | 11+ | Android SDK需要 |
| Android SDK Platform Tools | 34+ | 提供adb等工具 |

---

## 快速开始

### 1. 安装Python依赖

```bash
cd mobile-test-framework
pip install -r requirements.txt
```

### 2. 安装Appium2

```bash
# 安装Appium2服务端
npm install -g appium

# 安装Android驱动 (UiAutomator2)
appium driver install uiautomator2

# 验证安装
appium --version
appium driver list
```

输出示例：
```
✔ Listing available drivers
- uiautomator2 [installed (npm)]
```

### 3. 配置ADB

**方式一：使用项目内置的 platform-tools**

项目上层目录 `platform-tools/` 已包含 adb.exe，框架会自动检测。

**方式二：手动配置环境变量**

1. 下载 [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools)
2. 解压到任意目录 (如 `C:\android-sdk\platform-tools`)
3. 将路径添加到系统环境变量 `PATH`
4. 验证：

```bash
adb version
# Android Debug Bridge version 1.0.41
# Version 34.0.x
```

### 4. 连接Android设备

#### 真机连接

1. 手机开启**开发者模式**：
   - 设置 → 关于手机 → **连续点击版本号7次**

2. 开启**USB调试**：
   - 设置 → 系统 → 开发人员选项 → 开启 USB调试

3. 用USB数据线连接电脑

4. 手机上点击"**允许USB调试**"

5. 验证连接：

```bash
adb devices
# List of devices attached
# XXXXXXXX    device
```

#### 模拟器连接

如果使用Android Studio Emulator：

```bash
# 启动模拟器后验证
adb devices
# List of devices attached
# emulator-5554    device
```

### 5. 配置测试参数

编辑 `config/config.yaml`，根据实际情况修改：

```yaml
# 设备配置
devices:
  - name: "Xiaomi14"
    udid: ""                      # 留空自动检测，或填入 adb devices 显示的ID
    app_package: "com.dolphin.atc"      # 替换为实际包名
    app_activity: ".MainActivity"       # 替换为实际Activity

# 测试账号
test_accounts:
  default:
    username: "your_test_username"
    password: "your_test_password"
```

---

## 运行测试

### 命令行方式

```bash
# 1. 先启动Appium Server (新开一个终端)
appium

# 2. 运行所有测试 (另一个终端)
cd mobile-test-framework
pytest tests/ -v --alluredir=reports/allure-results
```

### 运行脚本方式

```bash
# 运行所有测试
python run_tests.py

# 仅运行冒烟测试 (核心功能)
python run_tests.py --smoke

# 运行并自动打开Allure报告
python run_tests.py --report

# 并行执行 (2个worker)
python run_tests.py --parallel 2

# 指定设备
python run_tests.py --device 1
```

### 运行特定模块

```bash
# 登录模块
pytest tests/test_login.py -v

# 飞行计划模块
pytest tests/test_flight.py -v

# 运行特定标记
pytest tests/ -m smoke        # 冒烟测试
pytest tests/ -m login        # 登录测试
pytest tests/ -m gps          # GPS测试
pytest tests/ -m offline      # 离线测试
pytest tests/ -m "not slow"   # 排除慢测试
```

### 并行执行

```bash
# 2个worker并行
pytest tests/ -n 2 -v --alluredir=reports/allure-results

# 每个worker使用不同设备需要在 conftest 中配置worker-id到设备的映射
```

---

## 生成测试报告

```bash
# 1. 运行测试并生成Allure数据
pytest tests/ -v --alluredir=reports/allure-results

# 2. 生成并打开HTML报告
allure serve reports/allure-results

# 3. 或生成静态报告
allure generate reports/allure-results -o reports/allure-report --clean
```

报告包含：
- ✅ 测试用例执行状态 (通过/失败/跳过)
- 📊 测试趋势图表
- 📝 测试步骤详情
- 📸 失败截图附件
- 📄 页面源码 (用于调试)
- 🏷️ 按Epic/Feature/Story分类

---

## 测试模块说明

### 登录测试 (`test_login.py`)

| 用例 | 标记 | 说明 |
|------|------|------|
| `test_login_success` | smoke | 正常登录流程 |
| `test_login_failure[错误密码]` | login | 错误密码提示 |
| `test_login_failure[空账号]` | login | 空账号校验 |
| `test_login_failure[空密码]` | login | 空密码校验 |
| `test_login_wrong_captcha` | login | 错误验证码 |
| `test_refresh_captcha` | login | 刷新验证码 |
| `test_forgot_password_flow` | login, slow | 找回密码完整流程 |
| `test_wechat_login_entry` | login | 微信登录入口检测 |

### 首页测试 (`test_home.py`)

| 用例 | 标记 | 说明 |
|------|------|------|
| `test_notification_list_display` | smoke | 通知列表加载 |
| `test_switch_notify_tabs[审批/告警/协调]` | home | Tab切换 |
| `test_alert_read_filter` | home | 已读/未读筛选 |
| `test_coordination_acknowledge` | home | 管制通知操作 |
| `test_ai_question_input` | home | AI输入 |
| `test_chat_mode_switch` | home | 对话态切换 |
| `test_chat_history` | home | 对话历史 |
| `test_navigate_from_home[申报/资讯/我的]` | smoke | Tab跳转 |

### 飞行计划测试 (`test_flight.py`)

| 用例 | 标记 | 说明 |
|------|------|------|
| `test_gps_permission_allow` | gps | GPS允许定位 |
| `test_gps_permission_deny` | gps | GPS拒绝降级 |
| `test_search_airport` | flight | 起降场搜索 |
| `test_create_flight_plan` | flight, slow | 创建计划全流程 |
| `test_view_my_plans` | flight | 审批进度查询 |
| `test_filter_plans_by_status` | flight | 状态筛选 |
| `test_loiter_flight_draw` | flight, slow | 留空飞行绘制 |
| `test_offline_cache` | offline, slow | 断网暂存 |

### 资讯测试 (`test_news.py`)

| 用例 | 标记 | 说明 |
|------|------|------|
| `test_law_list` | smoke | 法律法规列表 |
| `test_law_detail` | news | 文章详情 |
| `test_notice_list` | news | 通知公告列表 |
| `test_switch_tabs` | news | Tab切换 |
| `test_article_attachment` | news | 附件检测 |

### 我的测试 (`test_mine.py`)

| 用例 | 标记 | 说明 |
|------|------|------|
| `test_credit_score_display` | smoke | 信誉积分显示 |
| `test_credit_level_mapping` | mine | 等级对应 |
| `test_credit_detail_entry` | mine | 明细入口 |
| `test_about_us` | mine | 关于我们 |
| `test_logout` | mine | 退出登录 |
| `test_logout_cancel` | mine | 取消退出 |
| `test_user_profile` | mine | 个人信息 |

---

## 框架设计

### 架构分层

```
┌─────────────────────────────────────────┐
│              测试用例层 (tests/)          │
│   test_login.py  test_home.py  ...       │
├─────────────────────────────────────────┤
│            Page Object层 (pages/)         │
│   LoginPage  HomePage  FlightPage  ...   │
│              BasePage                     │
├─────────────────────────────────────────┤
│              驱动层 (drivers/)            │
│         AppiumDriverManager             │
├─────────────────────────────────────────┤
│            基础设施层 (utils/ + config/)  │
│   Logger  Screenshot  ADB  Config       │
└─────────────────────────────────────────┘
```

### 设计模式

- **Page Object Model (POM)**: 每个页面封装为独立的Page类
- **单例模式**: ConfigManager全局唯一配置实例
- **工厂模式**: AppiumDriverManager根据平台创建对应driver
- **策略模式**: 通过YAML配置切换不同设备和环境

### 关键设计决策

1. **定位策略优先级**: `accessibility_id` > `resource-id` > `xpath` > `class_name`
2. **等待策略**: 统一使用`WebDriverWait`显式等待，避免`time.sleep()`
3. **失败截图**: 通过`pytest_runtest_makereport` hook自动触发
4. **数据驱动**: YAML管理测试数据，通过`@pytest.mark.parametrize`注入
5. **iOS扩展**: BasePage平台无关，config中预留iOS配置段

---

## 扩展指南

### 添加新页面

1. 在 `pages/` 下创建新文件，继承 `BasePage`
2. 定义元素定位器 (类常量)
3. 实现页面操作方法
4. 在 `tests/` 中创建对应测试文件

```python
# 示例: pages/new_feature_page.py
from pages.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy

class NewFeaturePage(BasePage):
    FEATURE_BUTTON = (AppiumBy.ID, "com.dolphin.atc:id/btn_feature")

    def click_feature(self):
        self.click(self.FEATURE_BUTTON)
        return self
```

### 添加iOS支持

1. 安装iOS驱动: `appium driver install xcuitest`
2. 在 `config/config.yaml` 的 `ios_devices` 段配置iOS设备
3. 使用: `driver_manager.get_driver(platform="iOS")`

### 添加新的配置环境

在 `config/config.yaml` 的 `environments` 段添加:

```yaml
environments:
  production:
    app_package: "com.dolphin.atc"
    app_activity: ".MainActivity"
```

使用: `TEST_ENV=production python run_tests.py`

---

## 常见问题

### Q: `adb devices` 显示 `unauthorized`？

**A**: 手机上重新插拔USB线，在弹出的"允许USB调试"对话框中点击"允许"。

### Q: Appium启动报错 `Could not find a connected Android device`？

**A**: 检查:
1. `adb devices` 是否显示设备
2. 设备是否已解锁屏幕
3. USB调试是否已开启

### Q: 测试运行时提示 `An element could not be located`？

**A**: 元素定位器需要与实际APP的resource-id/content-desc对齐。
1. 使用Appium Inspector查看实际元素属性
2. 更新对应Page Object中的定位器

### Q: 如何查看更详细的错误信息？

**A**: 
```bash
# 查看完全的错误回溯
pytest tests/ -v --tb=long

# 查看日志文件
cat logs/test_*.log
cat logs/error_*.log
```

### Q: 如何在CI/CD中运行？

**A**: 
```bash
# Jenkins / GitLab CI 示例
export TEST_ENV=test
appium --log-level error &
sleep 5
pytest tests/ -v --alluredir=reports/allure-results --reruns 2
allure generate reports/allure-results -o reports/allure-report --clean
```

---

## 许可

内部项目，仅供低空空管自动化系统团队使用。

---

*文档版本: v1.0*
*最后更新: 2026-08-04*
