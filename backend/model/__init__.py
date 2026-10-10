# -*- coding: utf-8 -*-
"""
模型包：统一导入所有 ORM 模型
保证 Base.metadata 能看到全部表（create_all_tables / 自动建表用）
"""
from model.base import Base, SessionLocal, engine, get_db  # noqa: F401
from model.price import Breed, PriceCategory, PriceData, Region  # noqa: F401
from model.user import LoginLog, User  # noqa: F401
from model.alert import (AlertRecord, AlertRule, InputCorrelation,  # noqa: F401
                         PredictResult)
from model.farm import CostConfig, Farm, Livestock  # noqa: F401
from model.ledger import FeedRecord, FeedStock, Ledger, PushLog  # noqa: F401
