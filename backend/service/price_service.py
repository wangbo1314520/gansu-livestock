# -*- coding: utf-8 -*-
"""
价格业务：查询、趋势、地区对比、最新价、同比环比、增删改、批量导入
"""
from datetime import date, datetime, timedelta

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from model.price import Breed, PriceCategory, PriceData, Region


def _apply_sample_filter(q, include_sample=False):
    """默认排除示例数据（is_sample=1）；include_sample=True 时不过滤"""
    if not include_sample:
        q = q.filter(PriceData.is_sample == 0)
    return q


def _row_to_dict(row):
    """查询结果行转字典（含地区名、分类名、品种名）"""
    d = {
        "id": row.id,
        "region_id": row.region_id,
        "region_name": row.region_name,
        "breed_id": row.breed_id,
        "breed_name": row.breed_name,
        "category_id": row.category_id,
        "category_name": row.category_name,
        "price": float(row.price),
        "unit": row.unit,
        "source": row.source,
        "source_detail": row.source_detail,
        "record_date": str(row.record_date),
        "remark": row.remark,
    }
    return d


def query_prices(db: Session, region_id=None, category_id=None, breed_id=None,
                 source=None, start_date=None, end_date=None,
                 page=1, page_size=20, include_sample=False):
    """分页查询价格数据，支持多条件筛选；默认只查真实数据"""
    q = (
        db.query(PriceData, Region.name, PriceCategory.name, Breed.name)
        .join(Region, PriceData.region_id == Region.id)
        .join(PriceCategory, PriceData.category_id == PriceCategory.id)
        .outerjoin(Breed, PriceData.breed_id == Breed.id)
    )
    q = _apply_sample_filter(q, include_sample)
    if region_id:
        q = q.filter(PriceData.region_id == region_id)
    if category_id:
        q = q.filter(PriceData.category_id == category_id)
    if breed_id:
        q = q.filter(PriceData.breed_id == breed_id)
    if source:
        q = q.filter(PriceData.source == source)
    if start_date:
        q = q.filter(PriceData.record_date >= start_date)
    if end_date:
        q = q.filter(PriceData.record_date <= end_date)

    total = q.count()
    rows = (
        q.order_by(PriceData.record_date.desc(), PriceData.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = []
    for price_data, region_name, category_name, breed_name in rows:
        price_data.region_name = region_name
        price_data.category_name = category_name
        price_data.breed_name = breed_name
        items.append(_row_to_dict(price_data))
    return items, total


def _region_with_data(db, category_id, exclude_region=None, include_sample=False):
    """动态查找该分类最近有数据的地区（不硬编码），返回 region_id 或 None"""
    q = db.query(
        PriceData.region_id, func.max(PriceData.record_date)
    ).filter(PriceData.category_id == category_id)
    q = _apply_sample_filter(q, include_sample)
    if exclude_region:
        q = q.filter(PriceData.region_id != exclude_region)
    row = q.group_by(PriceData.region_id).order_by(
        func.max(PriceData.record_date).desc()).first()
    return row[0] if row else None


def get_trend(db: Session, category_id, region_id, start_date=None, end_date=None,
              include_sample=False):
    """趋势数据：{points: [{date, price}], data_region_id, data_region_name, fallback}
    指定地区无数据时自动回退到该分类最近有数据的地区（数据源地区在返回中告知）"""
    def _query(rid):
        q = db.query(
            PriceData.record_date,
            func.avg(PriceData.price).label("avg_price"),
            func.group_concat(PriceData.source.distinct()).label("sources"),
        ).filter(
            PriceData.category_id == category_id,
            PriceData.region_id == rid,
        )
        q = _apply_sample_filter(q, include_sample)
        if start_date:
            q = q.filter(PriceData.record_date >= start_date)
        if end_date:
            q = q.filter(PriceData.record_date <= end_date)
        return q.group_by(PriceData.record_date).order_by(PriceData.record_date).all()

    rows = _query(region_id)
    data_region_id, fallback = region_id, False
    if not rows:
        alt = _region_with_data(db, category_id, exclude_region=region_id,
                                include_sample=include_sample)
        if alt:
            rows = _query(alt)
            data_region_id, fallback = alt, True
    region = db.query(Region).get(data_region_id) if data_region_id else None
    return {
        "points": [
            {
                "date": str(r.record_date),
                "price": round(float(r.avg_price), 2),
                # 该日期的数据来源集合：gov / derived / index / manual（多来源逗号分隔）
                "source": (r.sources or "").split(",")[0] if r.sources else None,
            }
            for r in rows
        ],
        "data_region_id": data_region_id,
        "data_region_name": region.name if region else None,
        "fallback": fallback,
    }


def get_compare(db: Session, category_id, region_ids, start_date=None, end_date=None,
                include_sample=False):
    """地区对比：多个地区同期价格对比 [{region_id, region_name, avg_price}]"""
    results = []
    for rid in region_ids:
        q = db.query(func.avg(PriceData.price)).filter(
            PriceData.category_id == category_id,
            PriceData.region_id == rid,
        )
        q = _apply_sample_filter(q, include_sample)
        if start_date:
            q = q.filter(PriceData.record_date >= start_date)
        if end_date:
            q = q.filter(PriceData.record_date <= end_date)
        avg = q.scalar()
        region = db.query(Region).get(rid)
        results.append({
            "region_id": rid,
            "region_name": region.name if region else str(rid),
            "avg_price": round(float(avg), 2) if avg is not None else None,
        })
    return results


def get_latest(db: Session, region_id=None, type_=None, include_sample=False):
    """最新价格：每个分类取最近一条（可选只看牲畜/饲料）
    地区规则：
      - 未传 region_id -> 默认省级（region_id=1）
      - 指定地区该分类无数据 -> 降级取该分类任意地区最新一条
    """
    q_cat = db.query(PriceCategory)
    if type_:
        q_cat = q_cat.filter(PriceCategory.type == type_)
    categories = q_cat.order_by(PriceCategory.sort_order).all()

    if not region_id:
        region_id = 1          # 省级兜底

    items = []
    for cat in categories:
        q = db.query(PriceData, Region.name).join(Region, PriceData.region_id == Region.id).filter(
            PriceData.category_id == cat.id,
            PriceData.region_id == region_id,
        )
        q = _apply_sample_filter(q, include_sample)
        row = q.order_by(PriceData.record_date.desc()).first()
        if not row:
            # 指定地区无数据：降级取该分类最新一条（不限地区，同样尊重示例过滤）
            fallback = (db.query(PriceData, Region.name)
                        .join(Region, PriceData.region_id == Region.id)
                        .filter(PriceData.category_id == cat.id))
            fallback = _apply_sample_filter(fallback, include_sample)
            row = fallback.order_by(PriceData.record_date.desc()).first()
        if row:
            price_data, region_name = row
            items.append({
                "category_id": cat.id,
                "category_name": cat.name,
                "type": cat.type,
                "unit": cat.unit,
                "region_id": price_data.region_id,
                "region_name": region_name,
                "price": float(price_data.price),
                "record_date": str(price_data.record_date),
                "source": price_data.source,
                "source_detail": price_data.source_detail,
            })
    return items


def get_yoy(db: Session, category_id, region_id, ref_date=None, include_sample=False):
    """同比环比：给定日期与上月、去年同期对比"""
    ref = datetime.strptime(ref_date, "%Y-%m-%d").date() if ref_date else date.today()

    def _avg(begin, end):
        q = db.query(func.avg(PriceData.price)).filter(
            PriceData.category_id == category_id,
            PriceData.region_id == region_id,
            PriceData.record_date >= begin,
            PriceData.record_date <= end,
        )
        q = _apply_sample_filter(q, include_sample)
        v = q.scalar()
        return float(v) if v is not None else None

    current = _avg(ref - timedelta(days=6), ref)                     # 近7天均价
    last_month = _avg(ref - timedelta(days=36), ref - timedelta(days=30))   # 上月同期
    last_year = _avg(ref - timedelta(days=372), ref - timedelta(days=365))  # 去年同期

    def _chg(cur, base):
        if cur is None or base in (None, 0):
            return None
        return round((cur - base) / base * 100, 2)   # 百分比变化

    return {
        "ref_date": str(ref),
        "current": round(current, 2) if current is not None else None,
        "last_month": round(last_month, 2) if last_month is not None else None,
        "last_year": round(last_year, 2) if last_year is not None else None,
        "mom_pct": _chg(current, last_month),   # 环比
        "yoy_pct": _chg(current, last_year),    # 同比
    }


def add_price(db: Session, data: dict, user_id=None):
    """新增一条价格记录"""
    row = PriceData(
        region_id=data["region_id"],
        breed_id=data.get("breed_id"),
        category_id=data["category_id"],
        price=data["price"],
        unit=data.get("unit", "元/斤"),
        source=data.get("source", "manual"),
        source_detail=data.get("source_detail"),
        record_date=data["record_date"],
        user_id=user_id,
        farm_id=data.get("farm_id"),
        remark=data.get("remark"),
    )
    db.add(row)
    db.commit()
    return row.id


def update_price(db: Session, price_id, data: dict):
    """修改价格记录（只更新传入的字段）"""
    row = db.query(PriceData).get(price_id)
    if not row:
        return False
    for field in ("region_id", "breed_id", "category_id", "price", "unit",
                  "source", "source_detail", "record_date", "remark"):
        if field in data and data[field] is not None:
            setattr(row, field, data[field])
    db.commit()
    return True


def delete_price(db: Session, price_id):
    """删除价格记录"""
    row = db.query(PriceData).get(price_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def import_prices(db: Session, rows: list, user_id=None):
    """批量导入：rows 为字典列表，返回 (成功数, 失败详情)"""
    ok_count, errors = 0, []
    for i, item in enumerate(rows):
        try:
            add_price(db, item, user_id=user_id)
            ok_count += 1
        except Exception as e:
            db.rollback()
            errors.append({"index": i, "error": str(e), "data": item})
    return ok_count, errors


def export_rows(db: Session, region_id=None, category_id=None,
                start_date=None, end_date=None, include_sample=False):
    """导出查询结果（返回字典列表，API 层转 CSV）"""
    items, _ = query_prices(db, region_id=region_id, category_id=category_id,
                            start_date=start_date, end_date=end_date,
                            page=1, page_size=100000, include_sample=include_sample)
    return items


def get_base_data(db: Session):
    """基础下拉数据：地区 + 分类 + 品种"""
    regions = [{"id": r.id, "name": r.name, "level": r.level}
               for r in db.query(Region).order_by(Region.id).all()]
    categories = [{"id": c.id, "name": c.name, "type": c.type, "unit": c.unit}
                  for c in db.query(PriceCategory).order_by(PriceCategory.sort_order).all()]
    breeds = [{"id": b.id, "name": b.name, "category": b.category, "stage": b.stage}
              for b in db.query(Breed).order_by(Breed.id).all()]
    return {"regions": regions, "categories": categories, "breeds": breeds}
