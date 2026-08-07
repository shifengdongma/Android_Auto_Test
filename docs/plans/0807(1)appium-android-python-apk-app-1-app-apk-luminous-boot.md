# Android 测试框架扩展计划:APK 管理 / App 生命周期 / 性能 / 异常测试

## Context(背景)

当前框架(Appium2 3.6.0 + Pytest + Allure + POM,位于 `mobile-test-framework/`)是原型框架:以 browser 模式测 H5 原型,无正式 APK。用户后续将进行正式原生 APK 的安装、手动测试与自动化测试,需求 6 项:

1. APK 安装/卸载/更新 + 自动版本检测
2. App 开启/关闭/后台运行
3. 登录注册页面操作(登录已有,注册按用户决策**预留框架能力**)
4. 截图 + 测试操作日志抓取
5. 性能:启动时间 / CPU / 内存 / 电量 / 页面响应时间(按用户决策**采集+可调阈值,warn_only 不失败,先建基线**)
6. 异常:弱网络(按用户决策**开关级断网 + 代理限速接口预留**)、性能阻塞(ANR)、高资源占用(monkey)

目标:扩展框架使其在正式 APK 就绪后开箱即用,同时**不破坏现有 browser 模式**(零回归)。

## 可行性分析(逐条回答:能否在 Python+Appium 中实现)

| 需求 | 可行性 | 实现路径 |
|---|---|---|
| (1) APK 安装卸载更新 | ✅ 低风险 | 安装 `adb install -r -d`、卸载、`pm list packages`、`dumpsys package` 已有(ADBHelper);新增"本地 APK 文件版本解析":aapt dump badging(本机已确认 `%LOCALAPPDATA%\Android\Sdk\build-tools\36.0.0\aapt.exe` 存在,多路径探测)→ pyaxmlparser 纯 Python 回退 → 文件名启发式兜底;`compare_versions` 按 version_code 对比决定 installed/upgraded/skipped |
| (2) App 开启/关闭/后台 | ✅ 可行 | `am start -W` 解析 ThisTime/TotalTime + Android 12+ `LaunchState`(COLD/WARM)自动区分冷/热启动;关闭 `am force-stop`;后台 `input keyevent 3`(HOME);回前台优先 `driver.activate_app`(绕 MIUI 后台弹窗限制),回退 `am start -n` |
| (3) 登录注册 | ✅ 可行 | 登录已完整(LoginPage+9 用例);注册:RegisterPage 模板 + `data/register_data.yaml` + `test_data` fixture(首次消费),定位器带"待校准"注释,APK 就绪后仅改常量即自动激活 |
| (4) 截图 + 日志 | ✅ 可行 | 截图已有(失败 hook + ScreenshotManager);新增 LogcatCapture(按包名过滤抓取、Allure attach ≤50KB)与失败 hook 追加 logcat 尾部 |
| (5) 性能 | ✅ 可行(3 注意点) | `am start -W` 直读启动耗时;CPU 用 `top -b -n 1`(按表头定位 %CPU 列,兼容 toybox)/`dumpsys cpuinfo`;内存解析 Android 8+ `TOTAL PSS:` 行;电量 `dumpsys battery`(只读;若曾 `set level` 必须先 `reset`;uiautomator2 driver 无电量 API,必须走 adb);响应时间用 `pc.timer()` 上下文计时;CSV(utf-8-sig)+ Allure;阈值 warn_only |
| (6) 异常 | ✅ 可行(弱网限速需代理) | 开关级断网/飞行模式(ADB 已有,封装 NetworkController;小米 HyperOS `svc wifi disable` 失效时回退 `cmd wifi set-wifi-enabled disabled`);**真机弱网限速必须 PC 侧代理**(手机 WiFi 代理指向 PC),以 `ThrottleController` 抽象接口预留 + 文档接入步骤;ANR 检测 logcat 抓 `ANR in <pkg>`/`Input dispatching timed out`/`am_anr`;monkey `adb shell monkey` 参数化封装,解析 CRASH/ANR/aborted |

