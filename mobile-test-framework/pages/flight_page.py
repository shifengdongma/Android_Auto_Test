# -*- coding: utf-8 -*-
"""
申报页 - 飞行计划 (FlightPage)

页面路径: 底部Tab "申报" → 默认显示地图页
页面功能:
    - 地图展示 (起降场标记、空域等)
    - GPS定位 (允许/拒绝权限)
    - 起降场搜索
    - 飞行计划创建 (航线飞行 / 留空飞行)
        - 选择空域
        - 填写计划详情
        - 选择航空器/操控员
    - "我的计划"入口 → 审批进度
    - 离线暂存数据

对应原型: pages/小程序_办事.html, pages/小程序_计划编辑.html
"""

import logging
from typing import Dict, List, Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class FlightPage(BasePage):
    """
    申报(飞行计划) Page Object

    封装地图页和飞行计划创建流程。
    """

    # ============================================================
    # 元素定位器
    # ============================================================

    # --- 页面标识 ---
    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("申报")')
    MAP_VIEW = (AppiumBy.ID, "com.dolphin.atc:id/map_view")
    MAP_MARKER = (AppiumBy.ID, "com.dolphin.atc:id/map_marker")

    # --- GPS/定位 ---
    GPS_BUTTON = (AppiumBy.ID, "com.dolphin.atc:id/btn_gps")
    GPS_LOCATION_INDICATOR = (AppiumBy.ID, "com.dolphin.atc:id/location_indicator")
    GPS_PERMISSION_ALLOW = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("允许")')
    GPS_PERMISSION_DENY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("拒绝")')

    # --- 起降场搜索 ---
    SEARCH_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_search_airport")
    SEARCH_RESULT_LIST = (AppiumBy.ID, "com.dolphin.atc:id/rv_search_results")
    SEARCH_RESULT_ITEM = (AppiumBy.ID, "com.dolphin.atc:id/search_result_item")

    # --- 起降点选择 ---
    DEPARTURE_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("起飞")')
    ARRIVAL_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("降落")')
    SWAP_OD_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().description("交换")')

    # --- 空域选择 ---
    AIRSPACE_SEARCH = (AppiumBy.ID, "com.dolphin.atc:id/et_search_airspace")
    AIRSPACE_LIST = (AppiumBy.ID, "com.dolphin.atc:id/rv_airspace_list")
    AIRSPACE_ITEM = (AppiumBy.ID, "com.dolphin.atc:id/airspace_item")

    # --- 飞行计划表单 ---
    PLAN_NAME_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_plan_name")
    FLIGHT_TIME_START = (AppiumBy.ID, "com.dolphin.atc:id/tv_time_start")
    FLIGHT_TIME_END = (AppiumBy.ID, "com.dolphin.atc:id/tv_time_end")
    TIME_PICKER = (AppiumBy.ID, "com.dolphin.atc:id/time_picker")
    TIME_SLOT = (AppiumBy.ID, "com.dolphin.atc:id/time_slot")

    AIRCRAFT_SELECT = (AppiumBy.ID, "com.dolphin.atc:id/select_aircraft")
    AIRCRAFT_CHECKBOX = (AppiumBy.ID, "com.dolphin.atc:id/cb_aircraft")
    PILOT_SELECT = (AppiumBy.ID, "com.dolphin.atc:id/select_pilot")

    PLAN_NATURE_SELECT = (AppiumBy.ID, "com.dolphin.atc:id/select_plan_nature")
    PLAN_TYPE_SELECT = (AppiumBy.ID, "com.dolphin.atc:id/select_plan_type")

    FILE_UPLOAD_AREA = (AppiumBy.ID, "com.dolphin.atc:id/upload_area")
    FILE_UPLOAD_BUTTON = (AppiumBy.ID, "com.dolphin.atc:id/btn_upload")

    SUBMIT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("提交")')
    CANCEL_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("取消")')
    NEXT_STEP_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("下一步")')

    # --- 留空飞行 ---
    LOITER_FLIGHT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("留空飞行")')
    DRAW_TOOLBAR = (AppiumBy.ID, "com.dolphin.atc:id/draw_toolbar")
    DRAW_POLYGON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("多边形")')
    DRAW_CIRCLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("圆形")')
    DRAW_BUFFER = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("线缓冲区")')
    DRAW_CLEAR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("清空")')
    AIRSPACE_NAME_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/et_airspace_name")
    DRAW_NEXT_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("下一步")')

    # --- 我的计划 ---
    MY_PLANS_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的计划")')

    # --- 离线暂存提示 ---
    OFFLINE_BANNER = (AppiumBy.ID, "com.dolphin.atc:id/offline_banner")
    DRAFT_SAVED_TOAST = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("暂存")')

    # --- 备用定位 ---
    ALT_PLAN_NAME = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("计划名称")')
    ALT_SUBMIT = (AppiumBy.ID, "com.dolphin.atc:id/btn_submit")
    ALT_SEARCH_INPUT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.EditText")')

    # ============================================================
    # 页面操作方法 - 页面状态
    # ============================================================

    def is_on_flight_page(self) -> bool:
        """判断当前是否在申报页"""
        return (
            self.is_element_present(self.PAGE_TITLE, timeout=5)
            or self.is_element_present(self.MAP_VIEW, timeout=5)
        )

    def wait_for_flight_page(self, timeout: int = 30):
        """等待申报页加载完成"""
        logger.info("等待申报页加载...")
        self.wait_for_element_visible(self.MAP_VIEW, timeout)
        return self

    # ============================================================
    # GPS定位
    # ============================================================

    def allow_gps_permission(self):
        """
        允许GPS定位权限

        点击系统权限弹窗中的"允许"按钮。
        通常在首次打开申报页时自动弹出。

        Returns:
            self
        """
        logger.info("允许GPS定位权限")
        self.handle_permission_popup(allow=True, timeout=5)
        return self

    def deny_gps_permission(self):
        """
        拒绝GPS定位权限

        点击系统权限弹窗中的"拒绝"按钮。

        Returns:
            self
        """
        logger.info("拒绝GPS定位权限")
        self.handle_permission_popup(allow=False, timeout=5)
        return self

    def click_gps_button(self):
        """点击GSP定位按钮 (手动触发定位)"""
        logger.info("点击GPS定位按钮")
        self.click(self.GPS_BUTTON)
        return self

    def is_gps_located(self) -> bool:
        """判断GPS是否已定位成功 (位置指示器是否显示)"""
        return self.is_element_present(self.GPS_LOCATION_INDICATOR, timeout=5)

    def is_search_mode_active(self) -> bool:
        """
        判断是否处于搜索降级模式 (GPS被拒绝后)

        GPS被拒绝后应显示搜索输入框。

        Returns:
            bool
        """
        return self.is_element_present(self.SEARCH_INPUT, timeout=3)

    # ============================================================
    # 起降场搜索
    # ============================================================

    def search_airport(self, keyword: str):
        """
        搜索起降场

        Args:
            keyword: 搜索关键词

        Returns:
            self
        """
        logger.info(f"搜索起降场: {keyword}")
        self.input_text(self.SEARCH_INPUT, keyword)
        self.wait_for_element_visible(self.SEARCH_RESULT_LIST, timeout=10)
        return self

    def select_airport_result(self, index: int = 0):
        """
        从搜索结果中选择起降场

        Args:
            index: 结果索引 (0=第一个)

        Returns:
            self
        """
        logger.info(f"选择第{index}个搜索结果")
        results = self.find_elements(self.SEARCH_RESULT_ITEM)
        if index >= len(results):
            raise IndexError(
                f"搜索结果索引 {index} 超出范围 (共{len(results)}条)"
            )
        results[index].click()
        return self

    def get_search_results_count(self) -> int:
        """获取搜索结果数量"""
        return len(self.find_elements(self.SEARCH_RESULT_ITEM))

    # ============================================================
    # 起降点设置
    # ============================================================

    def set_departure(self, airport_name: str):
        """
        设置起飞地

        Args:
            airport_name: 起降场名称

        Returns:
            self
        """
        logger.info(f"设置起飞地: {airport_name}")
        self.input_text(self.DEPARTURE_INPUT, airport_name)
        return self

    def set_arrival(self, airport_name: str):
        """
        设置降落地

        Args:
            airport_name: 起降场名称

        Returns:
            self
        """
        logger.info(f"设置降落地: {airport_name}")
        self.input_text(self.ARRIVAL_INPUT, airport_name)
        return self

    def swap_od(self):
        """交换起飞地和降落地"""
        logger.info("交换起降点")
        self.click(self.SWAP_OD_BUTTON)
        return self

    # ============================================================
    # 航线选择 (进入表单前的推荐航线)
    # ============================================================

    def click_route_option(self, route_label: str = "A"):
        """
        选择推荐航线

        Args:
            route_label: 航线标签 (A/B/C)

        Returns:
            self
        """
        route_locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().textContains("路线 {route_label}")',
        )
        logger.info(f"选择航线: {route_label}")
        self.click(route_locator)
        return self

    def select_departure_time(self, time_text: str):
        """
        选择出发时间 (从时间选择器中)

        Args:
            time_text: 时间文本，如 "14:30"
        """
        logger.info(f"选择出发时间: {time_text}")
        slot_locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{time_text}")',
        )
        self.click(slot_locator)
        return self

    def click_next_step(self):
        """
        点击"下一步"进入表单填写

        Returns:
            self
        """
        logger.info("点击'下一步'")
        self.click(self.NEXT_STEP_BUTTON)
        return self

    # ============================================================
    # 飞行计划表单
    # ============================================================

    def enter_plan_name(self, name: str):
        """填写计划名称"""
        logger.info(f"填写计划名称: {name}")
        self.input_text(self.PLAN_NAME_INPUT, name)
        return self

    def select_aircraft(self, index: int = 0):
        """
        选择航空器 (移动端只读，从PC备案数据选择)

        Args:
            index: 航空器列表索引

        Returns:
            self
        """
        logger.info(f"选择航空器 #{index}")
        self.click(self.AIRCRAFT_SELECT)
        # 等待航空器列表弹出
        self.wait_seconds(0.5)
        checkboxes = self.find_elements(self.AIRCRAFT_CHECKBOX)
        if index < len(checkboxes):
            checkboxes[index].click()
        else:
            raise IndexError(f"航空器索引 {index} 超出范围")
        # 关闭选择列表
        self.go_back()
        return self

    def select_pilot(self, index: int = 0):
        """
        选择操控员

        Args:
            index: 操控员列表索引

        Returns:
            self
        """
        logger.info(f"选择操控员 #{index}")
        self.click(self.PILOT_SELECT)
        self.wait_seconds(0.5)
        # 通过文本选择操控员
        options = self.find_elements(
            (AppiumBy.ID, "com.dolphin.atc:id/pilot_item")
        )
        if index < len(options):
            options[index].click()
        return self

    def select_plan_nature(self, nature: str):
        """
        选择计划性质

        Args:
            nature: 计划性质，如 "物流运输"/"个人休闲飞行"

        Returns:
            self
        """
        logger.info(f"选择计划性质: {nature}")
        self.click(self.PLAN_NATURE_SELECT)
        nature_locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            f'new UiSelector().text("{nature}")',
        )
        self.click(nature_locator)
        return self

    def upload_file(self, file_path: str):
        """
        上传PDF文件

        Args:
            file_path: 本地PDF文件路径

        Returns:
            self

        Note:
            需要确保设备上存在该文件或通过Appium push到设备。
        """
        logger.info(f"上传文件: {file_path}")
        self.click(self.FILE_UPLOAD_AREA)
        # 系统文件选择器交互 — 实现取决于具体系统
        self.click(self.FILE_UPLOAD_BUTTON)
        return self

    def expand_more_info(self):
        """展开隐藏信息区域 (计划名称/文件资料/计划类型)"""
        more_locator = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("更多信息")')
        if self.is_element_present(more_locator, timeout=2):
            self.click(more_locator)
        return self

    def click_submit(self):
        """
        点击提交按钮

        创建即提交 (无草稿)。

        Returns:
            self: 提交后跳转到审批进度页
        """
        logger.info("提交飞行计划")
        locator = self.ALT_SUBMIT
        if not self.is_element_present(locator, timeout=2):
            locator = self.SUBMIT_BUTTON
        self.click(locator)
        return self

    def create_flight_plan(self, plan_data: Dict[str, any]):
        """
        完整创建飞行计划流程 (组合操作)

        Args:
            plan_data: 计划数据字典，包含:
                - departure: 起飞地
                - arrival: 降落地
                - plan_name: 计划名称
                - aircraft_index: 航空器索引
                - pilot_index: 操控员索引

        Returns:
            self
        """
        logger.info("开始创建飞行计划...")

        # 设置起降点
        if "departure" in plan_data:
            self.set_departure(plan_data["departure"])
        if "arrival" in plan_data:
            self.set_arrival(plan_data["arrival"])

        # 进入表单
        self.click_next_step()
        self.wait_seconds(1)

        # 填写表单
        if "plan_name" in plan_data:
            self.enter_plan_name(plan_data["plan_name"])
        if "aircraft_index" in plan_data:
            self.select_aircraft(plan_data["aircraft_index"])
        if "pilot_index" in plan_data:
            self.select_pilot(plan_data["pilot_index"])

        # 提交
        self.click_submit()
        logger.info("飞行计划创建流程完成")
        return self

    # ============================================================
    # 留空飞行 (隔离空域绘制)
    # ============================================================

    def open_loiter_flight(self):
        """打开留空飞行界面"""
        logger.info("打开留空飞行")
        self.click(self.LOITER_FLIGHT_BUTTON)
        self.wait_for_element_visible(self.DRAW_TOOLBAR, timeout=10)
        return self

    def select_draw_shape(self, shape: str):
        """
        选择绘制形状

        Args:
            shape: 形状类型
                - "polygon": 多边形
                - "circle": 圆形
                - "buffer": 线缓冲区

        Returns:
            self
        """
        shape_map = {
            "polygon": self.DRAW_POLYGON,
            "circle": self.DRAW_CIRCLE,
            "buffer": self.DRAW_BUFFER,
        }
        locator = shape_map.get(shape)
        if locator is None:
            raise ValueError(f"不支持的绘制形状: {shape}")
        logger.info(f"选择绘制形状: {shape}")
        self.click(locator)
        return self

    def clear_drawing(self):
        """清空绘制内容"""
        logger.info("清空绘制")
        self.click(self.DRAW_CLEAR)
        return self

    def enter_airspace_name(self, name: str):
        """
        输入空域名称

        留空飞行必须填写空域名称才能进入下一步。

        Args:
            name: 空域名称

        Returns:
            self
        """
        logger.info(f"输入空域名称: {name}")
        self.input_text(self.AIRSPACE_NAME_INPUT, name)
        return self

    def click_draw_next(self):
        """
        点击留空飞行的"下一步"

        如果空域名称为空，应该被拦截(表单校验)。
        """
        logger.info("点击留空飞行'下一步'")
        self.click(self.DRAW_NEXT_BUTTON)
        return self

    # ============================================================
    # 我的计划
    # ============================================================

    def open_my_plans(self):
        """
        点击"我的计划"按钮

        Returns:
            FlightApprovalPage: 审批进度页面
        """
        logger.info("打开'我的计划'")
        self.click(self.MY_PLANS_BUTTON)
        from pages.flight_page import FlightApprovalPage
        return FlightApprovalPage(self.driver)

    # ============================================================
    # 离线相关
    # ============================================================

    def is_offline_banner_shown(self) -> bool:
        """判断是否显示离线提示横幅"""
        return self.is_element_present(self.OFFLINE_BANNER, timeout=3)

    def is_draft_saved(self) -> bool:
        """判断数据是否已暂存"""
        return self.is_toast_displayed("暂存", timeout=5)

    def is_expired_draft_warning_shown(self) -> bool:
        """判断是否显示'时段已过期'警告"""
        expired_locator = (
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().textContains("已过期")',
        )
        return self.is_element_present(expired_locator, timeout=3)


