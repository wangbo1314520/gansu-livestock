# -*- coding: utf-8 -*-
"""
Flask 应用入口：
  python app.py                       # 学校版模式（默认）
  set APP_MODE=home && python app.py  # 家用版模式
启动时注册全部蓝图、CORS、统一错误处理，可选启动定时调度器
"""
import os

from flask import Flask, request
from werkzeug.exceptions import HTTPException

import config
from api import register_blueprints
from utils.logger import get_logger
from utils.response import err

logger = get_logger("app")


def create_app():
    """应用工厂"""
    app = Flask(__name__)
    app.config.from_object(config)
    app.json.ensure_ascii = False          # 中文原样输出

    # 跨域：两个前端（Vite 开发服务器 5173/5174）访问后端
    from flask_cors import CORS
    CORS(app, supports_credentials=True)

    # 注册全部接口蓝图
    register_blueprints(app)

    # 统一错误处理：异常也走 {"code":..,"msg":..} 格式
    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return err(e.code or 500, e.description or e.name)

    @app.errorhandler(Exception)
    def handle_error(e):
        logger.exception("未捕获异常: %s", e)
        return err(500, "服务器内部错误: %s" % e)

    @app.route("/api/health")
    def health():
        """健康检查"""
        return {"code": 200, "msg": "ok",
                "data": {"mode": config.MODE, "service": "gansu-livestock"}}

    return app


app = create_app()

if __name__ == "__main__":
    # 定时调度器默认随应用启动（爬虫/预测/预警就位后自动生效）
    if os.getenv("ENABLE_SCHEDULER", "1") == "1":
        from utils.scheduler import start_scheduler
        start_scheduler()

    logger.info("启动 gansu-livestock 后端，模式=%s", config.MODE)
    # host 0.0.0.0：家用版手机经 Tailscale/局域网访问
    app.run(host="0.0.0.0", port=5000, debug=False)
