# -*- coding: utf-8 -*-
"""8 个分类全量 arimax 验证：记录 mape（<25% 算通过）与区间宽度"""
import json
import time

import requests

BASE = "http://127.0.0.1:5000/api"

NAMES = {1: "活牛", 2: "牛肉", 3: "活羊", 4: "羊肉",
         5: "玉米", 6: "豆粕", 7: "麸皮", 8: "苜蓿草"}


def main():
    s = requests.Session()
    r = s.post(BASE + "/auth/login",
               json={"username": "admin", "password": "admin123"}, timeout=30)
    headers = {"Authorization": "Bearer " + r.json()["data"]["token"]}

    print("| 分类 | HTTP | mape | 评级 | 通过(<25%) | 区间宽度均值 |")
    print("|---|---|---|---|---|---|")
    for cid, name in NAMES.items():
        try:
            t0 = time.time()
            r = s.get(BASE + "/predict/arimax",
                      headers=headers,
                      params={"category_id": cid, "region_id": 1, "days": 30},
                      timeout=120)
            body = r.json()
            if body.get("code") != 200:
                print("| %s(%d) | %s | - | - | FAIL | - |" % (name, cid, body.get("code")))
                continue
            d = body["data"]
            m = d["metrics"] or {}
            mape = m.get("mape")
            fc = d["forecast"]
            widths = [p["upper"] - p["lower"] for p in fc]
            avg_w = sum(widths) / len(widths) if widths else 0
            ok = "PASS" if (mape is not None and mape < 25) else "FAIL"
            print("| %s(%d) | 200 | %s | %s | %s | %.3f |" % (
                name, cid, mape, m.get("grade", "-"), ok, avg_w))
        except Exception as e:
            print("| %s(%d) | EXC | - | - | FAIL | %s |" % (name, cid, str(e)[:30]))


if __name__ == "__main__":
    main()
