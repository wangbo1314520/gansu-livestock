# -*- coding: utf-8 -*-
"""
日志配置：控制台 + 文件（backend/logs/app.log）
文件按天滚动，保留 30 天
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def get_logger(name="gansu-livestock"):
    """获取带控制台+文件双输出的 logger"""
    logger = logging.getLogger(name)
    if logger.handlers:          # 防止重复添加 handler
        return logger
    logger.setLevel(logging.INFO)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(console)

    file_handler = TimedRotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    logger.addHandler(file_handler)

    return logger
