# -*- coding: utf-8 -*-
"""
饲料价格接口 /api/price/feed：列表、趋势、最新、新增
"""
from flask import Blueprint, request

from model import SessionLocal
from service import feed_service
from utils import auth
from utils.response import err, ok, page_data

feed_bp = Blueprint("feed", __name__, url_prefix="/api/price/feed")


@feed_bp.route("/list", methods=["GET"])
def feed_list():
    """饲料价格列表"""
    args = request.args
    db = SessionLocal()
    try:
        items, total = feed_service.list_feed_prices(
            db,
            feed_name=args.get("feed_name"),
            region_id=int(args["region_id"]) if args.get("region_id") else None,
            start_date=args.get("start_date"),
            end_date=args.get("end_date"),
            page=int(args.get("page", 1)),
            page_size=int(args.get("page_size", 20)),
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"))
        return ok(page_data(items, total,
                            int(args.get("page", 1)), int(args.get("page_size", 20))))
    finally:
        db.close()


@feed_bp.route("/trend", methods=["GET"])
def feed_trend():
    """饲料价格趋势：feed_name + region_id"""
    args = request.args
    if not args.get("feed_name") or not args.get("region_id"):
        return err(400, "缺少 feed_name 或 region_id")
    db = SessionLocal()
    try:
        data = feed_service.feed_trend(
            db, feed_name=args["feed_name"],
            region_id=int(args["region_id"]),
            start_date=args.get("start_date"), end_date=args.get("end_date"),
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"))
        return ok(data)
    finally:
        db.close()


@feed_bp.route("/latest", methods=["GET"])
def feed_latest():
    """最新饲料价格（四种饲料，附元/kg换算）"""
    args = request.args
    db = SessionLocal()
    try:
        data = feed_service.latest_feed_prices(
            db, region_id=int(args["region_id"]) if args.get("region_id") else None,
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"))
        return ok(data)
    finally:
        db.close()


@feed_bp.route("/add", methods=["POST"])
@auth.login_required
def feed_add():
    """新增饲料价格（自家采购价录入）"""
    data = request.get_json(silent=True) or {}
    for field in ("feed_name", "region_id", "price", "record_date"):
        if data.get(field) is None:
            return err(400, "缺少必填字段: %s" % field)
    db = SessionLocal()
    try:
        row_id = feed_service.add_feed_price(db, data,
                                             user_id=auth.get_current_user_id())
        return ok({"id": row_id}, msg="新增成功")
    except ValueError as e:
        return err(400, str(e))
    finally:
        db.close()