**限制**:monkey 破坏性测试须 `--kill-process-after-error` + 适度 events,不叠加 reruns(`@pytest.mark.flaky(reruns=0)`);logcat 环形缓冲有限,长测试需周期性 tail 落盘;CPU 瞬时采样抖动大,多取中位数。

## 设计决策

- **分层**:adb 原始命令进 `ADBHelper`(新增 7 方法);解析/归一/CSV/Allure/阈值进各 Manager(utils/ 新模块);测试只调 Manager
- **双模式兼容**:所有新工具以 ADB 为核心、不依赖 driver,browser 模式全可用(对 Chrome 包测机制、断网测 H5);仅 `require_native_mode`/`require_apk` 守卫的用例自动 skip——**不改 driver fixture 创建/teardown 逻辑**
- 容错底线:任何 adb 失败只 WARN 返回空值不抛异常;守卫用 skip 不用 fail,保证 APK 未就绪时全仓库测试依然绿
- 风格一致:中文注释、模块 docstring 含示例、`try/except` 容错、Allure 装饰器、配置走 `ConfigManager.get("点号路径")` 带默认值、`logger = logging.getLogger(__name__)`

## 新增文件(均在 `mobile-test-framework/` 下)

### 1. `utils/apk_manager.py` — APKManager
- `parse_apk_info(apk_path) -> Dict`:aapt dump badging(正则提取 package/versionCode/versionName/launchable-activity)→ pyaxmlparser(lazy import)→ 文件名启发式 `(v?)(\d+\.\d+(?:\.\d+)?)[_-](\d+)?`;返回含 `parse_method`
- `_find_aapt()`:探测顺序 config.apk.aapt_path > ANDROID_HOME > ANDROID_SDK_ROOT > %LOCALAPPDATA%\Android\Sdk > PATH
- `find_apk_files(dir=None)` / `get_latest_apk()`(多 APK 按 version_code 取最大)
- `get_installed_version(pkg=None)`(复用 `adb.get_app_info`)/ `compare_versions(local, installed)` → newer/same/older/not_installed
- `install(apk_path, upgrade=True)` / `uninstall(pkg=None)`
- `ensure_app_ready(apk_path=None)` → 一键就绪报告 `{"apk_path","local_version","installed_version","action":installed|upgraded|skipped|missing_apk,"success"}`
- `report_status()` 汇总(供 Allure attach / manual_test 打印)

### 2. `utils/app_lifecycle.py` — AppLifecycleManager
- `launch(package=None, activity=None, measure=True) -> Dict`:调 `adb.start_app_measured`,返回 total_time_ms/this_time_ms/wait_time_ms/launch_state
- `close(package=None)`:force-stop 优先,driver 可用时 terminate_app
- `background(package=None)`:`adb.press_key(3)` HOME,验证前台 != pkg(切后台后 0.5~1s 缓冲)
- `resume(package=None, activity=None)`:优先 `driver.activate_app`,回退 `adb.start_app`,验证前台 == pkg
- `cold_start_time(rounds=3)` / `warm_start_time(rounds=3)`:统计 values/avg/median/min/max
- `is_foreground(package=None)`(复用 `get_current_app_package`)/ `state_report()` 摘要

### 3. `utils/performance.py` — PerformanceCollector
- `get_pid(package)`(`pidof -s`)/ `snapshot_cpu(package)`(top 表头定位 %CPU 列,回退 dumpsys cpuinfo)/ `snapshot_memory(package)`(`TOTAL PSS:` 正则,回退旧 `TOTAL:`)/ `snapshot_battery()`(level/status/temperature)/ `snapshot_all(package)`(三合一+阈值打标)
- `measure_startup(cold=True, rounds=3)`:委托 AppLifecycleManager + 阈值校验
- `timer(name)`:上下文管理器,计页面操作响应时间,校验 `operation_response_ms`
- `start_sampling(package, interval, duration)`(daemon 线程定时采样)/ `stop_sampling()`(均值/峰值 + Allure attach)
- `check_threshold(metric, value) -> str`(ok/warn/fail;policy=warn_only 默认不失败;`--perf-strict` 覆盖为 strict)/ `assert_within_threshold(metric, value, hard=False)`
- `write_csv(rows)`(列:timestamp,test_name,metric,value,unit,threshold,result,package,device_id,extra;utf-8-sig,行锁)/ `save_report()` / `attach_to_allure()`

