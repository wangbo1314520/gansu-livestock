# -*- coding: utf-8 -*-
"""预警触发逻辑测试（不依赖定时器，直接调 service）"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import SessionLocal                              # noqa: E402
from model.alert import AlertRule                           # noqa: E402
from service.alert_service import check_rule, check_all_rules  # noqa: E402


def _db():
    return SessionLocal()


def test_below_cost_not_triggered():
    """规则A：活牛跌破14，当前价15.15>14 不触发"""
    db = _db()
    try:
        rule = db.query(AlertRule).filter(AlertRule.name == "规则A-活牛跌破14元").first()
        if not rule:
            print("SKIP：规则A不存在（可能已被清理）")
            return
        assert not check_rule(db, rule), "15.15>14 不应触发"
    finally:
        db.close()


def test_above_price_not_triggered():
    """规则C：玉米涨超1.2，当前价1.17<1.2 不触发"""
    db = _db()
    try:
        rule = db.query(AlertRule).filter(AlertRule.name == "规则C-玉米涨超1.2元").first()
        if not rule:
            print("SKIP：规则C不存在")
            return
        assert not check_rule(db, rule), "1.17<1.2 不应触发"
    finally:
        db.close()


def test_check_all_rules_runs():
    """全量巡检可执行且返回结构正确"""
    db = _db()
    try:
        result = check_all_rules(db)
        assert "total_rules" in result and "triggered" in result
        assert result["total_rules"] >= 1
    finally:
        db.close()
