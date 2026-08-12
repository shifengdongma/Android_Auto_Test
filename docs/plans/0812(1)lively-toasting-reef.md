# Implementation Plan: Mobile Test Framework Enhancement

## Context

The 低空空管自动化系统 (Low-Altitude Airspace Management System) mobile app prototype defines 5 major modules (Login, Home/Notifications+AI, Declaration/Flight Plans, News, My) across 13 HTML prototype pages. The existing Python + Appium2 + Pytest + Allure test framework already provides 88 test cases across 11 test modules covering all 6 required capability areas. This plan addresses the remaining gaps between the prototype specifications and test coverage, updates documentation, and pushes to GitHub.

## Analysis Result

### Already Covered (✅)
| Capability | Implementation |
|------------|---------------|
| (1) APK install/uninstall/version/update | `utils/apk_manager.py` + `tests/test_app_install.py` (10 cases) |
| (2) App start/close/background | `utils/app_lifecycle.py` + `tests/test_app_lifecycle.py` (8 cases) |
| (3) Login/page operations | `pages/login_page.py` + `tests/test_login.py` (8 cases) + 5 business page objects |
| (4) Screenshot & log capture | `utils/screenshot.py` + `utils/logcat.py` + `utils/logger.py` + conftest failure hooks |
| (5) Performance (CPU/memory/battery/startup/response) | `utils/performance.py` + `tests/test_performance.py` (8 cases) |
| (6) Exception/weak network/stability | `utils/network_controller.py` + `tests/test_network.py` (5 cases) + `tests/test_stability.py` (5 cases) |

### Gaps Identified (🔧)
1. **Missing sub-page objects**: The prototype has 13 HTML pages but only 6 Page Objects exist. Missing: AlertDetail page, PlanDetail pages (2 variants), CreditDetail page, PlanEdit page
2. **Test coverage gaps for notification flows**: Alert sign/ignore operations need status verification; coordination notification submit verification; plan status transitions (approval→approved→flying→done) need dedicated tests
3. **Page object selector alignment**: Some selectors use `com.dolphin.atc:id/...` (native) but browser mode uses CSS selectors from prototype HTML — need dual-mode selector strategy verification
4. **Register page**: Per prototype docs, "第一迭代不提供注册入口" — register_page.py correctly uses skip guards but comment should reflect this design decision
5. **Documentation staleness**: Architecture doc references 36 cases (now 88); work log/summary need current-date entries

## Implementation Plan

### Step 1: Add Missing Page Objects (`pages/`)

Create 3 new page object files for prototype sub-pages not yet covered:

**1a. `pages/alert_detail_page.py`** — Alert notification detail page
- Corresponds to `小程序_告警详情.html`
- Locators: alert type, alert time, alert basis/description, aircraft info, sign button, ignore button
- Methods: `get_alert_info()`, `click_sign()`, `click_ignore()`, `verify_alert_status()`

**1b. `pages/plan_detail_page.py`** — Flight plan detail page  
- Corresponds to `小程序_计划详情.html` and `小程序_计划详情_留空.html`
- Locators: plan route, status badge, flight time, basic info fields, file attachments, action buttons (edit/delay/cancel/recall)
- Methods: `get_plan_status()`, `click_edit()`, `click_delay()`, `click_cancel()`, `verify_status_transition()`

**1c. `pages/credit_detail_page.py`** — Credit score detail page
- Corresponds to `小程序_信誉明细.html`
- Locators: score display, level badge, score rules, history list
- Methods: `get_credit_score()`, `get_credit_level()`, `verify_score_rules_displayed()`

### Step 2: Add Test Cases (`tests/`)

**2a. `tests/test_alert_detail.py`** — Alert notification tests (~5 cases)
- `test_alert_detail_display` — Alert detail page loads with correct fields
- `test_alert_sign_operation` — Sign operation changes status to "部分签收"
- `test_alert_ignore_operation` — Ignore operation changes status to "已关闭"
- `test_alert_priority_display` — Priority tags (紧急/重要/一般) display correctly
- `test_alert_recent_3h_filter` — Only alerts from last 3 hours shown

**2b. `tests/test_plan_operations.py`** — Plan lifecycle tests (~6 cases)
- `test_plan_status_flow[审批中→审批通过]` — Approval flow transitions
- `test_plan_status_flow[审批通过→待飞行]` — Pre-flight state
- `test_plan_delay_operation` — Delay execution time (max 2 times)
- `test_plan_cancel_operation` — Cancel a plan
- `test_plan_edit_from_rejected` — Edit rejected plan and resubmit
- `test_plan_detail_fields_complete` — All fields display per prototype spec

**2c. Enhance existing tests:**
- `test_home.py`: Add `test_alert_sign_from_home` — navigate to alert detail and sign
- `test_home.py`: Add `test_coordination_submit_verify` — verify submitted coordination status
- `test_mine.py`: Add `test_credit_detail_navigation` — navigate to credit detail page

