# -*- coding: utf-8 -*-
"""
认证接口 /api/auth：登录、登出、用户信息、修改密码
"""
import datetime

from flask import Blueprint, g, request

from model import SessionLocal
from model.user import LoginLog, User
from utils import auth
from utils.response import err, ok

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    """用户名密码登录，返回 JWT"""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        return err(400, "用户名和密码不能为空")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            # 用户名不存在：不写 login_log，避免外键悬空的 user_id=0
            return err(401, "用户名或密码错误")
        if not auth.verify_password(password, user.password_hash):
            # 密码错误：用户存在，记录失败日志（user_id 为真实 id）
            db.add(LoginLog(user_id=user.id,
                            ip=request.remote_addr,
                            user_agent=request.headers.get("User-Agent", "")[:200],
                            success=0))
            db.commit()
            return err(401, "用户名或密码错误")
        if user.status != 1:
            return err(403, "账号已禁用")

        user.last_login = datetime.datetime.now()
        db.add(LoginLog(user_id=user.id,
                        ip=request.remote_addr,
                        user_agent=request.headers.get("User-Agent", "")[:200],
                        success=1))
        db.commit()

        token = auth.generate_token(user.id, user.username, user.role)
        return ok({"token": token, "user": user.to_dict()}, msg="登录成功")
    finally:
        db.close()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """登出：JWT 无状态，前端删除本地 token 即可"""
    return ok(msg="已登出")


@auth_bp.route("/info", methods=["GET"])
@auth.login_required
def info():
    """当前登录用户信息"""
    db = SessionLocal()
    try:
        user = db.query(User).get(g.user_id)
        if not user:
            return err(404, "用户不存在")
        return ok(user.to_dict())
    finally:
        db.close()


@auth_bp.route("/change-password", methods=["POST"])
@auth.login_required
def change_password():
    """修改密码：校验旧密码后更新哈希"""
    data = request.get_json(silent=True) or {}
    old_pwd = data.get("old_password") or ""
    new_pwd = data.get("new_password") or ""
    if len(new_pwd) < 6:
        return err(400, "新密码至少6位")

    db = SessionLocal()
    try:
        user = db.query(User).get(g.user_id)
        if not user:
            return err(404, "用户不存在")
        if not auth.verify_password(old_pwd, user.password_hash):
            return err(400, "旧密码错误")
        user.password_hash = auth.hash_password(new_pwd)
        db.commit()
        return ok(msg="密码已修改")
    finally:
        db.close()
