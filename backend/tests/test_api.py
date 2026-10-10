# -*- coding: utf-8 -*-
"""核心接口冒烟测试：需要后端在线（127.0.0.1:5000）且数据库可用"""
import pytest
import requests

BASE = "http://127.0.0.1:5000/api"


@pytest.fixture(scope="module")
def token():
    r = requests.post(BASE + "/auth/login",
                      json={"username": "admin", "password": "admin123"},
                      timeout=30)
    assert r.status_code == 200, "登录失败，请确认后端已启动"
    return r.json()["data"]["token"]


@pytest.fixture(scope="module")
def headers(token):
    return {"Authorization": "Bearer " + token}


def _get(path, headers, params=None):
    r = requests.get(BASE + path, headers=headers, params=params, timeout=60)
    body = r.json()
    assert body["code"] == 200, "%s 返回 code=%s msg=%s" % (path, body.get("code"), body.get("msg"))
    return body["data"]


def test_login(token):
    """登录返回 JWT"""
    assert token and token.count(".") == 2


def test_regions(headers):
    """地区列表 15 条"""
    data = _get("/base/regions", headers)
    assert len(data) == 15


def test_latest(headers):
    """最新价格：8 个分类，均为省级兜底"""
    data = _get("/price/latest", headers)
    assert len(data) == 8
    assert all(item["region_id"] == 1 for item in data)


def test_trend(headers):
    """趋势返回日期升序序列"""
    data = _get("/price/trend", headers,
                {"category_id": 1, "region_id": 1, "start_date": "2026-01-01"})
    assert len(data) > 30
    dates = [p["date"] for p in data]
    assert dates == sorted(dates)


def test_feed_latest(headers):
    """饲料最新价含 kg 换算"""
    data = _get("/price/feed/latest", headers, {"region_id": 1})
    assert len(data) == 4
    for item in data:
        assert abs(item["price_per_kg"] - item["price"] * 2) < 0.01
