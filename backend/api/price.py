# -*- coding: utf-8 -*-
"""
牛羊价格接口 /api/price：CRUD、趋势、对比、最新、同比环比、导入导出
"""
import csv
import io

from flask import Blueprint, request, Response

from model import SessionLocal
from service import price_service
from utils import auth
from utils.response import err, ok, page_data

price_bp = Blueprint("price", __name__, url_prefix="/api/price")


def _parse_common_params():
    """解析通用查询参数"""
    args = request.args
    return {
        "region_id": int(args["region_id"]) if args.get("region_id") else None,
        "category_id": int(args["category_id"]) if args.get("category_id") else None,
        "breed_id": int(args["breed_id"]) if args.get("breed_id") else None,
        "source": args.get("source"),
        "start_date": args.get("start_date"),
        "end_date": args.get("end_date"),
        "page": int(args.get("page", 1)),
        "page_size": int(args.get("page_size", 20)),
        "include_sample": args.get("include_sample", "false").lower() in ("1", "true", "yes"),
    }


@price_bp.route("/list", methods=["GET"])
def price_list():
    """分页查询价格数据"""
    p = _parse_common_params()
    db = SessionLocal()
    try:
        items, total = price_service.query_prices(db, **p)
        return ok(page_data(items, total, p["page"], p["page_size"]))
    finally:
        db.close()


@price_bp.route("/trend", methods=["GET"])
def trend():
    """趋势数据：category_id + region_id 必填"""
    args = request.args
    if not args.get("category_id") or not args.get("region_id"):
        return err(400, "缺少 category_id 或 region_id")
    db = SessionLocal()
    try:
        data = price_service.get_trend(
            db,
            category_id=int(args["category_id"]),
            region_id=int(args["region_id"]),
            start_date=args.get("start_date"),
            end_date=args.get("end_date"),
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"),
        )
        return ok(data)
    finally:
        db.close()


@price_bp.route("/compare", methods=["GET"])
def compare():
    """地区对比：region_ids 逗号分隔"""
    args = request.args
    if not args.get("category_id") or not args.get("region_ids"):
        return err(400, "缺少 category_id 或 region_ids")
    region_ids = [int(x) for x in args["region_ids"].split(",") if x.strip()]
    db = SessionLocal()
    try:
        data = price_service.get_compare(
            db, category_id=int(args["category_id"]), region_ids=region_ids,
            start_date=args.get("start_date"), end_date=args.get("end_date"),
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"))
        return ok(data)
    finally:
        db.close()


@price_bp.route("/latest", methods=["GET"])
def latest():
    """最新价格：每分类最近一条"""
    args = request.args
    db = SessionLocal()
    try:
        data = price_service.get_latest(
            db,
            region_id=int(args["region_id"]) if args.get("region_id") else None,
            type_=args.get("type"),
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"),
        )
        return ok(data)
    finally:
        db.close()


@price_bp.route("/yoy", methods=["GET"])
def yoy():
    """同比环比"""
    args = request.args
    if not args.get("category_id") or not args.get("region_id"):
        return err(400, "缺少 category_id 或 region_id")
    db = SessionLocal()
    try:
        data = price_service.get_yoy(
            db, category_id=int(args["category_id"]),
            region_id=int(args["region_id"]),
            ref_date=args.get("ref_date"),
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"))
        return ok(data)
    finally:
        db.close()


@price_bp.route("/add", methods=["POST"])
@auth.role_required("admin", "editor")
def add():
    """新增价格记录"""
    data = request.get_json(silent=True) or {}
    for field in ("region_id", "category_id", "price", "record_date"):
        if data.get(field) is None:
            return err(400, "缺少必填字段: %s" % field)
    db = SessionLocal()
    try:
        row_id = price_service.add_price(db, data, user_id=auth.get_current_user_id())
        return ok({"id": row_id}, msg="新增成功")
    finally:
        db.close()


@price_bp.route("/update", methods=["PUT"])
@auth.role_required("admin", "editor")
def update():
    """修改价格记录"""
    data = request.get_json(silent=True) or {}
    if not data.get("id"):
        return err(400, "缺少 id")
    db = SessionLocal()
    try:
        if not price_service.update_price(db, data["id"], data):
            return err(404, "记录不存在")
        return ok(msg="修改成功")
    finally:
        db.close()


@price_bp.route("/delete", methods=["DELETE"])
@auth.role_required("admin", "editor")
def delete():
    """删除价格记录：id 从查询串取"""
    price_id = request.args.get("id")
    if not price_id:
        return err(400, "缺少 id")
    db = SessionLocal()
    try:
        if not price_service.delete_price(db, int(price_id)):
            return err(404, "记录不存在")
        return ok(msg="删除成功")
    finally:
        db.close()


@price_bp.route("/import", methods=["POST"])
@auth.role_required("admin", "editor")
def import_batch():
    """批量导入：JSON 数组"""
    data = request.get_json(silent=True)
    if not isinstance(data, list) or not data:
        return err(400, "请上传 JSON 数组")
    db = SessionLocal()
    try:
        ok_count, errors = price_service.import_prices(
            db, data, user_id=auth.get_current_user_id())
        return ok({"success": ok_count, "failed": len(errors), "errors": errors[:20]})
    finally:
        db.close()


@price_bp.route("/export", methods=["GET"])
def export():
    """导出 CSV（UTF-8 BOM，Excel 直接打开不乱码）"""
    args = request.args
    db = SessionLocal()
    try:
        rows = price_service.export_rows(
            db,
            region_id=int(args["region_id"]) if args.get("region_id") else None,
            category_id=int(args["category_id"]) if args.get("category_id") else None,
            start_date=args.get("start_date"),
            end_date=args.get("end_date"),
            include_sample=args.get("include_sample", "false").lower() in ("1", "true", "yes"))
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["日期", "地区", "分类", "品种", "价格", "单位", "来源", "来源明细", "备注"])
        for r in rows:
            writer.writerow([r["record_date"], r["region_name"], r["category_name"],
                             r["breed_name"] or "", r["price"], r["unit"],
                             r["source"], r["source_detail"] or "",
                             (r.get("remark") or "")[:120]])
        return Response(
            "\ufeff" + buf.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=price_export.csv"},
        )
    finally:
        db.close()
