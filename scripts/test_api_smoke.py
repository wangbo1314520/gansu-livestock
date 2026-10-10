# -*- coding: utf-8 -*-
"""
接口冒烟测试：登录拿 token 后逐个请求，记录 状态码/耗时/data 是否为空
输出 markdown 表格行，供 day-report.log 使用
"""
import json
import time

import requests

BASE = "http://127.0.0.1:5000/api"


def main():
    s = requests.Session()

    # 登录
    r = s.post(BASE + "/auth/login",
               json={"username": "admin", "password": "admin123"}, timeout=30)
    token = r.json()["data"]["token"]
    headers = {"Authorization": "Bearer " + token}
    print("| 接口 | 状态码 | 耗时ms | data空? |")
    print("|---|---|---|---|")

    cases = [
        ("GET", "/base/regions", None),
        ("GET", "/base/categories", None),
        ("GET", "/base/breeds", None),
        ("GET", "/price/list", {"page": 1, "page_size": 5}),
        ("GET", "/price/trend", {"category_id": 1, "region_id": 1,
                                 "start_date": "2024-01-01"}),
        ("GET", "/price/latest", None),
        ("GET", "/price/yoy", {"category_id": 1, "region_id": 1}),
        ("GET", "/price/compare", {"category_id": 1, "region_ids": "1,8,9"}),
        ("GET", "/price/feed/list", {"page": 1, "page_size": 5}),
        ("GET", "/price/feed/trend", {"feed_name": "玉米", "region_id": 1}),
        ("GET", "/predict/arima", {"category_id": 1, "region_id": 1, "days": 30}),
        ("GET", "/predict/arimax", {"category_id": 1, "region_id": 1, "days": 30}),
        ("GET", "/analysis/correlation", {"region_id": 1,
                                          "livestock_category_id": 1,
                                          "input_category_id": 5}),
        ("GET", "/analysis/cost-impact", {"livestock_category_id": 1,
                                          "input_category_id": 5, "region_id": 1}),
        ("GET", "/alert/rules", None),
        ("GET", "/alert/records", None),
        ("GET", "/health", None),
    ]
    for method, path, params in cases:
        url = BASE + path
        try:
            t0 = time.time()
            r = s.request(method, url, headers=headers, params=params, timeout=60)
            cost = int((time.time() - t0) * 1000)
            try:
                body = r.json()
                code = body.get("code")
                data = body.get("data")
                empty = "空" if data in (None, {}, [], "") else (
                    "空" if isinstance(data, dict) and data.get("list") == [] else "有数据")
            except Exception:
                code, empty = r.status_code, "非JSON"
            print("| %s | %s | %d | %s |" % (path, code, cost, empty))
        except Exception as e:
            print("| %s | EXC | - | %s |" % (path, str(e)[:40]))


if __name__ == "__main__":
    main()