### 4. `utils/logcat.py` — LogcatCapture + LogcatAnalyzer
- `LogcatCapture.start(pkg=None)`(先 clear_logcat 再 Popen,复用 `adb.start_logcat`;抓全量,停止时 pidof 过滤保真)/ `stop()` / `tail(lines=200, pkg=None)`(`logcat -d -v threadtime`)/ `attach(name, max_bytes=50KB)`
- `LogcatAnalyzer(package)`:ANR_PATTERNS(`ANR in <pkg>`/Input dispatching timed out/am_anr/Application Not Responding)、CRASH_PATTERNS(FATAL EXCEPTION/Process: <pkg>)、KILL_PATTERNS(lowmemorykiller/Killing);`scan(text)` → 命中列表;`assert_clean(text)` 有命中则 attach ±3 行上下文 + pytest.fail

### 5. `utils/network_controller.py` — NetworkController + ThrottleController 协议
- `set_mode(mode)`(normal/offline/airplane/wifi_only/mobile_only)/ `disconnect_all()` / `restore_all()` / `is_offline()`(ping 8.8.8.8)/ `check_connectivity()` → `{"offline","wifi","mobile_data","airplane","detail"}`
- `get_throttle_controller()`:按 `config.network.throttle.backend` 返回实现;默认 `NullThrottleController`(available()→False,WARN 说明需 mitmproxy/Charles)
- `ThrottleController(ABC)`:name/available()/apply(down_kbps, up_kbps, latency_ms)/remove() — **接口预留,实现方式写入 docs/弱网测试方案.md**

### 6. `pages/register_page.py` — RegisterPage(BasePage)预留
- 定位器常量全部 `# 待校准`(REGISTER_ENTRY/USERNAME/PASSWORD/CONFIRM/EMAIL/VERIFY_CODE/SEND_CODE/SUBMIT/ERROR_MESSAGE/PAGE_TITLE),结构仿 LoginPage 的 ALT_ 回退模式
- 方法(链式):enter_username/enter_password(日志打码)/enter_confirm_password/enter_email/enter_verify_code/click_send_code/click_submit/`register(...)` 组合流程/`is_on_register_page()`/`get_error_message()`(Toast→弹窗→页面文本三级)/`wait_for_register_page()`

### 7. `data/register_data.yaml`
- `register_success_cases`(正常注册)、`register_validation_cases`(空用户名/密码过短/两次密码不一致,各带 expected_error)

### 8. `scripts/monkey_stress.py`(可选)
- monkey 参数化 CLI:`--pkg --events --seed --throttle --with-perf`;运行中采样性能 + logcat 扫 ANR/崩溃,输出摘要+CSV(约 120 行)

## 修改文件

### 1. `utils/adb_helper.py` — 新增 7 方法(adb 原始层)
- `start_app_measured(package_name, activity, device_id=None) -> Dict`:`am start -W -n`,解析 ThisTime/TotalTime/WaitTime/LaunchState(Android 12+,找不到为 UNKNOWN)
- `get_pid(package_name) -> Optional[int]` / `is_process_alive(package_name) -> bool`:`pidof -s`
- `top_snapshot(pid=None)` / `cpuinfo_snapshot(package_name)` / `meminfo_snapshot(package_name)`(timeout 30)/ `battery_snapshot()`
- `run_monkey(package_name, events=500, seed=None, throttle_ms=300, kill_after_error=True, timeout=600) -> Dict`:解析 "Monkey finished"→success/"// CRASH"→crashed/"// ANR"→anr/"Monkey aborted"→aborted

