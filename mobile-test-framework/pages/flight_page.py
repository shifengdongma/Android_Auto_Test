# -*- coding: utf-8 -*-
"""
申报页 - 飞行计划 (FlightPage)

页面功能 (真机实测):
    - 起降场选择: 起飞地/降落地/备降地, 字段即搜索框 (点击聚焦后输入关键词过滤列表)
    - 表单提交: 出发时间/下一步/航空器/操作员 (选完机场后逐步出现)

交互方式: uni-app WebView内容, 经 utils.webview_a11y 定位;
中文输入 = 剪贴板 + keyevent 279 原生粘贴 (见 webview_a11y.type_chinese)。
"""

import logging
import time

from pages.base_page import BasePage
from utils import webview_a11y

logger = logging.getLogger(__name__)


class FlightPage(BasePage):
    """申报Page Object"""

    FIELD_DEPART = "请输入起飞地"
    FIELD_ARRIVE = "请输入降落地"
    FIELD_ALT = "请输入备降地"

    AIRPORT_QF_1 = "新疆起降场1"
    AIRPORT_QF_2 = "新疆起降场2"

    def select_airport(
        self, field_placeholder: str, keyword: str, result_text: str, retry: bool = True
    ) -> bool:
        """
        起降场搜索选择完整流程

        流程 (真机实测):
            1. 点击字段 (占位文本) 聚焦; 首次进入可能弹系统位置权限
            2. 剪贴板+原生粘贴输入关键词, 列表实时过滤
            3. 点击列表结果项 (y>650 过滤后台首页同文案节点)
            4. 验证字段值已更新 (表单区 y<650 精确文本, 排除列表项误判)

        重试策略: 每次重试前先检查"已选中" (点击结果后字段值可能
        延迟刷新, 上一轮实际已成功), 避免字段已更新后误判失败。

        Args:
            field_placeholder: 字段占位文本 (请输入起飞地/降落地/备降地)
            keyword: 搜索关键词 (如 新疆)
            result_text: 要选择的结果项文本 (如 新疆起降场1)

        Returns:
            bool: 是否选择成功 (字段值已更新)
        """
        logger.info(f"选择{field_placeholder}: 搜索'{keyword}' -> '{result_text}'")

        # 定位字段并用坐标点击 (元素易stale, 坐标稳定); 返回字段行y供校验定位
        def tap_field():
            el = webview_a11y.find_text(self.driver, field_placeholder, timeout=10)
            if el is None:
                el = webview_a11y.find_text(self.driver, keyword, timeout=10)
            if el is None:
                return None
            x, y = webview_a11y.element_center(el)
            self.driver.tap([(x, y)])
            return y

        field_y = tap_field()
        assert field_y is not None, f"未找到字段: {field_placeholder}"

        # 目标字段行区间精确文本校验: 只认该字段所在行的值节点
        # (三个字段行相邻且值可相同, 如降落地与备降地同为新疆起降场2,
        #  不限定行区间会命中相邻字段导致误判; 也排除y>650列表项与首页卡片)
        def field_updated():
            return (
                webview_a11y.find_visible_by_text(
                    self.driver, result_text, timeout=12,
                    min_y=field_y - 70, max_y=field_y + 70, exact=True,
                )
                is not None
            )
        time.sleep(1.5)
        # 首次进入申报页会弹系统位置权限 (EMUI定制文案)
        webview_a11y.handle_emui_permission(self.driver)

        for attempt in range(1, 7):
            # 上一轮点击结果后字段值可能延迟刷新: 先确认是否已选中
            if field_updated():
                logger.info(f"选择成功: {result_text} (第{attempt}轮确认)")
                return True
            if tap_field() is None:
                logger.error(f"第{attempt}次: 字段重新定位失败")
                break
            time.sleep(1.5)
            if attempt == 1:
                # 只有第一次粘贴; 重试时字段已有关键词, 重新聚焦等列表刷新即可
                webview_a11y.type_chinese(self.driver, keyword)
            else:
                time.sleep(4)  # 列表刷新等待
            result = webview_a11y.pick_result(self.driver, result_text, timeout=25)
            if result is not None:
                x, y = webview_a11y.element_center(result)
                self.driver.tap([(x, y)])
                time.sleep(2.5)
                if field_updated():
                    logger.info(f"选择成功: {result_text}")
                    return True
                logger.warning(f"点击结果后字段未更新, 重试 ({attempt})")
            else:
                logger.warning(f"未找到结果项 {result_text}, 重试 ({attempt})")
        logger.error(f"选择失败: {field_placeholder} -> {result_text}")
        return False

    def select_depart(self) -> bool:
        """选择起飞地: 新疆起降场1"""
        return self.select_airport(self.FIELD_DEPART, "新疆", self.AIRPORT_QF_1)

    def select_arrive(self) -> bool:
        """选择降落地: 新疆起降场2"""
        return self.select_airport(self.FIELD_ARRIVE, "新疆", self.AIRPORT_QF_2)

    def select_alternate(self) -> bool:
        """选择备降地: 新疆起降场2"""
        return self.select_airport(self.FIELD_ALT, "新疆", self.AIRPORT_QF_2)

    def has_text(self, text: str, timeout: float = 5) -> bool:
        """页面是否存在指定文本 (校准用)"""
        return webview_a11y.find_visible_by_text(
            self.driver, text, timeout=timeout, min_y=100
        ) is not None

    def modify_departure_time(self, new_time: str = "04:00") -> bool:
        """
        修改出发时间 (真机实测: 15分钟一档的时间选择器)

        流程: 展开出发时间区 -> 点击"修改" -> 选择时间档 -> 确定

        Args:
            new_time: 目标时间档 (如 04:00)

        Returns:
            bool: 出发时间是否已更新
        """
        logger.info(f"修改出发时间: -> {new_time}")
        el = webview_a11y.find_visible_by_text(
            self.driver, "出发时间", timeout=8, min_y=500
        )
        assert el is not None, "未找到出发时间区"
        el.click()
        time.sleep(1)
        modify = webview_a11y.find_visible_by_text(
            self.driver, "修改", timeout=8, min_y=800
        )
        assert modify is not None, "未找到'修改'按钮"
        modify.click()
        time.sleep(2)
        assert webview_a11y.find_text(
            self.driver, "选择出发时间", timeout=8
        ) is not None, "时间选择器未打开"

        # 选择时间档 (选择器内时间文本)
        slot = webview_a11y.find_visible_by_text(
            self.driver, new_time, timeout=8, min_y=1400
        )
        if slot is not None:
            slot.click()
            time.sleep(1)
        # 确认 (选择器的确定按钮)
        confirm = webview_a11y.find_text(self.driver, "确定", timeout=8)
        assert confirm is not None, "时间选择器无确定按钮"
        confirm.click()
        time.sleep(1)
        ok = self.has_text(new_time, timeout=5)
        logger.info(f"出发时间修改: {'成功' if ok else '失败'} ({new_time})")
        return ok

    def click_next_step(self, marker: str = "填写飞行计划") -> bool:
        """
        点击"下一步" (选完机场与时间后表单底部)

        真机实测: 下一步直接进入"填写飞行计划"页 (无航路中间页)。

        Args:
            marker: 点击后应出现的后续页面特征文本

        Returns:
            bool: 是否出现后续页面特征 (后台计算较慢, 轮询至20秒)
        """
        logger.info(f"点击下一步 (期望出现: {marker})")
        el = webview_a11y.find_visible_by_text(
            self.driver, "下一步", timeout=8, min_y=1500
        )
        assert el is not None, "未找到下一步按钮"
        el.click()
        return self.has_text(marker, timeout=20)

    def _select_form_picker(self, placeholder: str, sheet_title: str) -> bool:
        """
        点击表单行 -> 底部弹层选择首项 -> 确定

        实测弹层结构 (NOH-AN01, 2026-08-14):
            头部: 取消 | {sheet_title} | 确定 (y≈1930-2090)
            列表: 单选行 (y≈2100-2360), 点行选中后需点"确定"提交

        Args:
            placeholder: 表单行占位文本 (请选择航空器/请选择操控员)
            sheet_title: 弹层标题 (选择航空器/选择操控员)

        Returns:
            bool: 占位文本消失 (值已更新)
        """
        logger.info(f"选择{placeholder} (弹层: {sheet_title})")
        el = webview_a11y.find_visible_by_text(
            self.driver, placeholder, timeout=8, min_y=200
        )
        assert el is not None, f"未找到: {placeholder}"
        x, y = webview_a11y.element_center(el)
        self.driver.tap([(x, y)])
        time.sleep(2)

        # 弹层打开校验 (标题为唯一特征: 选择航空器 != 请选择航空器)
        if webview_a11y.find_text(self.driver, sheet_title, timeout=8) is None:
            logger.error(f"{placeholder} 弹层未打开 (未找到标题: {sheet_title})")
            return False

        # 列表首项: 弹层区域(y2050-2360)内排除静态按钮后最靠上的节点
        y1 = webview_a11y.find_top_sheet_item(self.driver)
        if y1 is None:
            logger.error(f"{placeholder} 弹层列表为空")
            return False
        # 首项文本起点x≈99, 点(200, y1+33)落于首行文本内
        self.driver.tap([(200, y1 + 33)])
        time.sleep(1.5)

        # 弹层若不自动关闭则点"确定"提交选择
        confirm = webview_a11y.find_visible_by_text(
            self.driver, "确定", timeout=3, min_y=1900
        )
        if confirm is not None:
            cx, cy = webview_a11y.element_center(confirm)
            self.driver.tap([(cx, cy)])
            time.sleep(1.5)

        ok = (
            webview_a11y.find_visible_by_text(
                self.driver, placeholder, timeout=3, min_y=200
            )
            is None
        )
        logger.info(f"{placeholder} 选择: {'成功' if ok else '失败'}")
        return ok

    def select_aircraft(self) -> bool:
        """选择航空器 (弹层列表首项)"""
        return self._select_form_picker("请选择航空器", "选择航空器")

    def select_operator(self) -> bool:
        """选择操控员 (弹层列表首项)"""
        return self._select_form_picker("请选择操控员", "选择操控员")

    def enter_loiter_flight(self):
        """
        点击底部"留空飞行" -> 进入留空飞行空域绘制页

        Returns:
            LoiterPage: 留空飞行绘制页对象 (继承FlightPage, 后续
            下一步->填写飞行计划->提交 复用原有流程)
        """
        logger.info("进入留空飞行空域绘制页")
        el = webview_a11y.find_visible_by_text(
            self.driver, "留空飞行", timeout=8, min_y=2000
        )
        assert el is not None, "未找到留空飞行按钮"
        x, y = webview_a11y.element_center(el)
        self.driver.tap([(x, y)])
        time.sleep(2.5)
        assert (
            webview_a11y.find_text(self.driver, "留空飞行空域绘制", timeout=8)
            is not None
        ), "未进入留空飞行空域绘制页"
        return LoiterPage(self.driver)

    def open_my_plans(self) -> bool:
        """
        点击底部"我的计划" -> 计划列表页

        Returns:
            bool: 是否进入计划列表页 (特征: 顶部"全部状态"筛选器)
        """
        logger.info("打开我的计划")
        el = webview_a11y.find_visible_by_text(
            self.driver, "我的计划", timeout=8, min_y=2000
        )
        assert el is not None, "未找到我的计划按钮"
        x, y = webview_a11y.element_center(el)
        self.driver.tap([(x, y)])
        time.sleep(2.5)
        ok = self.has_text("全部状态", timeout=8)
        logger.info(f"我的计划: {'已打开' if ok else '打开失败'}")
        return ok

    def submit_plan(self) -> bool:
        """
        点击底部提交按钮 -> 确认弹窗点"确定"

        实测 (NOH-AN01, 2026-08-14):
            提交后弹确认框: "进入PC端飞行计划审批流程" + 确定按钮
            (确定 bounds y≈1260-1413); 点确定后跳转"我的计划"页,
            新计划置顶 (状态: 已通过)。

        Returns:
            bool: 是否成功进入"我的计划"页
        """
        logger.info("提交飞行计划")
        el = webview_a11y.find_visible_by_text(
            self.driver, "提交", timeout=8, min_y=2000
        )
        if el is None:
            # 兜底: 实测提交按钮中心坐标
            logger.warning("a11y未找到提交按钮, 坐标兜底 (721,2265)")
            self.driver.tap([(721, 2265)])
        else:
            x, y = webview_a11y.element_center(el)
            self.driver.tap([(x, y)])
        time.sleep(2)

        # 确认弹窗: 确定按钮 (y>1200 过滤页面其他同文案节点)
        confirm = webview_a11y.find_visible_by_text(
            self.driver, "确定", timeout=10, min_y=1200
        )
        if confirm is None:
            logger.error("未出现提交确认弹窗 (未找到确定按钮)")
            return False
        x, y = webview_a11y.element_center(confirm)
        self.driver.tap([(x, y)])
        time.sleep(3)
        ok = self.has_text("我的计划", timeout=5)
        logger.info(f"提交飞行计划: {'成功(已进入我的计划)' if ok else '失败'}")
        return ok