### Step 3: Update & Optimize Existing Code

**3a. Update `pages/register_page.py`**
- Update docstring to note: "第一迭代不提供注册入口，仅支持PC端已有账号登录"
- No logic change needed

**3b. Verify browser-mode CSS selectors in existing Page Objects**
- Review selectors in login_page, home_page, flight_page, news_page, mine_page
- Ensure they match the actual CSS classes/elements in the prototype HTML
- Add CSS_SELECTOR backup locators where only native IDs exist

**3c. Add `data/` YAML files for new test data**
- `data/alert_data.yaml` — Alert test scenarios
- `data/plan_operations_data.yaml` — Plan status transition test data

### Step 4: Update Documentation

**4a. Update `docs/系统架构文档.md`**
- Update test case count (36 → ~100)
- Add new page objects and test modules to architecture diagram
- Add new sections: 告警详情测试, 计划操作测试, 信誉明细测试

**4b. Update `docs/工作日志.md`**
- Add entry for 2026-08-12: prototype analysis, gap identification, code supplementation
- Document new page objects, test cases, and optimizations

**4c. Update `docs/工作总结.md`**
- Update to v5.0
- Add new section: 第四阶段 — 原型对齐与测试补充
- Update test coverage statistics
- Update capability matrix

**4d. Update `启动命令.md`**
- Add `--module alert` and `--module plan-ops` entries
- Update test case counts
- Add new module descriptions

**4e. Update `README.md`** (root and mobile-test-framework/)
- Update test module table with new modules
- Update test case count

### Step 5: Push to GitHub

```bash
git add -A
git commit -m "feat: prototype alignment - add alert/plan/credit page objects and tests, update docs"
git push origin main
```

## Files to Modify/Create

### New Files (6)
| File | Description |
|------|-------------|
| `mobile-test-framework/pages/alert_detail_page.py` | Alert detail page object |
| `mobile-test-framework/pages/plan_detail_page.py` | Plan detail page object |
| `mobile-test-framework/pages/credit_detail_page.py` | Credit detail page object |
| `mobile-test-framework/tests/test_alert_detail.py` | Alert detail tests (~5 cases) |
| `mobile-test-framework/tests/test_plan_operations.py` | Plan operations tests (~6 cases) |
| `mobile-test-framework/data/alert_data.yaml` | Alert test data |
| `mobile-test-framework/data/plan_operations_data.yaml` | Plan operations test data |

### Modified Files (12)
| File | Changes |
|------|---------|
| `mobile-test-framework/pages/register_page.py` | Docstring update (no-registration note) |
| `mobile-test-framework/pages/login_page.py` | Add CSS_SELECTOR backup locators |
| `mobile-test-framework/pages/home_page.py` | Add CSS_SELECTOR backup locators, new methods for alert/coordination |
| `mobile-test-framework/pages/mine_page.py` | Add credit detail navigation method |
| `mobile-test-framework/tests/test_home.py` | +2 cases (alert sign, coordination submit verify) |
| `mobile-test-framework/tests/test_mine.py` | +1 case (credit detail navigation) |
| `mobile-test-framework/pytest.ini` | Register new markers: alert_detail, plan_ops |
| `mobile-test-framework/run_tests.py` | Add --module alert, --module plan-ops |
| `docs/系统架构文档.md` | Update architecture, counts, new modules |
| `docs/工作日志.md` | Add 2026-08-12 entry |
| `docs/工作总结.md` | Update to v5.0 |
| `README.md` | Update test module table |
| `mobile-test-framework/README.md` | Update test module table |

## Reuse of Existing Code

- **BasePage** (`pages/base_page.py`): All new page objects inherit from BasePage — reuse `find_element`, `click`, `input_text`, `swipe_up`, `is_element_present`, `take_screenshot`, `wait_for_element`
- **ConfigManager** (`config/config_manager.py`): Singleton pattern for configuration access
- **conftest.py fixtures**: Reuse `driver`, `logged_in_driver`, `config`, `adb`, `screenshot_manager`
- **ADBHelper** (`utils/adb_helper.py`): Reuse for GPS, network, screenshot utilities
- **Logger** (`utils/logger.py`): Reuse for all logging
- **pytest markers** (`pytest.ini`): Extend existing marker pattern

## Verification

1. **Syntax check**: `python -m pytest --collect-only tests/` — all new tests should be collected
2. **Smoke test**: `python run_tests.py --smoke` — existing smoke tests still pass
3. **New module tests**: `python run_tests.py --module alert` and `--module plan-ops` — new tests collected
4. **Browser mode verification**: Start `serve_pages.py`, connect phone, verify new page objects can find elements in prototype HTML
5. **Git push**: Confirm `git push origin main` succeeds
6. **Documentation review**: Spot-check all 5 updated docs for consistency
