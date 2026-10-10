# -*- coding: utf-8 -*-
"""
平凉红牛指数数据入库：PingliangSpider.run() -> price_data（is_sample=0 真实数据）
映射：region 平凉市=9；category 活牛=1；source=index（新华·中国平凉红牛价格指数）
remark 记录指数点位与 S 级胴体价（爬虫输出已含）。
"""
import os
import sys

PROJECT_ROOT = r"E:\Program\gansu-livestock"
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))
os.chdir(os.path.join(PROJECT_ROOT, "backend"))

from model import SessionLocal                     # noqa: E402
from model.price import PriceCategory, PriceData, Region  # noqa: E402
from spider.pingliang_spider import PingliangSpider  # noqa: E402

REGION_NAME = "平凉市"
SOURCE = "index"


def main(max_reports=3):
    spider = PingliangSpider()
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
                record_date=r["date"], source=SOURCE).count()
            if exists:
                skipped += 1
                continue
            db.add(PriceData(
                region_id=region_id,
                category_id=cid,
                price=r["price"],
                unit="元/斤",
                source=SOURCE,
                source_detail=r["source_detail"],
                record_date=r["date"],
                is_sample=0,
                remark="%s（来源报告: %s）" % (
                    r.get("remark", ""), r["report_title"][:60]),
            ))
            inserted += 1
        db.commit()
        print("入库完成: 插入 %d 条, 跳过 %d 条（无映射/重复）" % (inserted, skipped))
        return inserted
    finally:
        db.close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
