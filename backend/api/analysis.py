# -*- coding: utf-8 -*-
"""
关联分析接口 /api/analysis：相关性、滞后、成本影响
"""
from flask import Blueprint, request

from model import SessionLocal
from service import analysis_service
from utils.response import err, ok

analysis_bp = Blueprint("analysis", __name__, url_prefix="/api/analysis")


@analysis_bp.route("/correlation", methods=["GET"])
def correlation():
    """
    饲料与牛羊价相关性：
      单对：livestock_category_id + input_category_id
      矩阵：只传 region_id（热力图用）
    """
    args = request.args
    if not args.get("region_id"):
        return err(400, "缺少 region_id")
    region_id = int(args["region_id"])
    db = SessionLocal()
    try:
        if args.get("livestock_category_id") and args.get("input_category_id"):
            result = analysis_service.correlation(
                db, int(args["livestock_category_id"]),
                int(args["input_category_id"]), region_id)
            if not result:
                return err(404, "数据不足，无法计算相关性")
            if args.get("save") == "1":
                analysis_service.save_correlation(
                    db, int(args["livestock_category_id"]),
                    int(args["input_category_id"]), region_id, result)
            return ok(result)
        return ok(analysis_service.correlation_matrix(db, region_id))
    finally:
        db.close()


@analysis_bp.route("/lag", methods=["GET"])
def lag():
    """滞后关系分析：相关系数随滞后天数的变化曲线"""
    args = request.args
    for field in ("livestock_category_id", "input_category_id", "region_id"):
        if not args.get(field):
            return err(400, "缺少 %s" % field)
    db = SessionLocal()
    try:
        curve = analysis_service.lag_analysis(
            db, int(args["livestock_category_id"]),
            int(args["input_category_id"]), int(args["region_id"]),
            max_lag=int(args.get("max_lag", 60)))
        return ok(curve)
    finally:
        db.close()


@analysis_bp.route("/cost-impact", methods=["GET"])
def cost_impact():
    """饲料涨价对利润影响（敏感性分析）"""
    args = request.args
    for field in ("livestock_category_id", "input_category_id", "region_id"):
        if not args.get(field):
            return err(400, "缺少 %s" % field)
    db = SessionLocal()
    try:
        result = analysis_service.cost_impact(
            db, int(args["livestock_category_id"]),
            int(args["input_category_id"]), int(args["region_id"]),
            feed_ratio=float(args.get("feed_ratio", 0.6)),
            daily_feed_amount=float(args.get("daily_feed_amount", 8.0)),
            weight=float(args.get("weight", 500.0)))
        if not result:
            return err(404, "饲料价格数据不足")
        return ok(result)
    finally:
        db.close()
