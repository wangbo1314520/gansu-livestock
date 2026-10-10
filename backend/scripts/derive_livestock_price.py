# -*- coding: utf-8 -*-
"""
活畜价格反推补全：由牛肉/羊肉价反推活牛/活羊缺失周的价格

背景：定西周报并非每周发布"主产省份活牛/活羊价格"，但牛肉/羊肉每周发布。
方法：用同日重叠周实测的 活畜价/肉价 平均比值作为系数，反推缺失周的活畜价。
标记：source='derived'（衍生数据，不与 gov 真实观测混合统计），is_sample=0，
      remark 注明反推来源与系数。

系数（2026-10-10 实测，定西 gov 数据同日重叠周平均）：
  活牛/牛肉 = 0.3888（12 周，取 0.39）
  活羊/羊肉 = 0.4224（10 周，取 0.42）
用法：
  cd backend
  set DB_PASSWORD=***
  venv\\Scripts\\python.exe scripts\\derive_livestock_price.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func                                    # noqa: E402
from model import SessionLocal                                 # noqa: E402
from model.price import PriceData                              # noqa: E402

REGION_ID = 12          # 定西市
# (活畜分类, 肉类分类, 实测平均系数)
DERIVE_PLAN = [
    (1, 2, 0.39),       # 活牛 <- 牛肉，系数 0.3888≈0.39
    (3, 4, 0.42),       # 活羊 <- 羊肉，系数 0.4224≈0.42
]
# 系数只用 gov 同日重叠记录实测得出（与脚本头部说明一致）


def recompute_ratio(db, live_cat, meat_cat):
    """gov 同日重叠周的 活畜/肉 平均比值（供核对，不直接用于反推）"""
    live = db.query(PriceData.record_date, PriceData.price).filter(
        PriceData.category_id == live_cat, PriceData.region_id == REGION_ID,
        PriceData.source == "gov").subquery()
    meat = db.query(PriceData.record_date, PriceData.price).filter(
        PriceData.category_id == meat_cat, PriceData.region_id == REGION_ID,
        PriceData.source == "gov").subquery()
    rows = db.query(live.c.price, meat.c.price).join(
        meat, live.c.record_date == meat.c.record_date).all()
    if not rows:
        return None, 0
    return sum(float(l) / float(m) for l, m in rows) / len(rows), len(rows)


def main():
    db = SessionLocal()
    try:
        for live_cat, meat_cat, coef in DERIVE_PLAN:
            actual, weeks = recompute_ratio(db, live_cat, meat_cat)
            print("分类%d<-分类%d 实测系数(重叠%d周): %s（脚本采用 %s）"
                  % (live_cat, meat_cat, weeks,
                     round(actual, 4) if actual else "-", coef))
            # 肉类各周 gov 价格
            meats = db.query(PriceData.record_date, PriceData.price).filter(
                PriceData.category_id == meat_cat, PriceData.region_id == REGION_ID,
                PriceData.source == "gov").all()
            # 活畜已有记录的日期（任意来源：gov 不重抓、derived 不重插）
            have = {r[0] for r in db.query(PriceData.record_date).filter(
                PriceData.category_id == live_cat,
                PriceData.region_id == REGION_ID).all()}
            remark = "由%s价反推，系数%.2f" % (
                "牛肉" if meat_cat == 2 else "羊肉", coef)
            inserted = 0
            for date, meat_price in meats:
                if date in have:
                    continue
                db.add(PriceData(
                    region_id=REGION_ID,
                    category_id=live_cat,
                    price=round(float(meat_price) * coef, 2),
                    unit="元/斤",
                    source="derived",
                    source_detail=remark,
                    record_date=date,
                    is_sample=0,
                    remark=remark,
                ))
                inserted += 1
            db.commit()
            print("  补入 %d 条 derived（活畜分类%d）" % (inserted, live_cat))
    finally:
        db.close()


if __name__ == "__main__":
    main()
