# -*- coding: utf-8 -*-
"""
账本接口 /api/ledger（家用版）：收支 CRUD、汇总、利润统计
"""
from flask import Blueprint, request

import config
from model import SessionLocal
from service import ledger_service
from utils import auth
from utils.response import err, ok, page_data

ledger_bp = Blueprint("ledger", __name__, url_prefix="/api/ledger")


def _home_only():
    return config.feature_enabled("ledger")


@ledger_bp.route("/list", methods=["GET"])
@auth.login_required
def list_():
    """账目分页"""
    if not _home_only():
        return err(403, "家庭账本为家用版功能，当前模式未开放")
    args = request.args
    if not args.get("farm_id"):
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        items, total = ledger_service.list_records(
            db, int(args["farm_id"]),
            type_=args.get("type"), category=args.get("category"),
            start_date=args.get("start_date"), end_date=args.get("end_date"),
            page=int(args.get("page", 1)), page_size=int(args.get("page_size", 20)))
        return ok(page_data(items, total,
                            int(args.get("page", 1)), int(args.get("page_size", 20))))
    finally:
        db.close()


@ledger_bp.route("/add", methods=["POST"])
@auth.login_required
def add():
    """新增账目：body {farm_id, type, category, amount, trade_date}"""
    if not _home_only():
        return err(403, "家庭账本为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    for field in ("farm_id", "type", "category", "amount", "trade_date"):
        if data.get(field) is None:
            return err(400, "缺少必填字段: %s" % field)
    if data["type"] not in ("income", "expense"):
        return err(400, "type 只能是 income 或 expense")
    db = SessionLocal()
    try:
        row_id = ledger_service.add_record(db, int(data["farm_id"]), data)
        return ok({"id": row_id}, msg="记账成功")
    finally:
        db.close()


@ledger_bp.route("/update", methods=["PUT"])
@auth.login_required
def update():
    """修改账目"""
    if not _home_only():
        return err(403, "家庭账本为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    if not data.get("id") or not data.get("farm_id"):
        return err(400, "缺少 id 或 farm_id")
    db = SessionLocal()
    try:
        if not ledger_service.update_record(db, int(data["id"]), int(data["farm_id"]), data):
            return err(404, "账目不存在")
        return ok(msg="修改成功")
    finally:
        db.close()


@ledger_bp.route("/delete", methods=["DELETE"])
@auth.login_required
def delete():
    """删除账目"""
    if not _home_only():
        return err(403, "家庭账本为家用版功能，当前模式未开放")
    args = request.args
    if not args.get("id") or not args.get("farm_id"):
        return err(400, "缺少 id 或 farm_id")
    db = SessionLocal()
    try:
        if not ledger_service.delete_record(db, int(args["id"]), int(args["farm_id"])):
            return err(404, "账目不存在")
        return ok(msg="删除成功")
    finally:
        db.close()


@ledger_bp.route("/summary", methods=["GET"])
@auth.login_required
def summary():
    """收支汇总（可选 year 过滤）"""
    if not _home_only():
        return err(403, "家庭账本为家用版功能，当前模式未开放")
    args = request.args
    if not args.get("farm_id"):
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        return ok(ledger_service.summary(
            db, int(args["farm_id"]),
            year=int(args["year"]) if args.get("year") else None))
    finally:
        db.close()


@ledger_bp.route("/profit", methods=["GET"])
@auth.login_required
def profit():
    """按月利润统计"""
    if not _home_only():
        return err(403, "家庭账本为家用版功能，当前模式未开放")
    args = request.args
    if not args.get("farm_id"):
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        return ok(ledger_service.profit_trend(
            db, int(args["farm_id"]),
            year=int(args["year"]) if args.get("year") else None))
    finally:
        db.close()
