# -*- coding: utf-8 -*-
"""
关联分析业务：饲料价与牛羊价的相关性、滞后关系、饲料涨价对利润的影响
计算用 pandas，结果可落库 input_correlation
"""
import datetime

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from model.alert import InputCorrelation
from model.price import PriceCategory, PriceData


def _daily_series(db: Session, category_id, region_id):
    """分类+地区的日均价序列（date 索引）"""
    rows = (
        db.query(PriceData.record_date, func.avg(PriceData.price))
        .filter(PriceData.category_id == category_id,
                PriceData.region_id == region_id)
        .group_by(PriceData.record_date)
        .order_by(PriceData.record_date)
        .all()
    )
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series({r[0]: float(r[1]) for r in rows}, dtype=float)
    s.index = pd.to_datetime(s.index)
    return s.sort_index()


def correlation(db: Session, livestock_category_id, input_category_id,
                region_id, max_lag=30):
    """
    饲料价与牛羊价相关性：
      - 零滞后皮尔逊相关系数
      - 在 [0, max_lag] 天内找使相关系数绝对值最大的滞后天数
    """
    livestock = _daily_series(db, livestock_category_id, region_id)
    feed = _daily_series(db, input_category_id, region_id)
    if len(livestock) < 10 or len(feed) < 10:
        return None

    # 对齐到共同日期，缺失日线性插值
    idx = livestock.index.union(feed.index)
    li = livestock.reindex(idx).interpolate()
    fe = feed.reindex(idx).interpolate()

    corr0 = li.corr(fe)

    best_lag, best_corr = 0, corr0
    for lag in range(1, max_lag + 1):
        c = li.corr(fe.shift(lag))       # 饲料价滞后 lag 天后与牛羊价的相关
        if pd.isna(c):
            continue
        if abs(c) > abs(best_corr):
            best_lag, best_corr = lag, c

    return {
        "correlation": round(float(corr0), 4),
        "best_lag_days": best_lag,
        "best_lag_correlation": round(float(best_corr), 4) if pd.notna(best_corr) else None,
        "sample_days": len(idx),
    }


def correlation_matrix(db: Session, region_id):
    """牲畜分类 x 饲料分类 的相关系数矩阵（热力图用）"""
    livestock_cats = db.query(PriceCategory) \
        .filter(PriceCategory.type == "livestock").all()
    feed_cats = db.query(PriceCategory) \
        .filter(PriceCategory.type == "feed").all()

    matrix, details = [], []
    for lc in livestock_cats:
        row = {"category_id": lc.id, "category_name": lc.name, "values": []}
        for fc in feed_cats:
            result = correlation(db, lc.id, fc.id, region_id, max_lag=0)
            value = result["correlation"] if result else None
            row["values"].append({"feed_id": fc.id, "feed_name": fc.name,
                                  "correlation": value})
            if result:
                details.append({
                    "livestock": lc.name, "feed": fc.name,
                    "correlation": result["correlation"],
                    "best_lag_days": result["best_lag_days"],
                })
        matrix.append(row)
    return {"matrix": matrix, "details": details}


def lag_analysis(db: Session, livestock_category_id, input_category_id, region_id,
                 max_lag=60):
    """滞后关系曲线：lag 从 0 到 max_lag 的相关系数序列"""
    livestock = _daily_series(db, livestock_category_id, region_id)
    feed = _daily_series(db, input_category_id, region_id)
    if len(livestock) < 10 or len(feed) < 10:
        return []

    idx = livestock.index.union(feed.index)
    li = livestock.reindex(idx).interpolate()
    fe = feed.reindex(idx).interpolate()

    curve = []
    for lag in range(0, max_lag + 1, 5):
        c = li.corr(fe.shift(lag))
        if pd.notna(c):
            curve.append({"lag_days": lag, "correlation": round(float(c), 4)})
    return curve


def cost_impact(db: Session, livestock_category_id, input_category_id, region_id,
                feed_ratio=0.6, daily_feed_amount=8.0, weight=500.0):
    """
    饲料涨价对利润的影响（敏感性分析）：
      饲料每涨 0.1 元/斤，一头 weight kg 牲畜的养殖成本增加 =
        0.1 * 2(kg/斤换算) * daily_feed_amount * feed_ratio * 养殖天数(按120天估)
    """
    feed = _daily_series(db, input_category_id, region_id)
    if feed.empty:
        return None
    current_feed_price = float(feed.iloc[-1])          # 最新饲料价 元/斤

    steps = []                                          # 敏感性表格
    for delta in (-0.2, -0.1, 0.0, 0.1, 0.2, 0.3):
        price = current_feed_price + delta
        extra_cost_per_day = delta * 2 * daily_feed_amount * feed_ratio
        steps.append({
            "feed_price_delta": delta,                  # 元/斤
            "feed_price": round(price, 2),
            "daily_cost_change": round(extra_cost_per_day, 2),      # 元/头/天
            "total_cost_change_120d": round(extra_cost_per_day * 120, 2),
            "breakeven_price_change": round(extra_cost_per_day * 120 / (weight * 2), 3),
        })
    return {
        "current_feed_price": round(current_feed_price, 2),
        "weight_kg": weight,
        "feed_ratio": feed_ratio,
        "daily_feed_amount": daily_feed_amount,
        "steps": steps,
    }


def save_correlation(db: Session, livestock_category_id, input_category_id,
                     region_id, result):
    """把相关性计算结果落库"""
    if not result:
        return
    row = InputCorrelation(
        livestock_category_id=livestock_category_id,
        input_category_id=input_category_id,
        region_id=region_id,
        correlation=result["correlation"],
        lag_days=result["best_lag_days"],
        calc_date=datetime.date.today(),
    )
    db.add(row)
    db.commit()
