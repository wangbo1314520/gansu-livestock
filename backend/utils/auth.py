# -*- coding: utf-8 -*-
"""
认证工具：bcrypt 密码哈希 + JWT 生成校验 + 登录装饰器
"""
from functools import wraps

import bcrypt
import jwt
from flask import request, g

import config
from utils.response import err, unauthorized

# 密码哈希 ------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """明文密码 -> bcrypt 哈希"""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("utf-8")


def verify_password(plain: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


# JWT ----------------------------------------------------------------------


def generate_token(user_id, username, role):
    """生成 JWT，payload 含用户 id / 用户名 / 角色"""
    import datetime
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=config.JWT_EXPIRE_HOURS),
        "iat": datetime.datetime.utcnow(),
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)


def verify_token(token: str):
    """校验 JWT，成功返回 payload 字典，失败返回 None"""
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# 装饰器 --------------------------------------------------------------------


def login_required(func):
    """登录校验装饰器：从 Authorization: Bearer <token> 解析用户写入 g"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return unauthorized()
        token = auth_header[7:]
        payload = verify_token(token)
        if payload is None:
            return unauthorized()
        g.user_id = payload.get("user_id")
        g.username = payload.get("username")
        g.role = payload.get("role")
        return func(*args, **kwargs)
    return wrapper


def role_required(*roles):
    """角色校验装饰器：role_required("admin") / role_required("admin","editor")"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return unauthorized()
            payload = verify_token(auth_header[7:])
            if payload is None:
                return unauthorized()
            if payload.get("role") not in roles:
                return err(403, "需要角色权限: %s" % "/".join(roles))
            g.user_id = payload.get("user_id")
            g.username = payload.get("username")
            g.role = payload.get("role")
            return func(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_id():
    """在已通过 login_required 的视图里取当前用户ID"""
    return getattr(g, "user_id", None)
