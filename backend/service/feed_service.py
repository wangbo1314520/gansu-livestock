# -*- coding: utf-8 -*-
"""
饲料价格业务：复用 price_data 表，分类 type='feed'
（玉米、豆粕、麸皮、苜蓿草）
"""
from sqlalchemy.orm import Session

from model.price import PriceCategory, PriceData, Region
from service.price_service import _apply_sample_filter, get_trend as _get_price_trend


def _feed_categories(db: Session):
    """全部饲料分类"""
    return db.query(PriceCategory).filter(PriceCategory.type == "feed") \
        .order_by(PriceCategory.sort_order).all()


def list_feed_prices(db: Session, feed_name=None, region_id=None,
                     start_date=None, end_date=None, page=1, page_size=20,
                     include_sample=False):
    """饲料价格分页列表"""
    q = (
        db.query(PriceData, Region.name, PriceCategory.name)
        .join(Region, PriceData.region_id == Region.id)
        .join(PriceCategory, PriceData.category_id == PriceCategory.id)
        .filter(PriceCategory.type == "feed")
    )
    q = _apply_sample_filter(q, include_sample)
    if feed_name:
        q = q.filter(PriceCategory.name == feed_name)
    if region_id:
        q = q.filter(PriceData.region_id == region_id)
    if start_date:
        q = q.filter(PriceData.record_date >= start_date)
    if end_date:
        q = q.filter(PriceData.record_date <= end_date)

    total = q.count()
    rows = (q.order_by(PriceData.record_date.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    items = [{
        "id": p.id,
        "feed_name": cat_name,
        "region_id": p.region_id,
        "region_name": region_name,
        "price": float(p.price),
        "unit": p.unit,
        "source": p.source,
        "record_date": str(p.record_date),
    } for p, region_name, cat_name in rows]
    return items, total


def feed_trend(db: Session, feed_name, region_id, start_date=None, end_date=None,
               include_sample=False):
    """单个饲料的价格趋势"""
    cat = db.query(PriceCategory).filter(
        PriceCategory.name == feed_name, PriceCategory.type == "feed").first()
    if not cat:
        return []
    return _get_price_trend(db, category_id=cat.id, region_id=region_id,
                            start_date=start_date, end_date=end_date,
                            include_sample=include_sample)


def latest_feed_prices(db: Session, region_id=None, include_sample=False):
    """最新饲料价格：四种饲料各取最近一条，外加 kg/斤 换算参考"""
    items = []
    for cat in _feed_categories(db):
        q = db.query(PriceData, Region.name) \
            .join(Region, PriceData.region_id == Region.id) \
            .filter(PriceData.category_id == cat.id)
        q = _apply_sample_filter(q, include_sample)
        if region_id:
            q = q.filter(PriceData.region_id == region_id)
        row = q.order_by(PriceData.record_date.desc()).first()
        if row:
            p, region_name = row
            price_per_jin = float(p.price)            # 元/斤
            items.append({
                "category_id": cat.id,
                "feed_name": cat.name,
                "region_id": p.region_id,
                "region_name": region_name,
                "price": price_per_jin,
                "price_per_kg": round(price_per_jin * 2, 2),   # 成本计算用 元/kg
                "unit": cat.unit,
                "record_date": str(p.record_date),
                "source": p.source,
            })
    return items


def add_feed_price(db: Session, data: dict, user_id=None):
    """新增饲料价格记录（手工录入自家采购价）"""
    cat = db.query(PriceCategory).filter(
        PriceCategory.name == data.get("feed_name"),
        PriceCategory.type == "feed").first()
    if not cat:
        raise ValueError("未知饲料: %s" % data.get("feed_name"))
    row = PriceData(
        region_id=data["region_id"],
        category_id=cat.id,
        price=data["price"],
        unit=cat.unit,
        source=data.get("source", "self"),
        source_detail=data.get("source_detail"),
        record_date=data["record_date"],
        user_id=user_id,
        farm_id=data.get("farm_id"),
        remark=data.get("remark"),
    )
    db.add(row)
    db.commit()
    return row.id
