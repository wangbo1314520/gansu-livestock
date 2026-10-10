# -*- coding: utf-8 -*-
"""
账本相关模型：ledger 家庭账本、feed_stock 饲料库存、
feed_record 饲料出入库、push_log 推送日志
"""
from datetime import datetime

from sqlalchemy import (BigInteger, Column, Date, DateTime, Numeric, Index,
                        Integer, SmallInteger, String, Text, UniqueConstraint)

from model.base import Base


class Ledger(Base):
    """家庭账本表"""
    __tablename__ = "ledger"
    __table_args__ = (
        Index("idx_farm_date", "farm_id", "trade_date"),
        {"comment": "家庭账本表"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="账目ID")
    farm_id = Column(Integer, nullable=False, comment="牧场ID")
    type = Column(String(20), nullable=False, comment="income=收入 expense=支出")
    category = Column(String(30), nullable=False, comment="收支分类：卖牛 卖羊 购饲料 兽药")
    amount = Column(Numeric(10, 2), nullable=False, comment="金额（元）")
    livestock_id = Column(BigInteger, comment="关联牲畜ID")
    quantity = Column(Integer, nullable=False, default=1, comment="数量")
    unit_price = Column(Numeric(10, 2), comment="单价（元）")
    trade_date = Column(Date, nullable=False, comment="交易日期")
    counterparty = Column(String(100), comment="交易对方")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "type": self.type,
            "category": self.category,
            "amount": float(self.amount) if self.amount is not None else None,
            "livestock_id": self.livestock_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price) if self.unit_price is not None else None,
            "trade_date": str(self.trade_date),
            "counterparty": self.counterparty,
            "remark": self.remark,
        }


class FeedStock(Base):
    """饲料库存表：每种饲料每个牧场一行"""
    __tablename__ = "feed_stock"
    __table_args__ = (
        UniqueConstraint("farm_id", "feed_name", name="uk_farm_feed"),
        {"comment": "饲料库存表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="库存ID")
    farm_id = Column(Integer, nullable=False, comment="牧场ID")
    feed_name = Column(String(50), nullable=False, comment="玉米 豆粕 麸皮 苜蓿草")
    quantity = Column(Numeric(10, 2), nullable=False, default=0, comment="当前库存（kg）")
    unit = Column(String(20), nullable=False, default="kg", comment="库存单位")
    unit_price = Column(Numeric(8, 2), comment="最近入库单价（元/kg）")
    warn_threshold = Column(Numeric(10, 2), comment="库存预警阈值（kg）")
    updated_at = Column(DateTime, nullable=False, default=datetime.now,
                        onupdate=datetime.now, comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "feed_name": self.feed_name,
            "quantity": float(self.quantity) if self.quantity is not None else 0.0,
            "unit": self.unit,
            "unit_price": float(self.unit_price) if self.unit_price is not None else None,
            "warn_threshold": float(self.warn_threshold) if self.warn_threshold is not None else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }


class FeedRecord(Base):
    """饲料出入库记录表"""
    __tablename__ = "feed_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    farm_id = Column(Integer, nullable=False, comment="牧场ID")
    feed_name = Column(String(50), nullable=False, comment="饲料名称")
    type = Column(String(10), nullable=False, comment="in=入库 out=出库")
    quantity = Column(Numeric(10, 2), nullable=False, comment="数量（kg）")
    unit_price = Column(Numeric(8, 2), comment="单价（元/kg）")
    total_price = Column(Numeric(10, 2), comment="总金额（元）")
    record_date = Column(Date, nullable=False, comment="记录日期")
    supplier = Column(String(100), comment="供应商")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "feed_name": self.feed_name,
            "type": self.type,
            "quantity": float(self.quantity) if self.quantity is not None else None,
            "unit_price": float(self.unit_price) if self.unit_price is not None else None,
            "total_price": float(self.total_price) if self.total_price is not None else None,
            "record_date": str(self.record_date),
            "supplier": self.supplier,
            "remark": self.remark,
        }


class PushLog(Base):
    """推送日志表：预警消息推送记录"""
    __tablename__ = "push_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="推送ID")
    user_id = Column(Integer, nullable=False, comment="接收用户ID")
    channel = Column(String(20), comment="wechat bark sms")
    title = Column(String(200), comment="推送标题")
    content = Column(Text, comment="推送内容")
    send_time = Column(DateTime, nullable=False, default=datetime.now, comment="发送时间")
    status = Column(SmallInteger, nullable=False, default=0, comment="0=待发送 1=成功 2=失败")
