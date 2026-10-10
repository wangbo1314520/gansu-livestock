# -*- coding: utf-8 -*-
"""
全局配置：运行模式、数据库连接、JWT、功能开关
数据库账号密码通过环境变量或 .env 注入，不要写死提交到 git
"""
import os

# ------------------------------------------------------------
# 运行模式：school=学校版 home=家用版（同一后端，功能开关不同）
# ------------------------------------------------------------
MODE = os.getenv("APP_MODE", "school")

# ------------------------------------------------------------
# 数据库连接（默认本机 MySQL，实际密码请用环境变量 DB_PASSWORD 覆盖）
# ------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "gansu_livestock"),
    "charset": "utf8mb4",
}

DB_URI = (
    "mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
).format(**DB_CONFIG)

# ------------------------------------------------------------
# JWT 认证配置
# ------------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "gansu-livestock-dev-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7          # token 有效期 7 天，家人懒得天天登录

# ------------------------------------------------------------
# Flask 配置
# ------------------------------------------------------------
JSON_AS_ASCII = False               # 中文原样返回
SQLALCHEMY_TRACK_MODIFICATIONS = False

# ------------------------------------------------------------
# 功能开关：一套后端服务两个前端
# ------------------------------------------------------------
FEATURES = {
    "school": {
        "cost": False,     # 成本计算器（家用）
        "advice": False,   # 出栏建议（家用）
        "farm": False,     # 牧场/存栏管理（家用）
        "ledger": False,   # 家庭账本（家用）
        "push": False,     # 预警推送（家用）
        "lstm": False,     # LSTM 预测（预留）
    },
    "home": {
        "cost": True,
        "advice": True,
        "farm": True,
        "ledger": True,
        "push": True,
        "lstm": False,
    },
}

CURRENT_FEATURES = FEATURES.get(MODE, FEATURES["school"])


def feature_enabled(name):
    """判断某功能在当前模式下是否开放"""
    return CURRENT_FEATURES.get(name, False)
