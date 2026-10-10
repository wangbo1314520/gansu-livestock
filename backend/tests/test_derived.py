# -*- coding: utf-8 -*-
"""反推数据标记正确性测试（source/derived，is_sample=0，remark 含系数）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import SessionLocal                          # noqa: E402
from model.price import PriceData                       # noqa: E402


def test_derived_marks():
    db = SessionLocal()
    try:
        rows = db.query(PriceData).filter(PriceData.source == "derived").all()
        assert rows, "库中无 derived 数据（先跑 derive_livestock_price.py）"
        for r in rows:
            # 反推数据三条硬约束：source=derived / is_sample=0 / remark 注明系数
            assert r.is_sample == 0, "反推数据 is_sample 必须为 0: id=%s" % r.id
            assert r.remark and "反推" in r.remark and "系数" in r.remark, \
                "remark 缺反推说明: id=%s" % r.id
            assert r.source_detail and "反推" in r.source_detail
            assert r.unit == "元/斤"
        # 只允许出现在活牛(1)/活羊(3)
        cats = {r.category_id for r in rows}
        assert cats <= {1, 3}, "derived 只应覆盖活牛/活羊: %s" % cats
    finally:
        db.close()


def test_derived_not_mix_gov_same_day():
    """同日同分类不应既有 gov 又有 derived（反推只补缺失周）"""
    from sqlalchemy import func
    db = SessionLocal()
    try:
        dup = db.query(PriceData.category_id, PriceData.record_date).filter(
            PriceData.source.in_(["gov", "derived"]),
            PriceData.region_id == 12,
        ).group_by(PriceData.category_id, PriceData.record_date).having(
            func.count(func.distinct(PriceData.source)) > 1).all()
        # 允许活牛同日 gov 与 index 并存（不同来源体系），但 gov/derived 同日重复属反推失误
        assert not dup, "gov/derived 同日重复: %s" % dup
    finally:
        db.close()
