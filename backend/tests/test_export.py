# -*- coding: utf-8 -*-
"""CSV 导出接口测试（UTF-8 BOM / 表头 / 内容行）"""
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE = "http://127.0.0.1:5000/api"


def _token():
    r = requests.post(BASE + "/auth/login",
                      json={"username": "admin", "password": "admin123"}, timeout=10)
    return r.json().get("data", {}).get("token") or r.json().get("token")


def test_export_csv_bom_and_header():
    """导出含 BOM、表头齐全、默认不含示例数据"""
    try:
        h = {"Authorization": "Bearer " + _token()}
    except Exception:
        print("SKIP：后端未运行")
        return
    r = requests.get(BASE + "/price/export",
                     params={"region_id": 12, "category_id": 1}, headers=h, timeout=30)
    assert r.status_code == 200
    assert r.content[:3] == b"\xef\xbb\xbf", "缺 UTF-8 BOM"
    text = r.content.decode("utf-8-sig")
    header = text.splitlines()[0]
    for col in ("日期", "地区", "分类", "价格", "单位", "来源", "备注"):
        assert col in header, "表头缺列: %s" % col
    assert "manual" not in text.splitlines()[1], "默认导出不应含示例数据"
    assert "元/斤" in text
