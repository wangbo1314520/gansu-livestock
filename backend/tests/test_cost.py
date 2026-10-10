# -*- coding: utf-8 -*-
"""成本计算逻辑测试：直接调 service 纯函数（不经 HTTP、不连库）
公式来源：需求文档第 7 章
"""
import pytest

from service import cost_service
from service.advice_service import _decide


class TestDailyFeedCost:
    def test_basic(self):
        """配比 x 日量(kg) x 价格(元/斤→元/kg)"""
        prices = {"玉米": 1.25, "豆粕": 2.0, "麸皮": 0.9, "苜蓿草": 1.5}
        detail = {"玉米": 0.6, "豆粕": 0.2, "麸皮": 0.1, "苜蓿草": 0.1}
        # 8kg/天：玉米0.6*8*2.5 + 豆粕0.2*8*4.0 + 麸皮0.1*8*1.8 + 苜蓿0.1*8*3.0
        # = 12.0 + 6.4 + 1.44 + 2.4 = 22.24 元/天
        assert cost_service.calc_daily_feed_cost(detail, 8.0, prices) == pytest.approx(22.24, abs=0.01)

    def test_missing_price_raises(self):
        with pytest.raises(ValueError):
            cost_service.calc_daily_feed_cost({"玉米": 1.0}, 8.0, {})


class TestProfitAndBreakeven:
    def test_profit(self):
        """500kg x 2 x 14.5 - 12000 = 14500 - 12000 = 2500"""
        assert cost_service.calc_profit(500, 14.5, 12000) == 2500.0

    def test_profit_negative(self):
        assert cost_service.calc_profit(500, 11.0, 12000) == -1000.0

    def test_breakeven(self):
        """12000 / (500*2) = 12 元/斤"""
        assert cost_service.calc_breakeven(12000, 500) == 12.0

    def test_breakeven_zero_weight(self):
        with pytest.raises(ValueError):
            cost_service.calc_breakeven(12000, 0)


class TestDelay:
    def test_delay_better(self):
        """涨价行情：压栏有利"""
        r = cost_service.calc_delay_profit(
            weight=500, daily_gain=1.2, daily_feed_cost=22.0,
            daily_other_cost=3.0, current_price=13.0,
            days=30, predicted_price=15.0)
        # 未来体重 536，收入 536*2*15=16080，新增成本 25*30=750，现在收入 13000
        assert r["future_weight"] == pytest.approx(536.0)
        assert r["diff"] == pytest.approx(16080 - 750 - 13000, abs=0.5)
        assert r["better"] is True

    def test_delay_worse(self):
        """跌价行情：压栏不利"""
        r = cost_service.calc_delay_profit(
            weight=500, daily_gain=0.5, daily_feed_cost=25.0,
            daily_other_cost=5.0, current_price=15.0,
            days=30, predicted_price=12.0)
        assert r["better"] is False


class TestAdviceRules:
    """需求文档 8.5 出栏建议规则矩阵"""

    def test_sell(self):
        action, _ = _decide(14.5, 12.0, 13.5)      # 价好且预测跌 -> 出栏
        assert action == "sell"

    def test_hold(self):
        action, _ = _decide(11.5, 12.0, 13.0)      # 价差且预测涨 -> 压栏
        assert action == "hold"

    def test_sell_now(self):
        action, _ = _decide(11.5, 12.0, 11.0)      # 价差且预测还跌 -> 止损
        assert action == "sell_now"

    def test_wait(self):
        action, _ = _decide(14.5, 12.0, 15.0)      # 价好且预测涨 -> 观察
        assert action == "wait"
