# -*- coding: utf-8 -*-
"""
管理接口 /api/admin：用户管理、爬虫触发、爬虫日志、系统信息
"""
import os
import platform
import sys

from flask import Blueprint, request

from model import SessionLocal
from model.user import User
from utils import auth
from utils.response import err, ok, page_data

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

# 爬虫日志文件（spider 模块写入 data/ 目录）
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "data")


@admin_bp.route("/users", methods=["GET"])
@auth.role_required("admin")
def users():
    """用户列表"""
    args = request.args
    db = SessionLocal()
    try:
        page, page_size = int(args.get("page", 1)), int(args.get("page_size", 20))
        q = db.query(User)
        total = q.count()
        rows = q.order_by(User.id).offset((page - 1) * page_size).limit(page_size).all()
        return ok(page_data([u.to_dict() for u in rows], total, page, page_size))
    finally:
        db.close()


@admin_bp.route("/user/add", methods=["POST"])
@auth.role_required("admin")
def user_add():
    """新增用户"""
    data = request.get_json(silent=True) or {}
    for field in ("username", "password", "role"):
        if not data.get(field):
            return err(400, "缺少必填字段: %s" % field)
    if data["role"] not in ("admin", "editor", "viewer"):
        return err(400, "role 只能是 admin / editor / viewer")
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == data["username"]).first():
            return err(409, "用户名已存在")
        user = User(
            username=data["username"],
            password_hash=auth.hash_password(data["password"]),
            real_name=data.get("real_name"),
            phone=data.get("phone"),
            role=data["role"],
            farm_id=data.get("farm_id"),
        )
        db.add(user)
        db.commit()
        return ok({"id": user.id}, msg="用户已创建")
    finally:
        db.close()


@admin_bp.route("/spider/run", methods=["POST"])
@auth.role_required("admin", "editor")
def spider_run():
    """手动触发爬虫：body {spider: gov|feed}"""
    data = request.get_json(silent=True) or {}
    which = data.get("spider", "gov")
    if which not in ("gov", "feed", "all"):
        return err(400, "spider 只能是 gov / feed / all")
    # TODO: 阶段3 爬虫就位后在后台线程执行：
    #   from spider.gov_spider import GovSpider; GovSpider().run()
    #   from spider.feed_spider import FeedSpider; FeedSpider().run()
    return ok({"spider": which, "status": "accepted"},
              msg="已提交爬虫任务（爬虫实现接入后生效）")


@admin_bp.route("/spider/log", methods=["GET"])
@auth.role_required("admin", "editor")
def spider_log():
    """爬虫日志：读 data/spider_log.txt 最近若干行"""
    path = os.path.join(LOG_DIR, "spider_log.txt")
    if not os.path.exists(path):
        return ok({"exists": False, "lines": [], "message": "暂无爬虫日志"})
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        tail = request.args.get("tail", "100")
        return ok({"exists": True, "lines": [l.rstrip("\n") for l in lines[-int(tail):]]})
    except OSError as e:
        return err(500, "读取日志失败: %s" % e)


@admin_bp.route("/system/info", methods=["GET"])
@auth.role_required("admin")
def system_info():
    """系统信息"""
    import flask
    import sqlalchemy
    try:
        import pandas, numpy, statsmodels, sklearn
        versions = {
            "pandas": pandas.__version__,
            "numpy": numpy.__version__,
            "statsmodels": statsmodels.__version__,
            "scikit-learn": sklearn.__version__,
        }
    except ImportError as e:
        versions = {"error": str(e)}
    return ok({
        "app": "gansu-livestock",
        "python": sys.version.split()[0],
        "platform": "%s %s" % (platform.system(), platform.release()),
        "flask": flask.__version__,
        "sqlalchemy": sqlalchemy.__version__,
        "libs": versions,
    })
