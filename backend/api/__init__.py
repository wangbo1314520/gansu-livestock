# -*- coding: utf-8 -*-
"""
API 蓝图注册：所有接口统一挂在 /api 下
"""
from flask import Flask


def register_blueprints(app: Flask):
    """注册全部蓝图"""
    from api.auth import auth_bp
    from api.base import base_bp
    from api.price import price_bp
    from api.feed import feed_bp
    from api.predict import predict_bp
    from api.analysis import analysis_bp
    from api.alert import alert_bp
    from api.cost import cost_bp
    from api.advice import advice_bp
    from api.farm import farm_bp
    from api.ledger import ledger_bp
    from api.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(base_bp)
    app.register_blueprint(price_bp)
    app.register_blueprint(feed_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(cost_bp)
    app.register_blueprint(advice_bp)
    app.register_blueprint(farm_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(admin_bp)