class FlightApprovalPage(BasePage):
    """
    审批进度页面 (我的计划)

    页面路径: 申报页 → "我的计划"
    页面功能:
        - 飞行计划列表 (多种状态)
        - 状态筛选
        - 计划操作 (查看/编辑/取消/推延/放飞申请)

    对应原型: pages/小程序_审批进度.html
    """

    # --- 元素定位器 ---
    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("我的计划")')
    BACK_BUTTON = (AppiumBy.ACCESSIBILITY_ID, "返回")

    FILTER_TRIGGER = (AppiumBy.ID, "com.dolphin.atc:id/filter_trigger")
    FILTER_DROPDOWN = (AppiumBy.ID, "com.dolphin.atc:id/filter_dropdown")
    FILTER_ALL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("全部")')
    FILTER_PENDING = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("审批中")')
    FILTER_APPROVED = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("已通过")')
    FILTER_REJECTED = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("已驳回")')

    PLAN_CARD = (AppiumBy.ID, "com.dolphin.atc:id/plan_card")
    PLAN_STATUS = (AppiumBy.ID, "com.dolphin.atc:id/plan_status")
    PLAN_ROUTE = (AppiumBy.ID, "com.dolphin.atc:id/plan_route")

    BTN_VIEW_DETAIL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("查看详情")')
    BTN_EDIT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("编辑")')
    BTN_CANCEL = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("取消")')
    BTN_DELAY = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("推延")')
    BTN_LAUNCH = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("放飞申请")')
    BTN_MONITOR = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("飞行监控")')

    # 推延弹窗
    DELAY_START_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/delay_start")
    DELAY_END_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/delay_end")
    DELAY_REASON_INPUT = (AppiumBy.ID, "com.dolphin.atc:id/delay_reason")
    DELAY_SUBMIT = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("提交推延")')

    # ============================================================
    # 操作方法
    # ============================================================

    def is_on_approval_page(self) -> bool:
        """判断是否在审批进度页"""
        return self.is_element_present(self.PAGE_TITLE, timeout=5)

    def wait_for_page(self, timeout: int = 20):
        """等待审批进度页加载"""
        self.wait_for_element_visible(self.PAGE_TITLE, timeout)
        return self

    def get_plan_count(self) -> int:
        """获取计划列表数量"""
        return len(self.find_elements(self.PLAN_CARD))

    def filter_by_status(self, status: str):
        """
        按状态筛选计划

        Args:
            status: 状态名称 (审批中/已通过/已驳回/全部)
        """
        status_map = {
            "全部": self.FILTER_ALL,
            "审批中": self.FILTER_PENDING,
            "已通过": self.FILTER_APPROVED,
            "已驳回": self.FILTER_REJECTED,
        }
        locator = status_map.get(status)
        if locator is None:
            raise ValueError(f"未知状态: {status}")

        logger.info(f"筛选计划状态: {status}")
        self.click(self.FILTER_TRIGGER)
        self.wait_for_element_visible(self.FILTER_DROPDOWN, timeout=5)
        self.click(locator)
        return self

    def get_plan_statuses(self) -> List[str]:
        """获取列表中所有计划的状态文本"""
        cards = self.find_elements(self.PLAN_CARD)
        statuses = []
        for card in cards:
            try:
                status = card.find_element(*self.PLAN_STATUS).text
                statuses.append(status)
            except Exception:
                continue
        return statuses

    def click_first_plan(self):
        """点击第一个计划条目查看详情"""
        cards = self.find_elements(self.PLAN_CARD)
        if cards:
            cards[0].click()
        return self

    def cancel_plan(self):
        """取消计划 (带确认对话框)"""
        logger.info("取消飞行计划")
        self.click(self.BTN_CANCEL)
        # 处理确认弹窗
        self.accept_alert()
        return self

    def back_to_flight(self):
        """返回申报页"""
        self.click(self.BACK_BUTTON)
        return FlightPage(self.driver)
