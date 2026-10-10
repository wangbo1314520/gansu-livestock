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
    """通用参数解析：体重、当前价、累计成本、预测价"""
    for field in ("weight", "current_price", "total_cost", "predicted_price"):
        if source.get(field) is None:
            return None, "缺少必填参数: %s" % field
    return {
        "weight": float(source["weight"]),
        "current_price": float(source["current_price"]),
        "total_cost": float(source["total_cost"]),
        "predicted_price": float(source["predicted_price"]),
        "farm_id": source.get("farm_id"),
        "category": source.get("category", "cattle"),
        "region_id": source.get("region_id"),
    }, None


@advice_bp.route("/sell", methods=["GET"])
def sell():
    """出栏建议（需求文档 8.5 规则 + 压栏利润对比）"""
    if not config.feature_enabled("advice"):
        return err(403, "出栏建议为家用版功能，当前模式未开放")
    params, msg = _parse_params(request.args)
    if msg:
        return err(400, msg)
    db = SessionLocal()
    try:
        return ok(advice_service.sell_advice(db, **params))
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
        return ok(advice_service.advice_reason(db, **params))
    finally:
        db.close()
