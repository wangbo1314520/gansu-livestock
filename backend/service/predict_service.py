# -*- coding: utf-8 -*-
"""
预测业务：组装数据 -> 调用 predict/ 模型包 -> 结果落库 predict_result
"""
import os
import sys
import datetime

from sqlalchemy.orm import Session

# 项目根目录（backend 的上一级）加入 sys.path，以便导入根级 predict 包
# 注意：本文件位于 <root>/backend/service/，需三层 dirname 才是根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from model.alert import PredictResult  # noqa: E402
from model.price import PriceCategory, PriceData, Region  # noqa: E402
from utils.logger import get_logger  # noqa: E402

logger = get_logger("predict_service")


def _load_series(db: Session, category_id, region_id):
    """从 price_data 取 (date, price) 序列，按日聚合均价"""
    from sqlalchemy import func
    rows = (
        db.query(PriceData.record_date, func.avg(PriceData.price))
        .filter(PriceData.category_id == category_id,
                PriceData.region_id == region_id)
        .group_by(PriceData.record_date)
        .order_by(PriceData.record_date)
        .all()
    )
    return [(str(r[0]), float(r[1])) for r in rows]


def _load_exog_series(db: Session, feed_category_id, region_id):
    """取外生变量（饲料价格）序列，与主序列对齐用"""
    from sqlalchemy import func
    rows = (
        db.query(PriceData.record_date, func.avg(PriceData.price))
        .filter(PriceData.category_id == feed_category_id,
                PriceData.region_id == region_id)
        .group_by(PriceData.record_date)
        .order_by(PriceData.record_date)
        .all()
    )
    return [(str(r[0]), float(r[1])) for r in rows]


def run_predict(db: Session, category_id, region_id, model="arimax", days=30,
                feed_category_id=None):
    """
    执行预测：
      model=arima  -> 纯历史价格 ARIMA
      model=arimax -> 带饲料外生变量的 SARIMAX
    返回 {history, forecast, metrics}
    """
    # 延迟导入：模型包依赖 pandas/statsmodels，导入较慢
    from predict.predictor import predict_series

    series = _load_series(db, category_id, region_id)
    if len(series) < 30:
        raise ValueError("历史数据不足30条（当前%d条），无法预测" % len(series))

    exog = None
    if model == "arimax":
        if feed_category_id is None:
            # 默认用玉米（id=5）作为外生变量
            feed_category_id = 5
        exog = _load_exog_series(db, feed_category_id, region_id)

    result = predict_series(series, exog=exog, model=model, days=days)

    # 结果落库
    today = datetime.date.today()
    for point in result["forecast"]:
        row = PredictResult(
            category_id=category_id,
            region_id=region_id,
            model=model,
            predict_date=datetime.datetime.strptime(point["date"], "%Y-%m-%d").date(),
            predict_value=round(point["value"], 2),
            lower_bound=round(point["lower"], 2) if point.get("lower") is not None else None,
            upper_bound=round(point["upper"], 2) if point.get("upper") is not None else None,
            confidence=95.0,
        )
        db.add(row)
    # 精度指标写在最近一条上，避免逐行冗余
    if result.get("metrics"):
        m = result["metrics"]
        for row in db.new:                      # 本次会话新增的行
            row.mae = m.get("mae")
            row.rmse = m.get("rmse")
            row.mape = m.get("mape")
    db.commit()
    logger.info("预测完成 model=%s category=%s region=%s days=%s",
                model, category_id, region_id, days)
    return result


def get_accuracy(db: Session, category_id, region_id, model=None):
    """查询已落库预测的精度指标"""
    q = db.query(PredictResult).filter(
        PredictResult.category_id == category_id,
        PredictResult.region_id == region_id)
    if model:
        q = q.filter(PredictResult.model == model)
    row = q.order_by(PredictResult.created_at.desc(), PredictResult.id.desc()).first()
    if not row or row.mae is None:
        return None
    return {"mae": float(row.mae), "rmse": float(row.rmse), "mape": float(row.mape)}


def run_all_predict(db: Session, days=30):
    """定时任务用：对所有牲畜分类 x 全省 跑一遍 ARIMAX"""
    categories = db.query(PriceCategory) \
        .filter(PriceCategory.type == "livestock").all()
    region = db.query(Region).filter(Region.level == 1).first()
    summary = []
    for cat in categories:
        try:
            result = run_predict(db, cat.id, region.id, model="arimax", days=days)
            summary.append({"category_id": cat.id, "name": cat.name,
                            "status": "ok", "points": len(result["forecast"])})
        except Exception as e:
            db.rollback()
            logger.error("分类%s预测失败: %s", cat.name, e)
            summary.append({"category_id": cat.id, "name": cat.name,
                            "status": "error", "message": str(e)})
    return summary