### 2. `config/config.yaml` — 追加 4 个配置段(devices 段与 test_mode 不动)
```yaml
apk:
  dir: "apk"                        # 本地APK目录,不存在自动建
  package_name: "com.dolphin.atc"
  aapt_path: ""                     # 留空自动探测
performance:
  enabled: true
  threshold_policy: "warn_only"     # warn_only / strict
  csv_dir: "reports/performance"
  sample_interval: 2
  thresholds: {cold_start_ms: 5000, warm_start_ms: 2000, operation_response_ms: 3000,
               memory_mb: 500, cpu_percent: 80, battery_drop_percent: 5}
network:
  weaknet_mode: "offline"           # offline/airplane/wifi_only/mobile_only/throttle
  throttle: {backend: "none", down_kbps: 100, up_kbps: 50, latency_ms: 500,
             proxy_host: "127.0.0.1", proxy_port: 8899}
stability:
  monkey_events: 500
  monkey_seed: 42
  monkey_throttle_ms: 300
  anr_check_after_each_test: false
```

### 3. `tests/conftest.py`
- 新 fixture(全部 lazy import 于 fixture 体,同 screenshot_manager 风格):
  - session 级:`adb`(ADBHelper 单例)、`apk_manager`、`app_lifecycle`(driver=None 即 adb 模式,用例内可 set_driver)、`performance_collector`、`network_controller`、`require_native_mode`(browser 下 skip)、`require_apk`(无 APK 时 skip,返回最新 APK)
  - function 级:`weak_network`(teardown 强制 restore_all,防网络状态污染)
- `pytest_addoption` 新增:`--perf-baseline`(只采集不告警)、`--perf-strict`(超阈值判失败)、`--apk-path`(覆盖 apk.dir)
- 失败 hook 扩展:截图 attach 后追加 logcat 尾部 attach(`logcat -d -v threadtime` 末 100 行 grep 包名,截断 50KB,整体 try/except)
- `pytest_configure` environment.properties 追加:TestMode/DeviceModel/PerfPolicy

### 4. `pytest.ini` — 新增 markers
`install: APK安装/卸载/升级测试`、`lifecycle: App生命周期测试`、`perf: 性能采集与基线测试`、`weaknet: 弱网/断网测试`、`stability: 稳定性测试`、`monkey: monkey压力测试(长耗时)`、`register: 注册模块测试(预留)`

### 5. `requirements.txt` — 追加
`pyaxmlparser>=0.3.30`(aapt 不可用时的纯 Python 回退;不引入 androguard 重型依赖)

### 6. `manual_test.py` / `run_tests.py`
- manual_test 新增:apk_info/list_apks/check_apk_version/install_or_update_apk/bg_app/fg_app/cold_start/perf_snapshot/monkey_run/logcat_tail(初始化顺序不动,末尾加函数)
- run_tests `--module` choices 增加 install/lifecycle/performance/network/stability/register/monkey;透传 `--perf-baseline/--perf-strict`

### 7. 文档与杂项
- `README.md`:新模块结构、新 marker、APK 工作流(放 APK → 自动安装/升级 → 切 native 模式)、性能基线说明
- `docs/APK管理使用说明.md`(aapt 探测与回退链、ensure_app_ready 流程)
- `docs/性能测试基线建立.md`(跑 3 次 `--module performance --perf-baseline` 取中位 → 回填 thresholds)
- `docs/弱网测试方案.md`(开关级断网 + mitmproxy/Charles 接入步骤、ThrottleController 实现指引、设备代理配置)
- `.gitignore`:`apk/*.apk`、`reports/performance/`、`logs/logcat/`

## 新增测试用例

