# -*- coding: utf-8 -*-
"""
牧场相关模型：farm 牧场、livestock 存栏牲畜、cost_config 成本配置
"""
from datetime import datetime

from sqlalchemy import (JSON, BigInteger, Column, Date, DateTime, Numeric,
                        Integer, String, Text, UniqueConstraint)

from model.base import Base


class Farm(Base):
    """牧场表"""
    __tablename__ = "farm"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="牧场ID")
    name = Column(String(100), nullable=False, comment="牧场名称")
    owner_id = Column(Integer, nullable=False, comment="归属用户ID")
    region_id = Column(Integer, comment="所在地区ID")
    address = Column(String(200), comment="详细地址")
    cattle_count = Column(Integer, nullable=False, default=0, comment="牛存栏数")
    sheep_count = Column(Integer, nullable=False, default=0, comment="羊存栏数")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "region_id": self.region_id,
            "address": self.address,
            "cattle_count": self.cattle_count,
            "sheep_count": self.sheep_count,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class Livestock(Base):
    """存栏牲畜表"""
    __tablename__ = "livestock"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="牲畜ID")
    farm_id = Column(Integer, nullable=False, comment="牧场ID")
    category = Column(String(20), nullable=False, comment="cattle=牛 sheep=羊")
    breed_id = Column(Integer, comment="品种ID")
    ear_tag = Column(String(50), comment="耳标号")
    birth_date = Column(Date, comment="出生日期")
    weight = Column(Numeric(8, 2), comment="当前体重（kg）")
    status = Column(String(20), nullable=False, default="raising",
                    comment="raising=在养 sold=已出栏 dead=死亡")
    purchase_price = Column(Numeric(10, 2), comment="购入价（元/头）")
    purchase_date = Column(Date, comment="购入日期")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "category": self.category,
            "breed_id": self.breed_id,
            "ear_tag": self.ear_tag,
            "birth_date": str(self.birth_date) if self.birth_date else None,
            "weight": float(self.weight) if self.weight is not None else None,
            "status": self.status,
            "purchase_price": float(self.purchase_price) if self.purchase_price is not None else None,
            "purchase_date": str(self.purchase_date) if self.purchase_date else None,
            "remark": self.remark,
        }


class CostConfig(Base):
    """成本配置表：日饲料量、日增重等参数，用于利润计算"""
    __tablename__ = "cost_config"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="配置ID")
    farm_id = Column(Integer, nullable=False, comment="牧场ID")
    category = Column(String(20), nullable=False, comment="cattle=牛 sheep=羊")
    daily_feed_amount = Column(Numeric(8, 2), comment="日饲料量（kg/头）")
    daily_labor_cost = Column(Numeric(8, 2), comment="日人工成本（元/头）")
    daily_other_cost = Column(Numeric(8, 2), comment="日其他成本（元/头）")
    daily_gain = Column(Numeric(6, 3), comment="日增重（kg/头）")
    feed_detail = Column(JSON, comment='饲料配比，如 {"玉米":0.6,"豆粕":0.2,"麸皮":0.1,"苜蓿草":0.1}')
    effective_date = Column(Date, comment="生效日期")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "category": self.category,
            "daily_feed_amount": float(self.daily_feed_amount) if self.daily_feed_amount is not None else None,
            "daily_labor_cost": float(self.daily_labor_cost) if self.daily_labor_cost is not None else None,
            "daily_other_cost": float(self.daily_other_cost) if self.daily_other_cost is not None else None,
            "daily_gain": float(self.daily_gain) if self.daily_gain is not None else None,
            "feed_detail": self.feed_detail,
            "effective_date": str(self.effective_date) if self.effective_date else None,
        }
