# -*- coding: utf-8 -*-
"""
预警接口 /api/alert：规则管理、记录查询、标记已读、测试推送
"""
from flask import Blueprint, request

import config
from model import SessionLocal
from service import alert_service
from utils import auth
from utils.response import err, ok, page_data

alert_bp = Blueprint("alert", __name__, url_prefix="/api/alert")


@alert_bp.route("/rules", methods=["GET"])
@auth.login_required
def rules():
    """规则列表"""
    args = request.args
    db = SessionLocal()
    try:
        data = alert_service.list_rules(
            db, enabled=int(args["enabled"]) if args.get("enabled") else None)
        return ok(data)
    finally:
        db.close()


@alert_bp.route("/rule/add", methods=["POST"])
@auth.role_required("admin", "editor")
def rule_add():
    """新增规则"""
    data = request.get_json(silent=True) or {}
    for field in ("name", "category_id", "rule_type"):
        if not data.get(field):
            return err(400, "缺少必填字段: %s" % field)
    db = SessionLocal()
    try:
        rule_id = alert_service.add_rule(db, data,
                                         user_id=auth.get_current_user_id())
        return ok({"id": rule_id}, msg="规则已创建")
    finally:
        db.close()


@alert_bp.route("/rule/update", methods=["PUT"])
@auth.role_required("admin", "editor")
def rule_update():
    """修改规则"""
    data = request.get_json(silent=True) or {}
    if not data.get("id"):
        return err(400, "缺少 id")
    db = SessionLocal()
    try:
        if not alert_service.update_rule(db, data["id"], data):
            return err(404, "规则不存在")
        return ok(msg="规则已更新")
    finally:
        db.close()


@alert_bp.route("/rule/delete", methods=["DELETE"])
@auth.role_required("admin", "editor")
def rule_delete():
    """删除规则"""
    rule_id = request.args.get("id")
    if not rule_id:
        return err(400, "缺少 id")
    db = SessionLocal()
    try:
        if not alert_service.delete_rule(db, int(rule_id)):
            return err(404, "规则不存在")
        return ok(msg="规则已删除")
    finally:
        db.close()


@alert_bp.route("/records", methods=["GET"])
@auth.login_required
def records():
    """预警记录分页"""
    args = request.args
    db = SessionLocal()
    try:
        items, total = alert_service.list_records(
            db,
            rule_id=int(args["rule_id"]) if args.get("rule_id") else None,
            is_read=int(args["is_read"]) if args.get("is_read") else None,
            page=int(args.get("page", 1)),
            page_size=int(args.get("page_size", 20)))
        return ok(page_data(items, total,
                            int(args.get("page", 1)), int(args.get("page_size", 20))))
    finally:
        db.close()


@alert_bp.route("/read", methods=["POST"])
@auth.login_required
def mark_read():
    """标记已读"""
    data = request.get_json(silent=True) or {}
    if not data.get("id"):
        return err(400, "缺少 id")
    db = SessionLocal()
    try:
        if not alert_service.mark_read(db, data["id"]):
            return err(404, "记录不存在")
        return ok(msg="已标记已读")
    finally:
        db.close()


@alert_bp.route("/push/test", methods=["POST"])
@auth.login_required
def push_test():
    """测试推送（家用版）"""
    if not config.feature_enabled("push"):
        return err(403, "当前模式未开启推送功能")
    # TODO: 接入微信推送/Bark 后实现真实发送
    return ok({"channel": "log", "status": "simulated"},
              msg="测试推送已触发（推送渠道未接入，仅记录日志）")
