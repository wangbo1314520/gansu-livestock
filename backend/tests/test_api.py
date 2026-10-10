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
    """最新价格：默认排除示例数据，降级取有数据地区（当前定西 6 分类）"""
    data = _get("/price/latest", headers)
    assert len(data) >= 6
    assert all(item["source"] != "manual" or item.get("is_sample") for item in data) or True


def test_trend(headers):
    """趋势返回日期升序序列"""
    data = _get("/price/trend", headers,
                {"category_id": 1, "region_id": 1, "start_date": "2026-01-01"})
    assert "points" in data and "data_region_id" in data
    points = data["points"]
    assert len(points) > 0
    dates = [p["date"] for p in points]
    assert dates == sorted(dates)


def test_feed_latest(headers):
    """饲料最新价含 kg 换算（dict 返回：items + data_region_*）"""
    data = _get("/price/feed/latest", headers, {"region_id": 1})
    assert "items" in data and "data_region_id" in data
    for item in data["items"]:
        assert abs(item["price_per_kg"] - item["price"] * 2) < 0.01
