# -*- coding: utf-8 -*-
"""
价格相关模型：region 地区、breed 品种、price_category 价格分类、price_data 价格数据
"""
from datetime import datetime

from sqlalchemy import (BigInteger, Column, Date, DateTime, Numeric, Index,
                        Integer, String, Text)

from model.base import Base


class Region(Base):
    """地区表：甘肃省(1, 省级) + 14 个市州"""
    __tablename__ = "region"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="地区ID")
    name = Column(String(50), nullable=False, unique=True, comment="地区名称")
    city_code = Column(String(20), comment="行政区划代码，如 620100")
    level = Column(Integer, nullable=False, default=2, comment="层级：1=省级 2=市州")
    parent_id = Column(Integer, nullable=False, default=0, comment="上级地区ID，省级为0")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")


class Breed(Base):
    """品种表：牛/羊品种"""
    __tablename__ = "breed"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="品种ID")
    name = Column(String(50), nullable=False, unique=True, comment="品种名称")
    category = Column(String(20), nullable=False, comment="类别：cattle=牛 sheep=羊")
    remark = Column(String(200), comment="备注，产地特点")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")


class PriceCategory(Base):
    """价格分类表：活牛/牛肉/活羊/羊肉/玉米/豆粕/麸皮/苜蓿草"""
    __tablename__ = "price_category"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(50), nullable=False, unique=True, comment="分类名称")
    type = Column(String(20), nullable=False, comment="类型：livestock=牲畜 feed=饲料")
    unit = Column(String(20), nullable=False, default="元/斤", comment="计价单位")
    sort_order = Column(Integer, nullable=False, default=0, comment="显示排序")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")


class PriceData(Base):
    """价格数据表：牛羊价格与饲料价格共用"""
    __tablename__ = "price_data"
    __table_args__ = (
        Index("idx_region_date", "region_id", "record_date"),
        Index("idx_category_date", "category_id", "record_date"),
        Index("idx_source", "source"),
        Index("idx_record_date", "record_date"),
        {"comment": "价格数据表（牛羊+饲料共用）"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    region_id = Column(Integer, nullable=False, comment="地区ID")
    breed_id = Column(Integer, comment="品种ID，饲料类为NULL")
    category_id = Column(Integer, nullable=False, comment="价格分类ID")
    price = Column(Numeric(10, 2), nullable=False, comment="价格（元/斤）")
    unit = Column(String(20), nullable=False, default="元/斤", comment="计价单位")
    source = Column(String(50), nullable=False, comment="gov政府 manual手工 dealer贩子 market市场 self自家")
    source_detail = Column(String(100), comment="来源明细")
    record_date = Column(Date, nullable=False, comment="价格所属日期")
    user_id = Column(Integer, comment="录入用户ID")
    farm_id = Column(Integer, comment="牧场ID")
    remark = Column(Text, comment="备注")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now,
                        onupdate=datetime.now, comment="更新时间")

    # 便于输出的属性
    @property
    def price_float(self):
        """价格转 float，序列化用"""
        return float(self.price) if self.price is not None else None
