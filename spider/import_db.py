# -*- coding: utf-8 -*-
"""
入库脚本：把 data/clean/ 清洗后的 JSON 导入 MySQL price_data 表
把 region/category 名称换算成表里的 ID，异常值默认不导入。

用法（在 backend 目录下运行，或设置 PYTHONPATH=backend）：
  cd backend
  venv\Scripts\python.exe ..\spider\import_db.py ..\data\clean\gov_20261010_clean.json
"""
import json
import os
import sys

# 让 import_db 能找到 backend 下的 model 包
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "backend")
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)      # config.py 里如有相对路径以此为准

from model import SessionLocal                       # noqa: E402
from model.price import Breed, PriceCategory, PriceData, Region  # noqa: E402
from utils.logger import get_logger                  # noqa: E402

logger = get_logger("import_db")


def build_id_maps(db):
    """名称 -> ID 映射"""
    regions = {r.name: r.id for r in db.query(Region).all()}
    categories = {c.name: c.id for c in db.query(PriceCategory).all()}
    breeds = {b.name: b.id for b in db.query(Breed).all()}
    return regions, categories, breeds


def import_file(path: str, skip_outliers: bool = True):
    """导入一个清洗后的 JSON 文件"""
    with open(path, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if not rows:
        logger.info("文件为空: %s", path)
        return 0

    db = SessionLocal()
    try:
        regions, categories, breeds = build_id_maps(db)
        # 全省兜底：找不到具体市州时挂到甘肃省
        province_id = regions.get("甘肃省", 1)

        inserted, skipped = 0, 0
        for row in rows:
            if skip_outliers and row.get("is_outlier"):
                skipped += 1
                continue
            category_id = categories.get(row["category"])
            if not category_id:
                skipped += 1
                continue
            breed_id = breeds.get(row.get("breed")) if row.get("breed") else None

            db.add(PriceData(
                region_id=regions.get(row["region"], province_id),
                breed_id=breed_id,
                category_id=category_id,
                price=round(float(row["price"]), 2),
                unit="元/斤",
                source=row.get("source", "gov"),
                source_detail=row.get("source_detail"),
                record_date=row["date"],
            ))
            inserted += 1
            # 每500条提交一次，避免长事务
            if inserted % 500 == 0:
                db.commit()
        db.commit()
        logger.info("入库完成: 插入 %d 条，跳过 %d 条（文件=%s）",
                    inserted, skipped, path)
        return inserted
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python import_db.py <清洗后JSON路径>")
        sys.exit(1)
    count = import_file(sys.argv[1])
    print("共插入 %d 条" % count)