class LoiterPage(FlightPage):
    """
    留空飞行空域绘制页 (申报页底部"留空飞行"进入)

    页面结构 (真机实测, NOH-AN01 2026-08-14):
        - 标题: 留空飞行空域绘制
        - 空域类型: 多边形 | 圆形 | 线缓冲区 (y≈1485-1539, 点击切换)
        - 地图画布区: y≈250-1400, 绘制手势作用于此区域
        - 请输入空域名称 (y≈1653), 常飞空域
        - 出发时间区 (y≈1827+) 与 下一步 按钮 (底部)

    绘制手势 (实测):
        - 多边形/线缓冲区: 单击加点, 双击结束 (mobile: doubleClickGesture)
        - 圆形: 长按后向外拖动 (mobile: dragGesture, duration=1500)

    后续流程与普通飞行计划一致: 下一步 -> 填写飞行计划 (航空器/操控员/提交),
    继承 FlightPage 复用 select_aircraft/select_operator/submit_plan。
    """

    # ---- 实测绘制坐标 (地图画布区内) ----
    POLYGON_TRIANGLE = [(400, 750), (750, 750), (575, 550)]
    CIRCLE_CENTER = (550, 750)
    CIRCLE_EDGE = (780, 750)
    BUFFER_LINE = [(350, 900), (800, 900)]

    def select_type(self, type_name: str) -> bool:
        """点击切换空域绘制类型 (多边形/圆形/线缓冲区)"""
        el = webview_a11y.find_visible_by_text(
            self.driver, type_name, timeout=8, min_y=1400
        )
        assert el is not None, f"未找到空域类型: {type_name}"
        x, y = webview_a11y.element_center(el)
        self.driver.tap([(x, y)])
        time.sleep(1)
        logger.info(f"已选择空域类型: {type_name}")
        return True

    def _double_click(self, x: int, y: int):
        """双击结束绘制 (mobile手势优先, 失败回退两次快速tap)"""
        try:
            self.driver.execute_script(
                "mobile: doubleClickGesture", {"x": x, "y": y}
            )
            return
        except Exception as e:
            logger.warning(f"doubleClickGesture失败({type(e).__name__}), 回退两次tap")
        self.driver.tap([(x, y)])
        time.sleep(0.08)
        self.driver.tap([(x, y)])

    def draw_polygon(self, points=None) -> bool:
        """多边形绘制: 依次单击各顶点, 末点双击结束"""
        points = points or self.POLYGON_TRIANGLE
        for i, (x, y) in enumerate(points, 1):
            self.driver.tap([(x, y)])
            time.sleep(0.8)
            logger.debug(f"多边形顶点{i}: ({x},{y})")
        self._double_click(points[-1][0], points[-1][1])
        time.sleep(1.5)
        logger.info(f"多边形绘制完成 ({len(points)}个顶点)")
        return True

    def draw_buffer(self, points=None) -> bool:
        """线缓冲区绘制: 依次单击路径点, 末点双击结束"""
        points = points or self.BUFFER_LINE
        for i, (x, y) in enumerate(points, 1):
            self.driver.tap([(x, y)])
            time.sleep(0.8)
            logger.debug(f"线缓冲点{i}: ({x},{y})")
        self._double_click(points[-1][0], points[-1][1])
        time.sleep(1.5)
        logger.info(f"线缓冲区绘制完成 ({len(points)}个点)")
        return True

    def draw_circle(self, center=None, edge=None) -> bool:
        """圆形绘制: 圆心长按后向边缘拖动 (慢速drag模拟长按)"""
        center = center or self.CIRCLE_CENTER
        edge = edge or self.CIRCLE_EDGE
        try:
            self.driver.execute_script(
                "mobile: dragGesture",
                {
                    "startX": center[0], "startY": center[1],
                    "endX": edge[0], "endY": edge[1], "duration": 1500,
                },
            )
        except Exception as e:
            logger.warning(f"dragGesture失败({type(e).__name__})")
            return False
        time.sleep(1.5)
        logger.info(f"圆形绘制完成 (圆心{center}, 半径至{edge})")
        return True

    def input_airspace_name(self, name: str = "测试") -> bool:
        """
        输入空域名称 (剪贴板+原生粘贴), 完成后关闭输入法键盘

        注意: 键盘不关闭时底部"修改/下一步"按钮被遮挡不可见。
        """
        el = webview_a11y.find_visible_by_text(
            self.driver, "请输入空域名称", timeout=8, min_y=1500
        )
        assert el is not None, "未找到空域名称输入框"
        x, y = webview_a11y.element_center(el)
        self.driver.tap([(x, y)])
        time.sleep(1.2)
        webview_a11y.type_chinese(self.driver, name)
        # 关闭输入法键盘 (底部按钮需要)
        try:
            self.driver.hide_keyboard()
        except Exception:
            from utils.adb_helper import ADBHelper

            ADBHelper().press_key(4)
        time.sleep(1.5)
        ok = (
            webview_a11y.find_visible_by_text(
                self.driver, name, timeout=5, min_y=1500, exact=True
            )
            is not None
        )
        logger.info(f"空域名称输入: {'成功' if ok else '失败'} ({name})")
        return ok
