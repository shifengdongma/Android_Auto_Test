# APK 管理使用说明

> 版本: v1.0 | 日期: 2026-08-07 | 适用框架: mobile-test-framework

## 一、功能概述

框架提供完整的 APK 生命周期管理能力,覆盖:

| 能力 | 说明 | 实现 |
|---|---|---|
| 本地APK扫描 | 扫描 `apk/` 目录,多APK时按版本自动选最新 | `APKManager.find_apk_files/get_latest_apk` |
| 版本解析 | 解析本地APK的包名/版本号/启动Activity | `APKManager.parse_apk_info` |
| 设备版本检测 | 读取设备已装版本 | `APKManager.get_installed_version` |
| 版本对比 | 本地 vs 设备,自动判断需安装/升级/跳过 | `APKManager.compare_versions` |
| 安装/升级 | 覆盖安装(`-r -d`,保留数据)或干净安装 | `APKManager.install` |
| 卸载 | 卸载并确认 | `APKManager.uninstall` |
| 一键就绪 | 自动完成 扫描→解析→对比→安装/升级 | `APKManager.ensure_app_ready` |

## 二、APK 放置与目录约定

```
mobile-test-framework/
└── apk/                    ← 本地APK目录 (config.apk.dir, 不存在自动创建)
    ├── app_v1.0.0.apk
    └── app_v1.1.0.apk
```

- 目录不存在时框架自动创建
- APK 文件已被 `.gitignore` 排除(`apk/*.apk`),不提交到版本库
- 支持同时放置多个版本,自动按 `version_code` 取最新
- 可用 `--apk-path` 命令行参数指定具体APK,覆盖自动扫描

## 三、版本解析方案(优先级)

```
1. aapt dump badging      ← 信息最全 (含启动Activity), 推荐
2. pyaxmlparser           ← 纯Python回退 (无build-tools环境可用)
3. 文件名启发式            ← 兜底 (如 app_v1.2.3_4.apk)
```

**aapt 探测路径顺序:**

1. `config.yaml` 中 `apk.aapt_path` 显式配置
2. `ANDROID_HOME/build-tools/*/aapt.exe`
3. `ANDROID_SDK_ROOT/build-tools/*/aapt.exe`
4. `%LOCALAPPDATA%\Android\Sdk\build-tools/*/aapt.exe`
5. 系统 PATH 中的 `aapt` / `aapt.bat`

探测到 aapt 时,`parse_apk_info` 还会返回 `launchable-activity`
(即 main_activity),可用于未安装时校准 `config.yaml` 的 `app_activity`。

> 依赖: `pyaxmlparser>=0.3.30` (requirements.txt 已加入,`pip install -r requirements.txt` 安装)

## 四、配置项

```yaml
apk:
  dir: "apk"                        # 本地APK目录(相对mobile-test-framework/), 不存在自动创建
  package_name: "com.dolphin.atc"   # 缺省包名(与 devices[].app_package 一致)
  aapt_path: ""                     # aapt路径, 留空自动探测
```

## 五、使用方式

### 1. 自动化测试

```bash
# 运行安装/卸载/升级测试 (需先将APK放入 apk/ 目录)
python run_tests.py --module install

# 无APK时全部自动跳过 (require_apk 守卫)
```

对应测试文件:`tests/test_app_install.py`(10个用例,纯ADB不依赖driver)

### 2. 手动测试控制台

```bash
python -i manual_test.py
```

```python
list_apks()              # 列出本地APK及版本
apk_info("apk/app.apk")  # 解析单个APK信息
check_apk_version()      # 本地 vs 设备版本对比 + 建议
install_or_update_apk()  # 一键安装/升级
```

### 3. 代码调用

```python
from utils.apk_manager import APKManager

mgr = APKManager()
report = mgr.ensure_app_ready()
# report = {"apk_path": ..., "local_version": ..., "installed_version": ...,
#           "action": "installed|upgraded|skipped|missing_apk", "success": bool}
```

## 六、ensure_app_ready 流程

```
扫描 apk/ 目录取最新APK
    ↓
parse_apk_info 解析本地版本 (aapt优先)
    ↓
get_installed_version 读取设备版本
    ↓
compare_versions 对比
    ├── not_installed → install (-r -d 覆盖安装)
    ├── newer        → install (升级, 保留数据)
    └── same/older   → skipped (无需操作)
    ↓
返回 {"action", "local_version", "installed_version", "success"}
```

## 七、注意事项

1. **安装耗时**:大APK安装可能超时,现有 timeout=120s 足够
2. **签名冲突**:`-r -d` 覆盖安装对签名不同的APK会失败(targetSdk 30+),
   需先卸载再装;代码 `install(upgrade=False)` 支持干净安装
3. **小米未知来源弹窗**:USB 安装经 adb 不受影响
4. **测试设备建议**:安装/卸载/升级用例会实际改动设备,
   建议在专用测试设备上执行,避免影响日常使用
5. **容错**:APK目录不存在/解析失败均返回空值并WARN,不抛异常
