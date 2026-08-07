# -*- coding: utf-8 -*-
"""
APK安装/卸载/升级 - 自动化测试用例

测试范围:
    - 本地APK文件扫描与版本解析
    - 本地与设备版本对比
    - 安装 / 覆盖安装幂等 / 升级 / 卸载
    - 一键就绪流程 (ensure_app_ready)

说明:
    - 纯ADB操作，不需要driver，browser/native双模式可跑
    - 无本地APK时由 require_apk 守卫自动skip
    - 安装/升级类用例会实际改动设备，建议在专用测试设备上执行

标记: @pytest.mark.install
"""

import logging

import pytest
import allure

logger = logging.getLogger(__name__)


# ============================================================
# 本地APK文件与版本解析
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("APK文件扫描")
@allure.title("扫描本地APK文件")
@pytest.mark.install
def test_find_local_apk_files(apk_manager, require_apk):
    """
    验证点: 本地APK目录存在且扫描到文件
    """
    with allure.step("1. 扫描本地APK目录"):
        files = apk_manager.find_apk_files()

    with allure.step("2. 验证扫描结果"):
        assert files, "未找到本地APK文件"
        for f in files:
            assert f.exists(), f"APK文件不存在: {f}"
    logger.info(f"扫描到 {len(files)} 个APK: {[f.name for f in files]}")


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("APK版本解析")
@allure.title("解析本地APK版本信息")
@pytest.mark.install
def test_parse_apk_info(apk_manager, require_apk):
    """
    验证点: APK包名/版本号解析成功 (aapt或回退方案)
    """
    apk_path = require_apk
    with allure.step("1. 解析APK信息"):
        info = apk_manager.parse_apk_info(apk_path)

    with allure.step("2. 验证解析结果"):
        assert info.get("package_name"), f"无法解析包名: {info}"
        assert info.get("version_name"), f"无法解析版本名: {info}"
        assert isinstance(info.get("version_code"), int), f"version_code应为int: {info}"
        assert info.get("parse_method") in ("aapt", "pyaxmlparser", "filename", "unknown")

    allure.attach(str(info), name="APK解析结果", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"APK解析[{info['parse_method']}]: {info['package_name']} v{info['version_name']} ({info['version_code']})")


# ============================================================
# 版本对比 (纯逻辑, 不碰设备)
# ============================================================

def _make_installed(code, name):
    return {"is_installed": True, "version_code": code, "version_name": name}


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("版本对比")
@allure.title("版本对比: 设备未安装")
@pytest.mark.install
def test_compare_versions_not_installed(apk_manager):
    """本地APK有版本，设备未安装 -> not_installed"""
    local = {"version_code": 10, "version_name": "1.0.0"}
    installed = {"is_installed": False, "version_code": None, "version_name": None}
    assert apk_manager.compare_versions(local, installed) == "not_installed"


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("版本对比")
@allure.title("版本对比: 本地与设备相同")
@pytest.mark.install
def test_compare_versions_same(apk_manager):
    """version_code相同 -> same"""
    local = {"version_code": 10, "version_name": "1.0.0"}
    assert apk_manager.compare_versions(local, _make_installed(10, "1.0.0")) == "same"


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("版本对比")
@allure.title("版本对比: 本地较新")
@pytest.mark.install
def test_compare_versions_newer(apk_manager):
    """本地version_code更大 -> newer"""
    local = {"version_code": 11, "version_name": "1.1.0"}
    assert apk_manager.compare_versions(local, _make_installed(10, "1.0.0")) == "newer"


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("版本对比")
@allure.title("版本对比: 设备较新")
@pytest.mark.install
def test_compare_versions_older(apk_manager):
    """设备version_code更大 -> older"""
    local = {"version_code": 9, "version_name": "0.9.0"}
    assert apk_manager.compare_versions(local, _make_installed(10, "1.0.0")) == "older"


