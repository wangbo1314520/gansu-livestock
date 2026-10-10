# -*- coding: utf-8 -*-
"""
出栏建议业务（家用版，需求文档 8.5 规则）
输入：当前价 P、成本线 C、预测价 P_f
  P > C 且 P_f < P   -> 建议出栏（现在价好，往后要跌）
  P < C 且 P_f > P   -> 可压栏（现在亏，往后回暖）
  P < C 且 P_f < P   -> 尽快出栏止损（越养越亏）
  P > C 且 P_f > P   -> 可继续观察（还会涨）
"""
from sqlalchemy.orm import Session

from service import cost_service


def _decide(current_price, cost_line, predicted_price):
    """核心规则，返回 (action, reason)"""
    if current_price > cost_line and predicted_price < current_price:
        return "sell", (
            "当前价 %.2f 元/斤已高于成本线 %.2f 元/斤，每头约有利润；"
            "预测 %d 天后价格将回落到 %.2f 元/斤，建议趁高价出栏。" % (
                current_price, cost_line, 30, predicted_price))
    if current_price < cost_line and predicted_price > current_price:
        return "hold", (
            "当前价 %.2f 元/斤低于成本线 %.2f 元/斤，现在卖出每头亏损；"
            "预测 %d 天后回升到 %.2f 元/斤，膘情允许的话可以压栏等价。" % (
                current_price, cost_line, 30, predicted_price))
    if current_price < cost_line and predicted_price <= current_price:
        return "sell_now", (
            "当前价 %.2f 元/斤已低于成本线 %.2f 元/斤，且预测 %d 天后 %.2f 元/斤仍不回暖，"
            "继续喂养每天还要投入饲料钱，建议尽快出栏止损。" % (
                current_price, cost_line, 30, predicted_price))
    return "wait", (
        "当前价 %.2f 元/斤高于成本线 %.2f 元/斤，预测 %d 天后 %.2f 元/斤还有上涨空间，"
        "可以继续观察，涨势放缓时再出栏。" % (
            current_price, cost_line, 30, predicted_price))


ACTION_CN = {
    "sell": "建议出栏",
    "hold": "可压栏",
    "sell_now": "尽快出栏止损",
    "wait": "可继续观察",
}


def sell_advice(db: Session, weight, current_price, total_cost,
                predicted_price, farm_id=None, category="cattle", region_id=None,
                include_sample=False):
    """
    完整出栏建议：
      成本线 = total_cost / (weight*2)
      再用压栏模型算 30 天后的利润差，给家人一个直观的"每头多赚/少赚多少钱"
    """
    cost_line = cost_service.calc_breakeven(total_cost, weight)
    action, reason = _decide(current_price, cost_line, predicted_price)

    delay = cost_service.delay_calculate(
        db, weight=weight, days=30,
        predicted_price=predicted_price, current_price=current_price,
        farm_id=farm_id, category=category, region_id=region_id,
        include_sample=include_sample)
    profit_now = cost_service.calc_profit(weight, current_price, total_cost)

    return {
        "action": action,
        "action_cn": ACTION_CN[action],
        "reason": reason,
        "cost_line": cost_line,
        "current_price": current_price,
        "predicted_price_30d": predicted_price,
        "profit_now": profit_now,                       # 现在卖净利润
        "delay_30d": delay,                             # 压栏30天对比
        "rule_version": "v1（需求文档 8.5）",
    }


def advice_reason(db: Session, weight, current_price, total_cost,
                  predicted_price, farm_id=None, category="cattle", region_id=None,
                  include_sample=False):
    """建议理由（家用版 /api/advice/reason）"""
    result = sell_advice(db, weight, current_price, total_cost,
                         predicted_price, farm_id, category, region_id,
                         include_sample=include_sample)
    return {
        "action_cn": result["action_cn"],
        "reason": result["reason"],
        "numbers": {
            "成本线(元/斤)": result["cost_line"],
            "当前价(元/斤)": result["current_price"],
            "预测价(元/斤)": result["predicted_price_30d"],
            "现在卖利润(元/头)": result["profit_now"],
            "压栏30天差额(元/头)": result["delay_30d"]["diff"],
        },
    }
