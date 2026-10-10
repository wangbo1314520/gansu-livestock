# -*- coding: utf-8 -*-
"""
SQLAlchemy 基础：引擎、会话工厂、Base 声明基类
连接配置来自 config.DB_URI，惰性连接，只有真正执行 SQL 才会连数据库
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import config

# pool_pre_ping 防止 MySQL 8 小时断连；pool_recycle 定期回收连接
engine = create_engine(
    config.DB_URI,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,   # commit 后对象仍可访问属性，方便序列化
)

Base = declarative_base()


def get_db():
    """Flask 请求级数据库会话：视图里 with 或生成器使用，请求结束关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """按 ORM 模型建表（开发调试用，生产请用 sql/init.sql）"""
    import model  # noqa: F401 确保所有模型已注册
    Base.metadata.create_all(bind=engine)
