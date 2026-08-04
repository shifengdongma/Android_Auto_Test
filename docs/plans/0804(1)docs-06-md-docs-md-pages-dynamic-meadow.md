# Android自动化测试框架 — 实施计划

## Context

为"低空空管自动化系统"移动端Android APP建设企业级自动化测试框架。该APP第一迭代包含登录、首页(消息通知+AI问答)、申报(地图+GPS+飞行计划)、资讯、我的五大模块。采用 Python + Appium2 + Pytest + Allure + Page Object Model 技术栈。

当前项目状态：
- 已有 `pages/` 目录下13个HTML页面原型，模拟了完整的移动端交互
- 已有 `platform-tools/` 包含 adb.exe 等Android调试工具
- 已有 `docs/` 包含测试方案和需求文档
- 无现有测试代码，需从零搭建

## 项目目录结构

```
D:\liyang\code\Android_Auto_Test\mobile-test-framework\
├── config/                         # 配置管理
│   ├── __init__.py
│   ├── config_manager.py           # YAML配置加载器
│   └── config.yaml                 # 主配置文件
├── drivers/                        # 驱动层
│   ├── __init__.py
│   └── appium_driver.py            # Appium Driver封装
├── pages/                          # Page Object层
│   ├── __init__.py
│   ├── base_page.py                # 基础页面类
│   ├── login_page.py               # 登录页
│   ├── home_page.py                # 首页
│   ├── flight_page.py              # 申报页(飞行计划)
│   ├── news_page.py                # 资讯页
│   └── mine_page.py                # 我的页
├── tests/                          # 测试用例层
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── test_login.py               # 登录测试
│   ├── test_home.py                # 首页测试
│   ├── test_flight.py              # 飞行计划测试
│   ├── test_news.py                # 资讯测试
│   └── test_mine.py                # 我的测试
├── utils/                          # 工具层
│   ├── __init__.py
│   ├── logger.py                   # 日志系统
│   ├── screenshot.py               # 截图机制
│   └── adb_helper.py              # ADB辅助工具
├── data/                           # 测试数据
│   ├── login_data.yaml             # 登录测试数据
│   ├── flight_data.yaml            # 飞行计划测试数据
│   └── test_accounts.yaml          # 测试账号
├── reports/                        # 测试报告(Allure输出)
│   └── .gitkeep
├── requirements.txt                # Python依赖
├── pytest.ini                      # Pytest配置
├── run_tests.py                    # 测试运行入口
└── README.md                       # 项目文档
```

## 实施阶段

### 第一阶段：项目骨架搭建

创建目录结构和基础文件：
- 全部7个目录 + `__init__.py` 文件
- `requirements.txt` — 依赖清单(Appium-Python-Client, pytest, allure-pytest, PyYAML, selenium等)
- `pytest.ini` — Pytest配置(allure、日志、标记)

### 第二阶段：基础能力实现

**2.1 Appium Driver封装** (`drivers/appium_driver.py`)
- `AppiumDriverManager` 类，单例模式
- 支持真机/模拟器自动识别(通过ADB检测)
- 多设备支持(从config读取desired_caps)
- 自动启动/关闭session
- 连接重试机制(最多3次)
- 中文注释说明每个方法

**2.2 配置管理** (`config/config_manager.py` + `config/config.yaml`)
- `ConfigManager` 类，加载YAML配置
- 支持环境切换(dev/test/staging)
- 配置项：deviceName, platformVersion, appPackage, appActivity, server_url, timeout等
- 多设备配置段

**2.3 日志系统** (`utils/logger.py`)
- `TestLogger` 类，基于Python logging
- 双通道输出：控制台 + 文件
- 按日期滚动日志文件
- 分级记录：DEBUG/INFO/WARNING/ERROR
- 自动附加到Allure报告

**2.4 截图机制** (`utils/screenshot.py`)
- `ScreenshotManager` 类
- 失败自动截图(通过pytest hook)
- 截图命名规范：`{test_name}_{timestamp}.png`
- 自动附加到Allure报告

### 第三阶段：Page Object实现

**3.1 BasePage** (`pages/base_page.py`)
核心方法(均含异常处理和显式等待)：
- `find_element(locator)` / `find_elements(locator)`
- `click(locator)` — 含重试
- `input_text(locator, text)` — 含清除
- `swipe(direction)` — 上下左右滑动
- `wait_for_element(locator, timeout)` — 显式等待
- `is_element_present(locator)` — 元素存在判断
- `get_text(locator)` — 获取文本
- `take_screenshot(name)` — 页面截图
- `tap_coordinates(x, y)` — 坐标点击(地图等)

**3.2 LoginPage** (`pages/login_page.py`)
定位元素：
- 账号输入框、密码输入框
- 验证码输入框、验证码图片
- 登录按钮、忘记密码链接
- 微信登录按钮(预留)
方法：`login(username, password, captcha)`, `click_forgot_password()`, `get_error_message()`