| 文件 | 用例(要点) |
|---|---|
| `tests/test_app_install.py`(@install) | find_local_apk_files / parse_apk_info / compare_versions 四分支(纯逻辑) / install_apk(装后 is_app_installed 且版本一致) / install_is_idempotent / upgrade_apk(version_code 变大) / uninstall_apk / ensure_app_ready_flow;`require_apk` 守卫,无 APK 全 skip;不需要 driver,纯 ADB |
| `tests/test_app_lifecycle.py`(@lifecycle) | cold_start_app(total_time>0 且进程存活) / launch_state_detected(不硬断言 COLD) / close_app(pidof 为空) / background_and_resume(前台包切换验证) / warm_start_time / cold_start_time(统计齐全+warn_only 校验) |
| `tests/test_performance.py`(@perf) | cpu_snapshot / memory_snapshot / battery_snapshot(level 0~100)/ startup_cold_with_threshold / page_operation_response(`pc.timer` 包 logged_in_driver 场景) / sampling_during_scenario(样本≥3+CSV 生成) / threshold_policy_warn_only / csv_encoding_utf8_sig(BOM 校验);APK 就绪前可用 `com.android.chrome` 跑通机制 |
| `tests/test_network.py`(@weaknet+offline) | disconnect_all_blocks_network / login_fails_when_offline(错误态不崩溃) / restore_network_recovers / airplane_mode / throttle_interface_reserved(**永远通过**,接口预留落点);`weak_network` fixture 自动恢复 |
| `tests/test_stability.py`(@stability/@monkey,`flaky(reruns=0)`) | monkey_smoke(events=200, 无 CRASH/ANR) / monkey_with_perf_sampling(events=500+采样 CSV, slow) / anr_detector_scan / logcat_capture_and_attach(文件含包名日志) / monkey_abort_on_wrong_package(容错路径) |
| `tests/test_register.py`(@register) | register_page_displayed(定位器探测不到→skip) / register_success(数据驱动,首次消费 test_data) / register_validation(expected_error 校验);APK 就绪校准定位器后自动激活 |

## 实施阶段与验证(5 阶段,每阶段独立可验证)

1. **基础工具层**:ADBHelper 7 方法 + apk_manager + logcat + network_controller + config apk/network 段
   验证:`python -i manual_test.py` 手动验证 `adb.start_app_measured("com.android.chrome", ...)`、`apk_info()`、`logcat_tail()`;无 APK 时 install 用例 skip 属预期
2. **性能**:performance.py + conftest 新 fixture/参数 + config performance 段
   验证:真机跑 `pytest tests/test_performance.py -m perf --perf-baseline`,检查 reports/performance/*.csv 与 Allure 附件;连跑 3 次取中位回填 thresholds
3. **生命周期与稳定性**:app_lifecycle.py + pytest.ini markers + 失败 hook 加 logcat attach
   验证:`pytest tests/test_app_lifecycle.py -m lifecycle`(browser 用 chrome 包跑机制);`adb.run_monkey("com.android.chrome", 200)` 手动
4. **测试用例层**:6 个测试文件 + register_data.yaml
   验证:分模块跑通;`python run_tests.py --module performance --perf-baseline`、`--module stability`
5. **集成与文档**:run_tests.py 扩展、manual_test.py 新函数、README/docs 三篇、.gitignore
   验证:全量回归(旧 43 用例 + 新用例,`python run_tests.py --smoke` 确认 browser 模式零回归)、docs 命令逐条可执行

## 关键注意事项

- **不破坏现有 browser 模式**:config.yaml devices 段与 test_mode 不动;新配置全部追加;manual_test 初始化顺序不动;run_tests 只扩 choices
- 真机/模拟器兼容:device_id 经 `get_device_config(device_index)["udid"]`,空则自动取首台在线设备(沿用 `_run_adb` 的 `-s` 语义);meminfo/top 双格式兼容
- Android 16:LaunchState 可选解析、TOTAL PSS 新格式、battery 只读(如有 set 测试态先 reset)、skip 设置沿用现有
- perf/monkey 用例加 `@pytest.mark.flaky(reruns=0)` 防重跑污染数据;CSV 用 utf-8-sig(Excel 可开);Allure attach 全部限 50KB
- 阈值默认值仅是起点(冷启动 5000ms/热 2000ms/响应 3000ms/内存 500MB/CPU 80%/电量 5%),首次基线后按真机实际校准

## 关键文件

- `mobile-test-framework/utils/adb_helper.py`(扩展地基,7 新方法)
- `mobile-test-framework/utils/apk_manager.py`(新建)
- `mobile-test-framework/utils/performance.py`(新建)
- `mobile-test-framework/utils/app_lifecycle.py`(新建)
- `mobile-test-framework/utils/logcat.py`(新建)
- `mobile-test-framework/utils/network_controller.py`(新建)
- `mobile-test-framework/pages/register_page.py`(新建,预留)
- `mobile-test-framework/config/config.yaml`、`tests/conftest.py`、`pytest.ini`、`requirements.txt`、`manual_test.py`、`run_tests.py`(修改)
- `mobile-test-framework/tests/test_app_install.py` 等 6 个新测试文件
