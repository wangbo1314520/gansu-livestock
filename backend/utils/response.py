# -*- coding: utf-8 -*-
"""
统一返回格式工具
所有接口返回 {"code":200,"msg":"success","data":{},"timestamp":...}
"""
import time
from flask import jsonify


def ok(data=None, msg="success"):
    """成功返回"""
    return jsonify({
        "code": 200,
        "msg": msg,
        "data": data if data is not None else {},
        "timestamp": int(time.time()),
    })


def err(code=400, msg="error", data=None):
    """失败返回"""
    return jsonify({
        "code": code,
        "msg": msg,
        "data": data if data is not None else {},
        "timestamp": int(time.time()),
    })


def page_data(items, total, page, page_size):
    """分页数据包装"""
    return {
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def not_found(msg="资源不存在"):
    return err(404, msg)


def unauthorized(msg="未登录或 token 已过期"):
    return err(401, msg)


def forbidden(msg="没有权限"):
    return err(403, msg)
