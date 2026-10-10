# -*- coding: utf-8 -*-
"""
用户相关模型：user 用户表、login_log 登录日志
"""
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, SmallInteger, String

from model.base import Base


class User(Base):
    """用户表"""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(50), nullable=False, unique=True, comment="登录用户名")
    password_hash = Column(String(200), nullable=False, comment="bcrypt 密码哈希")
    real_name = Column(String(50), comment="真实姓名")
    phone = Column(String(20), comment="手机号")
    role = Column(String(20), nullable=False, default="viewer",
                  comment="角色：admin editor viewer")
    farm_id = Column(Integer, comment="关联牧场ID（家庭账号）")
    status = Column(SmallInteger, nullable=False, default=1, comment="1=正常 0=禁用")
    last_login = Column(DateTime, comment="最后登录时间")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")

    def to_dict(self, with_hash=False):
        """序列化，默认不输出密码哈希"""
        d = {
            "id": self.id,
            "username": self.username,
            "real_name": self.real_name,
            "phone": self.phone,
            "role": self.role,
            "farm_id": self.farm_id,
            "status": self.status,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
        if with_hash:
            d["password_hash"] = self.password_hash
        return d


class LoginLog(Base):
    """登录日志表"""
    __tablename__ = "login_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="日志ID")
    user_id = Column(Integer, nullable=False, comment="用户ID")
    ip = Column(String(50), comment="登录IP")
    user_agent = Column(String(200), comment="浏览器标识")
    login_time = Column(DateTime, nullable=False, default=datetime.now, comment="登录时间")
    success = Column(SmallInteger, nullable=False, default=1, comment="1=成功 0=失败")