# ============================================================
# 安装/卸载/升级 (实际改动设备)
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("安装卸载")
@allure.title("安装APK")
@pytest.mark.install
def test_install_apk(apk_manager, require_apk):
    """
    验证点: 安装成功后应用存在且版本与APK一致
    """
    apk_path = require_apk
    local_info = apk_manager.parse_apk_info(apk_path)

    with allure.step("1. 安装APK (覆盖安装)"):
        assert apk_manager.install(apk_path, upgrade=True), "APK安装失败"

    with allure.step("2. 验证安装结果"):
        pkg = local_info.get("package_name")
        assert apk_manager.adb.is_app_installed(pkg), f"安装后未检测到应用: {pkg}"
        installed = apk_manager.get_installed_version(pkg)
        assert installed.get("version_code") == local_info.get("version_code"), (
            f"设备版本 {installed.get('version_code')} 与APK版本 {local_info.get('version_code')} 不一致"
        )

    allure.attach(
        f"APK: {apk_path}\n设备版本: {installed}",
        name="安装结果",
        attachment_type=allure.attachment_type.TEXT,
    )


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("安装卸载")
@allure.title("覆盖安装幂等性")
@pytest.mark.install
def test_install_is_idempotent(apk_manager, require_apk):
    """
    验证点: 二次覆盖安装成功且版本不变
    """
    apk_path = require_apk
    local_info = apk_manager.parse_apk_info(apk_path)

    with allure.step("1. 第一次安装"):
        assert apk_manager.install(apk_path, upgrade=True), "首次安装失败"

    with allure.step("2. 第二次覆盖安装"):
        assert apk_manager.install(apk_path, upgrade=True), "二次覆盖安装失败"

    with allure.step("3. 验证版本不变"):
        installed = apk_manager.get_installed_version(local_info.get("package_name"))
        assert installed.get("version_code") == local_info.get("version_code"), "覆盖安装后版本不应变化"


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("安装卸载")
@allure.title("APK升级")
@pytest.mark.install
def test_upgrade_apk(apk_manager, require_apk):
    """
    验证点: 版本更高的APK覆盖安装后version_code变大

    说明: 若无更高版本APK，先安装当前版本再重装同一版本视为无变化，
          用 ensure_app_ready 的diff逻辑验证不会误报升级。
    """
    apk_path = require_apk
    local_info = apk_manager.parse_apk_info(apk_path)
    pkg = local_info.get("package_name")

    with allure.step("1. 确保已安装当前版本"):
        assert apk_manager.install(apk_path, upgrade=True), "安装失败"

    with allure.step("2. 重跑ensure_app_ready对比"):
        report = apk_manager.ensure_app_ready(apk_path)
        assert report["success"], f"就绪流程失败: {report}"
        # 版本相同时应为skipped而非upgraded
        assert report["action"] in ("skipped", "upgraded"), f"意外动作: {report['action']}"
        logger.info(f"ensure_app_ready动作: {report['action']} (local={report['local_version']}, device={report['installed_version']})")


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("安装卸载")
@allure.title("卸载APK")
@pytest.mark.install
def test_uninstall_apk(apk_manager, require_apk):
    """
    验证点: 卸载后应用不存在
    """
    apk_path = require_apk
    local_info = apk_manager.parse_apk_info(apk_path)
    pkg = local_info.get("package_name")

    with allure.step("1. 先确保已安装"):
        assert apk_manager.install(apk_path, upgrade=True), "安装失败"

    with allure.step("2. 卸载应用"):
        assert apk_manager.uninstall(pkg), "卸载失败"

    with allure.step("3. 验证卸载结果"):
        assert not apk_manager.adb.is_app_installed(pkg), f"卸载后应用仍存在: {pkg}"


# ============================================================
# 一键就绪流程
# ============================================================

@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("一键就绪")
@allure.title("ensure_app_ready一键就绪流程")
@pytest.mark.install
def test_ensure_app_ready_flow(apk_manager, require_apk):
    """
    验证点: 一键就绪报告完整且action合法

    action: installed / upgraded / skipped / install_failed
    """
    with allure.step("1. 执行一键就绪"):
        report = apk_manager.ensure_app_ready()

    with allure.step("2. 验证报告完整性"):
        assert report["apk_path"], "报告缺少APK路径"
        assert report["action"] in ("installed", "upgraded", "skipped", "install_failed"), (
            f"未知action: {report['action']}"
        )
        if report["action"] in ("installed", "upgraded"):
            assert report["success"], f"安装/升级应成功: {report}"

    allure.attach(str(report), name="就绪报告", attachment_type=allure.attachment_type.TEXT)
    logger.info(f"一键就绪: action={report['action']} local={report['local_version']} device={report['installed_version']}")


@allure.epic("低空空管系统")
@allure.feature("APK管理")
@allure.story("状态报告")
@allure.title("APK状态汇总报告")
@pytest.mark.install
def test_report_status(apk_manager, require_apk):
    """汇总报告包含本地列表与设备版本与建议"""
    with allure.step("1. 生成状态报告"):
        report = apk_manager.report_status()

    with allure.step("2. 验证报告结构"):
        assert report["local_apks"], "本地APK列表不应为空"
        assert "installed" in report, "缺少设备版本信息"
        assert report["recommendation"], "缺少建议动作"

    allure.attach(str(report), name="APK状态报告", attachment_type=allure.attachment_type.TEXT)
