# -*- coding: utf-8 -*-
"""
牧场接口 /api/farm（家用版）：牧场信息、存栏管理、饲料出入库
"""
from flask import Blueprint, g, request

import config
from model import SessionLocal
from service import farm_service
from utils import auth
from utils.response import err, ok, page_data

farm_bp = Blueprint("farm", __name__, url_prefix="/api/farm")


def _home_only():
    return config.feature_enabled("farm")


def _current_farm_id():
    """当前用户关联的牧场ID（user.farm_id），家用版单牧场简化处理"""
    return getattr(g, "farm_id", None)


@farm_bp.route("/info", methods=["GET"])
@auth.login_required
def info():
    """牧场信息 + 实时存栏统计"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    farm_id = int(request.args.get("farm_id") or 0) or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        data = farm_service.get_farm_info(db, farm_id)
        if not data:
            return err(404, "牧场不存在")
        return ok(data)
    finally:
        db.close()


@farm_bp.route("/livestock/list", methods=["GET"])
@auth.login_required
def livestock_list():
    """存栏列表"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    args = request.args
    farm_id = int(args.get("farm_id") or 0) or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        items, total = farm_service.list_livestock(
            db, farm_id,
            category=args.get("category"),
            status=args.get("status", "raising"),
            page=int(args.get("page", 1)), page_size=int(args.get("page_size", 50)))
        return ok(page_data(items, total,
                            int(args.get("page", 1)), int(args.get("page_size", 50))))
    finally:
        db.close()


@farm_bp.route("/livestock/add", methods=["POST"])
@auth.login_required
def livestock_add():
    """新增牲畜"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    if not data.get("category"):
        return err(400, "缺少 category（cattle/sheep）")
    farm_id = data.get("farm_id") or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        row_id = farm_service.add_livestock(db, int(farm_id), data)
        return ok({"id": row_id}, msg="新增成功")
    finally:
        db.close()


@farm_bp.route("/livestock/update", methods=["PUT"])
@auth.login_required
def livestock_update():
    """修改牲畜信息（体重、状态等）"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    if not data.get("id"):
        return err(400, "缺少 id")
    farm_id = data.get("farm_id") or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        if not farm_service.update_livestock(db, int(data["id"]), int(farm_id), data):
            return err(404, "牲畜不存在")
        return ok(msg="修改成功")
    finally:
        db.close()


@farm_bp.route("/livestock/delete", methods=["DELETE"])
@auth.login_required
def livestock_delete():
    """删除牲畜记录"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    livestock_id = request.args.get("id")
    if not livestock_id:
        return err(400, "缺少 id")
    farm_id = int(request.args.get("farm_id") or 0) or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        if not farm_service.delete_livestock(db, int(livestock_id), int(farm_id)):
            return err(404, "牲畜不存在")
        return ok(msg="删除成功")
    finally:
        db.close()


@farm_bp.route("/feed/list", methods=["GET"])
@auth.login_required
def feed_list():
    """饲料库存（附低于阈值预警标记）"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    args = request.args
    farm_id = int(args.get("farm_id") or 0) or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        return ok(farm_service.list_feed_stock(db, int(farm_id)))
    finally:
        db.close()


@farm_bp.route("/feed/in", methods=["POST"])
@auth.login_required
def feed_in():
    """饲料入库：body {feed_name, quantity, unit_price?, supplier?}"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    for field in ("feed_name", "quantity"):
        if data.get(field) is None:
            return err(400, "缺少必填字段: %s" % field)
    farm_id = data.get("farm_id") or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        result = farm_service.feed_in(
            db, int(farm_id), data["feed_name"], float(data["quantity"]),
            unit_price=float(data["unit_price"]) if data.get("unit_price") else None,
            supplier=data.get("supplier"))
        return ok(result, msg="入库成功")
    finally:
        db.close()


@farm_bp.route("/feed/out", methods=["POST"])
@auth.login_required
def feed_out():
    """饲料出库：body {feed_name, quantity}"""
    if not _home_only():
        return err(403, "牧场管理为家用版功能，当前模式未开放")
    data = request.get_json(silent=True) or {}
    for field in ("feed_name", "quantity"):
        if data.get(field) is None:
            return err(400, "缺少必填字段: %s" % field)
    farm_id = data.get("farm_id") or _current_farm_id()
    if not farm_id:
        return err(400, "缺少 farm_id")
    db = SessionLocal()
    try:
        result = farm_service.feed_out(db, int(farm_id), data["feed_name"],
                                       float(data["quantity"]))
        return ok(result, msg="出库成功")
    except ValueError as e:
        return err(400, str(e))
    finally:
        db.close()
