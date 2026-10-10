# -*- coding: utf-8 -*-
"""
牧场业务（家用版）：牧场信息、存栏牲畜 CRUD、饲料库存与出入库
出入库联动：feed_record 记流水，feed_stock 增减库存
"""
import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from model.farm import Farm, Livestock
from model.ledger import FeedRecord, FeedStock


# ---------------- 牧场 ----------------

def get_farm_info(db: Session, farm_id):
    farm = db.query(Farm).get(farm_id)
    if not farm:
        return None
    info = farm.to_dict()
    # 实时统计在养数量（不依赖冗余字段）
    counts = dict(
        db.query(Livestock.category, func.count(Livestock.id))
        .filter(Livestock.farm_id == farm_id, Livestock.status == "raising")
        .group_by(Livestock.category).all()
    )
    info["cattle_count"] = counts.get("cattle", 0)
    info["sheep_count"] = counts.get("sheep", 0)
    return info


# ---------------- 存栏牲畜 ----------------

def list_livestock(db: Session, farm_id, category=None, status="raising",
                   page=1, page_size=50):
    q = db.query(Livestock).filter(Livestock.farm_id == farm_id)
    if category:
        q = q.filter(Livestock.category == category)
    if status:
        q = q.filter(Livestock.status == status)
    total = q.count()
    rows = (q.order_by(Livestock.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return [r.to_dict() for r in rows], total


# status 只允许这三个值；品种阶段（育肥/母羊等）用 breed 表的 stage 表达
LIVESTOCK_STATUS = ("raising", "sold", "dead")


def add_livestock(db: Session, farm_id, data: dict):
    """新增牲畜；支持 count 批量（同属性一次录入 N 头/只，耳标自动编号后缀）"""
    status = data.get("status", "raising")
    if status not in LIVESTOCK_STATUS:
        raise ValueError("status 只能是 %s（品种阶段请用 breed_id 表达，如'黄牛-育肥'）"
                         % "/".join(LIVESTOCK_STATUS))
    try:
        count = int(data.get("count", 1))
    except (TypeError, ValueError):
        raise ValueError("count 必须是整数")
    if not 1 <= count <= 500:
        raise ValueError("count 取值 1~500")
    rows = []
    for i in range(count):
        ear_tag = data.get("ear_tag")
        if ear_tag and count > 1:
            ear_tag = "%s-%d" % (ear_tag, i + 1)
        rows.append(Livestock(
            farm_id=farm_id,
            category=data["category"],
            breed_id=data.get("breed_id"),
            ear_tag=ear_tag,
            birth_date=data.get("birth_date"),
            weight=data.get("weight"),
            status=status,
            purchase_price=data.get("purchase_price"),
            purchase_date=data.get("purchase_date"),
            remark=data.get("remark"),
        ))
    db.add_all(rows)
    db.commit()
    return rows[-1].id


def update_livestock(db: Session, livestock_id, farm_id, data: dict):
    """只允许改自家牧场的牲畜；status 同样做枚举校验"""
    if data.get("status") and data["status"] not in LIVESTOCK_STATUS:
        raise ValueError("status 只能是 %s" % "/".join(LIVESTOCK_STATUS))
    row = db.query(Livestock).filter(
        Livestock.id == livestock_id, Livestock.farm_id == farm_id).first()
    if not row:
        return False
    for f in ("category", "breed_id", "ear_tag", "birth_date", "weight",
              "status", "purchase_price", "purchase_date", "remark"):
        if f in data and data[f] is not None:
            setattr(row, f, data[f])
    db.commit()
    return True


def delete_livestock(db: Session, livestock_id, farm_id):
    row = db.query(Livestock).filter(
        Livestock.id == livestock_id, Livestock.farm_id == farm_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


# ---------------- 饲料库存 ----------------

def list_feed_stock(db: Session, farm_id):
    """库存列表，附低于阈值标记"""
    rows = db.query(FeedStock).filter(FeedStock.farm_id == farm_id) \
        .order_by(FeedStock.id).all()
    items = []
    for r in rows:
        d = r.to_dict()
        d["warning"] = (
            d["warn_threshold"] is not None and d["quantity"] < d["warn_threshold"])
        items.append(d)
    return items


def _touch_stock(db: Session, farm_id, feed_name, delta, unit_price=None):
    """库存增减；无该饲料行则新建"""
    stock = db.query(FeedStock).filter(
        FeedStock.farm_id == farm_id, FeedStock.feed_name == feed_name).first()
    if not stock:
        stock = FeedStock(farm_id=farm_id, feed_name=feed_name,
                          quantity=0, unit="kg")
        db.add(stock)
    stock.quantity = (stock.quantity or 0) + delta
    if unit_price is not None and delta > 0:
        stock.unit_price = unit_price
    db.flush()
    return stock


def feed_in(db: Session, farm_id, feed_name, quantity, unit_price=None,
            supplier=None, record_date=None, remark=None):
    """饲料入库：记流水 + 加库存"""
    record = FeedRecord(
        farm_id=farm_id, feed_name=feed_name, type="in",
        quantity=quantity, unit_price=unit_price,
        total_price=round(quantity * unit_price, 2) if unit_price else None,
        record_date=record_date or datetime.date.today(),
        supplier=supplier, remark=remark,
    )
    db.add(record)
    stock = _touch_stock(db, farm_id, feed_name, quantity, unit_price)
    db.commit()
    return {"record_id": record.id, "stock_quantity": float(stock.quantity)}


def feed_out(db: Session, farm_id, feed_name, quantity,
             record_date=None, remark=None):
    """饲料出库（喂养消耗）：记流水 - 减库存，库存不足则报错"""
    stock = db.query(FeedStock).filter(
        FeedStock.farm_id == farm_id, FeedStock.feed_name == feed_name).first()
    current = float(stock.quantity) if stock else 0.0
    if current < quantity:
        raise ValueError("库存不足：%s 当前 %.2f kg，需出库 %.2f kg"
                         % (feed_name, current, quantity))
    record = FeedRecord(
        farm_id=farm_id, feed_name=feed_name, type="out",
        quantity=quantity, unit_price=stock.unit_price if stock else None,
        record_date=record_date or datetime.date.today(),
        remark=remark,
    )
    db.add(record)
    _touch_stock(db, farm_id, feed_name, -quantity)
    db.commit()
    return {"record_id": record.id, "stock_quantity": float(stock.quantity)}
