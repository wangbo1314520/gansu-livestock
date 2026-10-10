# -*- coding: utf-8 -*-
"""
出栏建议接口 /api/advice（家用版）：建议 + 理由
"""
from flask import Blueprint, request

import config
from model import SessionLocal
from service import advice_service
from utils.response import err, ok

advice_bp = Blueprint("advice", __name__, url_prefix="/api/advice")


def _parse_params(source):
    """通用参数解析：体重、累计成本必填；
    current_price/predicted_price 可选（缺省时自动查最新价/跑预测）"""
    for field in ("weight", "total_cost"):
        if source.get(field) is None:
            return None, "缺少必填参数: %s" % field
    return {
        "weight": float(source["weight"]),
        "current_price": float(source["current_price"]) if source.get("current_price") is not None else None,
        "total_cost": float(source["total_cost"]),
        "predicted_price": float(source["predicted_price"]) if source.get("predicted_price") is not None else None,
        "farm_id": source.get("farm_id"),
        "category": source.get("category", "cattle"),
        "region_id": source.get("region_id"),
        "include_sample": str(source.get("include_sample", "false")).lower() in ("1", "true", "yes"),
    }, None


def _fill_auto_prices(db, params):
    """current_price/predicted_price 缺省时自动查（第七轮签名兼容修复）"""
    if params["current_price"] is None or params["predicted_price"] is None:
        from service import price_service
        category_id = 1 if params["category"] == "cattle" else 3
        region_id = int(params["region_id"] or 12)     # 默认定西（当前唯一真实周报源）
        if params["current_price"] is None:
            items = price_service.get_latest(db, region_id=region_id)
            hit = next((i for i in items if i["category_id"] == category_id), None)
            if not hit:
                raise ValueError("自动取价失败：该地区无 %s 最新价，请显式传 current_price"
                                 % params["category"])
            params["current_price"] = hit["price"]
        if params["predicted_price"] is None:
            try:
                from service import predict_service
                pred = predict_service.run_predict(
                    db, category_id=category_id, region_id=region_id,
                    days=30, model="arimax")
                fc = pred.get("forecast") or []
                params["predicted_price"] = round(
                    sum(p["value"] for p in fc) / len(fc), 2) if fc else None
            except Exception:
                params["predicted_price"] = None      # 预测不可用时退化为无预测
    return params


@advice_bp.route("/sell", methods=["GET"])
def sell():
    """出栏建议（需求文档 8.5 规则 + 压栏利润对比）
    current_price/predicted_price 可省略：自动取最新真实价/ARIMAX 预测"""
    if not config.feature_enabled("advice"):
        return err(403, "出栏建议为家用版功能，当前模式未开放")
    params, msg = _parse_params(request.args)
    if msg:
        return err(400, msg)
    db = SessionLocal()
    try:
        return ok(advice_service.sell_advice(db, **_fill_auto_prices(db, params)))
    except ValueError as e:
        return err(400, str(e))
    finally:
        db.close()


@advice_bp.route("/reason", methods=["GET"])
def reason():
    """建议理由（人话版，给家人看）"""
    if not config.feature_enabled("advice"):
        return err(403, "出栏建议为家用版功能，当前模式未开放")
    params, msg = _parse_params(request.args)
    if msg:
        return err(400, msg)
    db = SessionLocal()
    try:
        return ok(advice_service.advice_reason(db, **_fill_auto_prices(db, params)))
    except ValueError as e:
        return err(400, str(e))
    finally:
        db.close()
