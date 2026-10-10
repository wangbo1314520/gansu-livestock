# -*- coding: utf-8 -*-
"""
家庭账本业务（家用版）：收支 CRUD、按月汇总、利润统计
"""
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from model.ledger import Ledger


def list_records(db: Session, farm_id, type_=None, category=None,
                 start_date=None, end_date=None, page=1, page_size=20):
    """账目分页查询"""
    q = db.query(Ledger).filter(Ledger.farm_id == farm_id)
    if type_:
        q = q.filter(Ledger.type == type_)
    if category:
        q = q.filter(Ledger.category == category)
    if start_date:
        q = q.filter(Ledger.trade_date >= start_date)
    if end_date:
        q = q.filter(Ledger.trade_date <= end_date)
    total = q.count()
    rows = (q.order_by(Ledger.trade_date.desc(), Ledger.id.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return [r.to_dict() for r in rows], total


def add_record(db: Session, farm_id, data: dict):
    row = Ledger(
        farm_id=farm_id,
        type=data["type"],
        category=data["category"],
        amount=data["amount"],
        livestock_id=data.get("livestock_id"),
        quantity=data.get("quantity", 1),
        unit_price=data.get("unit_price"),
        trade_date=data["trade_date"],
        counterparty=data.get("counterparty"),
        remark=data.get("remark"),
    )
    db.add(row)
    db.commit()
    return row.id


def update_record(db: Session, record_id, farm_id, data: dict):
    row = db.query(Ledger).filter(
        Ledger.id == record_id, Ledger.farm_id == farm_id).first()
    if not row:
        return False
    for f in ("type", "category", "amount", "quantity", "unit_price",
              "trade_date", "counterparty", "remark"):
        if f in data and data[f] is not None:
            setattr(row, f, data[f])
    db.commit()
    return True


def delete_record(db: Session, record_id, farm_id):
    row = db.query(Ledger).filter(
        Ledger.id == record_id, Ledger.farm_id == farm_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def summary(db: Session, farm_id, year=None):
    """收支汇总：总收入、总支出、净收益、分类明细"""
    q = db.query(
        Ledger.type,
        Ledger.category,
        func.sum(Ledger.amount),
    ).filter(Ledger.farm_id == farm_id)
    if year:
        q = q.filter(extract("year", Ledger.trade_date) == year)
    rows = q.group_by(Ledger.type, Ledger.category).all()

    income = expense = 0.0
    by_category = {"income": {}, "expense": {}}
    for type_, category, total in rows:
        total = float(total or 0)
        if type_ == "income":
            income += total
            by_category["income"][category] = round(total, 2)
        else:
            expense += total
            by_category["expense"][category] = round(total, 2)

    return {
        "year": year,
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "net_profit": round(income - expense, 2),
        "by_category": by_category,
    }


def profit_trend(db: Session, farm_id, year=None):
    """按月利润统计：[{month, income, expense, profit}]"""
    q = db.query(
        extract("month", Ledger.trade_date).label("month"),
        Ledger.type,
        func.sum(Ledger.amount),
    ).filter(Ledger.farm_id == farm_id)
    if year:
        q = q.filter(extract("year", Ledger.trade_date) == year)
    rows = q.group_by("month", Ledger.type).all()

    months = {m: {"income": 0.0, "expense": 0.0} for m in range(1, 13)}
    for month, type_, total in rows:
        months[int(month)][type_] = float(total or 0)

    return [
        {
            "month": m,
            "income": round(v["income"], 2),
            "expense": round(v["expense"], 2),
            "profit": round(v["income"] - v["expense"], 2),
        }
        for m, v in sorted(months.items())
    ]
