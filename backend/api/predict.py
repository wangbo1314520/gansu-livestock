# -*- coding: utf-8 -*-
"""
预测接口 /api/predict：ARIMA、ARIMAX、LSTM（预留）、精度、重训
"""
from flask import Blueprint, request

import config
from model import SessionLocal
from service import predict_service
from utils import auth
from utils.response import err, ok

predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")


def _common_args():
    args = request.args
    return {
        "category_id": int(args["category_id"]) if args.get("category_id") else None,
        "region_id": int(args["region_id"]) if args.get("region_id") else None,
        "days": min(int(args.get("days", 30)), 90),   # 最多预测90天
        "feed_category_id": int(args["feed_category_id"]) if args.get("feed_category_id") else None,
    }


@predict_bp.route("/arima", methods=["GET"])
@auth.login_required
def arima():
    """ARIMA 预测（纯历史价格）"""
    p = _common_args()
    if not p["category_id"] or not p["region_id"]:
        return err(400, "缺少 category_id 或 region_id")
    db = SessionLocal()
    try:
        data = predict_service.run_predict(
            db, p["category_id"], p["region_id"],
            model="arima", days=p["days"])
        return ok(data)
    except ValueError as e:
        return err(400, str(e))
    finally:
        db.close()


@predict_bp.route("/arimax", methods=["GET"])
@auth.login_required
def arimax():
    """ARIMAX 预测（含饲料外生变量）"""
    p = _common_args()
    if not p["category_id"] or not p["region_id"]:
        return err(400, "缺少 category_id 或 region_id")
    db = SessionLocal()
    try:
        data = predict_service.run_predict(
            db, p["category_id"], p["region_id"],
            model="arimax", days=p["days"],
            feed_category_id=p["feed_category_id"])
        return ok(data)
    except ValueError as e:
        return err(400, str(e))
    finally:
        db.close()


@predict_bp.route("/lstm", methods=["GET"])
@auth.login_required
def lstm():
    """LSTM 预测：家用版预留开关"""
    if not config.feature_enabled("lstm"):
        return err(404, "LSTM 模型未启用（预留功能）")
    return err(501, "LSTM 模型尚未实现，当前版本请使用 arima / arimax")


@predict_bp.route("/accuracy", methods=["GET"])
@auth.login_required
def accuracy():
    """查询最近一次预测的精度指标 MAE/RMSE/MAPE"""
    args = request.args
    if not args.get("category_id") or not args.get("region_id"):
        return err(400, "缺少 category_id 或 region_id")
    db = SessionLocal()
    try:
        data = predict_service.get_accuracy(
            db, int(args["category_id"]), int(args["region_id"]),
            model=args.get("model"))
        if not data:
            return err(404, "暂无精度数据，请先执行一次预测")
        return ok(data)
    finally:
        db.close()


@predict_bp.route("/retrain", methods=["POST"])
@auth.role_required("admin", "editor")
def retrain():
    """重新训练：对全部牲畜分类重跑 ARIMAX"""
    db = SessionLocal()
    try:
        summary = predict_service.run_all_predict(db)
        return ok(summary, msg="重新训练完成")
    except Exception as e:
        db.rollback()
        return err(500, "训练失败: %s" % e)
    finally:
        db.close()
