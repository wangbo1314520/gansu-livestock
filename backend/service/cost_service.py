# -*- coding: utf-8 -*-
"""
成本计算业务（家用版核心，需求文档第7章）
单位约定：
  - 价格一律 元/斤（与价格库一致），计算时按 1kg = 2斤 换算
  - 体重、日增重、日饲料量用 kg
"""
from sqlalchemy.orm import Session

from model.farm import CostConfig, Farm
from model.price import PriceCategory, PriceData
from service.feed_service import latest_feed_prices

# 默认饲料配比（可在 cost_config.feed_detail 覆盖）
DEFAULT_FEED_DETAIL = {"玉米": 0.6, "豆粕": 0.2, "麸皮": 0.1, "苜蓿草": 0.1}


def calc_daily_feed_cost(feed_detail: dict, daily_feed_amount: float,
                         feed_prices: dict) -> float:
    """
    日饲料成本（元/头/天）
      feed_detail:       {"玉米":0.6,"豆粕":0.2,"麸皮":0.1,"苜蓿草":0.1} 配比
      daily_feed_amount: 日饲料量 kg
      feed_prices:       {"玉米":1.25,...} 元/斤（换算 x2 得 元/kg）
    """
    cost = 0.0
    for feed, ratio in feed_detail.items():
        price_per_jin = feed_prices.get(feed)
        if price_per_jin is None:
            raise ValueError("缺少饲料 %s 的价格" % feed)
        price_per_kg = price_per_jin * 2          # 元/斤 -> 元/kg
        cost += ratio * daily_feed_amount * price_per_kg
    return round(cost, 2)


def calc_profit(weight: float, current_price: float, total_cost: float) -> float:
    """出栏利润（元/头）：体重kg x 2(转斤) x 售价元/斤 - 累计成本"""
    revenue = weight * 2 * current_price
    return round(revenue - total_cost, 2)


def calc_breakeven(total_cost: float, weight: float) -> float:
    """盈亏平衡价（元/斤）：累计成本 / (体重kg x 2)"""
    if weight <= 0:
        raise ValueError("体重必须大于0")
    return round(total_cost / (weight * 2), 2)


def calc_delay_profit(weight, daily_gain, daily_feed_cost, daily_other_cost,
                      current_price, days, predicted_price) -> dict:
    """
    压栏 N 天后的利润对比（元/头）
      现在卖：weight x 2 x current_price
      压栏后卖：(weight + daily_gain x days) x 2 x predicted_price - 新增成本
    """
    future_weight = weight + daily_gain * days
    future_extra_cost = (daily_feed_cost + daily_other_cost) * days

    profit_now = calc_profit(weight, current_price, 0)          # 毛收入口径
    revenue_future = future_weight * 2 * predicted_price
    diff = revenue_future - future_extra_cost - weight * 2 * current_price

    return {
        "days": days,
        "future_weight": round(future_weight, 1),
        "future_extra_cost": round(future_extra_cost, 2),
        "revenue_now": round(weight * 2 * current_price, 2),
        "revenue_future": round(revenue_future, 2),
        "diff": round(diff, 2),                       # 压栏相对现在卖的差额（未扣历史成本）
        "better": diff > 0,
    }


# ------------------------------------------------------------------
# 组合服务：取实时饲料价 + 牧场成本配置，给出完整计算结果
# ------------------------------------------------------------------

def _feed_price_map(db: Session, region_id, include_sample=False):
    """最新饲料价 {名称: 元/斤}"""
    res = latest_feed_prices(db, region_id=region_id, include_sample=include_sample)
    return {i["feed_name"]: i["price"] for i in res["items"]}


def _load_config(db: Session, farm_id, category):
    """读牧场成本配置，没有则用默认值"""
    row = (db.query(CostConfig)
           .filter(CostConfig.farm_id == farm_id, CostConfig.category == category)
           .order_by(CostConfig.id.desc()).first())
    if row:
        return row.to_dict()
    return {
        "daily_feed_amount": 8.0,        # kg/天（牛），羊约2.5
        "daily_labor_cost": 2.0,         # 元/天
        "daily_other_cost": 1.0,         # 元/天
        "daily_gain": 1.2,               # kg/天（牛），羊约0.25
        "feed_detail": DEFAULT_FEED_DETAIL,
    }


def get_config(db: Session, farm_id, category="cattle"):
    """获取成本参数（供前端展示/修改）"""
    return _load_config(db, farm_id, category)


def save_config(db: Session, farm_id, category, data: dict):
    """保存成本参数（新增一行配置，保留历史）"""
    old = _load_config(db, farm_id, category)
    merged = {**old, **{k: v for k, v in data.items() if v is not None}}
    import datetime
    row = CostConfig(
        farm_id=farm_id,
        category=category,
        daily_feed_amount=merged.get("daily_feed_amount"),
        daily_labor_cost=merged.get("daily_labor_cost"),
        daily_other_cost=merged.get("daily_other_cost"),
        daily_gain=merged.get("daily_gain"),
        feed_detail=merged.get("feed_detail"),
        effective_date=datetime.date.today(),
    )
    db.add(row)
    db.commit()
    return row.id


def calculate(db: Session, weight, current_price, total_cost,
              farm_id=None, category="cattle", region_id=None, include_sample=False):
    """当前出栏利润 + 盈亏平衡价 + 日成本明细"""
    cfg = _load_config(db, farm_id, category) if farm_id else {
        "daily_feed_amount": 8.0, "daily_labor_cost": 2.0,
        "daily_other_cost": 1.0, "daily_gain": 1.2,
        "feed_detail": DEFAULT_FEED_DETAIL,
    }
    feed_prices = _feed_price_map(db, region_id, include_sample=include_sample)
    daily_feed = calc_daily_feed_cost(
        cfg["feed_detail"], cfg["daily_feed_amount"], feed_prices)

    return {
        "weight": weight,
        "current_price": current_price,
        "total_cost": total_cost,
        "revenue": round(weight * 2 * current_price, 2),
        "profit": calc_profit(weight, current_price, total_cost),
        "breakeven_price": calc_breakeven(total_cost, weight),
        "daily_feed_cost": daily_feed,
        "daily_total_cost": round(daily_feed + cfg["daily_labor_cost"] + cfg["daily_other_cost"], 2),
        "feed_prices": feed_prices,
        "config": cfg,
    }


def delay_calculate(db: Session, weight, days, predicted_price, current_price,
                    farm_id=None, category="cattle", region_id=None, include_sample=False):
    """压栏 N 天利润对比（需求文档 7.4）"""
    cfg = _load_config(db, farm_id, category) if farm_id else {
        "daily_feed_amount": 8.0, "daily_labor_cost": 2.0,
        "daily_other_cost": 1.0, "daily_gain": 1.2,
        "feed_detail": DEFAULT_FEED_DETAIL,
    }
    feed_prices = _feed_price_map(db, region_id, include_sample=include_sample)
    daily_feed = calc_daily_feed_cost(
        cfg["feed_detail"], cfg["daily_feed_amount"], feed_prices)

    return calc_delay_profit(
        weight=weight,
        daily_gain=cfg["daily_gain"],
        daily_feed_cost=daily_feed,
        daily_other_cost=cfg["daily_labor_cost"] + cfg["daily_other_cost"],
        current_price=current_price,
        days=days,
        predicted_price=predicted_price,
    )