**3.3 HomePage** (`pages/home_page.py`)
两种状态：
- 默认态：消息通知列表、Tab切换(审批/告警/协调)、底部输入框
- 对话态：AI对话区域、返回首页按钮、对话历史按钮
方法：`switch_notify_tab(type)`, `input_ai_question(text)`, `back_to_home()`, `open_chat_history()`

**3.4 FlightPage** (`pages/flight_page.py`)
- 地图区域、GPS定位按钮
- "我的计划"入口
- 搜索起降场输入框
- 飞行计划表单(计划名称、执飞时段、航空器选择、操控员选择、空域选择)
方法：`allow_gps()`, `deny_gps()`, `search_airport(keyword)`, `create_flight_plan(data)`, `open_my_plans()`

**3.5 NewsPage** (`pages/news_page.py`)
- 子Tab切换(法律法规/通知公告)
- 文章列表、文章详情
方法：`switch_tab(type)`, `click_article(index)`, `get_article_list()`

**3.6 MinePage** (`pages/mine_page.py`)
- 信誉积分卡片
- 关于我们、退出登录菜单项
方法：`get_credit_score()`, `click_about_us()`, `click_logout()`

### 第四阶段：自动化测试开发

**4.1 conftest.py** (`tests/conftest.py`)
- `driver` fixture — session级别，管理driver生命周期
- `login` fixture — function级别，预登录
- `screenshot_on_failure` — pytest hook，失败自动截图
- Allure报告配置

**4.2 test_login.py**
用例：
| 用例 | 数据 | 预期 |
|------|------|------|
| test_login_success | 有效账号密码 | 进入首页 |
| test_login_wrong_password | 有效账号+错误密码 | 提示密码错误 |
| test_login_empty_input | 空账号/空密码 | 按钮禁用或提示 |
| test_login_wrong_captcha | 正确账号+错误验证码 | 提示验证码错误 |
| test_forgot_password | 邮箱 | 进入找回密码流程 |

**4.3 test_home.py**
| 用例 | 验证点 |
|------|--------|
| test_notification_list_display | 消息列表正常加载 |
| test_switch_notify_tabs | 审批/告警/协调Tab切换 |
| test_ai_question_input | AI输入框可用 |
| test_chat_mode_switch | 默认态↔对话态切换 |

**4.4 test_flight.py**
| 用例 | 验证点 |
|------|--------|
| test_gps_permission_allow | GPS允许后显示位置 |
| test_gps_permission_deny | GPS拒绝后降级搜索模式 |
| test_create_flight_plan | 完整创建流程 |
| test_offline_cache | 断网→填写→恢复→数据在 |

**4.5 test_news.py**
| 用例 | 验证点 |
|------|--------|
| test_law_list | 法律法规列表加载 |
| test_notice_list | 通知公告列表加载 |
| test_article_detail | 文章详情打开 |

**4.6 test_mine.py**
| 用例 | 验证点 |
|------|--------|
| test_credit_score_display | 信誉分显示 |
| test_about_us | 关于我们页面 |
| test_logout | 退出登录→返回登录页 |

### 第五阶段：测试增强

**5.1 参数化测试**
- `@pytest.mark.parametrize` 实现多组数据
- 登录场景：多组账号密码组合
- 飞行计划：不同空域类型

**5.2 数据驱动** (data/*.yaml)
- `login_data.yaml` — 账号、密码、预期结果
- `flight_data.yaml` — 计划名称、航空器、空域等
- 通过 `ConfigManager` 加载

**5.3 Allure报告**
- `@allure.feature` / `@allure.story` / `@allure.step` 装饰器
- 截图附件：`allure.attach(screenshot, ...)`
- 日志附件
- `--alluredir=reports` 输出

### 第六阶段：README文档

内容：
1. 环境要求(Python 3.9+, Node.js, Java JDK)
2. Appium2安装：`npm install -g appium` + `appium driver install uiautomator2`
3. ADB配置和环境变量
4. 设备连接步骤(开启USB调试→adb devices验证)
5. 依赖安装：`pip install -r requirements.txt`
6. 运行测试：`pytest tests/ -v --alluredir=reports`
7. 生成报告：`allure serve reports`
8. 项目结构说明

## 关键技术决策

1. **定位策略**：优先使用 `accessibility_id`(content-desc)，其次 `id`，最后 `xpath`。需要与实际APK的resource-id对齐
2. **等待策略**：统一使用显式等待(WebDriverWait)，避免 `time.sleep()`
3. **Driver管理**：conftest.py session级别fixture，所有测试共享一个driver实例
4. **留iOS扩展接口**：BasePage中方法不依赖Android特有API，config中预留iOS配置段
5. **测试数据隔离**：YAML文件管理，不硬编码

## 验证方式

1. 创建完目录结构后运行 `python -c "import config; import drivers; import pages; import tests; import utils"` 验证模块可导入
2. 连接Android设备后运行 `pytest tests/test_login.py -v` 验证基础框架
3. 运行全量测试 `pytest tests/ -v --alluredir=reports && allure serve reports`
4. 检查 `reports/` 目录生成Allure数据
