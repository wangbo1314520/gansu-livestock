# -*- coding: utf-8 -*-
"""
基础数据接口 /api/base：地区、品种、价格分类下拉数据
"""
from flask import Blueprint, request

from model import SessionLocal
from service import price_service
from utils.response import ok

base_bp = Blueprint("base", __name__, url_prefix="/api/base")


@base_bp.route("/regions", methods=["GET"])
def regions():
    """地区列表（甘肃省 + 14 市州）"""
    db = SessionLocal()
    try:
        data = price_service.get_base_data(db)
        return ok(data["regions"])
    finally:
        db.close()


@base_bp.route("/breeds", methods=["GET"])
def breeds():
    """品种列表（牛5 + 羊5 + 品种×阶段细分）
    可选参数：category=cattle|sheep 过滤类别；stage=bull|cow|calf|fattening|ram|ewe|lamb 过滤阶段
    """
    args = request.args
    db = SessionLocal()
    try:
        data = price_service.get_base_data(db)
        breeds = data["breeds"]
        if args.get("category"):
            breeds = [b for b in breeds if b["category"] == args["category"]]
        if args.get("stage"):
            breeds = [b for b in breeds if b["stage"] == args["stage"]]
        return ok(breeds)
    finally:
        db.close()


@base_bp.route("/categories", methods=["GET"])
def categories():
    """价格分类列表（4牲畜 + 4饲料）"""
    db = SessionLocal()
    try:
        data = price_service.get_base_data(db)
        return ok(data["categories"])
    finally:
        db.close()
