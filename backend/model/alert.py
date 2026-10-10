# -*- coding: utf-8 -*-
"""
预测与预警模型：predict_result 预测结果、alert_rule 预警规则、
alert_record 预警记录、input_correlation 关联分析
"""
from datetime import datetime

from sqlalchemy import (BigInteger, Column, Date, DateTime, Numeric, Index,
                        Integer, SmallInteger, String)

from model.base import Base


class PredictResult(Base):
    """预测结果表"""
    __tablename__ = "predict_result"
    __table_args__ = (
        Index("idx_category_region", "category_id", "region_id", "predict_date"),
        Index("idx_model", "model"),
        {"comment": "预测结果表"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    category_id = Column(Integer, nullable=False, comment="价格分类ID")
    region_id = Column(Integer, nullable=False, comment="地区ID")
    model = Column(String(20), nullable=False, comment="模型：arima arimax lstm")
    predict_date = Column(Date, nullable=False, comment="预测日期")
    predict_value = Column(Numeric(10, 2), nullable=False, comment="预测值（元/斤）")
    lower_bound = Column(Numeric(10, 2), comment="置信下界")
    upper_bound = Column(Numeric(10, 2), comment="置信上界")
    confidence = Column(Numeric(5, 2), nullable=False, default=95.00, comment="置信度（%）")
    mae = Column(Numeric(10, 4), comment="平均绝对误差")
    rmse = Column(Numeric(10, 4), comment="均方根误差")
    mape = Column(Numeric(10, 4), comment="平均绝对百分比误差（%）")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "region_id": self.region_id,
            "model": self.model,
            "predict_date": str(self.predict_date),
            "predict_value": float(self.predict_value) if self.predict_value else None,
            "lower_bound": float(self.lower_bound) if self.lower_bound is not None else None,
            "upper_bound": float(self.upper_bound) if self.upper_bound is not None else None,
            "confidence": float(self.confidence) if self.confidence else None,
            "mae": float(self.mae) if self.mae is not None else None,
            "rmse": float(self.rmse) if self.rmse is not None else None,
            "mape": float(self.mape) if self.mape is not None else None,
        }


class AlertRule(Base):
    """预警规则表"""
    __tablename__ = "alert_rule"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="规则ID")
    name = Column(String(100), nullable=False, comment="规则名称")
    category_id = Column(Integer, nullable=False, comment="价格分类ID")
    region_id = Column(Integer, comment="地区ID，NULL=全部地区")
    rule_type = Column(String(30), nullable=False,
                       comment="below_cost above_price continuous_rise continuous_fall feed_rise")
    threshold = Column(Numeric(10, 2), comment="阈值价格（元/斤）")
    continuous_days = Column(Integer, nullable=False, default=3, comment="连续天数")
    enabled = Column(SmallInteger, nullable=False, default=1, comment="1=启用 0=停用")
    user_id = Column(Integer, comment="创建用户ID")
    farm_id = Column(Integer, comment="牧场ID")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category_id": self.category_id,
            "region_id": self.region_id,
            "rule_type": self.rule_type,
            "threshold": float(self.threshold) if self.threshold is not None else None,
            "continuous_days": self.continuous_days,
            "enabled": self.enabled,
            "user_id": self.user_id,
            "farm_id": self.farm_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }


class AlertRecord(Base):
    """预警记录表"""
    __tablename__ = "alert_record"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    rule_id = Column(Integer, nullable=False, comment="触发规则ID")
    category_id = Column(Integer, comment="价格分类ID")
    region_id = Column(Integer, comment="地区ID")
    trigger_value = Column(Numeric(10, 2), comment="触发时价格")
    message = Column(String(500), comment="预警消息")
    trigger_time = Column(DateTime, nullable=False, default=datetime.now, comment="触发时间")
    is_read = Column(SmallInteger, nullable=False, default=0, comment="0=未读 1=已读")
    user_id = Column(Integer, comment="通知用户ID")
    push_status = Column(SmallInteger, nullable=False, default=0, comment="0=未推送 1=已推送 2=失败")

    def to_dict(self):
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "category_id": self.category_id,
            "region_id": self.region_id,
            "trigger_value": float(self.trigger_value) if self.trigger_value is not None else None,
            "message": self.message,
            "trigger_time": self.trigger_time.strftime("%Y-%m-%d %H:%M:%S") if self.trigger_time else None,
            "is_read": self.is_read,
            "user_id": self.user_id,
            "push_status": self.push_status,
        }


class InputCorrelation(Base):
    """关联分析表：饲料价与牛羊价的相关系数与滞后"""
    __tablename__ = "input_correlation"
    __table_args__ = (
        Index("idx_livestock_input", "livestock_category_id", "input_category_id"),
        Index("idx_calc_date", "calc_date"),
        {"comment": "投入品与牛羊价格关联分析表"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    livestock_category_id = Column(Integer, nullable=False, comment="牛羊价格分类ID")
    input_category_id = Column(Integer, nullable=False, comment="饲料价格分类ID")
    region_id = Column(Integer, comment="地区ID，NULL=全省")
    correlation = Column(Numeric(6, 4), comment="皮尔逊相关系数")
    lag_days = Column(Integer, comment="最优滞后天数")
    calc_date = Column(Date, comment="计算日期")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
