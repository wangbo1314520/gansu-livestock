# -*- coding: utf-8 -*-
"""
定西爬虫数据入库：DingxiSpider.run() -> price_data（is_sample=0 真实数据）
映射：region 定西市=12；活牛1 牛肉2 活羊3 羊肉4 玉米5 豆粕6
"""
import os
import sys

PROJECT_ROOT = r"E:\Program\gansu-livestock"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
os.chdir(os.path.join(PROJECT_ROOT, "backend"))

from model import SessionLocal                     # noqa: E402
from model.price import PriceCategory, PriceData, Region  # noqa: E402
from spider.dingxi_spider import DingxiSpider      # noqa: E402

REGION_NAME = "定西市"
CATEGORY_MAP = {"活牛": None, "牛肉": None, "活羊": None,
                "羊肉": None, "玉米": None, "豆粕": None}


def main(max_reports=8):
    spider = DingxiSpider()
    records = spider.run(max_reports=max_reports)

    db = SessionLocal()
    try:
        region_id = db.query(Region).filter(Region.name == REGION_NAME).one().id
        cats = {c.name: c.id for c in db.query(PriceCategory).all()}

        inserted, skipped = 0, 0
        for r in records:
            cid = cats.get(r["category"])
            if not cid:
                skipped += 1
                continue
            # 同日同分类同来源幂等（重复执行不翻倍）
            exists = db.query(PriceData).filter_by(
                region_id=region_id, category_id=cid,
                record_date=r["date"], source="gov",
                source_detail=r["source_detail"]).count()
            if exists:
                skipped += 1
                continue
            db.add(PriceData(
                region_id=region_id,
                category_id=cid,
                price=r["price"],
                unit="元/斤",
                source="gov",
                source_detail=r["source_detail"],
                record_date=r["date"],
                is_sample=0,
                remark="来源报告: %s" % r["report_title"][:80],
            ))
            inserted += 1
        db.commit()
        print("入库完成: 插入 %d 条, 跳过 %d 条（无映射/重复）" % (inserted, skipped))
        return inserted
    finally:
        db.close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8)
