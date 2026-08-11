# Plan: 支持华为 NOH-AN01 设备运行

## Context

更换了测试设备从 Redmi K80 (24117RK2CC, Android 16) 到华为 NOH-AN01 (Android 12) 后启动失败。

错误日志核心信息：
```
The instrumentation process cannot be initialized.
Make sure the application under test does not crash 
and investigate the logcat output.
```
发生在 `UiAutomator2Server.startSession` 阶段。

**根因分析:**

1. **`config.yaml` 只配置了一台 Redmi K80 设备** (device index 0)，平台版本硬编码为 `16`。华为设备连接时仍使用 Redmi K80 的配置。

2. **虽然有 `_auto_fix_platform_version()` 自动修正版本号**（16→12），但没有自动设备匹配机制——无法区分当前连接的是哪台设备并选择对应配置。

3. **`skipServerInstallation: true` 是关键问题**: 该标志告诉 Appium 跳过 `io.appium.settings` 和 `io.appium.uiautomator2.server` 等辅助 APK 的安装/更新检查。Redmi K80 之前已经运行过 Appium，这些 APK 早已装好，所以没问题。但华为设备是首次运行 Appium，缺少这些必要的 instrumentation APK，导致 `UiAutomator2Server` 初始化失败。

## 修改方案

### 1. `config.yaml` — 添加华为设备配置

在 `devices` 列表末尾添加华为 NOH-AN01 条目（保持原有 Redmi K80 配置不变）：

```yaml
  - name: "NOH-AN01"
    platform: "Android"
    platform_version: "12"
    device_name: "Huawei_NOH"
    udid: ""
    app_package: "com.dolphin.atc"
    app_activity: ".MainActivity"
    automation_name: "UiAutomator2"
    no_reset: true
    full_reset: false
    auto_grant_permissions: true
    new_command_timeout: 120
    # Android 12 首次使用 Appium，需要让其安装辅助 APK
    skip_device_initialization: false
    skip_server_installation: false
```

与 Redmi K80 配置的关键区别：
- `platform_version: "12"` 而非 `"16"`
- `skip_device_initialization: false`
- `skip_server_installation: false` — **最关键**，允许 Appium 在华为设备上首次安装必要的 instrumentation APK

### 2. `appium_driver.py` — 增强自动设备匹配

在 `AppiumDriverManager.get_driver()` 中添加自动设备匹配逻辑：

```
当前流程:
get_driver(device_index=0) → 取 devices[0] → auto_fix_platform_version → build_driver

新流程:
get_driver(device_index=0, auto_match=True) → 
  检测当前连接设备 → 
  按 model 名称匹配 devices 列表中的配置项 →
  匹配到则使用该配置 → 
  auto_fix_platform_version → 
  build_driver
```

具体实现：
- 新增 `_auto_match_device()` 方法：通过 ADB 获取当前连接设备的 model 属性，与 `config.yaml` 中 `devices[].name` 匹配
- 匹配规则：如果配置中的 `name` 字段是当前连接设备 model 的子串（或相等），则使用该配置
- 如果 `udid` 已配置且匹配，优先使用该配置
- 兜底：如果无法匹配，fallback 到 `device_index` 指定的配置

### 3. `config_manager.py` — 增加按设备名查找的方法

新增 `get_device_config_by_model(model: str)` 方法，根据设备型号名称查找匹配的配置：

```python
def get_device_config_by_model(self, model: str) -> Optional[Dict[str, Any]]:
    """根据设备型号名称查找匹配的设备配置"""
    devices = self._config.get("devices", [])
    for device in devices:
        name = device.get("name", "")
        if name and (name in model or model in name):
            return device.copy()
    return None
```

### 4. `manual_test.py` — 无需修改

`manual_test.py` 通过 `AppiumDriverManager` 创建 driver，自动设备匹配逻辑在 Driver 层完成，入口脚本无需改动。

### 5. `conftest.py` — 无需修改

同样通过 `AppiumDriverManager` 创建 driver，自动匹配逻辑透明。

## 文件变更清单

| 文件 | 变更 | 说明 |
|------|------|------|
| `config/config.yaml` | 新增设备条目 | 添加 NOH-AN01 (Android 12) 配置 |
| `drivers/appium_driver.py` | 新增方法 | `_auto_match_device()` + `get_driver()` 增强 |
| `config/config_manager.py` | 新增方法 | `get_device_config_by_model()` |

## 验证方法

1. 确保华为设备已连接: `adb devices` 显示 `7TD5T21420012429 device`
2. 确保 Appium Server 已启动: `appium`
3. 运行: `python -i manual_test.py`
4. 预期输出:
   ```
   [OK] 配置已加载 (环境: test)
   [OK] ADB已就绪 (在线设备: 1)
        - NOH-AN01 | Android 12 | device
   [INFO] 自动匹配设备配置: NOH-AN01 (index 1)
   [OK] Appium Session已建立
   ```
5. 换回 Redmi K80 时，自动匹配 index 0 配置，仍能正常工作
6. 运行 pytest: `pytest tests/ --device-index=0` (Redmi) / `pytest tests/ --device-index=1` (Huawei)，或依赖自动匹配

## 关键决策说明

- **不修改 Redmi K80 配置**：保持 `skip_server_installation: true` 等设置不变，确保原设备继续正常工作
- **自动匹配而非要求用户手动指定**：降低使用门槛，插上哪台就测哪台
- **通过 model 名称匹配**：比 UDID 匹配更通用（UDID 每次重新连接可能变化）
