# -*- coding: utf-8 -*-
"""
信誉明细页面 (CreditDetailPage)

页面路径: 我的 → 信誉积分卡片 → 信誉明细
页面功能:
    - 信誉积分总览 (企业名称/当前积分/等级)
    - 累计加分/扣分统计
    - 加分项列表 (备案/申报等)
    - 扣分项列表 (黑飞/偏离航路等)
    - 积分政策解读入口

对应原型: pages/小程序_信誉明细.html
"""

import logging
from typing import Dict, List, Optional

from appium.webdriver.common.appiumby import AppiumBy

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class CreditDetailPage(BasePage):
    """
    信誉明细页面对象

    封装信誉积分的元素定位和操作方法。
    """

    # ============================================================
    # 元素定位器 - Native (resource-id, 待APK校准)
    # ============================================================

    PAGE_TITLE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("信誉明细")')
    BACK_BUTTON = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().descriptionContains("返回")')

    SCORE_VALUE = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").instance(3)')

    # 规则卡片
    RULE_CARD = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().className("android.widget.TextView").instance(6)')

    # 积分政策解读
    POLICY_LINK = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("积分政策解读")')

    # ============================================================
    # 元素定位器 - Browser模式 (CSS Selectors)
    # ============================================================

    ALT_PAGE_TITLE = (AppiumBy.CSS_SELECTOR, ".page-header .title")
    ALT_BACK_BUTTON = (AppiumBy.CSS_SELECTOR, ".page-header .back")

    # 积分头部
    ALT_SCORE_HEAD = (AppiumBy.CSS_SELECTOR, ".score-head")
    ALT_COMPANY_NAME = (AppiumBy.CSS_SELECTOR, ".score-head .company")
    ALT_SCORE_VALUE = (AppiumBy.CSS_SELECTOR, ".score-head .score")
    ALT_SCORE_LABEL = (AppiumBy.CSS_SELECTOR, ".score-head .score-label")

    # 累计统计
    ALT_SUMMARY = (AppiumBy.CSS_SELECTOR, ".summary")
    ALT_TOTAL_PLUS = (AppiumBy.CSS_SELECTOR, ".summary .num.plus")
    ALT_TOTAL_MINUS = (AppiumBy.CSS_SELECTOR, ".summary .num.minus")

    # 章节标题
    ALT_SECTION_TITLE = (AppiumBy.CSS_SELECTOR, ".section-title")
    ALT_DOT_GREEN = (AppiumBy.CSS_SELECTOR, ".section-title .dot.green")
    ALT_DOT_RED = (AppiumBy.CSS_SELECTOR, ".section-title .dot.red")

    # 规则卡片
    ALT_RULE_CARDS = (AppiumBy.CSS_SELECTOR, ".rule-card")
    ALT_RULE_NAME = (AppiumBy.CSS_SELECTOR, ".rule-card .rc-name")
    ALT_RULE_DESC = (AppiumBy.CSS_SELECTOR, ".rule-card .rc-desc")
    ALT_RULE_SCORE = (AppiumBy.CSS_SELECTOR, ".rule-card .rc-score")

    # 标签
    ALT_TAG_OK = (AppiumBy.CSS_SELECTOR, ".tag.ok")
    ALT_TAG_BAD = (AppiumBy.CSS_SELECTOR, ".tag.bad")

    # 积分政策解读
    ALT_POLICY_LINK = (AppiumBy.CSS_SELECTOR, "a[href*='信誉统计']")

    # ============================================================
    # 页面状态判断
    # ============================================================

    def is_on_credit_detail_page(self, timeout: int = 10) -> bool:
        """判断是否在信誉明细页面"""
        return (
            self.is_element_present(self.ALT_PAGE_TITLE, timeout) or
            self.is_element_present(self.PAGE_TITLE, timeout)
        )

    def wait_for_credit_detail_page(self, timeout: int = 15):
        """等待信誉明细页面加载完成"""
        self.wait_for_element_visible(self.ALT_PAGE_TITLE, timeout)
        logger.info("信誉明细页面已加载")
        return self

    # ============================================================
    # 信息获取
    # ============================================================

    def get_company_name(self) -> str:
        """获取企业/运营人名称"""
        return self.get_text(self.ALT_COMPANY_NAME, timeout=5)

    def get_credit_score(self) -> int:
        """
        获取当前信誉积分

        Returns:
            int: 信誉积分值
        """
        try:
            text = self.get_text(self.ALT_SCORE_VALUE, timeout=5)
            return int(text.strip())
        except (ValueError, TypeError):
            logger.warning(f"无法解析信誉积分: {text}")
            return 0

    def get_total_plus(self) -> int:
        """获取累计加分"""
        try:
            text = self.get_text(self.ALT_TOTAL_PLUS, timeout=5)
            return int(text.strip().lstrip("+"))
        except (ValueError, TypeError):
            return 0

    def get_total_minus(self) -> int:
        """获取累计扣分"""
        try:
            text = self.get_text(self.ALT_TOTAL_MINUS, timeout=5)
            # 扣分显示为负值
            val = text.strip().lstrip("-")
            return int(val) if val else 0
        except (ValueError, TypeError):
            return 0

    def get_credit_level(self) -> str:
        """
        根据积分判断信誉等级

        积分规则 (来自原型文档):
            - 优秀: 800+
            - 良好: 600-799
            - 告警: 400-599
            - 限制: <400

        Returns:
            str: 优秀 / 良好 / 告警 / 限制
        """
        score = self.get_credit_score()
        if score >= 800:
            return "优秀"
        elif score >= 600:
            return "良好"
        elif score >= 400:
            return "告警"
        else:
            return "限制"

    def get_plus_rules(self) -> List[Dict[str, str]]:
        """
        获取加分项列表

        Returns:
            list[dict]: [{tag, name, description, score}]
        """
        return self._get_rules_by_section(is_plus=True)

    def get_minus_rules(self) -> List[Dict[str, str]]:
        """
        获取扣分项列表

        Returns:
            list[dict]: [{tag, name, description, score}]
        """
        return self._get_rules_by_section(is_plus=False)

    def _get_rules_by_section(self, is_plus: bool) -> List[Dict[str, str]]:
        """
        按章节获取规则卡片

        Args:
            is_plus: True=加分项, False=扣分项

        Returns:
            list[dict]: 规则列表
        """
        rules = []
        try:
            cards = self.find_elements(self.ALT_RULE_CARDS, timeout=5)
            for card in cards:
                try:
                    score_el = card.find_element(*(self.ALT_RULE_SCORE))
                    score_text = score_el.text.strip()
                    is_card_plus = score_text.startswith("+")

                    if is_card_plus != is_plus:
                        continue

                    rule = {"score": score_text}
                    try:
                        name_el = card.find_element(*(self.ALT_RULE_NAME))
                        rule["name"] = name_el.text.strip()
                    except Exception:
                        pass
                    try:
                        desc_el = card.find_element(*(self.ALT_RULE_DESC))
                        rule["description"] = desc_el.text.strip()
                    except Exception:
                        pass

                    rules.append(rule)
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"获取规则列表失败: {e}")

        return rules

    def verify_score_rules_displayed(self) -> bool:
        """
        验证积分规则是否正确展示

        检查点:
            - 加分项区域存在
            - 扣分项区域存在
            - 积分政策入口可点击

        Returns:
            bool: 验证通过
        """
        has_plus = len(self.find_elements(self.ALT_RULE_CARDS, timeout=5)) > 0
        has_policy = self.is_element_present(self.ALT_POLICY_LINK, timeout=3)

        if has_plus and has_policy:
            logger.info("积分规则展示验证通过")
            return True
        else:
            logger.warning(f"积分规则验证失败: plus={has_plus}, policy={has_policy}")
            return False

    def get_all_credit_info(self) -> Dict:
        """
        获取完整信誉信息

        Returns:
            dict: {company, score, level, total_plus, total_minus, plus_rules, minus_rules}
        """
        return {
            "company": self.get_company_name(),
            "score": self.get_credit_score(),
            "level": self.get_credit_level(),
            "total_plus": self.get_total_plus(),
            "total_minus": self.get_total_minus(),
            "plus_rules": self.get_plus_rules(),
            "minus_rules": self.get_minus_rules(),
        }

    # ============================================================
    # 导航
    # ============================================================

    def go_to_policy_page(self):
        """
        点击积分政策解读

        Returns:
            CreditStatsPage
        """
        try:
            self.click(self.ALT_POLICY_LINK)
            logger.info("进入积分政策解读页面")
        except Exception as e:
            logger.error(f"进入积分政策页面失败: {e}")
            raise
        return self

    def go_back_to_mine(self):
        """
        返回到"我的"页面

        Returns:
            MinePage
        """
        from pages.mine_page import MinePage
        try:
            self.click(self.ALT_BACK_BUTTON)
        except Exception:
            self.click(self.BACK_BUTTON)
        logger.info("从信誉明细返回我的页面")
        return MinePage(self.driver)
