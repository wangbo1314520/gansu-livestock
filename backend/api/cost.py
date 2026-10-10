# -*- coding: utf-8 -*-
"""
成本接口 /api/cost（家用版）：出栏利润、压栏利润、盈亏平衡价、参数管理
"""
from flask import Blueprint, request

import config
from model import SessionLocal
from service import cost_service
from utils.response import err, ok

cost_bp = Blueprint("cost", __name__, url_prefix="/api/cost")


def _home_only():
    """家用版功能开关"""
    return config.feature_enabled("cost")


@cost_bp.route("/calculate", methods=["POST"])
def calculate():
    """当前出栏利润计算
    body: {weight, current_price, total_cost, farm_id?, category?, region_id?}
    """
    if not _home_only():
        return err(403, "成本计算为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    for field in ("weight", "current_price", "total_cost"):
        if data.get(field) is None:
            return err(400, "缺少必填字段: %s" % field)
    db = SessionLocal()
    try:
        result = cost_service.calculate(
            db,
            weight=float(data["weight"]),
            current_price=float(data["current_price"]),
            total_cost=float(data["total_cost"]),
            farm_id=data.get("farm_id"),
            category=data.get("category", "cattle"),
            region_id=data.get("region_id"),
            include_sample=bool(data.get("include_sample", False)))
        return ok(result)
    finally:
        db.close()


@cost_bp.route("/delay", methods=["POST"])
def delay():
    """压栏 N 天利润对比
    body: {weight, days, predicted_price, current_price, farm_id?, category?, region_id?}
    """
    if not _home_only():
        return err(403, "成本计算为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    for field in ("weight", "days", "predicted_price", "current_price"):
        if data.get(field) is None:
            return err(400, "缺少必填字段: %s" % field)
    db = SessionLocal()
    try:
        result = cost_service.delay_calculate(
            db,
            weight=float(data["weight"]),
            days=int(data["days"]),
            predicted_price=float(data["predicted_price"]),
            current_price=float(data["current_price"]),
            farm_id=data.get("farm_id"),
            category=data.get("category", "cattle"),
            region_id=data.get("region_id"),
            include_sample=bool(data.get("include_sample", False)))
        return ok(result)
    finally:
        db.close()


@cost_bp.route("/breakeven", methods=["GET"])
def breakeven():
    """盈亏平衡价：total_cost / (weight*2)"""
    if not _home_only():
        return err(403, "成本计算为家用版功能，当前模式未开放")
    args = request.args
    if not args.get("total_cost") or not args.get("weight"):
        return err(400, "缺少 total_cost 或 weight")
    try:
        value = cost_service.calc_breakeven(float(args["total_cost"]),
                                            float(args["weight"]))
        return ok({"breakeven_price": value, "unit": "元/斤"})
    except ValueError as e:
        return err(400, str(e))


@cost_bp.route("/config", methods=["GET"])
def get_config():
    """获取成本参数"""
    if not _home_only():
        return err(403, "成本计算为家用版功能，当前模式未开放")
    args = request.args
    farm_id = int(args["farm_id"]) if args.get("farm_id") else 0
    db = SessionLocal()
    try:
        return ok(cost_service.get_config(db, farm_id,
                                          category=args.get("category", "cattle")))
    finally:
        db.close()


@cost_bp.route("/config/save", methods=["POST"])
def save_config():
    """保存成本参数
    body: {farm_id, category, daily_feed_amount?, daily_gain?, feed_detail?...}
    """
    if not _home_only():
        return err(403, "成本计算为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    if not data.get("farm_id"):
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        row_id = cost_service.save_config(
            db, int(data["farm_id"]), data.get("category", "cattle"), data)
        return ok({"id": row_id}, msg="参数已保存")
    finally:
        db.close()
